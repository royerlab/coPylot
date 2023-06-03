from pypylon import pylon as py
from pypylon import genicam
import sys



exitcode = 0


class bCam:
    def __init__(self):
        # get transport layer and all attached devices
        self.cameras = None
        self.tl_factory = py.TlFactory.GetInstance()
        self.devices = self.tl_factory.EnumerateDevices()
        if len(self.devices) == 0:
            raise py.RuntimeException("No camera connected")
        else:
            self.maxCameraToUSe = len(self.devices)
            print(len(self.maxCameraToUSe))
            for device in self.devices:
                print(device.GetFriendlyName())  # return readable name

    def __del__(self):
        self.closecam()
        exitcode = 1
        sys.exit(exitcode)

    def opencam(self):
        try:
            self.cameras = py.InstantCameraArray(min(len(self.devices)),
                                                    self.maxCameraToUSe)  # create multiple camera
            # Create and attach all Pylon Devices.
            for idx, cam in enumerate(self.cameras):
                cam.Attach(self.tlFactory.CreateDevice(self.devices[i]))
                # Print the model name of the camera.
                print("Using device ", cam.GetDeviceInfo().GetModelName())
                camera_serial = cam.DeviceInfo.GetSerialNumber()
                print(f"set context {idx} for camera {camera_serial}")
                cam.SetCameraContext(idx)
            self.cameras.Open()
            self.

        except genicam.GenericException as e:
            # Error handling
            print("An exception occurred. {}".format(e))
            exitcode = 1
            sys.exit(exitcode)
    def closecam(self):
        try:
            # Check whether there is any cameras are running and stop the running cam
            if self.cameras.isGrabbing():
                for idx, cam in enumerate(self.cameras):
                    cam.AcquisitionAbort.Execute()
            #close cam
            self.cameras.Close()
        except genicam.GenericException as e:
            # Error handling
            print("An exception occurred. {}".format(e))
            exitcode = 1
            sys.exit(exitcode)

    def trigermode(self,cam):
        cam.Attach(AcquisitionMode.SetValue(AcquisitionMode_SingleFrame);
)


