# vl53l0x

C++ VL53L0X driver as an ESP-IDF component

Based on [kerikun11/ESP32_VL53L0X](https://github.com/kerikun11/ESP32_VL53L0X),
ported to the ESP-IDF I2C master driver and extended with offset calibration.

## Dependency

- [ESP-IDF](https://github.com/espressif/esp-idf) >= 5.3

## Installation

Add the component to your project's `main/idf_component.yml`:

```yaml
dependencies:
  vl53l0x:
    git: git@github.com:michelfeike-dev/vl53l0x.git
    version: v1.2.0
```

and add `vl53l0x` to `REQUIRES` in your component's `CMakeLists.txt`.

## Usage

The driver uses the ESP-IDF I2C master driver (`driver/i2c_master.h`).
Create the bus in your application and pass its handle to the sensor:

```cpp
i2c_master_bus_config_t bus_cfg = {};
bus_cfg.i2c_port = I2C_NUM_0;
bus_cfg.sda_io_num = GPIO_NUM_21;
bus_cfg.scl_io_num = GPIO_NUM_22;
bus_cfg.clk_source = I2C_CLK_SRC_DEFAULT;
bus_cfg.glitch_ignore_cnt = 7;
bus_cfg.flags.enable_internal_pullup = true;
i2c_master_bus_handle_t bus = NULL;
ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus));

VL53L0X vl(bus);
if (vl.init()) {
  uint16_t mm;
  vl.read(&mm);
}
```

## Offset

Each sensor has a small range offset that depends on the part and its
mounting (cover glass, housing). Determine it once with the
[calibration example](examples/calibration) and apply it in your application.
The value is in micrometers and follows the ST convention
`offset = actual - measured`; the sensor adds it to every range.

```cpp
// via the constructor, applied in init()
VL53L0X vl(bus, GPIO_NUM_MAX, GPIO_NUM_MAX, 400000, -12 * 1000);
vl.init();

// or at runtime, after init()
vl.setOffset(-12 * 1000);
```

The offset is not stored on the sensor and must be applied after every reset.

## Examples

| Example                             | Description                          |
|-------------------------------------|--------------------------------------|
| [polling](examples/polling)         | Continuous distance measurement      |
| [calibration](examples/calibration) | Determine and apply the range offset |

```sh
git clone git@github.com:michelfeike-dev/vl53l0x.git
cd vl53l0x/examples/calibration
idf.py build flash monitor
```

## API using

[STMicroelectronics official VL53L0X API](http://www.st.com/content/st_com/en/products/embedded-software/proximity-sensors-software/stsw-img005.html)

- core
- platform

## License

MIT, see [LICENSE](LICENSE).
