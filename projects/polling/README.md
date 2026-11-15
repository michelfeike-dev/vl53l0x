# Polling

Continuous measurement with noise compensation using a median filter. 

## Hardware

| Component    | Connection                             |
|--------------|----------------------------------------|
| Board        | ESP32-S3                               |
| VL53L0X      | SDA → GPIO 8<br>SCL → GPIO 9<br>VCC → 3.3 V<br>GND → GND|

## Software

- ESP-IDF 5.3

## Getting Started

### Configuration

| Constant         | Default | Meaning                                    |
|------------------|---------|--------------------------------------------|
| `OFFSET_MM`      | 0       | Offset from [calibration](../calibration)  |
| `FILTER_WINDOW`  | 5       | Median window (odd)                        |

### Build and Flash

```sh
cd projects/polling
idf.py set-target esp32s3
idf.py build flash monitor
```

### Output

```text
I (1234) polling: 512 [mm]
```

### Error Handling

`VL53L0X::ReadStatus`:

| Status       | Cause                                         | Reaction                           |
|--------------|-----------------------------------------------|------------------------------------|
| `Done`       | Valid range                                   | Filter and log the value           |
| `OutOfRange` | No valid target (sigma, signal or phase fail) | Clear the filter, log `NO TARGET`  |
| `BusError`   | I2C or API error                              | Clear the filter, log `BUS ERROR`  |
