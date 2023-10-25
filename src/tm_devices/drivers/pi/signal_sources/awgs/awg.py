"""Base AWG device driver module."""
import inspect
import os
import struct

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Dict, Literal, Optional, Tuple, Type

from tm_devices.driver_mixins.signal_generator_mixin import (
    ExtendedSourceDeviceConstants,
    ParameterRange,
    SourceDeviceConstants,
)
from tm_devices.drivers.device import family_base_class
from tm_devices.drivers.pi.signal_sources.signal_source import SignalSource
from tm_devices.helpers import DeviceTypes, SignalSourceFunctionsAWG


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

    def get_waveform_constraints(
        self,
        function: Optional[SignalSourceFunctionsAWG] = None,
        file_name: Optional[str] = None,
        frequency: Optional[float] = None,
    ) -> Optional[ExtendedSourceDeviceConstants]:
        if not function and not file_name:
            raise ValueError(f"Constraints require either a function or filename to be provided.")
        amplitude_range, offset_range, sample_rate_range = self._get_limited_constraints()
        if function:
            func_sample_rate_lookup: Dict[str, ParameterRange] = {
                SignalSourceFunctionsAWG.SIN.name: ParameterRange(10, 3600),
                SignalSourceFunctionsAWG.CLOCK.name: ParameterRange(960, 960),
                SignalSourceFunctionsAWG.SQUARE.name: ParameterRange(10, 1000),
                SignalSourceFunctionsAWG.RAMP.name: ParameterRange(10, 1000),
                SignalSourceFunctionsAWG.TRIANGLE.name: ParameterRange(10, 1000),
                SignalSourceFunctionsAWG.DC.name: ParameterRange(1000, 1000),
            }
            # set the low range to the lowest frequency on source divided by longest waveform
            slowest_frequency = sample_rate_range.min / func_sample_rate_lookup[function.name].max

            # set the high range to the highest frequency on source divided by shortest waveform
            fastest_frequency = sample_rate_range.max / func_sample_rate_lookup[function.name].min
        elif file_name:
            try:
                target_file = file_name.replace('"', "")
                wanted_file = Path(target_file).stem
                page_length = self.query(f'WLIST:WAVEFORM:LENGTH? "{wanted_file}"')
                page_length = int(page_length)
                # set the low range to the lowest frequency on source divided by longest waveform
                slowest_frequency = sample_rate_range.min / page_length

                # set the high range to the highest frequency on source divided by shortest waveform
                fastest_frequency = sample_rate_range.max / page_length
            except AssertionError:
                return None
            # set the new range
        else:
            return None
        frequency_range = ParameterRange(slowest_frequency, fastest_frequency)
        esdc = ExtendedSourceDeviceConstants(
            amplitude_range=amplitude_range,
            offset_range=offset_range,
            frequency_range=frequency_range,
            sample_rate_range=sample_rate_range,
        )

        return esdc

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
    def _get_limited_constraints(
        self,
    ) -> Tuple[Optional[ParameterRange], Optional[ParameterRange], Optional[ParameterRange]]:
        raise NotImplementedError
