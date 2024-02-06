"""AWG7K device driver module."""
from types import MappingProxyType
from typing import Dict, Optional, Tuple

from tm_devices.commands import AWG7KMixin
from tm_devices.drivers.device import family_base_class
from tm_devices.drivers.pi.signal_generators.awgs.awg import (
    AWG,
    AWGChannel,
    AWGSourceDeviceConstants,
    ParameterBounds,
)
from tm_devices.drivers.pi.signal_generators.awgs.awg5k import AWG5KChannel
from tm_devices.helpers import (
    ReadOnlyCachedProperty,
    SignalSourceOutputPathsBase,
)


class AWG7KChannel(AWG5KChannel):
    """AWG7K channel driver."""

    def set_offset(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the offset on the source channel.

        Args:
            value: The offset value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        output_path = float(self._awg.query(f"AWGCONTROL:DOUTPUT{self.num}:STATE?"))
        if not ("02" in self._awg.opt_string or "06" in self._awg.opt_string) and not output_path:
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
                f"The offset can only be set on {self._awg.model} without an 02 or 06 "
                "option and with an output signal path of "
                f"{self._awg.OutputSignalPath.DCA.value} "
                f"(AWGCONTROL:DOUTPUT{self.num}:STATE set to 0)."
            )
            raise ValueError(offset_error)

    def set_output_path(self, value: Optional[SignalSourceOutputPathsBase] = None) -> None:
        """Set the output signal path on the source channel.

        Args:
            value: The output signal path.
        """
        if not ("02" in self._awg.opt_string or "06" in self._awg.opt_string):
            super().set_output_path(value)


@family_base_class
class AWG7K(AWG7KMixin, AWG):
    """AWG7K device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=32400000,
        memory_min_record_length=2,
    )

    ################################################################################################
    # Properties
    ################################################################################################
    @ReadOnlyCachedProperty
    def source_channel(self) -> MappingProxyType[str, AWGChannel]:
        """Mapping of channel names to AWGChannel objects."""
        channel_map: Dict[str, AWG7KChannel] = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWG7KChannel(self, channel_name)
        return MappingProxyType(channel_map)

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _get_series_specific_constraints(
        self,
        output_path: Optional[SignalSourceOutputPathsBase],
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        """Get constraints which are dependent on the model series."""
        if not output_path:
            output_path = self.OutputSignalPath.DCA

        # if we are using the high bandwidth options
        if "02" in self.opt_string or "06" in self.opt_string:
            amplitude_range = ParameterBounds(lower=500.0e-3, upper=1.0)
            offset_range = ParameterBounds(lower=-0.0, upper=0.0)
        else:
            amplitude_range = ParameterBounds(lower=50e-3, upper=2.0)
            if output_path == self.OutputSignalPath.DCA:
                offset_range = ParameterBounds(lower=-0.5, upper=0.5)
            else:
                offset_range = ParameterBounds(lower=-0.0, upper=0.0)
        # AWG(Arbitrary Waveform Generator)7(Series)xx(GS/s)x(Channels)z(Model)
        sample_rate_range = ParameterBounds(lower=10.0e6, upper=int(self.model[4:6]) * 1.0e9)

        return amplitude_range, offset_range, sample_rate_range
