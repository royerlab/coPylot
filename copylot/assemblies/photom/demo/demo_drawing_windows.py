import sys

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsItem,
    QGraphicsView,
    QPushButton,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QDesktopWidget,
)

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QMouseEvent, QCursor, QFont, QFontMetricsF
from copylot import logger


class CustomWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.windowGeo = (300, 300, 500, 500)
        self.setMouseTracking(True)
        self.mouseX = None
        self.mouseY = None
        self.board_num = 0
        self.setWindowOpacity(0.7)
        self.scale = 0.025

        self.view = None
        self.scene = None
        self.initUI()
        self.initMarker()
        self.show()
        print(
            f'liveView actual {self.frameGeometry().x(), self.frameGeometry().y(), self.width(), self.height()}'
        )
        print(self.frameGeometry().height(), self.frameGeometry().width())

    def initUI(self):
        self.setWindowTitle('Mouse Tracker')
        self.setFixedSize(
            self.windowGeo[2],
            self.windowGeo[3],
        )
        self.sidebar_size = self.frameGeometry().width() - self.windowGeo[2]
        self.topbar_size = self.frameGeometry().height() - self.windowGeo[3]
        self.canvas_width = self.frameGeometry().width() - self.sidebar_size
        self.canvas_height = self.frameGeometry().height() - self.topbar_size
        print(f'sidebar size: {self.sidebar_size}, topbar size: {self.topbar_size}')
        print(f'canvas width: {self.canvas_width}, canvas height: {self.canvas_height}')

    def initMarker(self):
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, self.canvas_width, self.canvas_width)

        self.view = QGraphicsView(self.scene)
        self.view.setMouseTracking(True)
        self.setCentralWidget(self.view)
        self.view.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.view.viewport().installEventFilter(self)
        self.setMouseTracking(True)
        # Scene items
        self.marker = QGraphicsSimpleTextItem('X')
        self.marker.setFlag(QGraphicsItem.ItemIsMovable, True)

        # Disable scrollbars
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Move the marker
        self.display_marker_center(
            self.marker, (self.canvas_width / 2, self.canvas_height / 2)
        )

        # Add items and set the scene
        self.scene.addItem(self.marker)
        self.view.setScene(self.scene)

    def get_marker_center(self, marker):
        fm = QFontMetricsF(QFont())
        boundingRect = fm.tightBoundingRect(marker.text())
        mergintop = fm.ascent() + boundingRect.top()
        x = marker.pos().x() + boundingRect.left() + boundingRect.width() / 2
        y = marker.pos().y() + mergintop + boundingRect.height() / 2
        return x, y

    def display_marker_center(self, marker, coords=None):
        if coords is None:
            coords = (marker.x(), marker.y())

        if coords is None:
            coords = (marker.x(), marker.y())
        fm = QFontMetricsF(QFont())
        boundingRect = fm.tightBoundingRect(marker.text())
        mergintop = fm.ascent() + boundingRect.top()
        marker.setPos(
            coords[0] - boundingRect.left() - boundingRect.width() / 2,
            coords[1] - mergintop - boundingRect.height() / 2,
        )
        return marker

    def eventFilter(self, source, event):
        "The mouse movements do not work without this function"
        if event.type() == QMouseEvent.MouseMove:
            print('mouse move')
            print(f'x1: {event.screenPos().x()}, y1: {event.screenPos().y()}')
            # print(f'x: {event.posF().x()}, y: {event.posF().y()}')
            # print(f'x: {event.localPosF().x()}, y: {event.localPosF().y()}')
            # print(f'x: {event.windowPosF().x()}, y: {event.windowPosF().y()}')
            # print(f'x: {event.screenPosF().x()}, y: {event.screenPosF().y()}')
            # print(f'x: {event.globalPosF().x()}, y: {event.globalPosF().y()}')
            print(f'x2: {event.pos().x()}, y2: {event.pos().y()}')
        elif event.type() == QMouseEvent.MouseButtonPress:
            print('mouse button pressed')
            if event.buttons() == Qt.LeftButton:
                print('left button pressed')
            elif event.buttons() == Qt.RightButton:
                print('right button pressed')

        elif event.type() == QMouseEvent.MouseButtonRelease:
            print('mouse button released')
            if event.buttons() == Qt.LeftButton:
                print('left button released')
            elif event.buttons() == Qt.RightButton:
                print('right button released')

        return super(CustomWindow, self).eventFilter(source, event)


class CtrlWindow(QMainWindow):
    def __init__(self, mouse_tracker_window):
        super().__init__()
        # Get the number of screens and make the live view
        num_screens = QDesktopWidget().screenCount()
        logger.debug(f'num screens {num_screens}')
        self.mouse_tracker_window = mouse_tracker_window
        self.windowGeo = (1300, 300, 500, 1000)
        self.buttonSize = (200, 100)
        self.initUI()

        # Set the layout on the central widget

    def initUI(self):
        # Create a central widget for the main window
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.setGeometry(
            self.windowGeo[0],
            self.windowGeo[1],
            self.windowGeo[2],
            self.windowGeo[3],
        )
        self.setWindowTitle('Control panel')
        self.setFixedSize(
            self.windowGeo[2],
            self.windowGeo[3],
        )

        self.button = QPushButton("OK", self)
        self.button.setStyleSheet(
            "QPushButton{"
            "font-size: 24px;"
            "font-family: Helvetica;"
            "border-width: 2px;"
            "border-radius: 15px;"
            "border-color: black;"
            "border-style: outset;"
            "}\n"
            "QPushButton:pressed {background-color: gray;}"
        )
        self.button.move(250, 250)  # button location
        self.button.setGeometry(
            (self.windowGeo[2] - self.buttonSize[0]) // 2,
            100,
            self.buttonSize[0],
            self.buttonSize[1],
        )
        self.button.clicked.connect(self.buttonClicked)
        layout.addWidget(self.button)

        self.show()

    def buttonClicked(self):
        print('button clicked')
        x, y = self.mouse_tracker_window.get_marker_center(
            self.mouse_tracker_window.marker
        )
        print(f'x: {x}, y: {y}')
        self.mouse_tracker_window.display_marker_center(
            self.mouse_tracker_window.marker,
            (
                self.mouse_tracker_window.canvas_width / 2,
                self.mouse_tracker_window.canvas_height / 2,
            ),
        )
        # self.mouse_tracker_windowdisplay_marker_center(self.mouse_tracker_window.marker, (0.0, 0.0))
        # self.mouse_tracker_window.marker.setPos(0, 0)


if __name__ == "__main__":
    import os

    os.environ["DISPLAY"] = ":1005"
    app = QApplication(sys.argv)
    dac = CustomWindow()
    ctrl = CtrlWindow(dac)
    sys.exit(app.exec_())
