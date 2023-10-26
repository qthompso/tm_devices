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
    ) -> Tuple[ParameterRange, ParameterRange, ParameterRange]:
        # if we are using the high bandwidth options
        if "02" in self.opt_string or "06" in self.opt_string:
            amplitude_range = ParameterRange(500.0e-3, 1.0)
            offset_range = ParameterRange(-0.0, 0.0)
        else:
            amplitude_range = ParameterRange(50e-3, 2.0)
            offset_range = ParameterRange(-0.5, 0.5)
        # AWG(Arbitrary Waveform Generator)7(Series)xx(GS/s)x(Channels)z(Model)
        sample_rate_range = ParameterRange(10.0e6, int(self.model[4:6])*1.0e9)

        return amplitude_range, offset_range, sample_rate_range
