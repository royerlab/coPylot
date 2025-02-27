import math
import numpy as np
from numpy.typing import ArrayLike


class ScanAlgorithm:
    """
    Borrowing from Hirofumi's photom-code
    """

    def __init__(self, initial_cord, size, gap, shape, sec_per_cycle):
        """
        Generates lists of x & y coordinates for various shapes with different scanning curves.
        :param initial_cord: the initial coordinates of x & y
        :param size: the bounding box size of the shape
        :param gap: the gap between two scan lines. determined by the beam size
        :param shape: str; outer shape name i.e. 'square' or 'disk'
        :param sec_per_cycle: the amount of seconds to scan one cycle of the entire shape;
                <100 sec (= self.max_num_points / self.sampling_rate)
        """

        self.initial_x = initial_cord[0]
        self.initial_y = initial_cord[1]
        self.height = size[0] / 2
        self.width = size[1] / 2
        self.gap = gap
        self.shape = shape
        max_num_points = 1e7  # max coordinates data to be transferred to DAC; 10MB:6s, 8MB:4s, 4MB:2s, 400kB:<1s
        sampling_rate = int(1e5)  # max sampling rate is 100kS/s
        self.num_points_cycle = int(
            sec_per_cycle * sampling_rate
        )  # number of points for one scan of the entire shape
        self.resolution = 1  # obsoleted argument
        # check if total number of points exceeds the max buffer memory
        if self.num_points_cycle > max_num_points:
            raise ValueError(
                'The total number of points exceeded buffer memory. \nTry shorter sec/cycle or smaller scanning area.'
            )

    def shape_coeff(self, x):
        """
        Output a coefficient for y to generate the desired outer shape.
        Used in generate_lissajous and generate_sin
        :return: lists of x & y coordinates
        """
        if self.shape.lower() in ('square', 'rect'):
            return 1
        elif self.shape.lower() == 'disk':
            return math.sqrt(1 - x**2)
        else:
            ValueError('Invalid shape.')

    def generate_cornerline(self):
        """
        Generates a rigorous raster scan path but hard to scale to different shapes other than square.
        Currently obsolete.
        :return: lists of x and y coordinates
        """
        cord_x = [self.initial_x]
        cord_y = [self.initial_y]
        count_y = 0
        steps_h = max(int(self.width // self.resolution), 1)
        steps_v = max(int(self.gap // self.resolution), 1)
        while cord_y[-1] <= self.initial_y + self.height:
            cord_x += [
                cord_x[-1] + (i + 1) * self.resolution * (-1) ** (count_y % 2)
                for i in range(steps_h)
            ]
            cord_y += [cord_y[-1] for _ in range(steps_h)]
            count_y += 1
            cord_x += [cord_x[-1] for _ in range(steps_v)]
            cord_y += [cord_y[-1] + (i + 1) * self.resolution for i in range(steps_v)]
        return cord_x[:-1], cord_y[:-1]

    def generate_spiral(self):
        """
        :return: lists of x and y coordinates of a spiral
        """
        cord_x = []
        cord_y = []
        r = 0
        aspect = self.width / self.height
        num_cycle = self.height / self.gap
        num_points_unitround = int(self.num_points_cycle / num_cycle)
        i = 0
        if self.shape.lower() == 'disk':
            while r <= self.height:
                x = math.cos(2 * math.pi * i / num_points_unitround)
                y = math.sin(2 * math.pi * i / num_points_unitround)
                cord_x.append(r * x * aspect + self.initial_x)
                cord_y.append(r * y + self.initial_y)
                r += self.gap / num_points_unitround
                i += 1
        elif self.shape.lower() in ('square', 'rect'):
            while r <= self.height:
                if i % num_points_unitround < num_points_unitround / 4:
                    y = r * math.cos(((2 * i / num_points_unitround) // 0.5) * math.pi)
                    x = r * math.tan(
                        2 * math.pi * i / num_points_unitround - math.pi / 4
                    )
                elif (
                    num_points_unitround / 4
                    <= i % num_points_unitround
                    < num_points_unitround / 2
                ):
                    y = -r * math.tan(
                        2 * math.pi * i / num_points_unitround + math.pi / 4
                    )
                    x = -r * math.cos(((2 * i / num_points_unitround) // 0.5) * math.pi)
                elif (
                    num_points_unitround / 2
                    <= i % num_points_unitround
                    < 3 * num_points_unitround / 4
                ):
                    y = -r * math.cos(((2 * i / num_points_unitround) // 0.5) * math.pi)
                    x = -r * math.tan(
                        2 * math.pi * i / num_points_unitround - math.pi / 4
                    )
                else:
                    y = r * math.tan(
                        2 * math.pi * i / num_points_unitround + math.pi / 4
                    )
                    x = r * math.cos(((2 * i / num_points_unitround) // 0.5) * math.pi)
                r += self.gap / num_points_unitround
                i += 1
                cord_x.append(x * aspect + self.initial_x)
                cord_y.append(y + self.initial_y)
        return cord_x, cord_y

    def generate_lissajous(self):
        """
        :return: lists of x and y coordinates of a Lissajous curve
        """
        cord_x = []
        cord_y = []
        r = self.height
        a = 5 * 10 / self.gap
        b = math.pi * 6 * 10 / self.gap
        for i in range(self.num_points_cycle):
            x = math.cos(2 * a * math.pi * i / self.num_points_cycle + (math.pi / 8))
            cord_x.append(self.width * x + self.initial_x)
            cord_y.append(
                self.height
                * self.shape_coeff(x)
                * math.sin(2 * b * math.pi * i / self.num_points_cycle)
                + self.initial_y
            )
        return cord_x, cord_y

    def generate_sin(self):
        """
        :return: lists of x and y coordinates of a sine curve as an approximate raster scan
        """
        startingy = self.initial_y - self.height
        freq = self.height / self.gap
        cord_x = []
        cord_y = []
        for i in range(self.num_points_cycle):
            x = math.sin(2 * math.pi * freq * i / self.num_points_cycle - math.pi / 2)
            cord_x.append(
                self.width * self.shape_coeff(1 - 2 * i / self.num_points_cycle) * x
                + self.initial_x
            )
            cord_y.append(i * 2 * self.height / self.num_points_cycle + startingy)
        return cord_x, cord_y

    def generate_rect(self):
        """
        :return: lists of x and y coordinates of a rectangular
        """
        cord_x = []
        cord_y = []
        num_cycle = self.height * 2 / self.gap
        num_points_unitround = int(self.num_points_cycle / num_cycle)
        x = self.initial_x - self.width
        y = self.initial_y - self.height
        num_points_side = num_points_unitround / 4
        for i in range(num_points_unitround):
            if i % num_points_unitround < num_points_side:
                x += self.width * 2 / num_points_side
            elif (
                num_points_unitround / 4
                <= i % num_points_unitround
                < num_points_unitround / 2
            ):
                y += self.height * 2 / num_points_side
            elif (
                num_points_unitround / 2
                <= i % num_points_unitround
                < 3 * num_points_unitround / 4
            ):
                x -= self.width * 2 / num_points_side
            else:
                y -= self.height * 2 / num_points_side
            cord_x.append(x)
            cord_y.append(y)
        return cord_x, cord_y


def calculate_rectangle_corners(window_size: tuple[int, int], center=[0.0, 0.0]):
    # window_size is a tuple of (width, height)

    # Calculate the coordinates of the rectangle corners
    x0y0 = [
        -window_size[0] / 2 + center[0],
        -window_size[1] / 2 + center[1],
    ]
    x1y0 = [x0y0[0] + window_size[0], x0y0[1]]
    x1y1 = [x0y0[0] + window_size[0], x0y0[1] + window_size[1]]
    x0y1 = [x0y0[0], x0y0[1] + window_size[1]]

    return [x0y0, x1y0, x1y1, x0y1]


def generate_grid_points(rectangle_size: ArrayLike, n_points: int = 5,flip_xy = False) -> np.ndarray:
    """
    Generate grid points for a given rectangle.

    Parameters:
    - rectangle_size: ArrayLike, containing the start and end coordinates of the rectangle
                      as [[start_x, start_y], [end_x, end_y]].
    - n_points: The number of points per row and column in the grid.

    Returns:
    - An array of coordinates for the grid points, evenly distributed across the rectangle in (x,y).

    Example:
    >>> rectangle_size = [[-1, -1], [1, 1]]
    >>> n_points = 3
    >>> generate_grid_points(rectangle_size, n_points)
    array([[-1. , -1. ],
           [ 0. , -1. ],
           [ 1. , -1. ],
           [-1. ,  0. ],
           [ 0. ,  0. ],
           [ 1. ,  0. ],
           [-1. ,  1. ],
           [ 0. ,  1. ],
           [ 1. ,  1. ]], dtype=float32)
    """
    start_x, start_y = rectangle_size[0]
    end_x, end_y = rectangle_size[1]

    # Calculate intervals between points in the grid
    interval_x = (end_x - start_x) / (n_points - 1)
    interval_y = (end_y - start_y) / (n_points - 1)

    # Initialize an array to store the coordinates of the grid points
    grid_points = np.zeros((n_points * n_points, 2), dtype=np.float32)

    # Populate the array with the coordinates of the grid points
    for i in range(n_points):
        for j in range(n_points):
            index = i * n_points + j
            x = start_x + j * interval_x
            y = start_y + i * interval_y
            grid_points[index] = [x, y]

    return grid_points
