import sys
import yaml
from PyQt5.QtCore import Qt
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
    QFileDialog,
    QLineEdit,
    QGridLayout,
)
from PyQt5.QtGui import QColor, QPen, QFont, QFontMetricsF, QMouseEvent
from copylot.assemblies.photom.utils.scanning_algorithms import (
    calculate_rectangle_corners,
)
import numpy as np
from copylot.assemblies.photom.photom import PhotomAssembly
from typing import Tuple

DEMO_MODE = True

# TODO: deal with the logic when clicking calibrate. Mirror dropdown
# TODO: check that the calibration step is implemented properly.
# TODO: connect marker to actual mirror position. Unclear why it's not working.


class LaserWidget(QWidget):
    def __init__(self, laser):
        super().__init__()
        self.laser = laser

        self.emission_state = 0  # 0 = off, 1 = on

        self.initializer_laser()
        self.initialize_UI()

    def initializer_laser(self):
        self.laser.toggle_emission = self.emission_state

    def initialize_UI(self):
        layout = QVBoxLayout()

        self.laser_label = QLabel(self.laser.name)
        layout.addWidget(self.laser_label)

        self.laser_power_slider = QSlider(Qt.Horizontal)
        self.laser_power_slider.setMinimum(0)
        self.laser_power_slider.setMaximum(100)
        self.laser_power_slider.setValue(self.laser.laser_power)
        self.laser_power_slider.valueChanged.connect(self.update_power)
        layout.addWidget(self.laser_power_slider)

        # Add a QLabel to display the power value
        self.power_edit = QLineEdit(f"{self.laser.laser_power}")  # Changed to QLineEdit
        self.power_edit.returnPressed.connect(
            self.edit_power
        )  # Connect the returnPressed signal
        layout.addWidget(self.power_edit)

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
        self.laser.laser_power = value
        # Update the QLineEdit with the new power value
        self.power_edit.setText(f"{value:.2f}")  # Use string formatting for float

    def edit_power(self):
        try:
            # Convert the text value to float
            value = float(self.power_edit.text())
            if 0 <= value <= 100:  # Assuming the power range is 0 to 100
                self.laser.laser_power = value
                self.laser_power_slider.setValue(
                    int(value)
                )  # Synchronize the slider position, may need adjustment for float handling
                self.power_edit.setText(f"{value:.2f}")
            else:
                self.power_edit.setText(
                    f"{self.laser.laser_power:.2f}"
                )  # Reset to the last valid value if out of bounds
        except ValueError:
            # If conversion fails, reset QLineEdit to the last valid value
            self.power_edit.setText(f"{self.laser.laser_power:.2f}")


class QDoubleSlider(QSlider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._multiplier = 1000

    def value(self):
        return super().value() / self._multiplier

    def setValue(self, val):
        super().setValue(int(val * self._multiplier))

    def setMinimum(self, val):
        super().setMinimum(int(val * self._multiplier))

    def setMaximum(self, val):
        super().setMaximum(int(val * self._multiplier))


class ArduinoPWMWidget(QWidget):
    def __init__(self, arduino_pwm):
        super().__init__()
        self.arduino_pwm = arduino_pwm

        # default values
        self.duty_cycle = 50  # [%] (0-100)
        self.frequency = 1000  # [Hz]
        self.duration = 5000  # [ms]

        self.initialize_UI()

    def initialize_UI(self):
        layout = QGridLayout()  # Use QGridLayout

        # Duty Cycle
        layout.addWidget(QLabel("Duty Cycle [%]:"), 0, 0)  # Label for duty cycle
        self.duty_cycle_slider = QDoubleSlider(Qt.Horizontal)
        self.duty_cycle_slider.setMinimum(0)
        self.duty_cycle_slider.setMaximum(100)
        self.duty_cycle_slider.setValue(self.duty_cycle)
        self.duty_cycle_slider.valueChanged.connect(self.update_duty_cycle)
        layout.addWidget(self.duty_cycle_slider, 0, 1)
        self.duty_cycle_edit = QLineEdit(f"{self.duty_cycle}")
        self.duty_cycle_edit.returnPressed.connect(self.edit_duty_cycle)
        layout.addWidget(self.duty_cycle_edit, 0, 2)

        # Frequency
        layout.addWidget(QLabel("Frequency [Hz]:"), 1, 0)  # Label for frequency
        self.frequency_slider = QDoubleSlider(Qt.Horizontal)
        self.frequency_slider.setMinimum(0)
        self.frequency_slider.setMaximum(100)
        self.frequency_slider.setValue(self.frequency)
        self.frequency_slider.valueChanged.connect(self.update_frequency)
        layout.addWidget(self.frequency_slider, 1, 1)
        self.frequency_edit = QLineEdit(f"{self.frequency}")
        self.frequency_edit.returnPressed.connect(self.edit_frequency)
        layout.addWidget(self.frequency_edit, 1, 2)

        # Duration
        layout.addWidget(QLabel("Duration [ms]:"), 2, 0)  # Label for duration
        self.duration_slider = QDoubleSlider(Qt.Horizontal)
        self.duration_slider.setMinimum(0)
        self.duration_slider.setMaximum(100)
        self.duration_slider.setValue(self.duration)
        self.duration_slider.valueChanged.connect(self.update_duration)
        layout.addWidget(self.duration_slider, 2, 1)
        self.duration_edit = QLineEdit(f"{self.duration}")
        self.duration_edit.returnPressed.connect(self.edit_duration)
        layout.addWidget(self.duration_edit, 2, 2)

        # Add Start Button
        self.start_button = QPushButton("Start PWM")
        self.start_button.clicked.connect(
            self.start_pwm
        )  # Assuming start_pwm is a method you've defined
        layout.addWidget(self.start_button, 0, 3, 1, 2)  # Span 1 row and 2 columns

        self.setLayout(layout)

    def update_duty_cycle(self, value):
        self.duty_cycle = value
        self.duty_cycle_edit.setText(f"{value:.2f}")
        self.update_command()

    def edit_duty_cycle(self):
        value = float(self.duty_cycle_edit.text())
        self.duty_cycle = value
        self.duty_cycle_slider.setValue(value)

    def update_frequency(self, value):
        self.frequency = value
        self.frequency_edit.setText(f"{value:.2f}")
        self.update_command()

    def edit_frequency(self):
        value = float(self.frequency_edit.text())
        self.frequency = value
        self.frequency_slider.setValue(value)

    def update_duration(self, value):
        self.duration = value
        self.duration_edit.setText(f"{value:.2f}")
        self.update_command()

    def edit_duration(self):
        value = float(self.duration_edit.text())
        self.duration = value
        self.duration_slider.setValue(value)

    def update_command(self):
        self.command = f"U,{self.duty_cycle},{self.frequency},{self.duration}"
        self.arduino_pwm.send_command(self.command)

    def start_pwm(self):
        self.arduino_pwm.send_command("S")


# TODO: connect widget to actual abstract mirror calls
class MirrorWidget(QWidget):
    def __init__(self, mirror):
        super().__init__()
        self.mirror = mirror
        self.initialize_UI()

    def initialize_UI(self):
        layout = QVBoxLayout()

        mirror_x_label = QLabel("Mirror X Position")
        layout.addWidget(mirror_x_label)

        self.mirror_x_slider = QSlider(Qt.Horizontal)
        self.mirror_x_slider.setMinimum(-500)
        self.mirror_x_slider.setMaximum(500)
        self.mirror_x_slider.valueChanged.connect(self.update_mirror_x)
        layout.addWidget(self.mirror_x_slider)

        # Add a QLabel to display the mirror X value
        self.mirror_x_label = QLabel(f"X: {self.mirror.position_x}")
        layout.addWidget(self.mirror_x_label)

        mirror_y_label = QLabel("Mirror Y Position")
        layout.addWidget(mirror_y_label)

        self.mirror_y_slider = QSlider(Qt.Horizontal)
        self.mirror_y_slider.setMinimum(-500)
        self.mirror_y_slider.setMaximum(500)
        self.mirror_y_slider.valueChanged.connect(self.update_mirror_y)
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


class PhotomApp(QMainWindow):
    def __init__(
        self,
        photom_assembly: PhotomAssembly,
        photom_window_size: Tuple[int, int] = (100, 100),
        demo_window=None,
        arduino=[],
    ):
        super().__init__()

        self.photom_window = None
        self.photom_controls_window = None

        self.photom_assembly = photom_assembly
        self.lasers = self.photom_assembly.laser
        self.mirrors = self.photom_assembly.mirror
        self.photom_window_size = photom_window_size
        self._current_mirror_idx = 0

        # TODO: this probably will probably get removed along with any arduino pwm functionalities
        self.arduino_pwm = arduino

        if DEMO_MODE:
            self.demo_window = demo_window

        self.initialize_UI()
        self.initializer_laser_marker_window()

    def initializer_laser_marker_window(self):
        # Making the photom_window a square

        window_size = (
            self.photom_window_size[0],
            0,
            self.photom_window_size[0],
            self.photom_window_size[1],
        )
        self.photom_window = LaserMarkerWindow(
            photom_controls=self, name='Laser Marker', window_size=window_size
        )

    def initialize_UI(self):
        """
        Initialize the UI.

        """
        self.setGeometry(100, 100, 400, 500)
        self.setWindowTitle("Laser and Mirror Control App")

        # Adding slider to adjust transparency
        transparency_group = QGroupBox("Photom Transparency")
        transparency_layout = QVBoxLayout()
        # Create a slider to adjust the transparency
        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setMinimum(0)
        self.transparency_slider.setMaximum(100)
        self.transparency_slider.setValue(100)  # Initial value is fully opaque
        self.transparency_slider.valueChanged.connect(self.update_transparency)
        transparency_layout.addWidget(self.transparency_slider)

        # Add a QLabel to display the current percent transparency value
        self.transparency_label = QLabel(f"Transparency: 100%")
        transparency_layout.addWidget(self.transparency_label)
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
        for mirror in self.mirrors:
            mirror_widget = MirrorWidget(mirror)
            self.mirror_widgets.append(mirror_widget)
            mirror_layout.addWidget(mirror_widget)
        mirror_group.setLayout(mirror_layout)

        # Adding group for arduino PWM
        arduino_group = QGroupBox("Arduino PWM")
        arduino_layout = QVBoxLayout()
        self.arduino_pwm_widgets = []
        for arduino in self.arduino_pwm:
            arduino_pwm_widget = ArduinoPWMWidget(arduino)
            self.arduino_pwm_widgets.append(arduino_pwm_widget)
            arduino_layout.addWidget(arduino_pwm_widget)
        arduino_group.setLayout(arduino_layout)

        # Add the laser and mirror group boxes to the main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(transparency_group)
        main_layout.addWidget(laser_group)
        main_layout.addWidget(mirror_group)
        main_layout.addWidget(arduino_group)

        self.mirror_dropdown = QComboBox()
        self.mirror_dropdown.addItems([mirror.name for mirror in self.mirrors])
        main_layout.addWidget(self.mirror_dropdown)
        self.mirror_dropdown.setCurrentIndex(self._current_mirror_idx)
        self.mirror_dropdown.currentIndexChanged.connect(self.mirror_dropdown_changed)

        self.calibrate_button = QPushButton("Calibrate")
        self.calibrate_button.clicked.connect(self.calibrate)
        main_layout.addWidget(self.calibrate_button)

        # Add a "Done Calibration" button (initially hidden)
        self.done_calibration_button = QPushButton("Done Calibration")
        self.done_calibration_button.clicked.connect(self.done_calibration)
        self.done_calibration_button.hide()
        main_layout.addWidget(self.done_calibration_button)

        # Add a "Cancel Calibration" button (initially hidden)
        self.cancel_calibration_button = QPushButton("Cancel Calibration")
        self.cancel_calibration_button.clicked.connect(self.cancel_calibration)
        self.cancel_calibration_button.hide()
        main_layout.addWidget(self.cancel_calibration_button)
        main_widget = QWidget(self)
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)
        self.show()

    def mirror_dropdown_changed(self, index):
        print(f"Mirror dropdown changed to index {index}")
        self._current_mirror_idx = index

        # Reset to (0,0) position
        self.photom_assembly.mirror[self._current_mirror_idx].position = [0, 0]

    def calibrate(self):
        # Implement your calibration function here
        print("Calibrating...")
        # Hide the 'X' marker in photom_window
        # self.photom_window.marker.hide()
        # Hide the calibrate button
        self.calibrate_button.hide()
        # Show the "Cancel Calibration" button
        self.cancel_calibration_button.show()
        # Display the rectangle
        self.display_rectangle()
        self.source_pts = self.photom_window.get_coordinates()
        # Show the "Done Calibration" button
        self.done_calibration_button.show()

        selected_mirror_name = self.mirror_dropdown.currentText()
        self._current_mirror_idx = next(
            i
            for i, mirror in enumerate(self.mirrors)
            if mirror.name == selected_mirror_name
        )
        if not DEMO_MODE:
            # TODO: move in the pattern for calibration
            self.photom_assembly.calibrate(self._current_mirror_idx)
        else:
            print(f'Calibrating mirror: {self._current_mirror_idx}')

    def cancel_calibration(self):
        # Implement your cancel calibration function here
        print("Canceling calibration...")
        # Hide the "Done Calibration" button
        self.done_calibration_button.hide()
        # Show the "Calibrate" button
        self.calibrate_button.show()
        # Show the "X" marker in photom_window
        self.photom_window.marker.show()

        self.cancel_calibration_button.hide()
        # Switch back to the shooting scene
        self.photom_window.switch_to_shooting_scene()

    def done_calibration(self):
        # Perform any necessary actions after calibration is done
        self.target_pts = self.photom_window.get_coordinates()
        origin = np.array(
            [[pt.x(), pt.y()] for pt in self.source_pts], dtype=np.float32
        )
        dest = np.array([[pt.x(), pt.y()] for pt in self.target_pts], dtype=np.float32)

        T_affine = self.photom_assembly.mirror[
            self._current_mirror_idx
        ].affine_transform_obj.compute_affine_matrix(dest, origin)
        # logger.debug(f"Affine matrix: {T_affine}")
        print(f"Affine matrix: {T_affine}")

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
                matrix=T_affine, config_file=typed_filename
            )
            self.photom_window.switch_to_shooting_scene()
            self.photom_window.marker.show()

            # Hide the "Done Calibration" button
            self.done_calibration_button.hide()
            self.calibrate_button.show()
            self.cancel_calibration_button.hide()

            if DEMO_MODE:
                print(f'origin: {origin}')
                print(f'dest: {dest}')
                # transformed_coords = self.affine_trans_obj.apply_affine(dest)
                transformed_coords = self.photom_assembly.mirror[
                    self._current_mirror_idx
                ].affine_transform_obj.apply_affine(dest)
                print(transformed_coords)
                coords_list = self.photom_assembly.mirror[
                    self._current_mirror_idx
                ].affine_transform_obj.trans_pointwise(transformed_coords)
                print(coords_list)
                self.demo_window.updateVertices(coords_list)
                return
        else:
            print("No file selected")
            # Show dialog box saying no file selected
        print("Calibration done")

    def update_transparency(self, value):
        transparency_percent = value
        self.transparency_label.setText(f"Transparency: {transparency_percent}%")
        opacity = 1.0 - (transparency_percent / 100.0)  # Calculate opacity (0.0 to 1.0)
        self.photom_window.setWindowOpacity(opacity)  # Update photom_window opacity

    def display_rectangle(self):
        # Calculate the coordinates of the rectangle corners
        rectangle_scaling = 0.5
        window_size = (self.photom_window.width(), self.photom_window.height())
        rectangle_size = (
            (window_size[0] * rectangle_scaling),
            (window_size[1] * rectangle_scaling),
        )
        rectangle_coords = calculate_rectangle_corners(rectangle_size)
        self.photom_window.updateVertices(rectangle_coords)
        self.photom_window.switch_to_calibration_scene()


class LaserMarkerWindow(QMainWindow):
    def __init__(
        self,
        photom_controls: QMainWindow = None,
        name="Laser Marker",
        window_size=(100, 100, 100, 100),
    ):
        super().__init__()
        self.photom_controls = photom_controls
        self.window_name = name
        self.window_geometry = window_size
        self.setMouseTracking(True)
        self.mouseX = None
        self.mouseY = None
        self.setWindowOpacity(0.7)
        self.scale = 0.025
        # self.offset = (-0.032000, -0.046200)

        # Create a QStackedWidget
        self.stacked_widget = QStackedWidget()
        # Set the QStackedWidget as the central widget

        self.initMarker()
        self.init_tetragon()

        self.initialize_UI()

        self.setCentralWidget(self.stacked_widget)

    def initialize_UI(self):
        self.setGeometry(
            self.window_geometry[0],
            self.window_geometry[1],
            self.window_geometry[2],
            self.window_geometry[3],
        )
        self.setWindowTitle(self.window_name)

        # Fix the size of the window
        self.setFixedSize(
            self.window_geometry[2],
            self.window_geometry[3],
        )
        self.switch_to_shooting_scene()
        self.show()

    def initMarker(self):
        self.shooting_scene = QGraphicsScene(self)
        self.shooting_view = QGraphicsView(self.shooting_scene)
        self.shooting_view.setMouseTracking(True)
        self.setCentralWidget(self.shooting_view)
        self.setMouseTracking(True)
        self.marker = QGraphicsSimpleTextItem("X")
        self.marker.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.shooting_scene.addItem(self.marker)

        # Add the view to the QStackedWidget
        self.stacked_widget.addWidget(self.shooting_view)

    def init_tetragon(
        self, tetragon_coords: list = [(100, 100), (200, 100), (200, 200), (100, 200)]
    ):
        self.calibration_scene = QGraphicsScene(self)
        self.calibration_view = QGraphicsView(self.calibration_scene)
        self.calibration_view.setMouseTracking(True)
        self.setCentralWidget(self.calibration_view)
        self.setMouseTracking(True)
        self.vertices = []
        for x, y in tetragon_coords:
            vertex = QGraphicsEllipseItem(x - 5, y - 5, 10, 10)
            vertex.setBrush(Qt.red)
            vertex.setFlag(QGraphicsEllipseItem.ItemIsMovable)
            self.vertices.append(vertex)
            self.calibration_scene.addItem(vertex)

        # Add the view to the QStackedWidget
        self.stacked_widget.addWidget(self.calibration_view)

    def switch_to_shooting_scene(self):
        self.stacked_widget.setCurrentWidget(self.shooting_view)

    def switch_to_calibration_scene(self):
        self.stacked_widget.setCurrentWidget(self.calibration_view)

    def get_coordinates(self):
        return [vertex.pos() for vertex in self.vertices]

    def updateVertices(self, new_coordinates):
        for vertex, (x, y) in zip(self.vertices, new_coordinates):
            vertex.setPos(x, y)

    def recordinate(self, rawcord):
        return -self.scale * (rawcord - (self.window_geometry[2] / 2)) / 50

    def mouseMoveEvent(self, event: "QGraphicsSceneMouseEvent"):
        new_cursor_position = event.screenPos()
        print(f"current x: {new_cursor_position}")

    def mousePressEvent(self, event):
        marker_x = self.marker.pos().x()
        marker_y = self.marker.pos().y()
        print(f"x position (x,y): {(marker_x, marker_y)}")
        # print('Mouse press coords: ( %f : %f )' % (self.mouseX, self.mouseY))
        # Update the mirror slider values
        if self.photom_controls is not None:
            self.photom_controls.mirror_widgets[
                self.photom_controls._current_mirror_idx
            ].mirror_x_slider.setValue(int(self.marker.pos().x()))
            self.photom_controls.mirror_widgets[
                self.photom_controls._current_mirror_idx
            ].mirror_y_slider.setValue(int(self.marker.pos().y()))

        # Update the photom_assembly mirror position
        # self.photom_controls.mirror[self._current_mirror_idx].position = [
        #     self.marker.pos().x(),
        #     self.marker.pos().y(),
        # ]

    def mouseReleaseEvent(self, event):
        print("Mouse release coords: ( %f : %f )" % (self.mouseX, self.mouseY))


if __name__ == "__main__":
    import os

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
        # NOTE: These are the actual classes that will be used in the photom assembly
        from copylot.hardware.lasers.vortran.vortran import VortranLaser as Laser
        from copylot.hardware.mirrors.optotune.mirror import OptoMirror as Mirror
        from copylot.assemblies.photom.utils.arduino import ArduinoPWM

    try:
        os.environ["DISPLAY"] = ":1002"

    except:
        raise Exception("DISPLAY environment variable not set")

    config_path = r"copylot\assemblies\photom\demo\photom_VIS_config.yml"

    # TODO: this should be a function that parses the config_file and returns the photom_assembly
    # Load the config file and parse it
    with open(config_path, "r") as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)
        lasers = [Laser(**laser_data) for laser_data in config["lasers"]]
        mirrors = [
            Mirror(
                name=mirror_data["name"],
                pos_x=mirror_data["x_position"],
                pos_y=mirror_data["y_position"],
            )
            for mirror_data in config["mirrors"]
        ]  # Initial mirror position
        affine_matrix_paths = [
            mirror['affine_matrix_path'] for mirror in config['mirrors']
        ]
        arduino = [ArduinoPWM(serial_port='COM3', baud_rate=115200)]
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
            window_size=(ctrl_window_width, 0, ctrl_window_width, ctrl_window_width),
        )  # Set the positions of the windows
        ctrl_window = PhotomApp(
            photom_assembly=photom_assembly,
            photom_window_size=(ctrl_window_width, ctrl_window_width),
            demo_window=camera_window,
            arduino=arduino,
        )
        ctrl_window.setGeometry(0, 0, ctrl_window_width, ctrl_window_width)

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
        camera_window.updateVertices(rectangle_coords)
    else:
        # Set the positions of the windows
        ctrl_window = PhotomApp(
            photom_assembly=photom_assembly,
            photom_window_size=(ctrl_window_width, ctrl_window_height),
        )
        ctrl_window.setGeometry(0, 0, ctrl_window_width, ctrl_window_height)

    sys.exit(app.exec_())
