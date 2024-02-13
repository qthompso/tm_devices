"""AWG70KA device driver module."""
import math

from pathlib import Path
from types import MappingProxyType
from typing import cast, Dict, List, Optional, Tuple

from tm_devices.commands import AWG70KAMixin
from tm_devices.drivers.device import family_base_class
from tm_devices.drivers.pi.signal_generators.awgs.awg import (
    AWG,
    AWGChannel,
    AWGSourceDeviceConstants,
    ParameterBounds,
)
from tm_devices.helpers import (
    ReadOnlyCachedProperty,
    SASSetWaveformFileTypes,
    SignalSourceOutputPathsBase,
)


class AWG70KAChannel(AWGChannel):
    """AWG70KA channel driver."""

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
            f"{self.name}:FREQUENCY", value, tolerance=tolerance, percentage=percentage, opc=True
        )

    def set_output_signal_path(self, value: Optional[SignalSourceOutputPathsBase] = None) -> None:
        """Set the output signal path on the source channel.

        Can only set the output signal path to DCA when an MDC4500 is connected to the AWG70K.

        Args:
            value: The output signal path
                (The default is to attempt to set output signal path to DCA and falling back to DIR)
        """
        if not value:
            # Attempt to set the output signal path to DCA.
            try:
                self._awg.set_and_check(
                    f"OUTPUT{self.num}:PATH", self._awg.OutputSignalPath.DCA.value
                )
            except AssertionError:  # pragma: no cover
                # If error, set output signal path to DIR.
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


@family_base_class
class AWG70KA(AWG70KAMixin, AWG):
    """AWG70KA device driver."""

    sample_waveform_set_file = (
        "C:\\Program Files\\Tektronix\\AWG70000\\Samples\\AWG5k7k Predefined Waveforms.awgx"
    )

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=2000000000,
        memory_min_record_length=1,
    )

    ################################################################################################
    # Properties
    ################################################################################################
    @property
    def point_byte_length(self) -> int:
        """The number of bytes representing a single waveform point."""
        return 4

    @ReadOnlyCachedProperty
    def source_channel(self) -> "MappingProxyType[str, AWGChannel]":
        """Mapping of channel names to AWGChannel objects."""
        channel_map: Dict[str, AWG70KAChannel] = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWG70KAChannel(self, channel_name)
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

    def send_waveform_data_to_memory(self, points: List[float], waveform_name: str) -> None:  # pylint: disable=too-many-locals
        """Send the provided waveform data to the device and store in memory.

        Args:
            points: The list of points that represent the waveform.
            waveform_name: The waveform name to store the data as.
        """
        if not all(-1 <= point <= 1 for point in points):
            invalid_point_message = "All points must be between -1 and 1 (inclusive)."
            raise ValueError(invalid_point_message)
        num_points = len(points)
        self.write(f'WLIST:WAVEFORM:NEW "{waveform_name}", {num_points}')
        buffer = (
            f"WLIST:WAVEFORM:DATA "
            f'"{waveform_name}",0,{num_points},'
            f"#{len(str(num_points * self.point_byte_length))}{num_points * self.point_byte_length}"
        )
        self.write(buffer)
        for point in points:
            if not point:
                buffer += "".join([chr(0)] * 4)
            else:
                inverse_bit = 2**31 if point < 0 else 0
                # use log base 2 to find exponent and leftover floating point
                floating_point, integer = math.modf(-math.log(abs(point), 2))
                leftover = 2 ** (1 - floating_point) - 1
                # split at 23rd bit
                bit_shift = 2**23
                # bitshift both by 23
                floating_byte = int(leftover * bit_shift)
                shifted_integer = int(127 - (integer + 1)) * bit_shift
                # append all information
                data = inverse_bit + shifted_integer + floating_byte
                # extract each 8 bit block and encode as ASCII
                output_bytes = [chr((data >> (i * 8)) & 0b11111111) for i in range(4)]
                buffer += "".join(output_bytes)
        buffer += "\r\n"
        self.write_raw(buffer.encode("latin-1"))

    def set_waveform_properties(
        self,
        source_channel: AWGChannel,
        output_signal_path: Optional[SignalSourceOutputPathsBase],
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
        source_channel = cast(AWG70KAChannel, source_channel)
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
        output_signal_path: Optional[SignalSourceOutputPathsBase],
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        """Get constraints which are dependent on the model series."""
        if not output_signal_path:
            output_signal_path = self.OutputSignalPath.DIR

        amplitude_range = ParameterBounds(lower=0.125, upper=0.5)

        if output_signal_path == self.OutputSignalPath.DCA:
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
