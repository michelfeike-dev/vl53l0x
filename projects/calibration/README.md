# Calibration

Offset definition of the VL53L0X with a reference target.

## Hardware

| Component    | Connection                             |
|--------------|----------------------------------------|
| Board        | ESP32-S3                               |
| VL53L0X      | SDA → GPIO 8, SCL → GPIO 9, 3.3 V, GND |
| Start Button | GPIO 14 → GND                          |
| Target       | White, flat, 100 mm                    |

## Software

- ESP-IDF 5.3

## Getting Started

### Configuration

| Constant           | Default | Meaning                    |
|--------------------|---------|----------------------------|
| `TARGET_DISTANCE`  | 100     | Target distance in mm      |
| `NUM_MEASUREMENTS` | 100     | Readings for the mean      |
| `START_PIN`        | 14      | Start button               |

### Build and Flash

```sh
cd projects/calibration
idf.py set-target esp32s3
idf.py build flash monitor
```

### Measurement

Place the target at `TARGET_DISTANCE` and press the start button. The
project computes `offset = TARGET_DISTANCE - mean` and applies it:

```
I (...) calibration: OFFSET = 14 [mm]
I (...) calibration: REFERENCE MEASUREMENT: 102 [mm]
```

## Evaluation

- **Reference measurement** ≈ `TARGET_DISTANCE`
- **Offset** repeatable on a second run
- **Bias** ≈ 0 at 100 mm in [accuracy](../accuracy)

Use the offset as `OFFSET_MM` in [accuracy](../accuracy) and
[filter](../filter).
