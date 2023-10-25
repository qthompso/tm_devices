"""AWG7K device driver module."""
from typing import Optional, Tuple

from tm_devices.commands import AWG7KMixin
from tm_devices.drivers.pi.signal_sources.awgs.awg import (
    AWG,
    AWGSourceDeviceConstants,
    ParameterRange,
)


class AWG7K(AWG7KMixin, AWG):
    """AWG7K device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=32400000,
        memory_min_record_length=2,
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
            amplitude_range = ParameterRange(100e-3, 2.0)
            offset_range = ParameterRange(-0.5, 0.5)
        # AWG(Arbitrary Waveform Generator)7(Series)05(GS/s)1,2(Channels)
        if self.model in ("AWG7051", "AWG7052"):
            sample_rate_range = ParameterRange(10.0e6, 5.0e9)
        # AWG(Arbitrary Waveform Generator)7(Series)10(GS/s)1,2(Channels)
        elif self.model in ("AWG7101", "AWG7102"):
            sample_rate_range = ParameterRange(10.0e6, 10.0e9)
        else:
            sample_rate_range = None
        return amplitude_range, offset_range, sample_rate_range
