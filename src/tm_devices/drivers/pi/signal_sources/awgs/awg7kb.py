"""AWG7KB device driver module."""
from typing import Optional, Tuple

from tm_devices.drivers.pi.signal_sources.awgs.awg7k import AWG7K, ParameterRange


class AWG7KB(AWG7K):
    """AWG7KB device driver."""

    def _get_limited_constraints(
        self,
    ) -> Tuple[Optional[ParameterRange], Optional[ParameterRange], Optional[ParameterRange]]:
        amplitude_range, offset_range, sample_rate_range = super()._get_limited_constraints()
        # AWG(Arbitrary Waveform Generator)7(Series)06(GS/s)1,2(Channels)B(Model)
        if self.model in ("AWG7061B", "AWG7061B"):
            sample_rate_range = ParameterRange(10.0e6, 6.0e9)
        # AWG(Arbitrary Waveform Generator)7(Series)12(GS/s)1,2(Channels)B(Model)
        elif self.model in ("AWG7121B", "AWG7121B"):
            sample_rate_range = ParameterRange(10.0e6, 12.0e9)

        return amplitude_range, offset_range, sample_rate_range
