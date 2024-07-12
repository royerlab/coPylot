import PySpin
import sys


class FlirCamera:
    def __init__(self):
        _system = PySpin.System.GetInstance()

        print(_system.GetCameras())


if __name__ == '__main__':
    print(f"spawned proc version: {sys.version}")
    flir_camera = FlirCamera()
