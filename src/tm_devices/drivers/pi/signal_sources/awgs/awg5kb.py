"""AWG5KB device driver module."""
from typing import Optional, Tuple

from tm_devices.drivers.pi.signal_sources.awgs.awg5k import AWG5K, ParameterRange


class AWG5KB(AWG5K):
    """AWG5KB device driver."""

    def _get_limited_constraints(
        self,
    ) -> Tuple[Optional[ParameterRange], Optional[ParameterRange], Optional[ParameterRange]]:
        amplitude_range, offset_range, sample_rate_range = super()._get_limited_constraints()
        if self.model in ("AWG5012B"):
            sample_rate_range = ParameterRange(10.0e6, 1.2e9)

        return amplitude_range, offset_range, sample_rate_range
