"""AWG5K device driver module."""
from functools import cached_property
from types import MappingProxyType
from typing import Optional, Tuple

from tm_devices.commands import AWG5KMixin
from tm_devices.drivers.pi.signal_generators.awgs.awg import (
    AWG,
    AWGChannel,
    AWGSourceDeviceConstants,
    ParameterBounds,
)
from tm_devices.helpers import SignalSourceOutputPaths


class AWG5KChannel(AWGChannel):
    """AWG5K channel driver."""

    def set_offset(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the offset on the source.

        Args:
            value: The offset value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        if not float(self._awg.query(f"AWGCONTROL:DOUTPUT{self.num}:STATE?")):
            self._awg.set_if_needed(
                f"{self.name}:VOLTAGE:OFFSET",
                value,
                tolerance=tolerance,
                percentage=percentage,
            )
        elif value:
            offset_error = (
                f"The offset can only be set on {self._awg.model} with an output signal path of "
                f"{SignalSourceOutputPaths.DCA.value} "
                f"(AWGCONTROL:DOUTPUT{self.num}:STATE set to 0)."
            )
            raise ValueError(offset_error)

    def set_output_path(self, value: Optional[SignalSourceOutputPaths] = None) -> None:
        """Set the output signal path on the source.

        Args:
            value: The output signal path.
        """
        if not value or value == SignalSourceOutputPaths.DCA:
            output_state = 0
        elif value == SignalSourceOutputPaths.DIR:
            output_state = 1
        else:
            output_signal_path_error = (
                f"{value.value} is an invalid output signal path for {self._awg.model}."
            )
            raise ValueError(output_signal_path_error)
        self._awg.set_if_needed(f"AWGCONTROL:DOUTPUT{self.num}:STATE", output_state)


class AWG5K(AWG5KMixin, AWG):
    """AWG5K device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=16200000,
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
            channel_map[channel_name] = AWG5KChannel(self, channel_name)
        return MappingProxyType(channel_map)

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _get_series_specific_constraints(
        self,
        output_path: Optional[SignalSourceOutputPaths],
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        """Get constraints which are dependent on the model series."""
        if not output_path:
            output_path = SignalSourceOutputPaths.DCA

        amplitude_range = ParameterBounds(lower=20.0e-3, upper=4.5)
        if output_path == SignalSourceOutputPaths.DCA:
            offset_range = ParameterBounds(lower=-2.25, upper=2.25)
        else:
            offset_range = ParameterBounds(lower=-0.0, upper=0.0)
        # AWG(Arbitrary Waveform Generator)5(Series)0x(.6 + .6GS/s)x(Channels)z(Model)
        sample_rate_range = ParameterBounds(
            lower=10.0e6, upper=600.0e6 + (600.0e6 * int(self.model[5]))
        )
        return amplitude_range, offset_range, sample_rate_range
