"""AWG5K device driver module."""
from typing import Optional, Tuple

from tm_devices.commands import AWG5KMixin
from tm_devices.drivers.pi.signal_sources.awgs.awg import (
    AWG,
    AWGSourceDeviceConstants,
    ParameterRange,
)


class AWG5K(AWG5KMixin, AWG):
    """AWG5K device driver."""

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
        if "02" in self.opt_string or "06" in self.opt_string:
            amplitude_range = ParameterRange(500.0e-3, 1.0)
            offset_range = ParameterRange(-0.0, 0.0)
        else:
            amplitude_range = ParameterRange(20.0e-3, 4.5)
            offset_range = ParameterRange(-2.25, 2.25)
        # if the model is 500x
        if self.model in ("AWG5002", "AWG5004"):
            sample_rate_range = ParameterRange(10.0e6, 600.0e6)
        # if the model is 501x
        elif self.model in ("AWG5012", "AWG5014"):
            sample_rate_range = ParameterRange(10.0e6, 1.2e9)
        else:
            sample_rate_range = None
        return amplitude_range, offset_range, sample_rate_range
