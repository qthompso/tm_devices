# Architectural Overview

An overview of this package's architecture.

______________________________________________________________________

## The Device Manager

The `SignalGenerator` class is responsible for most waveform generators, including AWGs and AFGs.
Similarily, `Tekscope` is responsible for AFGs internal to the scopes themselves, commonly referred to as
IAFGs. Both classes inheret `SignalGeneratorMixin` for a list of methods which share functionality throughout
all signal sources. These public properties, functions and methods include:
source_device_constants is a property which holds information about what functions
and memory sizes are allowed.
generate_function is a method which allows for the user to request a function from
any source,

The `DeviceManager` uses a configuration parser (`DMConfigParser`) to read in
connection information from an optional config file as well as to store
connection information that is provided directly via python code.

### Block Diagram

```{mermaid}
classDiagram
    direction LR

    DeviceManager --> "0..n" Device : contains
    DeviceManager --> "1" DMConfigParser : uses
```

______________________________________________________________________

## Main device types

There are currently 9 different supported device types: **Scopes**, **Arbitrary
Waveform Generators (AWGs)**, **Arbitrary Function Generators (AFGs)**, **Source
Measure Units (SMUs)**, **Power Supplies (PSUs)**, **Data Acquisition Systems
(DAQs)**, **Digital Multimeters (DMMs)**, **Systems Switches (SSs)**, and
**Margin Testers**.

The driver class structure uses inheritance, which means that common attributes
and methods can be defined in higher-level classes (sometimes called parent
classes) and inherited by subclasses (sometimes called child classes), to reduce
the lines of code needed to create new device drivers.

Every single device driver within a particular device type is guaranteed to have
the same class signature (attribute and method names). Often times specific
device drivers will need to implement the functionality for specific methods or
even overwrite inherited functionality due to the differences that can occur
between different models of the same device type.

### Block Diagram

```{autoclasstree} tm_devices.drivers.device_type_classes
---
full:
namespace: tm_devices.drivers
align: center
alt: Main device types class diagram
---
```

______________________________________________________________________

## All device drivers

This package supports many devices, zoom in to see them all!

### Block Diagram

```{autoclasstree} tm_devices.drivers
---
full:
namespace: tm_devices.drivers
align: center
alt: Complete device driver class diagram
---
```
