"""Base AWG device driver module."""
import struct

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import ClassVar, Dict, List, Literal, Optional, Tuple, Type

from tm_devices.driver_mixins.class_extension_mixin import ExtendableMixin
from tm_devices.driver_mixins.signal_generator_mixin import (
    ExtendedSourceDeviceConstants,
    ParameterBounds,
    SourceDeviceConstants,
)
from tm_devices.drivers.device import family_base_class
from tm_devices.drivers.pi.signal_generators.signal_generator import SignalGenerator
from tm_devices.helpers import (
    DeviceTypes,
    LoadImpedanceAFG,
    ReadOnlyCachedProperty,
    SignalSourceFunctionsAWG,
    SignalSourceOutputPathsBase,
    SignalSourceOutputPathsNon5200,
)


@dataclass(frozen=True)
class AWGSourceDeviceConstants(SourceDeviceConstants):
    """Class to hold source device constants."""

    functions: Type[SignalSourceFunctionsAWG] = SignalSourceFunctionsAWG


class AWGChannel(ExtendableMixin):
    """AWG channel driver."""

    def __init__(self, awg: "AWG", channel_name: str) -> None:
        """Create an AWG channel object.

        Args:
            awg: An AWG object.
            channel_name: The channel name for the AWG channel.
        """
        self._name = channel_name
        self._num = int("".join(filter(str.isdigit, channel_name)))
        self._awg = awg

    @property
    def name(self) -> str:
        """Return the channel's name."""
        return self._name

    @property
    def num(self) -> int:
        """Return the channel number."""
        return self._num

    def set_amplitude(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the amplitude on the source channel.

        Args:
            value: The amplitude value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        self._awg.set_if_needed(
            f"{self.name}:VOLTAGE:AMPLITUDE",
            value,
            tolerance=tolerance,
            percentage=percentage,
        )

    def set_frequency(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the frequency on the source channel.

        Args:
            value: The frequency value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        self._awg.set_if_needed(
            f"{self.name}:FREQUENCY", value, tolerance=tolerance, percentage=percentage
        )

    def set_offset(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the offset on the source channel.

        Args:
            value: The offset value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        output_path = self._awg.query(f"OUTPUT{self.num}:PATH?")
        if output_path == self._awg.OutputSignalPath.DCA.value:
            self._awg.set_if_needed(
                f"{self.name}:VOLTAGE:OFFSET",
                value,
                tolerance=tolerance,
                percentage=percentage,
            )
        elif value:
            # No error is raised when 0 is the offset value and the output path is in a state where
            # offset cannot be set.
            offset_error = (
                f"The offset can only be set with an output signal path of "
                f"{self._awg.OutputSignalPath.DCA.value}."
            )
            raise ValueError(offset_error)

    def set_output_path(self, value: Optional[SignalSourceOutputPathsBase] = None) -> None:
        """TODO: better? - Set the output signal path on the source channel.

        Args:
            value: The output signal path.
        """
        raise NotImplementedError

    def load_waveform(self, waveform_name: str) -> None:
        """Load in a waveform from the waveform list to the source channel.

        Args:
            waveform_name: The name of the waveform to generate.
        """
        self._awg.set_if_needed(f"{self.name}:WAVEFORM", f'"{waveform_name}"', allow_empty=True)


@family_base_class
class AWG(SignalGenerator, ABC):
    """Base AWG device driver."""

    _DEVICE_TYPE = DeviceTypes.AWG.value
    _PRE_MADE_SIGNAL_RECORD_LENGTH_SIN: ClassVar[List[int]] = [3600, 1000, 960, 360, 100, 36, 10]
    _PRE_MADE_SIGNAL_RECORD_LENGTH_CLOCK: ClassVar[List[int]] = [960]
    # all waveforms have sample sizes of 10, 100 and 1000
    _PRE_MADE_SIGNAL_RECORD_LENGTH_DEFAULT: ClassVar[List[int]] = [1000, 960, 100, 10]

    ################################################################################################
    # Magic Methods
    ################################################################################################

    ################################################################################################
    # Properties
    ################################################################################################
    @property
    def OutputSignalPath(self) -> Type[SignalSourceOutputPathsNon5200]:  # noqa: N802  # pylint: disable=invalid-name
        """Return the output signal path enum."""
        return SignalSourceOutputPathsNon5200

    @ReadOnlyCachedProperty
    def source_channel(self) -> MappingProxyType[str, AWGChannel]:  # pragma: no cover
        """Mapping of channel names to AWGChannel objects."""
        channel_map: Dict[str, AWGChannel] = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWGChannel(self, channel_name)
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
        function: SignalSourceFunctionsAWG,
        amplitude: float,
        offset: float,
        channel: str = "all",
        output_path: Optional[SignalSourceOutputPathsBase] = None,
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
            output_path: The output signal path of the specified channel.
            termination: The impedance this device's ``channel`` expects to see at the received end.
            duty_cycle: The duty cycle percentage within [10.0, 90.0].
            polarity: The polarity to set the signal to.
            symmetry: The symmetry to set the signal to, only applicable to certain functions.
        """
        predefined_name, needed_sample_rate = self._get_predefined_filename(
            frequency, function, output_path, symmetry
        )
        for channel_name in self._validate_channels(channel):
            source_channel = self.source_channel[channel_name]
            self.set_if_needed(f"OUTPUT{source_channel.num}:STATE", "0")
            self.set_waveform_properties(
                source_channel=source_channel,
                output_path=output_path,
                waveform_name=predefined_name,
                needed_sample_rate=needed_sample_rate,
                amplitude=amplitude,
                offset=offset,
            )
            self.set_if_needed(f"OUTPUT{source_channel.num}:STATE", "1")
        self.write("AWGCONTROL:RUN")
        self.expect_esr(0)

    def setup_burst(  # noqa: PLR0913  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        frequency: float,
        function: SignalSourceFunctionsAWG,
        amplitude: float,
        offset: float,
        channel: str = "all",
        output_path: Optional[SignalSourceOutputPathsBase] = None,
        burst_count: int = 0,
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
            channel: The channel name to output the signal from, or 'all'.
            output_path: The output signal path of the specified channel.
            burst_count: The number of wavelengths to be generated.
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
        source_channel: AWGChannel,
        output_path: Optional[SignalSourceOutputPathsBase],
        waveform_name: str,
        needed_sample_rate: float,
        amplitude: float,
        offset: float,
    ) -> None:
        """Set the properties of the waveform.

        Args:
            source_channel: The source channel class for the requested channel.
            output_path: The output signal path of the specified channel.
            waveform_name: The name of the waveform from the waveform list to generate.
            needed_sample_rate: The required sample rate.
            amplitude: The amplitude of the signal to generate.
            offset: The offset of the signal to generate.
        """
        first_source_channel = self.source_channel["SOURCE1"]
        first_source_channel.set_frequency(needed_sample_rate, tolerance=2, percentage=True)
        source_channel.load_waveform(waveform_name)
        source_channel.set_amplitude(amplitude)
        source_channel.set_output_path(output_path)
        source_channel.set_offset(offset)

    def get_waveform_constraints(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        function: Optional[SignalSourceFunctionsAWG] = None,
        waveform_length: Optional[int] = None,
        frequency: Optional[float] = None,
        output_path: Optional[SignalSourceOutputPathsBase] = None,
        load_impedance: LoadImpedanceAFG = LoadImpedanceAFG.HIGHZ,
    ) -> ExtendedSourceDeviceConstants:
        """Get the constraints that restrict the waveform to certain parameter ranges.

        Args:
            function: The function that needs to be generated.
            waveform_length: The length of the waveform if no function or arbitrary is provided.
            frequency: The frequency of the waveform that needs to be generated.
            output_path: The output path that was set on the channel.
            load_impedance: The suggested impedance on the source.
        """
        del frequency, load_impedance

        amplitude_range, offset_range, sample_rate_range = self._get_series_specific_constraints(
            output_path,
        )

        if function and not waveform_length:
            func_sample_rate_lookup: Dict[str, ParameterBounds] = {
                SignalSourceFunctionsAWG.SIN.name: ParameterBounds(lower=10, upper=3600),
                SignalSourceFunctionsAWG.CLOCK.name: ParameterBounds(lower=960, upper=960),
                SignalSourceFunctionsAWG.SQUARE.name: ParameterBounds(lower=10, upper=1000),
                SignalSourceFunctionsAWG.RAMP.name: ParameterBounds(lower=10, upper=1000),
                SignalSourceFunctionsAWG.TRIANGLE.name: ParameterBounds(lower=10, upper=1000),
                SignalSourceFunctionsAWG.DC.name: ParameterBounds(lower=1000, upper=1000),
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
    def _get_predefined_filename(  # TODO: change filename to waveform name
        self,
        frequency: float,
        function: SignalSourceFunctionsAWG,
        output_path: Optional[SignalSourceOutputPathsBase],
        symmetry: Optional[float] = 50.0,
    ) -> Tuple[str, float]:
        """Get the predefined file name for the provided function.

        Args:
            frequency: The frequency of the waveform to generate.
            function: The waveform shape to generate.
            output_path: The output signal path of the specified channel.
            symmetry: The symmetry to set the signal to, only applicable to certain functions.
        """
        if function == function.RAMP and symmetry == 50:  # noqa: PLR2004
            function = function.TRIANGLE
        if function != SignalSourceFunctionsAWG.DC and not function.value.startswith("*"):
            device_constraints = self.get_waveform_constraints(
                function=function, frequency=frequency, output_path=output_path
            )
            if function == SignalSourceFunctionsAWG.SIN:
                premade_signal_rl = self._PRE_MADE_SIGNAL_RECORD_LENGTH_SIN
            elif function == SignalSourceFunctionsAWG.CLOCK:
                premade_signal_rl = self._PRE_MADE_SIGNAL_RECORD_LENGTH_CLOCK
            else:
                premade_signal_rl = self._PRE_MADE_SIGNAL_RECORD_LENGTH_DEFAULT
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
        output_path: Optional[SignalSourceOutputPathsBase],
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
