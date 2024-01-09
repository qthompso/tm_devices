"""AWG70KA device driver module."""
from functools import cached_property
from pathlib import Path
from types import MappingProxyType
from typing import cast, Optional, Tuple

from tm_devices.commands import AWG70KAMixin
from tm_devices.drivers.pi.signal_generators.awgs.awg import (
    AWG,
    AWGChannel,
    AWGSourceDeviceConstants,
    ParameterBounds,
)
from tm_devices.helpers import SignalSourceOutputPaths


class AWG70KAChannel(AWGChannel):
    """AWG70KA channel driver."""

    sample_waveform_file = (
        "C:\\Program Files\\Tektronix\\AWG70000\\Samples\\AWG5k7k Predefined Waveforms.awgx"
    )

    def load_waveform(
        self,
        waveform_file: str,
        waveform: Optional[str] = None,
    ) -> None:
        """Load in all waveforms or a specific waveform from a waveform file.

        Arguments:
            waveform_file: The waveform file to load.
            waveform: The specific waveform to load from the waveform file.
        """
        waveform_file_type = Path(waveform_file).suffix.lower()
        if waveform_file_type not in [".awg", ".awgx", ".mat", ".seqx"]:
            waveform_file_type_error = (
                f"{waveform_file_type} is an invalid waveform file extension."
            )
            raise ValueError(waveform_file_type_error)
        if not waveform:
            self._awg.write(command=f'MMEMORY:OPEN:SASSET "{waveform_file}"', opc=True)
        else:
            self._awg.write(
                command=f'MMEMORY:OPEN:SASSET:WAVEFORM "{waveform_file}", "{waveform}"', opc=True
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
        self._awg.set_if_needed(
            f"{self.name}:FREQUENCY", value, tolerance=tolerance, percentage=percentage, opc=True
        )

    def set_output_path(self, value: Optional[SignalSourceOutputPaths] = None) -> None:
        """Set the output signal path on the source.

        Args:
            value: The output signal path.
        """
        if not value:
            value = SignalSourceOutputPaths.DIR
        if value not in [SignalSourceOutputPaths.DIR, SignalSourceOutputPaths.DCA]:
            output_signal_path_error = (
                f"{value.value} is an invalid output signal path for {self._awg.model}."
            )
            raise ValueError(output_signal_path_error)
        self._awg.set_if_needed(f"OUTPUT{self.num}:PATH", value.value)


class AWG70KA(AWG70KAMixin, AWG):
    """AWG70KA device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=2000000000,
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
            channel_map[channel_name] = AWG70KAChannel(self, channel_name)
        return MappingProxyType(channel_map)

    ################################################################################################
    # Public Methods
    ################################################################################################
    def set_waveform_properties(  # noqa: PLR0913
        self,
        source_channel: AWGChannel,
        output_path: Optional[SignalSourceOutputPaths],
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
        source_channel = cast(AWG70KAChannel, source_channel)
        source_channel.load_waveform(waveform_file=source_channel.sample_waveform_file)
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
        output_path: Optional[SignalSourceOutputPaths],
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        """Get constraints which are dependent on the model series."""
        if not output_path:
            output_path = SignalSourceOutputPaths.DIR

        amplitude_range = ParameterBounds(lower=0.125, upper=0.5)

        if output_path == SignalSourceOutputPaths.DCA:
            offset_range = ParameterBounds(lower=-400.0e-3, upper=800.0e-3)
        else:
            offset_range = ParameterBounds(lower=-0.0, upper=0.0)

        rates = ["50", "25", "16", "08"]
        max_sample_rate = [rate for rate in rates if rate in self.opt_string][0]  # noqa: RUF015
        # first digit indicates the number of channels, second and third indicate sample rate (GHz)
        sample_rate_range = ParameterBounds(lower=1.5e3, upper=int(max_sample_rate) * 1.0e9)
        return amplitude_range, offset_range, sample_rate_range
