# Accuracy Measurement Example

Logs a series of measurements at stepped target distances so you can compare
the sensor readings against the real distance, e.g. to check a calibration or
characterize the sensor over its range.

## Hardware

| Signal       | GPIO | Notes                                     |
|--------------|------|-------------------------------------------|
| I2C SDA      | 8    | internal pull-up enabled                  |
| I2C SCL      | 9    | internal pull-up enabled                  |
| Start button | 14   | active low, internal pull-up; press = GND |

Pins are set at the top of `main/accuracy.cpp` and in the I2C bus config.
Adjust them for your board.

## Configuration

Set these defines at the top of `main/accuracy.cpp`:

| Define                  | Default | Meaning                                           |
|-------------------------|---------|---------------------------------------------------|
| `SENSOR_OFFSET`         | 0       | Offset in mm from the [calibration](../calibration) example |
| `TARGET_DISTANCE_MIN`   | 100     | First target distance in mm                       |
| `TARGET_DISTANCE_MAX`   | 1200    | Last target distance in mm                        |
| `TARGET_DISTANCE_DELTA` | 100     | Step between target distances in mm              |
| `NUM_MEASUREMENTS`      | 10      | Measurements per target distance, 100 ms apart    |

## Run

```sh
idf.py build flash monitor
```

1. Place a **white**, flat target at the first distance (100 mm).
2. Press the start button. The example logs the target distance and
   `NUM_MEASUREMENTS` readings.
3. Move the target one step further (+100 mm) and press the button again.
4. Repeat up to `TARGET_DISTANCE_MAX`. After the last distance the example
   logs `MEASUREMENT SERIES COMPLETE`, and the next press starts a new
   series at `TARGET_DISTANCE_MIN`.

Example output:

```
I (...) accuracy: TARGET DISTANCE: 100
I (...) accuracy: MEASUREMENT 0: 101 [mm]
I (...) accuracy: MEASUREMENT 1: 99 [mm]
...
```

Copy the log into a spreadsheet to compute the mean error and spread per
distance.
