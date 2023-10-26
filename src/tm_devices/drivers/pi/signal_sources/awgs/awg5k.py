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
    ) -> Tuple[ParameterRange, ParameterRange, ParameterRange]:
        amplitude_range = ParameterRange(20.0e-3, 4.5)
        offset_range = ParameterRange(-2.25, 2.25)
        # AWG(Arbitrary Waveform Generator)5(Series)0x(.6 + .6GS/s)x(Channels)z(Model)
        sample_rate_range = ParameterRange(10.0e6, 600.0e6 + (600.0e6 * int(self.model[5])))
        return amplitude_range, offset_range, sample_rate_range
