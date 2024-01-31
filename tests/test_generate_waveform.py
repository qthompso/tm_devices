# pyright: reportPrivateUsage=none
"""Test generate_function."""
from typing import cast

import pytest

from tm_devices import DeviceManager
from tm_devices.drivers import AWG5K, AWG7K, AWG70KA, AWG5200, MSO5
from tm_devices.helpers import SignalSourceOutputPaths5200, SignalSourceOutputPathsNon5200


def test_awg5200_gen_waveform(device_manager: DeviceManager) -> None:
    """Test generate waveform for AWG5200.

    Args:
        device_manager: The DeviceManager object.
    """
    awg520050 = cast(AWG5200, device_manager.add_awg("awg5200opt50-hostname", alias="awg520050a"))

    awg520050.generate_function(
        10e3, awg520050.source_device_constants.functions.SIN, 1.0, 0.2, channel="SOURCE1"
    )
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
    awg520050.generate_function(
        10e3, awg520050.source_device_constants.functions.DC, 1.0, 0.0, channel="SOURCE1", burst=1
    )
    source1_waveform_file = awg520050.query("SOURCE1:WAVEFORM?")
    assert source1_waveform_file != '"*DC"'

    assert awg520050.expect_esr(0)[0]
    assert awg520050.get_eventlog_status() == (True, '0,"No error"')

    # Invalid burst
    with pytest.raises(ValueError, match="-1 is an invalid burst value. Burst count must be > 0."):
        awg520050.generate_function(
            10e3,
            awg520050.source_device_constants.functions.SIN,
            1.0,
            0.0,
            channel="SOURCE1",
            burst=-1,
        )

    # Frequency is too high to produce CLOCK function on this AWG.
    with pytest.raises(
        ValueError,
        match="Unable to generate Clock waveform with provided frequency of 10000000000.0 Hz.",
    ):
        awg520050.generate_function(
            10e9, awg520050.source_device_constants.functions.CLOCK, 1.0, 0.0, channel="SOURCE1"
        )

    # Invalid output path.
    with pytest.raises(ValueError, match="DIR is an invalid output signal path for AWG5204."):
        awg520050.generate_function(
            10e3,
            awg520050.source_device_constants.functions.SIN,
            1.2,
            0.2,
            channel="SOURCE1",
            output_path=SignalSourceOutputPathsNon5200.DIR,
        )

    awg520025 = cast(AWG5200, device_manager.add_awg("awg5200opt25-hostname", alias="awg520050"))
    seq_error = "A sequencing license is required to generate a burst waveform."
    with pytest.raises(AssertionError, match=seq_error):
        awg520025.generate_function(
            10e3,
            awg520025.source_device_constants.functions.DC,
            1.0,
            0.0,
            channel="SOURCE1",
            burst=1,
        )


def test_awg70k_gen_waveform(
    device_manager: DeviceManager, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test generate waveform for AWG70k.

    Args:
        device_manager: The DeviceManager object.
        capsys: The captured stdout and stderr.
    """
    awg70ka150 = cast(
        AWG70KA, device_manager.add_awg("awg70001aopt150-hostname", alias="awg70ka150")
    )
    awg70ka150.generate_function(
        frequency=10e4,
        function=awg70ka150.source_device_constants.functions.CLOCK,
        amplitude=1.0,
        offset=0.1,
        channel="SOURCE1",
        output_path=awg70ka150.output_signal_path.DCA,
    )
    source1_frequency = awg70ka150.query("SOURCE1:FREQUENCY?")
    assert float(source1_frequency) == 96000000
    source1_waveform_file = awg70ka150.query("SOURCE1:WAVEFORM?")
    assert source1_waveform_file == '"*Clock960"'
    source1_amplitude = awg70ka150.query("SOURCE1:VOLTAGE:AMPLITUDE?")
    assert float(source1_amplitude) == 1.0
    source1_offset = awg70ka150.query("SOURCE1:VOLTAGE:OFFSET?")
    assert float(source1_offset) == 0.1
    output1_state = awg70ka150.query("OUTPUT1:STATE?")
    assert int(output1_state) == 1

    assert awg70ka150.expect_esr(0)[0]
    assert awg70ka150.get_eventlog_status() == (True, '0,"No error"')
    assert "MMEMORY:OPEN:SASSET" not in capsys.readouterr().out

    # call generate_function with only *DC in the waveform list.
    awg70ka225 = cast(
        AWG70KA, device_manager.add_awg("awg70002aopt225-hostname", alias="awg70ka225")
    )
    _ = capsys.readouterr().out  # throw away stdout
    awg70ka225.generate_function(
        frequency=10e4,
        function=awg70ka150.source_device_constants.functions.CLOCK,
        amplitude=1.0,
        offset=0.1,
        channel="SOURCE1",
        output_path=awg70ka150.output_signal_path.DCA,
    )
    assert "MMEMORY:OPEN:SASSET" in capsys.readouterr().out


def test_awg7k_gen_waveform(device_manager: DeviceManager) -> None:
    """Test generate waveform for AWG7k.

    Args:
        device_manager: The DeviceManager object.
    """
    awg7k01 = cast(AWG7K, device_manager.add_awg("awg7051opt01-hostname", alias="awg7k01"))
    awg7k06 = cast(AWG7K, device_manager.add_awg("awg7102opt06-hostname", alias="awg7k06"))

    error_match = (
        "The offset can only be set on AWG7102 without an 02 or 06 option and with an output "
        "signal path of DCA \(AWGCONTROL:DOUTPUT1:STATE set to 0\)."  # noqa: W605  # pylint: disable=anomalous-backslash-in-string  # pyright: ignore [reportInvalidStringEscapeSequence]
    )
    with pytest.raises(ValueError, match=error_match):
        awg7k06.source_channel["SOURCE1"].set_offset(0.2)
    awg7k06.generate_function(
        10e4, awg7k06.source_device_constants.functions.CLOCK, 1.0, 0.0, channel="SOURCE1"
    )
    source1_frequency = awg7k06.query("SOURCE1:FREQUENCY?")
    assert float(source1_frequency) == 96000000
    source1_waveform_file = awg7k06.query("SOURCE1:WAVEFORM?")
    assert source1_waveform_file == '"*Clock960"'
    source1_amplitude = awg7k06.query("SOURCE1:VOLTAGE:AMPLITUDE?")
    assert float(source1_amplitude) == 1.0
    source1_offset = awg7k06.query("SOURCE1:VOLTAGE:OFFSET?")
    assert not float(source1_offset)
    output1_state = awg7k06.query("OUTPUT1:STATE?")
    assert int(output1_state) == 1

    assert awg7k06.expect_esr(0)[0]
    assert awg7k06.get_eventlog_status() == (True, '0,"No error"')

    # AWG7k with option 1 should set offset.
    awg7k01.generate_function(
        10e3, awg7k01.source_device_constants.functions.SIN, 1.2, 0.2, channel="SOURCE1"
    )
    source1_offset = awg7k01.query("SOURCE1:VOLTAGE:OFFSET?")
    assert float(source1_offset) == 0.2

    # AWG7k with option 1 should not be able to set offset with DIR output signal path.
    error_match = (
        "The offset can only be set on AWG7051 without an 02 or 06 option and with an output "
        "signal path of DCA \(AWGCONTROL:DOUTPUT1:STATE set to 0\)."  # noqa: W605  # pylint: disable=anomalous-backslash-in-string  # pyright: ignore [reportInvalidStringEscapeSequence]
    )
    with pytest.raises(ValueError, match=error_match):
        awg7k01.generate_function(
            10e3,
            awg7k01.source_device_constants.functions.SIN,
            1.2,
            0.2,
            channel="SOURCE1",
            output_path=awg7k01.output_signal_path.DIR,
        )

    # DCHB is not a valid output signal path for AWG7k's.
    with pytest.raises(ValueError, match="DCHB is an invalid output signal path for AWG7051."):
        awg7k01.generate_function(
            10e3,
            awg7k01.source_device_constants.functions.SIN,
            1.2,
            0.2,
            channel="SOURCE1",
            output_path=SignalSourceOutputPaths5200.DCHB,
        )

    assert awg7k01.expect_esr(0)[0]
    assert awg7k01.get_eventlog_status() == (True, '0,"No error"')

    # Clock
    awg7k01.generate_function(
        10e4,
        awg7k01.source_device_constants.functions.CLOCK,
        1.0,
        0.0,
        channel="SOURCE1",
        output_path=awg7k01.output_signal_path.DCA,
    )
    source1_frequency = awg7k01.query("SOURCE1:FREQUENCY?")
    assert float(source1_frequency) == 96000000
    source1_waveform_file = awg7k01.query("SOURCE1:WAVEFORM?")
    assert source1_waveform_file == '"*Clock960"'

    # Iterate through pre-made signal record length
    awg7k01.generate_function(
        10e7, awg7k01.source_device_constants.functions.RAMP, 1.0, 0.0, channel="SOURCE1"
    )
    source1_frequency = awg7k01.query("SOURCE1:FREQUENCY?")
    assert float(source1_frequency) == 1000000000
    source1_waveform_file = awg7k01.query("SOURCE1:WAVEFORM?")
    assert source1_waveform_file == '"*Triangle10"'

    # Burst > 0
    awg7k01.generate_function(
        10e3, awg7k01.source_device_constants.functions.SIN, 1.0, 0.0, channel="SOURCE1", burst=100
    )
    source1_frequency = awg7k01.query("SOURCE1:FREQUENCY?")
    assert float(source1_frequency) == 36000000
    source1_waveform_file = awg7k01.query("SEQUENCE:ELEMENT1:WAVEFORM1?")
    assert source1_waveform_file == '"*Sine3600"'
    source1_loop_count = awg7k01.query("SEQUENCE:ELEMENT1:LOOP:COUNT?")
    assert float(source1_loop_count) == 100

    assert awg7k01.expect_esr(0)[0]
    assert awg7k01.get_eventlog_status() == (True, '0,"No error"')

    # Invalid burst
    with pytest.raises(ValueError, match="-1 is an invalid burst value. Burst count must be > 0."):
        awg7k01.generate_function(
            10e3,
            awg7k01.source_device_constants.functions.SIN,
            1.0,
            0.0,
            channel="SOURCE1",
            burst=-1,
        )


def test_awg5k_gen_waveform(device_manager: DeviceManager) -> None:
    """Test generate waveform for AWG5k.

    Args:
        device_manager: The DeviceManager object.
    """
    awg5k = cast(AWG5K, device_manager.add_awg("AWG5012-hostname", alias="awg5k"))
    # Sine
    awg5k.generate_function(
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

    # Cannot set offset with DIR output path.
    offset_error = (
        "The offset can only be set on AWG5012 with an output signal path of DCA "
        "\(AWGCONTROL:DOUTPUT1:STATE set to 0\)."  # noqa: W605  # pylint: disable=anomalous-backslash-in-string  # pyright: ignore [reportInvalidStringEscapeSequence]
    )
    with pytest.raises(ValueError, match=offset_error):
        awg5k.generate_function(
            10e3,
            awg5k.source_device_constants.functions.SIN,
            2.0,
            2.0,
            channel="SOURCE1",
            output_path=awg5k.output_signal_path.DIR,
        )

    # Even with an output path of DIR, no error is raised because no offset is requested (0).
    awg5k.generate_function(
        10e3,
        awg5k.source_device_constants.functions.SIN,
        2.0,
        0,
        channel="SOURCE1",
        output_path=awg5k.output_signal_path.DIR,
    )


def test_afg3k_gen_waveform(
    device_manager: DeviceManager, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test generate waveform for AWG3k.

    Args:
        device_manager: The DeviceManager object.
        capsys: The captured stdout and stderr.
    """
    afg3kc = device_manager.add_afg(
        "afg3252c-hostname", alias="afg3kc", connection_type="SOCKET", port=10001
    )
    afg3kc.generate_function(25e6, afg3kc.source_device_constants.functions.PULSE, 1.0, 0.0, "all")
    assert "SOURCE1:PHASE:INITIATE" in capsys.readouterr().out

    afg3kc.generate_function(
        25e6,
        afg3kc.source_device_constants.functions.DC,
        1.0,
        0.0,
        "SOURCE1",
        termination="HIGHZ",
    )
    assert "TRIGGER:SEQUENCE:SOURCE" not in capsys.readouterr().out
    assert "SOURCE1:BURST:STATE" not in capsys.readouterr().out
    assert "SOURCE1:BURST:MODE" not in capsys.readouterr().out
    assert "SOURCE1:BURST:NCYCLES" not in capsys.readouterr().out

    afg3kc.generate_function(
        25e6,
        afg3kc.source_device_constants.functions.SIN,
        1.0,
        0.0,
        "SOURCE1",
        burst=1,
        termination="HIGHZ",
    )
    assert "OUTPUT1:IMPEDANCE INFINITY" in capsys.readouterr().out
    source1_frequency = afg3kc.query("SOURCE1:FREQUENCY:FIXED?")
    assert float(source1_frequency) == 25e6
    source1_offset = afg3kc.query("SOURCE1:VOLTAGE:OFFSET?")
    assert not float(source1_offset)
    assert "SOURCE1:PULSE:DCYCLE" not in capsys.readouterr().out
    assert "SOURCE1:FUNCTION:RAMP:SYMMETRY" not in capsys.readouterr().out
    source1_function = afg3kc.query("SOURCE1:FUNCTION?")
    assert source1_function == "SIN"
    source1_amplitude = afg3kc.query("SOURCE1:VOLTAGE:AMPLITUDE?")
    assert float(source1_amplitude) == 1.0
    trigger_sequence_source = afg3kc.query("TRIGGER:SEQUENCE:SOURCE?")
    assert trigger_sequence_source == "EXT"
    source1_burst_state = afg3kc.query("SOURCE1:BURST:STATE?")
    assert int(source1_burst_state) == 1
    source1_burst_mode = afg3kc.query("SOURCE1:BURST:MODE?")
    assert source1_burst_mode == "TRIG"
    source1_burst_ncycles = afg3kc.query("SOURCE1:BURST:NCYCLES?")
    assert int(source1_burst_ncycles) == 1
    output1_state = afg3kc.query("OUTPUT1:STATE?")
    assert int(output1_state) == 1

    afg3kc.generate_function(
        25e6,
        afg3kc.source_device_constants.functions.RAMP,
        1.0,
        0.0,
        "SOURCE1",
        burst=1,
        termination="FIFTY",
    )
    impedance = afg3kc.query("OUTPUT1:IMPEDANCE?")
    assert float(impedance) == 50
    ramp_symmetry = afg3kc.query("SOURCE1:FUNCTION:RAMP:SYMMETRY?")
    assert float(ramp_symmetry) == 100
    source1_function = afg3kc.query("SOURCE1:FUNCTION?")
    assert source1_function == "RAMP"

    afg3kc.generate_function(
        25e6,
        afg3kc.source_device_constants.functions.PULSE,
        1.0,
        0.0,
        "SOURCE1",
        termination="FIFTY",
    )
    pulse_dcycle = afg3kc.query("SOURCE1:PULSE:DCYCLE?")
    assert float(pulse_dcycle) == 50

    assert afg3kc.expect_esr(0)[0]
    assert afg3kc.get_eventlog_status() == (True, '0,"No error"')


def test_internal_afg_gen_waveform(
    device_manager: DeviceManager, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test generate waveform for IAFG in tekscopes.

    Args:
        device_manager: The DeviceManager object.
        capsys: The captured stdout and stderr.
    """
    scope: MSO5 = cast(
        MSO5, device_manager.add_scope("MSO56-SERIAL1", alias="mso56", connection_type="USB")
    )

    scope.generate_function(10e3, scope.source_device_constants.functions.SIN, 0.5, 0.0)
    assert "AFG:OUTPUT:MODE" not in capsys.readouterr().out
    assert "AFG:BURST:CCOUNT" not in capsys.readouterr().out
    frequency = scope.query("AFG:FREQUENCY?")
    assert float(frequency) == 10e3
    offset = scope.query("AFG:OFFSET?")
    assert not float(offset)
    square_duty = scope.query("AFG:SQUARE:DUTY?")
    assert float(square_duty) == 50
    assert "AFG:RAMP:SYMMETRY" not in capsys.readouterr().out
    function = scope.query("AFG:FUNCTION?")
    assert function == "SINE"
    impedance = scope.query("AFG:OUTPUT:LOAD:IMPEDANCE?")
    assert impedance == "FIFTY"
    amplitude = scope.query("AFG:AMPLITUDE?")
    assert float(amplitude) == 0.5
    output_state = scope.query("AFG:OUTPUT:STATE?")
    assert int(output_state) == 1
    assert "AFG:BURST:TRIGGER" not in capsys.readouterr().out

    scope.generate_function(
        10e3, scope.source_device_constants.functions.SIN, 0.5, 0.0, termination="HIGHZ"
    )
    impedance = scope.query("AFG:OUTPUT:LOAD:IMPEDANCE?")
    assert impedance == "HIGHZ"

    scope.generate_function(10e3, scope.source_device_constants.functions.RAMP, 0.5, 0.0, burst=1)
    output_mode = scope.query("AFG:OUTPUT:MODE?")
    assert output_mode == "BURST"
    burst_ccount = scope.query("AFG:BURST:CCOUNT?")
    assert int(burst_ccount) == 1
    ramp_symmetry = scope.query("AFG:RAMP:SYMMETRY?")
    assert float(ramp_symmetry) == 50
    assert "AFG:BURST:TRIGGER" in capsys.readouterr().out
    assert scope.expect_esr(0)[0]
    assert scope.get_eventlog_status() == (True, '0,"No events to report - queue empty"')

    with pytest.raises(
        TypeError,
        match="Generate Waveform does not accept functions as non Enums. "
        "Please use 'source_device_constants.functions'.",
    ):
        scope.generate_function(
            25e6,
            scope.source_device_constants.functions.PULSE.value,  # type: ignore[reportArgumentType]
            1.0,
            0.0,
            "all",
        )
