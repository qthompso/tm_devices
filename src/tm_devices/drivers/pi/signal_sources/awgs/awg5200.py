"""AWG5200 device driver module."""
from typing import Optional, Tuple

from tm_devices.commands import AWG5200Mixin
from tm_devices.drivers.pi.signal_sources.awgs.awg import (
    AWG,
    AWGSourceDeviceConstants,
    ParameterRange,
)


class AWG5200(AWG5200Mixin, AWG):
    """AWG5200 device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=16200000,
        memory_min_record_length=1,
    )

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
