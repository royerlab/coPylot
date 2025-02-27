import os
import sys

import yaml
from PyQt5.QtWidgets import QApplication

from copylot.assemblies.photom.gui.windows import PhotomApp
from copylot.assemblies.photom.photom import PhotomAssembly


def load_config(config: str) -> dict:
    assert config.endswith(".yml"), "Config file must be a .yml file"
    # TODO: this should be a function that parses the config_file and returns the photom_assembly
    # Load the config file and parse it
    with open(config, "r") as config_file:
        config_dict = yaml.load(config_file, Loader=yaml.FullLoader)
    return config_dict


def make_photom_assembly(config):
    lasers = [
        Laser(
            name=laser_data["name"],
            port=laser_data["COM_port"],
        )
        for laser_data in config["lasers"]
    ]
    mirrors = [
        Mirror(
            name=mirror_data["name"],
            com_port=mirror_data["COM_port"],
            pos_x=mirror_data["x_position"],
            pos_y=mirror_data["y_position"],
        )
        for mirror_data in config["mirrors"]
    ]
    affine_matrix_paths = [mirror['affine_matrix_path'] for mirror in config['mirrors']]

    # Check that the number of mirrors and affine matrices match
    assert len(mirrors) == len(affine_matrix_paths)

    # Load photom assembly
    photom_assembly = PhotomAssembly(
        laser=lasers, mirror=mirrors, affine_matrix_path=affine_matrix_paths
    )
    return photom_assembly


if __name__ == "__main__":
    DEMO_MODE = False
    # TODO: grab the actual value if the camera is connected to photom_assmebly
    # CAMERA_SENSOR_YX = (2048, 2448)

    if DEMO_MODE:
        from copylot.assemblies.photom.photom_mock_devices import (
            MockArduinoPWM,
            MockLaser,
            MockMirror,
        )

        Laser = MockLaser
        Mirror = MockMirror
        ArduinoPWM = MockArduinoPWM
    else:
        from copylot.assemblies.photom.utils.arduino import ArduinoPWM as ArduinoPWM
        from copylot.hardware.lasers.vortran.vortran import VortranLaser as Laser
        from copylot.hardware.mirrors.optotune.mirror import OptoMirror as Mirror

    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "..", "demo", "photom_VIS_config.yml")
    config = load_config(config_path)
    photom_assembly = make_photom_assembly(config)

    # QT APP
    app = QApplication(sys.argv)

    # Get screen dimensions
    screen = app.primaryScreen()
    screen_geometry = screen.geometry()

    # Calculate window positions - place windows side by side
    control_window_pos = (50, 50)  # Offset from top-left corner

    arduino = [ArduinoPWM(serial_port='COM10', baud_rate=115200)]

    if DEMO_MODE:
        ctrl_window = PhotomApp(
            photom_assembly=photom_assembly,
            photom_window_pos=control_window_pos,
            demo_mode=DEMO_MODE,
            arduino=arduino,
        )
    else:
        ctrl_window = PhotomApp(
            photom_assembly=photom_assembly,
            photom_window_pos=control_window_pos,
            arduino=arduino,
        )

    sys.exit(app.exec_())
