"""AWG5200 device driver module."""
import time

from pathlib import Path
from types import MappingProxyType
from typing import cast, Dict, Literal, Optional, Tuple, Type

from tm_devices.commands import AWG5200Mixin
from tm_devices.drivers.pi.signal_generators.awgs.awg import (
    AWG,
    AWGChannel,
    AWGSourceDeviceConstants,
    ParameterBounds,
)
from tm_devices.helpers import (
    ReadOnlyCachedProperty,
    SignalSourceFunctionsAWG,
    SignalSourceOutputPaths5200,
    SignalSourceOutputPathsBase,
)


class AWG5200Channel(AWGChannel):
    """AWG5200 channel driver."""

    def __init__(self, awg: "AWG", channel_name: str) -> None:
        """Create an AWG5200 channel object.

        Args:
            awg: An AWG5200 object.
            channel_name: The channel name for the AWG channel.
        """
        super().__init__(awg, channel_name)
        self._awg = cast(AWG5200, awg)

    def set_frequency(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the frequency on the source.

        Args:
            value: The frequency value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        self._awg.set_if_needed("CLOCK:SRATE", value, verify_value=False, opc=True)
        time.sleep(0.1)
        self._awg.ieee_cmds.opc()
        self._awg.ieee_cmds.cls()
        self._awg.poll_query(30, "CLOCK:SRATE?", value, tolerance=tolerance, percentage=percentage)

    def set_offset(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the offset on the source.

        Args:
            value: The offset value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        self._awg.set_if_needed(
            f"{self.name}:VOLTAGE:OFFSET",
            value,
            tolerance=tolerance,
            percentage=percentage,
        )

    def set_output_path(self, value: Optional[SignalSourceOutputPathsBase] = None) -> None:
        """Set the output signal path on the source.

        Args:
            value: The output signal path.
        """
        if not value:
            value = self._awg.output_signal_path.DCHB
        if value not in self._awg.output_signal_path:
            output_signal_path_error = (
                f"{value.value} is an invalid output signal path for {self._awg.model}."
            )
            raise ValueError(output_signal_path_error)
        self._awg.set_if_needed(f"OUTPUT{self.num}:PATH", value.value)

    def setup_burst_waveform(self, filename: str, burst_count: int = 0) -> None:
        """Prepare device for burst waveform.

        Args:
            filename: The filename for the burst waveform to generate.
            burst_count: The number of wavelengths to be generated.
        """
        del filename
        if burst_count > 0 and "SEQ" not in self._awg.opt_string:
            sequence_license_error = (
                "A sequencing license is required to generate a burst waveform."
            )
            raise AssertionError(sequence_license_error)
        if burst_count <= 0:
            error_message = f"{burst_count} is an invalid burst value. Burst count must be > 0."
            raise ValueError(error_message)


class AWG5200(AWG5200Mixin, AWG):
    """AWG5200 device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=16200000,
        memory_min_record_length=1,
    )
    sample_waveform_file = (
        "C:\\Program Files\\Tektronix\\AWG5200\\Samples\\AWG5k7k Predefined Waveforms.awgx"
    )

    ################################################################################################
    # Properties
    ################################################################################################
    @property
    def output_signal_path(self) -> Type[SignalSourceOutputPaths5200]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Return the output signal path enum."""
        return SignalSourceOutputPaths5200

    @ReadOnlyCachedProperty
    def source_channel(self) -> MappingProxyType[str, AWGChannel]:
        """Mapping of channel names to AWGChannel objects."""
        channel_map: Dict[str, AWG5200Channel] = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWG5200Channel(self, channel_name)
        return MappingProxyType(channel_map)

    ################################################################################################
    # Public Methods
    ################################################################################################
    def load_waveform_set(
        self,
        waveform_file: Optional[str] = None,
        waveform: Optional[str] = None,
    ) -> None:
        """Load in all waveforms or a specific waveform from a waveform file.

        Arguments:
            waveform_file: The waveform file to load.
            waveform: The specific waveform to load from the waveform file.
        """
        if not waveform_file:
            waveform_file = self.sample_waveform_file
        waveform_file_type = Path(waveform_file).suffix.lower()
        if waveform_file_type not in [".awg", ".awgx", ".mat", ".seqx"]:
            waveform_file_type_error = (
                f"{waveform_file_type} is an invalid waveform file extension."
            )
            raise ValueError(waveform_file_type_error)
        if not waveform:
            self.write(command=f'MMEMORY:OPEN:SASSET "{waveform_file}"', opc=True)
        else:
            self.write(
                command=f'MMEMORY:OPEN:SASSET:WAVEFORM "{waveform_file}", "{waveform}"', opc=True
            )

    def generate_function(  # noqa: PLR0913  # pylint: disable=too-many-locals
        self,
        frequency: float,
        function: SignalSourceFunctionsAWG,
        amplitude: float,
        offset: float,
        channel: str = "all",
        output_path: Optional[SignalSourceOutputPathsBase] = None,
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
            output_path: The output signal path of the specified channel.
            burst: The number of wavelengths to be generated.
            termination: The impedance this device's ``channel`` expects to see at the received end.
            duty_cycle: The duty cycle percentage within [10.0, 90.0].
            polarity: The polarity to set the signal to.
            symmetry: The symmetry to set the signal to, only applicable to certain functions.
        """
        predefined_name, needed_sample_rate = self._get_predefined_filename(
            frequency, function, output_path, symmetry
        )
        self.ieee_cmds.opc()
        self.ieee_cmds.cls()
        for channel_name in self._validate_channels(channel):
            source_channel = cast(AWG5200Channel, self.source_channel[channel_name])
            if not burst:
                self.set_and_check(f"OUTPUT{source_channel.num}:STATE", "0")
            self.set_waveform_properties(
                source_channel=source_channel,
                output_path=output_path,
                predefined_name=predefined_name,
                needed_sample_rate=needed_sample_rate,
                amplitude=amplitude,
                offset=offset,
                burst=burst,
            )
            self.ieee_cmds.wai()
            self.ieee_cmds.opc()
            self.ieee_cmds.cls()
            self.set_if_needed(f"OUTPUT{source_channel.num}:STATE", "1")
        self.ieee_cmds.opc()
        self.write("AWGCONTROL:RUN")
        time.sleep(0.1)
        self.ieee_cmds.opc()
        self.ieee_cmds.cls()
        self.poll_query(30, "AWGControl:RSTate?", 2.0)
        self.expect_esr(0)

    def set_waveform_properties(  # noqa: PLR0913
        self,
        source_channel: AWGChannel,
        output_path: Optional[SignalSourceOutputPathsBase],
        predefined_name: str,
        needed_sample_rate: float,
        amplitude: float,
        offset: float,
        burst: int,
    ) -> None:
        """Set the properties of the waveform.

        Args:
            source_channel: The source channel class for the requested channel.
            output_path: The output signal path of the specified channel.
            predefined_name: The name of the function to generate.
            needed_sample_rate: The required sample
            amplitude: The amplitude of the signal to generate.
            offset: The offset of the signal to generate.

            burst: The number of wavelengths to be generated.
        """
        if predefined_name not in self.query("WLISt:LIST?").split(","):
            self.load_waveform_set()
        source_channel = cast(AWG5200Channel, source_channel)
        super().set_waveform_properties(
            source_channel=source_channel,
            output_path=output_path,
            predefined_name=predefined_name,
            needed_sample_rate=needed_sample_rate,
            amplitude=amplitude,
            offset=offset,
            burst=burst,
        )

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _get_series_specific_constraints(
        self,
        output_path: Optional[SignalSourceOutputPathsBase],
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        """Get constraints which are dependent on the model series."""
        if not output_path:
            output_path = self.output_signal_path.DCHB

        if "DC" in self.opt_string and output_path == self.output_signal_path.DCHB:
            amplitude_range = ParameterBounds(lower=25.0e-3, upper=1.5)
        elif output_path == self.output_signal_path.DCHV:
            amplitude_range = ParameterBounds(lower=10.0e-3, upper=5.0)
        else:
            amplitude_range = ParameterBounds(lower=25.0e-3, upper=750.0e-3)

        offset_range = ParameterBounds(lower=-2.0, upper=2.0)

        max_sample_rate = 25.0 if "25" in self.opt_string else 50.0
        # option is the sample rate in hundreds of Mega Hertz
        sample_rate_range = ParameterBounds(lower=300.0, upper=max_sample_rate * 100.0e6)

        return amplitude_range, offset_range, sample_rate_range
