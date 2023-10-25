"""AFG3KB device driver module."""
from typing import Optional, Tuple

from tm_devices.commands import AFG3KBMixin
from tm_devices.drivers.pi.signal_sources.afgs.afg3k import (
    AFG3K,
    ParameterRange,
    SignalSourceFunctionsAFG,
)


class AFG3KB(AFG3KBMixin, AFG3K):
    """AFG3KB device driver."""

    ################################################################################################
    # Public Methods
    ################################################################################################
    def _get_limited_constraints(
        self, function: Optional[SignalSourceFunctionsAFG] = None, frequency: Optional[float] = None
    ) -> Tuple[ParameterRange, ParameterRange, ParameterRange, ParameterRange]:
        # AFG(Arbitrary Function Generator)3(Series)02(*10^7 Mhz Sin)1,2(Channels)B(Model)
        amplitude_range = ParameterRange(20.0e-3, 20.0)
        offset_range = ParameterRange(-10.0, 10.0)
        sample_rate_range = ParameterRange(1, 250.0e6)
        if function.name in {
            SignalSourceFunctionsAFG.ARBITRARY.name,
            SignalSourceFunctionsAFG.PULSE.name,
            SignalSourceFunctionsAFG.SQUARE.name,
        }:
            frequency_range = ParameterRange(1.0e-3, 12.5e6)
        elif function.name in {SignalSourceFunctionsAFG.SIN.name}:
            frequency_range = ParameterRange(1.0e-6, 25.0e6)
        else:
            frequency_range = ParameterRange(1.0e-6, 250.0e3)
        return amplitude_range, offset_range, frequency_range, sample_rate_range
