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
        10e3, awg520050.source_device_constants.functions.SIN, 1.0, 0.0, channel="SOURCE1"
    )
    awg520050.generate_waveform(
        10e3, awg520050.source_device_constants.functions.DC, 1.0, 0.0, channel="SOURCE1", burst=1
    )


def test_awg7k_gen_waveform(device_manager: DeviceManager, capsys: pytest.CaptureFixture[str]) -> None:
    awg7k01 = device_manager.add_awg("awg7k01-hostname", alias="awg7k01")
    awg7k06 = device_manager.add_awg("awg7k06-hostname", alias="awg7k06")
    awg7k01.generate_waveform(
        10e3, awg7k01.source_device_constants.functions.SIN, 1.0, 0.0, channel="SOURCE1"
    )
    awg7k06.generate_waveform(
        10e3, awg7k01.source_device_constants.functions.SIN, 1.0, 0.0, channel="SOURCE1"
    )


def test_awg5k_gen_waveform(device_manager: DeviceManager, capsys: pytest.CaptureFixture[str]) -> None:
    awg5k = device_manager.add_awg("awg5k-hostname", alias="awg5k")
    awg5k.generate_waveform(
        10e3, awg5k.source_device_constants.functions.SIN, 1.0, 0.0, channel="SOURCE1"
    )
    awg5k.generate_waveform(
        10e4, awg5k.source_device_constants.functions.CLOCK, 1.0, 0.0, channel="SOURCE1"
    )
    # Iterate through pre-made signal record length
    awg5k.generate_waveform(
        10e7, awg5k.source_device_constants.functions.SQUARE, 1.0, 0.0, channel="SOURCE1"
    )
    # Burst > 0
    awg5k.generate_waveform(
        10e3, awg5k.source_device_constants.functions.SIN, 1.0, 0.0, channel="SOURCE1", burst=2
    )
    # Invalid burst
    with pytest.raises(ValueError):
        awg5k.generate_waveform(
            10e3, awg5k.source_device_constants.functions.SIN, 1.0, 0.0, channel="SOURCE1", burst=-1
        )
