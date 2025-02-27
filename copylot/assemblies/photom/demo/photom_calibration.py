import sys
from tokenize import Double
from matplotlib.pylab import f
import yaml
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QLabel,
    QSlider,
    QVBoxLayout,
    QGraphicsView,
    QGroupBox,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsItem,
    QGraphicsEllipseItem,
    QStackedWidget,
    QComboBox,
    QSpinBox,
    QFileDialog,
    QLineEdit,
    QGridLayout,
    QProgressBar,
    QGraphicsRectItem,
)
from PyQt5.QtGui import (
    QColor,
    QPen,
    QFont,
    QFontMetricsF,
    QMouseEvent,
    QBrush,
    QPixmap,
    QResizeEvent,
)
from pathlib import Path
from copylot.assemblies.photom.utils.scanning_algorithms import (
    calculate_rectangle_corners,
)
from copylot.assemblies.photom.gui.utils import DoubleSlider
import numpy as np
from copylot.assemblies.photom.photom import PhotomAssembly
from typing import Any, Tuple
import time

from copylot.hardware.cameras.flir.flir_camera import FlirCamera

# DEMO_MODE = True
DEMO_MODE = False

# TODO: deal with the logic when clicking calibrate. Mirror dropdown
# TODO: if camera is in use. unload it before calibrating
# TODO:make sure to update the affine_mat after calibration with the dimensions of laserwindow


class LaserWidget(QWidget):
    def __init__(self, laser):
        super().__init__()
        self.laser = laser

        self.emission_state = 0  # 0 = off, 1 = on
        self.emission_delay = 0  # 0 =off ,1= 5 sec delay

        self._curr_power = 0
        self._slider_decimal = 1
        self._curr_laser_pulse_mode = False

        self.initializer_laser()
        self.initialize_UI()

    def initializer_laser(self):
        # Set the power to 0
        self.laser.toggle_emission = 0
        self.laser.emission_delay = self.emission_delay
        self.laser.pulse_power = self._curr_power
        self.laser.power = self._curr_power

        # Make sure laser is in continuous mode
        if self.laser.pulse_mode == 1:
            self.laser.toggle_emission = 1
            time.sleep(0.2)
            self.laser.pulse_mode = self._curr_laser_pulse_mode ^ 1
            time.sleep(0.2)
            self.laser.toggle_emission = 0

    def initialize_UI(self):
        layout = QVBoxLayout()

        self.laser_label = QLabel(self.laser.name)
        layout.addWidget(self.laser_label)

        self.laser_power_slider = DoubleSlider(
            orientation=Qt.Horizontal, decimals=self._slider_decimal
        )
        self.laser_power_slider.setMinimum(0)
        self.laser_power_slider.setMaximum(100)
        self.laser_power_slider.setValue(self.laser.power)
        self.laser_power_slider.valueChanged.connect(self.update_power)
        layout.addWidget(self.laser_power_slider)

        # Add a QLabel to display the power value
        self.power_edit = QLineEdit(f"{self._curr_power:.2f}")  # Changed to QLineEdit
        self.power_edit.returnPressed.connect(
            self.edit_power
        )  # Connect the returnPressed signal
        layout.addWidget(self.power_edit)

        # Set Pulse Mode Button
        self.pulse_mode_button = QPushButton("Pulse Mode")
        self.pulse_mode_button.clicked.connect(self.laser_pulse_mode)
        layout.addWidget(self.pulse_mode_button)
        self.pulse_mode_button.setStyleSheet("background-color: magenta")

        self.laser_toggle_button = QPushButton("Toggle")
        self.laser_toggle_button.clicked.connect(self.toggle_laser)
        # make it background red if laser is off
        if self.emission_state == 0:
            self.laser_toggle_button.setStyleSheet("background-color: magenta")
        layout.addWidget(self.laser_toggle_button)

        self.setLayout(layout)

    def toggle_laser(self):
        self.emission_state = self.emission_state ^ 1
        self.laser.toggle_emission = self.emission_state
        if self.emission_state == 0:
            self.laser_toggle_button.setStyleSheet("background-color: magenta")
        else:
            self.laser_toggle_button.setStyleSheet("background-color: green")

    def update_power(self, value):
        self._curr_power = value / (10**self._slider_decimal)
        if self._curr_laser_pulse_mode:
            self.laser.pulse_power = self._curr_power
        else:
            self.laser.power = self._curr_power

        # Update the QLabel with the new power value
        self.power_edit.setText(f"{self._curr_power:.2f}")

    def edit_power(self):
        try:
            # Extract the numerical value from the QLineEdit text
            power_value_str = self.power_edit.text()
            power_value = float(power_value_str)

            if (
                0 <= power_value <= 100
            ):  # Assuming the power range is 0 to 100 percentages
                self._curr_power = power_value
                self.laser.power = self._curr_power
                self.laser_power_slider.setValue(self._curr_power)
                self.power_edit.setText(f"{self._curr_power:.2f}")
            else:
                self.power_edit.setText(f"{self._curr_power:.2f}")
            print(f"Power: {self._curr_power}")
        except ValueError:
            self.power_edit.setText(f"{self._curr_power:.2f}")

    def laser_pulse_mode(self):
        self._curr_laser_pulse_mode = not self._curr_laser_pulse_mode
        self.laser.toggle_emission = 1
        if self._curr_laser_pulse_mode:
            self.pulse_mode_button.setStyleSheet("background-color: green")
            self.laser.pulse_power = self._curr_power
            self.laser.pulse_mode = 1
            time.sleep(0.2)
        else:
            self.laser.power = self._curr_power
            self.laser.pulse_mode = 0
            self.pulse_mode_button.setStyleSheet("background-color: magenta")
            time.sleep(0.2)
            self.laser_toggle_button.setStyleSheet("background-color: magenta")
            self.laser.toggle_emission = 0
            self.emission_state = 0

        print(f'pulse mode bool: {self._curr_laser_pulse_mode}')
        print(f'digital modulation = {self.laser.pulse_mode}')


# TODO: connect widget to actual abstract mirror calls
class MirrorWidget(QWidget):
    def __init__(self, mirror):
        super().__init__()
        self.mirror = mirror

        self.check_mirror_limits()
        self.initialize_UI()

    def initialize_UI(self):
        layout = QVBoxLayout()

        mirror_x_label = QLabel("Mirror X Position")
        layout.addWidget(mirror_x_label)

        self.mirror_x_slider = DoubleSlider(orientation=Qt.Horizontal)
        self.mirror_x_slider.setMinimum(self.movement_limits_x[0])
        self.mirror_x_slider.setMaximum(self.movement_limits_x[1])
        self.mirror_x_slider.doubleValueChanged.connect(self.update_mirror_x)
        layout.addWidget(self.mirror_x_slider)

        # Add a QLabel to display the mirror X value
        self.mirror_x_label = QLabel(f"X: {self.mirror.position_x}")
        layout.addWidget(self.mirror_x_label)

        mirror_y_label = QLabel("Mirror Y Position")
        layout.addWidget(mirror_y_label)

        self.mirror_y_slider = DoubleSlider(orientation=Qt.Horizontal)
        self.mirror_y_slider.setMinimum(self.movement_limits_y[0])
        self.mirror_y_slider.setMaximum(self.movement_limits_y[1])
        self.mirror_y_slider.doubleValueChanged.connect(self.update_mirror_y)
        layout.addWidget(self.mirror_y_slider)

        # Add a QLabel to display the mirror Y value
        self.mirror_y_label = QLabel(f"Y: {self.mirror.position_y}")
        layout.addWidget(self.mirror_y_label)

        self.setLayout(layout)

    def update_mirror_x(self, value):
        self.mirror.position_x = value
        # Update the QLabel with the new X value
        self.mirror_x_label.setText(f"X: {value}")

    def update_mirror_y(self, value):
        self.mirror.position_y = value
        # Update the QLabel with the new Y value
        self.mirror_y_label.setText(f"Y: {value}")

    def check_mirror_limits(self):
        movement_limits = self.mirror.movement_limits
        self.movement_limits_x = movement_limits[0:2]
        self.movement_limits_y = movement_limits[2:4]


class ArduinoPWMWidget(QWidget):
    def __init__(self, photom_assembly, arduino_pwm, parent):
        super().__init__()
        self.parent = parent
        self.arduino_pwm = arduino_pwm
        self.photom_assembly = photom_assembly
        # default values
        self.duty_cycle = 50  # [%] (0-100)
        self.time_period_ms = 100  # [ms]
        self.frequency = 1000.0 / self.time_period_ms  # [Hz]
        self.duration = 5000  # [ms]
        self.repetitions = 1  # By default it runs once
        self.time_interval_s = 0  # [s]

        self.command = f"U,{self.duty_cycle},{self.frequency},{self.duration}"

        self._curr_laser_idx = 0

        self.initialize_UI()

    def initialize_UI(self):
        layout = QGridLayout()  # Use QGridLayout

        # Laser Dropdown Menu
        self.laser_dropdown = QComboBox()
        for laser in self.photom_assembly.laser:
            self.laser_dropdown.addItem(laser.name)
        layout.addWidget(QLabel("Select Laser:"), 0, 0)
        layout.addWidget(self.laser_dropdown, 0, 1)
        self.laser_dropdown.setCurrentIndex(self._curr_laser_idx)
        self.laser_dropdown.currentIndexChanged.connect(self.current_laser_changed)

        # Duty Cycle
        layout.addWidget(QLabel("Duty Cycle [%]:"), 1, 0)
        self.duty_cycle_edit = QLineEdit(f"{self.duty_cycle}")
        self.duty_cycle_edit.returnPressed.connect(self.edit_duty_cycle)
        layout.addWidget(self.duty_cycle_edit, 1, 1)

        # Time Period
        layout.addWidget(QLabel("Time Period [ms]:"), 2, 0)
        self.time_period_edit = QLineEdit(f"{self.time_period_ms}")
        self.time_period_edit.returnPressed.connect(self.edit_time_period)
        layout.addWidget(self.time_period_edit, 2, 1)

        # Duration
        layout.addWidget(QLabel("Duration [ms]:"), 3, 0)
        self.duration_edit = QLineEdit(f"{self.duration}")
        self.duration_edit.returnPressed.connect(self.edit_duration)
        layout.addWidget(self.duration_edit, 3, 1)

        # Repetitions
        layout.addWidget(QLabel("Repetitions:"), 4, 0)
        self.repetitions_edit = QLineEdit(f"{self.repetitions}")
        self.repetitions_edit.textChanged.connect(self.edit_repetitions)
        layout.addWidget(self.repetitions_edit, 4, 1)

        # Time interval
        layout.addWidget(QLabel("Time interval [s]:"), 5, 0)
        self.time_interval_edit = QLineEdit(f"{self.time_interval_s}")
        self.time_interval_edit.textChanged.connect(self.edit_time_interval)
        layout.addWidget(self.time_interval_edit, 5, 1)

        # Apply Button
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        layout.addWidget(self.apply_button, 6, 0, 1, 2)

        # Start Button
        self.start_button = QPushButton("Start PWM")
        self.start_button.clicked.connect(self.start_pwm)
        layout.addWidget(self.start_button, 7, 0, 1, 2)

        # Add Stop Button
        self.stop_button = QPushButton("Stop PWM")
        self.stop_button.clicked.connect(self.stop_pwm)
        layout.addWidget(self.stop_button, 8, 0, 1, 2)  # Adjust position as needed

        # Add Progress Bar
        self.progressBar = QProgressBar(self)
        self.progressBar.setMaximum(100)  # Set the maximum value
        layout.addWidget(self.progressBar, 9, 0, 1, 2)  # Adjust position as needed

        self.setLayout(layout)

    def edit_duty_cycle(self):
        try:
            value = float(self.duty_cycle_edit.text())
            self.duty_cycle = value
            self.update_command()
        except ValueError:
            self.duty_cycle_edit.setText(f"{self.duty_cycle}")

    def edit_time_period(self):
        try:
            value = float(self.time_period_edit.text())
            self.time_period_ms = value
            self.frequency = 1000.0 / self.time_period_ms
            self.update_command()
        except ValueError:
            self.time_period_edit.setText(f"{self.time_period}")

    def edit_duration(self):
        try:
            value = float(self.duration_edit.text())
            self.duration = value
            self.update_command()
        except ValueError:
            self.duration_edit.setText(f"{self.duration}")

    def edit_repetitions(self):
        try:
            value = int(self.repetitions_edit.text())
            self.repetitions = value
        except ValueError:
            self.repetitions_edit.setText(
                f"{self.repetitions}"
            )  # Reset to last valid value

    def edit_time_interval(self):
        try:
            value = float(self.time_interval_edit.text())
            self.time_interval_s = value
        except ValueError:
            self.time_interval_edit.setText(
                f"{self.time_interval_s}"
            )  # Reset to last valid value

    def update_command(self):
        self.command = f"U,{self.duty_cycle},{self.frequency},{self.duration}"
        print(f"arduino out: {self.command}")
        self.arduino_pwm.send_command(self.command)

    def start_pwm(self):
        if not self.parent.laser_widgets[self._curr_laser_idx]._curr_laser_pulse_mode:
            print('Setup laser as pulse mode...')
            self.parent.laser_widgets[self._curr_laser_idx].laser_pulse_mode()

        print("Starting PWM...")
        self.pwm_worker = PWMWorker(
            self.arduino_pwm,
            'S',
            self.repetitions,
            self.time_interval_s,
            self.duration,
        )
        # Rest Progress Bar
        self.progressBar.setValue(0)
        self.pwm_worker.finished.connect(self.on_pwm_finished)
        self.pwm_worker.progress.connect(self.update_progress_bar)
        self.pwm_worker.start()

    def update_progress_bar(self, value):
        self.progressBar.setValue(value)  # Update the progress bar with the new value

    def stop_pwm(self):
        if hasattr(self, 'pwm_worker') and self.pwm_worker.isRunning():
            self.pwm_worker.request_stop()

    def on_pwm_finished(self):
        print("PWM operation completed.")
        # self.progressBar.setValue(0)  # Reset the progress bar

    def current_laser_changed(self, index):
        self._curr_laser_idx = index
        self.apply_settings()

    def apply_settings(self):
        # Implement functionality to apply settings to the selected laser
        self._curr_laser_idx = self.laser_dropdown.currentIndex()
        # TODO: Need to modify the data struct for command for multiple lasers
        if hasattr(self, 'command'):
            self.arduino_pwm.send_command(self.command)


class PhotomApp(QMainWindow):
    def __init__(
        self,
        photom_assembly: PhotomAssembly,
        photom_sensor_size_yx: Tuple[int, int] = (2048, 2448),
        photom_window_size_x: int = 800,
        photom_window_pos: Tuple[int, int] = (100, 100),
        demo_window=None,
        arduino=[],
    ):
        super().__init__()
        # TODO:temporary for arduino. remove when we replace with dac
        self.arduino_pwm = arduino

        self.photom_window = None
        self.photom_controls_window = None

        self.photom_assembly = photom_assembly
        self.lasers = self.photom_assembly.laser
        self.mirrors = self.photom_assembly.mirror
        self.photom_window_size_x = photom_window_size_x
        self.photom_sensor_size_yx = photom_sensor_size_yx
        self.photom_window_pos = photom_window_pos
        self._current_mirror_idx = 0
        self._laser_window_transparency = 0.7
        self.scaling_matrix = np.eye(3)
        self.T_mirror_cam_matrix = np.eye(3)
        self.calibration_thread = CalibrationThread(
            self.photom_assembly, self._current_mirror_idx
        )
        self.calibration_w_cam_thread = CalibrationWithCameraThread(
            self.photom_assembly, self._current_mirror_idx
        )
        self.calibration_w_cam_thread.finished.connect(self.done_calibration)
        self.imageWindows = []
        if DEMO_MODE:
            self.demo_window = demo_window

        self.initializer_laser_marker_window()
        self.initialize_UI()

    def initializer_laser_marker_window(self):
        # Making the photom_window a square and display right besides the control UI
        window_pos = (
            self.photom_window_size_x + self.photom_window_pos[0],
            self.photom_window_pos[1],
        )
        self.photom_window = LaserMarkerWindow(
            photom_controls=self,
            name='Laser Marker',
            sensor_size_yx=self.photom_sensor_size_yx,
            fixed_width=self.photom_window_size_x,
            window_pos=window_pos,
        )
        self.aspect_ratio = (
            self.photom_sensor_size_yx[1] / self.photom_sensor_size_yx[0]
        )
        calculated_height = self.photom_window_size_x / self.aspect_ratio
        self.scaling_factor_x = (
            self.photom_sensor_size_yx[1] / self.photom_window_size_x
        )
        self.scaling_factor_y = self.photom_sensor_size_yx[0] / calculated_height
        # TODO: the affine transforms are in XY coordinates. Need to change to YX
        self.scaling_matrix = np.array(
            [[self.scaling_factor_x, 0, 1], [0, self.scaling_factor_y, 1], [0, 0, 1]]
        )
        self.photom_window.windowClosed.connect(
            self.closeAllWindows
        )  # Connect the signal to slot

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

        # Adding slider to adjust transparency
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
        self.resize_spinbox.setRange(50, 200)  # Set range from 50% to 200%
        self.resize_spinbox.setSuffix("%")  # Add a percentage sign as suffix
        self.resize_spinbox.setValue(100)  # Default value is 100%
        self.resize_spinbox.valueChanged.connect(self.resize_laser_marker_window)
        self.resize_spinbox.editingFinished.connect(self.resize_laser_marker_window)
        transparency_layout.addWidget(QLabel("Resize Window:"))
        transparency_layout.addWidget(self.resize_spinbox)

        # Set the transparency group layout
        transparency_group.setLayout(transparency_layout)

        # Adding a group box for the lasers
        laser_group = QGroupBox("Lasers")
        laser_layout = QVBoxLayout()
        self.laser_widgets = []
        for laser in self.lasers:
            laser_widget = LaserWidget(laser)
            self.laser_widgets.append(laser_widget)
            laser_layout.addWidget(laser_widget)
        laser_group.setLayout(laser_layout)

        # Adding a group box for the mirror
        mirror_group = QGroupBox("Mirror")
        mirror_layout = QVBoxLayout()

        self.mirror_widgets = []
        for idx, mirror in enumerate(self.mirrors):
            mirror_widget = MirrorWidget(mirror)
            self.mirror_widgets.append(mirror_widget)
            mirror_layout.addWidget(mirror_widget)
        mirror_group.setLayout(mirror_layout)

        # TODO remove if arduino is removed
        # Adding group for arduino PWM
        arduino_group = QGroupBox("Arduino PWM")
        arduino_layout = QVBoxLayout()
        self.arduino_pwm_widgets = []
        for arduino in self.arduino_pwm:
            arduino_pwm_widget = ArduinoPWMWidget(self.photom_assembly, arduino, self)
            self.arduino_pwm_widgets.append(arduino_pwm_widget)
            arduino_layout.addWidget(arduino_pwm_widget)
        arduino_group.setLayout(arduino_layout)

        # Add the laser and mirror group boxes to the main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(transparency_group)
        main_layout.addWidget(laser_group)
        main_layout.addWidget(mirror_group)
        main_layout.addWidget(arduino_group)  # TODO remove if arduino is removed

        self.mirror_dropdown = QComboBox()
        self.mirror_dropdown.addItems([mirror.name for mirror in self.mirrors])
        main_layout.addWidget(self.mirror_dropdown)
        self.mirror_dropdown.setCurrentIndex(self._current_mirror_idx)
        self.mirror_dropdown.currentIndexChanged.connect(self.mirror_dropdown_changed)

        self.recenter_marker_button = QPushButton("Recenter Marker")
        self.recenter_marker_button.clicked.connect(self.recenter_marker)
        main_layout.addWidget(self.recenter_marker_button)

        self.calibrate_button = QPushButton("Calibrate")
        self.calibrate_button.clicked.connect(self.calibrate_w_camera)
        main_layout.addWidget(self.calibrate_button)

        self.load_calibration_button = QPushButton("Load Calibration")
        self.load_calibration_button.clicked.connect(self.load_calibration)
        main_layout.addWidget(self.load_calibration_button)

        # Add a "Cancel Calibration" button (initially hidden)
        self.cancel_calibration_button = QPushButton("Cancel Calibration")
        self.cancel_calibration_button.clicked.connect(self.cancel_calibration)
        self.cancel_calibration_button.hide()
        main_layout.addWidget(self.cancel_calibration_button)
        main_widget = QWidget(self)
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)
        self.show()

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
            [[self.scaling_factor_x, 0, 1], [0, self.scaling_factor_y, 1], [0, 0, 1]]
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
        print("Calibrating with camera...")
        # Hide the calibrate button
        self.calibrate_button.hide()
        self.load_calibration_button.hide()
        # Show the "Cancel Calibration" button
        self.cancel_calibration_button.show()
        if DEMO_MODE:
            print(f'Calibrating mirror: {self._current_mirror_idx}')
        else:
            # TODO: Hardcoding the camera and coordinates of mirror for calib. Change this after
            self.setup_calibration()
            self.photom_assembly.mirror[
                self._current_mirror_idx
            ].affine_transform_obj.reset_T_affine()
            self.calibration_w_cam_thread.start()

    # TODO: these parameters are currently hardcoded
    def setup_calibration(self):
        # Open the camera and add it to the assembly
        cam = FlirCamera()
        cam.open()
        self.photom_assembly.camera = [cam]

        self.photom_assembly.laser[0].power = 0.0
        self.photom_assembly.laser[0].toggle_emission = True
        self.photom_assembly.laser[0].power = 30.0

    def load_calibration(self):
        self.photom_assembly._calibrating = False
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

    def cancel_calibration(self):
        # Implement your cancel calibration function here
        print("Canceling calibration...")
        # Show the "Calibrate" button
        self.calibrate_button.show()
        self.load_calibration_button.show()
        # Show the "X" marker in photom_window
        self.photom_window.marker.show()

        self.cancel_calibration_button.hide()
        # Switch back to the shooting scene
        self.photom_window.switch_to_shooting_scene()

    def display_saved_plot(self, plot_path):
        # This function assumes that a QApplication instance is already running
        image_window = ImageWindow(plot_path)
        image_window.show()
        self.imageWindows.append(image_window)
        # return image_window

    def done_calibration(self, T_affine, plot_save_path):
        # Unload the camera
        self.photom_assembly.camera[0].close()
        self.photom_assembly.camera = []

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

            # Hide the "Done Calibration" button
            self.calibrate_button.show()
            self.cancel_calibration_button.hide()

            # Update the affine to match the photom laser window
            self.update_laser_window_affine()

            if DEMO_MODE:
                NotImplementedError("Demo Mode: Calibration not implemented yet.")
        else:
            print("No file selected. Skiping Saving the calibration matrix.")
            # Show dialog box saying no file selected
        print("Calibration done")

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
            [[self.scaling_factor_x, 0, 1], [0, self.scaling_factor_y, 1], [0, 0, 1]]
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

    def display_rectangle(self):
        self.photom_window.switch_to_calibration_scene()

    def closeEvent(self, event):
        self.closeAllWindows()  # Ensure closing main window closes everything
        super().closeEvent(event)

    def closeAllWindows(self):
        self.photom_window.close()
        self.close()
        QApplication.quit()  # Quit the application


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


class PWMWorker(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(int)  # Signal to report progress
    _stop_requested = False

    def request_stop(self):
        self._stop_requested = True

    def __init__(self, arduino_pwm, command, repetitions, time_interval_s, duration):
        super().__init__()
        self.arduino_pwm = arduino_pwm
        self.command = command
        self.repetitions = repetitions
        self.time_interval_s = time_interval_s
        self.duration = duration

    def run(self):
        # Simulate sending the command and waiting (replace with actual logic)
        for i in range(self.repetitions):
            if self._stop_requested:
                break
            self.arduino_pwm.send_command(self.command)
            # TODO: replace when using a better microcontroller since we dont get signals back rn
            time.sleep(self.duration / 1000)
            self.progress.emit(int((i + 1) / self.repetitions * 100))
            time.sleep(self.time_interval_s)  # Simulate time interval

        self.finished.emit()


class CalibrationThread(QThread):
    finished = pyqtSignal()

    def __init__(self, photom_assembly, current_mirror_idx):
        super().__init__()
        self.photom_assembly = photom_assembly
        self.current_mirror_idx = current_mirror_idx

    def run(self):
        self.photom_assembly.calibrate(
            self.current_mirror_idx,
            rectangle_size_xy=self.photom_assembly._calibration_rectangle_size_xy,
            center=[0.000, 0.000],
        )


class CalibrationWithCameraThread(QThread):
    finished = pyqtSignal(np.ndarray, str)

    def __init__(self, photom_assembly, current_mirror_idx):
        super().__init__()
        self.photom_assembly = photom_assembly
        self.current_mirror_idx = current_mirror_idx

    def run(self):
        # TODO: hardcoding the camera for now
        mirror_roi = [[-0.01, 0.0], [0.015, 0.018]]  # [x,y]
        T_mirror_cam_matrix, plot_save_path = self.photom_assembly.calibrate_w_camera(
            mirror_index=self.current_mirror_idx,
            camera_index=0,
            rectangle_boundaries=mirror_roi,
            grid_n_points=5,
            # config_file="calib_config.yml",
            save_calib_stack_path=r"C:\Users\ZebraPhysics\Documents\tmp\test_calib",
            verbose=True,
        )
        self.finished.emit(T_mirror_cam_matrix, str(plot_save_path))


class LaserMarkerWindow(QMainWindow):
    windowClosed = pyqtSignal()  # Define the signal

    def __init__(
        self,
        photom_controls: QMainWindow = None,
        name="Laser Marker",
        sensor_size_yx: Tuple = (2048, 2048),
        window_pos: Tuple = (100, 100),
        fixed_width: int = 800,
    ):
        super().__init__()
        self.photom_controls = photom_controls
        self.window_name = name
        self.aspect_ratio = sensor_size_yx[1] / sensor_size_yx[0]
        self.fixed_width = fixed_width
        calculated_height = int(self.fixed_width / self.aspect_ratio)
        self.window_pos = window_pos
        self.window_geometry = self.window_pos + (self.fixed_width, calculated_height)
        self.setMouseTracking(True)
        self.setWindowOpacity(self.photom_controls._laser_window_transparency)

        # Create a QStackedWidget
        # TODO: do we need the stacked widget?
        self.stacked_widget = QStackedWidget()
        # Set the QStackedWidget as the central widget
        self.initialize_UI()
        self.initMarker()

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
        self.setCentralWidget(self.shooting_view)
        self.shooting_view.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.shooting_view.setFixedSize(
            self.window_geometry[-2], self.window_geometry[-1]
        )

        # Mouse tracking
        self.shooting_view.installEventFilter(self)
        self.setMouseTracking(True)
        self.marker = QGraphicsSimpleTextItem("+")
        self.marker.setBrush(QColor(255, 0, 0))
        self.marker.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.shooting_view.viewport().installEventFilter(self)
        # Set larger font size
        font = self.marker.font()
        font.setPointSize(30)
        self.marker.setFont(font)

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

    def switch_to_shooting_scene(self):
        self.stacked_widget.setCurrentWidget(self.shooting_view)

    def switch_to_calibration_scene(self):
        self.stacked_widget.setCurrentWidget(self.calibration_view)

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
        if event.type() == QMouseEvent.MouseMove:
            pass
            if self._left_click_hold:
                # Move the mirror around if the left button is clicked
                self._move_marker_and_update_sliders()
            # Debugging statements
            # print('mouse move')
            # print(f'x1: {event.screenPos().x()}, y1: {event.screenPos().y()}')
            # print(f'x: {event.posF().x()}, y: {event.posF().y()}')
            # print(f'x: {event.localPosF().x()}, y: {event.localPosF().y()}')
            # print(f'x: {event.windowPosF().x()}, y: {event.windowPosF().y()}')
            # print(f'x: {event.screenPosF().x()}, y: {event.screenPosF().y()}')
            # print(f'x: {event.globalPosF().x()}, y: {event.globalPosF().y()}')
            # print(f'x2: {event.pos().x()}, y2: {event.pos().y()}')
        elif event.type() == QMouseEvent.MouseButtonPress:
            print('mouse button pressed')
            print('shooting mode')
            if event.buttons() == Qt.LeftButton:
                self._left_click_hold = True
                print('left button pressed')
                print(f'x2: {event.pos().x()}, y2: {event.pos().y()}')
                self._move_marker_and_update_sliders()
            elif event.buttons() == Qt.RightButton:
                self._right_click_hold = True
                self.photom_controls.photom_assembly.laser[0].toggle_emission = True
                print('right button pressed')
        elif event.type() == QMouseEvent.MouseButtonRelease:
            print('mouse button released')
            if event.button() == Qt.LeftButton:
                print('left button released')
                self._left_click_hold = False
            elif event.button() == Qt.RightButton:
                self._right_click_hold = False
                self.photom_controls.photom_assembly.laser[0].toggle_emission = False
                time.sleep(0.5)
                print('right button released')

        return super(LaserMarkerWindow, self).eventFilter(source, event)

    # Triggered after manual resizing or calling window.setGeometry()
    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        super().resizeEvent(a0)
        rect = self.shooting_view.sceneRect()
        self.shooting_scene.setSceneRect(0, 0, rect.width(), rect.height())
        print(f'resize event: {rect.width()}, {rect.height()}')
        self._update_scene_items(rect.width(), rect.height())

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
            marker_position = [self.marker.pos().x(), self.marker.pos().y()]
            new_coords = self.photom_controls.mirror_widgets[
                self.photom_controls._current_mirror_idx
            ].mirror.affine_transform_obj.apply_affine(marker_position)
            self.photom_controls.mirror_widgets[
                self.photom_controls._current_mirror_idx
            ].mirror_x_slider.setValue(new_coords[0][0])
            self.photom_controls.mirror_widgets[
                self.photom_controls._current_mirror_idx
            ].mirror_y_slider.setValue(new_coords[1][0])

    def display_marker_center(self, marker, coords=None):
        if coords is None:
            coords = (marker.x(), marker.y())
        # Obtain font metrics and bounding rectangle
        fm = QFontMetricsF(marker.font())
        boundingRect = fm.tightBoundingRect(marker.text())

        # Adjust position based on the bounding rectangle
        adjustedX = coords[0] - boundingRect.width() / 2
        adjustedY = coords[1] - boundingRect.height() / 2

        marker.setPos(adjustedX, adjustedY)

    def closeEvent(self, event):
        self.windowClosed.emit()  # Emit the signal when the window is about to close
        super().closeEvent(event)  # Proceed with the default close event


if __name__ == "__main__":
    import os

    # TODO: grab the actual value if the camera is connected to photom_assmebly
    CAMERA_SENSOR_YX = (2048, 2448)

    if DEMO_MODE:
        from copylot.assemblies.photom.photom_mock_devices import (
            MockLaser,
            MockMirror,
            MockArduinoPWM,
        )

        Laser = MockLaser
        Mirror = MockMirror
        ArduinoPWM = MockArduinoPWM
    else:
        from copylot.hardware.mirrors.optotune.mirror import OptoMirror as Mirror
        from copylot.hardware.lasers.vortran.vortran import VortranLaser as Laser
        from copylot.assemblies.photom.utils.arduino import ArduinoPWM as ArduinoPWM

    config_path = r"./copylot/assemblies/photom/demo/photom_VIS_config.yml"

    # TODO: this should be a function that parses the config_file and returns the photom_assembly
    # Load the config file and parse it
    with open(config_path, "r") as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)
        lasers = [
            Laser(
                name=laser_data["name"],
                port=laser_data["COM_port"],
            )
            for laser_data in config["lasers"]
        ]
        mirrors = [
            Mirror(
                name=mirror_data["name"],
                com_port=mirror_data["COM_port"],
                pos_x=mirror_data["x_position"],
                pos_y=mirror_data["y_position"],
            )
            for mirror_data in config["mirrors"]
        ]  # Initial mirror position
        affine_matrix_paths = [
            mirror['affine_matrix_path'] for mirror in config['mirrors']
        ]
        arduino = [ArduinoPWM(serial_port='COM10', baud_rate=115200)]

        # Check that the number of mirrors and affine matrices match
        assert len(mirrors) == len(affine_matrix_paths)

    # Load photom assembly
    photom_assembly = PhotomAssembly(
        laser=lasers, mirror=mirrors, affine_matrix_path=affine_matrix_paths
    )

    # QT APP
    app = QApplication(sys.argv)

    # Define the positions and sizes for the windows
    screen_width = app.desktop().screenGeometry().width()
    screen_height = app.desktop().screenGeometry().height()
    ctrl_window_width = screen_width // 3  # Adjust the width as needed
    ctrl_window_height = screen_height // 3  # Use the full screen height

    if DEMO_MODE:
        camera_window = LaserMarkerWindow(
            name="Mock laser dots",
            sensor_size_yx=(2048, 2048),
            window_pos=(100, 100),
            fixed_width=ctrl_window_width,
        )  # Set the positions of the windows
        ctrl_window = PhotomApp(
            photom_assembly=photom_assembly,
            photom_sensor_size_yx=CAMERA_SENSOR_YX,
            photom_window_size_x=ctrl_window_width,
            photom_window_pos=(100, 100),
            demo_window=camera_window,
            arduino=arduino,
        )
        # Set the camera window to the calibration scene
        camera_window.switch_to_calibration_scene()
        rectangle_scaling = 0.2
        window_size = (camera_window.width(), camera_window.height())
        rectangle_size = (
            (window_size[0] * rectangle_scaling),
            (window_size[1] * rectangle_scaling),
        )
        rectangle_coords = calculate_rectangle_corners(rectangle_size)
        # translate each coordinate by the offset
        rectangle_coords = [(x + 30, y) for x, y in rectangle_coords]
        camera_window.update_vertices(rectangle_coords)
    else:
        # Set the positions of the windows
        ctrl_window = PhotomApp(
            photom_assembly=photom_assembly,
            photom_sensor_size_yx=CAMERA_SENSOR_YX,
            photom_window_size_x=ctrl_window_width,
            photom_window_pos=(100, 100),
            arduino=arduino,
        )

    sys.exit(app.exec_())
