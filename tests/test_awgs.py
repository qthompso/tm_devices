# pyright: reportPrivateUsage=none
"""Test the AWGs."""
import pytest

from tm_devices import DeviceManager
from tm_devices.drivers.pi.signal_generators.awgs.awg import (
    AWGSourceDeviceConstants,
    ExtendedSourceDeviceConstants,
    ParameterBounds,
    SignalSourceFunctionsAWG,
)


def check_constraints(
    constraint: ExtendedSourceDeviceConstants,
    sample_range: ParameterBounds,
    amplitude_range: ParameterBounds,
    offset_range: ParameterBounds,
    length_range: ParameterBounds,
) -> None:
    """Check to see if the waveform constraints are correct.

    Args:
        constraint: The constraints to verify.
        sample_range: The wanted sample range.
        amplitude_range: The wanted amplitude range.
        offset_range: The wanted offset_range.
        length_range: The length range of the waveform.
    """
    assert constraint == ExtendedSourceDeviceConstants(
        amplitude_range=amplitude_range,
        offset_range=offset_range,
        frequency_range=ParameterBounds(
            lower=sample_range.lower / length_range.upper,
            upper=sample_range.upper / length_range.lower,
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
    awg520050 = device_manager.add_awg("awg5200opt50-hostname", alias="awg520050")
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
    assert awg520050.opt_string == "50,HV"
    awg520050_constraints = awg520050.get_waveform_constraints(SignalSourceFunctionsAWG.SIN)
    min_smaple_50 = 300.0
    max_sample_50 = 5.0e9
    assert awg520050_constraints == ExtendedSourceDeviceConstants(
        amplitude_range=ParameterBounds(lower=25.0e-3, upper=750.0e-3),
        offset_range=ParameterBounds(lower=-2.0, upper=2.0),
        frequency_range=ParameterBounds(lower=min_smaple_50 / 3600.0, upper=max_sample_50 / 10.0),
        sample_rate_range=ParameterBounds(lower=min_smaple_50, upper=max_sample_50),
        square_duty_cycle_range=None,
        pulse_width_range=None,
        ramp_symmetry_range=None,
    )

    awg520050_constraints = awg520050.get_waveform_constraints(
        SignalSourceFunctionsAWG.SIN,
        output_path="DCHV",
    )
    min_smaple_50 = 300.0
    max_sample_50 = 5.0e9
    assert awg520050_constraints == ExtendedSourceDeviceConstants(
        amplitude_range=ParameterBounds(lower=10.0e-3, upper=5.0),
        offset_range=ParameterBounds(lower=-2.0, upper=2.0),
        frequency_range=ParameterBounds(lower=min_smaple_50 / 3600.0, upper=max_sample_50 / 10.0),
        sample_rate_range=ParameterBounds(lower=min_smaple_50, upper=max_sample_50),
        square_duty_cycle_range=None,
        pulse_width_range=None,
        ramp_symmetry_range=None,
    )

    awg520025 = device_manager.add_awg("awg5200opt25-hostname", alias="awg520025")
    assert awg520025.opt_string == "25,DC"
    awg520025_constraints = awg520025.get_waveform_constraints(
        waveform_length=500,
    )
    min_smaple_25 = 300.0
    max_sample_25 = 2.5e9
    assert awg520025_constraints == ExtendedSourceDeviceConstants(
        amplitude_range=ParameterBounds(lower=25.0e-3, upper=1.5),
        offset_range=ParameterBounds(lower=-2.0, upper=2.0),
        frequency_range=ParameterBounds(lower=min_smaple_25 / 500.0, upper=max_sample_25 / 500.0),
        sample_rate_range=ParameterBounds(lower=min_smaple_25, upper=max_sample_25),
        square_duty_cycle_range=None,
        pulse_width_range=None,
        ramp_symmetry_range=None,
    )
    error = "AWG Constraints require exclusively function or waveform_length."
    with pytest.raises(ValueError, match=error):
        awg520025.get_waveform_constraints()


def test_awg70k(device_manager: DeviceManager) -> None:  # pylint: disable=too-many-locals
    """Test the AWG70K driver.

    Args:
        device_manager: The DeviceManager object.
    """
    awg70ka150 = device_manager.add_awg("awg70001aopt150-hostname", alias="awg70ka150")
    awg70ka225 = device_manager.add_awg("awg70002aopt225-hostname", alias="awg70ka225")
    awg70ka216 = device_manager.add_awg("awg70002aopt216-hostname", alias="awg70ka216")
    awg70kb208 = device_manager.add_awg("awg70002bopt208-hostname", alias="awg70kb208")
    length_range = ParameterBounds(lower=10, upper=1000)
    min_smaple = 1.5e3
    awg_list = [awg70ka150, awg70ka225, awg70ka216, awg70kb208]
    output_path = None
    for awg in awg_list:
        option = awg.alias[-3:]
        assert awg.opt_string == option

        if not output_path:
            offset_range = ParameterBounds(lower=-0.0, upper=0.0)
            ampl_range = ParameterBounds(lower=0.125, upper=0.5)
        else:
            offset_range = ParameterBounds(lower=-0.4, upper=0.8)
            ampl_range = ParameterBounds(lower=31.0e-3, upper=1.2)

        constraints = awg.get_waveform_constraints(
            SignalSourceFunctionsAWG.RAMP,
            output_path=output_path,
        )

        output_path = "DCA"

        sample_range = ParameterBounds(lower=min_smaple, upper=int(option[1:3]) * 1.0e9)
        check_constraints(
            constraints,
            sample_range,
            ampl_range,
            offset_range,
            length_range,
        )

    awg70ka150.source_channel["SOURCE1"].set_offset(2.0)
    current_high = float(awg70ka150.query("SOURCE1:VOLTAGE:HIGH?"))
    current_low = float(awg70ka150.query("SOURCE1:VOLTAGE:LOW?"))
    current_amplitude = current_high - current_low
    offset = current_high - (current_amplitude / 2)
    assert offset == 2.0

    awg70ka150.source_channel["SOURCE1"].set_amplitude(4.0)
    current_high = float(awg70ka150.query("SOURCE1:VOLTAGE:HIGH?"))
    current_low = float(awg70ka150.query("SOURCE1:VOLTAGE:LOW?"))
    current_amplitude = current_high - current_low
    assert current_amplitude == 4.0

    awg70ka150.source_channel["SOURCE1"].set_frequency(500000000)
    current_frequency = awg70ka150.query("SOURCE1:FREQUENCY?")
    assert float(current_frequency) == 500000000


def test_awg7k(device_manager: DeviceManager) -> None:  # pylint: disable=too-many-locals
    """Test the AWG7K driver.

    Args:
        device_manager: The DeviceManager object.
    """
    awg7k01 = device_manager.add_awg("awg7051opt01-hostname", alias="awg7k01")
    awg7k06 = device_manager.add_awg("awg7102opt06-hostname", alias="awg7k06")
    awg7kb02 = device_manager.add_awg("awg7062bopt02-hostname", alias="awg7kb02")
    awg7kb01 = device_manager.add_awg("awg7121bopt01-hostname", alias="awg7kb01")
    awg7kc06 = device_manager.add_awg("awg7082copt01-hostname", alias="awg7kc01")
    awg7kc01 = device_manager.add_awg("awg7122copt06-hostname", alias="awg7kc06")
    length_range = ParameterBounds(lower=10, upper=1000)
    awg_list = [awg7k01, awg7k06, awg7kb02, awg7kb01, awg7kc06, awg7kc01]

    output_path = None
    for awg in awg_list:
        option = awg.alias[-2:]
        assert awg.opt_string == option

        sample_range = ParameterBounds(lower=10.0e6, upper=int(awg.model[4:6]) * 1.0e9)

        if option in {"02", "06"}:
            ampl_range = ParameterBounds(lower=0.5, upper=1.0)
            offset_range = ParameterBounds(lower=-0.0, upper=0.0)
        else:
            if not output_path:
                offset_range = ParameterBounds(lower=-0.5, upper=0.5)
            else:
                offset_range = ParameterBounds(lower=-0.0, upper=0.0)

            ampl_range = ParameterBounds(lower=50.0e-3, upper=2.0)

        constraints = awg.get_waveform_constraints(
            SignalSourceFunctionsAWG.TRIANGLE,
            output_path=output_path,
        )
        output_path = "1"
        check_constraints(
            constraints,
            sample_range,
            ampl_range,
            offset_range,
            length_range,
        )


def test_awg5k(device_manager: DeviceManager) -> None:
    """Test the AWG5K driver.

    Args:
        device_manager: The DeviceManager object.
    """
    awg5k = device_manager.add_awg("awg5012-hostname", alias="awg5k")
    awg5kb = device_manager.add_awg("awg5002b-hostname", alias="awg5kb")
    awg5kc = device_manager.add_awg("awg5012c-hostname", alias="awg5kc")
    length_range = ParameterBounds(lower=960, upper=960)
    awg_list = [awg5k, awg5kb, awg5kc]

    ampl_range = ParameterBounds(lower=20.0e-3, upper=4.5)
    output_path = None

    for awg in awg_list:
        sample_range = ParameterBounds(lower=10.0e6, upper=int(awg.model[5]) * 600.0e6 + 600.0e6)

        constraints = awg.get_waveform_constraints(
            SignalSourceFunctionsAWG.CLOCK, output_path=output_path
        )
        if not output_path:
            offset_range = ParameterBounds(lower=-2.25, upper=2.25)
        else:
            offset_range = ParameterBounds(lower=-0.0, upper=0.0)

        output_path = "1"
        check_constraints(
            constraints,
            sample_range,
            ampl_range,
            offset_range,
            length_range,
        )
