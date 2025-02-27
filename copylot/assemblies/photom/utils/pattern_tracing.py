from typing import List, Tuple
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPolygon
import logging
from collections import deque
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
        self.ablation_points = []  # points to be ablated
        self.pattern_points = (
            []
        )  # points to be plotted in gray for pattern visualization

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
        if horizontal_spacing < self.gap:
            logging.warning(
                f"horizontal spacing is too small for the gap. defaulting to gap ({self.gap})."
            )
            horizontal_spacing = self.gap
        if vertical_spacing < self.gap:
            logging.warning(
                f"vertical spacing is too small for the gap. defaulting to gap ({self.gap})."
            )
            vertical_spacing = self.gap
        self.border_style = "Bidirectional"
        min_x = self.boundingRect().left()
        max_x = self.boundingRect().right()
        min_y = self.boundingRect().top()
        max_y = self.boundingRect().bottom()

        center_x = round((min_x + max_x) / 2)
        center_y = round((min_y + max_y) / 2)

        visited = set()
        queue = deque([(center_x, center_y)])
        visited.add((center_x, center_y))
        directions = [
            (0, -vertical_spacing), # up
            (horizontal_spacing, 0), # right
            (0, vertical_spacing), # down
            (-horizontal_spacing, 0), # left
        ]

        while queue and (num_points is None or len(self.ablation_points) < num_points):
            curr_x, curr_y = queue.popleft()
            self.ablation_points.append((curr_x, curr_y))

            for dx, dy in directions:
                new_x, new_y = curr_x + dx, curr_y + dy
                if (
                    self.containsPoint(QPoint(new_x, new_y), Qt.OddEvenFill)
                    and (new_x, new_y) not in visited
                ):
                    queue.append((new_x, new_y))
                    visited.add((new_x, new_y))
        if not self.ablation_points:
            self.ablation_points.append((center_x, center_y))
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
        distance_bt_turns = max_radius / num_turns

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
            print(
                f"num_points: {num_points} is greater than max_num_points: {max_num_points}, defaulting to max_num_points."
            )
            num_points = max_num_points

        # getting equidistant points along the arc length with at least gap distance b/w
        target_lengths = np.linspace(0, total_length, num_points)
        indices = np.searchsorted(arc_length, target_lengths)
        indices = set(indices)

        for idx in range(len(x)):
            plot_x = int(x[idx]) + self.boundingRect().left()
            plot_y = int(y[idx]) + self.boundingRect().top()
            point = QPoint(plot_x, plot_y)
            if idx in indices:
                if self.containsPoint(point, Qt.OddEvenFill):
                    self.ablation_points.append((plot_x, plot_y))
            else:
                if self.containsPoint(point, Qt.OddEvenFill):
                    self.pattern_points.append((plot_x, plot_y))
