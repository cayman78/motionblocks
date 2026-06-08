# Environment Setup — MotionBlocks

## Purpose

This document describes the required development environment for the **MotionBlocks** project.

The goal is to prepare a participant’s computer for:

* working with the GitHub repository;
* building firmware for **M5StickC Plus2**;
* uploading firmware to the device;
* reading serial output from the device;
* later working with Python, SQLite, and motion data.

---

# 1. Required tools

## Already required at Stage 1

Each participant should have:

* **VS Code**
* **PlatformIO IDE extension for VS Code**
* **Git**
* **Python 3**
* **Access to the MotionBlocks GitHub repository**
* **USB cable for M5StickC Plus2**
* **USB-UART driver**, if Windows does not detect the device automatically

## Not required at Stage 1

These tools are not required for the first firmware stage:

* Arduino IDE
* Edge Impulse
* Orange Data Mining
* Advanced ML tools

Arduino framework is installed automatically by PlatformIO when the firmware project is built.

---

# 2. Install VS Code

Download and install **Visual Studio Code**.

After installation, open VS Code and make sure it starts normally.

---

# 3. Install PlatformIO

In VS Code:

1. Open **Extensions**.
2. Search for:

```text
PlatformIO IDE
```

3. Install the extension published by:

```text
PlatformIO
```

Use the official **PlatformIO IDE** extension with the orange icon.

Do not install additional PlatformIO-related extensions unless the mentor asks for them.

Not needed at this stage:

* PlatformIO Big Buttons
* PlatformIO Support
* IoT Utility
* PIO Dev Tools
* pioarduino IDE

After installation:

1. Restart VS Code.
2. Wait until PlatformIO finishes its initial setup.
3. Check that the PlatformIO icon appears in the left sidebar.

---

# 4. Check PlatformIO installation

Open PowerShell or the VS Code terminal and run:

```powershell
pio --version
```

Expected result:

```text
PlatformIO Core, version 6.x.x
```

Example working result:

```text
PlatformIO Core, version 6.1.19
```

If `pio` is not recognized in the normal terminal, open the PlatformIO terminal:

```text
PlatformIO icon → Quick Access → Miscellaneous → New Terminal
```

Then run again:

```powershell
pio --version
```

---

# 5. Check Git

Open a terminal and run:

```powershell
git --version
```

Expected result:

```text
git version ...
```

If Git is not installed, install Git for Windows.

---

# 6. Clone the repository

Choose a local folder for projects, for example:

```powershell
C:\projects
```

Then run:

```powershell
cd C:\projects
git clone https://github.com/cayman78/motionblocks.git
cd motionblocks
code .
```

After opening the repository in VS Code, check:

```powershell
git status
```

Expected result:

```text
On branch main
Your branch is up to date with 'origin/main'
```

---

# 7. Check Python

Run:

```powershell
python --version
```

or:

```powershell
py --version
```

Then check pip:

```powershell
python -m pip --version
```

Python is needed for later stages:

* serial logging;
* CSV processing;
* SQLite import;
* plotting;
* feature calculation.

---

# 8. SQLite and DBeaver

For Stage 1, a separate SQLite server is not required.

SQLite will be used as a local file database.

Python already includes the `sqlite3` module.

To check it:

```powershell
python
```

Then inside Python:

```python
import sqlite3
sqlite3.sqlite_version
```

Exit Python:

```python
exit()
```

DBeaver may be used later to open and inspect the SQLite database visually.

---

# 9. Connect M5StickC Plus2

Connect **M5StickC Plus2** to the computer using a USB-C cable.

On Windows:

```text
Device Manager → Ports (COM & LPT)
```

The device should appear as a USB serial device.

Example detected device:

```text
USB-Enhanced-SERIAL CH9102 (COM6)
```

In this example, the correct serial port is:

```text
COM6
```

Ignore Bluetooth serial ports such as:

```text
COM3
COM4
```

They are not used for firmware upload.

---

# 10. Check device from PlatformIO

Run:

```powershell
pio device list
```

Expected result: the M5StickC Plus2 should appear as a COM port, for example:

```text
COM6
```

If the device does not appear:

* check the USB cable;
* try another USB port;
* check Device Manager;
* install the required USB-UART driver;
* reconnect the device.

---

# 11. Branch for first firmware work

Before changing firmware files, create a feature branch:

```powershell
git checkout -b feature/first-firmware
```

Check current branch:

```powershell
git branch
```

Expected result:

```text
* feature/first-firmware
  main
```

The feature branch is used for safe development. The `main` branch should remain stable.

---

# 12. Firmware project location

The M5StickC Plus2 firmware should be placed in:

```text
firmware/m5stickc-plus2/
```

Expected structure:

```text
firmware/
└── m5stickc-plus2/
    ├── platformio.ini
    └── src/
        └── main.cpp
```

---

# 13. First `platformio.ini`

Create the file:

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

Notes:

* Arduino framework is downloaded automatically by PlatformIO.
* M5Unified and M5GFX are used for M5Stack device support and display handling.

---

# 14. First firmware program

Create the file:

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

This first firmware does not read IMU data yet.

Its purpose is to check that:

* the project builds;
* the device can be flashed;
* the display works;
* serial output works.

---

# 15. Build firmware

From the firmware folder:

```powershell
cd firmware\m5stickc-plus2
```

Run:

```powershell
pio run
```

During the first build, PlatformIO will download the ESP32 platform, Arduino framework, and required libraries.

Expected final result:

```text
SUCCESS
```

---

# 16. Upload firmware to M5StickC Plus2

If the device is on `COM6`, run:

```powershell
pio run --target upload --upload-port COM6
```

If your device uses another port, replace `COM6` with the correct port.

Example:

```powershell
pio run --target upload --upload-port COM7
```

After successful upload, the device screen should show:

```text
MotionBlocks
Stage 1
Hello!
```

---

# 17. Open Serial Monitor

Run:

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

To exit the Serial Monitor, use:

```text
Ctrl + C
```

or:

```text
Ctrl + ]
```

---

# 18. Commit the first firmware

Return to the repository root:

```powershell
cd ..\..
```

Check changes:

```powershell
git status
```

Add files:

```powershell
git add firmware/m5stickc-plus2/platformio.ini firmware/m5stickc-plus2/src/main.cpp
```

Commit:

```powershell
git commit -m "Add first M5StickC Plus2 firmware"
```

Push the feature branch to GitHub:

```powershell
git push -u origin feature/first-firmware
```

After this, create a Pull Request on GitHub:

```text
feature/first-firmware → main
```

---

# 19. Stage 1 checklist

A participant is ready for Stage 1 if:

* [ ] VS Code is installed.
* [ ] PlatformIO IDE extension is installed.
* [ ] `pio --version` works.
* [ ] Git is installed.
* [ ] Python is installed.
* [ ] The `motionblocks` repository is cloned.
* [ ] M5StickC Plus2 appears as a COM port.
* [ ] PlatformIO can build the firmware.
* [ ] Firmware can be uploaded to the device.
* [ ] Serial Monitor shows output from the device.

---

# 20. Known working configuration

Example working setup:

```text
OS: Windows
VS Code: installed
PlatformIO Core: 6.1.19
Device: M5StickC Plus2
Detected port: USB-Enhanced-SERIAL CH9102 (COM6)
Repository: motionblocks
```
