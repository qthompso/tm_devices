"""AWG70KA device driver module."""
from pathlib import Path
from types import MappingProxyType
from typing import cast, Dict, Optional, Tuple

from tm_devices.commands import AWG70KAMixin
from tm_devices.drivers.device import family_base_class
from tm_devices.drivers.pi.signal_generators.awgs.awg import (
    AWG,
    AWGSourceChannel,
    AWGSourceDeviceConstants,
    ParameterBounds,
)
from tm_devices.helpers import (
    ReadOnlyCachedProperty,
    SASSetWaveformFileTypes,
    SignalGeneratorOutputPathsBase,
)


class AWG70KASourceChannel(AWGSourceChannel):
    """AWG70KA source channel driver."""

    def set_frequency(self, value: float, absolute_tolerance: float = 0) -> None:
        """Set the frequency on the source channel.

        Args:
            value: The frequency value to set.
            absolute_tolerance: The acceptable difference between two floating point values.
        """
        self.awg.set_if_needed(
            f"{self.name}:FREQUENCY", value, tolerance=absolute_tolerance, opc=True
        )

    def set_output_signal_path(
        self, value: Optional[SignalGeneratorOutputPathsBase] = None
    ) -> None:
        """Set the output signal path on the source channel.

        Can only set the output signal path to DCA when an MDC4500 is connected to the AWG70K.

        Args:
            value: The output signal path
                (The default is to attempt to set output signal path to DCA and falling back to DIR)
        """
        if not value:
            # Attempt to set the output signal path to DCA.
            try:
                self.awg.set_and_check(
                    f"OUTPUT{self.num}:PATH", self.awg.OutputSignalPath.DCA.value
                )
            except AssertionError:  # pragma: no cover
                # If error, set output signal path to DIR.
                expected_esr_message = (
                    '-222,"Data out of range;Data Out of Range - '
                    f'OUTPUT{self.num}:PATH DCA\r\n"\n0,"No error"'
                )
                self.awg.expect_esr("16", expected_esr_message)
                self.awg.set_and_check(
                    f"OUTPUT{self.num}:PATH", self.awg.OutputSignalPath.DIR.value
                )
        elif value in self.awg.OutputSignalPath:
            self.awg.set_if_needed(f"OUTPUT{self.num}:PATH", value.value)
        else:
            output_signal_path_error = (
                f"{value.value} is an invalid output signal path for {self.awg.model}."
            )
            raise ValueError(output_signal_path_error)


@family_base_class
class AWG70KA(AWG70KAMixin, AWG):
    """AWG70KA device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=2000000000,
        memory_min_record_length=1,
    )
    sample_waveform_set_file = (
        "C:\\Program Files\\Tektronix\\AWG70000\\Samples\\AWG5k7k Predefined Waveforms.awgx"
    )

    ################################################################################################
    # Properties
    ################################################################################################
    @ReadOnlyCachedProperty
    def source_channel(self) -> "MappingProxyType[str, AWGSourceChannel]":
        """Mapping of channel names to AWG70KASourceChannel objects."""
        channel_map: Dict[str, AWG70KASourceChannel] = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWG70KASourceChannel(self, channel_name)
        return MappingProxyType(channel_map)

    ################################################################################################
    # Public Methods
    ################################################################################################
    def load_waveform_set(self, waveform_set_file: Optional[str] = None) -> None:
        """Load a waveform set into the memory of the AWG.

        Arguments:
            waveform_set_file: The waveform set file to load
                (The default is defined in the ``sample_wave_file`` attribute).
        """
        self._load_waveform_or_set(waveform_set_file=waveform_set_file, waveform_name=None)

    def load_waveform_from_set(
        self,
        waveform_name: str,
        waveform_set_file: Optional[str] = None,
    ) -> None:
        """Load in a specific waveform from a waveform set into the memory of the AWG.

        Arguments:
            waveform_name: The waveform name to load from the waveform set file.
            waveform_set_file: The waveform set file to load
                (The default is defined in the ``sample_wave_file`` attribute).
        """
        self._load_waveform_or_set(waveform_set_file=waveform_set_file, waveform_name=waveform_name)

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
        if waveform_name not in self.query("WLISt:LIST?", allow_empty=True):
            self.load_waveform_set()
        source_channel = cast(AWG70KASourceChannel, source_channel)
        super().set_waveform_properties(
            source_channel=source_channel,
            output_signal_path=output_signal_path,
            waveform_name=waveform_name,
            needed_sample_rate=needed_sample_rate,
            amplitude=amplitude,
            offset=offset,
        )

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _get_series_specific_constraints(
        self,
        output_signal_path: Optional[SignalGeneratorOutputPathsBase],
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        """Get constraints which are dependent on the model series."""
        if not output_signal_path:
            output_signal_path = self.OutputSignalPath.DIR

        if output_signal_path == self.OutputSignalPath.DCA:
            amplitude_range = ParameterBounds(lower=31.0e-3, upper=1.2)
            offset_range = ParameterBounds(lower=-400.0e-3, upper=800.0e-3)
        else:
            amplitude_range = ParameterBounds(lower=0.125, upper=0.5)
            offset_range = ParameterBounds(lower=-0.0, upper=0.0)

        rates = ["50", "25", "16", "08"]
        max_sample_rate = [rate for rate in rates if rate in self.opt_string][0]  # noqa: RUF015
        # first digit indicates the number of channels, second and third indicate sample rate (GHz)
        # option 150 would be a one channel source with 50 GHz sample rate
        sample_rate_range = ParameterBounds(lower=1.5e3, upper=int(max_sample_rate) * 1.0e9)
        return amplitude_range, offset_range, sample_rate_range

    def _cleanup(self) -> None:
        """Perform the cleanup defined for the device."""
        super()._cleanup()
        for source_channel in self.source_channel.values():
            source_channel.set_output_signal_path()
            source_channel.set_offset(0)

    def _load_waveform_or_set(
        self,
        waveform_set_file: Optional[str] = None,
        waveform_name: Optional[str] = None,
    ) -> None:
        """Load in a waveform set or a specific waveform from a waveform set into memory.

        Arguments:
            waveform_set_file: The waveform set file to load.
                (The default is defined in the ``sample_wave_file`` attribute).
            waveform_name: The waveform name to load from the waveform set file.
        """
        if not waveform_set_file:
            waveform_set_file = self.sample_waveform_set_file
        waveform_file_type = Path(waveform_set_file).suffix.lower()
        if waveform_file_type not in SASSetWaveformFileTypes:
            waveform_file_type_error = (
                f"{waveform_file_type} is an invalid waveform file extension."
            )
            raise ValueError(waveform_file_type_error)
        if not waveform_name:
            self.write(f'MMEMORY:OPEN:SASSET "{waveform_set_file}"', opc=True)
        else:
            self.write(
                f'MMEMORY:OPEN:SASSET:WAVEFORM "{waveform_set_file}", "{waveform_name}"', opc=True
            )
        self.expect_esr(0)
