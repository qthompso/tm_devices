"""An example showing the use of waveform constraints for an AWG."""
from tm_devices import DeviceManager
from tm_devices.drivers import AWG5K
from tm_devices.helpers import SignalGeneratorFunctionsAWG

# The desired frequency.
DESIRED_FREQUENCY = 10e3

# The desired function to generate.
DESIRED_FUNCTION = SignalGeneratorFunctionsAWG.SIN

with DeviceManager(verbose=True) as dm:
    # Create a connection to the scope and indicate that it is an AWG5K for type hinting.
    awg5k: AWG5K = dm.add_awg("10.233.71.102")  # pyright: ignore[reportAssignmentType]

    # Get the device constraints for generating the desired function on an AWG5K.
    awg5k_constraints_function = awg5k.get_waveform_constraints(function=DESIRED_FUNCTION)

    # Get the frequency constraints.
    frequency_range = awg5k_constraints_function.frequency_range

    frequency_error_message = (
        f"The desired frequency ({DESIRED_FREQUENCY}) is not within the device's frequency "
        f"range for generating a {DESIRED_FUNCTION.name} waveform. "
        "Frequency must be in the range of "
        f"[{frequency_range.lower}, {frequency_range.upper}]."
    )
    # Raise an error if the desired frequency is not within the frequency constraints.
    if not frequency_range.lower <= DESIRED_FREQUENCY <= frequency_range.upper:
        raise ValueError(frequency_error_message)
