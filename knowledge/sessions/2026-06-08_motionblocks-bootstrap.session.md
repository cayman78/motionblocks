# LLM Session — MotionBlocks Bootstrap

## Date

2026-06-08

## Topics

- Project naming
- Repository structure
- GitHub workflow
- LLM project memory
- Environment setup
- PlatformIO basics
- First firmware run
- IMU serial logger
- Next steps: button-controlled recording and wireless transport

## Main decisions

- Laboratory name: Stofendez Lab
- Project name: MotionBlocks
- Future technology name: MotionLink
- Use VS Code + PlatformIO + Arduino framework
- Use M5StickC Plus2 as first device
- Use GitHub repository `motionblocks`
- Use `llm/` folder for project memory
- Use `docs/journal.md` as chronological project journal
- Use `records` and `recorddata` as initial SQLite tables
- Use separate branches when replacing working firmware
- Use `M5.Imu.update()` before `M5.Imu.getImuData()`

## Technical results

- PlatformIO installed successfully.
- `pio --version` works.
- Device detected as `USB-Enhanced-SERIAL CH9102 (COM6)`.
- First firmware successfully built and uploaded.
- Screen output works.
- Serial output works.
- IMU logger v0.1 works after adding `M5.Imu.update()`.
- IMU values change when the device is moved.

## Important commands

```powershell
pio --version
pio run --target upload --upload-port COM6
pio device monitor --port COM6 --baud 115200