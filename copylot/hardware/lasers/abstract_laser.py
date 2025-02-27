from abc import ABCMeta, abstractmethod
from typing import Tuple


class AbstractLaser(metaclass=ABCMeta):
    """AbstractLaser

    This class includes only the members that known to be common
    across different laser adapters. By no
    means this class in a final state. We will be making additions
    as needs rise.

    """

    _device_id = None

    @property
    def device_id(self):
        """Returns device_id (serial number) of the current laser"""
        return self._device_id

    @abstractmethod
    def connect(self):
        """Connect to the laser"""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the laser"""
        pass

    @property
    @abstractmethod
    def drive_control_mode(self) -> str:
        """Get the current laser drive control mode"""
        pass

    @drive_control_mode.setter
    @abstractmethod
    def drive_control_mode(self, value: bool):
        """Set the laser drive control mode"""
        pass

    @property
    @abstractmethod
    def toggle_emission(self) -> bool:
        """Toggle laser emission"""
        pass

    @toggle_emission.setter
    @abstractmethod
    def toggle_emission(self, value: bool):
        """Toggle laser emission"""
        pass

    @property
    @abstractmethod
    def power(self) -> float:
        """Get the current laser power"""
        pass

    @power.setter
    @abstractmethod
    def power(self, value: float):
        """Set the laser power"""
        pass

    @property
    @abstractmethod
    def pulse_mode(self) -> bool:
        """Get the current laser pulse mode"""
        pass

    @pulse_mode.setter
    @abstractmethod
    def pulse_mode(self, value: bool):
        """Set the laser pulse mode"""
        pass

    @property
    @abstractmethod
    def maximum_power(self) -> float:
        """Get the current laser maximum power"""
        pass

    @property
    @abstractmethod
    def current_control_mode(self) -> str:
        """Get the current laser current control mode"""
        pass

    @current_control_mode.setter
    @abstractmethod
    def current_control_mode(self, value: str):
        """Set the laser current control mode"""
        pass

    @property
    @abstractmethod
    def external_power_control(self) -> bool:
        """Get the current laser external power control"""
        pass

    @external_power_control.setter
    @abstractmethod
    def external_power_control(self, value: bool):
        """Set the laser external power control"""
        pass

    @property
    @abstractmethod
    def status(self) -> str:
        """Get the current laser status"""
        pass
