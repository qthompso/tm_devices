"""AWG7K device driver module."""
from functools import cached_property
from types import MappingProxyType
from typing import Optional, Tuple

from tm_devices.commands import AWG7KMixin
from tm_devices.drivers.pi.signal_generators.awgs.awg import (
    AWG,
    AWGChannel,
    AWGSourceDeviceConstants,
    ParameterBounds,
)
from tm_devices.drivers.pi.signal_generators.awgs.awg5k import AWG5KChannel
from tm_devices.helpers import SignalSourceOutputPaths


class AWG7KChannel(AWG5KChannel):
    """AWG7K channel driver."""


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
    @cached_property
    def source_channel(self) -> "MappingProxyType[str, AWGChannel]":
        """Mapping of channel names to AWGChannel objects."""
        channel_map = {}
        for channel_name in self.all_channel_names_list:
            channel_map[channel_name] = AWG7KChannel(self, channel_name)
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

        # if we are using the high bandwidth options
        if "02" in self.opt_string or "06" in self.opt_string:
            amplitude_range = ParameterBounds(lower=500.0e-3, upper=1.0)
            offset_range = ParameterBounds(lower=-0.0, upper=0.0)
        else:
            amplitude_range = ParameterBounds(lower=50e-3, upper=2.0)
            if output_path == SignalSourceOutputPaths.DCA:
                offset_range = ParameterBounds(lower=-0.5, upper=0.5)
            else:
                offset_range = ParameterBounds(lower=-0.0, upper=0.0)
        # AWG(Arbitrary Waveform Generator)7(Series)xx(GS/s)x(Channels)z(Model)
        sample_rate_range = ParameterBounds(lower=10.0e6, upper=int(self.model[4:6]) * 1.0e9)

        return amplitude_range, offset_range, sample_rate_range
