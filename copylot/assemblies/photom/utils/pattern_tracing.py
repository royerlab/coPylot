import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QComboBox, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QHBoxLayout
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QPolygon

class Shape(QPolygon):
    def __init__(self, border_points):
        super().__init__(border_points)
        self.border_points = border_points
        self.pattern_style = None
        self.pattern_points = set()

    def _pattern_bidirectional(self, vertical_spacing, horizontal_spacing):
        self.border_style = "Bidirectional"
        min_x = self.boundingRect().left()
        max_x = self.boundingRect().right()
        min_y = self.boundingRect().top()
        max_y = self.boundingRect().bottom()

        curr_x = min_x
        curr_y = min_y
        direction = True # true if moving right, false if moving left

        while curr_y <= max_y:
            if direction:
                while curr_x <= max_x:
                    if self.containsPoint(QPoint(curr_x, curr_y), Qt.OddEvenFill):
                        self.pattern_points.add((curr_x, curr_y))
                    curr_x += horizontal_spacing
            else:
                while curr_x >= min_x:
                    if self.containsPoint(QPoint(curr_x, curr_y), Qt.OddEvenFill):
                        self.pattern_points.add((curr_x, curr_y))
                    curr_x -= horizontal_spacing

            curr_y += vertical_spacing
            direction = not direction

            if direction:
                curr_x = min_x
            else:
                curr_x = max_x


