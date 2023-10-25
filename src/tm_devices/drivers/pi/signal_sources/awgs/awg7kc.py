"""AWG7K device driver module."""
from typing import Optional, Tuple

from tm_devices.commands import AWG7KCMixin
from tm_devices.drivers.pi.signal_sources.awgs.awg7kb import AWG7KB, ParameterRange


class AWG7KC(AWG7KCMixin, AWG7KB):
    """AWG7KC device driver."""

    ################################################################################################
    # Public Methods
    ################################################################################################
    def _get_limited_constraints(
        self,
    ) -> Tuple[Optional[ParameterRange], Optional[ParameterRange], Optional[ParameterRange]]:
        amplitude_range, offset_range, sample_rate_range = super()._get_limited_constraints()
        if "02" not in self.opt_string and not "06" in self.opt_string:
            amplitude_range = ParameterRange(50.0e-3, 2.0)
            offset_range = ParameterRange(-0.5, 0.5)
        # AWG(Arbitrary Waveform Generator)7(Series)08(GS/s)2(Channels)C(Model)
        if self.model in "AWG7082C":
            sample_rate_range = ParameterRange(8.0e6, 8.0e9)
        # AWG(Arbitrary Waveform Generator)7(Series)12(GS/s)2(Channels)C(Model)
        elif self.model in "AWG7122C":
            sample_rate_range = ParameterRange(10.0e6, 12.0e9)

        return amplitude_range, offset_range, sample_rate_range
