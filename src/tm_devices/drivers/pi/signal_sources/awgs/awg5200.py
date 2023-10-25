"""AWG5200 device driver module."""
import time

from tm_devices.commands import AWG5200Mixin
from tm_devices.drivers.pi.signal_sources.awgs.awg import AWG, AWGChannel, AWGSourceDeviceConstants


class AWG5200Channel(AWGChannel):
    """AWG5200 channel driver."""

    def set_frequency(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the frequency on the source.

        Args:
            value: The frequency value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        self._pi_device.set_if_needed(
            "CLOCK:SRATE",
            round(value, -1),
            tolerance=tolerance,
            percentage=percentage,
        )
        time.sleep(0.1)
        self._pi_device.ieee_cmds.opc()
        self._pi_device.ieee_cmds.cls()
        self._pi_device.poll_query(30, "CLOCK:SRATE?", value, tolerance=10, percentage=percentage)


class AWG5200(AWG5200Mixin, AWG):
    """AWG5200 device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=16200000,
        memory_min_record_length=1,
    )

    ################################################################################################
    # Public Methods
    ################################################################################################
