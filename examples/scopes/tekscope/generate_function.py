"""An example showing how to generate a function using the scope's internal AFG.

This is equivalent to the signal in generate_internal_afg_signal.py.
"""
from tm_devices import DeviceManager
from tm_devices.drivers import MSO5
from tm_devices.helpers import SignalGeneratorFunctionsIAFG

with DeviceManager(verbose=True) as dm:
    # Create a connection to the scope and indicate that it is a MSO5 scope for type hinting
    scope: MSO5 = dm.add_scope("192.168.1.102")  # pyright: ignore[reportAssignmentType]

    # Generate a SQUARE waveform with the provided properties.
    scope.generate_function(
        frequency=10e6,
        offset=0.2,
        amplitude=0.5,
        duty_cycle=50,
        function=SignalGeneratorFunctionsIAFG.SQUARE,
        termination="FIFTY",
    )
    scope.commands.ch[1].scale.write(0.5, verify=True)  # set and check vertical scale on CH1
    scope.commands.acquire.stopafter.write("SEQUENCE")  # perform a single sequence
