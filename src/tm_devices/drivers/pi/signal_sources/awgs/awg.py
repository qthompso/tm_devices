"""Base AWG device driver module."""
import inspect
import os
import struct

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from typing import Dict, Literal, Optional, Tuple, Type

from tm_devices.driver_mixins.signal_generator_mixin import (
    ExtendedSourceDeviceConstants,
    ParameterBounds,
    SourceDeviceConstants,
)
from tm_devices.drivers.device import family_base_class
from tm_devices.drivers.pi.signal_sources.signal_source import SignalSource
from tm_devices.helpers import DeviceTypes, LoadImpedanceAFG, SignalSourceFunctionsAWG


@dataclass(frozen=True)
class AWGSourceDeviceConstants(SourceDeviceConstants):
    """Class to hold source device constants."""

    functions: Type[SignalSourceFunctionsAWG] = SignalSourceFunctionsAWG


@family_base_class
class AWG(SignalSource, ABC):
    """Base AWG device driver."""

    _DEVICE_TYPE = DeviceTypes.AWG.value

    ################################################################################################
    # Magic Methods
    ################################################################################################

    ################################################################################################
    # Properties
    ################################################################################################
    @property
    def source_device_constants(self) -> AWGSourceDeviceConstants:
        """Return the device constants."""
        return self._DEVICE_CONSTANTS  # type: ignore

    @cached_property
    def total_channels(self) -> int:
        """Return the total number of channels (all types)."""
        return int(self.query("AWGControl:CONFigure:CNUMber?", verbose=False))

    ################################################################################################
    # Public Methods
    ################################################################################################
    def load_waveform(self, wfm_name: str, waveform_file_path: str, wfm_type: str) -> None:
        """Load a waveform into the memory of the AWG.

        Args:
            wfm_name: The name to set the loaded waveform to on the AWG.
            waveform_file_path: The path to the waveform.
            wfm_type: The type of the waveform to import.
        """
        if not waveform_file_path.startswith('"'):
            waveform_file_path = '"' + waveform_file_path
        if not waveform_file_path.endswith('"'):
            waveform_file_path += '"'
        self.write(f'MMEMory:IMPort "{wfm_name}", {waveform_file_path}, {wfm_type}')
        self._ieee_cmds.opc()

    def generate_waveform(  # noqa: PLR0913  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        frequency: float,
        function: AWGSourceDeviceConstants,
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

        Raises:
            NotImplementedError: Indicates the current driver has not implemented this method.
        """
        # TODO: implement
        raise NotImplementedError(
            f"``.{inspect.currentframe().f_code.co_name}()``"  # pyright: ignore
            f" is not yet implemented for the {self.__class__.__name__} driver"
        )

    def get_waveform_constraints(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        function: Optional[SignalSourceFunctionsAWG] = None,
        waveform_length: Optional[int] = None,
        frequency: Optional[float] = None,
        load_impedance: LoadImpedanceAFG = LoadImpedanceAFG.HIGHZ,
    ) -> ExtendedSourceDeviceConstants:
        """Get the constraints that restrict the waveform to certain parameter ranges.

        Args:
            function: The function that needs to be generated.
            waveform_length: The length of the waveform if no function or arbitrary is provided.
            frequency: The frequency of the waveform that needs to be generated.
            load_impedance: The suggested impedance on the source.
        """
        del frequency, load_impedance
        if (function and waveform_length) or (not function and not waveform_length):
            msg = "AWG Constraints require function XOR waveform_length."
            raise ValueError(msg)
        amplitude_range, offset_range, sample_rate_range = self._get_series_specific_constraints()
        if function:
            func_sample_rate_lookup: Dict[str, ParameterBounds] = {
                SignalSourceFunctionsAWG.SIN.name: ParameterBounds(lower=10, upper=3600),
                SignalSourceFunctionsAWG.CLOCK.name: ParameterBounds(lower=960, upper=960),
                SignalSourceFunctionsAWG.SQUARE.name: ParameterBounds(lower=10, upper=1000),
                SignalSourceFunctionsAWG.RAMP.name: ParameterBounds(lower=10, upper=1000),
                SignalSourceFunctionsAWG.TRIANGLE.name: ParameterBounds(lower=10, upper=1000),
                SignalSourceFunctionsAWG.DC.name: ParameterBounds(lower=1000, upper=1000),
            }
            slowest_frequency = (
                sample_rate_range.lower / func_sample_rate_lookup[function.name].upper
            )
            fastest_frequency = (
                sample_rate_range.upper / func_sample_rate_lookup[function.name].lower
            )
        elif waveform_length:
            slowest_frequency = sample_rate_range.lower / waveform_length
            fastest_frequency = sample_rate_range.upper / waveform_length
        else:
            slowest_frequency = 0.0
            fastest_frequency = 0.0

        frequency_range = ParameterBounds(lower=slowest_frequency, upper=fastest_frequency)
        return ExtendedSourceDeviceConstants(
            amplitude_range=amplitude_range,
            offset_range=offset_range,
            frequency_range=frequency_range,
            sample_rate_range=sample_rate_range,
        )

    ################################################################################################
    # Private Methods
    ################################################################################################
    def _reboot(self) -> None:
        """Reboot the device."""
        # TODO: overwrite the reboot code here

    # TODO: add testing for this
    def _send_waveform(self, target_file: str) -> None:  # pragma: no cover
        """Send the waveform information to the AWG as a file in memory.

        Args:
            target_file: The name of the waveform file.
        """
        with open(target_file, "rb") as file_handle:
            file_handle.seek(0, 0)
            waveform_data = file_handle.read()
            # must be even to send
            if len(waveform_data) % 2:
                waveform_data += b"\0"

            info_len = int(len(waveform_data) / 2)
            bin_waveform = struct.unpack(">" + str(info_len) + "H", waveform_data)

            # Turn "path/to/stuff.wfm" into "stuff.wfm".
            filename_target = os.path.basename(target_file)
            # Write the waveform data to the AWG memory.
            string_to_send = 'MMEMORY:DATA "' + filename_target + '",'
            self._visa_resource.write_binary_values(
                string_to_send,
                bin_waveform,
                datatype="H",
                is_big_endian=True,
                termination="\r\n",
                encoding="latin-1",
            )

    @abstractmethod
    def _get_series_specific_constraints(
        self,
    ) -> Tuple[ParameterBounds, ParameterBounds, ParameterBounds]:
        raise NotImplementedError
