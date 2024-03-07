"""An example showing how to generate a function using an AFG and AWG."""
from tm_devices import DeviceManager
from tm_devices.helpers import SignalGeneratorFunctionsAFG, SignalGeneratorFunctionsAWG

with DeviceManager(verbose=True) as dm:
    afg = dm.add_afg("192.168.0.1")
    awg = dm.add_awg("192.168.0.2")

    # Generate a RAMP waveform on SOURCE1 of the AFG with the provided properties.
    afg.generate_function(
        function=SignalGeneratorFunctionsAFG.RAMP,
        channel="SOURCE1",
        frequency=10e5,
        amplitude=0.5,
        offset=0,
        symmetry=50.0,
    )

    # Generate a SIN waveform on all channels of the AWG with the provided properties.
    awg.generate_function(
        function=SignalGeneratorFunctionsAWG.SIN,
        channel="all",
        frequency=10e5,
        amplitude=0.5,
        offset=0,
    )
