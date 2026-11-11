# Median Filter

Applies a sliding median filter to the readings and evaluates the result at
the same stepped target distances as the [accuracy](../accuracy) project. The
median suppresses outliers without shifting the mean.

The filter is evaluated on the device (firmware) or offline
(`eval/filter.py` on a raw accuracy log, to compare window sizes).

```cpp
MedianFilter<5> filt;                  // components/median, N odd
uint16_t filtered = filt.update(raw);
```

## Hardware

| Component    | Connection                                          |
|--------------|-----------------------------------------------------|
| Board        | ESP32-S3                                            |
| VL53L0X      | SDA → GPIO 8, SCL → GPIO 9, 3.3 V, GND              |
| Start Button | GPIO 14 → GND (active low, internal pull-up)        |
| Target       | White, flat, larger than the field of view at `DIST_MAX` |

Same measurement setup as in [accuracy](../accuracy#hardware).

## Getting Started

### Requirements

- ESP-IDF 5.3 or later
- Python 3 with matplotlib for the evaluation

### Configuration

Constants at the top of `main/filter.cpp`:

| Constant           | Default | Meaning                                                     |
|--------------------|---------|-------------------------------------------------------------|
| `START_PIN`        | 14      | Start button                                                |
| `OFFSET_MM`        | 28      | Offset in mm from the [calibration](../calibration) project |
| `FILTER_WINDOW`    | 5       | Median filter window, odd                                   |
| `DIST_MIN`         | 100     | First target distance in mm                                 |
| `DIST_MAX`         | 1200    | Last target distance in mm                                  |
| `DIST_STEP`        | 100     | Step between target distances in mm                         |
| `NUM_MEASUREMENTS` | 100     | Readings per target distance                                |

The firmware uses the default timing budget (33 ms).

### Build and Flash

```sh
cd projects/filter
idf.py set-target esp32s3
idf.py build flash monitor
```

## Measurement

Same procedure as in [accuracy](../accuracy#measurement): place the target at
`DIST_MIN`, press the start button, move by `DIST_STEP`, repeat. Save the
monitor output in `data/`, e.g. `data/s1.log`.

## Evaluation

### Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install matplotlib
```

### Filtered on the Device

```sh
python3 ../accuracy/eval/evaluate.py data/s1.log -c data/s1.csv -o data/s1.png -m default
```

### Filtered Offline

```sh
python3 eval/filter.py ../accuracy/data/s1_ha.log -n 5 -c data/s1_ha_med5.csv -p data/s1_ha_med5.png -m high-accuracy
```

| Argument         | Meaning                                         |
|------------------|-------------------------------------------------|
| `log`            | Raw log file; stdin if omitted                  |
| `-n`, `--window` | Median filter window, odd (required)            |
| `-c`, `--csv`    | CSV output (required)                           |
| `-p`, `--plot`   | Save the plot instead of showing it             |
| `-o`, `--output` | Save the filtered log                           |
| `-m`, `--mode`   | `default` or `high-accuracy`                    |
| `--spec`         | Override the datasheet accuracy in %            |

### Results

Output and CSV match the [accuracy](../accuracy#results) evaluation, so raw
and filtered results compare directly:

```
High Accuracy Mode: datasheet accuracy ±3 %
Median filter N=5
 Target   n     Mean    Bias    Std   RMSE        95% range   Spec ±3%  OK
    100 100    100.3    -0.3    1.1    1.2     -2.6 .. +1.9       ±3.0 yes
    200 100    206.2    -6.2    0.6    6.2     -7.4 .. -5.0       ±6.0  no
```

The median reduces the standard deviation but not the bias. A systematic
error has to be corrected by calibration, not by filtering.
