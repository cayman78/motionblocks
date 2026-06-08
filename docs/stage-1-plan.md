# Stage 1 — First Firmware Bring-up and IMU Logger

## Goal

Prepare the first working firmware for **M5StickC Plus2** and confirm that the device can be used for collecting motion sensor data.

## Branches

```text
feature/first-firmware
feature/imu-serial-logger
```

## Expected Result

At the end of this stage, M5StickC Plus2 should:

* build firmware through PlatformIO;
* receive uploaded firmware through USB;
* show MotionBlocks status text on the screen;
* send serial output to the computer;
* read IMU data from accelerometer and gyroscope;
* print IMU data to Serial Monitor in CSV format.

Expected CSV format:

```csv
timestamp_ms,ax,ay,az,gx,gy,gz
```

## Definition of Done

Stage 1 is done when:

* [x] `firmware/m5stickc-plus2/platformio.ini` exists.
* [x] `firmware/m5stickc-plus2/src/main.cpp` exists.
* [x] PlatformIO is installed and available through `pio`.
* [x] M5StickC Plus2 is detected as a USB serial device.
* [x] Firmware builds successfully.
* [x] Firmware uploads successfully to M5StickC Plus2.
* [x] Device screen shows MotionBlocks status text.
* [x] Serial Monitor opens at `115200` baud.
* [x] Serial Monitor prints startup messages.
* [x] IMU logger prints CSV header:

```csv
timestamp_ms,ax,ay,az,gx,gy,gz
```

* [x] IMU logger prints continuous data rows.
* [x] IMU values change when the device is moved.
* [ ] Result is committed to Git.
* [ ] Branch is pushed to GitHub.
* [ ] Pull Request is created.
* [ ] Branch is merged into `main`.

## Important implementation note

When reading IMU data through M5Unified, the firmware must call:

```cpp
M5.Imu.update();
```

before:

```cpp
M5.Imu.getImuData();
```

Without `M5.Imu.update()`, the firmware may repeatedly print the same IMU values.

## Next technical stage

Button-controlled recording:

* double click starts a new record;
* single click stops the current record;
* current record number is shown on the screen;
* serial output uses structured events:

  * `EVENT,START,...`
  * `DATA,...`
  * `EVENT,STOP,...`
