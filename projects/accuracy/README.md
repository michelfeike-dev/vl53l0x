# Accuracy

Sensor accuracy at stepped target distances: bias, standard deviation and
datasheet limit.

## Hardware

| Component    | Connection                             |
|--------------|----------------------------------------|
| Board        | ESP32-S3                               |
| VL53L0X      | SDA → GPIO 8, SCL → GPIO 9, 3.3 V, GND |
| Start Button | GPIO 14 → GND                          |
| Target       | White, flat, larger than the field of view |

Note: The target must fill the field of view at every distance, otherwise the
sensor measures the background.

## Software

- ESP-IDF 5.3
- Python 3, matplotlib

## Getting Started

### Configuration

| Constant           | Default | Meaning                                      |
|--------------------|---------|----------------------------------------------|
| `OFFSET_MM`        | 28      | Offset from [calibration](../calibration)    |
| `TIMING_BUDGET_US` | 200000  | 33000 = default, 200000 = high accuracy      |
| `DIST_MIN`         | 100     | First target distance in mm                  |
| `DIST_MAX`         | 1200    | Last target distance in mm                   |
| `DIST_STEP`        | 100     | Step in mm                                   |
| `NUM_MEASUREMENTS` | 100     | Readings per distance                        |

### Build and Flash

```sh
cd projects/accuracy
idf.py set-target esp32s3
idf.py build flash monitor
```

### Measurement

1. Place the target at `DIST_MIN` and press the start button.
2. Move the target by `DIST_STEP` and press again, up to `DIST_MAX`.
3. Save the monitor output as `data/s1.log`.

## Evaluation

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install matplotlib
python3 eval/evaluate.py data/s1.log -c data/s1.csv -o data/s1.png -m high-accuracy
```

`-m` is `default` (±4 %) or `high-accuracy` (±3 %), matching
`TIMING_BUDGET_US`.

| Value | Meaning                                       |
|-------|-----------------------------------------------|
| Bias  | `target - mean`, corrected by calibration     |
| Std   | Noise, reduced by timing budget or filtering  |
| OK    | `bias ± 2σ` within the datasheet limit        |

```
 Target   n     Mean    Bias    Std   RMSE        95% range   Spec ±3%  OK
    100 100    100.2    -0.2    1.2    1.2     -2.5 .. +2.1       ±3.0 yes
    200 100    206.2    -6.2    0.8    6.3     -7.9 .. -4.5       ±6.0  no
```
