import sys
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QMainWindow,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPolygonF, QPen


class TetragonEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tetragon Editor")
        self.setGeometry(100, 100, 800, 600)

        # Create a QGraphicsView to display the scene
        self.view = QGraphicsView(self)
        self.view.setGeometry(10, 10, 780, 580)

        # Create a QGraphicsScene
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        # Create initial vertices for the tetragon
        self.vertices = []
        for x, y in [(100, 100), (200, 100), (200, 200), (100, 200)]:
            vertex = QGraphicsEllipseItem(x - 5, y - 5, 10, 10)
            vertex.setBrush(Qt.red)
            vertex.setFlag(QGraphicsEllipseItem.ItemIsMovable)
            self.vertices.append(vertex)
            self.scene.addItem(vertex)

    def getCoordinates(self):
        return [vertex.pos() for vertex in self.vertices]

    def resizeEvent(self, event):
        # Resize the view when the main window is resized
        self.view.setGeometry(10, 10, self.width() - 20, self.height() - 20)

    def updateVertices(self, new_coordinates):
        for vertex, (x, y) in zip(self.vertices, new_coordinates):
            vertex.setPos(x, y)


if __name__ == '__main__':
    import os

    os.environ["DISPLAY"] = ":1005"
    app = QApplication(sys.argv)
    window = TetragonEditor()
    # print(window.getCoordinates())
    # window.updateVertices([(10, 10), (300, 200), (0, 300), (200, 300)])
    # print(window.getCoordinates())
    window.show()
    sys.exit(app.exec_())
