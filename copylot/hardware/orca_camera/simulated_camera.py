import time
from os.path import join

import numpy


class SimulatedOrcaCamera:
    def __init__(self, camera_index: int = 0):
        self._camera_index = camera_index

    def run(self, nb_frame: int = 100000, path=None):
        if path is None:
            temp_file = join(get_temp_folder(), "stacks" + str(time.time()))

        frames = []
        for _ in nb_frame:
            frames.append(numpy.random.random((2048, 2048)))

        return frames
