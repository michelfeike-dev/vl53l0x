# Offset Calibration

Measures the mean distance to a reference target, computes the range offset
and applies it to the sensor. Run it once per sensor, and again after changing
the cover glass or the mounting, to find the offset your application should
use.

## How It Works

On a falling edge of the start button the project:

1. resets the sensor offset to 0, so a previous calibration does not skew the
   result,
2. takes `NUM_MEASUREMENTS` readings, 100 ms apart,
3. computes `offset = TARGET_DISTANCE - mean` (ST convention: the sensor adds
   the offset to every range),
4. applies the offset with `setOffset()` and logs one reference measurement,
   which should now be close to `TARGET_DISTANCE`.

Press the button again to recalibrate at any time.

## Hardware

| Signal       | GPIO | Notes                                     |
|--------------|------|-------------------------------------------|
| I2C SDA      | 8    | internal pull-up enabled                  |
| I2C SCL      | 9    | internal pull-up enabled                  |
| Start button | 14   | active low, internal pull-up; press = GND |

The start pin is set by `START_PIN` at the top of `main/calib.cpp`, the I2C
pins in the bus configuration in `app_main()`. Adjust them for your board.

## Configuration

Set these constants at the top of `main/calib.cpp`:

| Constant           | Default | Meaning                                  |
|--------------------|---------|------------------------------------------|
| `START_PIN`        | 14      | Start button                             |
| `TARGET_DISTANCE`  | 100     | Distance of the reference target in mm   |
| `NUM_MEASUREMENTS` | 100     | Readings averaged for the offset         |

## Setup

- Place a white, flat target at exactly `TARGET_DISTANCE` (100 mm) from the
  sensor. Measure from the front of the sensor, or from the cover glass if
  one is used.
- Keep the target perpendicular to the optical axis and large enough to fill
  the field of view of the sensor.
- Avoid strong ambient light, e.g. direct sunlight.

## Build and Flash

```sh
idf.py set-target esp32s3
idf.py build flash monitor
```

## Output

```
I (...) calibration: OFFSET CALIBRATION
I (...) calibration: Target distance: 100 mm
...
I (...) calibration: MEASUREMENT 98: 87 [mm]
I (...) calibration: MEASUREMENT 99: 90 [mm]
I (...) calibration: CALIBRATION SUCCESSFUL
I (...) calibration: OFFSET = 14 [mm]
I (...) calibration: STORE DATA SENSOR
I (...) calibration: REFERENCE MEASUREMENT: 102 [mm]
```

To keep the log of a calibration, save the monitor output in `data/`, e.g.
`data/s1.log`. Log files are ignored by Git.

## Using the Result

The offset is held in the sensor's RAM and is lost on reset or power loss.
Take the logged value and apply it in your application, either via the
constructor (applied in `init()`) or with `setOffset()` after `init()`. Both
take micrometers:

```cpp
// OFFSET = 14 [mm] from the calibration log
VL53L0X sensor(bus, GPIO_NUM_MAX, GPIO_NUM_MAX, 400000, 14 * 1000);
sensor.init();
```

The [accuracy](../accuracy) and [filter](../filter) projects take the offset
in mm as `OFFSET_MM`.

## Troubleshooting

| Symptom                                | Check                                                  |
|----------------------------------------|--------------------------------------------------------|
| Offset outside roughly ±50 mm          | Target distance, target color, mounting; the sensor accepts -512 mm to +511 mm |
| `CALIBRATION FAILED`                   | A reading was invalid: target missing, too small or too dark |
| `SENSOR INIT FAILED`                   | Wiring, supply voltage, pins, pull-up resistors        |
