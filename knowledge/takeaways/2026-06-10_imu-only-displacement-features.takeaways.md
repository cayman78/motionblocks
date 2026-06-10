# Takeaways — Experimental IMU-only displacement features

## Date

2026-06-10

## Status

Future idea / planned analysis layer

## Summary

We discussed whether MotionBlocks should compute additional derived metrics from IMU data, beyond directly observed accelerometer and gyroscope values.

The current decision is:

```text
Do not load the device with this now.
Do not put this into the Serial logger now.
Keep it as a future Python analysis layer.
```

The idea is still useful and should remain in the plan.

---

## Current reliable derived metrics

The firmware already computes:

```text
acc_norm = sqrt(ax^2 + ay^2 + az^2)
```

This is useful because it gives the total acceleration magnitude and is less dependent on device orientation than individual acceleration axes.

Possible simple future derived metrics:

```text
gyro_norm
jerk_norm
acc_norm_max_window
gyro_norm_max_window
post_event_rest_ratio
orientation_change_proxy
```

These are relatively robust and useful for motion classification and fall-like event detection.

---

## Experimental trajectory-like idea

In principle, acceleration can be integrated into velocity, and velocity can be integrated into position:

```text
acceleration → velocity → position
```

For each record, we can reset the estimates:

```text
record start:
  velocity = 0
  position = 0
```

Then for the duration of that record we can compute approximate motion estimates.

Possible future metrics:

```text
estimated_path_length
estimated_displacement_norm
estimated_vertical_displacement
vertical_drop_score
peak_velocity_estimate
impact_after_drop_score
```

These should be treated as experimental derived features, not as reliable physical coordinates.

---

## Why reset per record

Resetting at each `record_id` helps limit drift.

If each record is short, for example a few seconds, then accumulated integration error may remain useful as a relative feature.

The goal is not to say:

```text
The device moved exactly 0.82 meters.
```

The goal is to say:

```text
This record has a larger displacement-like score than ordinary walking or shaking.
```

Such a metric may still correlate with fall-like events.

---

## Gravity problem

The accelerometer measures both body acceleration and gravity.

In rest position, the sensor does not show zero acceleration. It shows approximately:

```text
acc_norm ≈ 1g
```

Therefore, gravity must be estimated and subtracted before integrating acceleration.

Possible simple approach:

```text
At the beginning of each record:
  assume the device is at rest
  estimate gravity from the first N samples
  use that as initial gravity direction
```

Limitation:

```text
If the device rotates during the record, the initial gravity estimate becomes inaccurate.
```

---

## Orientation problem

The device also provides gyroscope values:

```text
gx
gy
gz
```

These angular velocities can be integrated to approximate device orientation.

Possible approach:

```text
gyro → orientation estimate
body-frame acceleration → approximate world-frame acceleration
subtract gravity
integrate to velocity
integrate to position
```

Limitation:

```text
Gyro integration also drifts.
Orientation error causes gravity compensation error.
Gravity compensation error causes velocity and position drift.
```

So the resulting trajectory estimate is noisy.

---

## Fall-like detection relevance

Vertical displacement is physically meaningful for falls.

For example:

```text
standing or sitting → sudden vertical displacement of 60–100 cm
```

could be a strong fall-like indicator.

However, with only a wrist IMU, vertical displacement cannot be measured reliably. The wrist does not necessarily follow the body center of mass, and orientation/drift errors can be large.

Therefore, vertical displacement should not be used as a single decisive fall detector.

Better fall-like detection should combine multiple features:

```text
low acc_norm / possible free-fall phase
high acc_norm / impact
high gyro_norm / rotation
post-event inactivity
orientation change
experimental displacement-like score
```

---

## Implementation decision

Do not implement this in firmware now.

Do not implement this in `tools/serial_logger.py` now.

Future implementation should be a separate analysis script:

```text
tools/compute_features.py
```

Possible inputs:

```text
data/raw/EXP01/m5_001/session_A001.csv
data/metadata/recording_sessions.json
```

Possible outputs:

```text
data/features/EXP01/m5_001/session_A001_features.json
```

or:

```text
data/processed/EXP01/m5_001/session_A001_features.csv
```

---

## Recommended terminology

Use careful terminology:

```text
experimental IMU-only displacement features
estimated displacement
displacement-like score
path-length estimate
vertical drop score
```

Avoid overclaiming:

```text
true trajectory
exact coordinates
real vertical displacement
```

---

## Current position

This idea is useful, but not urgent.

Current priority remains:

```text
IMU reading → recording control → CSV saving → metadata → first labeled dataset
```

After labeled examples are collected, evaluate whether displacement-like metrics improve classification.

---

## Action items

* [ ] Keep firmware simple.
* [ ] Keep Serial logger simple.
* [ ] Collect labeled motion examples first.
* [ ] Later implement `tools/compute_features.py`.
* [ ] Compute simple robust features first.
* [ ] Add experimental IMU-only displacement features later.
* [ ] Evaluate correlation with fall-like recordings.

---

## Tags

#motionblocks #imu #features #trajectory #dead-reckoning #fall-detection #analysis-layer #future
