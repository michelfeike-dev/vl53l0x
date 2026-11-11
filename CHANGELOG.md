# Changelog

## Unreleased

- Add median filter example (`examples/filter`) with offline filter script
- Remove the polling example (`examples/polling`); the Quick Start in the
  README covers the minimal use case
- Remove the legacy GNU Make (`component.mk`) and PlatformIO (`library.json`)
  build files; ESP-IDF 5.3 or later builds with CMake only
- accuracy example: evaluation script `eval/evaluate.py` with datasheet
  limits per ranging profile and field of view plot
- Examples: `constexpr` configuration constants, explicit includes and
  portable format specifiers
- Ignore measurement logs and evaluation results (`data/*.log`, `*.csv`,
  `*.png`) in Git
- Rework the documentation of the component and all examples

## v1.3.1

- accuracy example: start at `TARGET_DISTANCE_MIN` and restart the series
  after `TARGET_DISTANCE_MAX`

## v1.3.0

- Add accuracy measurement example (`examples/accuracy`)

## v1.2.0

- Add offset calibration example (`examples/calibration`)
- Document offset handling in the README

## v1.1.0

- Apply the constructor offset in `init()`
- Accept negative offsets in the constructor

## v1.0.0

- Initial import based on kerikun11/ESP32_VL53L0X
- Port to the ESP-IDF I2C master driver
- Map I2C NACK to control interface error
- Add `setOffset()` and constructor offset parameter
