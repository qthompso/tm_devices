"""AFG31K device driver module."""
from typing import Optional, Tuple

from tm_devices.drivers.pi.signal_generators.afgs.afg3k import (
    AFG,
    AFGSourceDeviceConstants,
    LoadImpedanceAFG,
    ParameterBounds,
    SignalSourceFunctionsAFG,
)


class AFG31K(AFG):
    """AFG31K device driver."""

    _DEVICE_CONSTANTS = AFGSourceDeviceConstants(
        memory_page_size=2,
        memory_max_record_length=131072,
        memory_min_record_length=2,
    )

    _PRE_15_FREQ_THRESHOLD_1 = 60.0e6
    _PRE_15_FREQ_THRESHOLD_2 = 80.0e6
    _POST_15_FREQ_THRESHOLD = 200.0e6

    _16KB_THRESHOLD = 16 * 1024
    ################################################################################################
    # Magic Methods
    ################################################################################################

    ################################################################################################
    # Properties
    ################################################################################################

    ################################################################################################
    # Public Methods
    ################################################################################################

    @staticmethod
    def _get_driver_specific_multipliers(model_number: str) -> Tuple[float, float, float]:
        """Get multipliers for frequency dependant for different functions."""
        square_wave_multiplier = 0.64 if model_number == "25" else 0.8

        if model_number == "02":
            other_wave_multiplier = 0.025
        elif model_number == "05":
            other_wave_multiplier = 0.016
        else:
            other_wave_multiplier = 0.01

        arbitrary_multiplier = 0.5
        return square_wave_multiplier, other_wave_multiplier, arbitrary_multiplier

    # pylint: disable=too-many-locals
    def _get_series_specific_constraints(
        self,
        function: SignalSourceFunctionsAFG,
        waveform_length: Optional[int] = None,
        frequency: Optional[float] = None,
        load_impedance: LoadImpedanceAFG = LoadImpedanceAFG.HIGHZ,
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds, ParameterBounds]:
        """Get constraints which are dependent on the model series.

        Args:
            function: The function that needs to be generated.
            waveform_length: The length of the waveform if no function or arbitrary is provided.
            frequency: The frequency of the waveform that needs to be generated.
            load_impedance: The suggested impedance on the source.
        """
        model_number = self.model[5:7]

        load_impedance_multiplier = 1.0 if load_impedance == LoadImpedanceAFG.HIGHZ else 0.5

        freq_base = 10.0e6

        lower_amplitude = 2.0e-3
        # handle amplitude
        if model_number in {"02", "05", "10"}:
            if frequency and frequency <= self._PRE_15_FREQ_THRESHOLD_1:
                upper_amplitude = 20.0
            elif frequency and frequency <= self._PRE_15_FREQ_THRESHOLD_2:
                upper_amplitude = 16.0
            else:
                upper_amplitude = 12.0

            offset_bound = 10.0
        else:
            upper_amplitude = (
                10.0 if (frequency and frequency <= self._POST_15_FREQ_THRESHOLD) else 8.0
            )

            offset_bound = 5.0
        # handle frequency
        model_multiplier = 2.5 if "02" in model_number else float(model_number)

        sample_rate = 250.0e6
        if waveform_length and waveform_length < self._16KB_THRESHOLD:
            if model_number in {"05", "10"}:
                sample_rate = 1.0e9
            elif model_number in {"15", "25"}:
                sample_rate = 2.0e9

        square_mult, other_mult, arb_mult = self._get_driver_specific_multipliers(model_number)
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

        amplitude_range = ParameterBounds(
            lower=lower_amplitude * load_impedance_multiplier,
            upper=upper_amplitude * load_impedance_multiplier,
        )

        frequency_range = ParameterBounds(
            lower=low_freq_range,
            upper=high_freq_range,
        )

        offset_range = ParameterBounds(
            lower=-offset_bound * load_impedance_multiplier,
            upper=offset_bound * load_impedance_multiplier,
        )

        sample_rate_range = ParameterBounds(lower=sample_rate, upper=sample_rate)

        return amplitude_range, frequency_range, offset_range, sample_rate_range

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _reboot(self) -> None:
        """Reboot the device."""
        self.write("SYSTem:RESTart")
