# Takeaways — First Firmware Run

## Date

2026-06-08

## Status

Accepted

## Summary

The first firmware for **M5StickC Plus2** was successfully built and uploaded using **VS Code + PlatformIO**.

This confirms that the local development environment is working, the device is detected correctly, firmware can be compiled, uploaded, and executed, and serial output can be monitored.

---

# 1. Goal

The goal of the first firmware run is to check the full development pipeline:

```text
main.cpp
  ↓
PlatformIO build
  ↓
firmware.bin
  ↓
upload to M5StickC Plus2
  ↓
screen output + serial output
```

At this stage, the firmware does not yet read IMU data.

The first firmware only checks:

* build process;
* firmware upload;
* device screen;
* serial output.

---

# 2. Required project files

The firmware project is located in:

```text
firmware/m5stickc-plus2/
```

Minimal required structure:

```text
firmware/
└── m5stickc-plus2/
    ├── platformio.ini
    └── src/
        └── main.cpp
```

---

# 3. `platformio.ini`

File:

```text
firmware/m5stickc-plus2/platformio.ini
```

Content:

```ini
[env:m5stickc_plus2]
platform = espressif32
board = m5stick-c
framework = arduino
monitor_speed = 115200
lib_deps =
    m5stack/M5Unified
    m5stack/M5GFX
```

Meaning:

* `platform = espressif32` — build for ESP32 platform;
* `board = m5stick-c` — use M5StickC board profile;
* `framework = arduino` — use Arduino-style `setup()` and `loop()`;
* `monitor_speed = 115200` — use serial monitor speed 115200;
* `M5Unified` and `M5GFX` — M5Stack libraries for device and display support.

---

# 4. First `main.cpp`

File:

```text
firmware/m5stickc-plus2/src/main.cpp
```

Content:

```cpp
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
```

---

# 5. Device port

The M5StickC Plus2 was detected in Windows Device Manager as:

```text
USB-Enhanced-SERIAL CH9102 (COM6)
```

Therefore, the upload and serial monitor port is:

```text
COM6
```

Bluetooth COM ports such as `COM3` or `COM4` should not be used for firmware upload.

---

# 6. Build and upload command

Run the command from the firmware project folder:

```powershell
cd firmware\m5stickc-plus2
```

Then build and upload:

```powershell
pio run --target upload --upload-port COM6
```

During the first run, PlatformIO may download:

* `espressif32` platform;
* ESP32 toolchain;
* Arduino framework for ESP32;
* `esptool.py`;
* M5Stack libraries;
* build tools.

This may take several minutes during the first setup.

---

# 7. Successful upload indicators

The upload is successful if the log contains:

```text
Building .pio\build\m5stickc_plus2\firmware.bin
Uploading .pio\build\m5stickc_plus2\firmware.bin
Serial port COM6
Chip is ESP32-PICO-V3-02
Hard resetting via RTS pin...
[SUCCESS]
```

In the first successful run, PlatformIO reported:

```text
PlatformIO Core, version 6.1.19
```

The device was detected as:

```text
Chip is ESP32-PICO-V3-02
```

The upload finished with:

```text
[SUCCESS]
```

---

# 8. Expected device screen output

After successful upload, the M5StickC Plus2 screen should show:

```text
MotionBlocks
Stage 1
Hello!
```

This confirms that:

* firmware runs on the device;
* display initialization works;
* M5Unified/M5GFX are working.

---

# 9. Serial Monitor

After upload, open the serial monitor:

```powershell
pio device monitor --port COM6 --baud 115200
```

Expected output:

```text
MotionBlocks first firmware started
alive
alive
alive
```

This confirms that:

* serial communication works;
* the firmware loop is running;
* the device can send data to the computer.

To exit Serial Monitor:

```text
Ctrl + C
```

or:

```text
Ctrl + ]
```

---

# 10. What this proves

The first firmware run proves that:

* PlatformIO is installed correctly;
* the repository structure is valid;
* `platformio.ini` is recognized;
* `main.cpp` is compiled;
* ESP32 firmware is generated;
* M5StickC Plus2 is detected on COM6;
* firmware upload works;
* screen output works;
* serial output works.

---

# 11. Stage result

The first firmware bring-up is complete.

Current status:

```text
[✓] PlatformIO installed
[✓] Device detected as COM6
[✓] Firmware project created
[✓] main.cpp compiled
[✓] Firmware uploaded
[✓] Screen output works
[✓] Serial output works
```

---

# 12. Next step

The next firmware step is:

```text
Add IMU serial logger firmware
```

The device should read:

* accelerometer: `ax`, `ay`, `az`;
* gyroscope: `gx`, `gy`, `gz`;

and print CSV-like output to Serial Monitor:

```csv
timestamp_ms,ax,ay,az,gx,gy,gz
1020,0.0123,-0.0341,0.9872,0.1200,-0.0300,0.0100
```

This will prepare the project for the first real motion records.
