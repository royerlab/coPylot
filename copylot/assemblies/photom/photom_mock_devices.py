from typing import Tuple
from copylot.hardware.cameras.abstract_camera import AbstractCamera
from copylot.hardware.lasers.abstract_laser import AbstractLaser
from copylot.hardware.mirrors.abstract_mirror import AbstractMirror

from copylot import logger


class MockLaser(AbstractLaser):
    def __init__(self, name, serial_number=None, port=None, baudrate=19200, timeout=1):
        self.name = name
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._device_id = serial_number
        self._drive_control_mode = "automatic"
        self._toggle_emission = False
        self._power = 0.0
        self._pulse_mode = False
        self._maximum_power = 100.0
        self._current_control_mode = "automatic"
        self._external_power_control = False
        self._status = "disconnected"

    @property
    def device_id(self):
        return self._device_id

    def connect(self):
        self._status = "connected"
        print("Mock laser connected")

    def disconnect(self):
        self._status = "disconnected"
        print("Mock laser disconnected")

    @property
    def drive_control_mode(self) -> str:
        return self._drive_control_mode

    @drive_control_mode.setter
    def drive_control_mode(self, value: str):
        self._drive_control_mode = value
        print(f"Drive control mode set to {value}")

    @property
    def toggle_emission(self) -> bool:
        return self._toggle_emission

    @toggle_emission.setter
    def toggle_emission(self, value: bool):
        self._toggle_emission = value
        print(f"Laser emission {'enabled' if value else 'disabled'}")

    @property
    def power(self) -> float:
        return self._power

    @power.setter
    def power(self, value: float):
        if 0.0 <= value <= self._maximum_power:
            self._power = value
            print(f"Laser power set to {value} mW")
        else:
            print(f"Power value {value} is out of range")

    @property
    def pulse_mode(self) -> bool:
        return self._pulse_mode

    @pulse_mode.setter
    def pulse_mode(self, value: bool):
        self._pulse_mode = value
        print(f"Laser pulse mode {'enabled' if value else 'disabled'}")

    @property
    def maximum_power(self) -> float:
        return self._maximum_power

    @property
    def current_control_mode(self) -> str:
        return self._current_control_mode

    @current_control_mode.setter
    def current_control_mode(self, value: str):
        self._current_control_mode = value
        print(f"Current control mode set to {value}")

    @property
    def external_power_control(self) -> bool:
        return self._external_power_control

    @external_power_control.setter
    def external_power_control(self, value: bool):
        self._external_power_control = value
        print(f"External power control {'enabled' if value else 'disabled'}")

    @property
    def status(self) -> str:
        return self._status


class MockMirror(AbstractMirror):
    def __init__(
        self,
        name: str = "OPTOTUNE_MIRROR",
        com_port: str = None,
        pos_x: float = 0.0,
        pos_y: float = 0.0,
    ):
        super().__init__()
        self.name = name
        self.mirror = 'mirror_instane'
        self._movement_limits = [-2000.0, 2000.0, -2000.0, 2000.0]
        self._position = [0.0, 0.0]
        self._relative_position = [0.0, 0.0]
        self._step_resolution = 0.01
        self._external_drive_control = "manual"
        self._step_resolution = 0.01
        self._external_drive_control = "manual"
        self.position_x = pos_x
        self.position_y = pos_y

    @property
    def device_id(self):
        return self.name

    @device_id.setter
    def device_id(self, value: str):
        self.name = value

    @property
    def position(self) -> list[float, float]:
        return self._position

    @position.setter
    def position(self, value: list[float, float]):
        if (
            self._movement_limits[0] <= value[0] <= self._movement_limits[1]
            and self._movement_limits[2] <= value[1] <= self._movement_limits[3]
        ):
            self._position = value
            print(f"Mirror position set to {value}")
        else:
            print("Position out of bounds")

    @property
    def position_x(self) -> float:
        return self._position[0]

    @position_x.setter
    def position_x(self, value: float):
        if self._movement_limits[0] <= value <= self._movement_limits[1]:
            self._position[0] = value
            print(f"Mirror position X set to {value}")
        else:
            print("Position X out of bounds")

    @property
    def position_y(self) -> float:
        return self._position[1]

    @position_y.setter
    def position_y(self, value: float):
        if self._movement_limits[2] <= value <= self._movement_limits[3]:
            self._position[1] = value
            print(f"Mirror position Y set to {value}")
        else:
            print("Position Y out of bounds")

    @property
    def relative_position(self) -> list[float, float]:
        return self._relative_position

    @relative_position.setter
    def relative_position(self, value: list[float, float]):
        self._relative_position = value
        print(f"Relative position set to {value}")

    @property
    def movement_limits(self) -> list[float, float, float, float]:
        return self._movement_limits

    @movement_limits.setter
    def movement_limits(self, value: list[float, float, float, float]):
        self._movement_limits = value
        print(f"Movement limits set to {value}")

    @property
    def step_resolution(self) -> float:
        return self._step_resolution

    @step_resolution.setter
    def step_resolution(self, value: float):
        self._step_resolution = value
        print(f"Step resolution set to {value}")

    def set_home(self):
        self._position = [0.0, 0.0]
        print("Mirror home position set to [0.0, 0.0]")

    def set_origin(self, axis: str):
        if axis == 'x':
            self._position[0] = 0.0
        elif axis == 'y':
            self._position[1] = 0.0
        print(f"Mirror origin set for axis {axis}")

    @property
    def external_drive_control(self) -> str:
        return self._external_drive_control

    @external_drive_control.setter
    def external_drive_control(self, value: bool):
        self._external_drive_control = value
        print(f"External drive control set to {value}")

    def voltage_to_position(self, voltage: list[float, float]) -> list[float, float]:
        # Simple conversion for mock purposes
        position = [v * 10 for v in voltage]
        print(f"Converted voltage {voltage} to position {position}")
        return position


class MockArduinoPWM:
    def __init__(self, serial_port, baud_rate):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        print(
            f"MockArduinoPWM initialized with serial port {serial_port} and baud rate {baud_rate}"
        )

    def __del__(self):
        self.close()

    def connect(self):
        print("MockArduinoPWM: Simulating serial connection...")

    def close(self):
        print("MockArduinoPWM: Simulating closing serial connection...")

    def send_command(self, command):
        print(f"MockArduinoPWM: Simulating sending command: {command}")
        # Simulate some processing time
        import time

        time.sleep(0.5)
        # Simulate a response from the Arduino if needed
        response = "OK"  # or simulate different responses based on the command
        print(f"MockArduinoPWM: Received response: {response}")


class MockFlirCamera(AbstractCamera):
    def __init__(self):
        self._cam = None
        self._device_id = "MOCK1234"
        self._nodemap_tldevice = None

    @property
    def cam(self):
        return self._cam

    @cam.setter
    def cam(self, val):
        self._cam = val

    @property
    def nodemap_tldevice(self):
        return self._nodemap_tldevice

    @nodemap_tldevice.setter
    def nodemap_tldevice(self, val):
        self._nodemap_tldevice = val

    @property
    def device_id(self):
        return self._device_id

    def open(self, index=0):
        self._cam = "MockCameraInstance"
        self._nodemap_tldevice = "MockNodeMap"
        logger.info(f"Mock camera opened with index {index}")

    def initialize(self):
        logger.info("Mock camera initialized")

    def close(self):
        self._cam = None
        self._nodemap_tldevice = None
        logger.info("Mock camera closed")

    def list_available_cameras(self):
        return ["MockCamera1", "MockCamera2"]

    def save_image(self, all_arrays, image_format='tiff'):
        if isinstance(all_arrays, list):
            n = len(all_arrays)
        else:
            n = 1
        logger.info(f"Mock save {n} images in {image_format} format")

    def return_image(self, processor, processing_type, wait_time):
        width, height = 640, 480
        image_array = np.random.randint(0, 256, (height, width), dtype=np.uint8)
        logger.info(f"Mock return image of size {width}x{height}")
        return image_array

    def acquire_images(self, mode, n_images, wait_time, processing, processing_type):
        images = [self.return_image(None, None, wait_time) for _ in range(n_images)]
        logger.info(f"Mock acquire {n_images} images in mode {mode}")
        return images if n_images > 1 else images[0]

    def snap(
        self,
        n_images=1,
        mode='Continuous',
        wait_time=1000,
        processing=False,
        processing_type=None,
    ):
        result_array = self.acquire_images(
            mode, n_images, wait_time, processing, processing_type
        )
        return result_array

    @property
    def exposure_limits(self):
        return 100.0, 10000.0

    @property
    def exposure(self):
        return 1000.0

    @exposure.setter
    def exposure(self, exp):
        logger.info(f"Mock set exposure to {exp} microseconds")

    @property
    def gain_limits(self):
        return 0.0, 1.0

    @property
    def gain(self):
        return 0.5

    @gain.setter
    def gain(self, g):
        logger.info(f"Mock set gain to {g * 18.0} dB")

    @property
    def framerate(self):
        return 30.0

    @property
    def bitdepth(self):
        return 8

    @bitdepth.setter
    def bitdepth(self, bit):
        logger.info(f"Mock set bit depth to {bit}")

    @property
    def image_size(self):
        return 640, 480

    @image_size.setter
    def image_size(self, size):
        logger.info(f"Mock set image size to {size}")

    @property
    def image_size_limits(self):
        return 320, 1280, 240, 960

    @property
    def binning(self):
        return 1, 1

    @binning.setter
    def binning(self, val):
        logger.info(f"Mock set binning to {val}")

    @property
    def shutter_mode(self):
        return 1

    @shutter_mode.setter
    def shutter_mode(self, mode):
        logger.info(f"Mock set shutter mode to {mode}")

    @property
    def flip_sensor_X(self):
        return False

    @flip_sensor_X.setter
    def flip_sensor_X(self, value):
        logger.info(f"Mock set flip sensor X to {value}")

    @property
    def flip_sensor_Y(self):
        return False

    @flip_sensor_Y.setter
    def flip_sensor_Y(self, value):
        logger.info(f"Mock set flip sensor Y to {value}")

    @property
    def pixel_format(self):
        return "Mono8"

    @pixel_format.setter
    def pixel_format(self, format_str):
        logger.info(f"Mock set pixel format to {format_str}")
