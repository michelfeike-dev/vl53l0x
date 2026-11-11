# Filter

Noise reduction using a median filter, on the device or offline.

```cpp
MedianFilter<5> filt;                  // N odd
uint16_t filtered = filt.update(raw);
```

## Hardware

| Component    | Connection                             |
|--------------|----------------------------------------|
| Board        | ESP32-S3                               |
| VL53L0X      | SDA → GPIO 8, SCL → GPIO 9, VCC → 3.3 V, GND → GND|

## Software

- ESP-IDF 5.3
- Python 3, matplotlib

## Getting Started

### Configuration

| Constant           | Default | Meaning                                   |
|--------------------|---------|-------------------------------------------|
| `OFFSET_MM`        | 28      | Offset from [calibration](../calibration) |
| `FILTER_WINDOW`    | 5       | Median window, odd                        |
| `DIST_MIN`         | 100     | First target distance in mm               |
| `DIST_MAX`         | 1200    | Last target distance in mm                |
| `DIST_STEP`        | 100     | Step in mm                                |
| `NUM_MEASUREMENTS` | 100     | Readings per distance                     |

### Build and Flash

```sh
cd projects/filter
idf.py set-target esp32s3
idf.py build flash monitor
```

### Measurement

Same procedure as in [accuracy](../accuracy). Save the monitor output as
`data/s1.log`.

## Evaluation

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install matplotlib

# Filtered on the device (default timing budget)
python3 ../accuracy/eval/evaluate.py data/s1.log -c data/s1.csv -o data/s1.png -m default

# Filtered offline, raw log of accuracy, window -n
python3 eval/filter.py ../accuracy/data/s1.log -n 5 -c data/s1_med5.csv -p data/s1_med5.png -m high-accuracy
```

The output matches [accuracy](../accuracy#evaluation). The median reduces the
standard deviation, not the bias.
