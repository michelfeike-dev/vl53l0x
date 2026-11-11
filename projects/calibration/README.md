# Offset Calibration

Measures a reference target at a known distance, computes the range offset
and applies it to the sensor. Run it once per sensor and again after changing
the cover glass or the mounting.

## Hardware

| Component    | Connection                                          |
|--------------|-----------------------------------------------------|
| Board        | ESP32-S3                                            |
| VL53L0X      | SDA → GPIO 8, SCL → GPIO 9, 3.3 V, GND              |
| Start Button | GPIO 14 → GND (active low, internal pull-up)        |
| Target       | White, flat, at exactly 100 mm, fills the field of view |

- Measure the distance from the front of the sensor (or the cover glass).
- Keep the target perpendicular to the optical axis; avoid direct sunlight.
- On a bare sensor add external 4.7 kΩ pull-ups on SDA and SCL.

## Getting Started

### Requirements

- ESP-IDF 5.3 or later

### Configuration

Constants at the top of `main/calib.cpp`:

| Constant           | Default | Meaning                                |
|--------------------|---------|----------------------------------------|
| `START_PIN`        | 14      | Start button                           |
| `TARGET_DISTANCE`  | 100     | Distance of the reference target in mm |
| `NUM_MEASUREMENTS` | 100     | Readings averaged for the offset       |

### Build and Flash

```sh
cd projects/calibration
idf.py set-target esp32s3
idf.py build flash monitor
```

## Measurement

Press the start button. The project resets the offset to 0, averages
`NUM_MEASUREMENTS` readings, computes `offset = TARGET_DISTANCE - mean`,
applies it and logs one reference measurement:

```
I (...) calibration: CALIBRATION SUCCESSFUL
I (...) calibration: OFFSET = 14 [mm]
I (...) calibration: STORE DATA SENSOR
I (...) calibration: REFERENCE MEASUREMENT: 102 [mm]
```

Save the monitor output in `data/`, e.g. `data/s1.log` (ignored by Git).

## Evaluation

The calibration is valid if:

- the **reference measurement** is close to `TARGET_DISTANCE`,
- the **offset** is plausible (roughly within ±50 mm) and repeatable when you
  press the button again,
- the [accuracy](../accuracy) project with this offset shows a bias close to
  0 at 100 mm.

If not, check the target distance, color and mounting. `CALIBRATION FAILED`
means a reading was invalid (target missing, too small or too dark).

## Using the Result

The offset is lost on reset. Apply the logged value in your application (in
µm) or as `OFFSET_MM` in the [accuracy](../accuracy) and [filter](../filter)
projects:

```cpp
VL53L0X sensor(bus, GPIO_NUM_MAX, GPIO_NUM_MAX, 400000, 14 * 1000);
sensor.init();
```
