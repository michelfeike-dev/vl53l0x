#include <cinttypes>
#include <cstdint>
#include <numeric>
#include <vector>

#include "VL53L0X.h"
#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "esp_err.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "calibration";

constexpr gpio_num_t START_PIN = GPIO_NUM_14;
constexpr int TARGET_DISTANCE = 100;
constexpr int NUM_MEASUREMENTS = 100;

extern "C" void app_main(void) {
  // GPIO
  ESP_LOGI(TAG, "GPIO CONFIG");
  gpio_config_t io_conf = {};
  io_conf.mode = GPIO_MODE_INPUT;
  io_conf.pin_bit_mask = (1ULL << START_PIN);
  io_conf.pull_up_en = GPIO_PULLUP_ENABLE;
  io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
  gpio_config(&io_conf);

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
    ESP_LOGE(TAG, "SENSOR INIT FAILED");
    vTaskDelay(portMAX_DELAY);
  }

  ESP_LOGI(TAG, "OFFSET CALIBRATION");
  ESP_LOGI(TAG, "Target distance: %d mm", TARGET_DISTANCE);
  ESP_LOGI(TAG, "Target color: white");
  ESP_LOGI(TAG, "Number of measurements: %d", NUM_MEASUREMENTS);
  ESP_LOGI(TAG, "Type: Mean Offset");
  ESP_LOGI(TAG, "START CALIBRATION: F_TRIG PIN%d", static_cast<int>(START_PIN));

  uint16_t data;
  std::vector<uint16_t> meas;
  int input;
  int last_input = 1;

  while (true) {
    input = gpio_get_level(START_PIN);

    // 0 := Low; 1 := High

    if ((input == 0) && (last_input == 1)) {
      data = 0;
      meas.clear();

      // Measure without a previously applied offset
      if (!sensor.setOffset(0)) {
        ESP_LOGI(TAG, "RESET OFFSET FAILED");
        return;
      }

      for (int i = 0; i < NUM_MEASUREMENTS; i++) {
        if (sensor.read(&data)) {
          ESP_LOGI(TAG, "MEASUREMENT %d: %" PRIu16 " [mm]", i, data);
          meas.push_back(data);
          vTaskDelay(pdMS_TO_TICKS(10));
        } else {
          ESP_LOGI(TAG, "CALIBRATION FAILED");
          return;
        }
      }

      ESP_LOGI(TAG, "CALIBRATION SUCCESSFUL");

      uint64_t sum = std::accumulate(meas.begin(), meas.end(), 0ULL);
      // ST convention: offset = target - measured, the sensor adds it to each
      // range
      int32_t mean_mm = static_cast<int32_t>(sum / meas.size());
      int32_t offset_mm = static_cast<int32_t>(TARGET_DISTANCE) - mean_mm;

      ESP_LOGI(TAG, "OFFSET = %" PRId32 " [mm]", offset_mm);

      int32_t offset_um = offset_mm * 1000;

      ESP_LOGI(TAG, "STORE DATA SENSOR");

      if (sensor.setOffset(offset_um)) {
        sensor.read(&data);
        ESP_LOGI(TAG, "REFERENCE MEASUREMENT: %" PRIu16 " [mm]", data);
      } else {
        ESP_LOGI(TAG, "STORE DATA SENSOR FAILED");
      }
    }

    last_input = input;

    vTaskDelay(pdMS_TO_TICKS(10));
  }
}