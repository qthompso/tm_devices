"""AWG5KC device driver module."""
from typing import Optional, Tuple

from tm_devices.commands import AWG5KCMixin
from tm_devices.drivers.pi.signal_sources.awgs.awg5kb import AWG5KB, ParameterRange


class AWG5KC(AWG5KCMixin, AWG5KB):
    """AWG5KC device driver."""

    def _get_limited_constraints(
        self,
    ) -> Tuple[Optional[ParameterRange], Optional[ParameterRange], Optional[ParameterRange]]:
        amplitude_range, offset_range, sample_rate_range = super()._get_limited_constraints()
        # if the model is 500x
        if self.model in ("AWG5002C"):
            sample_rate_range = ParameterRange(10.0e6, 600.0e6)
        # if the model is 501x
        elif self.model in ("AWG5012C", "AWG5014C"):
            sample_rate_range = ParameterRange(10.0e6, 1.2e9)
        # called afterwards so that the frequency can be set
        return amplitude_range, offset_range, sample_rate_range
