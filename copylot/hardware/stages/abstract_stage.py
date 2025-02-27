from abc import ABCMeta, abstractmethod


class AbstractStage(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def list_available_stages():
        """List all stages that driver discovers."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def position(self):
        "Method to get/set the position in um"
        raise NotImplementedError()

    @position.setter
    @abstractmethod
    def position(self, value):
        raise NotImplementedError()

    @property
    @abstractmethod
    def travel_range(self):
        """
        Valid minimum and maximum travel range values.
        Returns
        -------
        Tuple
            (min_valid_position, max_valid_position)
        """
        raise NotImplementedError()

    @travel_range.setter
    @abstractmethod
    def travel_range(self, value):
        """
        Set the travel range of the stage
        ----
        Tuple
            (min_valid_position, max_valid_position)
        """
        raise NotImplementedError()

    @abstractmethod
    def move_relative(self, value):
        "Move a relative distance from current position"
        raise NotImplementedError()

    @abstractmethod
    def move_absolute(self, value):
        "Move to an absolute position"
        raise NotImplementedError()

    @abstractmethod
    def zero_position(self):
        "Move the stage to 0 position"
        raise NotImplementedError()
