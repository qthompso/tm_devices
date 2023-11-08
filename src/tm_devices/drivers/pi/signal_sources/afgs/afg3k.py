"""AFG3K device driver module."""
from typing import Optional, Tuple

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

    def _acquire_frequency_multipliers(self):
        """"""
        return 0.5, 0.01

    def _get_limited_constraints(
        self,
        function,
        waveform_length: Optional[int] = None,
        frequency: Optional[float] = None,
    ) -> Tuple[ParameterRange, ParameterRange, ParameterRange, ParameterRange]:
        model_number = self.model[4:6]

        lower_base_amplitude = 40.0e-3
        upper_base_amplitude = 40.0

        offset_bound = 20.0

        base_freq = 10.0e6

        # handle amplitude
        if model_number in ("02", "05"):
            lower_amplitude_multiplier = 0.5
            upper_amplitude_multiplier = 0.5

            offset_multiplier = 0.5
        elif model_number in ("10", "15"):
            lower_amplitude_multiplier = 1
            upper_amplitude_multiplier = 0.5

            offset_multiplier = 0.5
        elif model_number in ("25",):
            lower_amplitude_multiplier = 2.5
            upper_amplitude_multiplier = 0.25

            offset_multiplier = 0.25
        else:
            lower_amplitude_multiplier = 1
            upper_amplitude_multiplier = 1

            offset_multiplier = 1

        # handle sample_rate
        if (
            model_number in ("05", "10", "15", "25")
            and waveform_length
            and waveform_length < 16_000
        ):
            # upper amplitude multiplier just happens to reflect what the sampling rate should be
            sample_rate = 0.5e9 / upper_amplitude_multiplier
        else:
            sample_rate = 250.0e6

        if model_number in ("15", "25"):
            if not frequency or frequency > 50.0e6 / upper_amplitude_multiplier:
                upper_amplitude_multiplier *= 0.8

        if "02" in model_number:
            model_multiplier = 2.5
        else:
            model_multiplier = min(float(model_number), 24.0)

        square_wave_mult, other_wave_mult = self._acquire_frequency_multipliers()

        if function.name in {SignalSourceFunctionsAFG.SIN.name}:
            high_freq_range = base_freq * model_multiplier
            low_freq_range = 1.0e-6
        elif function.name in {
            SignalSourceFunctionsAFG.ARBITRARY.name,
            SignalSourceFunctionsAFG.PULSE.name,
            SignalSourceFunctionsAFG.SQUARE.name,
        }:
            high_freq_range = base_freq * model_multiplier * square_wave_mult
            low_freq_range = 1.0e-3
        else:
            high_freq_range = base_freq * model_multiplier * other_wave_mult
            low_freq_range = 1.0e-6

        amplitude_range = ParameterRange(
            lower_base_amplitude * lower_amplitude_multiplier,
            upper_base_amplitude * upper_amplitude_multiplier,
        )

        frequency_range = ParameterRange(
            min=low_freq_range,
            max=high_freq_range,
        )

        offset_range = ParameterRange(
            min=-offset_bound * offset_multiplier,
            max=offset_bound * offset_multiplier,
        )

        sample_rate_range = ParameterRange(sample_rate, sample_rate)

        return amplitude_range, frequency_range, offset_range, sample_rate_range
