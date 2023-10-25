"""AFG3K device driver module."""
from typing import Tuple

from tm_devices.commands import AFG3KMixin
from tm_devices.drivers.pi.signal_sources.afgs.afg import (
    AFG,
    AFGSourceDeviceConstants,
    ParameterRange,
    SignalSourceFunctionsAFG,
)


class AFG3K(AFG3KMixin, AFG):
    """AFG3K device driver."""

    _DEVICE_CONSTANTS = AFGSourceDeviceConstants(
        memory_page_size=2,
        memory_max_record_length=128 * 1024,
        memory_min_record_length=2,
    )

    def _get_limited_constraints(
        self,
        function,
        frequency,
    ) -> Tuple[ParameterRange, ParameterRange, ParameterRange, ParameterRange]:
        number_of_points = 0

        # AFG(Arbitrary Function Generator)3(Series)01(*10^7 Mhz Sin)1(Channels)
        if self.model in "AFG3011":
            amplitude_range = ParameterRange(40.0e-3, 40.0)
            offset_range = ParameterRange(-20.0, 20.0)
            sample_rate_range = ParameterRange(1, 250.0e6)
            if function.name in {
                SignalSourceFunctionsAFG.ARBITRARY.name,
                SignalSourceFunctionsAFG.PULSE.name,
                SignalSourceFunctionsAFG.SQUARE.name,
            }:
                frequency_range = ParameterRange(1.0e-3, 5.0e6)
            elif function.name in {SignalSourceFunctionsAFG.SIN.name}:
                frequency_range = ParameterRange(1.0e-6, 10.0e6)
            else:
                frequency_range = ParameterRange(1.0e-6, 100.0e3)

        # AFG(Arbitrary Function Generator)3(Series)10(*10^7 Mhz Sin)1,2(Channels)
        elif self.model in ("AFG3101", "AFG3102"):
            amplitude_range = ParameterRange(40.0e-3, 20.0)
            offset_range = ParameterRange(-10.0, 10.0)
            if number_of_points > 16_000:
                sample_rate_range = ParameterRange(1, 250.0e6)
            else:
                sample_rate_range = ParameterRange(1, 2.0e9)
            if function.name in {
                SignalSourceFunctionsAFG.ARBITRARY.name,
                SignalSourceFunctionsAFG.PULSE.name,
                SignalSourceFunctionsAFG.SQUARE.name,
            }:
                frequency_range = ParameterRange(1.0e-6, 50.0e6)
            elif function.name in {SignalSourceFunctionsAFG.SIN.name}:
                frequency_range = ParameterRange(1.0e-6, 100.0e6)
            else:
                frequency_range = ParameterRange(1.0e-6, 1.0e6)

        # AFG(Arbitrary Function Generator)3(Series)25(*10^7 Mhz Sin)1,2(Channels)
        elif self.model in ("AFG3251", "AFG3252"):
            if frequency and frequency <= 200.0e6:
                amplitude_range = ParameterRange(100.0e-3, 10.0)
            else:
                amplitude_range = ParameterRange(100.0e-3, 8.0)
            offset_range = ParameterRange(-5.0, 5.0)

            if number_of_points > 16_000:
                sample_rate_range = ParameterRange(1, 250.0e6)
            else:
                sample_rate_range = ParameterRange(1, 2.0e9)

            if function.name in {
                SignalSourceFunctionsAFG.ARBITRARY.name,
                SignalSourceFunctionsAFG.PULSE.name,
                SignalSourceFunctionsAFG.SQUARE.name,
            }:
                frequency_range = ParameterRange(1.0e-6, 120.0e6)
            elif function.name in {SignalSourceFunctionsAFG.SIN.name}:
                frequency_range = ParameterRange(1.0e-6, 240.0e6)
            else:
                frequency_range = ParameterRange(1.0e-6, 2.4e6)

        # Lowest possible ranges
        else:
            amplitude_range = ParameterRange(100.0e-3, 8.0)
            offset_range = ParameterRange(-5.0, 5.0)
            sample_rate_range = ParameterRange(1, 250.0e6)
            if function.name in {
                SignalSourceFunctionsAFG.ARBITRARY.name,
                SignalSourceFunctionsAFG.PULSE.name,
                SignalSourceFunctionsAFG.SQUARE.name,
            }:
                frequency_range = ParameterRange(1.0e-3, 5.0e6)
            elif function.name in {SignalSourceFunctionsAFG.SIN.name}:
                frequency_range = ParameterRange(1.0e-6, 10.0e6)
            else:
                frequency_range = ParameterRange(1.0e-6, 100.0e3)
        return amplitude_range, offset_range, frequency_range, sample_rate_range
