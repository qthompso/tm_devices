"""AWG5K device driver module."""
from typing import Optional, Tuple

from tm_devices.commands import AWG5KMixin
from tm_devices.drivers.pi.signal_generators.awgs.awg import (
    AWG,
    AWGSourceDeviceConstants,
    ParameterBounds,
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

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _get_series_specific_constraints(
        self,
        output_path: Optional[SignalSourceOutputPaths],
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        """Get constraints which are dependent on the model series."""
        if not output_path:
            output_path = SignalSourceOutputPaths.DCA

        amplitude_range = ParameterBounds(lower=20.0e-3, upper=4.5)
        if output_path == SignalSourceOutputPaths.DCA:
            offset_range = ParameterBounds(lower=-2.25, upper=2.25)
        else:
            offset_range = ParameterBounds(lower=-0.0, upper=0.0)
        # AWG(Arbitrary Waveform Generator)5(Series)0x(.6 + .6GS/s)x(Channels)z(Model)
        sample_rate_range = ParameterBounds(
            lower=10.0e6, upper=600.0e6 + (600.0e6 * int(self.model[5]))
        )
        return amplitude_range, offset_range, sample_rate_range
