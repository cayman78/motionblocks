#include <M5Unified.h>

static const uint32_t SAMPLE_INTERVAL_MS = 100;  // 10 Hz for first tests
uint32_t last_sample_ms = 0;

void drawHeader() {
    M5.Display.fillScreen(BLACK);
    M5.Display.setRotation(1);
    M5.Display.setTextSize(2);
    M5.Display.setCursor(5, 5);
    M5.Display.println("MotionBlocks");

    M5.Display.setTextSize(1);
    M5.Display.println("IMU logger v0.1");
}

void setup() {
    auto cfg = M5.config();
    M5.begin(cfg);

    Serial.begin(115200);
    delay(500);

    drawHeader();

    Serial.println("timestamp_ms,ax,ay,az,gx,gy,gz");

    M5.Display.setCursor(5, 40);
    M5.Display.println("CSV to Serial");
}

void loop() {
    M5.update();

    uint32_t now = millis();

    if (now - last_sample_ms < SAMPLE_INTERVAL_MS) {
        return;
    }

    last_sample_ms = now;

    bool imu_updated = M5.Imu.update();   // * НОВОЕ: просим IMU обновить измерения

    if (!imu_updated) {                   // * НОВОЕ: если данные не обновились
        Serial.print(now);                // * НОВОЕ
        Serial.println(",IMU_NOT_UPDATED,,,,,"); // * НОВОЕ
        return;                           // * НОВОЕ
    }


    auto data = M5.Imu.getImuData();

    float ax = data.accel.x;
    float ay = data.accel.y;
    float az = data.accel.z;

    float gx = data.gyro.x;
    float gy = data.gyro.y;
    float gz = data.gyro.z;

    Serial.print(now);
    Serial.print(",");
    Serial.print(ax, 4);
    Serial.print(",");
    Serial.print(ay, 4);
    Serial.print(",");
    Serial.print(az, 4);
    Serial.print(",");
    Serial.print(gx, 4);
    Serial.print(",");
    Serial.print(gy, 4);
    Serial.print(",");
    Serial.println(gz, 4);

    M5.Display.fillRect(0, 55, 240, 80, BLACK);
    M5.Display.setCursor(5, 55);
    M5.Display.printf("ax: %.2f\n", ax);
    M5.Display.printf("ay: %.2f\n", ay);
    M5.Display.printf("az: %.2f\n", az);
}