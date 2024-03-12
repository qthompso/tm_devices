# Signal Generation

An overview of this Signal generation in this package, along with Tektronix signal generators.

______________________________________________________________________

## Function Generation

A function is a limited set of common waveforms that are (usually) provided by default through the instrument.
This means that the output parameters like waveform length, sample rate and cycle frequency are
abstracted away in order to provide signals which easy to quantify and manipulate.

Arbitrary Function Generators (AFGs) utilize a phase increment process and a data lookup table to provide variable frequencies,
called DDS. The phase increment calculated is dependent on the waveform length and frequency requested. This has
a side effect where the phase increment can be larger than one index in the lookup table. Functions bypass this
issue by being simplistic enough that waveform length reduction doesn't have a detrimental effect on the end output.

Arbitrary Waveform Generators (AWGs) enforce one cycle per sample, allowing the output to be the same shape regardless of clock rate.
This does not exclude the use of functions, regardless of the name difference. Functionally, AWGs are usually more
constrained in amplitude and offset.

______________________________________________________________________

### Class Structure

Each Source class (AFG, AWG) and Tekscope (If the AFG license is installed) will contain a dictionary of source channel classes,
which are defined on first access. Each of these source channel classes represents an output channel on the source, or in the case
of Tekscope, the IAFG.

These channels contain methods and properties which pertain to PI commands that apply changes to one output channel.
For example: the afg.source_channel\["SOURCE1"\].set_amplitude() call will change the amplitude only for source output 1.

______________________________________________________________________

### Class Methods

The `SignalGenerator` class is responsible for most waveform generators, including `AWG` and `AFG`.
Similarily, `Tekscope` is responsible for AFGs internal to the scopes themselves, commonly referred to as
IAFGs. Both classes inheret `SignalGeneratorMixin` for a list of methods which share functionality throughout
all signal sources. These public properties, functions and methods include:

Each function exclude most attempts at validation, as the end developer can change aspects outside its purview.
There are several distinct instances where this can cause unwanted behavior or errors depending on source and what
state it was in before it is used.

`source_device_constants` is a property which holds information about what functions
and memory sizes are allowed.

`generate_function` is a method which allows for the user to request a function from
any source channel provided an amplitude, frequency and offset is supplied. Other key features
include the ability to manipulate specific aspects of certain functions, like symmetry for ramp
waveforms and duty cycle for pulse functions. The termination of the IAFG and any AFG can be
specified, along with customizable polarity specifically for AFGs. Finally, AWGs can have their signal output path
changed, value dependent on specific model types.

The `setup_burst` method places the source into a state where it can allow for waveforms to be generated a set number
of times. All parameters passed into the method are functionaly identical to generate_function, besides burst_count,
which specifies how many cycles of the waveform are to be generated.

`generate_burst` simply writes a trigger to the source, to initiate the burst of waveforms.

`get_waveform_constraints` will return a list of constraints that the signal generators must be within to be generated.
These constraints can be used before generating a function to make sure that the parameters you will be supplying
are not outside the bounds. The method requires no input, however, different aspects may need to be provided to
get a more accurate representation of what can actually be generated, as the lowest range will be chosen otherwise.
Specifying the function can help determine what frequencies can be generated on all sources. AWGs signal path effects
the range of the offset and amplitude. Higher frequencies on the AFG31K will lower the upper bound of the amplitude,
the same goes for what impedance is expected to be set.

`set_waveform_properties` is functionally identical to generate_function, but does not turn the channel
off or on, nor will it stop or start an AWG.

# Signal Generators

______________________________________________________________________

## Internal Arbitrary Function Generator

Requesting function generation will turn off the channel provided. The frequency, function,
amplitude, impedance and offset are set. If the function is a square wave, the duty cycle is used
to set how long the pulses are. Symmetry decides what direction the skews towards if the ramp function
is provided. After all parameters are set, the channel is turned back on.

Setting up bursts of the IAFG is a simple process, which simply involves setting it to burst mode and
loading in a specified number of bursts.

#### Stipulations:

Internal arbitrary signal generators are only accessable if the oscilloscope has the AFG license installed.
IAFGs contain no waveform list, editable memory or user defined waveforms. Arbitrary waveforms
must be loaded from the hard drive.

AFGs have access to the following functions:
SIN, SQUARE, RAMP, PULSE, PRNOISE, DC, SINC, GAUSSIAN, LORENTZ, ERISE, EDECAY, HAVERSINE, CARDIAC, ARBITRARY

### MSO2, MSO4, MSO4B, MSO5, MSO5LP, MSO6, MSO6B, LPD6

#### Constraints:

The amplitude and frequency range for the Internal AFG varies dependant on the function set.
All functions have the same lower bound, 20 mV and 100 mHz. Similarily, all offset ranges stay consistent,
plus or minus 2.5 volts. The higher bound for functions, however, consist of the following:

|           | Sin             | Square<br/>Pulse<br/>Arbitrary | Ramp<br/>Triangle | Sinc           | Gaussian<br/>Haversine | Lorentz        | Cardiac          | Arbitrary       |
| --------- | --------------- | ------------------------------ | ----------------- | -------------- | ---------------------- | -------------- | ---------------- | --------------- |
| Frequency | 100mHz to 50MHz | 100mHz to 25MHz                | 100mHz to 500kHz  | 100mHz to 2MHz | 100mHz to 5MHz         | 100mHz to 5MHz | 100mHz to 500kHz | 100mHz to 25MHz |
| Amplitude | 20mV to 5V      | 20mV to 5V                     | 20mV to 5V        | 20mV to 3V     | 20mV to 5V             | 20mV to 2.4V   | 20mV to 5V       | 20mV to 5V      |
| Offset    | -2.5V to 2.5V   | -2.5V to 2.5V                  | -2.5V to 2.5V     | -2.5V to 2.5V  | -2.5V to 2.5V          | -2.5V to 2.5V  | -2.5V to 2.5V    | -2.5V to 2.5V   |

### MSO5B

#### Constraints:

The constraints for the MSO5B are identical, except the upper frequency bound is doubled.

______________________________________________________________________

## Arbitrary Function Generators

Requesting function generation will turn off the channel requested. The frequency, function,
amplitude, impedance and offset are set. If the function is a square wave, the duty cycle is used
to set how long the pulses are. Symmetry decides what direction the skews towards if the ramp function
is provided. After all parameters are set, the channel is turned back on.

Setting up bursts of the AFG involves setting the AFG trigger to external, so the burst doesn't activate
on the internal trigger. Then the burst state is set on and mode set to triggered.

AFGs have access to the following functions:
SIN, SQUARE, RAMP, PULSE, DC, SINC, GAUSSIAN, LORENTZ, ERISE, EDECAY, HAVERSINE, CARDIAC, NOISE, ARBITRARY

### AFG3K, AFG3KB, AFG3KC

#### Constraints:

The amplitude, offset and frequency range for AFG3Ks is extremely varied dependent on model number, frequency and function. The sample rate of the entire AFG3K series is 250MS/s.
If the output termination matching is set to 50 ohms instead of high impedance then the offset and amplitude bounds will be halved.

AFG3011:

|             | Sin                      | Square                    | Pulse                     | Ramp<br/>Sinc<br/>Gaussian<br/>Lorentz<br/>ERise<br/>EDecay<br/>Haversine | Arbitrary       |
| ----------- | ------------------------ | ------------------------- | ------------------------- | ------------------------------------------------------------------------- | --------------- |
| AFG3011/C:  |                          |                           |                           |                                                                           |                 |
| Frequency   | 1uHz to 10MHz            | 1uHz to 5MHz              | 1mHz to 5MHz              | 1uHz to 100kHz                                                            | 1mHz to 5MHz    |
| Amplitude   | 40mV to 40V              | 40mV to 40V               | 40mV to 40V               | 40mV to 40V                                                               | 40mV to 40V     |
| Offset      | -20V to 20V              | -20V to 20V               | -20V to 20V               | -20V to 20V                                                               | -20V to 20V     |
| AFG302XB/C: |                          |                           |                           |                                                                           |                 |
| Frequency   | 1uHz to 25MHz            | 1uHz to 25MHz<sup>1</sup> | 1mHz to 25MHz<sup>1</sup> | 1uHz to 500kHz<sup>1</sup>                                                | 1mHz to 12.5MHz |
| Amplitude   | 20mV to 20V              | 20mV to 20V               | 20mV to 20V               | 20mV to 20V                                                               | 20mV to 20V     |
| Offset      | -10V to 10V              | -10V to 10V               | -10V to 10V               | -10V to 10V                                                               | -10V to 10V     |
| AFG305XC:   |                          |                           |                           |                                                                           |                 |
| Frequency   | 1uHz to 50MHz            | 1uHz to 40MHz             | 1mHz to 40MHz             | 1uHz to 800kHz                                                            | 1mHz to 25MHz   |
| Amplitude   | 20mV to 20V              | 20mV to 20V               | 20mV to 20V               | 20mV to 20V                                                               | 20mV to 20V     |
| Offset      | -10V to 10V              | -10V to 10V               | -10V to 10V               | -10V to 10V                                                               | -10V to 10V     |
| AFG310X/C:  |                          |                           |                           |                                                                           |                 |
| Frequency   | 1uHz to 100MHz           | 1uHz to 50MHz             | 1mHz to 50MHz             | 1uHz to 1MHz                                                              | 1mHz to 50MHz   |
| Amplitude   | 40mV to 20V              | 40mV to 20V               | 40mV to 20V               | 4 mV to 20V                                                               | 40mV to 20V     |
| Offset      | -10V to 10V              | -10V to 10V               | -10V to 10V               | -10V to 10V                                                               | -10V to 10V     |
| AFG315XC:   |                          |                           |                           |                                                                           |                 |
| Frequency   | 1uHz to 150MHz           | 1uHz to 100MHz            | 1mHz to 100MHz            | 1uHz to 1.5MHz                                                            | 1mHz to 100MHz  |
| Amplitude   | 40mV to 20V<sup>2</sup>  | 40mV to 20V               | 40mV to 20V               | 40mV to 20V                                                               | 40mV to 20V     |
| Offset      | -10V to 10V              | -10V to 10V               | -10V to 10V               | -10V to 10V                                                               | -10V to 10V     |
| AFG325X/C:  |                          |                           |                           |                                                                           |                 |
| Frequency   | 1uHz to 240MHz           | 1uHz to 120MHz            | 1mHz to 120MHz            | 1uHz to 2.4MHz                                                            | 1mHz to 120MHz  |
| Amplitude   | 100mV to 10V<sup>3</sup> | 100mV to 10V              | 100mV to 10V              | 100mV to 10V                                                              | 100mV to 10V    |
| Offset      | -5V to 5V                | -5V to 5V                 | -5V to 5V                 | -5V to 5V                                                                 | -5V to 5V       |

1: AFG302XB has its upper bound for frequency halved for these functions.\
2: Amplitude upper bound is reduced to 16 when frequency is greater than 100MHz.\
3: Amplitude upper bound is reduced to 8 when frequency is greater than 200MHz.

### AFG31K

#### Constraints:

If the output termination matching is set to 50 ohms instead of high impedance then the offset and amplitude bounds will be halved.

|             | Sin                    | Square<br/>Pulse       | Pulse          | Ramp<br/>Sinc<br/>Gaussian<br/>Lorentz<br/>ERise<br/>EDecay<br/>Haversine | Arbitrary         |
| ----------- | ---------------------- | ---------------------- | -------------- | ------------------------------------------------------------------------- | ----------------- |
| AFG3102X:   |                        |                        |                |                                                                           |                   |
| Frequency   | 1uHz to 25MHz          | 1uHz to 20MHz          | 1mHz to 25MHz  | 1uHz to 500kHz                                                            | 1mHz to 12.5MHz   |
| Amplitude   | 2mV to 20V             | 2mV to 20V             | 2mV to 20V     | 2mV to 20V                                                                | 2mV to 20V        |
| Offset      | -10V to 10V            | -10V to 10V            | -10V to 10V    | -10V to 10V                                                               | -10V to 10V       |
| Sample Rate |                        |                        |                |                                                                           | 250MS/s           |
| AFG3105X:   |                        |                        |                |                                                                           |                   |
| Frequency   | 1uHz to 50MHz          | 1uHz to 40MHz          | 1mHz to 40MHz  | 1uHz to 800kHz                                                            | 1mHz to 25MHz     |
| Amplitude   | 2mV to 20V             | 2mV to 20V             | 2mV to 20V     | 2mV to 20V                                                                | 2mV to 20V        |
| Offset      | -10V to 10V            | -10V to 10V            | -10V to 10V    | -10V to 10V                                                               | -10V to 10V       |
| Sample Rate |                        |                        |                |                                                                           | 1GS/s<sup>1</sup> |
| AFG3110X:   |                        |                        |                |                                                                           |                   |
| Frequency   | 1uHz to 100MHz         | 1uHz to 80MHz          | 1mHz to 50MHz  | 1uHz to 1MHz                                                              | 1mHz to 50MHz     |
| Amplitude   | 2mV to 20V<sup>2</sup> | 2mV to 20V<sup>2</sup> | 2mV to 20V     | 2mV to 20V                                                                | 2mV to 20V        |
| Offset      | -10V to 10V            | -10V to 10V            | -10V to 10V    | -10V to 10V                                                               | -10V to 10V       |
| Sample Rate |                        |                        |                |                                                                           | 1GS/s<sup>1</sup> |
| AFG3115X:   |                        |                        |                |                                                                           |                   |
| Frequency   | 1uHz to 150MHz         | 1uHz to 120MHz         | 1mHz to 100MHz | 1uHz to 1.5MHz                                                            | 1mHz to 75MHz     |
| Amplitude   | 2mV to 10V             | 2mV to 10V             | 2mV to 10V     | 2mV to 10V                                                                | 2mV to 10V        |
| Offset      | -5V to 5V              | -5V to 5V              | -5V to 5V      | -5V to 5V                                                                 | -5V to 5V         |
| Sample Rate |                        |                        |                |                                                                           | 2GS/s<sup>1</sup> |
| AFG3125X:   |                        |                        |                |                                                                           |                   |
| Frequency   | 1uHz to 250MHz         | 1uHz to 160MHz         | 1mHz to 120MHz | 1uHz to 2.5MHz                                                            | 1mHz to 125MHz    |
| Amplitude   | 2mV to 10V<sup>3</sup> | 2mV to 10V             | 2mV to 10V     | 2mV to 10V                                                                | 2mV to 10V        |
| Offset      | -5V to 5V              | -5V to 5V              | -5V to 5V      | -5V to 5V                                                                 | -5V to 5V         |
| Sample Rate |                        |                        |                |                                                                           | 2GS/s<sup>1</sup> |

1: When less than 16Kb, otherwise, the sample rate is 250MS/s.\
2: Amplitude upper bound is reduced to 16 when the frequency is greater than 60MHz. It is further reduced to 12 when the frequency is greater than 80 MHz\
3: Amplitude upper bound is reduced to 8 when the frequency is greater than 200MHz.

______________________________________________________________________

## Arbitrary Waveform Generators

Arbitrary Waveform Generators require several different parameters to be specified for a waveform to be generated

Requesting function generation will turn off the channel requested. Predefined waveforms provided with the AWG
are then loaded from the hard drive into the waveform list for the AWG5200 and AWG70K. Sample rate is not channel dependant,
and will be set through the source class. The channel provided has its waveform, offset, amplitude and signal path set.
If the waveform is ramp, a symmetry of 50 will set the waveform to a triangle.

The AWG class has methods specific to it. `generate_waveform` allows for a waveform name from the waveform list
to be provided, instead of a function. This is distinctly different from generate function as it relies on a sample
rate also being provided to actually generate the waveform.

The other method

AWGs have access to the following functions:
SIN, SQUARE, RAMP, TRIANGLE, DC, CLOCK

### AWG5K/AWG7K

`set_output_signal_path` is uniquely defined within the AWG5K and AWG7K classes, as it will set the value for
`AWGCONTROL:DOUTPUTx:STATE`, which is a unique option not seen in the other AWGs.

`set_offset` is conditioned to make sure that the AWG output signal path is not DIR, as the VISA query will time
out otherwise.

#### Stipulations:

Operation complete commands will always return 1 on the AWG5K/7K series.
All waveforms must be of the same length on requesting AWGCONTROL:RUN.

#### AWG5K, AWG5KB, AWG5KC

#### Constraints:

The AWG5K series offers a upper sample rate range from 600 MS/s to 1.2 GS/s dependent on the model number. The amplitude range is dependent on
the signal output path, and if the direct option is selected, it will reduce the amplitude range to 50mV to 1 V and the
offset to 0. Otherwise, the amplitude ranges from 20 mV to 2.25 V and an offset range of plus or minus 2.25 V.

|             | AWG500X/B/C       | AWG501X/B/C       |
| ----------- | ----------------- | ----------------- |
| Sample Rate | 10MS/S to 600MS/s | 10MS/S to 1.2MS/s |
| Amplitude   | 20mV to 2.25V     | 20mV to 2.25V     |
| Offset      | -2.25V to 2.25V   | -2.25V to 2.25V   |

#### Stipulations:

AWG5K's have digitized outputs on the rear of the device.

#### AWG7K, AWG7KB, AWG7KC

#### Constraints:

The AWG7K series functions identically to the AWG5K series, excluding the higher sample rate and lower amplitude and offset range.
The AWG7K also includes varying options which directly effect these ranges, such as option 02 and 06. These options will enforce the
output signal path to always be direct.

|             | AWG705X         | AWG710X          | AWG7102 Option 06            | AWG706XB        | AWG712XB/C       | AWG708XC        | AWG7122B/C Option 06         | AWG7K Option 02 |
| ----------- | --------------- | ---------------- | ---------------------------- | --------------- | ---------------- | --------------- | ---------------------------- | --------------- |
| Sample Rate | 10MS/s to 5GS/s | 10MS/s to 10GS/s | 10MS/s to 20GS/s<sup>1</sup> | 10MS/s to 6GS/s | 10MS/s to 12GS/s | 8MS/s to 10GS/s | 10MS/s to 24GS/s<sup>1</sup> | "               |
| Amplitude   | 50mV to 2V      | 50mV to 2V       | 0.5V to 1.0V                 | 50mV to 2V      | 50mV to 2V       | 50mV to 2V      | 0.5V to 1.0V                 | 0.5V to 1.0V    |
| Offset      | -0.5V to 0.5V   | -0.5V to 0.5V    | N/A                          | -0.5V to 0.5V   | -0.5V to 0.5V    | -0.5V to 0.5V   | N/A                          | N/A             |

1: Samples rates higher than 10GS/S(12GS/s for B/C) can only be done through Interleave.

### AWG5200

`set_output_signal_path` is uniquely defined within the AWG5200 as it has special output signal paths.

#### Constraints:

The AWG5200 does not have a sample rate range dependent on model number, but instead of what option is installed.
Option 25 on the devices means that the maximum rate is 2.5 GS/s, whereas option 50

|             | AWG5200 Option 25 | AWG5200 Option 50 | AWG5200 Option DC |
| ----------- | ----------------- | ----------------- | ----------------- |
| Sample Rate | 298S/s to 2.5GS/s | 298S/s to 5.0GS/s | "                 |
| Amplitude   | 25mV to 750mV     | 25mV to 750mV     | 25mV to 1.5V      |
| Offset      | -2.0V to 2.0V     | -2.0V to 2.0V     | -2.0V to 2.0V     |

#### Stipulations:

The AWG5200's programming commands are seperated into three seperated categories: Sequential, Blocking, Overlapping.
The type of command is important to consider as an incorrect order can lead to unintended results.

Sequential commands function as the standard PI commands. They will not start until the previous command has finished. These commands
tend to be fast and will allow for quick response times even if they are queued in the input buffer.

Blocking commands are very similar to sequential commands. However, these commands tend to take longer to execute. This means that
if a number of blocking commands are performed in sequence, a query may time out when sent.

Some commands can perform data analysis on another thread, these are referred to as overlapping commands. They allow any command to be executed
while they are being executed. They cannot be executed if the previous command was blocking or sequential, or if the operation complete status register is
not set.

### AWG70KA, AWG70KB

#### Constraints:

The AWG70K is a special case, where only the direct signal output path is allowed (unless option AC is installed). This means the amplitude is limited,
and offset is not allowed to be set by default. However, there is a secondary device which allows for DC amplification, the MDC4500-4B. The MDC4500-4B is an amplifier
which provides an AWG70K the ability to utilize DC offset. It also provides a large range for amplitude.

`set_output_signal_path` is uniquely defined within the AWG70KA and AWG70KB classes. By default, it will first attempt to set the output signal path to DCA.
If this fails (implying an MDC4500-4B is not connected), then a direct (DIR) signal path will be set.

`set_offset` is conditioned to make sure that the AWG output signal path is not DIR, as the VISA query will time
out otherwise.

|             | AWG70001A/B Option 150 | AWG70002A/B Option 225 | AWG70002A/B Option 216 | AWG70002A/B Option 208 | AWG7000XA/B MDC4500-4B DCA path |
| ----------- | ---------------------- | ---------------------- | ---------------------- | ---------------------- | ------------------------------- |
| Sample Rate | 1.49kS/s to 50GS/s     | 1.49kS/s to 25GS/s     | 1.49kS/s to 16GS/s     | 1.49kS/s to 8GS/s      | "                               |
| Amplitude   | 125mV to 500mV         | 125mV to 500mV         | 125mV to 500mV         | 125mV to 500mV         | 31mV to 1.6V<sup>1</sup>        |
| Offset      | N/A                    | N/A                    | N/A                    | N/A                    | -400mV to 800mv                 |

#### Stipulations:

The AWG70K also houses infrastructure to support sequential, blocking and overlapping commands.
