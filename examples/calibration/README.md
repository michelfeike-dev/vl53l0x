# Offset Calibration Example

Measures the mean distance to a reference target, computes the range offset
and applies it to the sensor. Use it once per sensor (and again after changing
the cover glass or mounting) to find the offset your application should use.

## Hardware

| Signal       | GPIO | Notes                                     |
|--------------|------|-------------------------------------------|
| I2C SDA      | 8    | internal pull-up enabled                  |
| I2C SCL      | 9    | internal pull-up enabled                  |
| Start button | 14   | active low, internal pull-up; press = GND |

Pins are set at the top of `main/calib.cpp` and in the I2C bus config. Adjust
them for your board.

## Setup

- Place a **white**, flat target at exactly **100 mm** from the sensor
  (`TARGET_DISTANCE`).
- Keep the target perpendicular to the sensor and avoid strong ambient light.

## Run

```sh
idf.py build flash monitor
```

Press the start button (falling edge on GPIO 14). The example then:

1. resets the sensor offset to 0, so a previous calibration does not skew the
   result,
2. takes 100 measurements 100 ms apart (`NUM_MEASUREMENTS`),
3. computes `offset = TARGET_DISTANCE - mean` (ST convention: the sensor adds
   the offset to every range),
4. applies the offset with `setOffset()` and logs one reference measurement,
   which should now be close to 100 mm.

You can press the button again to recalibrate at any time.

Example output:

```
I (...) calibration: CALIBRATION SUCCESSFUL
I (...) calibration: OFFSET = -12 [mm]
I (...) calibration: STORE DATA SENSOR
I (...) calibration: REFERENCE MEASUREMENT: 100 [mm]
```

## Using the result

The offset lives in the sensor's RAM and is lost on reset or power loss. Take
the logged value and pass it to your application, either via the constructor
(applied in `init()`) or with `setOffset()` after `init()`. Both take
micrometers:

```cpp
// OFFSET = -12 [mm] from the calibration log
VL53L0X sensor(bus, GPIO_NUM_MAX, GPIO_NUM_MAX, 400000, -12 * 1000);
sensor.init();
```

If the reported offset is outside roughly ±50 mm, check the target distance,
target color and mounting before using it. The sensor accepts
-512 mm to +511 mm.
