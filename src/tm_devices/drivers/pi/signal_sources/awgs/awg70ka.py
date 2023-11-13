"""AWG70KA device driver module."""
from functools import cached_property
from types import MappingProxyType
from typing import Tuple

from tm_devices.commands import AWG70KAMixin
from tm_devices.drivers.pi.signal_sources.awgs.awg import (
    AWG,
    AWGChannel,
    AWGSourceDeviceConstants,
    ParameterBounds,
)


class AWG70KAChannel(AWGChannel):
    """AWG70KA channel driver."""

    def set_offset(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the offset on the source.

        Args:
            value: The offset value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        current_high = float(self._pi_device.query(f"{self.name}:VOLTAGE:HIGH?"))
        current_low = float(self._pi_device.query(f"{self.name}:VOLTAGE:LOW?"))

        current_amplitude = current_high - current_low
        high_voltage = round(current_amplitude / 2 + value, 3)
        low_voltage = round(-current_amplitude / 2 + value, 3)
        self._set_high_and_low_voltage(
            high_voltage, low_voltage, tolerance=tolerance, percentage=percentage
        )

    def set_amplitude(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the amplitude on the source.

        Args:
            value: The amplitude value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        current_high = float(self._pi_device.query(f"{self.name}:VOLTAGE:HIGH?"))
        current_low = float(self._pi_device.query(f"{self.name}:VOLTAGE:LOW?"))

        current_amplitude = current_high - current_low
        offset = current_high - (current_amplitude / 2)
        high_voltage = round(value / 2 + offset, 3)
        low_voltage = round(-value / 2 + offset, 3)
        self._set_high_and_low_voltage(
            high_voltage, low_voltage, tolerance=tolerance, percentage=percentage
        )

    def _set_high_and_low_voltage(
        self,
        high_voltage: float,
        low_voltage: float,
        tolerance: float = 0,
        percentage: bool = False,
    ) -> None:
        """Set the HIGH and LOW voltage to the specified values.

        Args:
            high_voltage: The HIGH voltage value to set.
            low_voltage: The LOW voltage value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        self._pi_device.set_if_needed(
            f"{self.name}:VOLTAGE:HIGH",
            high_voltage,
            tolerance=tolerance,
            percentage=percentage,
        )
        self._pi_device.set_if_needed(
            f"{self.name}:VOLTAGE:LOW",
            low_voltage,
            tolerance=tolerance,
            percentage=percentage,
        )


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
    def channel(self) -> "MappingProxyType[str, AWG70KAChannel]":
        """Mapping of channel names to AWGChannel objects."""
        channel_map = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWG70KAChannel(self, channel_name)
        return MappingProxyType(channel_map)  # pyright: ignore[reportUnknownVariableType]

    ################################################################################################
    # Public Methods
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
