# flake8: noqa
import ctypes
from ctypes import *

errors = {
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
}

VTI_HARDWARE_AOTF_USB = 5

device = ctypes.c_ulong()


dll = ctypes.WinDLL("C:\Program Files\Micro-Manager-2.0\VisiSDK.dll")

print(dll)

dll.vti_Initialise.argtypes = (c_int, POINTER(ctypes.c_ulong))
dll.vti_Initialise.restype = ctypes.c_ulong

response = dll.vti_Initialise(VTI_HARDWARE_AOTF_USB, byref(device))
print(errors[hex(response)])


dll.vti_SetShutter.argtypes = (ctypes.c_ulong, c_bool)
dll.vti_SetShutter.restype = ctypes.c_ulong

response = dll.vti_SetShutter(device, True)
print(errors[hex(response)])
