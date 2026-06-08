# Takeaways — PlatformIO Basics

## Date

2026-06-08

## Status

Accepted

## Summary

PlatformIO is the build and development environment used for the MotionBlocks firmware.

In this project, PlatformIO defines the structure of the firmware folder, downloads the required ESP32 and Arduino framework packages, builds the firmware, uploads it to M5StickC Plus2, and opens the serial monitor.

The M5StickC Plus2 device defines the hardware, but the project structure is defined mainly by PlatformIO.

---

# 1. What PlatformIO is

PlatformIO is a development environment for embedded systems.

For MotionBlocks, PlatformIO is used to:

* manage the firmware project;
* download required frameworks and libraries;
* compile C++ code;
* upload firmware to M5StickC Plus2;
* monitor serial output from the device.

PlatformIO is installed as a VS Code extension:

```text
PlatformIO IDE
Publisher: PlatformIO
```

---

# 2. PlatformIO vs Arduino IDE

The project uses:

```text
VS Code + PlatformIO + Arduino framework
```

Arduino IDE is not required at Stage 1.

The Arduino framework is installed automatically by PlatformIO when the project is built.

This means:

* we write Arduino-style code;
* we use `setup()` and `loop()`;
* but we do not need the Arduino IDE application.

---

# 3. What defines the firmware folder structure

The folder structure inside:

```text
firmware/m5stickc-plus2/
```

is defined mainly by PlatformIO, not by the M5StickC Plus2 device.

Minimal PlatformIO firmware project:

```text
firmware/
└── m5stickc-plus2/
    ├── platformio.ini
    └── src/
        └── main.cpp
```

Optional folders that may be added later:

```text
include/   custom header files
lib/       local project libraries
test/      tests
```

At Stage 1, only these are required:

```text
platformio.ini
src/main.cpp
```

---

# 4. What `platformio.ini` does

`platformio.ini` is the configuration file of the PlatformIO project.

It tells PlatformIO:

* which hardware platform to use;
* which board profile to use;
* which programming framework to use;
* which libraries to download;
* which serial monitor speed to use.

Current Stage 1 configuration:

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

```text
platform = espressif32
```

Use the ESP32 platform.

```text
board = m5stick-c
```

Use an M5StickC-compatible board profile.

```text
framework = arduino
```

Use Arduino-style programming.

```text
monitor_speed = 115200
```

Use serial monitor speed 115200 baud.

```text
lib_deps =
    m5stack/M5Unified
    m5stack/M5GFX
```

Download M5Stack libraries for device and display support.

---

# 5. What `src/main.cpp` does

`src/main.cpp` is the main firmware source file.

PlatformIO automatically compiles files inside:

```text
src/
```

The file:

```text
src/main.cpp
```

contains the program that will be uploaded to M5StickC Plus2.

In Arduino-style firmware, the two key functions are:

```cpp
void setup()
```

Runs once when the device starts.

Used for:

* device initialization;
* screen setup;
* serial setup;
* sensor initialization.

```cpp
void loop()
```

Runs repeatedly forever.

Used for:

* reading sensors;
* sending data;
* updating the screen;
* detecting events.

---

# 6. First firmware example

The first firmware only checks that the device works.

It should:

* initialize M5StickC Plus2;
* print text on the screen;
* print messages to Serial Monitor.

File:

```text
firmware/m5stickc-plus2/src/main.cpp
```

Example:

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

This version does not read IMU data yet.

Its purpose is to verify:

* build works;
* upload works;
* display works;
* serial output works.

---

# 7. Basic PlatformIO commands

All commands should be run from:

```text
firmware/m5stickc-plus2/
```

## Check PlatformIO version

```powershell
pio --version
```

Example working output:

```text
PlatformIO Core, version 6.1.19
```

## Build firmware

```powershell
pio run
```

Expected result:

```text
SUCCESS
```

## List connected devices

```powershell
pio device list
```

This should show the M5StickC Plus2 COM port.

Example:

```text
COM6
```

## Upload firmware

```powershell
pio run --target upload --upload-port COM6
```

Replace `COM6` with the actual device port if different.

## Open Serial Monitor

```powershell
pio device monitor --port COM6 --baud 115200
```

Expected output for the first firmware:

```text
MotionBlocks first firmware started
alive
alive
alive
```

---

# 8. Device port

On Windows, the M5StickC Plus2 appears in:

```text
Device Manager → Ports (COM & LPT)
```

Example detected device:

```text
USB-Enhanced-SERIAL CH9102 (COM6)
```

In this case, the correct upload and monitor port is:

```text
COM6
```

Bluetooth serial ports such as `COM3` or `COM4` are not used for firmware upload.

---

# 9. What is defined by device vs PlatformIO

## Defined by M5StickC Plus2 hardware

* microcontroller type;
* display;
* IMU sensor;
* buttons;
* battery;
* USB serial chip;
* available memory;
* physical port.

## Defined by PlatformIO

* project folder structure;
* build process;
* dependency download;
* firmware upload command;
* serial monitor command;
* location of source files;
* use of `platformio.ini`.

## Defined by project code

* what appears on the screen;
* what data is read from sensors;
* what is sent to Serial Monitor;
* how motion events are processed.

---

# 10. Common mistakes

## Running `pio run` from the wrong folder

The command should be run from:

```text
firmware/m5stickc-plus2/
```

because this is where `platformio.ini` is located.

## Missing `platformio.ini`

Without `platformio.ini`, PlatformIO does not know how to build the project.

## Missing `src/main.cpp`

Without `src/main.cpp`, there is no firmware code to compile.

## Using the wrong COM port

Use the USB serial port, for example:

```text
USB-Enhanced-SERIAL CH9102 (COM6)
```

Do not use Bluetooth COM ports.

## Installing unnecessary extensions

At Stage 1, only the official PlatformIO IDE extension is required.

---

# 11. Stage 1 definition of done

PlatformIO setup is complete when:

* [ ] `pio --version` works.
* [ ] `firmware/m5stickc-plus2/platformio.ini` exists.
* [ ] `firmware/m5stickc-plus2/src/main.cpp` exists.
* [ ] `pio run` finishes with `SUCCESS`.
* [ ] firmware uploads to M5StickC Plus2.
* [ ] device screen shows MotionBlocks text.
* [ ] Serial Monitor shows `alive` messages.
