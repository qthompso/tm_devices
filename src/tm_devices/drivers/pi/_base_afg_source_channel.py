"""Base AFG source channel driver module."""
from abc import abstractmethod

from tm_devices.drivers.pi._base_source_channel import BaseSourceChannel
from tm_devices.drivers.pi.pi_device import PIDevice
from tm_devices.helpers.enums import SignalGeneratorFunctionBase


class BaseAFGSourceChannel(BaseSourceChannel):
    """Base AFG source channel driver."""

    def __init__(self, pi_device: PIDevice, channel_name: str) -> None:
        """Create an AFG source channel.

        Args:
            pi_device: A PI device.
            channel_name: The channel name for the AFG source channel.
        """
        super().__init__(pi_device=pi_device, channel_name=channel_name)

    @abstractmethod
    def set_burst_count(self, value: int) -> None:
        """Set the number of wavelengths to be generated when the source channel is set to burst.

        Args:
            value: The number of wavelengths to be generated within [1, 1000000].
        """
        raise NotImplementedError

    @abstractmethod
    def set_function(self, value: SignalGeneratorFunctionBase) -> None:
        """Set the function to output on the source channel.

        Args:
            value: The name of the function to output.
        """
        raise NotImplementedError

    @abstractmethod
    def set_ramp_symmetry(self, value: float) -> None:
        """Set the symmetry of the ramp waveform on the source channel.

        Args:
            value: The symmetry value to set within [0, 100].
        """
        raise NotImplementedError

    @abstractmethod
    def setup_burst_waveform(self, burst_count: int) -> None:
        """Prepare the source channel for a burst waveform.

        Args:
            burst_count: The number of wavelengths to be generated.
        """
        raise NotImplementedError
