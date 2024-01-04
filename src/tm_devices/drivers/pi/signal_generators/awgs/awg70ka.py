"""AWG70KA device driver module."""
from functools import cached_property
from types import MappingProxyType
from typing import Tuple

from tm_devices.commands import AWG70KAMixin
from tm_devices.drivers.pi.signal_generators.awgs.awg import (
    AWG,
    AWGChannel,
    AWGSourceDeviceConstants,
    ParameterBounds,
)


class AWG70KAChannel(AWGChannel):
    """AWG70KA channel driver."""

    def set_frequency(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the frequency on the source.

        Args:
            value: The frequency value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        self._awg.set_if_needed(
            f"{self.name}:FREQUENCY", value, tolerance=tolerance, percentage=percentage, opc=True
        )

    def set_offset(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the offset on the source.

        Args:
            value: The offset value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        output_signal_path = self._awg.query(f"OUTPUT{self.num}:PATH?")
        if output_signal_path.lower().startswith("dca"):
            super().set_offset(value, tolerance, percentage)
        elif value:
            offset_error = (
                f"The offset can only be set if the output signal path is "
                f'set to "DCAmplified". It is currently set to "{output_signal_path}"'
            )
            raise ValueError(offset_error)


class AWG70KA(AWG70KAMixin, AWG):
    """AWG70KA device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=2000000000,
        memory_min_record_length=1,
    )

    ################################################################################################
    # Properties
    ################################################################################################
    @cached_property
    def source_channel(self) -> "MappingProxyType[str, AWGChannel]":
        """Mapping of channel names to AWGChannel objects."""
        channel_map = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWG70KAChannel(self, channel_name)
        return MappingProxyType(channel_map)

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _get_series_specific_constraints(
        self,
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        """Get constraints which are dependent on the model series."""
        amplitude_range = ParameterBounds(lower=0.5, upper=1.0)
        offset_range = ParameterBounds(lower=-0.5, upper=0.5)
        # first digit indicates the number of channels, second and third indicate sample rate (GHz)
        sample_rate_range = ParameterBounds(lower=1.5e3, upper=int(self.opt_string[1:3]) * 1.0e9)
        return amplitude_range, offset_range, sample_rate_range
