# Takeaways — Device Identity and MAC Address

## Date

2026-06-10

## Status

Accepted as next working approach

## Context

MotionBlocks now supports wireless HTTP logging:

```text
M5StickC Plus2
  → Wi-Fi
  → HTTP POST /line
  → tools/http_logger.py
  → CSV files
  → draft metadata
```

The current logger still receives `device_id` from the command line:

```powershell
python tools/http_logger.py --host 0.0.0.0 --port 8080 --experiment-id EXP01 --device-id m5_001 --create-metadata
```

This works for one device, but will become inconvenient when multiple M5StickC devices are used.

We discussed whether the firmware should know the list of supported devices and map MAC addresses to readable device ids.

---

## Key decision

The device should report its own stable hardware identifier, but should not assign the final readable `device_id`.

Recommended split:

```text
firmware:
  reports hardware_id / mac_address

logger / metadata layer:
  maps mac_address → device_id
```

The firmware should not contain a hardcoded registry like:

```text
AA:BB:CC:DD:EE:FF → m5_001
11:22:33:44:55:66 → m5_002
```

That mapping belongs to the logger / metadata layer.

---

## Rationale

M5StickC Plus2 is based on ESP32, which has a stable MAC address.

The MAC address is a good technical hardware identifier.

However, the readable project identifier, such as:

```text
m5_001
m5_002
```

is not a property of the physical chip alone. It is part of the MotionBlocks project registry.

Therefore:

```text
MAC address = hardware identity
device_id   = project identity
```

The firmware should report hardware identity.

The logger should resolve it to project identity.

---

## Why not hardcode MAC → device_id in firmware

Hardcoding the full supported-device list in firmware is not recommended.

Problems:

* adding a new device would require firmware changes;
* device registry would be duplicated between firmware and metadata;
* firmware would become aware of project inventory;
* different firmware versions could contain different mappings;
* metadata and firmware could become inconsistent;
* the device would know more than it needs to know.

This violates the current MotionBlocks principle:

```text
Keep the device simple.
Keep project context outside the firmware.
```

---

## Why server-side transport detection is not enough

The logger should not rely on detecting MAC address from the network connection.

Reasons:

* HTTP server usually sees client IP, not necessarily MAC;
* MAC may be unavailable across network boundaries;
* Serial transport has no network MAC information;
* MQTT broker/subscriber may not expose device MAC;
* transport-level identification is not portable.

Therefore the device should explicitly send its hardware identifier as part of the MotionBlocks protocol.

---

## Proposed protocol extension

Add a startup protocol event:

```csv
EVENT,DEVICE_INFO,mac_address,firmware_version,timestamp_ms
```

Example:

```csv
EVENT,DEVICE_INFO,AA:BB:CC:DD:EE:FF,motionblocks.logger.v0.4,12345
```

This event should be emitted before the first session event:

```csv
EVENT,DEVICE_INFO,AA:BB:CC:DD:EE:FF,motionblocks.logger.v0.4,12345
EVENT,NEW_SESSION,A001,12400
```

The same line should be sent through both transports:

```text
Serial
HTTP POST
```

Later this can also work through MQTT.

---

## Logger behavior

For now, `--device-id` should remain supported as a manual override.

Recommended resolution logic:

```text
if --device-id is provided:
    use --device-id
    if DEVICE_INFO is received:
        optionally store / validate mac_address

if --device-id is not provided:
    wait for DEVICE_INFO
    resolve mac_address through devices.json
    use mapped device_id

if mac_address is unknown:
    warn user
    optionally create draft device metadata
```

This allows a gradual migration from manual device ids to automatic device recognition.

---

## Proposed device registry

Add a metadata file later:

```text
data/metadata/devices.json
```

Example:

```json
[
  {
    "device_id": "m5_001",
    "device_name": "M5StickC Plus2 primary prototype",
    "hardware_model": "M5StickC Plus2",
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "status": "active",
    "notes": "Primary MotionBlocks prototype device"
  }
]
```

This registry should be used by both:

```text
tools/serial_logger.py
tools/http_logger.py
```

---

## Current implementation strategy

Do not implement the full device registry immediately.

First implement a minimal safe step:

```text
1. Firmware sends EVENT,DEVICE_INFO,...
2. HTTP logger accepts and writes this event.
3. Serial logger accepts and writes this event.
4. Current --device-id behavior remains unchanged.
```

Then implement registry mapping as a separate step:

```text
5. Add data/metadata/devices.json
6. Add mac_address → device_id resolution
7. Allow --device-id to become optional
```

---

## Expected benefits

This approach gives:

* compatibility with Serial logging;
* compatibility with HTTP logging;
* compatibility with future MQTT logging;
* support for multiple devices;
* less manual configuration;
* better metadata quality;
* no hardcoded device registry inside firmware;
* clean separation of hardware identity and project identity.

---

## Current position

Accepted approach:

```text
Device reports MAC address.
Logger maps MAC address to device_id.
Firmware does not hardcode supported-device registry.
--device-id remains as manual override for now.
```

---

## Next branch

Recommended branch:

```text
feature/device-info-event
```

Goal:

```text
Add DEVICE_INFO protocol event with MAC address and firmware version.
```

Definition of Done:

* [ ] Firmware obtains Wi-Fi MAC address.
* [ ] Firmware defines firmware version constant.
* [ ] Firmware emits `EVENT,DEVICE_INFO,...` on startup.
* [ ] `DEVICE_INFO` is sent through Serial.
* [ ] `DEVICE_INFO` is sent through HTTP.
* [ ] HTTP logger accepts and writes `DEVICE_INFO`.
* [ ] Serial logger accepts and writes `DEVICE_INFO`.
* [ ] Existing `--device-id` behavior remains unchanged.
* [ ] Existing CSV session files remain readable.
* [ ] Current wireless logging still works.

---

## Later branch

Possible later branch:

```text
feature/device-registry
```

Goal:

```text
Add devices.json and resolve mac_address → device_id.
```

Do not start this until `DEVICE_INFO` is working reliably.
