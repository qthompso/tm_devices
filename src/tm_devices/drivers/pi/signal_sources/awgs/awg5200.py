"""AWG5200 device driver module."""
import time

from functools import cached_property
from types import MappingProxyType
from typing import Literal, Tuple

from tm_devices.commands import AWG5200Mixin
from tm_devices.drivers.pi.signal_sources.awgs.awg import (
    AWG,
    AWGChannel,
    AWGSourceDeviceConstants,
    ParameterBounds,
)
from tm_devices.helpers import SignalSourceFunctionsAWG


class AWG5200Channel(AWGChannel):
    """AWG5200 channel driver."""

    def set_frequency(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the frequency on the source.

        Args:
            value: The frequency value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        self._pi_device.set_if_needed(
            "CLOCK:SRATE",
            round(value, -1),
            tolerance=tolerance,
            percentage=percentage,
        )
        time.sleep(0.1)
        self._pi_device.ieee_cmds.opc()
        self._pi_device.ieee_cmds.cls()
        self._pi_device.poll_query(30, "CLOCK:SRATE?", value, tolerance=10, percentage=percentage)


class AWG5200(AWG5200Mixin, AWG):
    """AWG5200 device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=16200000,
        memory_min_record_length=1,
    )

    ################################################################################################
    # Properties
    ################################################################################################
    @cached_property
    def channel(self) -> "MappingProxyType[str, AWGChannel]":
        """Mapping of channel names to AWGChannel objects."""
        channel_map = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWG5200Channel(self, channel_name)
        return MappingProxyType(channel_map)

    ################################################################################################
    # Public Methods
    ################################################################################################
    def generate_waveform(  # noqa: PLR0913
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
        symmetry: float = 50.0,  # noqa: ARG002
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
        if predefined_name and needed_sample_rate:
            self.ieee_cmds.opc()
            self.ieee_cmds.cls()
            for channel_name in self._validate_channels(channel):
                source_channel = self.channel[channel_name]
                self.set_and_check(f"OUTPUT{source_channel.num}:STATE", "0")
                source_channel.set_frequency(round(needed_sample_rate, ndigits=-1))
                self._setup_burst_waveform(source_channel.num, predefined_name, burst)
                source_channel.set_amplitude(amplitude)
                source_channel.set_offset(offset)
                self.ieee_cmds.wai()
                self.ieee_cmds.opc()
                self.ieee_cmds.cls()
                self.set_and_check(f"OUTPUT{source_channel.num}:STATE", "1")
            self.ieee_cmds.opc()
            self.write("AWGCONTROL:RUN")
            time.sleep(0.1)
            self.ieee_cmds.opc()
            self.ieee_cmds.cls()
            self.poll_query(30, "AWGControl:RSTate?", 2.0)
            self.expect_esr(0)

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _get_series_specific_constraints(
        self,
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        """Get constraints which are dependent on the model series."""
        amplitude_range = ParameterBounds(lower=100e-3, upper=2.0)
        offset_range = ParameterBounds(lower=-0.5, upper=0.5)
        # option is the sample rate in hundreds of Mega Hertz
        sample_rate_range = ParameterBounds(lower=300.0, upper=int(self.opt_string) * 100.0e6)

        return amplitude_range, offset_range, sample_rate_range

    def _setup_burst_waveform(self, channel_num: int, filename: str, burst: int) -> None:
        """Prepare device for burst waveform.

        Args:
            channel_num: The channel number to output the signal from.
            filename: The filename for the burst waveform to generate.
            burst: The number of wavelengths to be generated.
        """
        if not burst:
            # handle the wave info
            # this is a sequential command
            self.set_and_check(f"SOURCE{channel_num}:WAVEFORM", f'"{filename}"')
