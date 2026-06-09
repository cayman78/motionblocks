# Takeaways — Sampling Rate Choice

## Date

2026-06-09

## Status

Accepted as current working approach

## Summary

We discussed the sampling frequency for MotionBlocks IMU data collection.

The current working decision is to use **10 Hz** as the default sampling rate for the first educational prototype, while recognizing that higher rates such as **25–50 Hz** will be needed later for more serious motion classification and fall-like event detection.

---

## Key point

The sampling frequency should not be lower than the characteristic frequency of human motion. It should be sufficiently higher.

According to the Nyquist principle, to observe a signal component with frequency `f`, the sampling frequency should be at least `2f`. In practice, for motion analysis it is better to sample several times faster than the dominant motion frequency.

---

## Current decision

For the first stages of MotionBlocks:

```text
Default sampling rate: 10 Hz
Sample interval: 100 ms
```

This is sufficient for:

* first IMU experiments;
* educational demonstrations;
* idle / rest detection;
* walking-like movements;
* slow arm movements;
* device orientation changes;
* simple comparison of motion patterns.

---

## Rationale

10 Hz is a good starting point because it:

* produces smaller CSV files;
* is easier to inspect manually;
* is easier to transmit over Serial or simple Wi-Fi;
* reduces load on firmware and logger;
* is enough for the first visible results;
* keeps the project accessible for children.

At this stage, the goal is not high-precision biomechanical analysis, but a reliable and understandable data collection pipeline.

---

## Limitation

10 Hz may be insufficient for fast events.

For example:

* sudden impact;
* fall-like movement;
* sharp rotation;
* fast shaking;
* short acceleration peaks.

At 10 Hz, one sample is collected every 100 ms. A short acceleration peak may be missed or badly represented.

Therefore, 10 Hz should be treated as an educational/default mode, not as the final rate for fall detection.

---

## Future sampling modes

Recommended future modes:

```text
10 Hz   — first prototype, education, slow movements
25 Hz   — normal educational motion recording
50 Hz   — fall-like events, sharper movements, better classification
100 Hz  — research mode / stress tests
```

Current recommendation:

```text
Stage 1–2 default: 10 Hz
Later classification target: 25–50 Hz
Fall-like event target: 50 Hz
```

---

## Implementation note

Current firmware can keep the sampling interval as a single constant:

```cpp
static const uint32_t SAMPLE_INTERVAL_MS = 100;  // 10 Hz
```

Later, for 50 Hz:

```cpp
static const uint32_t SAMPLE_INTERVAL_MS = 20;   // 50 Hz
```

This keeps the experiment simple and makes sampling frequency easy to change.

---

## Educational experiment idea

Later, record the same movement at different sampling rates:

```text
10 Hz
25 Hz
50 Hz
```

Then compare:

* signal smoothness;
* visibility of peaks;
* file size;
* transmission stability;
* classification quality.

This can become a useful lesson on discretization, signal sampling, and the trade-off between data quality and system complexity.

---

## Current position

Use **10 Hz now**.

Do not over-optimize the sampling rate before the recording pipeline is stable.

First stabilize:

```text
IMU reading → recording control → file saving → basic analysis
```

Then increase the sampling rate and compare results experimentally.

---

## Open questions

* What sampling rate is the practical limit for stable Serial logging?
* What sampling rate is practical for Wi-Fi HTTP?
* Should the device support selectable sampling modes?
* Should sampling rate be stored in `records.sample_rate_hz`?
* Should fall-like tests always use 50 Hz or higher?

---

## Action items

* [ ] Keep 10 Hz in the current firmware.
* [ ] Store sampling rate in record metadata.
* [ ] Later test 25 Hz and 50 Hz.
* [ ] Compare recordings of the same movement at different rates.

---

## Tags

#motionblocks #imu #sampling-rate #signal-processing #education #firmware
