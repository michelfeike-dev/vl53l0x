# Accuracy Measurement

Measures a series of readings at stepped target distances and evaluates how
far the sensor deviates from the real distance. Use it to verify a
calibration, compare ranging profiles or characterize your mechanical setup.

## Hardware

| Component    | Connection                                          |
|--------------|-----------------------------------------------------|
| Board        | ESP32-S3                                            |
| VL53L0X      | SDA → GPIO 8, SCL → GPIO 9, 3.3 V, GND              |
| Start Button | GPIO 14 → GND (active low, internal pull-up)        |
| Target       | White, flat, larger than the field of view at `DIST_MAX` |

The setup determines the result as much as the sensor:

- The target must cover the light spot at every distance (see the field of
  view plot), otherwise the sensor also measures the background.
- Mount the sensor high enough that the cone does not hit the ground up to
  `DIST_MAX`.
- Position the target precisely; any positioning error enters the bias.
- On a bare sensor add external 4.7 kΩ pull-ups on SDA and SCL.

## Getting Started

### Requirements

- ESP-IDF 5.3 or later
- Python 3 with matplotlib for the evaluation

### Configuration

Constants at the top of `main/accuracy.cpp`:

| Constant           | Default | Meaning                                                       |
|--------------------|---------|---------------------------------------------------------------|
| `START_PIN`        | 14      | Start button                                                  |
| `TIMING_BUDGET_US` | 200000  | Timing budget in µs (33000 = default, 200000 = high accuracy) |
| `OFFSET_MM`        | 28      | Offset in mm from the [calibration](../calibration) project   |
| `DIST_MIN`         | 100     | First target distance in mm                                   |
| `DIST_MAX`         | 1200    | Last target distance in mm                                    |
| `DIST_STEP`        | 100     | Step between target distances in mm                           |
| `NUM_MEASUREMENTS` | 100     | Readings per target distance                                  |

### Build and Flash

```sh
cd projects/accuracy
idf.py set-target esp32s3
idf.py build flash monitor
```

## Measurement

1. Place the target at `DIST_MIN` and press the start button.
2. Move the target by `DIST_STEP` and press again.
3. Repeat until `MEASUREMENT SERIES COMPLETE` is logged.
4. Save the monitor output in `data/`, e.g. `data/s1.log`.

```
I (...) accuracy: TARGET DISTANCE: 100
I (...) accuracy: MEASUREMENT 0: 101 [mm]
...
```

`MEASUREMENT FAILED` stops the series: check the setup and restart the board.

## Evaluation

### Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install matplotlib
```

### Usage

```sh
python3 eval/evaluate.py data/s1.log -c data/s1.csv -o data/s1.png
python3 eval/evaluate.py data/s1_ha.log -c data/s1_ha.csv -o data/s1_ha.png -m high-accuracy
```

| Argument         | Meaning                                                         |
|------------------|-----------------------------------------------------------------|
| `log`            | Log file; stdin if omitted                                      |
| `-c`, `--csv`    | CSV output (required)                                           |
| `-o`, `--output` | Save the plots instead of showing them                          |
| `-m`, `--mode`   | `default` (±4 %) or `high-accuracy` (±3 %); match `TIMING_BUDGET_US` |
| `--spec`         | Override the datasheet accuracy in %                            |
| `--fov`          | Full field of view in degrees; default 25                       |

### Results

The error is `target - measured`; positive means the sensor reads too short.

| Value      | Meaning                                                             |
|------------|---------------------------------------------------------------------|
| Bias       | Systematic error `target - mean`; corrected by calibration          |
| Std        | Noise σ; reduced by a longer timing budget or [filtering](../filter) |
| RMSE       | Total error ≈ `sqrt(bias² + σ²)`                                    |
| 95 % range | `bias ± 2σ`                                                         |
| OK         | `yes` if the 95 % range lies within the datasheet limit             |

```
High Accuracy Mode: datasheet accuracy ±3 %
 Target   n     Mean    Bias    Std   RMSE        95% range   Spec ±3%  OK
    100 100    100.2    -0.2    1.2    1.2     -2.5 .. +2.1       ±3.0 yes
    200 100    206.2    -6.2    0.8    6.3     -7.9 .. -4.5       ±6.0  no
```

- **Accuracy plot:** bias with `±2σ` band over the target distance and the
  datasheet limit. A band that excludes 0 indicates a systematic error.
- **Field of view plot** (`fov.png`): spot diameter at each distance; the
  target must be larger.
