"""Base AWG device driver module."""
import os
import struct

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from types import MappingProxyType
from typing import Dict, Literal, Optional, Tuple, Type

from tm_devices.driver_mixins.signal_generator_mixin import (
    ExtendedSourceDeviceConstants,
    ParameterBounds,
    SourceDeviceConstants,
)
from tm_devices.drivers.device import family_base_class
from tm_devices.drivers.pi.pi_device import PIDevice
from tm_devices.drivers.pi.signal_generators.signal_generator import SignalGenerator
from tm_devices.helpers import DeviceTypes, LoadImpedanceAFG, SignalSourceFunctionsAWG


@dataclass(frozen=True)
class AWGSourceDeviceConstants(SourceDeviceConstants):
    """Class to hold source device constants."""

    functions: Type[SignalSourceFunctionsAWG] = SignalSourceFunctionsAWG


class AWGChannel:
    """AWG channel driver."""

    def __init__(self, pi_device: PIDevice, channel_name: str) -> None:
        """Create an AWG channel object.

        Args:
            pi_device: A PI device object.
            channel_name: The channel name for the AWG channel.
        """
        self._name = channel_name
        self._num = int("".join(filter(str.isdigit, channel_name)))
        self._pi_device = pi_device

    def set_offset(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the offset on the source.

        Args:
            value: The offset value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        self._pi_device.set_if_needed(
            f"{self.name}:VOLTAGE:OFFSET",
            value,
            tolerance=tolerance,
            percentage=percentage,
        )

    def set_amplitude(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the amplitude on the source.

        Args:
            value: The amplitude value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        self._pi_device.set_if_needed(
            f"{self.name}:VOLTAGE:AMPLITUDE",
            value,
            tolerance=tolerance,
            percentage=percentage,
        )

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
            f"{self.name}:FREQUENCY", value, tolerance=tolerance, percentage=percentage
        )

    def setup_burst_waveform(self, filename: str, burst: int) -> None:
        """Prepare device for burst waveform.

        Args:
            filename: The filename for the burst waveform to generate.
            burst: The number of wavelengths to be generated.
        """
        if not burst:
            self._pi_device.set_and_check(f"{self.name}:WAVEFORM", f'"{filename}"')
        elif burst > 0:
            self._pi_device.set_and_check("AWGCONTROL:RMODE", "SEQ")
            self._pi_device.set_and_check("SEQUENCE:LENGTH", "1")
            self._pi_device.set_and_check(
                f"SEQUENCE:ELEMENT1:WAVEFORM{self.num}",
                f'"{filename}"',
            )
            self._pi_device.set_and_check(
                "SEQUENCE:ELEMENT1:LOOP:COUNT",
                burst,
            )
        else:
            error_message = f"{burst} is an invalid burst value. Burst must be >= 0."
            raise ValueError(error_message)

    @property
    def name(self) -> str:
        """Return the channel's name."""
        return self._name

    @property
    def num(self) -> int:
        """Return the channel number."""
        return self._num


@family_base_class
class AWG(SignalGenerator, ABC):
    """Base AWG device driver."""

    _DEVICE_TYPE = DeviceTypes.AWG.value

    ################################################################################################
    # Magic Methods
    ################################################################################################

    ################################################################################################
    # Properties
    ################################################################################################
    @cached_property
    def source_channel(self) -> "MappingProxyType[str, AWGChannel]":
        """Mapping of channel names to AWGChannel objects."""
        channel_map = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWGChannel(self, channel_name)
        return MappingProxyType(channel_map)

    @property
    def source_device_constants(self) -> AWGSourceDeviceConstants:
        """Return the device constants."""
        return self._DEVICE_CONSTANTS  # type: ignore

    @cached_property
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
            self.set_waveform_properties(
                source_channel, predefined_name, needed_sample_rate, amplitude, offset, burst
            )
            self.set_and_check(f"OUTPUT{source_channel.num}:STATE", "1")
        self.write("AWGCONTROL:RUN")
        self.expect_esr(0)

    def set_waveform_properties(
        self,
        source_channel: AWGChannel,
        predefined_name: str,
        needed_sample_rate: float,
        amplitude: float,
        offset: float,
        burst: int,
    ) -> None:
        """Set the properties of the waveform.

        Args:
            source_channel: The source channel class for the requested channel.
            predefined_name: The name of the function to generate.
            needed_sample_rate: The required sample
            amplitude: The amplitude of the signal to generate.
            offset: The offset of the signal to generate.

            burst: The number of wavelengths to be generated.
        """
        first_source_channel = self.source_channel["SOURCE1"]
        first_source_channel.set_frequency(round(needed_sample_rate, ndigits=-1))
        source_channel.setup_burst_waveform(predefined_name, burst)
        source_channel.set_amplitude(amplitude)
        source_channel.set_offset(offset)

    def get_waveform_constraints(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        function: Optional[SignalSourceFunctionsAWG] = None,
        waveform_length: Optional[int] = None,
        frequency: Optional[float] = None,
        load_impedance: LoadImpedanceAFG = LoadImpedanceAFG.HIGHZ,
    ) -> ExtendedSourceDeviceConstants:
        """Get the constraints that restrict the waveform to certain parameter ranges.

        Args:
            function: The function that needs to be generated.
            waveform_length: The length of the waveform if no function or arbitrary is provided.
            frequency: The frequency of the waveform that needs to be generated.
            load_impedance: The suggested impedance on the source.
        """
        del frequency, load_impedance

        amplitude_range, offset_range, sample_rate_range = self._get_series_specific_constraints()

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
    def _get_predefined_filename(
        self, frequency: float, function: SignalSourceFunctionsAWG, symmetry: Optional[float] = 50.0
    ) -> Tuple[str, float]:
        """Get the predefined file name for the provided function.

        Args:
            frequency: The frequency of the waveform to generate.
            function: The waveform shape to generate.
            symmetry: The symmetry to set the signal to, only applicable to certain functions.
        """
        predefined_name = ""
        needed_sample_rate = 0.0
        if function == function.RAMP and symmetry == 50:  # noqa: PLR2004
            function = function.TRIANGLE
        if function != SignalSourceFunctionsAWG.DC and not function.value.startswith("*"):
            device_constraints = self.get_waveform_constraints(
                function=function, frequency=frequency
            )
            if function == SignalSourceFunctionsAWG.SIN:
                premade_signal_rl = [3600, 1000, 960, 360, 100, 36, 10]
            elif function == SignalSourceFunctionsAWG.CLOCK:
                premade_signal_rl = [960]
            else:
                # all waveforms have sample sizes of 10, 100 and 1000
                premade_signal_rl = [1000, 960, 100, 10]
            # for each of these three records lengths
            sample_rate_found = False
            for record_length in premade_signal_rl:  # pragma: no cover
                needed_sample_rate = frequency * record_length
                # try for the highest record length that can generate the frequency
                if (
                    device_constraints.sample_rate_range
                    and device_constraints.sample_rate_range.lower
                    <= needed_sample_rate
                    <= device_constraints.sample_rate_range.upper
                ):
                    sample_rate_found = True
                    predefined_name = f"*{function.value.title()}{record_length}"
                    break
            if not sample_rate_found:
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
            filename_target = os.path.basename(target_file)
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
