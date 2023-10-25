"""AWG70KA device driver module."""
from tm_devices.commands import AWG70KAMixin
from tm_devices.drivers.pi.signal_sources.awgs.awg import AWG, AWGChannel, AWGSourceDeviceConstants


class AWG70KAChannel(AWGChannel):
    """AWG70KA channel driver."""

    def set_offset(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the offset on the source.

        Args:
            value: The offset value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        current_high = float(self._pi_device.query(f"{self.name}:VOLTAGE:HIGH?"))
        current_low = float(self._pi_device.query(f"{self.name}:VOLTAGE:LOW?"))

        current_amplitude = current_high - current_low
        high_voltage = round(current_amplitude / 2 + value, 3)
        low_voltage = round(-current_amplitude / 2 + value, 3)
        self._set_high_and_low_voltage(
            high_voltage, low_voltage, tolerance=tolerance, percentage=percentage
        )

    def set_amplitude(self, value: float, tolerance: float = 0, percentage: bool = False) -> None:
        """Set the amplitude on the source.

        Args:
            value: The amplitude value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        current_high = float(self._pi_device.query(f"{self.name}:VOLTAGE:HIGH?"))
        current_low = float(self._pi_device.query(f"{self.name}:VOLTAGE:LOW?"))

        current_amplitude = current_high - current_low
        offset = current_high - (current_amplitude / 2)
        high_voltage = round(value / 2 + offset, 3)
        low_voltage = round(-value / 2 + offset, 3)
        self._set_high_and_low_voltage(
            high_voltage, low_voltage, tolerance=tolerance, percentage=percentage
        )

    def _set_high_and_low_voltage(
        self,
        high_voltage: float,
        low_voltage: float,
        tolerance: float = 0,
        percentage: bool = False,
    ) -> None:
        """Set the HIGH and LOW voltage to the specified values.

        Args:
            high_voltage: The HIGH voltage value to set.
            low_voltage: The LOW voltage value to set.
            tolerance: The acceptable difference between two floating point values.
            percentage: A boolean indicating what kind of tolerance check to perform.
                 False means absolute tolerance: +/- tolerance.
                 True means percent tolerance: +/- (tolerance / 100) * value.
        """
        self._pi_device.set_and_check(
            f"{self.name}:VOLTAGE:HIGH",
            high_voltage,
            tolerance=tolerance,
            percentage=percentage,
        )
        self._pi_device.set_and_check(
            f"{self.name}:VOLTAGE:LOW",
            low_voltage,
            tolerance=tolerance,
            percentage=percentage,
        )


class AWG70KA(AWG70KAMixin, AWG):
    """AWG70KA device driver."""

    _DEVICE_CONSTANTS = AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=2000000000,
        memory_min_record_length=1,
    )

    ################################################################################################
    # Public Methods
    ################################################################################################
