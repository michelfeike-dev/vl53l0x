# Accuracy Measurement

Measures a series of readings at stepped target distances and evaluates how
far the sensor deviates from the real distance. Use it to verify a
calibration, to compare ranging profiles or to characterize the sensor in
your mechanical setup.

## How It Works

1. Initializes the sensor, sets the timing budget `TIMING_BUDGET_US` and the
   offset `OFFSET_MM`.
2. On every falling edge of the start button it logs the current target
   distance followed by `NUM_MEASUREMENTS` readings.
3. The target distance advances by `DIST_STEP` per button press, from
   `DIST_MIN` to `DIST_MAX`. After the last distance the project logs
   `MEASUREMENT SERIES COMPLETE` and the next press starts a new series.
4. The Python script `eval/evaluate.py` evaluates the saved log.

## Hardware

| Signal       | GPIO | Notes                                     |
|--------------|------|-------------------------------------------|
| I2C SDA      | 8    | internal pull-up enabled                  |
| I2C SCL      | 9    | internal pull-up enabled                  |
| Start button | 14   | active low, internal pull-up; press = GND |

The start pin is set by `START_PIN` at the top of `main/accuracy.cpp`, the I2C
pins in the bus configuration in `app_main()`. Adjust them for your board.

## Configuration

Set these constants at the top of `main/accuracy.cpp`:

| Constant           | Default | Meaning                                                     |
|--------------------|---------|-------------------------------------------------------------|
| `START_PIN`        | 14      | Start button                                                |
| `TIMING_BUDGET_US` | 200000  | Timing budget in µs (33000 = default, 200000 = high accuracy) |
| `OFFSET_MM`        | 28      | Offset in mm from the [calibration](../calibration) project |
| `DIST_MIN`         | 100     | First target distance in mm                                 |
| `DIST_MAX`         | 1200    | Last target distance in mm                                  |
| `DIST_STEP`        | 100     | Step between target distances in mm                         |
| `NUM_MEASUREMENTS` | 100     | Readings per target distance                                |

`DIST_MIN < DIST_MAX` is checked at compile time.

## Measurement Setup

The result depends as much on the setup as on the sensor:

- Use a white, flat target, perpendicular to the optical axis.
- The target must cover the spot of the field of view at every distance (see
  [Field of View](#field-of-view)). Otherwise the sensor also measures the
  background and the readings shift.
- Mount the sensor high enough above the ground that the cone does not hit
  the ground up to `DIST_MAX`.
- Position the target precisely; a positioning error enters directly into the
  bias.
- Avoid strong ambient light.

## Build and Flash

```sh
idf.py set-target esp32s3
idf.py build flash monitor
```

## Procedure

1. Place the target at `DIST_MIN` (100 mm).
2. Press the start button and wait until all readings are logged.
3. Move the target by `DIST_STEP` (+100 mm) and press the button again.
4. Repeat up to `DIST_MAX` until `MEASUREMENT SERIES COMPLETE` is logged.
5. Save the monitor output of the series in `data/`, e.g. `data/s1.log`.

```
I (...) accuracy: TARGET DISTANCE: 100
I (...) accuracy: MEASUREMENT 0: 101 [mm]
I (...) accuracy: MEASUREMENT 1: 101 [mm]
I (...) accuracy: MEASUREMENT 2: 99 [mm]
...
```

If a reading is invalid, e.g. because the target does not fill the field of
view, the project logs `MEASUREMENT FAILED` and stops. Check the setup and
restart the board.

## Evaluation

`eval/evaluate.py` parses the log, prints the statistics per target distance,
saves them as CSV and plots them. Lines with or without the ESP-IDF log
prefix are accepted; other lines are ignored. If a target distance appears
more than once, only its last series is evaluated.

### Setup

Python 3 with matplotlib:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install matplotlib
```

### Usage

```sh
python3 eval/evaluate.py data/s1.log -c data/s1.csv                    # show the plots
python3 eval/evaluate.py data/s1.log -c data/s1.csv -o data/s1.png     # save the plots
python3 eval/evaluate.py data/s1_ha.log -c data/s1_ha.csv -o data/s1_ha.png -m high-accuracy
```

| Argument         | Required | Meaning                                                           |
|------------------|----------|-------------------------------------------------------------------|
| `log`            | no       | Log file; reads stdin if omitted                                  |
| `-c`, `--csv`    | yes      | CSV file the values are written to                                |
| `-o`, `--output` | no       | Save the plots instead of showing them                            |
| `-m`, `--mode`   | no       | Ranging profile of the log: `default` (±4 %) or `high-accuracy` (±3 %); default `default` |
| `--spec`         | no       | Override the datasheet accuracy in percent of the target distance |
| `--fov`          | no       | Full field of view in degrees; default 25                         |

Use `-m` to match `TIMING_BUDGET_US` of the measurement. With `-o` the
accuracy plot is saved under the given name and the field of view plot as
`fov.<ext>` in the same directory; the field of view only depends on the
sensor, so every run overwrites it.

CSV, PNG and log files in `data/` are ignored by Git.

### Values

The error of a single reading is `target - measured`; a positive error means
the sensor reads too short. Per target distance the script computes:

| Column (CSV)                        | Meaning                                                                 |
|-------------------------------------|-------------------------------------------------------------------------|
| `target_mm`                         | Target distance                                                         |
| `n`                                 | Number of readings                                                      |
| `mean_mm`                           | Mean of the readings                                                    |
| `bias_mm`                           | Systematic error, `target - mean`; correctable by offset (constant) or gain (growing with distance) |
| `std_mm`                            | Standard deviation σ, the noise; reduced by averaging or a longer timing budget |
| `rmse_mm`                           | Total error, `sqrt(mean((target - measured)²))` ≈ `sqrt(bias² + σ²)`    |
| `range95_low_mm`, `range95_high_mm` | `bias ± 2σ`; about 95 % of the readings lie in this range               |
| `spec_mm`                           | Datasheet limit at this distance, `target × spec %`                     |
| `in_spec`                           | `1` if the whole 95 % range lies within `±spec_mm`                      |

Example (high accuracy mode, 100 readings per distance):

```
High Accuracy Mode: datasheet accuracy ±3 %
 Target   n     Mean    Bias    Std   RMSE        95% range   Spec ±3%  OK
    100 100    100.2    -0.2    1.2    1.2     -2.5 .. +2.1       ±3.0 yes
    200 100    206.2    -6.2    0.8    6.3     -7.9 .. -4.5       ±6.0  no
    300 100    309.9    -9.9    1.1    9.9    -12.1 .. -7.6       ±9.0  no
    400 100    407.8    -7.8    1.0    7.8     -9.8 .. -5.7      ±12.0 yes
    500 100    503.1    -3.1    1.6    3.5     -6.3 .. +0.2      ±15.0 yes
    600 100    593.0    +7.0    2.1    7.3    +2.8 .. +11.2      ±18.0 yes
```

### Accuracy Plot

Shows the bias over the target distance with the `bias ± 2σ` band, the
target as zero line and the datasheet limit of the selected mode. Where the
band does not include 0, the sensor reads systematically off; where it leaves
the limit, the reading is out of specification.

### Field of View

Shows the cone of the sensor (default 25°, ±12.5° around the optical axis)
and the diameter of the spot on the target at every measured distance. The
target must be larger than this spot, otherwise the sensor also sees the
background.

## Related Projects

- [calibration](../calibration): determine `OFFSET_MM`
- [filter](../filter): evaluate a median filter on the same measurement series
