"""AWG70KA device driver module."""
from pathlib import Path
from types import MappingProxyType
from typing import cast, Dict, Optional, Tuple

from tm_devices.commands import AWG70KAMixin
from tm_devices.drivers.pi.signal_generators.awgs.awg import (
    AWG,
    AWGChannel,
    AWGSourceDeviceConstants,
    ParameterBounds,
)
from tm_devices.helpers import (
    ReadOnlyCachedProperty,
    SignalSourceOutputPathsBase,
)


class AWG70KAChannel(AWGChannel):
    """AWG70KA channel driver."""

    def set_frequency(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the frequency on the source.

        Args:
            value: The frequency value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        self._awg.set_if_needed(
            f"{self.name}:FREQUENCY", value, tolerance=tolerance, percentage=percentage, opc=True
        )

    def set_output_path(self, value: Optional[SignalSourceOutputPathsBase] = None) -> None:
        """Set the output signal path on the source.

        Args:
            value: The output signal path.
        """
        if not value:
            try:
                self._awg.set_and_check(
                    f"OUTPUT{self.num}:PATH", self._awg.OutputSignalPath.DCA.value
                )
            except AssertionError:  # pragma: no cover
                expected_esr_message = (
                    '-222,"Data out of range;Data Out of Range - '
                    f'OUTPUT{self.num}:PATH DCA\r\n"\n0,"No error"'
                )
                self._awg.expect_esr("16", expected_esr_message)
                self._awg.set_and_check(
                    f"OUTPUT{self.num}:PATH", self._awg.OutputSignalPath.DIR.value
                )
        elif value in self._awg.OutputSignalPath:
            self._awg.set_if_needed(f"OUTPUT{self.num}:PATH", value.value)
        else:
            output_signal_path_error = (
                f"{value.value} is an invalid output signal path for {self._awg.model}."
            )
            raise ValueError(output_signal_path_error)


class AWG70KA(AWG70KAMixin, AWG):
    """AWG70KA device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=2000000000,
        memory_min_record_length=1,
    )
    sample_waveform_file = (
        "C:\\Program Files\\Tektronix\\AWG70000\\Samples\\AWG5k7k Predefined Waveforms.awgx"
    )

    ################################################################################################
    # Properties
    ################################################################################################
    @ReadOnlyCachedProperty
    def source_channel(self) -> MappingProxyType[str, AWGChannel]:
        """Mapping of channel names to AWGChannel objects."""
        channel_map: Dict[str, AWG70KAChannel] = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWG70KAChannel(self, channel_name)
        return MappingProxyType(channel_map)

    ################################################################################################
    # Public Methods
    ################################################################################################
    # TODO: 2 functions:
    #  - load_waveform_set
    #  - load_waveform
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
        # TODO: Separate loading waveform file and waveform
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
        if waveform_name not in self.query("WLISt:LIST?", allow_empty=True):
            self.load_waveform_set()
        source_channel = cast(AWG70KAChannel, source_channel)
        super().set_waveform_properties(
            source_channel=source_channel,
            output_path=output_path,
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
        output_path: Optional[SignalSourceOutputPathsBase],
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        """Get constraints which are dependent on the model series."""
        if not output_path:
            output_path = self.OutputSignalPath.DIR

        amplitude_range = ParameterBounds(lower=0.125, upper=0.5)

        if output_path == self.OutputSignalPath.DCA:
            offset_range = ParameterBounds(lower=-400.0e-3, upper=800.0e-3)
        else:
            offset_range = ParameterBounds(lower=-0.0, upper=0.0)

        rates = ["50", "25", "16", "08"]
        max_sample_rate = [rate for rate in rates if rate in self.opt_string][0]  # noqa: RUF015
        # first digit indicates the number of channels, second and third indicate sample rate (GHz)
        sample_rate_range = ParameterBounds(lower=1.5e3, upper=int(max_sample_rate) * 1.0e9)
        return amplitude_range, offset_range, sample_rate_range

    def _cleanup(self) -> None:
        """Perform the cleanup defined for the device."""
        super()._cleanup()
        for source_channel in self.source_channel.values():
            source_channel.set_output_path()
            source_channel.set_offset(0)
