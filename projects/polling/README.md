# Polling

Continuous measurement with a median filter. The sensor is read in a loop,
each reading passes through the filter and the result is logged.

```cpp
MedianFilter<5> filt;                  // N odd
uint16_t filtered = filt.update(raw);
filt.clean();                          // reset after a failed reading
```

## Hardware

| Component    | Connection                             |
|--------------|----------------------------------------|
| Board        | ESP32-S3                               |
| VL53L0X      | SDA → GPIO 8<br>SCL → GPIO 9<br>VCC → 3.3 V<br>GND → GND|

## Software

- ESP-IDF 5.3

## Getting Started

### Configuration

| Constant        | Default | Meaning                                   |
|-----------------|---------|-------------------------------------------|
| `OFFSET_MM`     | 0       | Offset from [calibration](../calibration) |
| `FILTER_WINDOW` | 5       | Median window, odd                        |

### Build and Flash

```sh
cd projects/polling
idf.py set-target esp32s3
idf.py build flash monitor
```

### Output

One line per reading, about every 45 ms (33 ms timing budget plus 10 ms
delay):

```text
I (1234) polling: 512 [mm]
```

A failed reading logs `ERROR` and clears the filter with `filt.clean()`.
The next valid reading starts a new window, so no stale values from before
the error enter the median.

To filter a recorded log offline, see [accuracy](../accuracy#median-filter).
