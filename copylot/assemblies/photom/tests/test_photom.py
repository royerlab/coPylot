import unittest
from unittest.mock import MagicMock
from photom import photom


class TestPhotom(unittest.TestCase):
    def test_capture(self):
        # Create mock objects for the hardware
        camera = MagicMock()
        laser = MagicMock()
        mirror = MagicMock()
        dac = MagicMock()

        # Instantiate your class with the mock objects
        p = photom(camera, laser, mirror, dac)

        # Call the method you want to test
        p.capture()

        # Assert that the camera's method was called
        camera.capture.assert_called_once()


if __name__ == '__main__':
    unittest.main()
