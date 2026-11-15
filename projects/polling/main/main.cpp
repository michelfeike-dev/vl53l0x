#include <cinttypes>
#include <cstddef>
#include <cstdint>

#include "VL53L0X.h"
#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "esp_err.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "median.hpp"

static const char *TAG = "polling";

constexpr int32_t OFFSET_MM = 0;
constexpr std::size_t FILTER_WINDOW = 5;

extern "C" void app_main(void) {
  // I2C
  ESP_LOGI(TAG, "I2C CONFIG");
  i2c_master_bus_config_t bus_cfg = {};
  bus_cfg.i2c_port = I2C_NUM_0;
  bus_cfg.sda_io_num = GPIO_NUM_8;
  bus_cfg.scl_io_num = GPIO_NUM_9;
  bus_cfg.clk_source = I2C_CLK_SRC_DEFAULT;
  bus_cfg.glitch_ignore_cnt = 7;
  bus_cfg.flags.enable_internal_pullup = true;

  i2c_master_bus_handle_t bus = nullptr;
  ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus));

  VL53L0X sensor(bus);

  ESP_LOGI(TAG, "SENSOR INIT");

  if (!sensor.init()) {
    ESP_LOGE(TAG, "INIT FAILED");
    vTaskDelay(portMAX_DELAY);
  }

  ESP_LOGI(TAG, "SENSOR OFFSET");

  int32_t offset_um = OFFSET_MM * 1000;

  if (!sensor.setOffset(offset_um)) {
    ESP_LOGE(TAG, "SENSOR OFFSET FAILED");
    vTaskDelay(portMAX_DELAY);
  }

  uint16_t data = 0;
  MedianFilter<FILTER_WINDOW> filt;

  while (true) {
    if (sensor.read(&data)) {
      ESP_LOGI(TAG, "%" PRIu16 " [mm]", filt.update(data));
    } else {
      filt.clean();
      ESP_LOGE(TAG, "ERROR");
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}
