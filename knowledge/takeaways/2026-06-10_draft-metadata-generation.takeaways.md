# Takeaways — Draft metadata generation

## Date

2026-06-10

## Status

Accepted as current working approach

## Summary

We implemented and tested automatic draft metadata generation in the MotionBlocks Python Serial logger.

The logger can now create raw CSV files and, when explicitly enabled, create draft records in project metadata files.

The goal is to reduce manual bookkeeping while preserving human control over semantic descriptions such as movement type, subject, comments, and experiment meaning.

---

## Current command

Run from the repository root:

```powershell
python tools/serial_logger.py --port COM6 --experiment-id EXP01 --device-id m5_001 --create-metadata
```

Without `--create-metadata`, the logger only writes raw CSV files.

With `--create-metadata`, the logger also creates or updates metadata JSON files.

---

## Files created or updated

Raw data files:

```text
data/raw/[experiment_id]/[device_id]/session_[session_id].csv
```

Example:

```text
data/raw/EXP01/m5_001/session_A001.csv
```

Metadata files:

```text
data/metadata/experiments.json
data/metadata/recording_sessions.json
```

---

## Metadata creation rule

Metadata generation is explicit and controlled by the flag:

```powershell
--create-metadata
```

When enabled:

```text
1. If experiments.json does not exist, create it.
2. If the specified experiment_id is missing, add a draft experiment record.
3. If recording_sessions.json does not exist, create it.
4. If the current session_uid is missing, add a draft session record.
5. If records already exist, preserve them and do not overwrite manual edits.
```

This prevents the logger from destroying or replacing human-curated metadata.

---

## Draft status

Automatically generated metadata records use status:

```text
auto created. needs description.
```

Meaning:

```text
The record was created automatically.
It is structurally valid.
It still requires human review and semantic description.
```

Later the user should update status manually, for example:

```text
raw
checked
processed
bad
archived
```

---

## Responsibility split

Firmware is intentionally simple and does not know experiment-level context.

Firmware sends:

```text
session_id
record_id
sample_id
sensor data
```

Python logger provides:

```text
experiment_id
device_id
file_path
```

Metadata provides:

```text
subject_id
movement_type
movement_label
location
comments
status
tags
```

Important rule:

```text
Device does not know experiment_id.
Device does not know subject_id.
Device does not know movement_type.
```

---

## Experiment metadata behavior

If the experiment does not exist, the logger creates a draft record in:

```text
data/metadata/experiments.json
```

Example draft fields:

```json
{
  "experiment_id": "EXP01",
  "short_name": "unknown",
  "title": "unknown",
  "started_at": "2026-06-10T18:30:00",
  "ended_at": null,
  "location": "unknown",
  "environment": "unknown",
  "goal": "",
  "participants": [],
  "operator_id": "unknown",
  "device_ids": ["m5_001"],
  "default_device_position": "unknown",
  "default_wrist": null,
  "default_sample_rate_hz": 10,
  "protocol": "Button-controlled recording. Button A starts/stops records. Button B switches to next session.",
  "comments": "",
  "status": "auto created. needs description.",
  "tags": []
}
```

Human should later fill in the meaningful fields.

---

## Recording session metadata behavior

When a new session appears, the logger creates a draft record in:

```text
data/metadata/recording_sessions.json
```

The session uid is built as:

```text
[experiment_id]_[device_id]_[session_id]
```

Example:

```text
EXP01_m5_001_A001
```

Example draft fields:

```json
{
  "experiment_id": "EXP01",
  "device_id": "m5_001",
  "session_id": "A001",
  "session_uid": "EXP01_m5_001_A001",
  "file_id": 1,
  "file_name": "session_A001.csv",
  "file_path": "data/raw/EXP01/m5_001/session_A001.csv",
  "file_role": "raw_data",
  "data_format": "wide_csv",
  "schema_version": "motionblocks.sample.v0.1",
  "movement_type": "unknown",
  "movement_label": "unknown",
  "subject_id": "unknown",
  "started_at": "2026-06-10T18:30:00",
  "sample_rate_hz": 10,
  "records_expected": null,
  "records_actual": null,
  "channels": [
    {"name": "ax", "kind": "acceleration", "axis": "x", "unit": "g"},
    {"name": "ay", "kind": "acceleration", "axis": "y", "unit": "g"},
    {"name": "az", "kind": "acceleration", "axis": "z", "unit": "g"},
    {"name": "gx", "kind": "angular_velocity", "axis": "x", "unit": "deg_per_sec"},
    {"name": "gy", "kind": "angular_velocity", "axis": "y", "unit": "deg_per_sec"},
    {"name": "gz", "kind": "angular_velocity", "axis": "z", "unit": "deg_per_sec"},
    {"name": "acc_norm", "kind": "derived_acceleration_norm", "unit": "g"}
  ],
  "comment": "",
  "status": "auto created. needs description.",
  "tags": []
}
```

Human should later fill:

```text
movement_type
movement_label
subject_id
comment
tags
status
```

---

## Why this design

This approach gives a good balance:

```text
Logger automates structure.
Human keeps semantic control.
Firmware stays generic.
Metadata stays FDAM-compatible.
```

It also prevents the common problem where raw CSV files are collected but later nobody remembers what they mean.

---

## Important protection rule

The logger must not overwrite existing metadata records.

If an experiment or session already exists, the logger should print that the existing metadata is preserved and leave the record unchanged.

This is important because manually completed metadata should not be lost.

---

## Current result

Confirmed:

```text
[✓] CSV files are created by the logger
[✓] experiments.json is created if missing
[✓] missing experiment record is auto-created
[✓] recording_sessions.json is created if missing
[✓] missing session record is auto-created
[✓] draft records use status "auto created. needs description."
[✓] existing metadata is preserved
```

---

## Open questions

* Should the logger update `records_actual` after STOP events?
* Should `ended_at` be filled automatically when a session is closed?
* Should there be a separate metadata validation script?
* Should the logger support a command-line label such as `--movement-type jumping`?
* Should metadata be moved to SQLite after the first real dataset?

---

## Action items

* [ ] Commit current logger implementation.
* [ ] Review generated metadata files.
* [ ] Manually complete `experiments.json`.
* [ ] Manually complete `recording_sessions.json`.
* [ ] Collect the first real dataset.
* [ ] Later implement a metadata validation script.

---

## Tags

#motionblocks #metadata #serial-logger #json #data-format #fdam #experiment-tracking
