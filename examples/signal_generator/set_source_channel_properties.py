"""An example showing the use of the source channel."""
from tm_devices import DeviceManager
from tm_devices.drivers import AWG5K

with DeviceManager(verbose=True) as dm:
    # Create a connection to the scope and indicate that it is an AWG5K for type hinting.
    awg5k: AWG5K = dm.add_awg("10.233.71.102")  # pyright: ignore[reportAssignmentType]

    # Set the offset of SOURCE1 on the AWG5K
    awg5k.source_channel["SOURCE1"].set_offset(0.5)

    # Set the frequency of SOURCE1 on the AWG5K
    awg5k.source_channel["SOURCE1"].set_frequency(10e3)
