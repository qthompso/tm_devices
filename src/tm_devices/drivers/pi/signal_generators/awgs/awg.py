"""Base AWG device driver module."""
import struct

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import cast, ClassVar, Dict, List, Literal, Optional, Tuple, Type

from tm_devices.driver_mixins.class_extension_mixin import ExtendableMixin
from tm_devices.driver_mixins.signal_generator_mixin import (
    ExtendedSourceDeviceConstants,
    ParameterBounds,
    SourceDeviceConstants,
)
from tm_devices.drivers.device import family_base_class
from tm_devices.drivers.pi._base_source_channel import BaseSourceChannel
from tm_devices.drivers.pi.signal_generators.signal_generator import SignalGenerator
from tm_devices.helpers import (
    DeviceTypes,
    LoadImpedanceAFG,
    ReadOnlyCachedProperty,
    SignalGeneratorFunctionsAWG,
    SignalGeneratorOutputPathsBase,
    SignalGeneratorOutputPathsNon5200,
)


@dataclass(frozen=True)
class AWGSourceDeviceConstants(SourceDeviceConstants):
    """Class to hold source device constants."""

    functions: Type[SignalGeneratorFunctionsAWG] = SignalGeneratorFunctionsAWG


@family_base_class
class AWGSourceChannel(BaseSourceChannel, ExtendableMixin):
    """AWG source channel driver."""

    def __init__(self, awg: "AWG", channel_name: str) -> None:
        """Create an AWG source channel.

        Args:
            awg: An AWG.
            channel_name: The channel name for the AWG source channel.
        """
        super().__init__(pi_device=awg, channel_name=channel_name)

    @property
    def awg(self) -> "AWG":
        """Returns the AWG."""
        return cast(AWG, self._pi_device)

    def set_amplitude(self, value: float, absolute_tolerance: float = 0) -> None:
        """Set the amplitude on the source channel.

        Args:
            value: The amplitude value to set.
            absolute_tolerance: The acceptable difference between two floating point values.
        """
        self.awg.set_if_needed(
            f"{self.name}:VOLTAGE:AMPLITUDE",
            value,
            tolerance=absolute_tolerance,
        )

    def set_frequency(self, value: float, absolute_tolerance: float = 0) -> None:
        """Set the frequency on the source channel.

        Args:
            value: The frequency value to set.
            absolute_tolerance: The acceptable difference between two floating point values.
        """
        self.awg.set_if_needed(f"{self.name}:FREQUENCY", value, tolerance=absolute_tolerance)

    def set_offset(self, value: float, absolute_tolerance: float = 0) -> None:
        """Set the offset on the source channel.

        Args:
            value: The offset value to set.
            absolute_tolerance: The acceptable difference between two floating point values.
        """
        output_path = self.awg.query(f"OUTPUT{self.num}:PATH?")
        if output_path == self.awg.OutputSignalPath.DCA.value:
            self.awg.set_if_needed(
                f"{self.name}:VOLTAGE:OFFSET",
                value,
                tolerance=absolute_tolerance,
            )
        elif value:
            # No error is raised when 0 is the offset value and the output signal path is
            # in a state where offset cannot be set.
            offset_error = (
                f"The offset can only be set with an output signal path of "
                f"{self.awg.OutputSignalPath.DCA.value}."
            )
            raise ValueError(offset_error)

    def set_state(self, value: int) -> None:
        """Set the output state to ON/OFF (1/0) on the source channel.

        Args:
            value: The output state.
        """
        if value not in [0, 1]:
            error_message = "Output state value must be 1 (ON) or 0 (OFF)."
            raise ValueError(error_message)
        self.awg.set_if_needed(f"OUTPUT{self.num}:STATE", value)

    def set_output_signal_path(
        self, value: Optional[SignalGeneratorOutputPathsBase] = None
    ) -> None:
        """Set the output signal path on the source channel.

        Args:
            value: The output signal path.
        """
        raise NotImplementedError

    def load_waveform(self, waveform_name: str) -> None:
        """Load in a waveform from the waveform list to the source channel.

        Args:
            waveform_name: The name of the waveform to load.
        """
        self.awg.set_if_needed(f"{self.name}:WAVEFORM", f'"{waveform_name}"', allow_empty=True)


class AWG(SignalGenerator, ABC):
    """Base AWG device driver."""

    OutputSignalPath = SignalGeneratorOutputPathsNon5200

    _DEVICE_TYPE = DeviceTypes.AWG.value
    _PRE_DEFINED_SIGNAL_RECORD_LENGTH_SIN: ClassVar[List[int]] = [3600, 1000, 960, 360, 100, 36, 10]
    _PRE_DEFINED_SIGNAL_RECORD_LENGTH_CLOCK: ClassVar[List[int]] = [960]
    # all waveforms have sample sizes of 10, 100 and 1000
    _PRE_DEFINED_SIGNAL_RECORD_LENGTH_DEFAULT: ClassVar[List[int]] = [1000, 960, 100, 10]

    ################################################################################################
    # Magic Methods
    ################################################################################################

    ################################################################################################
    # Properties
    ################################################################################################
    @ReadOnlyCachedProperty
    def source_channel(self) -> "MappingProxyType[str, AWGSourceChannel]":  # pragma: no cover
        """Mapping of channel names to AWGSourceChannel objects."""
        channel_map: Dict[str, AWGSourceChannel] = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWGSourceChannel(self, channel_name)
        return MappingProxyType(channel_map)

    @property
    def source_device_constants(self) -> AWGSourceDeviceConstants:
        """Return the device constants."""
        return self._DEVICE_CONSTANTS  # type: ignore[attr-defined]

    @ReadOnlyCachedProperty
    def total_channels(self) -> int:
        """Return the total number of channels (all types)."""
        return int(self.query("AWGControl:CONFigure:CNUMber?", verbose=False))

    ################################################################################################
    # Public Methods
    ################################################################################################
    def load_waveform(self, wfm_name: str, waveform_file_path: str, wfm_type: str) -> None:
        """Load a waveform into the memory of the AWG.

        Args:
            wfm_name: The name to set the loaded waveform to on the AWG.
            waveform_file_path: The path to the waveform.
            wfm_type: The type of the waveform to import.
        """
        if not waveform_file_path.startswith('"'):
            waveform_file_path = '"' + waveform_file_path
        if not waveform_file_path.endswith('"'):
            waveform_file_path += '"'
        self.write(f'MMEMory:IMPort "{wfm_name}", {waveform_file_path}, {wfm_type}')
        self._ieee_cmds.opc()

    def generate_function(  # noqa: PLR0913  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        frequency: float,
        function: SignalGeneratorFunctionsAWG,
        amplitude: float,
        offset: float,
        channel: str = "all",
        output_signal_path: Optional[SignalGeneratorOutputPathsBase] = None,
        termination: Literal["FIFTY", "HIGHZ"] = "FIFTY",
        duty_cycle: float = 50.0,
        polarity: Literal["NORMAL", "INVERTED"] = "NORMAL",
        symmetry: float = 50.0,
    ) -> None:
        """Generate a predefined waveform given the following parameters.

        Args:
            frequency: The frequency of the waveform to generate.
            function: The waveform shape to generate.
            amplitude: The amplitude of the signal to generate.
            offset: The offset of the signal to generate.
            channel: The channel name to output the signal from, or 'all'.
            output_signal_path: The output signal path of the specified channel.
            termination: The impedance this device's ``channel`` expects to see at the received end.
            duty_cycle: The duty cycle percentage within [10.0, 90.0].
            polarity: The polarity to set the signal to.
            symmetry: The symmetry to set the signal to, only applicable to certain functions.
        """
        predefined_name, needed_sample_rate = self._get_predefined_waveform_name(
            frequency, function, output_signal_path, symmetry
        )
        self.generate_waveform(
            needed_sample_rate=needed_sample_rate,
            waveform_name=predefined_name,
            amplitude=amplitude,
            offset=offset,
            channel=channel,
            output_signal_path=output_signal_path,
            termination=termination,
            duty_cycle=duty_cycle,
            polarity=polarity,
            symmetry=symmetry,
        )

    def generate_waveform(  # noqa: PLR0913
        self,
        needed_sample_rate: float,
        waveform_name: str,
        amplitude: float,
        offset: float,
        channel: str = "all",
        output_signal_path: Optional[SignalGeneratorOutputPathsBase] = None,
        termination: Literal["FIFTY", "HIGHZ"] = "FIFTY",  # noqa: ARG002
        duty_cycle: float = 50.0,  # noqa: ARG002
        polarity: Literal["NORMAL", "INVERTED"] = "NORMAL",  # noqa: ARG002
        symmetry: float = 50.0,  # noqa: ARG002
    ) -> None:
        """Generate a waveform given the following parameters.

        Args:
            needed_sample_rate: The required sample rate.
            waveform_name: The name of the waveform to generate.
            amplitude: The amplitude of the signal to generate.
            offset: The offset of the signal to generate.
            channel: The channel name to output the signal from, or 'all'.
            output_signal_path: The output signal path of the specified channel.
            termination: The impedance this device's ``channel`` expects to see at the received end.
            duty_cycle: The duty cycle percentage within [10.0, 90.0].
            polarity: The polarity to set the signal to.
            symmetry: The symmetry to set the signal to, only applicable to certain functions.
        """
        for channel_name in self._validate_channels(channel):
            source_channel = self.source_channel[channel_name]
            source_channel.set_state(0)
            self.set_waveform_properties(
                source_channel=source_channel,
                output_signal_path=output_signal_path,
                waveform_name=waveform_name,
                needed_sample_rate=needed_sample_rate,
                amplitude=amplitude,
                offset=offset,
            )
            source_channel.set_state(1)
        self.write("AWGCONTROL:RUN")
        self.expect_esr(0)

    def setup_burst(  # noqa: PLR0913  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        frequency: float,
        function: SignalGeneratorFunctionsAWG,
        amplitude: float,
        offset: float,
        burst_count: int,
        channel: str = "all",
        output_signal_path: Optional[SignalGeneratorOutputPathsBase] = None,
        termination: Literal["FIFTY", "HIGHZ"] = "FIFTY",
        duty_cycle: float = 50.0,
        polarity: Literal["NORMAL", "INVERTED"] = "NORMAL",
        symmetry: float = 50.0,
    ) -> None:
        """Set up the AWG for sending a burst of waveforms given the following parameters.

        Args:
            frequency: The frequency of the waveform to generate.
            function: The waveform shape to generate.
            amplitude: The amplitude of the signal to generate.
            offset: The offset of the signal to generate.
            burst_count: The number of wavelengths to be generated.
            channel: The channel name to output the signal from, or 'all'.
            output_signal_path: The output signal path of the specified channel.
            termination: The impedance this device's ``channel`` expects to see at the received end.
            duty_cycle: The duty cycle percentage within [10.0, 90.0].
            polarity: The polarity to set the signal to.
            symmetry: The symmetry to set the signal to, only applicable to certain functions.
        """
        raise NotImplementedError

    def generate_burst(self) -> None:
        """Generate a burst of waveforms by forcing trigger."""
        raise NotImplementedError

    def set_waveform_properties(
        self,
        source_channel: AWGSourceChannel,
        output_signal_path: Optional[SignalGeneratorOutputPathsBase],
        waveform_name: str,
        needed_sample_rate: float,
        amplitude: float,
        offset: float,
    ) -> None:
        """Set the given parameters on the provided source channel.

        Args:
            source_channel: The source channel class for the requested channel.
            output_signal_path: The output signal path of the specified channel.
            waveform_name: The name of the waveform from the waveform list to generate.
            needed_sample_rate: The required sample rate.
            amplitude: The amplitude of the signal to generate.
            offset: The offset of the signal to generate.
        """
        first_source_channel = self.source_channel["SOURCE1"]
        first_source_channel.set_frequency(needed_sample_rate)
        source_channel.load_waveform(waveform_name)
        source_channel.set_amplitude(amplitude)
        source_channel.set_output_signal_path(output_signal_path)
        source_channel.set_offset(offset)

    def get_waveform_constraints(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        function: Optional[SignalGeneratorFunctionsAWG] = None,
        waveform_length: Optional[int] = None,
        frequency: Optional[float] = None,
        output_signal_path: Optional[SignalGeneratorOutputPathsBase] = None,
        load_impedance: LoadImpedanceAFG = LoadImpedanceAFG.HIGHZ,
    ) -> ExtendedSourceDeviceConstants:
        """Get the constraints that restrict the waveform to certain parameter ranges.

        Args:
            function: The function that needs to be generated.
            waveform_length: The length of the waveform if no function or arbitrary is provided.
            frequency: The frequency of the waveform that needs to be generated.
            output_signal_path: The output signal path that was set on the channel.
            load_impedance: The suggested impedance on the source.
        """
        del frequency, load_impedance

        amplitude_range, offset_range, sample_rate_range = self._get_series_specific_constraints(
            output_signal_path,
        )

        if function and not waveform_length:
            # use the min and max waveform length dependent on the predefined files
            func_sample_rate_lookup: Dict[str, ParameterBounds] = {
                SignalGeneratorFunctionsAWG.SIN.name: ParameterBounds(lower=10, upper=3600),
                SignalGeneratorFunctionsAWG.CLOCK.name: ParameterBounds(lower=960, upper=960),
                SignalGeneratorFunctionsAWG.SQUARE.name: ParameterBounds(lower=10, upper=1000),
                SignalGeneratorFunctionsAWG.RAMP.name: ParameterBounds(lower=10, upper=1000),
                SignalGeneratorFunctionsAWG.TRIANGLE.name: ParameterBounds(lower=10, upper=1000),
                SignalGeneratorFunctionsAWG.DC.name: ParameterBounds(lower=1000, upper=1000),
            }
            slowest_frequency = (
                sample_rate_range.lower / func_sample_rate_lookup[function.name].upper
            )
            fastest_frequency = (
                sample_rate_range.upper / func_sample_rate_lookup[function.name].lower
            )
        elif waveform_length and not function:
            slowest_frequency = sample_rate_range.lower / waveform_length
            fastest_frequency = sample_rate_range.upper / waveform_length
        else:
            msg = "AWG Constraints require exclusively function or waveform_length."
            raise ValueError(msg)

        frequency_range = ParameterBounds(
            lower=slowest_frequency,
            upper=fastest_frequency,
        )
        return ExtendedSourceDeviceConstants(
            amplitude_range=amplitude_range,
            offset_range=offset_range,
            frequency_range=frequency_range,
            sample_rate_range=sample_rate_range,
        )

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _get_predefined_waveform_name(
        self,
        frequency: float,
        function: SignalGeneratorFunctionsAWG,
        output_signal_path: Optional[SignalGeneratorOutputPathsBase],
        symmetry: Optional[float] = 50.0,
    ) -> Tuple[str, float]:
        """Get the predefined waveform name for the provided function.

        Args:
            frequency: The frequency of the waveform to generate.
            function: The waveform shape to generate.
            output_signal_path: The output signal path of the specified channel.
            symmetry: The symmetry to set the signal to, only applicable to certain functions.
        """
        if function == function.RAMP and symmetry == 50:  # noqa: PLR2004
            function = function.TRIANGLE
        if function != SignalGeneratorFunctionsAWG.DC and not function.value.startswith("*"):
            device_constraints = self.get_waveform_constraints(
                function=function, frequency=frequency, output_signal_path=output_signal_path
            )
            if function == SignalGeneratorFunctionsAWG.SIN:
                premade_signal_rl = self._PRE_DEFINED_SIGNAL_RECORD_LENGTH_SIN
            elif function == SignalGeneratorFunctionsAWG.CLOCK:
                premade_signal_rl = self._PRE_DEFINED_SIGNAL_RECORD_LENGTH_CLOCK
            else:
                premade_signal_rl = self._PRE_DEFINED_SIGNAL_RECORD_LENGTH_DEFAULT
            # for each of these three records lengths
            for record_length in premade_signal_rl:  # pragma: no cover
                needed_sample_rate = frequency * record_length
                # try for the highest record length that can generate the frequency
                if (
                    device_constraints.sample_rate_range
                    and device_constraints.sample_rate_range.lower
                    <= needed_sample_rate
                    <= device_constraints.sample_rate_range.upper
                ):
                    predefined_name = f"*{function.value.title()}{record_length}"
                    break
            else:
                # This clause is skipped if break is called in for loop.
                error_message = (
                    f"Unable to generate {function.value} waveform with provided frequency of "
                    f"{frequency} Hz."
                )
                raise ValueError(error_message)
        else:
            predefined_name = "*DC"
            needed_sample_rate = 15000000.0

        return predefined_name, needed_sample_rate

    @abstractmethod
    def _get_series_specific_constraints(
        self,
        output_signal_path: Optional[SignalGeneratorOutputPathsBase],
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        raise NotImplementedError

    def _reboot(self) -> None:
        """Reboot the device."""
        # TODO: overwrite the reboot code here

    # TODO: add testing for this
    def _send_waveform(self, target_file: str) -> None:  # pragma: no cover
        """Send the waveform information to the AWG as a file in memory.

        Args:
            target_file: The name of the waveform file.
        """
        with open(target_file, "rb") as file_handle:
            file_handle.seek(0, 0)
            waveform_data = file_handle.read()
            # must be even to send
            if len(waveform_data) % 2:
                waveform_data += b"\0"

            info_len = int(len(waveform_data) / 2)
            bin_waveform = struct.unpack(">" + str(info_len) + "H", waveform_data)

            # Turn "path/to/stuff.wfm" into "stuff.wfm".
            filename_target = Path(target_file).name
            # Write the waveform data to the AWG memory.
            string_to_send = 'MMEMORY:DATA "' + filename_target + '",'
            self._visa_resource.write_binary_values(
                string_to_send,
                bin_waveform,
                datatype="H",
                is_big_endian=True,
                termination="\r\n",
                encoding="latin-1",
            )
