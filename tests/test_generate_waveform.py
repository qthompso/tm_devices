# pyright: reportPrivateUsage=none
"""Test generate_waveform."""
import pytest

from tm_devices import DeviceManager


def test_awg5200_gen_waveform(device_manager: DeviceManager, capsys: pytest.CaptureFixture[str]) -> None:
    """Test the AWG5200 driver.

    Args:
        device_manager: The DeviceManager object.
        capsys: The captured stdout and stderr.
    """
    awg520050 = device_manager.add_awg("awg520050-hostname", alias="awg520050")

    awg520050.generate_waveform(
        10e3, awg520050.source_device_constants.functions.SIN, 1., 0.2, channel="SOURCE1"
    )
    assert 'SOURCE1:FREQUENCY?' not in capsys.readouterr().out
    assert 'CLOCK:SRATE' in capsys.readouterr().out
    source1_srate = awg520050.query("CLOCK:SRATE?")
    assert float(source1_srate) == 36000000
    source1_waveform_file = awg520050.query("SOURCE1:WAVEFORM?")
    assert source1_waveform_file == '"*Sine3600"'
    source1_amplitude = awg520050.query("SOURCE1:VOLTAGE:AMPLITUDE?")
    assert float(source1_amplitude) == 1.0
    source1_offset = awg520050.query("SOURCE1:VOLTAGE:OFFSET?")
    assert float(source1_offset) == 0.2
    output1_state = awg520050.query("OUTPUT1:STATE?")
    assert int(output1_state) == 1

    # AWG5200 doesn't handle burst greater than 0.
    awg520050.generate_waveform(
        10e3, awg520050.source_device_constants.functions.DC, 1.0, 0.0, channel="SOURCE1", burst=1
    )
    source1_waveform_file = awg520050.query("SOURCE1:WAVEFORM?")
    assert source1_waveform_file != '"*DC"'


def test_awg7k_gen_waveform(device_manager: DeviceManager, capsys: pytest.CaptureFixture[str]) -> None:
    awg7k01 = device_manager.add_awg("awg7k01-hostname", alias="awg7k01")
    awg7k06 = device_manager.add_awg("awg7k06-hostname", alias="awg7k06")

    default_offset = 0
    awg7k06.channel["SOURCE1"].set_offset(default_offset)
    awg7k06.generate_waveform(
        10e4, awg7k06.source_device_constants.functions.CLOCK, 1.0, 0.2, channel="SOURCE1"
    )
    source1_frequency = awg7k06.query("SOURCE1:FREQUENCY?")
    assert float(source1_frequency) == 96000000
    source1_waveform_file = awg7k06.query("SOURCE1:WAVEFORM?")
    assert source1_waveform_file == '"*Clock960"'
    source1_amplitude = awg7k06.query("SOURCE1:VOLTAGE:AMPLITUDE?")
    assert float(source1_amplitude) == 1.0
    # AWG option 6 should not set the offset.
    source1_offset = awg7k06.query("SOURCE1:VOLTAGE:OFFSET?")
    assert float(source1_offset) == default_offset
    output1_state = awg7k06.query("OUTPUT1:STATE?")
    assert int(output1_state) == 1

    # AWG option 1 should set offset.
    awg7k01.generate_waveform(
        10e3, awg7k01.source_device_constants.functions.SIN, 1.2, 0.2, channel="SOURCE1"
    )
    source1_offset = awg7k01.query("SOURCE1:VOLTAGE:OFFSET?")
    assert float(source1_offset) == 0.2


def test_awg5k_gen_waveform(device_manager: DeviceManager, capsys: pytest.CaptureFixture[str]) -> None:
    awg5k = device_manager.add_awg("awg5k-hostname", alias="awg5k")
    # Sine
    awg5k.generate_waveform(
        10e3, awg5k.source_device_constants.functions.SIN, 2.0, 2.0, channel="SOURCE1"
    )
    source1_frequency = awg5k.query("SOURCE1:FREQUENCY?")
    assert float(source1_frequency) == 36000000
    source1_waveform_file = awg5k.query("SOURCE1:WAVEFORM?")
    assert source1_waveform_file == '"*Sine3600"'
    source1_amplitude = awg5k.query("SOURCE1:VOLTAGE:AMPLITUDE?")
    assert float(source1_amplitude) == 2.0
    source1_offset = awg5k.query("SOURCE1:VOLTAGE:OFFSET?")
    assert float(source1_offset) == 2.0
    output1_state = awg5k.query("OUTPUT1:STATE?")
    assert int(output1_state) == 1

    # Clock
    awg5k.generate_waveform(
        10e4, awg5k.source_device_constants.functions.CLOCK, 1.0, 0.0, channel="SOURCE1"
    )
    source1_frequency = awg5k.query("SOURCE1:FREQUENCY?")
    assert float(source1_frequency) == 96000000
    source1_waveform_file = awg5k.query("SOURCE1:WAVEFORM?")
    assert source1_waveform_file == '"*Clock960"'

    # Iterate through pre-made signal record length
    awg5k.generate_waveform(
        10e7, awg5k.source_device_constants.functions.SQUARE, 1.0, 0.0, channel="SOURCE1"
    )
    source1_frequency = awg5k.query("SOURCE1:FREQUENCY?")
    assert float(source1_frequency) == 1000000000
    source1_waveform_file = awg5k.query("SOURCE1:WAVEFORM?")
    assert source1_waveform_file == '"*Square10"'

    # Burst > 0
    awg5k.generate_waveform(
        10e3, awg5k.source_device_constants.functions.SIN, 1.0, 0.0, channel="SOURCE1", burst=100
    )
    source1_frequency = awg5k.query("SOURCE1:FREQUENCY?")
    assert float(source1_frequency) == 36000000
    source1_waveform_file = awg5k.query("SEQUENCE:ELEMENT1:WAVEFORM1?")
    assert source1_waveform_file == '"*Sine3600"'
    source1_loop_count = awg5k.query("SEQUENCE:ELEMENT1:LOOP:COUNT?")
    assert float(source1_loop_count) == 100

    # Invalid burst
    with pytest.raises(ValueError):
        awg5k.generate_waveform(
            10e3, awg5k.source_device_constants.functions.SIN, 1.0, 0.0, channel="SOURCE1", burst=-1
        )
