"""AFG31K device driver module."""
from typing import Tuple

from tm_devices.drivers.pi.signal_sources.afgs.afg3k import (
    AFG3K,
)


class AFG3KC(AFG3K):
    """AFG31K device driver."""

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

    def _acquire_frequency_multipliers(self) -> Tuple[float, float]:
        """"""
        model_number = self.model[4:6]
        # handle amplitude
        if model_number == "02":
            square_wave_multiplier = 1
            other_wave_multiplier = 0.02
        elif model_number == "05":
            square_wave_multiplier = 0.8
            other_wave_multiplier = 0.016
        else:
            square_wave_multiplier = 0.5
            other_wave_multiplier = 0.01
        return square_wave_multiplier, other_wave_multiplier
