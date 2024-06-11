import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QComboBox, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QHBoxLayout
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QPainterPath, QPolygon

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

        # self.pattern_points.add((min_x, min_y))
        # self.pattern_points.add((max_x, min_y))
        # self.pattern_points.add((min_x, max_y))
        # self.pattern_points.add((max_x, max_y))

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



class ViewerWindow(QMainWindow):
    shapesUpdated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Window")
        self.setGeometry(450, 100, 400, 300)

        # class variables
        self.drawing = False
        self.shapes = {}
        self.curr_shape_points = []
        self.curr_shape_id = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # point = (event.x(), event.y())
            point = event.pos()
            if not self.drawing:
                self.drawing = True
            self.curr_shape_points.append(point)

    def mouseMoveEvent(self, event):
        if self.drawing:
            # point = (event.x(), event.y())
            point = event.pos()
            self.curr_shape_points.append(point)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.drawing:
                # point = (event.x(), event.y())
                point = event.pos()
                self.curr_shape_points.append(point)

                self.curr_shape_points.append(self.curr_shape_points[0]) # connecting the final points in case not connected
                self.shapes[self.curr_shape_id] = Shape(self.curr_shape_points)
                self.shapesUpdated.emit()

                self.curr_shape_points = []
                self.drawing = False
                self.curr_shape_id += 1
            self.update()

    def paintEvent(self, event):
        self.draw_shapes()
        self.draw_patterns()

    def draw_shapes(self):
        painter = QPainter(self)
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        painter.setPen(pen)

        for shape_id, shape in self.shapes.items():
            border_points = shape.border_points
            for i in range(len(border_points) - 1):
                painter.drawLine(border_points[i], border_points[i + 1])

        if self.drawing and len(self.curr_shape_points) > 1:
            for i in range(len(self.curr_shape_points) - 1):
                painter.drawLine(self.curr_shape_points[i], self.curr_shape_points[i + 1])

    def draw_patterns(self):
        painter = QPainter(self)
        pen = QPen(Qt.green, 2, Qt.SolidLine)
        painter.setPen(pen)

        for shape_id, shape in self.shapes.items():
            if shape.pattern_points:
                pattern_points = shape.pattern_points
                for point in pattern_points:
                    point = QPoint(point[0], point[1])
                    painter.drawPoint(point)

class CtrlWindow(QMainWindow):
    def __init__(self, viewer_window):
        super().__init__()
        self.viewer_window = viewer_window 
        self.windowGeo = (500, 500, 500, 500)
        self.buttonSize = (200, 100)
        self.patterns = ['Bidirectional']
        self.initUI()

    def initUI(self):
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

        # roi dropdown box
        self.roi_dropdown= QComboBox(self)
        self.roi_dropdown.addItem("Select ROI")
        self.viewer_window.shapesUpdated.connect(self.updateRoiDropdown)
        layout.addWidget(self.roi_dropdown)

        # pattern dropdown box
        self.pattern_dropdown = QComboBox(self)
        self.pattern_dropdown.addItem("Select Pattern")
        self.addPatternDropdownItems()
        layout.addWidget(self.pattern_dropdown)
        self.pattern_dropdown.currentIndexChanged.connect(self.onPatternSelected)

        # horizontal spacing box
        spacing_boxes = QHBoxLayout()
        self.horizontal_spacing_label = QLabel("Horizontal Spacing:", self)
        spacing_boxes.addWidget(self.horizontal_spacing_label)
        self.horizontal_spacing_input = QLineEdit(self)
        spacing_boxes.addWidget(self.horizontal_spacing_input)

        # vertical spacing box
        self.vertical_spacing_label = QLabel("Vertical Spacing:", self)
        spacing_boxes.addWidget(self.vertical_spacing_label)
        self.vertical_spacing_input = QLineEdit(self)
        spacing_boxes.addWidget(self.vertical_spacing_input)
        layout.addLayout(spacing_boxes)

       # apply pattern button
        apply_and_ablate_buttons= QHBoxLayout()
        self.apply_pattern_button = QPushButton("Apply Pattern", self)
        self.apply_pattern_button.setMinimumSize(200, 50)
        self.apply_pattern_button.clicked.connect(self.onApplyPatternClick)
        apply_and_ablate_buttons.addWidget(self.apply_pattern_button)

        # show/hide the horizontal / vertical spacing input
        self.show_or_hide_spacing_input(False)

        # send to ablate button
        self.ablate_button = QPushButton("Ablate", self)
        self.ablate_button.setMinimumSize(150, 50)
        self.ablate_button.setStyleSheet("background-color: red; color: white;")
        self.ablate_button.clicked.connect(self.onAblateClick)
        apply_and_ablate_buttons.addWidget(self.ablate_button)

        apply_and_ablate_button_widget = QWidget()
        apply_and_ablate_button_widget.setLayout(apply_and_ablate_buttons)
        layout.addWidget(apply_and_ablate_button_widget)


    def updateRoiDropdown(self):
        self.roi_dropdown.clear()
        self.roi_dropdown.addItem("Select ROI")
        for roi in self.viewer_window.shapes.keys():
            self.roi_dropdown.addItem(f"Shape {roi + 1}")

    def addPatternDropdownItems(self):
        for pattern in self.patterns:
            self.pattern_dropdown.addItem(pattern)

    def onApplyPatternClick(self):
        selected_roi = self.roi_dropdown.currentText()
        if selected_roi == "Select ROI":
            return
        roi_number = int(selected_roi.split(" ")[1]) - 1
        selected_pattern = self.pattern_dropdown.currentText()

        if selected_pattern == 'Bidirectional':
            try:
                horizontal_spacing = int(self.horizontal_spacing_input.text())
                vertical_spacing = int(self.vertical_spacing_input.text())
                shape = self.viewer_window.shapes[roi_number]
                shape.pattern_points.clear()
                self.viewer_window.shapes[roi_number]._pattern_bidirectional(vertical_spacing, horizontal_spacing)
            except ValueError:
                print("invalid spacing input")

        self.viewer_window.update()

    def show_or_hide_spacing_input(self, show):
        self.horizontal_spacing_label.setVisible(show)
        self.horizontal_spacing_input.setVisible(show)
        self.vertical_spacing_label.setVisible(show)
        self.vertical_spacing_input.setVisible(show)
        
    def onPatternSelected(self):
        selected_pattern = self.pattern_dropdown.currentText()
        if selected_pattern == "Bidirectional":
            self.show_or_hide_spacing_input(True)
        else:
            self.show_or_hide_spacing_input(False)

    def onAblateClick(self):
        ablate_coords = []
        for shape in self.viewer_window.shapes.values():
            if shape.pattern_points:
                curr_ablation_coords = []
                for coord in shape.pattern_points:
                    curr_ablation_coords.append(coord)
                ablate_coords.append(curr_ablation_coords)

        return ablate_coords


if __name__ == "__main__":
    import os

    app = QApplication(sys.argv)
    dac = ViewerWindow()
    ctrl = CtrlWindow(dac)
    dac.show()
    ctrl.show()
    sys.exit(app.exec_())
