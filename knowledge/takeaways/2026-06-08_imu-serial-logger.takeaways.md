# Takeaways — IMU Serial Logger

## Date

2026-06-08

## Status

Accepted

## Summary

The MotionBlocks firmware was updated from a basic screen/serial test to **IMU logger v0.1**.

The logger reads accelerometer and gyroscope data from M5StickC Plus2 and prints it to Serial Monitor in CSV format.

A key issue was discovered: `M5.Imu.getImuData()` returned unchanged values until `M5.Imu.update()` was called before reading the data.

## Decisions

* Use a separate branch for the IMU logger:

```text
feature/imu-serial-logger
```

* Keep `feature/first-firmware` as the first successful screen/serial firmware.
* Use CSV serial output format:

```csv
timestamp_ms,ax,ay,az,gx,gy,gz
```

* Call `M5.Imu.update()` before `M5.Imu.getImuData()`.

## Rationale

The IMU logger changes the main firmware behavior and replaces the previous simple `main.cpp`.

Therefore, it should be developed in a separate branch and merged only after successful testing.

## Result

IMU logger v0.1 works:

* firmware builds;
* firmware uploads to M5StickC Plus2;
* Serial Monitor prints CSV rows;
* IMU values change when the device is moved.

## Open questions

* What sampling rate should be used for real motion recording: 10 Hz, 50 Hz, or another value?
* Should record numbering be stored only in RAM at first, or persisted in flash memory?
* Should the first wireless transport be Wi-Fi or Bluetooth/BLE?

## Action items

* [ ] Commit IMU logger v0.1.
* [ ] Push `feature/imu-serial-logger`.
* [ ] Update project journal.
* [ ] Prepare button-controlled recording firmware.
* [ ] Prepare Python serial logger for saving numbered CSV files.

## Related repository areas

* `firmware/m5stickc-plus2/src/main.cpp`
* `firmware/m5stickc-plus2/platformio.ini`
* `docs/stage_1_plan.md`
* `docs/journal.md`

## Tags

#motionblocks #firmware #m5stickc #imu #platformio #serial
