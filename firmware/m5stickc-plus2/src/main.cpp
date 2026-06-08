#include <M5Unified.h>

void setup() {
    auto cfg = M5.config();
    M5.begin(cfg);

    Serial.begin(115200);
    delay(500);

    M5.Display.setRotation(1);
    M5.Display.setTextSize(2);
    M5.Display.fillScreen(BLACK);
    M5.Display.setCursor(10, 10);

    M5.Display.println("MotionBlocks");
    M5.Display.println("Stage 1");
    M5.Display.println("Hello!");

    Serial.println("MotionBlocks first firmware started");
}

void loop() {
    M5.update();

    Serial.println("alive");
    delay(1000);
}