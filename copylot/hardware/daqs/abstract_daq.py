from abc import ABCMeta, abstractmethod


class AbstractDAQ(ABCMeta):
    @staticmethod
    @abstractmethod
    def list_available_daqs():
        """List all DAQs that the driver discovers."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def voltage(self):
        """Method to get the voltage in volts."""
        raise NotImplementedError()

    @voltage.setter
    @abstractmethod
    def voltage(self, value):
        """Method to set the voltage in volts."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def voltage_range(self):
        """
        Valid minimum and maximum voltage range values.
        Returns
        -------
        Tuple
            (min_valid_voltage, max_valid_voltage)
        """
        raise NotImplementedError()

    @voltage_range.setter
    @abstractmethod
    def voltage_range(self, value):
        """
        Set the voltage range of the DAQ.
        Parameters
        ----------
        value: Tuple
            (min_valid_voltage, max_valid_voltage)
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def sample_rate(self):
        """Get the sample rate in samples per second."""
        raise NotImplementedError()

    @sample_rate.setter
    @abstractmethod
    def sample_rate(self, value):
        """Set the sample rate in samples per second."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def available_channels(self):
        """Get the list of available channels."""
        raise NotImplementedError()

    @abstractmethod
    def start_acquisition(self):
        """Start data acquisition."""
        raise NotImplementedError()

    @abstractmethod
    def stop_acquisition(self):
        """Stop data acquisition."""
        raise NotImplementedError()

    @abstractmethod
    def read_data(self, num_points):
        """Read a specified number of data points from the DAQ."""
        raise NotImplementedError()

    @abstractmethod
    def calibrate(self):
        """Calibrate the DAQ device."""
        raise NotImplementedError()
