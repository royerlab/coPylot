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

from PyQt5.QtCore import Qt, pyqtSignal, QThread
import numpy as np
import time
import yaml
from copylot.assemblies.photom.gui.utils import PWMWorker
from copylot.assemblies.photom.gui.utils import DoubleSlider


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
        self.laser_power_slider.sliderReleased.connect(self.on_slider_released)
        self.laser_power_slider.valueChanged.connect(self.update_displayed_power)
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
        if self._curr_laser_pulse_mode:
            self.laser.pulse_power = self._curr_power
        else:
            self.laser.power = self._curr_power
        self.power_edit.setText(f"{self._curr_power:.2f}")

    def on_slider_released(self):
        value = self.laser_power_slider.value()
        self._curr_power = value
        self.update_power(self._curr_power)

    def update_displayed_power(self, value):
        # Update the displayed power value (e.g., in a QLabel) without calling the laser power update function
        self._curr_power = value / (10**self._slider_decimal)
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
                self.update_power(self._curr_power)
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
        self.duration = 1  # number of reps
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
        layout.addWidget(QLabel("Pulse Duration [ms]:"), 2, 0)
        self.time_period_edit = QLineEdit(f"{self.time_period_ms}")
        self.time_period_edit.returnPressed.connect(self.edit_time_period)
        layout.addWidget(self.time_period_edit, 2, 1)

        # Duration
        layout.addWidget(QLabel("Pulse repetitions:"), 3, 0)
        self.duration_edit = QLineEdit(f"{self.duration}")
        self.duration_edit.returnPressed.connect(self.edit_duration)
        layout.addWidget(self.duration_edit, 3, 1)

        # Repetitions
        layout.addWidget(QLabel("Timelapse - number of timepoints:"), 4, 0)
        self.repetitions_edit = QLineEdit(f"{self.repetitions}")
        self.repetitions_edit.textChanged.connect(self.edit_repetitions)
        layout.addWidget(self.repetitions_edit, 4, 1)

        # Time interval
        layout.addWidget(QLabel("Timelapse - Time interval [s]:"), 5, 0)
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
            value = self.time_period_ms * value
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

    def get_current_parameters_from_gui(self):
        self.duty_cycle = float(self.duty_cycle_edit.text())
        self.time_period_ms = float(self.time_period_edit.text())
        self.frequency = 1000.0 / self.time_period_ms
        self.duration = float(self.duration_edit.text()) * self.time_period_ms
        self.repetitions = int(self.repetitions_edit.text())
        self.time_interval_s = float(self.time_interval_edit.text())

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
        # Update the command with the current settings
        self.get_current_parameters_from_gui()
        self.update_command()
        # TODO: Need to modify the data struct for command for multiple lasers
        if hasattr(self, 'command'):
            self.arduino_pwm.send_command(self.command)
