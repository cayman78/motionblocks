# Takeaways — HTTP Keep-Alive Test for Per-Sample Logging

## Date

2026-06-11

## Status

Accepted as experimental result

## Context

During work on `feature/selectable-sampling-rate`, the firmware was extended to support selectable sampling rates:

```text
5 Hz
10 Hz
25 Hz
50 Hz
100 Hz
```

The device correctly reported the selected rate using:

```csv
EVENT,SAMPLE_RATE,sample_rate_hz,timestamp_ms
```

Example:

```csv
EVENT,SAMPLE_RATE,50,11143
```

The HTTP logger correctly received this event and stored the configured sampling rate in session metadata.

However, when recording over Wi-Fi using one HTTP POST per sample, the actual intervals between `DATA` rows remained around 80–100 ms even when 25 Hz or 50 Hz was selected.

This corresponds to approximately 10–12 Hz effective logging rate.

---

## Initial hypothesis

The first hypothesis was that the bottleneck might be caused by opening and closing a new HTTP/TCP connection for every sample.

Original simplified logic:

```text
for each DATA row:
    create HTTPClient
    begin HTTP request
    POST one line
    wait for response
    close HTTPClient
```

The idea was to test whether reusing the HTTP connection would be sufficient.

---

## Experiment

An experimental firmware version was created:

```text
motionblocks.logger.v0.6.1
```

The firmware used HTTP keep-alive during active recording.

The intended transport logic was:

```text
IDLE:
    DEVICE_INFO  → one-shot HTTP POST
    SAMPLE_RATE  → one-shot HTTP POST
    NEW_SESSION  → one-shot HTTP POST

RECORDING:
    START → open reusable HTTPClient
    DATA  → POST through the same HTTPClient
    DATA  → POST through the same HTTPClient
    DATA  → POST through the same HTTPClient
    STOP  → POST through the same HTTPClient
    after STOP → close HTTPClient
```

The goal was to keep the current HTTP POST architecture while reducing overhead from repeated connection setup and teardown.

---

## Result

The experiment did not solve the problem.

Even with HTTP keep-alive enabled, the device still did not reliably reach 25 Hz.

Observed behavior:

```text
5 Hz  → device slows down correctly
10 Hz → works approximately as before
25 Hz → not reached reliably
50 Hz → not reached reliably
```

This is important because it shows that the sampling-rate selection logic itself works.

The firmware does change the intended sampling interval correctly.

The bottleneck is not a simple firmware state bug.

---

## Interpretation

The limiting factor is the model:

```text
one sample = one synchronous HTTP request/response
```

Even if the TCP connection is reused, every call to HTTP POST is still a blocking request-response transaction.

That means each sample is delayed by:

```text
HTTP request overhead
Python HTTP server handling
HTTP response wait
ESP32 HTTPClient processing
Wi-Fi stack latency
```

The payload size is not the issue.

The data volume is tiny:

```text
100 Hz × one short CSV row ≈ only a few KB/s
```

The issue is latency and synchronous per-sample transaction overhead, not bandwidth.

---

## Conclusion

HTTP keep-alive is not sufficient for reliable 25 Hz / 50 Hz per-sample wireless logging.

The following model should not be used for high-frequency recording:

```text
DATA sample → individual HTTP POST → wait for response
```

This model remains acceptable for:

```text
5 Hz
10 Hz
simple educational tests
manual debugging
low-frequency demonstrations
```

But it should not be treated as the final transport model for higher-frequency IMU recording.

---

## Design decision

Do not continue optimizing per-sample HTTP POST.

The next transport improvement should be one of:

```text
1. HTTP batch mode
2. TCP stream
```

Preferred next step:

```text
HTTP batch mode
```

Reason:

```text
- keeps the current HTTP logger architecture;
- keeps the existing /line endpoint;
- Python http_logger.py already supports splitlines();
- firmware only needs to buffer several DATA rows before POST;
- easier educational explanation;
- lower implementation cost than TCP stream.
```

---

## Recommended next transport model

For 25 Hz / 50 Hz over Wi-Fi, use batch sending:

```text
read IMU at selected rate
append DATA rows to buffer
send several rows in one HTTP POST
```

Example for 50 Hz:

```text
sample every 20 ms
buffer 10 samples
POST one batch every ~200 ms
```

Instead of:

```text
50 HTTP POST requests per second
```

the device would send:

```text
5 HTTP POST requests per second
```

This should reduce overhead significantly while preserving the current HTTP-based architecture.

---

## Future branch candidate

```text
feature/http-batch-logging
```

Possible scope:

```text
- add DATA batch buffer in firmware;
- keep Serial output immediate;
- send HTTP DATA in batches;
- flush buffer on STOP;
- ensure STOP is sent only after all buffered DATA rows are sent;
- keep current http_logger.py mostly unchanged;
- measure effective sampling intervals at 25 Hz and 50 Hz.
```

---

## Current position

The selectable sampling rate feature is valid.

However, over current per-sample HTTP transport:

```text
selected_sample_rate_hz != guaranteed_effective_sample_rate_hz
```

The selected rate is the intended firmware sampling interval.

The effective rate depends on the transport.

This distinction should be reflected in documentation and future metadata design.

Possible future metadata fields:

```json
{
  "configured_sample_rate_hz": 50,
  "transport": "http_batch",
  "effective_sample_rate_hz": null
}
```

For now, keep:

```json
"sample_rate_hz": 50
```

but interpret it as the configured sampling rate, not as a verified effective rate.

---

## Action items

* [ ] Do not keep HTTP keep-alive experiment as the final solution.
* [ ] Revert or remove keep-alive-specific code unless needed for further tests.
* [ ] Keep selectable sampling rate logic.
* [ ] Update journal with the negative result.
* [ ] Consider `feature/http-batch-logging` before moving to TCP stream.
* [ ] Later measure actual effective sampling rate from CSV timestamps.

---

## Tags

#motionblocks #imu #http #wifi #sampling-rate #negative-result #transport #firmware
