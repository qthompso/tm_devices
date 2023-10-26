"""AWG7K device driver module."""
from typing import Literal, Optional, Tuple

from tm_devices.commands import AWG7KMixin
from tm_devices.drivers.pi.signal_sources.awgs.awg import (
    AWG,
    AWGSourceDeviceConstants,
    ParameterRange,
)
from tm_devices.helpers import SignalSourceFunctionsAWG


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
    def generate_waveform(  # noqa: PLR0913  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        frequency: float,
        function: SignalSourceFunctionsAWG,
        amplitude: float,
        offset: float,
        channel: str = "all",
        burst: int = 0,
        termination: Literal["FIFTY", "HIGHZ"] = "FIFTY",
        duty_cycle: float = 50.0,
        polarity: Literal["NORMAL", "INVERTED"] = "NORMAL",
        symmetry: float = 50.0,
    ) -> None:
        """Generate a signal given the following parameters.

        Args:
            frequency: The frequency of the waveform to generate.
            function: The waveform shape to generate.
            amplitude: The amplitude of the signal to generate.
            offset: The offset of the signal to generate.
            channel: The channel name to output the signal from, or 'all'.
            burst: The number of wavelengths to be generated.
            termination: The impedance this device's ``channel`` expects to see at the received end.
            duty_cycle: The duty cycle percentage within [10.0, 90.0].
            polarity: The polarity to set the signal to.
            symmetry: The symmetry to set the signal to, only applicable to certain functions.
        """
        predefined_name, needed_sample_rate = self._get_predefined_filename(frequency, function)
        for channel_name in self._validate_channels(channel):
            source_channel = self.channel[channel_name]
            self.set_and_check(f"OUTPUT{source_channel.num}:STATE", "0")
            if needed_sample_rate:
                first_source_channel = self.channel["SOURCE1"]
                first_source_channel.set_frequency(round(needed_sample_rate, -1))
            self._setup_burst_waveform(source_channel.num, predefined_name, burst)
            source_channel.set_amplitude(needed_sample_rate)
            if not ("02" in self.opt_string or "06" in self.opt_string):
                source_channel.set_offset(needed_sample_rate)
            self.set_and_check(f"OUTPUT{source_channel.num}:STATE", "1")
        self.write("AWGCONTROL:RUN")
        self.expect_esr(0)

    ################################################################################################
    # Private Methods
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
