"""A mixin class providing common methods and attributes for signal generators."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, NamedTuple, Optional, Type, TypeVar

from tm_devices.driver_mixins.class_extension_mixin import ExtendableMixin
from tm_devices.helpers.enums import (
    SignalSourceFunctionBase,
)

_SourceDeviceTypeVar = TypeVar("_SourceDeviceTypeVar", bound="SourceDeviceConstants")
_SignalSourceTypeVar = TypeVar("_SignalSourceTypeVar", bound=SignalSourceFunctionBase)

ParameterRange = NamedTuple("ParameterRange", [("min", float), ("max", float)])


@dataclass(frozen=True)
class ExtendedSourceDeviceConstants:
    """Class to hold source device constants."""

    amplitude_range: ParameterRange
    offset_range: ParameterRange
    frequency_range: ParameterRange
    sample_rate_range: Optional[ParameterRange] = None
    square_duty_cycle_range: Optional[ParameterRange] = None
    pulse_width_range: Optional[ParameterRange] = None
    ramp_symmetry_range: Optional[ParameterRange] = None


@dataclass(frozen=True)
class SourceDeviceConstants:
    """Class to hold source device constants."""

    memory_page_size: int
    memory_max_record_length: int
    memory_min_record_length: int
    functions: Type[SignalSourceFunctionBase]


class SignalGeneratorMixin(ExtendableMixin, ABC):
    """A mixin class which adds methods and properties for generating signals."""

    @staticmethod
    def _validate_generated_function(function: _SignalSourceTypeVar) -> _SignalSourceTypeVar:
        """Validate the functions within the waveform generation method.

        Args:
            function: The function type to verify.

        Raises:
            TypeError: Tells the user that they are using an incorrect function type.
        """
        if not issubclass(type(function), SignalSourceFunctionBase):
            msg = (
                "Generate Waveform does not accept functions as non Enums. "
                "Please use 'source_device_constants.functions'."
            )
            raise TypeError(msg)
        return function

    @property
    @abstractmethod
    def source_device_constants(
        self,
    ) -> _SourceDeviceTypeVar:  # pyright: ignore[reportInvalidTypeVarUse]
        """Return the device constants."""

    @abstractmethod
    def generate_waveform(  # noqa: PLR0913
        self,
        frequency: float,
        function: _SignalSourceTypeVar,  # pyright: ignore[reportInvalidTypeVarUse]
        amplitude: float,
        offset: float,
        channel: str = "all",
        burst: int = 0,
        termination: Literal["FIFTY", "HIGHZ"] = "FIFTY",
        duty_cycle: float = 50.0,
        polarity: Literal["NORMAL", "INVERTED"] = "NORMAL",
        symmetry: float = 50.0,
    ) -> None:
        """Generate a signal given the following parameters.

        Args:
            frequency: The frequency of the waveform to generate.
            function: The waveform shape to generate.
            amplitude: The amplitude of the signal to generate.
            offset: The offset of the signal to generate.
            channel: The channel name to output the signal from, or 'all'.
            burst: The number of wavelengths to be generated.
            termination: The impedance this device's ``channel`` expects to see at the received end.
            duty_cycle: The duty cycle percentage within [10.0, 90.0].
            polarity: The polarity to set the signal to.
            symmetry: The symmetry to set the signal to, only applicable to certain functions.
        """

    @abstractmethod
    def get_waveform_constraints(
        self,
        function: Optional[SignalSourceFunctionBase] = None,
        file_name: Optional[str] = None,
        frequency: Optional[float] = None,
    ) -> ExtendedSourceDeviceConstants:
        raise NotImplementedError
