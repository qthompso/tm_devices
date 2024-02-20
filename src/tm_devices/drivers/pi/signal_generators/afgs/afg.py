"""Base AFG device driver module."""
import re

from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import MappingProxyType
from typing import Dict, Literal, Optional, Tuple, Type

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
    SignalGeneratorFunctionsAFG,
    SignalGeneratorOutputPathsBase,
)


@dataclass(frozen=True)
class AFGSourceDeviceConstants(SourceDeviceConstants):
    """Class to hold source device constants."""

    functions: Type[SignalGeneratorFunctionsAFG] = SignalGeneratorFunctionsAFG


class AFGChannel:
    """AFG channel driver."""

    def __init__(self, afg: "AFG", channel_name: str) -> None:
        """Create an AFG channel object.

        Args:
            afg: An AFG object.
            channel_name: The channel name for the AFG channel.
        """
        self._name = channel_name
        self._num = int("".join(filter(str.isdigit, channel_name)))
        self._afg = afg

    @property
    def name(self) -> str:
        """Return the channel name."""
        return self._name

    @property
    def num(self) -> int:
        """Return the channel number."""
        return self._num

    def initiate_phase_sync(self) -> None:
        """Initialize a phase sync between SOURCE1 and SOURCE2 on the device.

        Does the same operation if called on SOURCE1 or SOURCE2.
        """
        self._afg.write(f"{self.name}:PHASE:INITIATE")

    def set_amplitude(self, value: float, absolute_tolerance: float = 0) -> None:
        """Set the amplitude on the source channel.

        Args:
            value: The amplitude value to set.
            absolute_tolerance: The acceptable difference between two floating point values.
        """
        self._afg.set_if_needed(
            f"{self._name}:VOLTAGE:AMPLITUDE",
            value,
            tolerance=absolute_tolerance,
        )

    def set_burst_state(self, value: int) -> None:
        """Set the burst mode to ON/OFF (1/0) on the source channel.

        Args:
            value: The burst state.
        """
        if value not in [0, 1]:
            error_message = "Burst state value must be 1 (ON) or 0 (OFF)."
            raise ValueError(error_message)
        self._afg.set_if_needed(f"{self.name}:BURST:STATE", value)

    def set_burst_mode(self, value: Literal["TRIGGERED", "GATED"]) -> None:
        """Set the burst mode on the source channel.

        Args:
            value: The burst mode (Options: "TRIGGERED", "GATED").
        """
        burst_mode_mapping = {
            "TRIGGERED": "TRIG",
            "GATED": "GAT",
        }
        self._afg.set_if_needed(f"{self.name}:BURST:MODE", burst_mode_mapping[value])

    def set_burst_count(self, value: int) -> None:
        """Set the number of wavelengths to be generated when the source channel is set to burst.

        Args:
            value: The number of wavelengths to be generated within [1, 1000000].
        """
        self._afg.set_if_needed(f"{self.name}:BURST:NCYCLES", value)

    def set_frequency(self, value: float, absolute_tolerance: float = 0) -> None:
        """Set the frequency on the source channel.

        Args:
            value: The frequency value to set.
            absolute_tolerance: The acceptable difference between two floating point values.
        """
        self._afg.set_if_needed(
            f"{self._name}:FREQUENCY:FIXED",
            value,
            tolerance=absolute_tolerance,
        )

    def set_function(self, value: SignalGeneratorFunctionsAFG) -> None:
        """Set the function to output on the source channel.

        Args:
            value: The name of the function to output.
        """
        self._afg.set_if_needed(f"{self.name}:FUNCTION", str(value.value))

    def set_impedance(self, value: float) -> None:
        """Set the output load impedance on the internal AFG.

        Args:
            value: The impedance value to set within [1, 10e3] or 99e36.
        """
        self._afg.set_if_needed(f"OUTPUT{self.num}:IMPEDANCE", value)

    def set_offset(self, value: float, absolute_tolerance: float = 0) -> None:
        """Set the offset on the source channel.

        Args:
            value: The offset value to set.
            absolute_tolerance: The acceptable difference between two floating point values.
        """
        self._afg.set_if_needed(
            f"{self._name}:VOLTAGE:OFFSET",
            value,
            tolerance=absolute_tolerance,
        )

    def set_polarity(self, value: Literal["NORMAL", "INVERTED"]) -> None:
        """Set the polarity on the source channel.

        An "INVERTED" polarity inverts the specific output waveform relative to the offset level.

        Args:
            value: The polarity value to set (Options: "NORMAL", "INVERTED").
        """
        polarity_mapping = {
            "NORMAL": "NORM",
            "INVERTED": "INV",
        }
        self._afg.set_if_needed(f"OUTPUT{self.num}:POLARITY", polarity_mapping[value])

    def set_pulse_duty_cycle(self, value: float) -> None:
        """Set the duty cycle of the pulse waveform on the source channel.

        Args:
            value: The duty cycle percentage within [0.4, 99.6].
        """
        self._afg.set_if_needed(f"{self.name}:PULSE:DCYCLE", value)

    def set_ramp_symmetry(self, value: float) -> None:
        """Set the symmetry of the ramp waveform on the source channel.

        Args:
            value: The symmetry value to set within [0, 100].
        """
        self._afg.set_if_needed(f"{self.name}:FUNCTION:RAMP:SYMMETRY", value)

    def set_state(self, value: int) -> None:
        """Set the output state to ON/OFF (1/0) on the source channel.

        Args:
            value: The output state.
        """
        if value not in [0, 1]:
            error_message = "Output state value must be 1 (ON) or 0 (OFF)."
            raise ValueError(error_message)
        self._afg.set_if_needed(f"OUTPUT{self.num}:STATE", value)

    def setup_burst_waveform(self, burst_count: int) -> None:
        """Prepare the source channel for a burst waveform.

        Args:
            burst_count: The number of wavelengths to be generated.
        """
        # set to external as to not burst every millisecond
        self._afg.set_if_needed("TRIGGER:SEQUENCE:SOURCE", "EXT")
        self.set_burst_state(1)
        self.set_burst_mode("TRIGGERED")
        self.set_burst_count(burst_count)


@family_base_class
class AFG(SignalGenerator, ABC):
    """Base AFG device driver."""

    _DEVICE_TYPE = DeviceTypes.AFG.value

    ################################################################################################
    # Properties
    ################################################################################################
    @ReadOnlyCachedProperty
    def source_channel(self) -> "MappingProxyType[str, AFGChannel]":
        """Mapping of channel names to AFGChannel objects."""
        channel_map: Dict[str, AFGChannel] = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AFGChannel(self, channel_name)
        return MappingProxyType(channel_map)

    @property
    def source_device_constants(self) -> AFGSourceDeviceConstants:
        """Return the device constants."""
        return self._DEVICE_CONSTANTS  # type: ignore[attr-defined]

    @ReadOnlyCachedProperty
    def total_channels(self) -> int:
        """Return the total number of channels (all types)."""
        if match := re.match(r"AFG\d+(\d)", self.model):
            return int(match.group(1))
        return 0  # pragma: no cover

    ################################################################################################
    # Public Methods
    ################################################################################################
    def generate_function(  # noqa: PLR0913  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        frequency: float,
        function: SignalGeneratorFunctionsAFG,
        amplitude: float,
        offset: float,
        channel: str = "all",
        output_signal_path: Optional[SignalGeneratorOutputPathsBase] = None,
        termination: Literal["FIFTY", "HIGHZ"] = "FIFTY",
        duty_cycle: float = 50.0,
        polarity: Literal["NORMAL", "INVERTED"] = "NORMAL",
        symmetry: float = 100.0,
    ) -> None:
        """Generate a signal given the following parameters.

        Args:
            frequency: The frequency of the waveform to generate.
            function: The waveform shape to generate.
            amplitude: The amplitude of the signal to generate.
            offset: The offset of the signal to generate.
            channel: The channel name to output the signal from, or 'all'.
            output_signal_path: The output signal path of the specified channel.
            termination: The impedance this device's ``channel`` expects to see at the received end.
            duty_cycle: The duty cycle percentage within [0.4, 99.6].
            polarity: The polarity to set the signal to.
            symmetry: The symmetry to set the signal to, only applicable to certain functions.
        """
        del output_signal_path  # Not used in AFGs.
        self._validate_generated_function(function)

        # Generate the waveform on the given channel
        for channel_name in self._validate_channels(channel):
            source_channel = self.source_channel[channel_name]
            # Temporarily turn off this channel
            source_channel.set_state(0)
            self.set_waveform_properties(
                frequency=frequency,
                function=function,
                amplitude=amplitude,
                offset=offset,
                source_channel=source_channel,
                burst_count=0,
                termination=termination,
                duty_cycle=duty_cycle,
                polarity=polarity,
                symmetry=symmetry,
            )
            # Turn on the channel
            source_channel.set_state(1)

            # Check if burst is enabled on any channel of the AFG
            burst_state = False
            for burst_channel in range(1, self.total_channels + 1):
                if self.query(f"SOURCE{burst_channel}:BURST:STATE?") == "1":
                    burst_state = True
            if (
                self.total_channels > 1  # pylint: disable=comparison-with-callable
                and function.value != SignalGeneratorFunctionsAFG.DC.value
                and not burst_state
            ):
                # Initiate a phase sync (between CH 1 and CH 2 output waveforms on two channel AFGs)
                self.source_channel["SOURCE1"].initiate_phase_sync()
            # Check for system errors
            self.expect_esr(0)

    def setup_burst(  # noqa: PLR0913  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        frequency: float,
        function: SignalGeneratorFunctionsAFG,
        amplitude: float,
        offset: float,
        burst_count: int,
        channel: str = "all",
        output_signal_path: Optional[SignalGeneratorOutputPathsBase] = None,
        termination: Literal["FIFTY", "HIGHZ"] = "FIFTY",
        duty_cycle: float = 50.0,
        polarity: Literal["NORMAL", "INVERTED"] = "NORMAL",
        symmetry: float = 100.0,
    ) -> None:
        """Set up the AFG for sending a burst of waveforms given the following parameters.

        Args:
            frequency: The frequency of the waveform to generate.
            function: The waveform shape to generate.
            amplitude: The amplitude of the signal to generate.
            offset: The offset of the signal to generate.
            burst_count: The number of wavelengths to be generated.
            channel: The channel name to output the signal from, or 'all'.
            output_signal_path: The output signal path of the specified channel.
            termination: The impedance this device's ``channel`` expects to see at the received end.
            duty_cycle: The duty cycle percentage within [0.4, 99.6].
            polarity: The polarity to set the signal to.
            symmetry: The symmetry to set the signal to, only applicable to certain functions.
        """
        del output_signal_path  # Not used in AFGs.
        self._validate_generated_function(function)
        # Generate the waveform on the given channel
        for channel_name in self._validate_channels(channel):
            source_channel = self.source_channel[channel_name]
            self.set_waveform_properties(
                frequency=frequency,
                function=function,
                amplitude=amplitude,
                offset=offset,
                source_channel=source_channel,
                burst_count=burst_count,
                termination=termination,
                duty_cycle=duty_cycle,
                polarity=polarity,
                symmetry=symmetry,
            )

    def generate_burst(self) -> None:
        """Generate a burst of waveforms by forcing trigger."""
        self.write("*TRG")
        self.expect_esr(0)

    def set_waveform_properties(  # noqa: PLR0913
        self,
        frequency: float,
        function: SignalGeneratorFunctionsAFG,
        amplitude: float,
        offset: float,
        source_channel: AFGChannel,
        burst_count: int = 0,
        termination: Literal["FIFTY", "HIGHZ"] = "FIFTY",
        duty_cycle: float = 50.0,
        polarity: Literal["NORMAL", "INVERTED"] = "NORMAL",
        symmetry: float = 100.0,
    ) -> None:
        """Set the given parameters on the provided source channel.

        Args:
            frequency: The frequency of the waveform to generate.
            function: The waveform shape to generate.
            amplitude: The amplitude of the signal to generate.
            offset: The offset of the signal to generate.
            source_channel: The source channel class for the requested channel.
            burst_count: The number of wavelengths to be generated.
            termination: The impedance this device's ``channel`` expects to see at the received end.
            duty_cycle: The duty cycle percentage within [0.4, 99.6].
            polarity: The polarity to set the signal to.
            symmetry: The symmetry to set the signal to, only applicable to certain functions.
        """
        # Termination
        if termination == "FIFTY":
            source_channel.set_impedance(50)
        elif termination == "HIGHZ":
            source_channel.set_impedance(99e36)
        else:  # pragma: no cover
            # if termination is MAXIMUM or MINIMUM or INFINITY
            self.set_if_needed(f"OUTPUT{source_channel.num}:IMPEDANCE", termination)
        # Frequency
        source_channel.set_frequency(frequency)
        # Offset
        source_channel.set_offset(offset, absolute_tolerance=0.01)
        if function == SignalGeneratorFunctionsAFG.PULSE:
            # Duty cycle is only valid for pulse
            source_channel.set_pulse_duty_cycle(duty_cycle)
        # Polarity
        source_channel.set_polarity(polarity)
        # Function
        if function == SignalGeneratorFunctionsAFG.RAMP:
            source_channel.set_ramp_symmetry(symmetry)
        source_channel.set_function(function)
        # Amplitude, needs to be after termination so that the amplitude is properly adjusted
        source_channel.set_amplitude(amplitude, absolute_tolerance=0.01)
        if burst_count > 0:
            source_channel.setup_burst_waveform(burst_count)

    def get_waveform_constraints(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        function: Optional[SignalGeneratorFunctionsAFG] = None,
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
        del output_signal_path

        if not function:
            msg = "AFGs must have a waveform defined."
            raise ValueError(msg)
        (
            amplitude_range,
            frequency_range,
            offset_range,
            sample_rate_range,
        ) = self._get_series_specific_constraints(
            function, waveform_length, frequency, load_impedance
        )

        return ExtendedSourceDeviceConstants(
            amplitude_range=amplitude_range,
            frequency_range=frequency_range,
            offset_range=offset_range,
            sample_rate_range=sample_rate_range,
        )

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _reboot(self) -> None:
        """Reboot the device."""
        # TODO: implement

    def _send_waveform(self, target_file: str) -> None:
        """Send the waveform information to the AWG as a file in memory.

        Args:
            target_file: The name of the waveform file.
        """
        # TODO: implement

    @abstractmethod
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
        raise NotImplementedError
