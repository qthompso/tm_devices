"""AFG31K device driver module."""
from typing import Optional, Tuple

from tm_devices.drivers.pi.signal_sources.afgs.afg3k import (
    AFG,
    AFGSourceDeviceConstants,
    ParameterRange,
    SignalSourceFunctionsAFG,
)

class AFG31K(AFG):
    """AFG31K device driver."""

    _DEVICE_CONSTANTS = AFGSourceDeviceConstants(
        memory_page_size=2,
        memory_max_record_length=131072,
        memory_min_record_length=2,
    )

    ################################################################################################
    # Magic Methods
    ################################################################################################

    ################################################################################################
    # Properties
    ################################################################################################

    ################################################################################################
    # Public Methods
    ################################################################################################

    def _get_limited_constraints(
        self,
        function,
        frequency,
    ) -> Tuple[Optional[ParameterRange], Optional[ParameterRange], Optional[ParameterRange]]:
        if self.model in ("AFG31021", "AFG31022", "AFG31051", "AFG31052", "AFG31101", "AFG31102"):
            offset_range = ParameterRange(-10.0, 10.0)
            if frequency and frequency < 60.0e6:
                amplitude_range = ParameterRange(2.0e-3, 20.0)
            elif frequency and 60.0e6 < frequency < 80.0e6:
                amplitude_range = ParameterRange(2.0e-3, 16.0)
            else:
                amplitude_range = ParameterRange(2.0e-3, 12.0)
        else:
            offset_range = ParameterRange(-5.0, 5.0)
            if frequency and frequency < 200.0e6:
                amplitude_range = ParameterRange(2.0e-3, 10.0)
            else:
                amplitude_range = ParameterRange(2.0e-3, 8.0)

        # AFG(Arbitrary Function Generator)31(Series)05(*10^7 Mhz Sin)1,2(Channels)
        if self.model in ("AFG31051", "AFG31052"):
            if function.name in (
                SignalSourceFunctionsAFG.PULSE.name,
                SignalSourceFunctionsAFG.SQUARE.name,
            ):
                frequency_range = ParameterRange(1.0e-6, 40.0e6)
            elif function.name in {SignalSourceFunctionsAFG.SIN.name}:
                frequency_range = ParameterRange(1.0e-6, 50.0e6)
            elif function.name in {SignalSourceFunctionsAFG.ARBITRARY.name}:
                frequency_range = ParameterRange(1.0e-3, 25.0e6)
            elif function.name in {SignalSourceFunctionsAFG.PRNOISE.name}:
                frequency_range = ParameterRange(1.0e-6, 150.0e6)
            else:
                frequency_range = ParameterRange(1.0e-6, 800.0e3)

        # AFG(Arbitrary Function Generator)31(Series)10(*10^7 Mhz Sin)1,2(Channels)
        elif self.model in ("AFG31101", "AFG31102"):
            if function.name in {
                SignalSourceFunctionsAFG.PULSE.name,
                SignalSourceFunctionsAFG.SQUARE.name,
            }:
                frequency_range = ParameterRange(1.0e-3, 80.0e6)
            elif function.name in {SignalSourceFunctionsAFG.SIN.name}:
                frequency_range = ParameterRange(1.0e-6, 100.0e6)
            elif function.name in {SignalSourceFunctionsAFG.ARBITRARY.name}:
                frequency_range = ParameterRange(1.0e-3, 50.0e6)
            elif function.name in {SignalSourceFunctionsAFG.PRNOISE.name}:
                frequency_range = ParameterRange(1.0e-6, 150.0e6)
            else:
                frequency_range = ParameterRange(1.0e-6, 1.0e6)

        # AFG(Arbitrary Function Generator)31(Series)15(*10^7 Mhz Sin)1,2(Channels)
        elif self.model in ("AFG31151", "AFG31152"):
            if function.name in {
                SignalSourceFunctionsAFG.PULSE.name,
                SignalSourceFunctionsAFG.SQUARE.name,
            }:
                frequency_range = ParameterRange(1.0e-3, 120.0e6)
            elif function.name in {SignalSourceFunctionsAFG.SIN.name}:
                frequency_range = ParameterRange(1.0e-6, 150.0e6)
            elif function.name in {SignalSourceFunctionsAFG.ARBITRARY.name}:
                frequency_range = ParameterRange(1.0e-3, 75.5e6)
            elif function.name in {SignalSourceFunctionsAFG.PRNOISE.name}:
                frequency_range = ParameterRange(1.0e-6, 360.0e6)
            else:
                frequency_range = ParameterRange(1.0e-6, 1.5e6)

        # AFG(Arbitrary Function Generator)31(Series)25(*10^7 Mhz Sin)1,2(Channels)
        elif self.model in ("AFG31251", "AFG31252"):
            if function.name in {
                SignalSourceFunctionsAFG.PULSE.name,
                SignalSourceFunctionsAFG.SQUARE.name,
            }:
                frequency_range = ParameterRange(1.0e-6, 160.0e6)
            elif function.name in {SignalSourceFunctionsAFG.SIN.name}:
                frequency_range = ParameterRange(1.0e-6, 250.0e6)
            elif function.name in {SignalSourceFunctionsAFG.ARBITRARY.name}:
                frequency_range = ParameterRange(1.0e-3, 125.0e6)
            elif function.name in {SignalSourceFunctionsAFG.PRNOISE.name}:
                frequency_range = ParameterRange(1.0e-6, 360.0e6)
            else:
                frequency_range = ParameterRange(1.0e-6, 2.5e6)

        # AFG(Arbitrary Function Generator)31(Series)02(*10^7 Mhz Sin)1,2(Channels)
        else:
            if function.name in {
                SignalSourceFunctionsAFG.PULSE.name,
                SignalSourceFunctionsAFG.SQUARE.name,
            }:
                frequency_range = ParameterRange(1.0e-3, 20.0e6)
            elif function.name in {SignalSourceFunctionsAFG.SIN.name}:
                frequency_range = ParameterRange(1.0e-6, 25.0e6)
            elif function.name in {SignalSourceFunctionsAFG.ARBITRARY.name}:
                frequency_range = ParameterRange(1.0e-3, 12.5e6)
            elif function.name in {SignalSourceFunctionsAFG.PRNOISE.name}:
                frequency_range = ParameterRange(1.0e-6, 150.0e6)
            else:
                frequency_range = ParameterRange(1.0e-6, 500.0e3)

        return amplitude_range, offset_range, frequency_range

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _reboot(self) -> None:
        """Reboot the device."""
        self.write("SYSTem:RESTart")
