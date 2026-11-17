# Accuracy

Sensor accuracy at stepped target distances: bias, standard deviation and
datasheet limit.

## Hardware

| Component    | Connection                             |
|--------------|----------------------------------------|
| Board        | ESP32-S3                               |
| VL53L0X      | SDA → GPIO 8<br>SCL → GPIO 9<br>VCC → 3.3 V<br>GND → GND|
| Start Pin    | GPIO 14                                |
| [Target](../../README.md#field-of-view)      | White                                  |

Note: 

$A_{Target} > A_{FoV}$ 

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
| `TIMING_BUDGET_US` | 33000   | default mode = 33000us<br> high accuracy mode = 200000us      |
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
3. Move the target by `DIST_STEP`, up to `DIST_MAX`
4. Save the monitor output as `data/s1.log`.

## Evaluation

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install matplotlib
python3 eval/evaluate.py data/s1.log -c data/s1.csv -o data/s1.png -m default
```

| Parameter        | Required | Description                                                    |
|------------------|----------|----------------------------------------------------------------|
| `log`            | no       | Input file of the measurement            |
| `-c`, `--csv`    | yes      | Output CSV file                                       |
| `-o`, `--output` | no       | Save accuracy and field of view |
| `-m`, `--mode`   | no       | `default` (±4 %)<br>`high-accuracy` (±3 %)<br>matching `TIMING_BUDGET_US`<br>default `default` |
| `--spec`         | no       | Override the datasheet accuracy [%]                            |
| `--fov`          | no       | Full field of view [°]<br>default 25                             |

**Target distance**: $z$ 

**Measurements**: $x_1 \dots x_n$:

**Bias**:

$$b = \frac{1}{n}\sum_{i=1}^{n}(z - x_i) = z - \bar{x}$$

**Standard deviation**:

$$\sigma = \sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(x_i - \bar{x})^2}$$

**RMSE**:

$$\mathrm{RMSE} = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(z - x_i)^2} \approx \sqrt{b^2 + \sigma^2}$$

```
 Target   n     Mean    Bias    Std   RMSE        95% range   Spec ±3%  OK
    100 100    100.2    -0.2    1.2    1.2     -2.5 .. +2.1       ±3.0 yes
    200 100    206.2    -6.2    0.8    6.3     -7.9 .. -4.5       ±6.0  no
```

## Improvements

### Median-Filter

A sliding median over $N$ readings reduces $\sigma$: 

$$\tilde{x}_k = \mathrm{median}(x_{k-N+1}, \dots, x_k)$$

The median follows a change of the distance with a delay of $\frac{N-1}{2} \cdot T$:

**Timing**: $T \approx$ `TIMING_BUDGET_US`

| Timing budget | Delay $N = 3$     | Delay $N = 5$ |
|---------------|---------|---------------|
| 33 ms         | ≈ 33 ms | ≈ 66 ms       |
| 200 ms        | ≈ 200 ms | ≈ 400 ms     |

## Measurement

<img src="doc/s1_raw.png" alt="Raw" width="49%"> <img src="doc/s1_ha.png" alt="Median N=5" width="49%">

<img src="doc/s1_med3.png" alt="Raw" width="49%"> <img src="doc/s1_med5.png" alt="Median N=5" width="49%">

#### What are the results?
- Default mode: the 95 % range (bias ± 2σ) stays within the datasheet limit
  of ±4 % up to 700 mm for sensor 2. Sensor 1 slightly exceeds it at 200 and
  300 mm (4.3 % and 4.4 %).
- High accuracy mode: the standard deviation drops by a factor of 2 to 2.5,
  close to the expected √6 ≈ 2.4. The bias stays the same, because it is a
  systematic error of the setup.
- The bias crosses zero between 550 and 650 mm.
- Beyond 700 mm the sensor reads up to 46 mm too short. Worst case: 6.7 %
  at 1000 mm.
- At 1200 mm the sensor reaches its range limit: the bias drops again, but
  the standard deviation rises to 12–20 mm in default mode.

#### Why does the error grow with distance?
- The sensor has a 25° [FoV](../../README.md#field-of-view). Its light spot grows linearly with the
distance, with a diameter of about 0.44 × distance.
- The lower edge of the cone hits the ground from about 180 mm. The ground
  lies between sensor and target, so it pulls the reading towards shorter
  distances.
- The echo of the target gets weaker with 1/d², so the share of the ground
  grows with the distance.
- From about 700 mm the light spot is larger than the A4 sheet.
What are the error sources?
- Random sensor noise
- Ground and background inside the field of view
- Target smaller than the light spot
- Individual sensor offsets within the datasheet specification
- Measurement setup (target distance, alignment of sensor and target)

#### How can I improve accuracy?
- Mount the sensor at least half a spot diameter above the ground
  (≥ 266 mm for 1200 mm)
- Use a target larger than the light spot (≥ 532 mm for 1200 mm)
- Offset and crosstalk calibration
- High accuracy mode or averaging against random noise
- Median filter against outliers