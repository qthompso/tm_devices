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
    awg520050 = device_manager.add_awg("awg520050-hostname", alias="awg520050")
    assert id(device_manager.get_awg(number_or_alias="awg520050")) == id(awg520050)
    assert id(device_manager.get_awg(number_or_alias=awg520050.device_number)) == id(awg520050)
    assert awg520050.total_channels == 4
    assert awg520050.all_channel_names_list == ("SOURCE1", "SOURCE2", "SOURCE3", "SOURCE4")
    awg520050.write("*SRE 256")
    awg520050.expect_esr(32, '1, "Command error"\n0,"No error"')
    with pytest.raises(AssertionError):
        awg520050.expect_esr(32, '1, Command error\n0,"No error"')
    awg520050.load_waveform("test", "file_path.txt", "TXT")
    assert 'MMEMory:IMPort "test", "file_path.txt", TXT' in capsys.readouterr().out
    awg520050.load_waveform("test", '"file_path.txt"', "TXT")
    assert 'MMEMory:IMPort "test", "file_path.txt", TXT' in capsys.readouterr().out
    assert awg520050.source_device_constants == AWGSourceDeviceConstants(
        memory_page_size=1,
        memory_max_record_length=16200000,
        memory_min_record_length=1,
    )
    assert awg520050.opt_string == "50"
    awg520050_constraints = awg520050.get_waveform_constraints(SignalSourceFunctionsAWG.SIN)
    min_smaple_50 = 300.0
    max_sample_50 = 5.0e9
    assert awg520050_constraints == ExtendedSourceDeviceConstants(
        amplitude_range=ParameterRange(min=0.1, max=2.0),
        offset_range=ParameterRange(min=-0.5, max=0.5),
        frequency_range=ParameterRange(min=min_smaple_50 / 3600.0, max=max_sample_50 / 10.0),
        sample_rate_range=ParameterRange(min=min_smaple_50, max=max_sample_50),
        square_duty_cycle_range=None,
        pulse_width_range=None,
        ramp_symmetry_range=None,
    )
    awg520025 = device_manager.add_awg("awg520025-hostname", alias="awg520025")
    assert awg520025.opt_string == "25"
    awg520025_constraints = awg520025.get_waveform_constraints(SignalSourceFunctionsAWG.DC)
    min_smaple_25 = 300.0
    max_sample_25 = 2.5e9
    assert awg520025_constraints == ExtendedSourceDeviceConstants(
        amplitude_range=ParameterRange(min=0.1, max=2.0),
        offset_range=ParameterRange(min=-0.5, max=0.5),
        frequency_range=ParameterRange(min=min_smaple_25 / 1000.0, max=max_sample_25 / 1000.0),
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

    awg7k01 = device_manager.add_awg("awg7k01-hostname", alias="awg7k01")
    awg7k06 = device_manager.add_awg("awg7k06-hostname", alias="awg7k06")
    awg7kb02 = device_manager.add_awg("awg7kb02-hostname", alias="awg7kb02")
    awg7kb01 = device_manager.add_awg("awg7kb01-hostname", alias="awg7kb01")
    awg7kc06 = device_manager.add_awg("awg7kc06-hostname", alias="awg7kc06")
    awg7kc01 = device_manager.add_awg("awg7kc01-hostname", alias="awg7kc01")
    length_range = ParameterRange(min=10, max=1000)
    awg_list = [awg7k01, awg7k06, awg7kb02, awg7kb01, awg7kc06, awg7kc01]
    for awg in awg_list:
        option = awg.alias[-2:]
        assert awg.opt_string == option

        sample_range = ParameterRange(min=10.0e6, max=int(awg.model[4:6]) * 1.0e9)

        if option in ("02", "06"):
            ampl_range = ParameterRange(min=0.5, max=1.0)
            offset_range = ParameterRange(min=-0.0, max=0.0)
        else:
            offset_range = ParameterRange(min=-0.5, max=0.5)
            ampl_range = ParameterRange(min=50.0e-3, max=2.0)

        constraints = awg.get_waveform_constraints(SignalSourceFunctionsAWG.TRIANGLE)

        check_constraints(
            constraints,
            sample_range,
            ampl_range,
            offset_range,
            length_range,
        )


def test_awg5k(device_manager: DeviceManager, capsys: pytest.CaptureFixture[str]) -> None:
    awg5k = device_manager.add_awg("awg5k-hostname", alias="awg5k")
    awg5kb = device_manager.add_awg("awg5kb-hostname", alias="awg5kb")
    awg5kc = device_manager.add_awg("awg5kc-hostname", alias="awg5kc")
    length_range = ParameterRange(min=960, max=960)
    awg_list = [awg5k, awg5kb, awg5kc]
    offset_range = ParameterRange(min=-2.25, max=2.25)
    ampl_range = ParameterRange(min=20.0e-3, max=4.5)

    for awg in awg_list:
        sample_range = ParameterRange(min=10.0e6, max=int(awg.model[5]) * 600.0e6 + 600.0e6)

        constraints = awg.get_waveform_constraints(SignalSourceFunctionsAWG.CLOCK)

        check_constraints(
            constraints,
            sample_range,
            ampl_range,
            offset_range,
            length_range,
        )
