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
)
from PyQt5.QtGui import QColor, QPen
from copylot.assemblies.photom.utils.affine_transform import AffineTransform
import numpy as np

DEMO_MODE = True


class Laser:
    def __init__(self, name, power=0):
        self.name = name
        self.power = power
        self.laser_on = False

    def toggle(self):
        self.laser_on = not self.laser_on

    def set_power(self, power):
        self.power = power


class Mirror:
    def __init__(self, x_position=0, y_position=0):
        self.x = x_position
        self.y = y_position


class LaserWidget(QWidget):
    def __init__(self, laser):
        super().__init__()
        self.laser = laser
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        laser_label = QLabel(self.laser.name)
        layout.addWidget(laser_label)

        laser_power_slider = QSlider(Qt.Horizontal)
        laser_power_slider.setMinimum(0)
        laser_power_slider.setMaximum(100)
        laser_power_slider.setValue(self.laser.power)
        laser_power_slider.valueChanged.connect(self.update_power)
        layout.addWidget(laser_power_slider)

        # Add a QLabel to display the power value
        self.power_label = QLabel(f"Power: {self.laser.power}")
        layout.addWidget(self.power_label)

        laser_toggle_button = QPushButton("Toggle")
        laser_toggle_button.clicked.connect(self.toggle_laser)
        layout.addWidget(laser_toggle_button)

        self.setLayout(layout)

    def toggle_laser(self):
        self.laser.toggle()

    def update_power(self, value):
        self.laser.set_power(value)
        # Update the QLabel with the new power value
        self.power_label.setText(f"Power: {value}")


class MirrorWidget(QWidget):
    def __init__(self, mirror):
        super().__init__()
        self.mirror = mirror
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        mirror_x_label = QLabel("Mirror X Position")
        layout.addWidget(mirror_x_label)

        self.mirror_x_slider = QSlider(Qt.Horizontal)
        self.mirror_x_slider.setMinimum(0)
        self.mirror_x_slider.setMaximum(100)
        self.mirror_x_slider.valueChanged.connect(self.update_mirror_x)
        layout.addWidget(self.mirror_x_slider)

        # Add a QLabel to display the mirror X value
        self.mirror_x_label = QLabel(f"X: {self.mirror.x}")
        layout.addWidget(self.mirror_x_label)

        mirror_y_label = QLabel("Mirror Y Position")
        layout.addWidget(mirror_y_label)

        self.mirror_y_slider = QSlider(Qt.Horizontal)
        self.mirror_y_slider.setMinimum(0)
        self.mirror_y_slider.setMaximum(100)
        self.mirror_y_slider.valueChanged.connect(self.update_mirror_y)
        layout.addWidget(self.mirror_y_slider)

        # Add a QLabel to display the mirror Y value
        self.mirror_y_label = QLabel(f"Y: {self.mirror.y}")
        layout.addWidget(self.mirror_y_label)

        self.setLayout(layout)

    def update_mirror_x(self, value):
        self.mirror.x = value
        # Update the QLabel with the new X value
        self.mirror_x_label.setText(f"X: {value}")

    def update_mirror_y(self, value):
        self.mirror.y = value
        # Update the QLabel with the new Y value
        self.mirror_y_label.setText(f"Y: {value}")


class PhotomApp(QMainWindow):
    def __init__(
        self, lasers, mirror, photom_window, affine_trans_obj, demo_window=None
    ):
        super().__init__()
        self.photom_window = photom_window
        self.lasers = lasers
        self.mirror = mirror
        self.affine_trans_obj = affine_trans_obj
        if DEMO_MODE:
            self.demo_window = demo_window

        self.initUI()

    def initUI(self):
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
        for laser in self.lasers:
            laser_widget = LaserWidget(laser)
            laser_layout.addWidget(laser_widget)
        laser_group.setLayout(laser_layout)

        # Adding a group box for the mirror
        mirror_group = QGroupBox("Mirror")
        mirror_layout = QVBoxLayout()
        for mirror in self.mirror:
            mirror_widget = MirrorWidget(mirror)
            mirror_layout.addWidget(mirror_widget)
        mirror_group.setLayout(mirror_layout)

        # Add the laser and mirror group boxes to the main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(transparency_group)
        main_layout.addWidget(laser_group)
        main_layout.addWidget(mirror_group)

        # Add a button to calibrate the mirror
        self.calibrate_button = QPushButton("Calibrate")
        self.calibrate_button.clicked.connect(self.calibrate)
        main_layout.addWidget(self.calibrate_button)

        # Add a "Done Calibration" button (initially hidden)
        self.done_calibration_button = QPushButton("Done Calibration")
        self.done_calibration_button.clicked.connect(self.done_calibration)
        self.done_calibration_button.hide()
        main_layout.addWidget(self.done_calibration_button)

        main_widget = QWidget(self)
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)
        self.show()

    def calibrate(self):
        # Implement your calibration function here
        print("Calibration function executed")
        # Hide the 'X' marker in photom_window
        # self.photom_window.marker.hide()
        self.display_rectangle()
        self.source_pts = self.photom_window.get_coordinates()
        # Show the "Done Calibration" button
        self.done_calibration_button.show()

    def done_calibration(self):
        # Perform any necessary actions after calibration is done
        self.photom_window.switch_to_shooting_scene()
        self.photom_window.marker.show()
        self.target_pts = self.photom_window.get_coordinates()
        origin = np.array(
            [[pt.x(), pt.y()] for pt in self.source_pts], dtype=np.float32
        )
        dest = np.array([[pt.x(), pt.y()] for pt in self.target_pts], dtype=np.float32)
        T_affine = self.affine_trans_obj.compute_affine_matrix(dest, origin)
        self.affine_trans_obj.save_matrix()
        print(T_affine)

        # Hide the "Done Calibration" button
        self.done_calibration_button.hide()

        if DEMO_MODE:
            print(origin)
            print(dest)
            transformed_coords = self.affine_trans_obj.apply_affine(dest)
            print(transformed_coords)
            coords_list = self.affine_trans_obj.trans_pointwise(transformed_coords)
            print(coords_list)
            self.demo_window.updateVertices(coords_list)

        print("Calibration done")

    def update_transparency(self, value):
        transparency_percent = value
        self.transparency_label.setText(f"Transparency: {transparency_percent}%")
        opacity = 1.0 - (transparency_percent / 100.0)  # Calculate opacity (0.0 to 1.0)
        self.photom_window.setWindowOpacity(opacity)  # Update photom_window opacity

    def calculate_rectangle_corners(self, window_size):
        # window_size is a tuple of (width, height)

        # Calculate the coordinates of the rectangle corners
        x0y0 = (
            -window_size[0] / 2,
            -window_size[1] / 2,
        )
        x1y0 = (x0y0[0] + window_size[0], x0y0[1])
        x1y1 = (x0y0[0] + window_size[0], x0y0[1] + window_size[1])
        x0y1 = (x0y0[0], x0y0[1] + window_size[1])
        return x0y0, x1y0, x1y1, x0y1

    def display_rectangle(self):
        # Calculate the coordinates of the rectangle corners
        rectangle_scaling = 0.5
        window_size = (self.photom_window.width(), self.photom_window.height())
        rectangle_size = (
            (window_size[0] * rectangle_scaling),
            (window_size[1] * rectangle_scaling),
        )
        rectangle_coords = self.calculate_rectangle_corners(rectangle_size)
        self.photom_window.updateVertices(rectangle_coords)
        self.photom_window.switch_to_calibration_scene()


class LaserMarkerWindow(QMainWindow):
    def __init__(self, name="Laser Marker", window_size=(100, 100, 100, 100)):
        super().__init__()
        self.window_name = name
        self.windowGeo = window_size
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

        self.initUI()

        self.setCentralWidget(self.stacked_widget)

    def initUI(self):
        self.setGeometry(
            self.windowGeo[0],
            self.windowGeo[1],
            self.windowGeo[2],
            self.windowGeo[3],
        )
        self.setWindowTitle(self.window_name)

        # Fix the size of the window
        self.setFixedSize(
            self.windowGeo[2],
            self.windowGeo[3],
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
        return -self.scale * (rawcord - (self.windowGeo[2] / 2)) / 50

    def mouseMoveEvent(self, event: "QGraphicsSceneMouseEvent"):
        new_cursor_position = event.screenPos()

        print(f"current x: {new_cursor_position}")

    def mousePressEvent(self, event):
        marker_x = self.marker.pos().x()
        marker_y = self.marker.pos().y()
        print(f"x position: {(marker_x, marker_y)}")
        # print('Mouse press coords: ( %f : %f )' % (self.mouseX, self.mouseY))

    def mouseReleaseEvent(self, event):
        print("Mouse release coords: ( %f : %f )" % (self.mouseX, self.mouseY))


if __name__ == "__main__":
    import os

    os.environ["DISPLAY"] = ":1005"
    config_path = (
        "/home/eduardo.hirata/repos/coPylot/copylot/assemblies/photom/demo/config.yml"
    )
    with open(config_path, "r") as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)
        lasers = [Laser(**laser_data) for laser_data in config["lasers"]]
        mirror = [
            Mirror(
                x_position=mirror_data["x_position"],
                y_position=mirror_data["y_position"],
            )
            for mirror_data in config["mirrors"]
        ]  # Initial mirror position

    app = QApplication(sys.argv)

    # Define the positions and sizes for the windows
    screen_width = app.desktop().screenGeometry().width()
    screen_height = app.desktop().screenGeometry().height()

    ctrl_window_width = screen_width // 3  # Adjust the width as needed
    ctrl_window_height = screen_height // 3  # Use the full screen height

    # Making the photom_window a square
    photom_window_width = screen_width // 3  # Adjust the width as needed
    photom_window_height = screen_width // 3  # Adjust the width as needed

    photom_window_size = (
        ctrl_window_width,
        0,
        photom_window_width,
        photom_window_height,
    )
    photom_window = LaserMarkerWindow(window_size=photom_window_size)

    # TODO: expose this path to user?
    affine_trans_obj = AffineTransform(config_file="./affine_transform.yml")

    if DEMO_MODE:
        camera_window = LaserMarkerWindow(
            name="Mock laser dots", window_size=photom_window_size
        )  # Set the positions of the windows
        ctrl_window = PhotomApp(
            lasers, mirror, photom_window, affine_trans_obj, camera_window
        )
        ctrl_window.setGeometry(0, 0, ctrl_window_width, ctrl_window_height)
        camera_window.switch_to_calibration_scene()
        rectangle_scaling = 0.2
        window_size = (camera_window.width(), camera_window.height())
        rectangle_size = (
            (window_size[0] * rectangle_scaling),
            (window_size[1] * rectangle_scaling),
        )
        rectangle_coords = ctrl_window.calculate_rectangle_corners(rectangle_size)
        # translate each coordinate by the offset
        rectangle_coords = [(x + 30, y) for x, y in rectangle_coords]
        camera_window.updateVertices(rectangle_coords)
    else:
        # Set the positions of the windows
        ctrl_window = PhotomApp(
            lasers,
            mirror,
            photom_window,
            affine_trans_obj,
        )
        ctrl_window.setGeometry(0, 0, ctrl_window_width, ctrl_window_height)

    sys.exit(app.exec_())
