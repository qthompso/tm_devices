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
    ) -> Tuple[Optional[ParameterRange], Optional[ParameterRange], Optional[ParameterRange]]:
        amplitude_range = ParameterRange(0.5, 1.0)
        offset_range = ParameterRange(-0.5, 0.5)
        # first digit indicates the number of channels, second and third indicate sample rate (GHz)
        if "150" in self.opt_string:
            sample_rate_range = ParameterRange(1.5e3, 50.0e9)
        elif "225" in self.opt_string:
            sample_rate_range = ParameterRange(1.5e3, 25.0e9)
        elif "216" in self.opt_string:
            sample_rate_range = ParameterRange(1.5e3, 16.0e9)
        elif "208" in self.opt_string:
            sample_rate_range = ParameterRange(1.5e3, 8.0e9)
        else:
            sample_rate_range = None
        return amplitude_range, offset_range, sample_rate_range
