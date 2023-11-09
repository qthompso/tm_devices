"""Base AFG device driver module."""
import re

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from typing import Literal, Optional, Tuple, Type

from tm_devices.driver_mixins.signal_generator_mixin import (
    ExtendedSourceDeviceConstants,
    ParameterBounds,
    SourceDeviceConstants,
)
from tm_devices.drivers.device import family_base_class
from tm_devices.drivers.pi.signal_sources.signal_source import SignalSource
from tm_devices.helpers import DeviceTypes, LoadImpedanceAFG, SignalSourceFunctionsAFG


@dataclass(frozen=True)
class AFGSourceDeviceConstants(SourceDeviceConstants):
    """Class to hold source device constants."""

    functions: Type[SignalSourceFunctionsAFG] = SignalSourceFunctionsAFG


@family_base_class
class AFG(SignalSource, ABC):
    """Base AFG device driver."""

    _DEVICE_TYPE = DeviceTypes.AFG.value

    ################################################################################################
    # Properties
    ################################################################################################
    @property
    def source_device_constants(self) -> AFGSourceDeviceConstants:
        """Return the device constants."""
        return self._DEVICE_CONSTANTS  # type: ignore

    @cached_property
    def total_channels(self) -> int:
        """Return the total number of channels (all types)."""
        if match := re.match(r"AFG\d+(\d)", self.model):
            return int(match.group(1))
        return 0  # pragma: no cover

    ################################################################################################
    # Public Methods
    ################################################################################################
    # pylint: disable=too-many-locals,line-too-long
    def generate_waveform(  # noqa: C901, PLR0913  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        frequency: float,
        function: SignalSourceFunctionsAFG,
        amplitude: float,
        offset: float,
        channel: str = "all",
        burst: int = 0,
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
            burst: The number of wavelengths to be generated.
            termination: The impedance this device's ``channel`` expects to see at the received end.
            duty_cycle: The duty cycle percentage within [10.0, 90.0].
            polarity: The polarity to set the signal to.
            symmetry: The symmetry to set the signal to, only applicable to certain functions.
        """
        polarity_mapping = {
            "NORMAL": "NORM",
            "INVERTED": "INV",
        }
        self._validate_generated_function(function)

        # Generate the waveform on the given channel
        for channel_name in self._validate_channels(channel):
            # grab the number(s) in the channel name
            channel_num = "".join(filter(str.isdigit, channel_name))
            # Temporarily turn off this channel
            self.set_and_check(f"OUTPUT{channel_num}:STATE", 0)
            # Termination
            if termination == "FIFTY":
                self.set_and_check(f"OUTPUT{channel_num}:IMPEDANCE", 50)
            elif termination == "HIGHZ":
                self.write(f"OUTPUT{channel_num}:IMPEDANCE INFINITY")
            else:  # pragma: no cover
                # if termination is MAXIMUM or MINIMUM or INFINITY
                self.set_and_check(f"OUTPUT{channel_num}:IMPEDANCE", termination)
            # Frequency
            self.set_and_check(f"SOURCE{channel_num}:FREQUENCY:FIXED", frequency)
            # Offset
            self.set_and_check(f"SOURCE{channel_num}:VOLTAGE:OFFSET", offset, tolerance=0.01)
            if function == SignalSourceFunctionsAFG.PULSE:
                # Duty cycle is only valid for pulse
                self.set_and_check(f"SOURCE{channel_num}:PULSE:DCYCLE", duty_cycle)
            # Polarity
            self.set_and_check(f"OUTPUT{channel_num}:POLARITY", polarity_mapping[polarity])
            # Function
            if function == SignalSourceFunctionsAFG.RAMP:
                self.set_and_check(f"SOURCE{channel_num}:FUNCTION:RAMP:SYMMETRY", symmetry)
            self.set_and_check(f"SOURCE{channel_num}:FUNCTION", function.value)
            # Amplitude, needs to be after termination so that the amplitude is properly adjusted
            self.set_and_check(f"SOURCE{channel_num}:VOLTAGE:AMPLITUDE", amplitude, tolerance=0.01)
            if burst > 0:
                # set to external as to not burst every millisecond
                self.set_and_check("TRIGGER:SEQUENCE:SOURCE", "EXT")
                self.set_and_check(f"SOURCE{channel_num}:BURST:STATE", 1)
                self.set_and_check(f"SOURCE{channel_num}:BURST:MODE", "TRIG")
                self.set_and_check(f"SOURCE{channel_num}:BURST:NCYCLES", burst)
            # Turn on the channel
            self.set_and_check(f"OUTPUT{channel_num}:STATE", 1)

            # Check if burst is enabled on any channel of the AFG
            burst_state = False
            for burst_channel in range(1, self.total_channels + 1):
                if self.query(f"SOURCE{burst_channel}:BURST:STATE?") == "1":
                    burst_state = True

            if burst > 0:
                self.write("*TRG")
            # Initiate a phase sync (between CH 1 and CH 2 output waveforms on two channel AFGs)
            elif (
                self.total_channels > 1
                and function != SignalSourceFunctionsAFG.DC
                and not burst_state
            ):
                self.write("SOURCE1:PHASE:INITIATE")
            # Check for system errors
            self.expect_esr(0)

    def get_waveform_constraints(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        function: Optional[SignalSourceFunctionsAFG] = None,
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
        function: SignalSourceFunctionsAFG,
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
