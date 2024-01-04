"""AWG7K device driver module."""
from functools import cached_property
from types import MappingProxyType
from typing import Literal, Tuple

from tm_devices.commands import AWG7KMixin
from tm_devices.drivers.pi.signal_generators.awgs.awg import (
    AWG,
    AWGChannel,
    AWGSourceDeviceConstants,
    ParameterBounds,
)
from tm_devices.helpers import SignalSourceFunctionsAWG


class AWG7KChannel(AWGChannel):
    """AWG7K channel driver."""

    def set_offset(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the offset on the source.

        Args:
            value: The offset value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        if not ("02" in self._awg.opt_string or "06" in self._awg.opt_string):
            super().set_offset(value, tolerance, percentage)
        elif value:
            offset_error = "The offset cannot be set on AWG7k's with 02 and 06 option."
            raise ValueError(offset_error)


class AWG7K(AWG7KMixin, AWG):
    """AWG7K device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=32400000,
        memory_min_record_length=2,
    )

    ################################################################################################
    # Properties
    ################################################################################################
    @cached_property
    def source_channel(self) -> "MappingProxyType[str, AWGChannel]":
        """Mapping of channel names to AWGChannel objects."""
        channel_map = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWG7KChannel(self, channel_name)
        return MappingProxyType(channel_map)

    ################################################################################################
    # Public Methods
    ################################################################################################
    def generate_function(  # noqa: PLR0913  # pylint: disable=too-many-locals
        self,
        frequency: float,
        function: SignalSourceFunctionsAWG,
        amplitude: float,
        offset: float,
        channel: str = "all",
        burst: int = 0,
        termination: Literal["FIFTY", "HIGHZ"] = "FIFTY",  # noqa: ARG002
        duty_cycle: float = 50.0,  # noqa: ARG002
        polarity: Literal["NORMAL", "INVERTED"] = "NORMAL",  # noqa: ARG002
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
        predefined_name, needed_sample_rate = self._get_predefined_filename(
            frequency, function, symmetry
        )
        for channel_name in self._validate_channels(channel):
            source_channel = self.source_channel[channel_name]
            self.set_and_check(f"OUTPUT{source_channel.num}:STATE", "0")
            first_source_channel = self.source_channel["SOURCE1"]
            first_source_channel.set_frequency(round(needed_sample_rate, ndigits=-1))
            source_channel.setup_burst_waveform(predefined_name, burst)
            source_channel.set_amplitude(amplitude)
            source_channel.set_offset(offset)
            self.set_and_check(f"OUTPUT{source_channel.num}:STATE", "1")
        self.write("AWGCONTROL:RUN")
        self.expect_esr(0)

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _get_series_specific_constraints(
        self,
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        """Get constraints which are dependent on the model series."""
        # if we are using the high bandwidth options
        if "02" in self.opt_string or "06" in self.opt_string:
            amplitude_range = ParameterBounds(lower=500.0e-3, upper=1.0)
            offset_range = ParameterBounds(lower=-0.0, upper=0.0)
        else:
            amplitude_range = ParameterBounds(lower=50e-3, upper=2.0)
            offset_range = ParameterBounds(lower=-0.5, upper=0.5)
        # AWG(Arbitrary Waveform Generator)7(Series)xx(GS/s)x(Channels)z(Model)
        sample_rate_range = ParameterBounds(lower=10.0e6, upper=int(self.model[4:6]) * 1.0e9)

        return amplitude_range, offset_range, sample_rate_range
