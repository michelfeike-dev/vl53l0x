# Median Filter Example

Applies a sliding median filter to the distance readings and evaluates the
filtered result with the same stepped target distances as the
[accuracy](../accuracy) example. A median filter suppresses single outliers
without shifting the mean like an average over outliers would.

The filter can be evaluated in two ways:

- **On the device:** the firmware filters the readings before logging them.
- **Offline:** `eval/filter.py` applies the same filter to a raw log, e.g. of
  the accuracy example, so several window sizes can be compared on one
  measurement series.

## How It Works

1. Initializes the sensor with the default timing budget (33 ms) and sets the
   offset `OFFSET_MM`.
2. On every falling edge of the start button it logs the current target
   distance, resets the filter and logs `NUM_MEASUREMENTS` filtered readings.
3. The target distance advances by `DIST_STEP` per button press, from
   `DIST_MIN` to `DIST_MAX`, then starts over.

The filter is implemented in the `median` component
(`components/median/include/median.hpp`):

```cpp
MedianFilter<5> filt;
uint16_t filtered = filt.update(raw);
```

`MedianFilter<N>` keeps the last `N` values in a ring buffer and returns
their median. Until the window is full, the median is taken over the values
received so far. `N` must be odd, which is checked at compile time.

## Hardware

| Signal       | GPIO | Notes                                     |
|--------------|------|-------------------------------------------|
| I2C SDA      | 8    | internal pull-up enabled                  |
| I2C SCL      | 9    | internal pull-up enabled                  |
| Start button | 14   | active low, internal pull-up; press = GND |

The start pin is set by `START_PIN` at the top of `main/filter.cpp`, the I2C
pins in the bus configuration in `app_main()`. Adjust them for your board.

## Configuration

Set these constants at the top of `main/filter.cpp`:

| Constant           | Default | Meaning                                                     |
|--------------------|---------|-------------------------------------------------------------|
| `START_PIN`        | 14      | Start button                                                |
| `OFFSET_MM`        | 28      | Offset in mm from the [calibration](../calibration) example |
| `FILTER_WINDOW`    | 5       | Median filter window, odd                                   |
| `DIST_MIN`         | 100     | First target distance in mm                                 |
| `DIST_MAX`         | 1200    | Last target distance in mm                                  |
| `DIST_STEP`        | 100     | Step between target distances in mm                         |
| `NUM_MEASUREMENTS` | 100     | Readings per target distance                                |

## Build and Flash

```sh
idf.py set-target esp32s3
idf.py build flash monitor
```

## Procedure

The procedure and the measurement setup are the same as in the
[accuracy](../accuracy#measurement-setup) example: place the target at
`DIST_MIN`, press the start button, move the target by `DIST_STEP` and press
again. Save the monitor output in `data/`, e.g. `data/s1.log`.

The log format is the same as in the accuracy example, so both evaluation
scripts accept it.

## Evaluation

Both scripts need Python 3 with matplotlib, see
[accuracy](../accuracy#setup).

### Filtered on the Device

Evaluate the log of this example with the script of the accuracy example.
The firmware uses the default timing budget, so use `-m default`:

```sh
python3 ../accuracy/eval/evaluate.py data/s1.log -c data/s1.csv -o data/s1.png -m default
```

### Filtered Offline

`eval/filter.py` reads a raw log, applies a median filter with window `-n`
per target distance (reset at every `TARGET DISTANCE` line, like the
firmware) and evaluates the filtered readings. It prints the same table and
writes the same CSV format as `evaluate.py`, so the filtered and the raw
results can be compared directly.

```sh
python3 eval/filter.py ../accuracy/data/s1_ha.log -n 5 -c data/s1_ha_med5.csv -p data/s1_ha_med5.png -m high-accuracy
python3 eval/filter.py ../accuracy/data/s1.log -n 3 -c data/s1_med3.csv -o data/s1_med3.log
```

| Argument         | Required | Meaning                                                           |
|------------------|----------|-------------------------------------------------------------------|
| `log`            | no       | Raw log file; reads stdin if omitted                              |
| `-n`, `--window` | yes      | Median filter window, odd and > 0                                 |
| `-c`, `--csv`    | yes      | CSV file for the values of the filtered readings                  |
| `-p`, `--plot`   | no       | Save the plot instead of showing it                               |
| `-o`, `--output` | no       | Save the filtered log, in the same format as the input            |
| `-m`, `--mode`   | no       | Ranging profile of the log: `default` or `high-accuracy`          |
| `--spec`         | no       | Override the datasheet accuracy in percent of the target distance |

The CSV columns are described in the [accuracy](../accuracy#values) example.
CSV, PNG and log files in `data/` are ignored by Git.

Example (raw log of the accuracy example, high accuracy mode, N = 5):

```
High Accuracy Mode: datasheet accuracy ±3 %
Median filter N=5
 Target   n     Mean    Bias    Std   RMSE        95% range   Spec ±3%  OK
    100 100    100.3    -0.3    1.1    1.2     -2.6 .. +1.9       ±3.0 yes
    200 100    206.2    -6.2    0.6    6.2     -7.4 .. -5.0       ±6.0  no
    300 100    309.9    -9.9    0.9    9.9    -11.6 .. -8.1       ±9.0  no
```

Compared with the raw readings, the median reduces the standard deviation
but does not change the bias. A systematic error has to be corrected by
calibration, not by filtering.

## Related Examples

- [accuracy](../accuracy): raw measurement series and evaluation script
- [calibration](../calibration): determine `OFFSET_MM`
