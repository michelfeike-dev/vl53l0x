# VL53L0X

Measurement projects with the VL53L0X Time-of-Flight.

## Contents

- [Features](#features)
- [Projects](#projects)
- [Hardware](#hardware)
- [Software](#software)
- [Getting Started](#getting-started)
- [Repository Structure](#repository-structure)
- [License](#license)

## Features

- **Offset Definition:** the [calibration](projects/calibration) project
  measures a reference target and computes the offset of the sensor.
- **Offset Compensation:** via the constructor 
  (applied in `init()`) or at runtime with `setOffset()`, including negative
  values.
- **High Accuracy Mode:** via `setTimingBudget()` from 33 ms to 200 ms.
- **Accuracy Determination:** the [accuracy](projects/accuracy) project
  measures stepped target distances and evaluates bias, standard deviation and the
  datasheet limit.
- **Median Filter:** the [filter](projects/filter) project filters the
  readings on the device or offline and evaluates the result.

## Projects

| Project                             | Purpose                                              | Result                         |
|-------------------------------------|------------------------------------------------------|--------------------------------|
| [calibration](projects/calibration) | Offset definition of the sensor             | mm                   |
| [accuracy](projects/accuracy)       | Sensor accuracy at stepped target distances     | CSV (bias, standard deviation, datasheet limit) |
| [filter](projects/filter)           | Noise reduction using a median filter | mm |

## Hardware

| Component    | Connection                                         |
|--------------|----------------------------------------------------|
| Board        | ESP32-S3                                           |
| VL53L0X      | SDA → GPIO 8, SCL → GPIO 9, 3.3 V, GND             |

Note: Pull Up 4.7 kΩ 

## Software

- ESP-IDF 5.3 
- Python 3 
- Official ST VL53L0X API ([STSW-IMG005](https://www.st.com/en/embedded-software/stsw-img005.html))
- C++ wrapper [kerikun11/ESP32_VL53L0X](https://github.com/kerikun11/ESP32_VL53L0X)

## Getting Started

### Build and Flash

```sh
git clone git@github.com:michelfeike-dev/vl53l0x.git
cd vl53l0x/projects/calibration
idf.py set-target esp32s3
idf.py build flash monitor
```

The projects reference the driver from the repository root via
`EXTRA_COMPONENT_DIRS`.

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