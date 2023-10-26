"""AFG31K device driver module."""
from typing import Optional, Tuple

from tm_devices.drivers.pi.signal_sources.afgs.afg3k import (
    AFG3K,
    AFGSourceDeviceConstants,
    ParameterRange,
    SignalSourceFunctionsAFG,
)


class AFG3KC(AFG3K):
    """AFG31K device driver."""

    _DEVICE_CONSTANTS = AFGSourceDeviceConstants(
        memory_page_size=2,
        memory_max_record_length=131072,
        memory_min_record_length=2,
    )

    ################################################################################################
    # Magic Methods
    ################################################################################################

    ################################################################################################
    # Properties
    ################################################################################################

    ################################################################################################
    # Public Methods
    ################################################################################################

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _reboot(self) -> None:
        """Reboot the device."""
        self.write("SYSTem:RESTart")
