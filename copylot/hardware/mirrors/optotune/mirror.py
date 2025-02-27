"""
@author:Yang Liu

Optotune Tip-tilt mirror controller MR-E-2 python wrapper

For more details regarding operation, refer to the manuals in https://www.optotune.com/fast-steering-mirrors

"""
from os import device_encoding
from zmq import device
from copylot import logger
from copylot.hardware.mirrors.optotune import optoMDC
from copylot.hardware.mirrors.abstract_mirror import AbstractMirror

# TODO: switch device ID for the serial number


class OptoMirror(AbstractMirror):
    def __init__(
        self,
        name: str = "OPTOTUNE_MIRROR",
        com_port: str = None,
        pos_x: float = 0.0,
        pos_y: float = 0.0,
    ):
        """
        Wrapper for Optotune mirror controller MR-E-2.
        establishes a connection through COM port

        """
        self.name = name
        self.mirror = optoMDC.connect(
            com_port
            if com_port is not None
            else optoMDC.tools.list_comports.get_mre2_port()
        )

        self.channel_x = self.mirror.Mirror.Channel_0
        self.channel_x.SetControlMode(optoMDC.Units.XY)
        self.channel_x.StaticInput.SetAsInput()

        self.channel_y = self.mirror.Mirror.Channel_1
        self.channel_y.SetControlMode(optoMDC.Units.XY)
        self.channel_y.StaticInput.SetAsInput()
        logger.info("mirror connected")
        self.position_x = pos_x
        self.position_y = pos_y

        self._movement_limits = [-1.0, 1.0, -1.0, 1.0]

    def __del__(self):
        self.position_x = 0
        self.position_y = 0
        self.mirror.disconnect()
        logger.info("mirror disconnected")

    @property
    def device_id(self):
        return self.name

    @device_id.setter
    def device_id(self, value: str):
        self.name = value
        logger.info(f"device_id set to: {value}")

    @property
    def position(self):
        """
        Returns
        -------
        float:
            Returning value is the current normalized angular value of the mirror
            value = theta/tan(50degree)
            50 degree is the maximum optical deflection angle for each direction.
        """
        return self.position_x, self.position_y

    @position.setter
    def position(self, value: list[float, float]):
        """
        Parameters
        ----------
        value:list[float,float]
            The normalized angular value, value = theta/tan(50degree)
            50 degree is the maximum optical deflection angle for each direction.
            Here x has a range limits of [-1,1] , The combination of value for x-axis and y-axis should be less than 1
            (ex. x^2+y^1<1)
            when |x|<0.7 and |y| <0.7 any combination works. otherwise, one will be reduced to value to
            nearest edge of the unit circle
        """
        self.position_x = value[0]
        self.position_y = value[1]
        logger.info(f"Position set to: {value}")

    @property
    def position_x(self):
        """
        Returns
        -------
        float:
            Returning value is the current normalized angular value of the mirror
            value = theta/tan(50degree)
            50 degree is the maximum optical deflection angle for each direction.

        """
        return self.channel_x.StaticInput.GetXY()[0]

    @position_x.setter
    def position_x(self, value):
        """
        Parameters
        ----------
        value:float
            The normalized angular value, value = theta/tan(50degree)
            50 degree is the maximum optical deflection angle for each direction.
            Here x has a range limits of [-1,1] , The combination of value for x-axis and y-axis should be less than 1
            (ex. x^2+y^1<1)
            when |x|<0.7 and |y| <0.7 any combination works. otherwise, one will be reduced to value to
            nearest edge of the unit circle
        """
        self.channel_x.StaticInput.SetXY(value)
        logger.info(f"position_x set to: {value}")

    @property
    def position_y(self):
        """
        Returns
        -------
        float:
            Returning value is the current normalized angular value of the mirror
            value = theta/tan(50degree)
            50 degree is the maximum optical deflection angle for each direction.
        """
        return self.channel_y.StaticInput.GetXY()[0]

    @position_y.setter
    def position_y(self, value):
        """
        Parameters
        ----------
        value(float):
            The normalized angular value, value = theta/tan(50degree)
            50 degree is the maximum optical deflection angle for each direction.
            Here x has a range limits of [-1,1] , The combination of value for x-axis and y-axis should be less than 1
            (ex. x^2+y^1<1)
            when |x|<0.7 and |y| <0.7 any combination works. otherwise, one will be reduced to value to
            nearest edge of the unit circle

        """
        self.channel_y.StaticInput.SetXY(value)
        logger.info(f"position_y set to: {value}")

    @property
    def relative_position(self) -> list[float, float]:
        """Get the current relative mirror position"""
        pass

    @relative_position.setter
    def relative_position(self, value: list[float, float]):
        """Set the relative mirror position"""
        pass

    @property
    def movement_limits(self) -> list[float, float, float, float]:
        """Get the current mirror movement limits"""
        return self._movement_limits

    @movement_limits.setter
    def movement_limits(self, value: list[float, float, float, float]):
        """Set the mirror movement limits"""
        self._movement_limits = value

    @property
    def step_resolution(self) -> float:
        """Get the current mirror step resolution"""
        pass

    @step_resolution.setter
    def step_resolution(self, value: float):
        """Set the mirror step resolution"""
        pass

    def set_home(self):
        """Set the mirror home position"""
        pass

    def set_origin(self, axis: str):
        """Set the mirror origin for a specific axis"""
        pass

    @property
    def external_drive_control(self) -> str:
        """Get the current mirror drive mode"""
        pass

    @external_drive_control.setter
    def external_drive_control(self, value: bool):
        """Set the mirror drive mode"""
        pass

    def voltage_to_position(self, voltage: list[float, float]) -> list[float, float]:
        """Convert voltage to position"""
        pass
