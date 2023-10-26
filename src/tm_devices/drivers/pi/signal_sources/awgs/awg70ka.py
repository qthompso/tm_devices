"""AWG70KA device driver module."""
from typing import Optional, Tuple

from tm_devices.commands import AWG70KAMixin
from tm_devices.drivers.pi.signal_sources.awgs.awg import (
    AWG,
    AWGSourceDeviceConstants,
    ParameterRange,
)


class AWG70KA(AWG70KAMixin, AWG):
    """AWG70KA device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=2000000000,
        memory_min_record_length=1,
    )

    ################################################################################################
    # Public Methods
    ################################################################################################
    def _get_limited_constraints(
        self,
    ) -> Tuple[ParameterRange, ParameterRange, ParameterRange]:
        amplitude_range = ParameterRange(0.5, 1.0)
        offset_range = ParameterRange(-0.5, 0.5)
        # first digit indicates the number of channels, second and third indicate sample rate (GHz)
        sample_rate_range = ParameterRange(1.5e3, int(self.opt_string[1:3]) * 1.0e9)
        return amplitude_range, offset_range, sample_rate_range
