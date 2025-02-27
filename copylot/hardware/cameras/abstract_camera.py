from abc import ABCMeta, abstractmethod
from typing import Tuple


class AbstractCamera(metaclass=ABCMeta):
    """AbstractCamera

    This class includes only the members that known to be common
    across different camera adapters that we've implemented. By no
    means this class in a final state. We will be making additions
    as needs rise.

    """

    _device_id = None

    @property
    def device_id(self):
        """Returns device_id (serial number) of the current camera"""
        return self._device_id

    @device_id.setter
    @abstractmethod
    def device_id(self, serial_number):
        """Sets the device_id (serial number) of the current camera"""
        raise NotImplementedError()

    @abstractmethod
    def snap(self):
        """Method to capture a single image from the camera."""
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def list_available_cameras():
        """List all cameras that driver discovers."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def exposure(self) -> float:
        """Current exposure

        Returns
        -------
        float

        """
        raise NotImplementedError()

    @exposure.setter
    @abstractmethod
    def exposure(self, value: float) -> None:
        """Current exposure

        Parameters
        ----------
        value : float

        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def exposure_limits(self) -> Tuple[float, float]:
        """
        Valid minimum and maximum exposure values.

        Returns
        -------
        Tuple
            (min_valid_exposure, max_valid_exposure)
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def bitdepth(self) -> int:
        """Currently selected  bitdepth

        Returns
        -------
        int

        """
        raise NotImplementedError()

    @bitdepth.setter
    @abstractmethod
    def bitdepth(self, value: int) -> None:
        """Currently selected  bitdepth

        Parameters
        ----------
        value : int

        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def image_size(self) -> Tuple[int, int, int, int]:
        """Currently selected image size
        Returns the width, height, offset_x, offset_y of the image

        Returns
        -------
        Tuple[int, int, int, int]

        """
        raise NotImplementedError()

    @image_size.setter
    @abstractmethod
    def image_size(self, value: Tuple[int, int, int, int]) -> None:
        """Currently selected image size
        Sets the width, height, offset_x, offset_y of the image

        Parameters
        ----------
        value : Tuple[int, int, int, int]

        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def image_size_limits(self) -> Tuple[int, int, int, int]:
        """
        Valid minimum and maximum image_size values.

        Returns
        -------
        Tuple
            (min_image_width, max_image_width, min_image_height, max_image_height)
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def binning(self) -> Tuple[int, int]:
        """Current binning

        Returns
        -------
        Tuple[int, int]

        """
        raise NotImplementedError()

    @binning.setter
    @abstractmethod
    def binning(self, value: Tuple[int, int]) -> None:
        """Current binning

        Parameters
        ----------
        value : Tuple[int, int]

        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def gain(self) -> float:
        """Implementations should normalize gain to range [0, 1]

        Returns
        -------
        float
            gain value

        """
        raise NotImplementedError()

    @gain.setter
    @abstractmethod
    def gain(self, value: float) -> None:
        """Implementations should normalize gain to range [0, 1]

        Parameters
        ----------
        value : float
            value to set as new gain

        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def gain_limits(self) -> Tuple[float, float]:
        """
        Valid minimum and maximum gain values.

        Returns
        -------
        Tuple[float, float]
            (min_valid_gain, max_valid_gain)
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def shutter_mode(self) -> str:
        """Current shutter mode

        Returns
        -------
        str

        """
        raise NotImplementedError()

    @shutter_mode.setter
    @abstractmethod
    def shutter_mode(self, mode: str) -> None:
        """Current shutter mode

        Parameters
        ----------
        mode : str

        """
        raise NotImplementedError()
