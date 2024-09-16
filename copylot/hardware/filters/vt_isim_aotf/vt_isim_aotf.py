from ctypes import WinDLL, c_int, c_ulong, POINTER, byref, c_bool
from enum import Enum


VTI_HARDWARE_AOTF_USB = 5


class AOTF_MODES(Enum):
    VTI_AOTF_MANUAL = 0
    VTI_AOTF_SOFTWARE = 1


class AOTF:
    """AOTF

    Parameters
    ----------
    channel_names : tuple

    """

    def __init__(
        self,
        dll_path=None,
        channel_names: tuple = (),
    ):
        self.dll = WinDLL(dll_path)
        self.dll.vti_Initialise.argtypes = (c_int, POINTER(c_ulong))
        self.dll.vti_Initialise.restype = c_ulong

        self.device = c_ulong()
        response = self.dll.vti_Initialise(VTI_HARDWARE_AOTF_USB, byref(self.device))
        print(self.parse_error_message(hex(response)))

        self.shutter_on = False
        self.channel_names = channel_names
        self.channel_power_status = {
            channel_name: False for channel_name in channel_names
        }

    def __del__(self):
        raise NotImplementedError()

    @staticmethod
    def parse_error_message(message):
        return {
            "0x1": "VTI_SUCCESS",
            "0x8000001": "VTI_ERR_NOT_INITIALISED",
            "0x8000002": "VTI_ERR_DEVICE_NOT_FOUND",
            "0x8000003": "VTI_ERR_PORT_NOT_OPEN",
            "0x8000004": "VTI_ERR_SENDING_DATA",
            "0x8000005": "VTI_ERR_P1_INVALID",
            "0x8000006": "VTI_ERR_P2_INVALID",
            "0x8000007": "VTI_ERR_P3_INVALID",
            "0x8000008": "VTI_ERR_MOTOR_HOME_FAILED",
            "0x8000009": "VTI_ERR_NOT_SUPPORTED",
            "0x800000A": "VTI_ERR_PORT_NOT_SET",
            "0x800000B": "VTI_ERR_ALREADY_INITIALISED",
            "0x800000C": "VTI_ERR_TIMEOUT_OCCURED",
            "0x800000D": "VTI_ERR_INCORRECT_MODE",
            "0x800000E": "VTI_ERR_P4_INVALID",
        }[message]

    def set_intensity(self, channel_name: str, intensity: int):
        if channel_name not in self.channel_names:
            raise ValueError(f"Channel: {channel_name} is not a valid option...")

        if intensity < 0 or intensity > 100:
            raise ValueError(
                f"Intensity has to be between [0,100], {intensity} is invalid..."
            )

        # Make a call to vti_SetIntensity()
        raise NotImplementedError()

    def set_channel_power_status(self, channel_name: str, power: bool = False):
        if channel_name in self.channel_names:
            self.channel_power_status[channel_name] = power

            # Make a call to vti_SetTTLBitmask()
        else:
            raise ValueError(f"No channel exist with given {channel_name}...")

    def set_shutter(self, open_shutter: bool = False):
        # Make a call to vti_SetShutter()
        self.dll.vti_SetShutter.argtypes = (c_ulong, c_bool)
        self.dll.vti_SetShutter.restype = c_ulong

        response = self.dll.vti_SetShutter(self.device, open_shutter)
        print(self.parse_error_message(hex(response)))
