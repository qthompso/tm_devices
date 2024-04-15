"""MSO5B device driver module."""

from tm_devices.commands import MSO5BMixin
from tm_devices.drivers.pi.scopes.tekscope.mso5 import MSO5


class MSO5B(MSO5BMixin, MSO5):
    """MSO5B device driver."""

    @staticmethod
    def _get_driver_specific_multipliers() -> float:
        """Return a value to multiply the original Tekscope IAFG frequency by."""
        return 2.0
