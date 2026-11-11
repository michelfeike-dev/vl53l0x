# Calibration

Offset definition of the VL53L0X with a reference target.

$d_{offset} = d_{target} - d_{measured}$

## Hardware

| Component    | Connection                             |
|--------------|----------------------------------------|
| Board        | ESP32-S3                               |
| VL53L0X      | SDA → GPIO 8<br>SCL → GPIO 9<br>VCC → 3.3 V<br>GND → GND |
| Start Pin    | GPIO 14                                |
| Target       | White                                  |
| [Target Size](../../README.md#field-of-view)       | ø44 mm @ 100 mm                                  |

Note: 

$A_{Target} > A_{FoV}$

## Software

- ESP-IDF 5.3
- Official ST VL53L0X API [STSW-IMG005](https://www.st.com/en/embedded-software/stsw-img005.html)
- C++ wrapper [kerikun11/ESP32_VL53L0X](https://github.com/kerikun11/ESP32_VL53L0X)

## Getting Started

### Configuration

| Constant           | Default | Description                |
|--------------------|---------|----------------------------|
| `TARGET_DISTANCE`  | 100     | Target distance [mm]       |
| `NUM_MEASUREMENTS` | 100     | Number of measurements     |
| `START_PIN`        | 14      | Input         |

### Build and Flash

```sh
cd projects/calibration
idf.py set-target esp32s3
idf.py build flash monitor
```

### Measurement

Place the target at `TARGET_DISTANCE`.
A falling edge on the `START_PIN` pin initiates the measurement. 

```
I (...) calibration: OFFSET = 14 [mm]
I (...) calibration: REFERENCE MEASUREMENT: 102 [mm]
```
