from typing import List, Tuple
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPolygon
import logging
import math
import numpy as np


class ShapeTrace(QPolygon):
    def __init__(self, border_points: List[Tuple[float, float]]) -> None:
        """initializes a Shape object.

        Args:
            border_points (List[Tuple[float, float]]): a list of tuples representing the border of the shape. each tuple is an (x, y)
        """
        super().__init__(border_points)
        self.border_points = border_points
        self.pattern_style = None
        self.pattern_points = set()

        self.gap = 5
        self.points_per_cycle = 80

    def _pattern_bidirectional(
        self, vertical_spacing: int, horizontal_spacing: int, num_points: int = None
    ) -> None:
        """adds a bidirectional (snaking) pattern to the shape.

        Args:
            vertical_spacing (int): determines how many pixels of space will be between each point in the shape vertically.
            horizontal_spacing (int): determines how many pixels of space will be between each point in the shape horizontally.
        """
        self.border_style = "Bidirectional"
        min_x = self.boundingRect().left()
        max_x = self.boundingRect().right()
        min_y = self.boundingRect().top()
        max_y = self.boundingRect().bottom()

        curr_x = min_x
        curr_y = min_y
        direction = True  # true if moving right, false if moving left

        while curr_y <= max_y and (
            num_points is None or len(self.pattern_points) < num_points
        ):
            if direction:
                while curr_x <= max_x and (
                    num_points is None or len(self.pattern_points) < num_points
                ):
                    if self.containsPoint(QPoint(curr_x, curr_y), Qt.OddEvenFill):
                        self.pattern_points.add((curr_x, curr_y))
                    curr_x += horizontal_spacing
            else:
                while curr_x >= min_x and (
                    num_points is None or len(self.pattern_points) < num_points
                ):
                    if self.containsPoint(QPoint(curr_x, curr_y), Qt.OddEvenFill):
                        self.pattern_points.add((curr_x, curr_y))
                    curr_x -= horizontal_spacing

            curr_y += vertical_spacing
            direction = not direction

            if direction:
                curr_x = min_x
            else:
                curr_x = max_x
        if not self.pattern_points:
            bounding_rect = self.boundingRect()
            center_x = round((bounding_rect.left() + bounding_rect.right()) / 2)
            center_y = round((bounding_rect.top() + bounding_rect.bottom()) / 2)
            self.pattern_points.add((center_x, center_y))
            logging.warning("spacing configuration is too large for the shape.")

    def _pattern_spiral(self, num_points: int = None) -> None:
        """adds a spiral pattern to the shape.

        Args:
            num_points (int): determines how many points will be added to the shape.
        """
        width = self.boundingRect().width()
        height = self.boundingRect().height()

        max_radius = min(width, height) / 2
        
        # starting with 4 turns at minimum
        num_turns = 4
        distance_bt_turns =  max_radius / num_turns
        
        # calculating number of turns based on gap
        while distance_bt_turns < self.gap:
            num_turns += 1
            distance_bt_turns = max_radius / num_turns
        
        theta = np.linspace(0, num_turns * np.pi, 1000)
        radius = theta

        # converting polar -> cartesian coordinates
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)

        # normalize coordinates to the bounding box
        x = (x - x.min()) / (x.max() - x.min()) * width
        y = (y - y.min()) / (y.max() - y.min()) * height

        # calculate cumulative arc length
        arc_length = np.cumsum(np.sqrt(np.diff(x) ** 2 + np.diff(y) ** 2))
        arc_length = np.insert(arc_length, 0, 0)

        # finding maximum possible points based on min gap
        total_length = arc_length[-1]
        max_num_points = int(total_length // self.gap)

        # if num_points is too large for shape, default to max_num_points
        if num_points > max_num_points:
            print(f"num_points: {num_points} is greater than max_num_points: {max_num_points}, defaulting to max_num_points.")
            num_points = max_num_points

        # getting equidistant points along the arc length with at least gap distance b/w 
        target_lengths = np.linspace(0, total_length, num_points)
        indices = np.searchsorted(arc_length, target_lengths)

        # adding points to the pattern
        for idx in indices:
            plot_x = int(x[idx]) + self.boundingRect().left()
            plot_y = int(y[idx]) + self.boundingRect().top()
            point = QPoint(plot_x, plot_y)
            if self.containsPoint(point, Qt.OddEvenFill):
                self.pattern_points.add((plot_x, plot_y))

