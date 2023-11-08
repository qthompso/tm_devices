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

    def _acquire_frequency_multipliers(self):
        """"""
        model_number = self.model[5:7]

        if model_number == "25":
            square_wave_multiplier = 0.64
        else:
            square_wave_multiplier = 0.8

        if model_number == "02":
            other_wave_multiplier = 0.025
        elif model_number == "05":
            other_wave_multiplier = 0.016
        else:
            other_wave_multiplier = 0.01

        arbitrary_multiplier = 0.5
        return square_wave_multiplier, other_wave_multiplier, arbitrary_multiplier

    def _get_limited_constraints(
        self,
        function,
        waveform_length: Optional[int] = None,
        frequency: Optional[float] = None,
    ) -> Tuple[ParameterRange, ParameterRange, ParameterRange, ParameterRange]:
        model_number = self.model[5:7]

        freq_base = 10.0e6

        lower_amplitude = 2.0e-3
        # handle amplitude
        if model_number in ("02", "05", "10"):
            if frequency <= 60.0e6:
                upper_amplitude = 20.0
            elif frequency <= 80.0e6:
                upper_amplitude = 16.0
            else:
                upper_amplitude = 12.0

            offset_bound = 10.0
        else:
            if frequency <= 200.0e6:
                upper_amplitude = 10.0
            else:
                upper_amplitude = 8.0

            offset_bound = 5.0
        # handle frequency
        if "02" in model_number:
            model_multiplier = 2.5
        else:
            model_multiplier = float(model_number)

        sample_rate = 250.0e6
        if waveform_length and waveform_length < 16_384:
            if model_number in ("05", "10"):
                sample_rate = 1.0e9
            elif model_number in ("15", "25"):
                sample_rate = 2.0e9

        square_mult, other_mult, arb_mult = self._acquire_frequency_multipliers()
        low_freq_range = 1.0e-6
        if function.name in {SignalSourceFunctionsAFG.SIN.name}:
            high_freq_range = model_multiplier * freq_base
        elif function.name == SignalSourceFunctionsAFG.ARBITRARY.name:
            high_freq_range = model_multiplier * arb_mult * freq_base
        elif function.name in {
            SignalSourceFunctionsAFG.PULSE.name,
            SignalSourceFunctionsAFG.SQUARE.name,
        }:
            high_freq_range = model_multiplier * square_mult * freq_base
        else:
            high_freq_range = model_multiplier * other_mult * freq_base

        amplitude_range = ParameterRange(
            lower_amplitude,
            upper_amplitude,
        )

        frequency_range = ParameterRange(
            min=low_freq_range,
            max=high_freq_range,
        )

        offset_range = ParameterRange(
            min=-offset_bound,
            max=offset_bound,
        )

        sample_rate_range = ParameterRange(sample_rate, sample_rate)

        return amplitude_range, frequency_range, offset_range, sample_rate_range

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _reboot(self) -> None:
        """Reboot the device."""
        self.write("SYSTem:RESTart")
