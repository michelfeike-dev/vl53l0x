# Changelog

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
