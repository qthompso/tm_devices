"""AWG5200 device driver module."""
import time

from functools import cached_property
from types import MappingProxyType
from typing import Literal, Optional, Tuple

from tm_devices.commands import AWG5200Mixin
from tm_devices.drivers.pi.signal_generators.awgs.awg import (
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
        # This is an overlapping command for the AWG5200, and will overlap the
        # next command and/or overlap the previous if it is still running.
        self._pi_device.set_if_needed(
            "CLOCK:SRATE",
            round(value, -1),
            tolerance=tolerance,
            percentage=percentage,
        )
        # there is a known issue where setting other parameters while clock rate is being set
        # may lock the AWG5200 software.

        # wait a fraction of a second for overlapping command CLOCK:SRATE to proceed
        time.sleep(0.1)
        # wait till overlapping command finishes
        self._pi_device.ieee_cmds.opc()
        # clear queue
        self._pi_device.ieee_cmds.cls()
        # ensure that the clock rate was actually set
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
    def source_channel(self) -> "MappingProxyType[str, AWGChannel]":
        """Mapping of channel names to AWGChannel objects."""
        channel_map = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWG5200Channel(self, channel_name)
        return MappingProxyType(channel_map)

    ################################################################################################
    # Public Methods
    ################################################################################################
    def generate_function(  # noqa: PLR0913
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
        # wait for operation complete from PI commands before setting up attributes
        # an overlapping command being set while frequency is being set may lock up the source
        self.ieee_cmds.opc()
        # clear queue
        self.ieee_cmds.cls()
        for channel_name in self._validate_channels(channel):
            source_channel = self.source_channel[channel_name]
            # turn channel off
            self.set_and_check(f"OUTPUT{source_channel.num}:STATE", "0")
            source_channel.set_frequency(round(needed_sample_rate, ndigits=-1))
            # Settings the frequency is done
            self._setup_burst_waveform(source_channel.num, predefined_name, burst)
            # setting amplitude is a blocking command
            source_channel.set_amplitude(amplitude)
            # setting offset is a blocking command
            source_channel.set_offset(offset)

            # wait a fraction of a second for blocking command CLOCK:SRATE to proceed
            # this fixes the channel from locking up the awg5200 too many blocking commands in a
            # row may block the next query if the queue is too long
            time.sleep(0.1)
            # wait until the blocking command is complete
            self.ieee_cmds.opc()
            # clear queue
            self.ieee_cmds.cls()
            # turn channel on
            self.set_and_check(f"OUTPUT{source_channel.num}:STATE", "1")
        # ensure previous command is finished
        self.ieee_cmds.opc()
        # this is an overlapping command
        self.write("AWGCONTROL:RUN")
        # wait a fraction of a second for overlapping command AWGCONTROL:RUN to proceed
        time.sleep(0.1)
        # ensure previous command is finished
        self.ieee_cmds.opc()
        # clear queue
        self.ieee_cmds.cls()
        # ensure that the control run was actually set
        self.poll_query(30, "AWGControl:RSTate?", 2.0)
        # we expect no errors
        self.expect_esr(0)

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _get_series_specific_constraints(
        self,
        output_path: Optional[str],
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        """Get constraints which are dependent on the model series."""
        if not output_path:
            output_path = "DCHB"
        # Direct Current High Bandwidth with the DC options has 1.5 V amplitude
        if "DC" in self.opt_string and output_path == "DCHB":
            amplitude_range = ParameterBounds(lower=25.0e-3, upper=1.5)
        # Direct Current High Voltage path connected has an even higher amplitude, 5 V
        elif output_path == "DCHV":
            amplitude_range = ParameterBounds(lower=10.0e-3, upper=5.0)
        # Else, the upper bound is 750 mV
        else:
            amplitude_range = ParameterBounds(lower=25.0e-3, upper=750.0e-3)

        offset_range = ParameterBounds(lower=-2.0, upper=2.0)
        # option is the sample rate in hundreds of Mega Hertz
        max_sample_rate = 25.0 if "25" in self.opt_string else 50.0
        # option 50 would have 5.0 GHz, option 2.5 would have 2.5 GHz
        sample_rate_range = ParameterBounds(lower=300.0, upper=max_sample_rate * 100.0e6)

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
