"""MSO5B device driver module."""
from tm_devices.commands import MSO5BMixin
from tm_devices.drivers.pi.scopes.tekscope.mso5 import MSO5
from tm_devices.drivers.pi.scopes.tekscope.tekscope import ParameterRange


class MSO5B(MSO5BMixin, MSO5):
    """MSO5B device driver."""

    def _get_limited_constraints(
        self,
    ) -> ParameterRange:
        return ParameterRange(0.1, 100.0e6)
