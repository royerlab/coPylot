from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen
import sys

class CustomWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setMouseTracking(True)
        self.mouseX = None
        self.mouseY = None
        self.setWindowOpacity(0.7)

    def initUI(self):
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Mouse Tracker')

        self.show()

    def mouseMoveEvent(self, event):
        self.mouseX = event.x() / 100
        self.mouseY = event.y() / 100
        print('Mouse coords: ( %d : %d )' % (event.x(), event.y()))

    def mousePressEvent(self, event):
        print('mouse pressed')

    def mouseReleaseEvent(self, event):
        print('mouse released')

    def paintEvent(self, event=None):
        painter = QPainter(self)

        # painter.setOpacity(0.5)
        painter.setBrush(Qt.white)
        painter.setPen(QPen(Qt.white))
        painter.drawRect(self.rect())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomWindow()
    app.exec_()
