"""An example showing how to generate a function using an AFG and AWG."""

from tm_devices import DeviceManager
from tm_devices.drivers import AFG3K, AWG5K
from tm_devices.helpers import SignalGeneratorFunctionsAFG, SignalGeneratorFunctionsAWG

with DeviceManager(verbose=True) as dm:
    # Create a connection to the AFG and indicate that it is an AFG3K for type hinting
    afg3k: AFG3K = dm.add_afg("192.168.0.1")  # pyright: ignore[reportAssignmentType]

    # Create a connection to the AWG and indicate that it is an AWG5K for type hinting
    awg5k: AWG5K = dm.add_awg("192.168.0.2")  # pyright: ignore[reportAssignmentType]

    # Generate a RAMP waveform on SOURCE1 of the AFG3K with the provided properties.
    afg3k.generate_function(
        function=SignalGeneratorFunctionsAFG.RAMP,
        channel="SOURCE1",
        frequency=10e5,
        amplitude=0.5,
        offset=0,
        symmetry=50.0,
    )

    # Generate a SIN waveform on all channels of the AWG5K with the provided properties.
    awg5k.generate_function(
        function=SignalGeneratorFunctionsAWG.SIN,
        channel="all",
        frequency=10e5,
        amplitude=0.5,
        offset=0,
    )
