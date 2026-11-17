#include <cinttypes>
#include <cstdint>

#include "VL53L0X.h"
#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "esp_err.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "level";

constexpr int NUM_SENSORS = 4;
constexpr gpio_num_t START_PIN = GPIO_NUM_14;
constexpr gpio_num_t XSHUT[NUM_SENSORS] = {GPIO_NUM_4, GPIO_NUM_5, GPIO_NUM_6,
                                           GPIO_NUM_7};
constexpr int32_t OFFSET_MM[NUM_SENSORS] = {14, 28, 28, 20};
constexpr uint8_t I2C_ADDRESS[NUM_SENSORS] = {0x30, 0x31, 0x32, 0x33};
constexpr int DEG_MIN = -60, DEG_MAX = 60, DELTA_DEG = 15;
constexpr int NUM_MEASUREMENTS = 100;

static_assert(DEG_MIN < DEG_MAX, "RANGE ERROR");

extern "C" void app_main(void) {
  // GPIO
  ESP_LOGI(TAG, "GPIO CONFIG");
  gpio_config_t io_conf = {};
  io_conf.mode = GPIO_MODE_INPUT;
  io_conf.pin_bit_mask = (1ULL << START_PIN);
  io_conf.pull_up_en = GPIO_PULLUP_ENABLE;
  io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;
  gpio_config(&io_conf);

  // Hold all sensors in reset until each one gets its own address
  for (gpio_num_t pin : XSHUT) {
    gpio_set_direction(pin, GPIO_MODE_OUTPUT);
    gpio_set_level(pin, 0);
  }

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

  VL53L0X s1(bus, XSHUT[0]);
  VL53L0X s2(bus, XSHUT[1]);
  VL53L0X s3(bus, XSHUT[2]);
  VL53L0X s4(bus, XSHUT[3]);
  VL53L0X *sensors[NUM_SENSORS] = {&s1, &s2, &s3, &s4};

  ESP_LOGI(TAG, "SENSOR INIT");

  for (int i = 0; i < NUM_SENSORS; i++) {
    if (!sensors[i]->init() || !sensors[i]->setDeviceAddress(I2C_ADDRESS[i])) {
      ESP_LOGE(TAG, "SENSOR %d INIT FAILED", i);
      vTaskDelay(portMAX_DELAY);
    }
  }

  ESP_LOGI(TAG, "SENSOR OFFSET");

  for (int i = 0; i < NUM_SENSORS; i++) {
    if (!sensors[i]->setOffset(OFFSET_MM[i] * 1000)) {
      ESP_LOGE(TAG, "SENSOR %d OFFSET FAILED", i);
      vTaskDelay(portMAX_DELAY);
    }
  }

  ESP_LOGI(TAG, "LEVEL DEFINITION MEASUREMENT");
  ESP_LOGI(TAG, "Minimum angle: %d deg", DEG_MIN);
  ESP_LOGI(TAG, "Maximum angle: %d deg", DEG_MAX);
  ESP_LOGI(TAG, "Delta angle: %d deg", DELTA_DEG);
  ESP_LOGI(TAG, "Target color: white");
  ESP_LOGI(TAG, "Number of measurements: %d", NUM_MEASUREMENTS);
  ESP_LOGI(TAG, "Out of range is logged as 0");
  ESP_LOGI(TAG, "START MEASUREMENT: F_TRIG PIN%d", static_cast<int>(START_PIN));

  uint16_t data[NUM_SENSORS];
  int input;
  int last_input = 1;
  int target_angle = DEG_MIN;

  while (true) {
    input = gpio_get_level(START_PIN);

    // 0 := Low; 1 := High

    if ((input == 0) && (last_input == 1)) {
      ESP_LOGI(TAG, "TARGET ANGLE: %d", target_angle);

      for (int i = 0; i < NUM_MEASUREMENTS; i++) {
        for (int j = 0; j < NUM_SENSORS; j++) {
          switch (sensors[j]->read(&data[j])) {
          case VL53L0X::ReadStatus::Done:
            break;

          case VL53L0X::ReadStatus::OutOfRange:
            ESP_LOGW(TAG, "SENSOR %d NO TARGET", j);
            data[j] = 0;
            break;

          case VL53L0X::ReadStatus::BusError:
            ESP_LOGE(TAG, "SENSOR %d BUS ERROR", j);
            vTaskDelay(portMAX_DELAY);
            break;
          }
          vTaskDelay(pdMS_TO_TICKS(35));
        }
        ESP_LOGI(TAG, "%" PRIu16 ", %" PRIu16 ", %" PRIu16 ", %" PRIu16,
                 data[0], data[1], data[2], data[3]);
      }

      target_angle += DELTA_DEG;

      if (target_angle > DEG_MAX) {
        ESP_LOGI(TAG, "MEASUREMENT SERIES COMPLETE");
        target_angle = DEG_MIN;
      }
    }

    last_input = input;

    vTaskDelay(pdMS_TO_TICKS(10));
  }
}
