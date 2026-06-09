# Takeaways — Wireless Transport Choice

## Date

2026-06-09

## Status

Draft / Accepted as current working approach

## Summary

We discussed possible wireless transport options for MotionBlocks after the first IMU Serial logger.

MQTT was considered as an attractive IoT/event-driven option, but it may be too complex as the first wireless step for an educational project. The current working decision is to **not start with MQTT**, but to introduce wireless communication in simpler stages.

The preferred approach is to first finish USB/Serial data collection, then add button-controlled recording, then implement a simple Wi-Fi HTTP proof of concept, and only later introduce MQTT as an architecture lesson.

---

## Context

Current working firmware:

```text
feature/imu-serial-logger
```

Current technical status:

* M5StickC Plus2 reads IMU data.
* Serial Monitor prints CSV rows.
* IMU values change when the device is moved.
* USB/Serial transport works.

The next broader question is how to move from wired COM-port logging to wireless data transmission.

---

## Options considered

### USB Serial

```text
M5StickC Plus2 → COM6 → Serial Monitor / Python logger
```

Pros:

* Already works.
* Very easy to debug.
* Minimal infrastructure.
* Best baseline for firmware and IMU testing.

Cons:

* Requires USB cable.
* Not a real wearable scenario.

Conclusion:

USB Serial remains the baseline and first reliable transport.

---

### Wi-Fi + HTTP POST

```text
M5StickC Plus2 → Wi-Fi → Python/FastAPI server → CSV / SQLite
```

Pros:

* Simple mental model: device sends a request to a server.
* Easier to explain to children than MQTT.
* Requires only one Python server, no broker.
* Easy to test with browser/curl.
* Good first wireless proof of concept.
* Natural path to dashboard.

Cons:

* Less elegant for IoT/event-driven architecture.
* HTTP overhead is high for high-frequency streaming.
* Better for 5–10 Hz proof of concept than for heavy 50 Hz streaming.

Conclusion:

Preferred first wireless transport.

---

### MQTT

```text
M5StickC Plus2 → MQTT broker → Python subscriber / dashboard
```

Pros:

* Strong IoT model.
* Good publish/subscribe architecture.
* Supports multiple subscribers.
* Fits future MotionLink / Human-by-Wire event-bus architecture.
* Good educational topic once basic data flow is understood.

Cons:

* Adds extra infrastructure: MQTT broker.
* Adds new concepts: topic, broker, publish, subscribe, QoS, client id, reconnect logic.
* More points of failure.
* May distract from the immediate goal of collecting motion data.

Conclusion:

MQTT is valuable, but should not be the first wireless protocol. It should be introduced later as an architectural improvement and IoT lesson.

---

### UDP

```text
M5StickC Plus2 → UDP packet → Python UDP listener
```

Pros:

* Lightweight.
* Fast.
* Suitable for high-frequency sensor streams.

Cons:

* Packets may be lost.
* Less transparent for beginners.
* Weaker fit for future dashboard and event architecture.
* Less educational than HTTP or MQTT for current goals.

Conclusion:

Not recommended for the first educational wireless step.

---

### Bluetooth / BLE

Pros:

* Closer to real wearable products.
* Good future direction for phone integration.

Cons:

* More complex to debug.
* Requires BLE client/app logic.
* GATT concepts add complexity too early.

Conclusion:

Not suitable for the current stage.

---

## Current decision

Do not start wireless development with MQTT.

Use this staged approach:

```text
Stage 1 — USB Serial IMU logger
Stage 2 — Button-controlled Serial recording
Stage 3 — Python Serial logger saving numbered CSV files
Stage 4 — Wi-Fi HTTP proof of concept
Stage 5 — MQTT as IoT/event-bus architecture lesson
```

MQTT is kept as a future MotionLink/event-bus candidate, but not as the first wireless implementation.

---

## Rationale

The project is educational. The first priority is to preserve motivation and maintain a clear path from device data to stored records.

MQTT is architecturally attractive but introduces too many new concepts at once. It may shift attention from motion data collection to infrastructure debugging.

HTTP POST is less elegant but easier to explain and debug:

```text
device → server → file
```

MQTT can be introduced later as an improvement:

```text
device → broker → subscribers
```

This creates a useful educational contrast between direct communication and publish/subscribe architecture.

---

## Architecture principle

The firmware should separate:

```text
1. IMU reading
2. Message construction
3. Transport
```

Recommended conceptual structure:

```text
readImuSample()
buildMessage()
sendMessage()
```

Possible transport implementations:

```text
sendMessageSerial()
sendMessageHttp()
sendMessageMqtt()
```

This allows the project to reuse the same motion/event data model across different transports.

---

## Message format principle

Use one logical event/message model and different transports.

Example logical event:

```json
{
  "type": "DATA",
  "device_id": "m5_001",
  "record_id": 7,
  "timestamp_ms": 125100,
  "ax": 0.0123,
  "ay": -0.0341,
  "az": 0.9872,
  "gx": 0.1200,
  "gy": -0.0300,
  "gz": 0.0100
}
```

Transport-specific representation:

```text
Serial: CSV or JSONL line
HTTP: JSON body
MQTT: JSON payload
```

This keeps the architecture flexible and avoids rewriting the whole project when changing transport.

---

## Recommended near-term path

### Step 1 — Finish current IMU Serial logger

Current branch:

```text
feature/imu-serial-logger
```

Expected result:

* IMU values are printed as CSV.
* Values change when the device is moved.
* Current firmware state is committed and pushed.

---

### Step 2 — Button-controlled Serial recording

Possible branch:

```text
feature/button-controlled-logger
```

Expected behavior:

* double click starts recording;
* single click stops recording;
* record number is displayed on screen;
* data is sent only while recording.

Proposed Serial protocol:

```csv
EVENT,START,record_id,timestamp_ms
DATA,record_id,timestamp_ms,ax,ay,az,gx,gy,gz
EVENT,STOP,record_id,timestamp_ms
```

---

### Step 3 — Python Serial logger

Possible branch:

```text
feature/python-serial-logger
```

Expected behavior:

* Python listens to COM port;
* receives START / DATA / STOP events;
* creates numbered CSV files;
* saves motion records to `data/raw/`.

---

### Step 4 — Wi-Fi HTTP proof of concept

Possible branch:

```text
feature/wifi-http-imu-stream
```

Expected behavior:

* M5StickC connects to Wi-Fi;
* Python server runs on computer;
* device sends IMU JSON using HTTP POST;
* server prints and optionally saves received data.

---

### Step 5 — MQTT architecture lesson

Possible branch:

```text
feature/mqtt-imu-stream
```

Expected behavior:

* local MQTT broker is introduced;
* M5StickC publishes messages to MQTT topics;
* Python subscriber receives them;
* compare MQTT with HTTP in terms of architecture.

---

## Open questions

* Should the first Wi-Fi proof of concept be done before or after button-controlled recording?
* What sampling rate should be used for Wi-Fi HTTP: 5 Hz, 10 Hz, or 20 Hz?
* Should Serial use CSV while HTTP/MQTT use JSON?
* When should MQTT be introduced: after Python CSV logger or after SQLite database?
* Should transport abstraction be implemented immediately or only after the first HTTP prototype?

---

## Action items

* [ ] Complete and commit `feature/imu-serial-logger`.
* [ ] Implement button-controlled Serial recording.
* [ ] Implement Python Serial logger for numbered CSV files.
* [ ] Later implement Wi-Fi HTTP proof of concept.
* [ ] Later introduce MQTT as an educational IoT/event-bus comparison.

---

## Tags

#motionblocks #wireless #mqtt #http #iot #transport #architecture #education
