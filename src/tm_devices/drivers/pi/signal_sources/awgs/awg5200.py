"""AWG5200 device driver module."""
import time

from functools import cached_property
from types import MappingProxyType
from typing import Optional, Tuple

from tm_devices.commands import AWG5200Mixin
from tm_devices.drivers.pi.signal_sources.awgs.awg import (
    AWG,
    AWGChannel,
    AWGSourceDeviceConstants,
    ParameterRange,
)


class AWG5200Channel(AWGChannel):
    """AWG5200 channel driver."""

    def set_frequency(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the frequency on the source.

        Args:
            value: The frequency value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        self._pi_device.set_if_needed(
            "CLOCK:SRATE",
            round(value, -1),
            tolerance=tolerance,
            percentage=percentage,
        )
        time.sleep(0.1)
        self._pi_device.ieee_cmds.opc()
        self._pi_device.ieee_cmds.cls()
        self._pi_device.poll_query(30, "CLOCK:SRATE?", value, tolerance=10, percentage=percentage)


class AWG5200(AWG5200Mixin, AWG):
    """AWG5200 device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=16200000,
        memory_min_record_length=1,
    )

    ################################################################################################
    # Properties
    ################################################################################################
    @cached_property
    def channel(self) -> "MappingProxyType[str, AWG5200Channel]":
        """Mapping of channel names to AWGChannel objects."""
        channel_map = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWG5200Channel(self, channel_name)
        return MappingProxyType(channel_map)  # pyright: ignore[reportUnknownVariableType]

    ################################################################################################
    # Public Methods
    ################################################################################################
    def _get_limited_constraints(
        self,
    ) -> Tuple[Optional[ParameterRange], Optional[ParameterRange], Optional[ParameterRange]]:
        amplitude_range = ParameterRange(100e-3, 2.0)
        offset_range = ParameterRange(-0.5, 0.5)
        if "50" in self.opt_string:
            sample_rate_range = ParameterRange(300.0, 2.5e9)
        elif "25" in self.opt_string:
            sample_rate_range = ParameterRange(300.0, 2.5e9)
        else:
            sample_rate_range = None
        return amplitude_range, offset_range, sample_rate_range
