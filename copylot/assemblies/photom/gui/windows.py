import os
import time
from datetime import date, datetime
from typing import Tuple

import numpy as np
from networkx import center
from PyQt5.QtCore import QPoint, Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetricsF,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QResizeEvent,
)
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from copylot.assemblies.photom.gui.utils import (
    CalibrationWithCameraThread,
    ClickablePixmapItem,
)
from copylot.assemblies.photom.gui.widgets import (
    ArduinoPWMWidget,
    LaserWidget,
    MirrorWidget,
)
from copylot.assemblies.photom.photom import PhotomAssembly
from copylot.assemblies.photom.utils.pattern_tracing import ShapeTrace
from copylot.assemblies.photom.utils.scanning_algorithms import (
    calculate_rectangle_corners,
)


class PhotomApp(QMainWindow):
    def __init__(
        self,
        photom_assembly: PhotomAssembly,
        photom_window_pos: tuple,
        demo_mode: bool = False,
        arduino=None,
    ):
        super().__init__()
        self.photom_assembly = photom_assembly
        self.photom_window_pos = photom_window_pos
        self.demo_mode = demo_mode
        self.arduino = arduino

        # Calculate window sizes based on screen dimensions
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        self.photom_window_size_x = screen_geometry.width() // 3

        # Get sensor size and ROI from assembly
        self.photom_sensor_size_yx = self.photom_assembly.sensor_size[:2]
        self.sensor_offset_yx = self.photom_assembly.sensor_size[2:]

        # Calculate effective dimensions based on ROI
        self.photom_window = None
        self.photom_controls_window = None

        self.lasers = self.photom_assembly.laser
        self.mirrors = self.photom_assembly.mirror
        self._current_mirror_idx = 0
        self._laser_window_transparency = 0.7
        self.scaling_matrix = np.eye(3)
        self.T_mirror_cam_matrix = np.eye(3)
        self.calibration_w_cam_thread = CalibrationWithCameraThread(
            self.photom_assembly, self._current_mirror_idx
        )
        self.calibration_w_cam_thread.finished.connect(self.done_calibration)
        self.imageWindows = []
        self.drawingTraces = []  # List to store traces
        self.currentTrace = []  # Current trace being drawn

        self.initializer_laser_marker_window()
        self.initialize_UI()

    def initializer_laser_marker_window(self):
        # Making the photom_window a square and display right besides the control UI
        window_pos = (
            self.photom_window_size_x + self.photom_window_pos[0],
            self.photom_window_pos[1],
        )

        # Use effective sensor size for aspect ratio
        self.aspect_ratio_yx = (
            self.photom_sensor_size_yx[1] / self.photom_sensor_size_yx[0]
        )

        self.photom_window = LaserMarkerWindow(
            photom_controls=self,
            name='Laser Marker',
            sensor_size_yx=self.photom_sensor_size_yx,
            sensor_offset_yx=self.sensor_offset_yx,
            fixed_width=self.photom_window_size_x,
            window_pos=window_pos,
        )

        calculated_height = self.photom_window_size_x / self.aspect_ratio_yx

        # Update scaling factors based on effective sensor size
        self.scaling_factor_x = (
            self.photom_sensor_size_yx[1] / self.photom_window_size_x
        )
        self.scaling_factor_y = self.photom_sensor_size_yx[0] / calculated_height
        # TODO: the affine transforms are in XY coordinates. Need to change to YX
        self.scaling_matrix = np.array(
            [
                [self.scaling_factor_x, 0, self.sensor_offset_yx[1]],
                [0, self.scaling_factor_y, self.sensor_offset_yx[0]],
                [0, 0, 1],
            ]
        )

        self.photom_window.windowClosed.connect(self.closeAllWindows)

    def initialize_UI(self):
        """
        Initialize the UI.

        """
        self.setGeometry(
            self.photom_window_pos[0],
            self.photom_window_pos[1],
            self.photom_window_size_x,
            self.photom_window_size_x,
        )
        self.setWindowTitle("Laser and Mirror Control App")

        # Create main layout
        main_layout = QVBoxLayout()

        # Create tab widget for all controls
        control_tabs = QTabWidget()

        # Create Photom Controls tab
        photom_tab = QWidget()
        photom_layout = QVBoxLayout()

        # Add all controls to photom_layout
        # Transparency group
        transparency_group = QGroupBox("Photom Transparency")
        transparency_layout = QVBoxLayout()
        # Create a slider to adjust the transparency
        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setMinimum(0)
        self.transparency_slider.setMaximum(100)
        self.transparency_slider.setValue(
            int(self._laser_window_transparency * 100)
        )  # Initial value is fully opaque
        self.transparency_slider.valueChanged.connect(self.update_transparency)
        transparency_layout.addWidget(self.transparency_slider)

        # Add a QLabel to display the current percent transparency value
        self.transparency_label = QLabel(f"Transparency: 100%")
        transparency_layout.addWidget(self.transparency_label)

        # Resize QSpinBox
        self.resize_spinbox = QSpinBox()
        self.resize_spinbox.setRange(50, 400)  # Set range from 50% to 200%
        self.resize_spinbox.setSuffix("%")  # Add a percentage sign as suffix
        self.resize_spinbox.setValue(100)  # Default value is 100%
        self.resize_spinbox.valueChanged.connect(self.resize_laser_marker_window)
        self.resize_spinbox.editingFinished.connect(self.resize_laser_marker_window)
        transparency_layout.addWidget(QLabel("Resize Window:"))
        transparency_layout.addWidget(self.resize_spinbox)

        # Set the transparency group layout
        transparency_group.setLayout(transparency_layout)
        photom_layout.addWidget(transparency_group)

        # Laser group
        laser_group = QGroupBox("Lasers")
        laser_layout = QVBoxLayout()
        self.laser_widgets = []
        for laser in self.lasers:
            laser_widget = LaserWidget(laser)
            self.laser_widgets.append(laser_widget)
            laser_layout.addWidget(laser_widget)
        laser_group.setLayout(laser_layout)
        photom_layout.addWidget(laser_group)

        # Mirror group
        mirror_group = QGroupBox("Mirrors")
        mirror_layout = QVBoxLayout()
        self.mirror_widgets = []
        for idx, mirror in enumerate(self.mirrors):
            mirror_widget = MirrorWidget(mirror)
            self.mirror_widgets.append(mirror_widget)
            mirror_layout.addWidget(mirror_widget)
        mirror_group.setLayout(mirror_layout)
        photom_layout.addWidget(mirror_group)

        # TODO remove if arduino is removed
        # Adding group for arduino PWM
        arduino_group = QGroupBox("Arduino PWM")
        arduino_layout = QVBoxLayout()
        self.arduino_pwm_widgets = []
        for arduino in self.arduino:
            arduino_pwm_widget = ArduinoPWMWidget(self.photom_assembly, arduino, self)
            self.arduino_pwm_widgets.append(arduino_pwm_widget)
            arduino_layout.addWidget(arduino_pwm_widget)
        arduino_group.setLayout(arduino_layout)
        photom_layout.addWidget(arduino_group)

        # Drawing controls
        drawing_group = QGroupBox("Drawing Controls")
        drawing_layout = QVBoxLayout()
        self.game_mode_button = QPushButton("Game Mode: OFF", self)
        self.game_mode_button.setCheckable(True)  # Make the button toggleable
        self.game_mode_button.clicked.connect(self.toggle_game_mode)

        self.toggle_drawing_mode_button = QPushButton("Toggle Drawing Mode", self)
        self.toggle_drawing_mode_button.clicked.connect(self.toggleDrawingMode)
        self.playButton = QPushButton("Play", self)
        self.playButton.clicked.connect(self.play_drawing)
        self.playButton.hide()  # Initially hide the Play button

        # dropdowns for drawing mode
        self.drawing_dropdowns = QHBoxLayout()
        self.drawing_dropdowns_widget = QWidget()

        # roi dropdown box
        self.roi_dropdown = QComboBox(self)
        self.roi_dropdown.addItem("Select ROI")
        self.photom_window.shapesUpdated.connect(self.updateRoiDropdown)
        self.roi_dropdown.currentIndexChanged.connect(self.onRoiSelected)
        self.drawing_dropdowns.addWidget(self.roi_dropdown)

        # pattern dropdown box
        self.patterns = ['Bidirectional', 'Spiral']
        self.pattern_dropdown = QComboBox(self)
        self.pattern_dropdown.addItem("Select Pattern")
        self.addPatternDropdownItems()
        self.pattern_dropdown.currentIndexChanged.connect(self.onPatternSelected)
        self.drawing_dropdowns.addWidget(self.pattern_dropdown)
        self.drawing_dropdowns_widget.setLayout(self.drawing_dropdowns)

        # horizontal spacing box for bidirectional pattern
        self.bidirectional_params = QHBoxLayout()
        self.horizontal_spacing_label = QLabel("H Spacing:", self)
        self.bidirectional_params.addWidget(self.horizontal_spacing_label)
        self.horizontal_spacing_input = QLineEdit(self)
        self.bidirectional_params.addWidget(self.horizontal_spacing_input)

        # vertical spacing box for bidirectional pattern
        self.vertical_spacing_label = QLabel("V Spacing:", self)
        self.bidirectional_params.addWidget(self.vertical_spacing_label)
        self.vertical_spacing_input = QLineEdit(self)
        self.bidirectional_params.addWidget(self.vertical_spacing_input)

        # n number of points box for bidirectional pattern
        self.num_points_label = QLabel("No. Points:", self)
        self.bidirectional_params.addWidget(self.num_points_label)
        self.num_points_input = QLineEdit(self)
        self.bidirectional_params.addWidget(self.num_points_input)

        # widget for spacing boxes
        self.bidirectional_params_widget = QWidget()
        self.bidirectional_params_widget.setLayout(self.bidirectional_params)
        self.bidirectional_params_widget.hide()

        # parameter layout for spiral pattern
        self.spiral_params = QHBoxLayout()

        self.spiral_nums_label = QLabel("Number of Points:", self)
        self.spiral_params.addWidget(self.spiral_nums_label)
        self.spiral_nums_input = QLineEdit(self)
        self.spiral_params.addWidget(self.spiral_nums_input)
        self.spiral_params_widget = QWidget()
        self.spiral_params_widget.setLayout(self.spiral_params)
        self.spiral_params_widget.hide()

        # time delay between_points
        self.delay_time_widget = QWidget()
        self.delay_label = QLabel("Delay (s):", self)
        self.delay_input = QLineEdit(self)
        self.delay_time_layout = QHBoxLayout()
        self.delay_time_layout.addWidget(self.delay_label)
        self.delay_time_layout.addWidget(self.delay_input)
        self.delay_time_widget.setLayout(self.delay_time_layout)
        self.delay_time_widget.hide()

        # apply pattern button
        self.pattern_and_delete_buttons = QHBoxLayout()
        self.apply_pattern_button = QPushButton("Apply Pattern", self)
        self.apply_pattern_button.setMinimumSize(200, 50)
        self.apply_pattern_button.clicked.connect(self.onApplyPatternClick)
        self.pattern_and_delete_buttons.addWidget(self.apply_pattern_button)

        # delete shape/pattern button
        self.delete_button = QPushButton("Delete", self)
        self.delete_button.setMinimumSize(200, 50)
        self.delete_button.clicked.connect(self.onDeleteClick)
        self.pattern_and_delete_buttons.addWidget(self.delete_button)
        self.pattern_and_delete_widget = QWidget()
        self.pattern_and_delete_widget.setLayout(self.pattern_and_delete_buttons)

        # run button
        self.run_button = QPushButton("Run", self)
        self.run_button.clicked.connect(self.photom_window._roi_tracing)

        # drawing mode widget
        self.drawing_mode_layout = QVBoxLayout()
        self.drawing_mode_widget = QWidget()
        self.drawing_mode_layout.addWidget(self.playButton)
        self.drawing_mode_layout.addWidget(self.drawing_dropdowns_widget)
        self.drawing_mode_layout.addWidget(self.bidirectional_params_widget)
        self.drawing_mode_layout.addWidget(self.spiral_params_widget)
        self.drawing_mode_layout.addWidget(self.delay_time_widget)
        self.drawing_mode_layout.addWidget(self.pattern_and_delete_widget)
        self.drawing_mode_layout.addWidget(self.run_button)
        self.drawing_mode_widget.setLayout(self.drawing_mode_layout)

        self.drawing_mode_group = QGroupBox("Drawing Mode")
        self.drawing_mode_group.setLayout(self.drawing_mode_layout)
        self.drawing_mode_group.hide()

        drawing_layout.addWidget(self.drawing_mode_group)
        drawing_layout.addWidget(self.game_mode_button)
        drawing_layout.addWidget(self.toggle_drawing_mode_button)
        drawing_layout.addWidget(self.drawing_mode_widget)

        drawing_group.setLayout(drawing_layout)
        photom_layout.addWidget(drawing_group)

        # Add mirror dropdown and other controls
        self.mirror_dropdown = QComboBox()
        self.mirror_dropdown.addItems([mirror.name for mirror in self.mirrors])
        photom_layout.addWidget(self.mirror_dropdown)
        self.mirror_dropdown.setCurrentIndex(self._current_mirror_idx)
        self.mirror_dropdown.currentIndexChanged.connect(self.mirror_dropdown_changed)

        self.recenter_marker_button = QPushButton("Recenter Marker")
        self.recenter_marker_button.clicked.connect(self.recenter_marker)
        photom_layout.addWidget(self.recenter_marker_button)

        self.calibrate_button = QPushButton("Calibrate")
        self.calibrate_button.clicked.connect(self.calibrate_w_camera)
        photom_layout.addWidget(self.calibrate_button)

        self.load_calibration_button = QPushButton("Load Calibration")
        self.load_calibration_button.clicked.connect(self.load_calibration)
        photom_layout.addWidget(self.load_calibration_button)

        # Add a "Cancel Calibration" button (initially hidden)
        self.cancel_calibration_button = QPushButton("Cancel Calibration")
        self.cancel_calibration_button.clicked.connect(self.cancel_calibration)
        self.cancel_calibration_button.hide()
        photom_layout.addWidget(self.cancel_calibration_button)

        # Set photom tab layout
        photom_tab.setLayout(photom_layout)

        # Create Dev Tools tab (ROI controls)
        dev_tab = QWidget()
        dev_layout = QVBoxLayout()

        # Add ROI control group to dev tab
        roi_group = QGroupBox("Sensor ROI")
        roi_grid_layout = QGridLayout()

        # Add spinboxes for ROI control
        self.roi_x_offset = QSpinBox()
        self.roi_y_offset = QSpinBox()
        self.roi_width = QSpinBox()
        self.roi_height = QSpinBox()

        # Configure spinboxes
        for spinbox in [self.roi_x_offset, self.roi_y_offset]:
            spinbox.setRange(0, max(self.photom_sensor_size_yx))
            spinbox.setValue(
                self.sensor_offset_yx[1]
                if spinbox == self.roi_x_offset
                else self.sensor_offset_yx[0]
            )

        for spinbox in [self.roi_width, self.roi_height]:
            spinbox.setRange(1, max(self.photom_sensor_size_yx))
            spinbox.setValue(
                self.photom_sensor_size_yx[1]
                if spinbox == self.roi_width
                else self.photom_sensor_size_yx[0]
            )

        # Add labels and spinboxes to layout
        roi_grid_layout.addWidget(QLabel("X Offset:"), 0, 0)
        roi_grid_layout.addWidget(self.roi_x_offset, 0, 1)
        roi_grid_layout.addWidget(QLabel("Y Offset:"), 1, 0)
        roi_grid_layout.addWidget(self.roi_y_offset, 1, 1)
        roi_grid_layout.addWidget(QLabel("Width:"), 2, 0)
        roi_grid_layout.addWidget(self.roi_width, 2, 1)
        roi_grid_layout.addWidget(QLabel("Height:"), 3, 0)
        roi_grid_layout.addWidget(self.roi_height, 3, 1)

        # Add apply button
        apply_roi_button = QPushButton("Apply ROI")
        apply_roi_button.clicked.connect(self.update_roi)
        roi_grid_layout.addWidget(apply_roi_button, 4, 0, 1, 2)

        roi_group.setLayout(roi_grid_layout)
        dev_layout.addWidget(roi_group)
        dev_tab.setLayout(dev_layout)

        # Add tabs to tab widget
        control_tabs.addTab(photom_tab, "Photom Controls")
        control_tabs.addTab(dev_tab, "Dev Tools")

        # Add tab widget to main layout
        main_layout.addWidget(control_tabs)

        # Create scrollable widget
        scroll_widget = QWidget()
        scroll_widget.setLayout(main_layout)

        # Set up scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Set the scroll area as the central widget
        self.setCentralWidget(scroll_area)
        self.show()

    def toggle_game_mode(self, checked):
        if checked:
            self.game_mode_button.setText("Game Mode: ON")
            self.photom_window.game_mode = True
        else:
            self.game_mode_button.setText("Game Mode: OFF")
            self.photom_window.game_mode = False

    def toggleDrawingMode(self):
        # Call the method to toggle the drawing scene on the LaserMarkerWindow
        if (
            self.photom_window.stacked_widget.currentWidget()
            == self.photom_window.drawing_view
        ):
            # If in drawing mode, clear the drawing before switching
            self.photom_window.clearDrawing()
            self.drawing_mode_group.hide()
            self.photom_window.toggleDrawingScene()
        else:
            self.drawing_mode_group.show()
            self.photom_window.toggleDrawingScene()

    def resize_laser_marker_window(self):
        # Retrieve the selected resize percentage from the QSpinBox
        percentage = self.resize_spinbox.value() / 100.0

        # Calculate the new width based on the selected percentage
        new_width = int(self.photom_window_size_x * percentage)
        # Calculate the new height to maintain the aspect ratio
        new_height = int(new_width / self.photom_window.aspect_ratio)

        self.photom_window.update_window_geometry(new_width, new_height)

        # Update the scaling transform matrix based on window size
        self.scaling_factor_x = self.photom_sensor_size_yx[1] / new_width
        self.scaling_factor_y = self.photom_sensor_size_yx[0] / new_height

        self.scaling_matrix = np.array(
            [
                [self.scaling_factor_x, 0, self.sensor_offset_yx[1]],
                [0, self.scaling_factor_y, self.sensor_offset_yx[0]],
                [0, 0, 1],
            ]
        )
        T_compose_mat = self.T_mirror_cam_matrix @ self.scaling_matrix
        self.photom_assembly.mirror[
            self._current_mirror_idx
        ].affine_transform_obj.set_affine_matrix(T_compose_mat)

    def mirror_dropdown_changed(self, index):
        print(f"Mirror dropdown changed to index {index}")
        self._current_mirror_idx = index

        # Reset to (0,0) position
        self.photom_assembly.mirror[self._current_mirror_idx].position = [0, 0]

    def recenter_marker(self):
        self.photom_window.recenter_marker()

    def calibrate_w_camera(self):
        """Start camera calibration process"""
        print("Calibrating with camera...")

        # Initialize camera
        self._initialize_camera()

        self.photom_assembly.laser[0].power = 0.0
        self.photom_assembly.laser[0].toggle_emission = True

        # Hide the calibration buttons
        self.calibrate_button.hide()
        self.load_calibration_button.hide()
        self.cancel_calibration_button.show()

        self.photom_window.switch_to_calibration_scene()
        self.calibration_w_cam_thread.start()

    def load_calibration(self):
        print("Loading calibration...")
        # Prompt the user to select a file
        typed_filename, _ = QFileDialog.getOpenFileName(
            self, "Open Calibration File", "", "YAML Files (*.yml)"
        )
        if typed_filename:
            assert typed_filename.endswith(".yml")
            print("Selected file:", typed_filename)
            # Load the matrix
            self.photom_assembly.mirror[
                self._current_mirror_idx
            ].affine_transform_obj.load_matrix(config_file=typed_filename)
            print(
                f'Loaded matrix:{self.photom_assembly.mirror[self._current_mirror_idx].affine_transform_obj.T_affine}'
            )
            # Scale the matrix calculated from calibration to match the photom laser window
            self.T_mirror_cam_matrix = self.photom_assembly.mirror[
                self._current_mirror_idx
            ].affine_transform_obj.get_affine_matrix()
            T_compose_mat = self.T_mirror_cam_matrix @ self.scaling_matrix
            self.photom_assembly.mirror[
                self._current_mirror_idx
            ].affine_transform_obj.set_affine_matrix(T_compose_mat)
            print("Scaled matrix:", T_compose_mat)
            self.photom_window.switch_to_shooting_scene()
            self.photom_window.marker.show()

            # Hide the "Done Calibration" button
            self.calibrate_button.show()
            self.cancel_calibration_button.hide()

            # Update the affine to match the photom laser window
            self.update_laser_window_affine()

            # if DEMO_MODE:
            #     NotImplementedError("Demo Mode: Calibration not implemented yet.")
        else:
            print("No file selected. Skiping Saving the calibration matrix.")
            # Show dialog box saying no file selected
        print("Calibration done")
        center_coords = [
            self.photom_sensor_size_yx[0] / 2,
            self.photom_sensor_size_yx[1] / 2,
        ]
        self.photom_assembly.set_position(self._current_mirror_idx, center_coords)

    def update_laser_window_affine(self):
        # Update the scaling transform matrix
        print('updating laser window affine')
        self.scaling_factor_x = (
            self.photom_sensor_size_yx[1] / self.photom_window_size_x
        )
        self.scaling_factor_y = (
            self.photom_sensor_size_yx[0] / self.photom_window_size_x
        )
        self.scaling_matrix = np.array(
            [
                [self.scaling_factor_x, 0, self.sensor_offset_yx[1]],
                [0, self.scaling_factor_y, self.sensor_offset_yx[0]],
                [0, 0, 1],
            ]
        )
        T_compose_mat = self.T_mirror_cam_matrix @ self.scaling_matrix
        self.photom_assembly.mirror[
            self._current_mirror_idx
        ].affine_transform_obj.set_affine_matrix(T_compose_mat)
        print(f'Updated affine matrix: {T_compose_mat}')

    def update_transparency(self, value):
        transparency_percent = value
        self.transparency_label.setText(f"Transparency: {transparency_percent}%")
        opacity = 1.0 - (transparency_percent / 100.0)  # Calculate opacity (0.0 to 1.0)
        self.photom_window.setWindowOpacity(opacity)  # Update photom_window opacity

    def play_drawing(self):
        for trace in self.photom_window.drawingTraces:
            print(f'Playing trace: {trace}')
            self.photom_assembly.set_position(self._current_mirror_idx, trace)

    def display_rectangle(self):
        self.photom_window.switch_to_calibration_scene()

    def closeEvent(self, event):
        self.closeAllWindows()  # Ensure closing main window closes everything
        super().closeEvent(event)

    def closeAllWindows(self):
        self.photom_window.close()
        self.close()
        QApplication.quit()  # Quit the application

    def updateRoiDropdown(self) -> None:
        """updates the ROI dropdown with the current shapes."""
        self.roi_dropdown.clear()
        self.roi_dropdown.addItem("Select ROI")
        for roi in self.photom_window.shapes.keys():
            self.roi_dropdown.addItem(f"Shape {roi + 1}")

    def onRoiSelected(self) -> None:
        """handles the selection of an ROI from the dropdown."""
        selected_roi = self.roi_dropdown.currentText()
        if selected_roi:
            if selected_roi == "Select ROI":
                self.photom_window.selected_shape_id = None
            else:
                roi_id = int(selected_roi.split(" ")[1]) - 1
                self.photom_window.selected_shape_id = roi_id
        self.photom_window.update()

    def addPatternDropdownItems(self) -> None:
        """adds the patterns to the pattern dropdown."""
        for pattern in self.patterns:
            self.pattern_dropdown.addItem(pattern)

    def onPatternSelected(self) -> None:
        """handles the selection of a pattern from the dropdown."""
        selected_pattern = self.pattern_dropdown.currentText()
        if selected_pattern == "Bidirectional":
            self.bidirectional_params_widget.show()
            self.spiral_params_widget.hide()
            self.delay_time_widget.show()
        elif selected_pattern == "Spiral":
            self.spiral_params_widget.show()
            self.bidirectional_params_widget.hide()
            self.delay_time_widget.show()
        else:
            self.bidirectional_params_widget.hide()
            self.spiral_params_widget.hide()
            self.delay_time_widget.hide()

    def onApplyPatternClick(self) -> None:
        """applies the selected pattern to the selected ROI."""
        selected_roi = self.roi_dropdown.currentText()
        if selected_roi == "Select ROI":
            return
        roi_number = int(selected_roi.split(" ")[1]) - 1
        selected_pattern = self.pattern_dropdown.currentText()

        if selected_pattern == 'Bidirectional':
            try:
                horizontal_spacing = int(self.horizontal_spacing_input.text())
                vertical_spacing = int(self.vertical_spacing_input.text())
                num_points = self.num_points_input.text()
                if num_points:
                    num_points = int(num_points)
                else:
                    num_points = None

                shape = self.photom_window.shapes[roi_number]
                shape.pattern_points = []
                shape.ablation_points = []
                self.photom_window.shapes[roi_number]._pattern_bidirectional(
                    vertical_spacing=vertical_spacing,
                    horizontal_spacing=horizontal_spacing,
                    num_points=num_points,
                )
            except ValueError:
                print('Invalid spacing value')
        elif selected_pattern == 'Spiral':
            try:
                num_points = self.spiral_nums_input.text()
                if num_points:
                    num_points = int(num_points)
                else:
                    num_points = None

                shape = self.photom_window.shapes[roi_number]
                shape.ablation_points.clear()
                self.photom_window.shapes[roi_number]._pattern_spiral(
                    num_points=num_points,
                )
            except ValueError:
                print('Invalid spacing value')

        self.photom_window.update()

    def onDeleteClick(self) -> None:
        """handles the deletion of shape when the delete button is clicked."""
        selected_roi = self.roi_dropdown.currentText()
        if selected_roi and selected_roi != 'Select ROI':
            roi_id = int(selected_roi.split(" ")[1]) - 1
            del self.photom_window.shapes[roi_id]
            self.photom_window.update()
            self.updateRoiDropdown()

    def update_roi(self):
        """Updates the ROI and recalculates window dimensions and scaling"""
        print("Updating ROI...")

        try:
            # Initialize camera
            cam = self._initialize_camera()

            # Update sensor size and offset
            new_sensor_size = (
                self.roi_height.value(),  # height (y)
                self.roi_width.value(),  # width (x)
                self.roi_x_offset.value(),  # x offset
                self.roi_y_offset.value(),  # y offset
            )

            # Update camera ROI
            self.photom_assembly.camera[0].image_size = new_sensor_size
            self.photom_assembly.sensor_size = new_sensor_size

            # Update local values
            self.photom_sensor_size_yx = new_sensor_size[:2]  # (height, width)
            self.sensor_offset_yx = new_sensor_size[2:]  # (x_offset, y_offset)

            # Update window dimensions and scaling
            calculated_height = self._update_window_dimensions()

            # Update laser marker window
            if self.photom_window:
                self.photom_window.sensor_size_yx = self.photom_sensor_size_yx
                self.photom_window.sensor_offset_yx = self.sensor_offset_yx
                self.photom_window.aspect_ratio = self.aspect_ratio_yx
                self.photom_window.update_window_geometry(
                    self.photom_window_size_x, int(calculated_height)
                )

        finally:
            self._cleanup_camera()

        print("ROI update complete")

    def done_calibration(self, T_affine, plot_save_path):
        """Handles completion of camera calibration"""
        self._cleanup_camera()

        # Show plot and update matrix
        self.display_saved_plot(plot_save_path)
        self.T_mirror_cam_matrix = T_affine

        # Save the affine matrix to a file
        typed_filename, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "YAML Files (*.yml)"
        )
        if typed_filename:
            if not typed_filename.endswith(".yml"):
                typed_filename += ".yml"
            print("Selected file:", typed_filename)
            # Save the matrix
            self.photom_assembly.mirror[
                self._current_mirror_idx
            ].affine_transform_obj.save_matrix(
                matrix=self.T_mirror_cam_matrix, config_file=typed_filename
            )
            self.photom_window.switch_to_shooting_scene()
            self.photom_window.marker.show()

            # Hide the calibration buttons
            self.calibrate_button.show()
            self.cancel_calibration_button.hide()

            # Update the affine to match the photom laser window
            self.update_laser_window_affine()

        print("Calibration done")
        center_coords = [
            self.photom_sensor_size_yx[0] / 2,
            self.photom_sensor_size_yx[1] / 2,
        ]
        self.photom_assembly.set_position(self._current_mirror_idx, center_coords)

    def display_saved_plot(self, plot_path):
        """Displays the calibration plot in a new window"""
        image_window = ImageWindow(plot_path)
        image_window.show()
        self.imageWindows.append(image_window)

    def cancel_calibration(self):
        """Cancels the calibration process and resets the UI"""
        print("Canceling calibration...")

        # Show the calibration buttons
        self.calibrate_button.show()
        self.load_calibration_button.show()

        # Show the marker in photom_window
        self.photom_window.marker.show()

        # Hide cancel button
        self.cancel_calibration_button.hide()

        # Switch back to the shooting scene
        self.photom_window.switch_to_shooting_scene()

    def _initialize_camera(self):
        """Initialize and return camera based on mode"""
        if self.demo_mode:
            from copylot.assemblies.photom.photom_mock_devices import MockFlirCamera

            cam = MockFlirCamera()
        else:
            from copylot.hardware.cameras.flir.flir_camera import FlirCamera

            cam = FlirCamera()
        cam.open()
        self.photom_assembly.camera = [cam]
        return cam

    def _cleanup_camera(self):
        """Cleanup camera resources"""
        if self.photom_assembly.camera:
            self.photom_assembly.camera[0].close()
            self.photom_assembly.camera = []

    def _update_window_dimensions(self):
        """Update window dimensions and scaling factors"""
        # Update aspect ratio and calculate new height
        self.aspect_ratio_yx = (
            self.photom_sensor_size_yx[1] / self.photom_sensor_size_yx[0]
        )
        calculated_height = self.photom_window_size_x / self.aspect_ratio_yx

        # Update scaling factors
        self.scaling_factor_x = (
            self.photom_sensor_size_yx[1] / self.photom_window_size_x
        )
        self.scaling_factor_y = self.photom_sensor_size_yx[0] / calculated_height

        # Update scaling matrix
        self.scaling_matrix = np.array(
            [
                [self.scaling_factor_x, 0, self.sensor_offset_yx[1]],
                [0, self.scaling_factor_y, self.sensor_offset_yx[0]],
                [0, 0, 1],
            ]
        )

        return calculated_height

    def update_laser_window_affine(self):
        # Update the scaling transform matrix
        print('updating laser window affine')
        self.scaling_factor_x = (
            self.photom_sensor_size_yx[1] / self.photom_window_size_x
        )
        self.scaling_factor_y = (
            self.photom_sensor_size_yx[0] / self.photom_window_size_x
        )
        self.scaling_matrix = np.array(
            [
                [self.scaling_factor_x, 0, self.sensor_offset_yx[1]],
                [0, self.scaling_factor_y, self.sensor_offset_yx[0]],
                [0, 0, 1],
            ]
        )
        T_compose_mat = self.T_mirror_cam_matrix @ self.scaling_matrix
        self.photom_assembly.mirror[
            self._current_mirror_idx
        ].affine_transform_obj.set_affine_matrix(T_compose_mat)
        print(f'Updated affine matrix: {T_compose_mat}')


class LaserMarkerWindow(QMainWindow):
    windowClosed = pyqtSignal()  # Define the signal
    shapesUpdated = pyqtSignal()

    def __init__(
        self,
        photom_controls: QMainWindow = None,
        name="Laser Marker",
        sensor_size_yx: Tuple = (2048, 2048),
        sensor_offset_yx: Tuple = (0, 0),
        window_pos: Tuple = (100, 100),
        fixed_width: int = 800,
    ):
        super().__init__()
        self.photom_controls = photom_controls
        self.window_name = name
        self.sensor_size_yx = sensor_size_yx
        self.sensor_offset_yx = sensor_offset_yx
        self.aspect_ratio = sensor_size_yx[1] / sensor_size_yx[0]
        self.fixed_width = fixed_width
        calculated_height = int(self.fixed_width / self.aspect_ratio)
        self.window_pos = window_pos
        self.window_geometry = self.window_pos + (self.fixed_width, calculated_height)
        self.setMouseTracking(True)
        self.setWindowOpacity(self.photom_controls._laser_window_transparency)
        self.game_mode = False  # Default to off
        # Create a QStackedWidget
        # TODO: do we need the stacked widget?
        self.stacked_widget = QStackedWidget()
        # Set the QStackedWidget as the central widget
        self.initialize_UI()
        self.initMarker()
        self.initDrawingScene()

        self.lastPoint = None
        self.drawing = False
        self.drawingTraces = []  # To store lists of traces
        self.currentTrace = []  # To store points of the current trace being drawn

        # drawing class variables
        self.drawing = False
        self.shapes = {}
        self.curr_shape_points = []
        self.curr_shape_id = 0
        self.selected_shape_id = None

        tetragon_coords = calculate_rectangle_corners(
            [self.window_geometry[-2] / 5, self.window_geometry[-1] / 5],
            center=[self.window_geometry[-2] / 2, self.window_geometry[-1] / 2],
        )
        self.init_tetragon(tetragon_coords=tetragon_coords)

        self.setCentralWidget(self.stacked_widget)

        self.switch_to_shooting_scene()

        # show the window
        self.show()

        # FLAGS
        self._right_click_hold = False
        self._left_click_hold = False

    def initialize_UI(self):
        print(f'window geometry: {self.window_geometry}')
        self.setWindowTitle(self.window_name)

        # Fix the size of the window
        self.setFixedSize(
            self.window_geometry[2],
            self.window_geometry[3],
        )
        # self.sidebar_size = self.frameGeometry().width() - self.window_geometry[2]
        # self.topbar_size = self.frameGeometry().height() - self.window_geometry[3]
        # self.canvas_width = self.frameGeometry().width() - self.sidebar_size
        # self.canvas_height = self.frameGeometry().height() - self.topbar_size

        # print(f'sidebar size: {self.sidebar_size}, topbar size: {self.topbar_size}')
        # print(f'canvas width: {self.canvas_width}, canvas height: {self.canvas_height}')

    def update_window_geometry(self, new_width, new_height):
        self.window_geometry = self.window_pos + (new_width, new_height)
        self.shooting_view.setFixedSize(new_width, new_height)
        self.shooting_scene.setSceneRect(0, 0, new_width, new_height)
        self.setFixedSize(new_width, new_height)

        self.drawing_view.setFixedSize(new_width, new_height)
        self.drawing_scene.setSceneRect(0, 0, new_width, new_height)
        self.drawablePixmap = QPixmap(int(new_width), int(new_height))
        self.drawablePixmapItem.setPixmap(self.drawablePixmap)

    def recenter_marker(self):
        self.display_marker_center(
            self.marker,
            (self.window_geometry[-2] / 2, self.window_geometry[-1] / 2),
        )

    def initMarker(self):
        # Generate the shooting scene
        self.shooting_scene = QGraphicsScene(self)
        self.shooting_scene.setSceneRect(
            0, 0, self.window_geometry[-2], self.window_geometry[-1]
        )

        # Generate the shooting view
        self.shooting_view = QGraphicsView(self.shooting_scene)
        self.shooting_view.setMouseTracking(True)
        self.shooting_view.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.shooting_view.setFixedSize(
            self.window_geometry[-2], self.window_geometry[-1]
        )

        # Mouse tracking
        self.shooting_view.installEventFilter(self)
        self.shooting_view.viewport().installEventFilter(self)
        self.setMouseTracking(True)
        # self.marker = QGraphicsSimpleTextItem("+")
        # self.marker.setBrush(QColor(255, 0, 0))
        # Load the PNG image
        # Get the current script directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the relative path
        image_path = os.path.join(
            current_dir, '..', 'utils', 'images', 'hit_marker_red.png'
        )

        pixmap = QPixmap(image_path)
        assert pixmap.isNull() == False
        pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Create a QGraphicsPixmapItem with the loaded image
        self.marker = ClickablePixmapItem(pixmap)
        self.marker.setFlag(QGraphicsItem.ItemIsMovable, True)

        # # Set larger font size
        # font = self.marker.font()
        # font.setPointSize(30)
        # self.marker.setFont(font)

        # Position the marker
        self.display_marker_center(
            self.marker, (self.window_geometry[-2] / 2, self.window_geometry[-1] / 2)
        )

        self.shooting_scene.addItem(self.marker)

        ## Add the rectangle
        rect_width = 2 * self.window_geometry[-2] / 3
        rect_height = 2 * self.window_geometry[-1] / 3
        rect_x = (self.window_geometry[-2] - rect_width) / 2
        rect_y = (self.window_geometry[-1] - rect_height) / 2
        # Continue from the previous code in initMarker...
        pen = QPen(QColor(0, 0, 0))
        pen.setStyle(Qt.DashLine)  # Dashed line style
        pen.setWidth(2)  # Set the pen width

        # Create the rectangle with no fill (transparent)
        self.dashed_rectangle = QGraphicsRectItem(
            rect_x, rect_y, rect_width, rect_height
        )
        self.dashed_rectangle.setPen(pen)
        self.dashed_rectangle.setBrush(QBrush(Qt.transparent))  # Transparent fill
        # Add the rectangle to the scene
        self.shooting_scene.addItem(self.dashed_rectangle)

        # Add the view to the QStackedWidget
        self.stacked_widget.addWidget(self.shooting_view)

        # Disable scrollbars
        self.shooting_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.shooting_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def init_tetragon(
        self, tetragon_coords: list = [(100, 100), (200, 100), (200, 200), (100, 200)]
    ):
        # Generate the calibration scene
        self.calibration_scene = QGraphicsScene(self)
        self.calibration_scene.setSceneRect(
            0, 0, self.window_geometry[-2], self.window_geometry[-1]
        )

        # Generate the calibration view
        self.calibration_view = QGraphicsView(self.calibration_scene)
        self.calibration_view.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # Disable scrollbars
        self.calibration_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.calibration_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Add the tetragon to the calibration scene
        self.vertices = []
        for x, y in tetragon_coords:
            vertex = QGraphicsEllipseItem(0, 0, 10, 10)
            vertex.setBrush(Qt.red)
            vertex.setFlag(QGraphicsEllipseItem.ItemIsMovable)
            vertex.setPos(x, y)
            self.vertices.append(vertex)
            self.calibration_scene.addItem(vertex)
            print(f"Vertex added at: ({x}, {y})")  # Debugging statement

        print(
            f"Scene Rect: {self.calibration_scene.sceneRect()}"
        )  # Debugging statement

        # Mouse tracking
        self.calibration_view.installEventFilter(self)
        self.setMouseTracking(True)

        # Add the view to the QStackedWidget
        self.stacked_widget.addWidget(self.calibration_view)

    def initDrawingScene(self):
        # Initialize the drawing scene
        self.drawing_scene = QGraphicsScene()
        self.drawing_scene.setSceneRect(
            0, 0, self.window_geometry[-2], self.window_geometry[-1]
        )

        # Initialize the drawing view
        self.drawing_view = QGraphicsView(self.drawing_scene)
        self.drawing_view.setFixedSize(
            self.window_geometry[-2], self.window_geometry[-1]
        )

        # Disable scrollbars
        self.drawing_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.drawing_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Mouse tracking
        self.drawing_view.setMouseTracking(True)
        self.drawing_view.installEventFilter(self)
        self.drawing_view.viewport().installEventFilter(self)

        # Add a drawable pixmap item to the scene
        self.drawablePixmapItem = QGraphicsPixmapItem()
        self.drawing_scene.addItem(self.drawablePixmapItem)
        # Initialize the pixmap with a transparent background of the same size as the scene
        self.drawablePixmap = QPixmap(
            self.window_geometry[-2], self.window_geometry[-1]
        )
        self.drawablePixmap.fill(Qt.transparent)  # Fill with transparent color
        self.drawablePixmapItem.setPixmap(self.drawablePixmap)

        # Add the drawing view to the stacked widget
        self.stacked_widget.addWidget(self.drawing_view)

    def switchToDrawingScene(self):
        # Method to switch to the drawing scene
        self.stacked_widget.setCurrentWidget(self.drawing_view)

    def switch_to_shooting_scene(self):
        self.stacked_widget.setCurrentWidget(self.shooting_view)

    def switch_to_calibration_scene(self):
        self.stacked_widget.setCurrentWidget(self.calibration_view)

    def toggleDrawingScene(self):
        # Check which scene is currently active and switch to the other
        if self.stacked_widget.currentWidget() == self.drawing_view:
            self.switch_to_shooting_scene()  # Assuming this is the method to switch back to your original scene
        else:
            self.switchToDrawingScene()

    def clearDrawing(self):
        # Clear the drawing by filling the pixmap with transparent color
        self.drawablePixmap.fill(Qt.transparent)
        self.drawablePixmapItem.setPixmap(self.drawablePixmap)

        # Reset the traces
        self.drawingTraces = []
        self.currentTrace = []

    def get_coordinates(self):
        return [vertex.pos() for vertex in self.vertices]

    def create_tetragon(self, tetragon_coords):
        # Add the tetragon to the calibration scene
        self.vertices = []
        for x, y in tetragon_coords:
            vertex = QGraphicsEllipseItem(x - 5, y - 5, 10, 10)
            vertex.setBrush(Qt.red)
            vertex.setFlag(QGraphicsEllipseItem.ItemIsMovable)
            self.vertices.append(vertex)
            vertex.setVisible(True)  # Show the item
            self.calibration_scene.addItem(vertex)

    def update_vertices(self, new_coordinates):
        # Check if the lengths of vertices and new_coordinates match
        if len(self.vertices) != len(new_coordinates):
            print("Error: Mismatch in the number of vertices and new coordinates")
            return
        for vertex, (x, y) in zip(self.vertices, new_coordinates):
            vertex.setPos(x, y)
            print(f'vertex pos: {vertex.pos()}')

    def eventFilter(self, source, event):
        "The mouse movements do not work without this function"

        if event.type() == QMouseEvent.MouseButtonPress:
            if event.buttons() == Qt.LeftButton:
                self._left_click_hold = True
                if self.stacked_widget.currentWidget() == self.drawing_view:
                    self.drawing = True
                    self.lastPoint = event.pos()
                    point = event.pos()
                    if not self.drawing:
                        self.drawing = True
                    self.curr_shape_points.append(point)
                    self.update()
                elif self.stacked_widget.currentWidget() == self.shooting_view:
                    self._move_marker_and_update_sliders()

            elif event.buttons() == Qt.RightButton:
                self._right_click_hold = True
                self.photom_controls.photom_assembly.laser[0].toggle_emission = True
                print('right button pressed')

        elif event.type() == QMouseEvent.MouseMove:
            pass
            if self._left_click_hold:
                if source == self.shooting_view.viewport():
                    self._move_marker_and_update_sliders()
                elif self.drawing and source == self.drawing_view.viewport():
                    point = event.pos()
                    self.curr_shape_points.append(point)
                    self.update()

        elif event.type() == QMouseEvent.MouseButtonRelease:
            if event.button() == Qt.LeftButton:
                print('left button released')
                self._left_click_hold = False

                if self.drawing:
                    point = event.pos()
                    self.curr_shape_points.append(point)

                    self.curr_shape_points.append(
                        self.curr_shape_points[0]
                    )  # connecting the final points in case not connected
                    self.shapes[self.curr_shape_id] = ShapeTrace(self.curr_shape_points)
                    self.shapesUpdated.emit()

                    self.curr_shape_points = []
                    self.drawing = False
                    self.curr_shape_id += 1
                    self.update()
            elif event.button() == Qt.RightButton:
                self._right_click_hold = False
                self.photom_controls.photom_assembly.laser[0].toggle_emission = False
                if self.game_mode:
                    self._game_mode_marker(event)
                time.sleep(0.3)
                print('right button released')

        return super(LaserMarkerWindow, self).eventFilter(source, event)

    # Triggered after manual resizing or calling window.setGeometry()
    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        super().resizeEvent(a0)
        rect = self.shooting_view.sceneRect()
        self.shooting_scene.setSceneRect(0, 0, rect.width(), rect.height())
        self.drawing_scene.setSceneRect(0, 0, rect.width(), rect.height())
        self.drawing_view.setSceneRect(0, 0, rect.width(), rect.height())
        print(f'resize event: {rect.width()}, {rect.height()}')
        self._update_scene_items(rect.width(), rect.height())

    def remove_score_text(self, text_item):
        self.shooting_scene.removeItem(text_item)

    def _game_mode_marker(self, event: QMouseEvent):
        # Show "+100" at click position
        score_text = QGraphicsSimpleTextItem("+100")
        score_text.setBrush(QColor(255, 255, 0))  # Yellow color for visibility
        # Set a larger font size
        font = QFont()
        font.setPointSize(30)  # Set the font size to 24 points
        score_text.setFont(font)
        score_text.setPos(
            event.pos().x() + 15, event.pos().y() - 70
        )  # Position at click
        self.shooting_scene.addItem(score_text)
        # Create a QTimer to remove the "+100" after 1 second
        QTimer.singleShot(1000, lambda: self.remove_score_text(score_text))

    def _update_scene_items(self, new_width, new_height):
        # Dahsed rectangle
        rect_width = new_width * 2 / 3  # Example: 2/3 of the new width
        rect_height = new_height * 2 / 3  # Example: 2/3 of the new height
        rect_x = (new_width - rect_width) / 2
        rect_y = (new_height - rect_height) / 2

        # Re-center the "X" marker
        marker_center_x = new_width / 2
        marker_center_y = new_height / 2
        self.recenter_marker()

        # resize the rectangle
        self.dashed_rectangle.setRect(rect_x, rect_y, rect_width, rect_height)
        pen = QPen(
            QColor(0, 0, 0), 2, Qt.DashLine
        )  # Example: black color, width 2, dashed line
        self.dashed_rectangle.setPen(pen)
        self.shooting_view.update()

    def _move_marker_and_update_sliders(self):
        # Update the mirror slider values
        if self.photom_controls is not None:
            marker_position = self.get_marker_center(
                self.marker, coords=(self.marker.pos().x(), self.marker.pos().y())
            )
            # marker_position = [self.marker.pos().x(), self.marker.pos().y()]
            new_coords = self.photom_controls.mirror_widgets[
                self.photom_controls._current_mirror_idx
            ].mirror.affine_transform_obj.apply_affine(marker_position)
            self.photom_controls.mirror_widgets[
                self.photom_controls._current_mirror_idx
            ].mirror_x_slider.setValue(new_coords[0][0])
            self.photom_controls.mirror_widgets[
                self.photom_controls._current_mirror_idx
            ].mirror_y_slider.setValue(new_coords[1][0])

    def _roi_tracing(self, pattern_delay: float = 1.0):
        delay_secs = self.photom_controls.delay_input.text()
        if delay_secs:
            pattern_delay = float(delay_secs)
        else:
            pattern_delay = 1.0
        print(f"the time delay is {pattern_delay}")
        if self.selected_shape_id is not None:
            shape = self.shapes[self.selected_shape_id]
            new_ablation_points = []
            if shape.ablation_points:
                for position in shape.ablation_points:
                    new_coords = self.photom_controls.mirror_widgets[
                        self.photom_controls._current_mirror_idx
                    ].mirror.affine_transform_obj.apply_affine(position)

                    self.photom_controls.mirror_widgets[
                        self.photom_controls._current_mirror_idx
                    ].mirror_x_slider.setValue(new_coords[0][0])

                    self.photom_controls.mirror_widgets[
                        self.photom_controls._current_mirror_idx
                    ].mirror_y_slider.setValue(new_coords[1][0])

                    time.sleep(pattern_delay)
                    print(f"time: {datetime.now()}")
                    # QTimer.singleShot(int(3 * 1000), lambda: None)

                    new_ablation_points.append(new_coords)
            return new_ablation_points

    def get_marker_center(self, marker, coords=None):
        if coords is None:
            coords = (marker.pos().x(), marker.pos().y())

        # Adjust coordinates to account for sensor offset
        adjusted_coords = [
            coords[0]
            + self.sensor_offset_yx[1] * (self.fixed_width / self.sensor_size_yx[1]),
            coords[1]
            + self.sensor_offset_yx[0]
            * (self.window_geometry[3] / self.sensor_size_yx[0]),
        ]

        return adjusted_coords

    def display_marker_center(self, marker, coords=None):
        if coords is None:
            coords = (marker.pos().x(), marker.pos().y())
        center_x = coords[0] - marker.pixmap().width() / 2
        center_y = coords[1] - marker.pixmap().height() / 2
        marker.setPos(center_x, center_y)

    def closeEvent(self, event):
        self.windowClosed.emit()  # Emit the signal when the window is about to close
        super().closeEvent(event)  # Proceed with the default close event

    def draw_shapes(self) -> None:
        """draws all the shapes on the widget."""
        self.drawablePixmap.fill(Qt.transparent)
        painter = QPainter(self.drawablePixmap)
        for shape_id, shape in self.shapes.items():
            if shape_id == self.selected_shape_id:
                pen = QPen(Qt.red, 2, Qt.SolidLine)
            else:
                pen = QPen(Qt.black, 2, Qt.SolidLine)
            painter.setPen(pen)

            border_points = shape.border_points
            for i in range(len(border_points) - 1):
                painter.drawLine(border_points[i], border_points[i + 1])

        if self.drawing and len(self.curr_shape_points) > 1:
            pen = QPen(Qt.black, 2, Qt.SolidLine)
            painter.setPen(pen)
            for i in range(len(self.curr_shape_points) - 1):
                painter.drawLine(
                    self.curr_shape_points[i], self.curr_shape_points[i + 1]
                )
        painter.end()
        self.drawablePixmapItem.setPixmap(self.drawablePixmap)

    def draw_patterns(self) -> None:
        """draws all the patterns in the shapes on the widget."""
        painter = QPainter(self.drawablePixmap)
        brush = QBrush(Qt.green, Qt.SolidPattern)
        point_size = 5

        for shape_id, shape in self.shapes.items():
            if shape.ablation_points:
                ablation_points = shape.ablation_points
                for point in ablation_points:
                    point = QPoint(point[0], point[1])
                    painter.setBrush(brush)
                    painter.drawEllipse(point, point_size, point_size)
            if shape.pattern_points:
                pattern_points = shape.pattern_points
                for point in pattern_points:
                    pen = QPen(Qt.gray, 2, Qt.SolidLine)
                    painter.setPen(pen)
                    point = QPoint(point[0], point[1])
                    painter.drawPoint(point)
        painter.end()
        self.drawablePixmapItem.setPixmap(self.drawablePixmap)

    def paintEvent(self, event):
        self.draw_shapes()
        self.draw_patterns()


class ImageWindow(QMainWindow):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calibration Overlay of laser grid and MIP points")

        # Create a label and set its pixmap to the image at image_path
        self.label = QLabel(self)
        self.pixmap = QPixmap(image_path)

        # Resize the label to fit the pixmap
        self.label.setPixmap(self.pixmap)
        self.label.resize(self.pixmap.width(), self.pixmap.height())

        # Resize the window to fit the label (plus a little margin if desired)
        self.resize(
            self.pixmap.width() + 20, self.pixmap.height() + 20
        )  # Adding a 20-pixel margin

        # Optionally, center the window on the screen
        self.center()

    def center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos()
        )
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())
