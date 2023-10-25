# pyright: reportPrivateUsage=none
"""Test the AWGs."""
import pytest

from tm_devices import DeviceManager
from tm_devices.drivers.pi.signal_sources.awgs.awg import (
    AWGSourceDeviceConstants,
    ExtendedSourceDeviceConstants,
    ParameterRange,
    SignalSourceFunctionsAWG,
)


def check_constraints(
    constraint: ExtendedSourceDeviceConstants,
    sample_range: ParameterRange,
    amplitude_range: ParameterRange,
    offset_range: ParameterRange,
    length_range: ParameterRange,
):
    assert constraint == ExtendedSourceDeviceConstants(
        amplitude_range=amplitude_range,
        offset_range=offset_range,
        frequency_range=ParameterRange(
            min=sample_range.min / length_range.max, max=sample_range.max / length_range.min
        ),
        sample_rate_range=sample_range,
        square_duty_cycle_range=None,
        pulse_width_range=None,
        ramp_symmetry_range=None,
    )


def test_awg5200(device_manager: DeviceManager, capsys: pytest.CaptureFixture[str]) -> None:
    """Test the AWG5200 driver.

    Args:
        device_manager: The DeviceManager object.
        capsys: The captured stdout and stderr.
    """
    awg5200_50 = device_manager.add_awg("awg520050-hostname", alias="awg520050")
    assert id(device_manager.get_awg(number_or_alias="awg5200_50")) == id(awg5200_50)
    assert id(device_manager.get_awg(number_or_alias=awg5200_50.device_number)) == id(awg5200_50)
    assert awg5200_50.total_channels == 4
    assert awg5200_50.all_channel_names_list == ("SOURCE1", "SOURCE2", "SOURCE3", "SOURCE4")
    awg5200_50.write("*SRE 256")
    awg5200_50.expect_esr(32, '1, "Command error"\n0,"No error"')
    with pytest.raises(AssertionError):
        awg5200_50.expect_esr(32, '1, Command error\n0,"No error"')
    awg5200_50.load_waveform("test", "file_path.txt", "TXT")
    assert 'MMEMory:IMPort "test", "file_path.txt", TXT' in capsys.readouterr().out
    awg5200_50.load_waveform("test", '"file_path.txt"', "TXT")
    assert 'MMEMory:IMPort "test", "file_path.txt", TXT' in capsys.readouterr().out
    assert awg5200_50.source_device_constants == AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=16200000,
        memory_min_record_length=1,
    )
    assert awg5200_50.opt_string == "50"
    awg520050_constraints = awg5200_50.get_waveform_constraints(SignalSourceFunctionsAWG.SIN)
    min_smaple_50 = 300.0
    max_sample_50 = 2.5e9
    assert awg520050_constraints == ExtendedSourceDeviceConstants(
        amplitude_range=ParameterRange(min=0.1, max=2.0),
        offset_range=ParameterRange(min=-0.5, max=0.5),
        frequency_range=ParameterRange(min=min_smaple_50 / 3600.0, max=max_sample_50 / 10.0),
        sample_rate_range=ParameterRange(min=min_smaple_50, max=max_sample_50),
        square_duty_cycle_range=None,
        pulse_width_range=None,
        ramp_symmetry_range=None,
    )
    awg5200 = device_manager.add_awg("awg520025-hostname", alias="awg520025")
    assert awg5200_50.opt_string == "25"
    awg520025_constraints = awg5200.get_waveform_constraints(SignalSourceFunctionsAWG.SQUARE)
    min_smaple_25 = 300.0
    max_sample_25 = 2.5e9
    assert awg520025_constraints == ExtendedSourceDeviceConstants(
        amplitude_range=ParameterRange(min=0.1, max=2.0),
        offset_range=ParameterRange(min=-0.5, max=0.5),
        frequency_range=ParameterRange(min=min_smaple_25 / 1000.0, max=max_sample_25 / 10.0),
        sample_rate_range=ParameterRange(min=min_smaple_25, max=max_sample_25),
        square_duty_cycle_range=None,
        pulse_width_range=None,
        ramp_symmetry_range=None,
    )


def test_awg70k(device_manager: DeviceManager, capsys: pytest.CaptureFixture[str]) -> None:
    ampl_range = ParameterRange(min=0.5, max=1.0)
    offset_range = ParameterRange(min=-0.5, max=0.5)
    awg70ka150 = device_manager.add_awg("awg70ka150-hostname", alias="awg70ka150")
    awg70ka225 = device_manager.add_awg("awg70ka225-hostname", alias="awg70ka225")
    awg70ka216 = device_manager.add_awg("awg70ka216-hostname", alias="awg70ka216")
    awg70kb208 = device_manager.add_awg("awg70kb208-hostname", alias="awg70kb208")
    length_range = ParameterRange(min=10, max=1000)
    min_smaple = 1.5e3
    awg_list = [awg70ka150, awg70ka225, awg70ka216, awg70kb208]
    for awg in awg_list:
        option = awg.alias[-3:]
        assert awg.opt_string == option

        constraints = awg.get_waveform_constraints(SignalSourceFunctionsAWG.RAMP)

        sample_range = ParameterRange(min=min_smaple, max=int(option[1:3]) * 1.0e9)
        check_constraints(
            constraints,
            sample_range,
            ampl_range,
            offset_range,
            length_range,
        )


def test_awg7k(device_manager: DeviceManager, capsys: pytest.CaptureFixture[str]) -> None:
    ampl_range = ParameterRange(min=0.5, max=1.0)
    offset_range = ParameterRange(min=-0.5, max=0.5)
    awg70ka150 = device_manager.add_awg("awg7k01-hostname", alias="awg7k01")
    awg70ka225 = device_manager.add_awg("awg7k06-hostname", alias="awg7k06")
