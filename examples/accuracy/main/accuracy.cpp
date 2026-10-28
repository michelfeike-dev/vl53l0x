#include "VL53L0X.h"
#include "driver/gpio.h"

static const char *TAG = "accuracy";

#define START_PIN GPIO_NUM_14
#define SENSOR_OFFSET 0 // [mm], result of examples/calibration
#define TARGET_DISTANCE_MIN 100
#define TARGET_DISTANCE_MAX 1200
#define TARGET_DISTANCE_DELTA 100
#define NUM_MEASUREMENTS 10

extern "C" void app_main(void)
{
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

    if (!sensor.init())
    {
        ESP_LOGE(TAG, "INIT FAILED");
        vTaskDelay(portMAX_DELAY);
    }

    ESP_LOGI(TAG, "SET SENSOR OFFSET");

    int32_t offset_um = static_cast<int32_t>(SENSOR_OFFSET) * 1000;

    if (!sensor.setOffset(offset_um))
    {
        ESP_LOGE(TAG, "SET SENSOR OFFSET FAILED");
        vTaskDelay(portMAX_DELAY);
    }

    ESP_LOGI(TAG, "ACCURACY MEASUREMENT");
    ESP_LOGI(TAG, "Minimum distance: %i mm", TARGET_DISTANCE_MIN);
    ESP_LOGI(TAG, "Maximum distance: %i mm", TARGET_DISTANCE_MAX);
    ESP_LOGI(TAG, "Delta distance: %i mm", TARGET_DISTANCE_DELTA);
    ESP_LOGI(TAG, "Target color: white");
    ESP_LOGI(TAG, "Number of measurements: %i", NUM_MEASUREMENTS);
    ESP_LOGI(TAG, "START MEASUREMENT: F_TRIG PIN%i", START_PIN);

    uint16_t data;
    int input;
    int last_input = 1;
    int target_distance = TARGET_DISTANCE_MIN;

    while (true)
    {
        input = gpio_get_level(START_PIN);

        // 0 := Low; 1 := High

        if ((input == 0) && (last_input == 1))
        {
            ESP_LOGI(TAG, "TARGET DISTANCE: %i", target_distance);

            data = 0;

            for (int i = 0; i < NUM_MEASUREMENTS; i++)
            {
                if (sensor.read(&data))
                {
                    ESP_LOGI(TAG, "MEASUREMENT %i: %u [mm]", i, data);
                    vTaskDelay(pdMS_TO_TICKS(100));
                }
                else
                {
                    ESP_LOGE(TAG, "MEASUREMENT FAILED");
                    vTaskDelay(portMAX_DELAY);
                }
            }

            target_distance += TARGET_DISTANCE_DELTA;

            // Start a new series at the minimum distance
            if (target_distance > TARGET_DISTANCE_MAX)
            {
                ESP_LOGI(TAG, "MEASUREMENT SERIES COMPLETE");
                target_distance = TARGET_DISTANCE_MIN;
            }
        }

        last_input = input;

        vTaskDelay(pdMS_TO_TICKS(10));
    }
}