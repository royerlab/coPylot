from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRectF
import time
import numpy as np
from PyQt5.QtWidgets import (
    QSlider,
    QWidget,
    QVBoxLayout,
    QDoubleSpinBox,
    QLabel,
    QGraphicsPixmapItem,
)
from PyQt5.QtGui import QPainterPath


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


class CalibrationWithCameraThread(QThread):
    finished = pyqtSignal(np.ndarray, str)

    def __init__(self, photom_assembly, current_mirror_idx):
        super().__init__()
        self.photom_assembly = photom_assembly
        self.current_mirror_idx = current_mirror_idx

    def run(self):
        # TODO: hardcoding the camera for now
        # mirror_roi = [[-0.008, -0.02], [0.019, 0.0]]  # [x,y] #old coordinates prior to internship
        # mirror_roi = [[0.0, -0.025], [0.02, -0.01]]  # [x,y]
        mirror_roi = [[0.005, -0.025], [0.025, -0.01]]  # [x,y]
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


class DoubleSlider(QSlider):
    # create our our signal that we can connect to if necessary
    doubleValueChanged = pyqtSignal(float)

    def __init__(self, decimals=5, *args, **kargs):
        super(DoubleSlider, self).__init__(*args, **kargs)
        self._multi = 10**decimals

        self.valueChanged.connect(self.emitDoubleValueChanged)

    def emitDoubleValueChanged(self):
        value = float(super(DoubleSlider, self).value()) / self._multi
        self.doubleValueChanged.emit(value)

    def value(self):
        return float(super(DoubleSlider, self).value()) / self._multi

    def setMinimum(self, value):
        return super(DoubleSlider, self).setMinimum(int(value * self._multi))

    def setMaximum(self, value):
        return super(DoubleSlider, self).setMaximum(int(value * self._multi))

    def setSingleStep(self, value):
        return super(DoubleSlider, self).setSingleStep(value * self._multi)

    def singleStep(self):
        return float(super(DoubleSlider, self).singleStep()) / self._multi

    def setValue(self, value):
        super(DoubleSlider, self).setValue(int(value * self._multi))


class ClickablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable, True)  # Make the item movable

    def boundingRect(self):
        # Override boundingRect to make the whole pixmap area clickable and draggable
        return QRectF(self.pixmap().rect())

    def shape(self):
        # Override shape to define the interactable area as the entire bounding rectangle
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path
