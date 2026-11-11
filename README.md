# VL53L0X Projects

Measurement projects with the STMicroelectronics VL53L0X time-of-flight
distance sensor on the ESP32-S3 with ESP-IDF: determine the range offset,
measure the accuracy and filter the readings.

The projects use a VL53L0X driver that was cloned and extended for this
purpose (see [Driver](#driver)).

## Contents

- [Features](#features)
- [Projects](#projects)
- [Workflow](#workflow)
- [Hardware](#hardware)
- [Getting Started](#getting-started)
- [Driver](#driver)
- [Repository Structure](#repository-structure)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Features

- **Settable offset:** the driver accepts a range offset, via the constructor
  (applied in `init()`) or at runtime with `setOffset()`, including negative
  values.
- **High accuracy mode:** the timing budget can be raised from 33 ms to
  200 ms to use the high accuracy ranging profile.
- **Offset determination:** the [calibration](projects/calibration) project
  measures a reference target and computes the offset of the sensor.
- **Accuracy determination:** the [accuracy](projects/accuracy) project
  measures stepped target distances and evaluates bias, noise and the
  datasheet limit.
- **Median filter:** the [filter](projects/filter) project filters the
  readings on the device or offline and evaluates the result.

## Projects

Each project is a standalone ESP-IDF project with its own documentation.

| Project                             | Purpose                                              | Result                         |
|-------------------------------------|------------------------------------------------------|--------------------------------|
| [calibration](projects/calibration) | Determine the range offset of the sensor             | Offset in mm                   |
| [accuracy](projects/accuracy)       | Measure the accuracy at stepped target distances     | Table, CSV, accuracy and field of view plot |
| [filter](projects/filter)           | Apply a median filter and evaluate the filtered readings | Table, CSV, accuracy plot  |

## Workflow

The projects build on each other:

1. **Calibrate:** run [calibration](projects/calibration) with a target at
   100 mm and note the logged offset.
2. **Measure:** set the offset as `OFFSET_MM` in
   [accuracy](projects/accuracy), choose the ranging profile with
   `TIMING_BUDGET_US` and record a series from 100 mm to 1200 mm.
3. **Evaluate:** run `eval/evaluate.py` on the log to get bias, standard
   deviation and the comparison with the datasheet limit.
4. **Filter:** run [filter](projects/filter) on the device, or apply the
   median filter offline to the accuracy log, and compare the results.

## Hardware

All projects use the same setup:

| Component    | Connection                                         |
|--------------|----------------------------------------------------|
| Board        | ESP32-S3                                           |
| VL53L0X      | SDA → GPIO 8, SCL → GPIO 9, 3.3 V, GND             |
| Start button | GPIO 14 → GND (active low, internal pull-up)       |
| Target       | White, flat, large enough to fill the field of view |

The internal pull-ups of the ESP32-S3 are weak. Most VL53L0X breakout boards
have their own pull-up resistors; on a bare sensor add external ones
(e.g. 4.7 kΩ).

## Getting Started

### Requirements

- ESP-IDF 5.3 or later (the projects build with v6.1)
- Python 3 with matplotlib for the evaluation scripts

### Build and Flash

```sh
git clone git@github.com:michelfeike-dev/vl53l0x.git
cd vl53l0x/projects/calibration
idf.py set-target esp32s3
idf.py build flash monitor
```

The projects reference the driver from the repository root via
`EXTRA_COMPONENT_DIRS`.

### Evaluation Scripts

```sh
cd projects/accuracy
python3 -m venv .venv
source .venv/bin/activate
pip install matplotlib
```

Save the monitor output of a measurement in the `data/` directory of the
project. Logs and evaluation results (`data/*.log`, `*.csv`, `*.png`) are
ignored by Git.

## Driver

The driver is a C++ wrapper around the official ST VL53L0X API
([STSW-IMG005](https://www.st.com/en/embedded-software/stsw-img005.html)),
located in `inc/` and `api/`. Compared with the original it was:

- ported to the ESP-IDF I2C master driver (`driver/i2c_master.h`); the
  application creates the bus and passes its handle,
- extended by a range offset in the constructor and `setOffset()`,
- changed to apply the constructor offset in `init()` and to accept negative
  offsets.

### Offset

The offset is given in micrometers and follows the ST convention
`offset = actual - measured`; the sensor adds it to every range. The valid
range is -512 mm to +511 mm. It is held in the sensor's RAM and must be
applied again after every reset.

```cpp
// Via the constructor, applied in init()
VL53L0X sensor(bus, GPIO_NUM_MAX, GPIO_NUM_MAX, 400000, 28 * 1000);
sensor.init();

// Or at runtime, after init()
sensor.setOffset(28 * 1000);
```

### High Accuracy Mode

`init()` sets a timing budget of 33 ms. A longer budget reduces the noise but
lowers the measurement rate:

| Profile       | Timing budget | Range | Datasheet accuracy |
|---------------|---------------|-------|--------------------|
| Default       | 30 ms         | 1.2 m | ±4 %               |
| High accuracy | 200 ms        | 1.2 m | ±3 %               |

```cpp
sensor.setTimingBudget(200000); // high accuracy
```

### Usage in Other Projects

The driver can be added as a component via the ESP Component Manager in
`main/idf_component.yml`:

```yaml
dependencies:
  vl53l0x:
    git: git@github.com:michelfeike-dev/vl53l0x.git
    version: v1.3.1
```

and `vl53l0x` added to `REQUIRES` in the component's `CMakeLists.txt`.
`read()` returns `false` if the sensor reports an invalid range status, e.g.
when no target is within range. The public interface is documented in
[inc/VL53L0X.h](inc/VL53L0X.h).

## Repository Structure

```
vl53l0x/
├── projects/
│   ├── calibration/       Offset determination
│   ├── accuracy/          Accuracy measurement and evaluate.py
│   └── filter/            Median filter and filter.py
├── inc/VL53L0X.h          Driver class
├── api/                   STMicroelectronics VL53L0X API (core, platform)
├── CMakeLists.txt         ESP-IDF component definition of the driver
├── idf_component.yml      Component manager manifest
└── CHANGELOG.md
```

## License

MIT, see [LICENSE](LICENSE).

## Acknowledgements

Based on [kerikun11/ESP32_VL53L0X](https://github.com/kerikun11/ESP32_VL53L0X),
ported to the ESP-IDF I2C master driver and extended with offset calibration.
