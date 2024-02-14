"""AFG3K device driver module."""
from typing import Optional, Tuple

from tm_devices.commands import AFG3KMixin
from tm_devices.drivers.pi.signal_generators.afgs.afg import (
    AFG,
    AFGSourceDeviceConstants,
    LoadImpedanceAFG,
    ParameterBounds,
    SignalGeneratorFunctionsAFG,
)


class AFG3K(AFG3KMixin, AFG):
    """AFG3K device driver."""

    _DEVICE_CONSTANTS = AFGSourceDeviceConstants(
        memory_page_size=2,
        memory_max_record_length=128 * 1024,
        memory_min_record_length=2,
    )

    _16KB_THRESHOLD = 16 * 1024

    @staticmethod
    def _get_driver_specific_multipliers(model_number: str) -> Tuple[float, float]:
        """Get multipliers for frequency dependant for different functions."""
        del model_number
        square_wave_multiplier = 0.5
        other_wave_multiplier = 0.01
        return square_wave_multiplier, other_wave_multiplier

    # pylint: disable=too-many-locals
    def _get_series_specific_constraints(
        self,
        function: SignalGeneratorFunctionsAFG,
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
        model_number = self.model[4:6]

        lower_base_amplitude = 40.0e-3
        upper_base_amplitude = 40.0

        load_impedance_multiplier = 1.0 if load_impedance == LoadImpedanceAFG.HIGHZ else 0.5

        offset_bound = 20.0

        base_freq = 10.0e6

        # handle amplitude
        if model_number in {"02", "05"}:
            lower_amplitude_multiplier = 0.5
            upper_amplitude_multiplier = 0.5

            offset_multiplier = 0.5
        elif model_number in {"10", "15"}:
            lower_amplitude_multiplier = 1
            upper_amplitude_multiplier = 0.5

            offset_multiplier = 0.5
        elif model_number == "25":
            lower_amplitude_multiplier = 2.5
            upper_amplitude_multiplier = 0.25

            offset_multiplier = 0.25
        else:
            lower_amplitude_multiplier = 1
            upper_amplitude_multiplier = 1

            offset_multiplier = 1

        # handle sample_rate
        if (
            model_number in {"05", "10", "15", "25"}
            and waveform_length
            and waveform_length < self._16KB_THRESHOLD
        ):
            # upper amplitude multiplier just happens to reflect what the sampling rate should be
            sample_rate = 0.5e9 / upper_amplitude_multiplier
        else:
            sample_rate = 250.0e6

        # model 15 and 25 have threshold where the amplitude is reduced
        if model_number in {"15", "25"} and (
            not frequency or frequency > 50.0e6 / upper_amplitude_multiplier
        ):
            upper_amplitude_multiplier *= 0.8

        model_multiplier = 2.5 if "02" in model_number else min(float(model_number), 24.0)

        square_wave_mult, other_wave_mult = self._get_driver_specific_multipliers(model_number)

        if function.name in {SignalGeneratorFunctionsAFG.SIN.name}:
            high_freq_range = base_freq * model_multiplier
            low_freq_range = 1.0e-6
        elif function.name in {
            SignalGeneratorFunctionsAFG.ARBITRARY.name,
            SignalGeneratorFunctionsAFG.PULSE.name,
            SignalGeneratorFunctionsAFG.SQUARE.name,
        }:
            high_freq_range = base_freq * model_multiplier * square_wave_mult
            low_freq_range = 1.0e-3
        else:
            high_freq_range = base_freq * model_multiplier * other_wave_mult
            low_freq_range = 1.0e-6

        amplitude_range = ParameterBounds(
            lower=lower_base_amplitude * lower_amplitude_multiplier * load_impedance_multiplier,
            upper=upper_base_amplitude * upper_amplitude_multiplier * load_impedance_multiplier,
        )

        frequency_range = ParameterBounds(
            lower=low_freq_range,
            upper=high_freq_range,
        )

        offset_range = ParameterBounds(
            lower=-offset_bound * offset_multiplier * load_impedance_multiplier,
            upper=offset_bound * offset_multiplier * load_impedance_multiplier,
        )

        sample_rate_range = ParameterBounds(lower=sample_rate, upper=sample_rate)

        return amplitude_range, frequency_range, offset_range, sample_rate_range
