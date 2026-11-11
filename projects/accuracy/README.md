# Accuracy

Sensor accuracy at stepped target distances: bias, standard deviation and
datasheet limit.

## Hardware

| Component    | Connection                             |
|--------------|----------------------------------------|
| Board        | ESP32-S3                               |
| VL53L0X      | SDA → GPIO 8, SCL → GPIO 9, VCC → 3.3 V, GND → GND|
| Start Pin    | GPIO 14                                |
| Target       | White                                  |

Note: 

[$A_{Target} > A_{FoV}$](../../README.md#field-of-view) 

## Software

- ESP-IDF 5.3
- Python 3, matplotlib
- Official ST VL53L0X API [STSW-IMG005](https://www.st.com/en/embedded-software/stsw-img005.html)
- C++ wrapper [kerikun11/ESP32_VL53L0X](https://github.com/kerikun11/ESP32_VL53L0X)

## Getting Started

### Configuration

| Constant           | Default | Meaning                                      |
|--------------------|---------|----------------------------------------------|
| `OFFSET_MM`        | 28      | Sensor offset [mm]                           |
| `TIMING_BUDGET_US` | 33000   | 33000 = default, 200000 = high accuracy      |
| `DIST_MIN`         | 100     | Target distance minimum [mm]                  |
| `DIST_MAX`         | 1200    | Target distance maximum [mm]                   |
| `DIST_STEP`        | 100     | Delta distance [mm]                                   |
| `NUM_MEASUREMENTS` | 100     | Readings per distance                        |
| `START_PIN`        | 14      | Input         |

### Build and Flash

```sh
cd projects/accuracy
idf.py set-target esp32s3
idf.py build flash monitor
```

### Measurement

1. Place the target at `DIST_MIN`.
2. Negative edge at `START_PIN`.
3. Move the target by `DIST_STEP`, repeat step 2 up to `DIST_MAX`.
4. Save the monitor output as `data/s1.log`.

## Evaluation

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install matplotlib
python3 eval/evaluate.py data/s1.log -c data/s1.csv -o data/s1.png -m default
```

`-m` is `default` (±4 %) or `high-accuracy` (±3 %), matching
`TIMING_BUDGET_US`.

With the target distance $z$ and the readings $x_1 \dots x_n$:

**Bias**: systematic error, corrected by calibration

$$b = \frac{1}{n}\sum_{i=1}^{n}(z - x_i) = z - \bar{x}$$

**Standard deviation**: noise, reduced by timing budget or filtering

$$\sigma = \sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(x_i - \bar{x})^2}$$

**OK**: $b \pm 2\sigma$ (95 % of the readings) lies within the datasheet limit.

```
 Target   n     Mean    Bias    Std   RMSE        95% range   Spec ±3%  OK
    100 100    100.2    -0.2    1.2    1.2     -2.5 .. +2.1       ±3.0 yes
    200 100    206.2    -6.2    0.8    6.3     -7.9 .. -4.5       ±6.0  no
```
