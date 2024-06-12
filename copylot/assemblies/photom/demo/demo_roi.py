import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QComboBox, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QPainterPath, QPolygon, QMouseEvent, QPaintEvent
from copylot.assemblies.photom.utils.pattern_tracing import Shape

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class ViewerWindow(QMainWindow):
    shapesUpdated = pyqtSignal()

    def __init__(self) -> None:
        """initializes the Viewer Window for drawing and viewing shapes.
        """
        super().__init__()
        self.setWindowTitle("Main Window")
        self.setGeometry(450, 100, 400, 300)

        # class variables
        self.drawing = False
        self.shapes = {}
        self.curr_shape_points = []
        self.curr_shape_id = 0
        self.selected_shape_id = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """records left mouse press for drawing shapes.

        Args:
            event (QMouseEvent): the mouse event that triggered the press. 
        """
        if event.button() == Qt.LeftButton:
            point = event.pos()
            if not self.drawing:
                self.drawing = True
            self.curr_shape_points.append(point)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """records mouse movement while drawing a shape.

        Args:
            event (QMouseEvent): the mouse event that triggered the movement. 
        """
        if self.drawing:
            point = event.pos()
            self.curr_shape_points.append(point)
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """handles the release of the left mouse button, completing the drawing of a shape.

        Args:
            event (QMouseEvent): the mouse event that triggered the release. 
        """
        if event.button() == Qt.LeftButton:
            if self.drawing:
                point = event.pos()
                self.curr_shape_points.append(point)

                self.curr_shape_points.append(self.curr_shape_points[0]) # connecting the final points in case not connected
                self.shapes[self.curr_shape_id] = Shape(self.curr_shape_points)
                self.shapesUpdated.emit()

                self.curr_shape_points = []
                self.drawing = False
                self.curr_shape_id += 1
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """handles the paint event, drawing shapes and patterns on the widget.

        Args:
            event (QPaintEvent): the paint event that triggered the redrawing. 
        """
        self.draw_shapes()
        self.draw_patterns()

    def draw_shapes(self) -> None:
        """draws all the shapes on the widget.
        """
        painter = QPainter(self)

        for shape_id, shape in self.shapes.items():
            if shape_id == self.selected_shape_id:
                pen = QPen(Qt.red, 2, Qt.SolidLine)
            else:
                pen = QPen(Qt.black, 2, Qt.SolidLine)
            painter.setPen(pen)

            border_points = shape.border_points
            for i in range(len(border_points) - 1):
                painter.drawLine(border_points[i], border_points[i + 1])

        if self.drawing and len(self.curr_shape_points) > 1:
            pen = QPen(Qt.black, 2, Qt.SolidLine)
            painter.setPen(pen)
            for i in range(len(self.curr_shape_points) - 1):
                painter.drawLine(self.curr_shape_points[i], self.curr_shape_points[i + 1])

    def draw_patterns(self) -> None:
        """draws all the patterns in the shapes on the widget.
        """
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
    def __init__(self, viewer_window: QMainWindow) -> None:
        """initializes the control window.

        Args:
            viewer_window (QMainWindow): the viewer window (main window) associated with the control window.
        """
        super().__init__()
        self.viewer_window = viewer_window 
        self.windowGeo = (500, 500, 500, 500)
        self.buttonSize = (200, 100)
        self.patterns = ['Bidirectional']
        self.initUI()

    def initUI(self) -> None:
        """initializes the user interface for the control window.
        """
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
        self.roi_dropdown.currentIndexChanged.connect(self.onRoiSelected)
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
        pattern_and_delete_buttons= QHBoxLayout()
        self.apply_pattern_button = QPushButton("Apply Pattern", self)
        self.apply_pattern_button.setMinimumSize(200, 50)
        self.apply_pattern_button.clicked.connect(self.onApplyPatternClick)
        pattern_and_delete_buttons.addWidget(self.apply_pattern_button)

        # show/hide the horizontal / vertical spacing input
        self.show_or_hide_spacing_input(False)

        # delete button
        self.delete_button = QPushButton("Delete", self)
        self.delete_button.setMinimumSize(200, 50)
        self.delete_button.clicked.connect(self.onDeleteClick)
        pattern_and_delete_buttons.addWidget(self.delete_button)

        pattern_and_delete_widget= QWidget()
        pattern_and_delete_widget.setLayout(pattern_and_delete_buttons)

        # vertical layout for button group, and ablate button
        main_buttons_layout = QVBoxLayout()
        main_buttons_layout.addWidget(pattern_and_delete_widget)

        # send to ablate button
        self.ablate_button = QPushButton("Ablate", self)
        self.ablate_button.setMinimumSize(200, 50)
        self.ablate_button.setStyleSheet("background-color: red; color: white;")
        self.ablate_button.clicked.connect(self.onAblateClick)
        main_buttons_layout.addWidget(self.ablate_button)

        layout.addLayout(main_buttons_layout)

    def updateRoiDropdown(self) -> None:
        """updates the ROI dropdown with the current shapes.
        """
        self.roi_dropdown.clear()
        self.roi_dropdown.addItem("Select ROI")
        for roi in self.viewer_window.shapes.keys():
            self.roi_dropdown.addItem(f"Shape {roi + 1}")

    def addPatternDropdownItems(self) -> None:
        """adds the patterns to the pattern dropdown.
        """
        for pattern in self.patterns:
            self.pattern_dropdown.addItem(pattern)

    def onApplyPatternClick(self) -> None:
        """applies the selected pattern to the selected ROI.
        """
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
                logging.error("Invalid spacing input")

        self.viewer_window.update()

    def show_or_hide_spacing_input(self, show) -> None:
        """shows or hides the spacing input fields.

        Args:
            show (bool): a boolean indicating whether to show (True) or hide (False) the spacing input fields.
        """
        self.horizontal_spacing_label.setVisible(show)
        self.horizontal_spacing_input.setVisible(show)
        self.vertical_spacing_label.setVisible(show)
        self.vertical_spacing_input.setVisible(show)
        
    def onPatternSelected(self) -> None:
        """handles the selection of a pattern from the dropdown.
        """
        selected_pattern = self.pattern_dropdown.currentText()
        if selected_pattern == "Bidirectional":
            self.show_or_hide_spacing_input(True)
        else:
            self.show_or_hide_spacing_input(False)

    def onAblateClick(self) -> list:
        """collects and returns the ablation coordinates from all the shapes.

        Returns:
            list: a list of lists containing the ablation coordinates for each shape.
        """
        ablate_coords = []
        for shape in self.viewer_window.shapes.values():
            if shape.pattern_points:
                curr_ablation_coords = []
                for coord in shape.pattern_points:
                    curr_ablation_coords.append(coord)
                ablate_coords.append(curr_ablation_coords)

        logging.debug(f"Ablation coordinates: \n {ablate_coords}")
        return ablate_coords
    
    def onRoiSelected(self) -> None:
        """handles the selection of an ROI from the dropdown.
        """
        selected_roi = self.roi_dropdown.currentText()
        if selected_roi:
            if selected_roi == "Select ROI":
                self.viewer_window.selected_shape_id = None
            else:
                roi_id = int(selected_roi.split(" ")[1]) - 1
                self.viewer_window.selected_shape_id = roi_id 
        self.viewer_window.update()

    def onDeleteClick(self) -> None:
        """handles the deletion of shape when the delete button is clicked.
        """
        selected_roi = self.roi_dropdown.currentText()
        if selected_roi and selected_roi != 'Select ROI':
            roi_id = int(selected_roi.split(" ")[1]) - 1
            del self.viewer_window.shapes[roi_id]
            logging.debug(f"roi {roi_id} removed.")
            self.viewer_window.update()
            self.updateRoiDropdown()



if __name__ == "__main__":
    import os

    app = QApplication(sys.argv)
    dac = ViewerWindow()
    ctrl = CtrlWindow(dac)
    dac.show()
    ctrl.show()
    sys.exit(app.exec_())
