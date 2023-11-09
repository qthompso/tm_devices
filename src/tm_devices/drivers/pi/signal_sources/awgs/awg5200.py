"""AWG5200 device driver module."""
from typing import Tuple

from tm_devices.commands import AWG5200Mixin
from tm_devices.drivers.pi.signal_sources.awgs.awg import (
    AWG,
    AWGSourceDeviceConstants,
    ParameterBounds,
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
    def _get_series_specific_constraints(
        self,
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        """Get constraints which are dependent on the model series."""
        amplitude_range = ParameterBounds(lower=100e-3, upper=2.0)
        offset_range = ParameterBounds(lower=-0.5, upper=0.5)
        # option is the sample rate in hundreds of Mega Hertz
        sample_rate_range = ParameterBounds(lower=300.0, upper=int(self.opt_string) * 100.0e6)

        return amplitude_range, offset_range, sample_rate_range
