# MotionBlocks Journal

This is the working project journal for **MotionBlocks** by **Stofendez Lab**.

The journal records important project events, decisions, experiments, problems, and next steps.

It is not a full documentation file.
Stable decisions should later be moved to the relevant documentation files.

---

# 2026-06-08

## Project identity fixed

We selected the project naming structure:

* **Stofendez Lab** — laboratory / team
* **MotionBlocks** — main project
* **MotionLink** — future technology for connecting the personal motion domain to external dashboards

Rationale:

* MotionBlocks is short and understandable for children.
* It connects well with LEGO / Roblox-style block thinking.
* It also describes the idea of a motion library built from reusable movement blocks.
* MotionLink can later describe the connection between the motion domain and family / medical dashboards.

## Development environment

Initial development stack:

* VS Code
* PlatformIO
* Arduino framework through PlatformIO
* Python
* SQLite / DBeaver
* GitHub

Optional tools for later stages:

* Edge Impulse
* ChatGPT Data Analysis
* Orange Data Mining

## PlatformIO installed

PlatformIO IDE extension was installed in VS Code.

Check command:

```powershell
pio --version
```

Working result:

```text
PlatformIO Core, version 6.1.19
```

## Device detected

M5StickC Plus2 was detected in Windows Device Manager as:

```text
USB-Enhanced-SERIAL CH9102 (COM6)
```

The correct device port for upload and serial monitor is:

```text
COM6
```

Bluetooth COM ports should not be used for firmware upload.

## First firmware uploaded

The first firmware was successfully built and uploaded using:

```powershell
pio run --target upload --upload-port COM6
```

Result:

```text
[SUCCESS]
```

The device screen showed:

```text
MotionBlocks
Stage 1
Hello!
```

Serial output worked and printed:

```text
MotionBlocks first firmware started
alive
alive
alive
```

## Confirmed

The first firmware bring-up is complete.

Confirmed:

* PlatformIO works.
* ESP32 toolchain was downloaded.
* Arduino framework was downloaded by PlatformIO.
* M5Unified and M5GFX libraries were downloaded.
* `main.cpp` was compiled.
* Firmware was uploaded to M5StickC Plus2.
* Display output works.
* Serial output works.

## Next steps

* Commit the first firmware.
* Push branch `feature/first-firmware` to GitHub.
* Create Pull Request.
* Add IMU serial logger firmware.
* Print IMU data as CSV:

  * `timestamp_ms`
  * `ax`
  * `ay`
  * `az`
  * `gx`
  * `gy`
  * `gz`
* Start preparing Python serial logger.
* Start preparing SQLite schema:

  * `records`
  * `recorddata`

---

# Journal entry template

## YYYY-MM-DD

### Topic

Short title of the work session.

### What was done

* ...

### Decisions

* ...

### Problems

* ...

### Results

* ...

### Next steps

* [ ] ...
* [ ] ...

### Related files

* `path/to/file`
* `path/to/file`


## 2026-06-08 — IMU logger v0.1

### Expected result

M5StickC Plus2 should read IMU data and print it to Serial Monitor in CSV format.

### Actual result

IMU logger works after adding `M5.Imu.update()` before reading data with `M5.Imu.getImuData()`.

Serial Monitor prints CSV rows:

```csv
timestamp_ms,ax,ay,az,gx,gy,gz
... 