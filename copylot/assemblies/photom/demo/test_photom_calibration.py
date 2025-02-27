import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication, QMainWindow

# Import the classes and functions you want to test
from copylot.assemblies.photom.demo.photom_calibration import (
    LaserWidget,
    MirrorWidget,
    PhotomApp,
    LaserMarkerWindow,
)


class TestLaserWidget(unittest.TestCase):
    def test_update_power(self):
        # Create a mock laser object
        laser = MagicMock()
        laser.power = 50

        # Create an instance of the LaserWidget with the mock laser
        widget = LaserWidget(laser)

        # Call the update_power method with a new value
        widget.update_power(75)

        # Check that the laser's power was updated
        self.assertEqual(laser.set_power.call_args[0][0], 75)

        # Check that the power_label text was updated
        self.assertEqual(widget.power_label.text(), "Power: 75")


class TestMirrorWidget(unittest.TestCase):
    def test_update_mirror_x(self):
        # Create a mock mirror object
        mirror = MagicMock()
        mirror.x = 50

        # Create an instance of the MirrorWidget with the mock mirror
        widget = MirrorWidget(mirror)

        # Call the update_mirror_x method with a new value
        widget.update_mirror_x(75)

        # Check that the mirror's x position was updated
        self.assertEqual(mirror.x, 75)

        # Check that the mirror_x_label text was updated
        self.assertEqual(widget.mirror_x_label.text(), "X: 75")


class TestPhotomApp(unittest.TestCase):
    def setUp(self):
        # Create a mock PhotomAssembly object
        self.photom_assembly = MagicMock()

        # Create a mock QMainWindow object
        self.photom_window = MagicMock()

        # Create a mock demo_window object
        self.demo_window = MagicMock()

        # Create an instance of the PhotomApp with the mock objects
        self.app = PhotomApp(
            self.photom_assembly, self.photom_window, demo_window=self.demo_window
        )

    def test_calibrate(self):
        # Create a mock mirror object
        mirror = MagicMock()
        mirror.name = "Mirror 1"

        # Set the mirrors attribute of the PhotomApp to a list containing the mock mirror
        self.app.mirrors = [mirror]

        # Set the currentText method of the mirror_dropdown to return the name of the mock mirror
        self.app.mirror_dropdown.currentText = MagicMock(return_value="Mirror 1")

        # Call the calibrate method
        self.app.calibrate()

        # Check that the calibrate method of the mock PhotomAssembly was called with the index of the mock mirror
        self.assertEqual(
            self.photom_assembly.calibrate.call_args[0][0],
            self.app.mirrors.index(mirror),
        )

    def test_done_calibration(self):
        # Create a mock mirror object
        mirror = MagicMock()
        mirror.name = "Mirror 1"

        # Set the mirrors attribute of the PhotomApp to a list containing the mock mirror
        self.app.mirrors = [mirror]

        # Set the _calibrating_mirror_idx attribute of the PhotomApp to the index of the mock mirror
        self.app._calibrating_mirror_idx = self.app.mirrors.index(mirror)

        # Call the done_calibration method
        self.app.done_calibration()

        # Check that the save_matrix method of the mock AffineTransform object was called
        self.assertTrue(mirror.affine_trans_obj.save_matrix.called)

    def test_update_transparency(self):
        # Call the update_transparency method with a new value
        self.app.update_transparency(50)

        # Check that the transparency_label text was updated
        self.assertEqual(self.app.transparency_label.text(), "Transparency: 50%")


class TestLaserMarkerWindow(unittest.TestCase):
    def test_init(self):
        # Create an instance of the LaserMarkerWindow
        window = LaserMarkerWindow()

        # Check that the window is an instance of QMainWindow
        self.assertIsInstance(window, QMainWindow)


if __name__ == "__main__":
    # Create a QApplication instance before running the tests
    app = QApplication([])

    # Run the tests
    unittest.main()

    # Close the QApplication instance after running the tests
    app.quit()
