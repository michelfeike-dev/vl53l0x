# VL53L0X Driver for ESP-IDF

C++ driver for the STMicroelectronics VL53L0X time-of-flight distance sensor,
packaged as an ESP-IDF component.

The driver wraps the official ST VL53L0X API and uses the ESP-IDF I2C master
driver (`driver/i2c_master.h`), so the sensor can share an I2C bus with other
devices.

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Offset Calibration](#offset-calibration)
- [Timing Budget](#timing-budget)
- [Examples](#examples)
- [Repository Structure](#repository-structure)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Features

- I2C master driver API of ESP-IDF 5.x and later, bus created by the application
- Single ranging measurements, polled or interrupt-driven via the GPIO1 pin
- Optional hardware reset via the XSHUT pin
- Configurable measurement timing budget
- Range offset calibration, applied in `init()` or at runtime
- Configurable I2C address to run several sensors on one bus

## Requirements

| Item     | Version / Notes                                      |
|----------|------------------------------------------------------|
| ESP-IDF  | 5.3 or later; the examples build with v6.1           |
| Target   | ESP32-series SoCs; the examples build for ESP32-S3 |
| Hardware | VL53L0X module, connected via I2C (3.3 V)            |

## Installation

### ESP Component Manager

Add the component to your project's `main/idf_component.yml`:

```yaml
dependencies:
  vl53l0x:
    git: git@github.com:michelfeike-dev/vl53l0x.git
    version: v1.3.1
```

### Local Component

Alternatively, clone the repository into the `components/` directory of your
project:

```sh
git clone git@github.com:michelfeike-dev/vl53l0x.git components/vl53l0x
```

In both cases add `vl53l0x` to `REQUIRES` of the component that uses the
driver:

```cmake
idf_component_register(SRCS "main.cpp"
                       REQUIRES vl53l0x)
```

## Quick Start

Create the I2C bus in your application and pass its handle to the sensor:

```cpp
#include <cinttypes>

#include "VL53L0X.h"
#include "driver/i2c_master.h"
#include "esp_err.h"
#include "esp_log.h"

static const char *TAG = "app";

extern "C" void app_main(void) {
  i2c_master_bus_config_t bus_cfg = {};
  bus_cfg.i2c_port = I2C_NUM_0;
  bus_cfg.sda_io_num = GPIO_NUM_21;
  bus_cfg.scl_io_num = GPIO_NUM_22;
  bus_cfg.clk_source = I2C_CLK_SRC_DEFAULT;
  bus_cfg.glitch_ignore_cnt = 7;
  bus_cfg.flags.enable_internal_pullup = true;

  i2c_master_bus_handle_t bus = nullptr;
  ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus));

  VL53L0X sensor(bus);
  if (!sensor.init()) {
    ESP_LOGE(TAG, "VL53L0X init failed");
    return;
  }

  uint16_t range_mm = 0;
  if (sensor.read(&range_mm))
    ESP_LOGI(TAG, "Range: %" PRIu16 " mm", range_mm);
}
```

The internal pull-ups of the ESP32 are weak. Most VL53L0X breakout boards
have their own pull-up resistors; on a bare sensor add external ones
(e.g. 4.7 kΩ).

## API Reference

All methods return `true` on success. Errors of the ST API are logged with the
tag `VL53L0X`. The read methods also return `false` if the sensor reports an
invalid range status, e.g. when no target is within range.

### Constructor

```cpp
VL53L0X(i2c_master_bus_handle_t i2c_bus,
        gpio_num_t gpio_xshut = GPIO_NUM_MAX,
        gpio_num_t gpio_gpio1 = GPIO_NUM_MAX,
        uint32_t scl_speed_hz = 400000,
        int32_t offset_mikro_meter = 0);
```

| Parameter            | Meaning                                                          |
|----------------------|------------------------------------------------------------------|
| `i2c_bus`            | Bus handle from `i2c_new_master_bus()`                           |
| `gpio_xshut`         | XSHUT pin for hardware reset; `GPIO_NUM_MAX` if not connected    |
| `gpio_gpio1`         | GPIO1 pin for the measurement-ready interrupt; `GPIO_NUM_MAX` if not connected |
| `scl_speed_hz`       | I2C clock of this device                                         |
| `offset_mikro_meter` | Range offset in µm, applied in `init()`                          |

### Methods

| Method                                 | Description                                                         |
|----------------------------------------|---------------------------------------------------------------------|
| `bool init()`                          | Adds the device to the bus, runs the ST calibration sequence, sets a 33 ms timing budget and applies the constructor offset |
| `bool read(uint16_t *mm)`              | Single measurement in mm; uses the interrupt if GPIO1 is configured, polling otherwise |
| `bool readSingleWithPolling(uint16_t *mm)`   | Single measurement, polling the sensor status                 |
| `bool readSingleWithDelay(uint16_t *mm)`     | Single measurement, waiting for the timing budget              |
| `bool readSingleWithInterrupt(uint16_t *mm)` | Single measurement, waiting for the GPIO1 interrupt            |
| `bool setTimingBudget(uint32_t us)`    | Sets the measurement timing budget in µs                            |
| `bool setOffset(int32_t um)`           | Sets the range offset in µm                                         |
| `bool setDeviceAddress(uint8_t addr)`  | Changes the 7-bit I2C address (default `0x29`)                      |
| `bool reset()`                         | Software reset; falls back to a hardware reset if it fails          |
| `bool hardwareReset()`                 | Resets the sensor via XSHUT                                         |
| `bool softwareReset()`                 | Resets the sensor via I2C                                           |

The I2C address and the offset are held in the sensor's RAM. Apply them again
after every reset or power cycle.

## Offset Calibration

Each sensor has a small range offset that depends on the part and its
mounting (cover glass, housing). Determine it once per sensor with the
[calibration example](examples/calibration) and apply it in your application.

The value is given in micrometers and follows the ST convention
`offset = actual - measured`; the sensor adds it to every range. The valid
range is -512 mm to +511 mm.

```cpp
// Via the constructor, applied in init()
VL53L0X sensor(bus, GPIO_NUM_MAX, GPIO_NUM_MAX, 400000, -12 * 1000);
sensor.init();

// Or at runtime, after init()
sensor.setOffset(-12 * 1000);
```

## Timing Budget

The timing budget is the time the sensor spends on one measurement. A longer
budget reduces the noise but lowers the measurement rate. `init()` sets
33 ms. The datasheet specifies these ranging profiles for a white target:

| Profile       | Timing budget | Range    | Accuracy |
|---------------|---------------|----------|----------|
| Default       | 30 ms         | 1.2 m    | ±4 %     |
| High accuracy | 200 ms        | 1.2 m    | ±3 %     |

```cpp
sensor.setTimingBudget(200000); // high accuracy
```

Use the [accuracy example](examples/accuracy) to verify the accuracy in your
own setup.

## Examples

Each example is a standalone ESP-IDF project with its own documentation.

| Example                             | Description                                                  |
|-------------------------------------|--------------------------------------------------------------|
| [calibration](examples/calibration) | Determines and applies the range offset                      |
| [accuracy](examples/accuracy)       | Measures and evaluates the accuracy at stepped distances     |
| [filter](examples/filter)           | Applies a median filter to the readings and evaluates the result |

```sh
git clone git@github.com:michelfeike-dev/vl53l0x.git
cd vl53l0x/examples/calibration
idf.py set-target esp32s3
idf.py build flash monitor
```

The examples reference the driver from the repository root via
`EXTRA_COMPONENT_DIRS`, so they build without the component manager.
Measurement logs and evaluation results (`data/*.log`, `*.csv`, `*.png`) are
ignored by Git.

## Repository Structure

```
vl53l0x/
├── inc/VL53L0X.h          Driver class (header-only)
├── api/                   STMicroelectronics VL53L0X API
│   ├── core/              Device-independent API
│   └── platform/          I2C platform layer for ESP-IDF
├── examples/
│   ├── calibration/       Offset calibration
│   ├── accuracy/          Accuracy measurement and evaluation script
│   └── filter/            Median filter and evaluation script
├── CMakeLists.txt         ESP-IDF component definition
├── idf_component.yml      Component manager manifest
└── CHANGELOG.md
```

The ST API is the official
[STSW-IMG005](https://www.st.com/en/embedded-software/stsw-img005.html)
package (core and platform layer). The platform layer is adapted to the
ESP-IDF I2C master driver.

## License

MIT, see [LICENSE](LICENSE).

## Acknowledgements

Based on [kerikun11/ESP32_VL53L0X](https://github.com/kerikun11/ESP32_VL53L0X),
ported to the ESP-IDF I2C master driver and extended with offset calibration.
