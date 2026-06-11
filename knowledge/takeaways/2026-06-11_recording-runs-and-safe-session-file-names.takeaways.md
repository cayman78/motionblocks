# Takeaways — Recording Runs and Safe Session File Names

## Date

2026-06-10

## Status

Accepted as future implementation step

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

The device currently manages local sessions:

```text
A001
A002
A003
```

After device restart, the firmware starts again from:

```text
A001
```

This creates a risk: if the logger writes directly to:

```text
session_A001.csv
```

then new recordings may overwrite old files or create confusing conflicts.

A previous idea was to let the logger scan existing files and continue with the next global session number, for example:

```text
device shows A001
logger writes A014
```

This was rejected because it creates confusion: the device display and the stored file would no longer match.

---

## Key decision

Do not silently renumber device sessions.

The session id shown on the device should remain visible in the file name.

Instead, introduce a separate concept:

```text
recording_run_id
```

A recording run is a technical series of recordings created during one logger/device run inside the same experiment and device folder.

---

## Terminology

### experiment_id

Logical experiment.

Example:

```text
EXP01
```

### device_id

Project-level device identifier.

Example:

```text
m5_001
```

### recording_run_id

Technical series of recordings within one experiment/device folder.

Examples:

```text
A
B
C
D
```

### device_session_id

The session id generated and displayed by the device.

Examples:

```text
A001
A002
A003
```

### sample_rate_hz

Sampling rate used for the current device run.

Examples:

```text
10
25
50
```

---

## File naming decision

Use the following raw file naming format:

```text
data/raw/[experiment_id]/[device_id]/run_[recording_run_id]_session_[device_session_id]_[sample_rate_hz]Hz.csv
```

Examples:

```text
data/raw/EXP01/m5_001/run_A_session_A001_10Hz.csv
data/raw/EXP01/m5_001/run_A_session_A002_10Hz.csv
data/raw/EXP01/m5_001/run_B_session_A001_50Hz.csv
data/raw/EXP01/m5_001/run_B_session_A002_50Hz.csv
data/raw/EXP01/m5_001/run_C_session_A001_25Hz.csv
```

This preserves all important meanings:

```text
EXP01      — experiment
m5_001     — device
run_B      — recording run assigned by logger
A001       — session id shown by device
50Hz       — selected sampling rate
```

---

## Why this is better than global session renumbering

Rejected approach:

```text
device shows A001
logger writes session_A014_50Hz.csv
```

Problem:

```text
displayed session id != stored session id
```

This creates cognitive and operational confusion.

Accepted approach:

```text
device shows A001
logger writes run_B_session_A001_50Hz.csv
```

This keeps the device-visible session id unchanged and adds the missing storage context through `recording_run_id`.

---

## Why this is better than creating a new experiment folder

Another possible approach was to create a new experiment folder for each device restart or recording series.

Rejected:

```text
EXP01/
EXP02/
EXP03/
```

Problem:

A new recording run is not necessarily a new experiment.

For example, the same experiment may contain recordings at different sampling rates:

```text
EXP01 — ordinary_home_movements
```

with files:

```text
run_A_session_A001_10Hz.csv
run_B_session_A001_50Hz.csv
run_C_session_A001_25Hz.csv
```

Therefore, the experiment remains stable, while `recording_run_id` separates technical recording series inside the experiment.

---

## Logger behavior

At logger startup, the logger should inspect:

```text
data/raw/[experiment_id]/[device_id]/
```

Then it should find existing recording run ids in file names:

```text
run_A_session_A001_10Hz.csv
run_A_session_A002_10Hz.csv
run_B_session_A001_50Hz.csv
```

If the maximum existing run is:

```text
B
```

then the new run should be:

```text
C
```

The device may still start from:

```text
A001
```

The logger should then create:

```text
run_C_session_A001_50Hz.csv
```

---

## Metadata decision

Recording session metadata should explicitly store:

```text
experiment_id
device_id
recording_run_id
device_session_id
sample_rate_hz
file_name
file_path
```

Example:

```json
{
  "experiment_id": "EXP01",
  "device_id": "m5_001",
  "recording_run_id": "B",
  "device_session_id": "A001",
  "sample_rate_hz": 50,
  "file_name": "run_B_session_A001_50Hz.csv",
  "file_path": "data/raw/EXP01/m5_001/run_B_session_A001_50Hz.csv",
  "status": "auto created. needs description."
}
```

Recommended `session_uid` format:

```text
[experiment_id]_[device_id]_[recording_run_id]_[device_session_id]
```

Example:

```text
EXP01_m5_001_B_A001
```

---

## CSV content decision

Inside the CSV, keep the device session id as received from firmware:

```csv
EVENT,A001,,,12345,,,,,,,,NEW_SESSION,
EVENT,A001,1,,13000,,,,,,,,START,
DATA,A001,1,1,13100,0.0123,-0.0341,0.9872,0.1200,-0.0300,0.0100,0.9880,,
EVENT,A001,1,,19000,,,,,,,,STOP,60
```

The file name and metadata provide the additional storage context:

```text
recording_run_id
sample_rate_hz
experiment_id
device_id
```

Do not rewrite `A001` inside CSV into a different session id.

---

## Relationship with selectable sampling rate

This decision should be implemented after the selectable sampling rate feature.

The intended order:

```text
1. DEVICE_INFO event with MAC address
2. Selectable sampling rate at device startup
3. Recording run id and safe session file names
```

The file naming decision depends on the selected sampling rate because the sampling rate is included in the file name:

```text
run_B_session_A001_50Hz.csv
```

---

## Future implementation branch

Recommended branch:

```text
feature/recording-runs-and-safe-file-names
```

Goal:

```text
Prevent overwriting old session files and preserve device-visible session ids.
```

Definition of Done:

* [ ] Logger scans `data/raw/[experiment_id]/[device_id]/` on startup.
* [ ] Logger detects existing `run_[letter]` values.
* [ ] Logger assigns the next available `recording_run_id`.
* [ ] Logger does not renumber `device_session_id`.
* [ ] File names use `run_[recording_run_id]_session_[device_session_id]_[sample_rate_hz]Hz.csv`.
* [ ] Metadata contains `recording_run_id`.
* [ ] Metadata contains `device_session_id`.
* [ ] Metadata contains `sample_rate_hz`.
* [ ] `session_uid` includes recording run id.
* [ ] Existing files are not overwritten.
* [ ] Old file names remain readable for backward compatibility where practical.

---

## Current position

Accepted future approach:

```text
Experiment remains stable.
Device session id remains unchanged.
Logger assigns recording_run_id.
File name includes run id, device session id, and sampling rate.
```

The key rule:

```text
Do not make the file disagree with the device display.
Add a recording run layer instead.
```
# Takeaways — Recording Runs and Safe Session File Names

## Date

2026-06-10

## Status

Accepted as future implementation step

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

The device currently manages local sessions:

```text
A001
A002
A003
```

After device restart, the firmware starts again from:

```text
A001
```

This creates a risk: if the logger writes directly to:

```text
session_A001.csv
```

then new recordings may overwrite old files or create confusing conflicts.

A previous idea was to let the logger scan existing files and continue with the next global session number, for example:

```text
device shows A001
logger writes A014
```

This was rejected because it creates confusion: the device display and the stored file would no longer match.

---

## Key decision

Do not silently renumber device sessions.

The session id shown on the device should remain visible in the file name.

Instead, introduce a separate concept:

```text
recording_run_id
```

A recording run is a technical series of recordings created during one logger/device run inside the same experiment and device folder.

---

## Terminology

### experiment_id

Logical experiment.

Example:

```text
EXP01
```

### device_id

Project-level device identifier.

Example:

```text
m5_001
```

### recording_run_id

Technical series of recordings within one experiment/device folder.

Examples:

```text
A
B
C
D
```

### device_session_id

The session id generated and displayed by the device.

Examples:

```text
A001
A002
A003
```

### sample_rate_hz

Sampling rate used for the current device run.

Examples:

```text
10
25
50
```

---

## File naming decision

Use the following raw file naming format:

```text
data/raw/[experiment_id]/[device_id]/run_[recording_run_id]_session_[device_session_id]_[sample_rate_hz]Hz.csv
```

Examples:

```text
data/raw/EXP01/m5_001/run_A_session_A001_10Hz.csv
data/raw/EXP01/m5_001/run_A_session_A002_10Hz.csv
data/raw/EXP01/m5_001/run_B_session_A001_50Hz.csv
data/raw/EXP01/m5_001/run_B_session_A002_50Hz.csv
data/raw/EXP01/m5_001/run_C_session_A001_25Hz.csv
```

This preserves all important meanings:

```text
EXP01      — experiment
m5_001     — device
run_B      — recording run assigned by logger
A001       — session id shown by device
50Hz       — selected sampling rate
```

---

## Why this is better than global session renumbering

Rejected approach:

```text
device shows A001
logger writes session_A014_50Hz.csv
```

Problem:

```text
displayed session id != stored session id
```

This creates cognitive and operational confusion.

Accepted approach:

```text
device shows A001
logger writes run_B_session_A001_50Hz.csv
```

This keeps the device-visible session id unchanged and adds the missing storage context through `recording_run_id`.

---

## Why this is better than creating a new experiment folder

Another possible approach was to create a new experiment folder for each device restart or recording series.

Rejected:

```text
EXP01/
EXP02/
EXP03/
```

Problem:

A new recording run is not necessarily a new experiment.

For example, the same experiment may contain recordings at different sampling rates:

```text
EXP01 — ordinary_home_movements
```

with files:

```text
run_A_session_A001_10Hz.csv
run_B_session_A001_50Hz.csv
run_C_session_A001_25Hz.csv
```

Therefore, the experiment remains stable, while `recording_run_id` separates technical recording series inside the experiment.

---

## Logger behavior

At logger startup, the logger should inspect:

```text
data/raw/[experiment_id]/[device_id]/
```

Then it should find existing recording run ids in file names:

```text
run_A_session_A001_10Hz.csv
run_A_session_A002_10Hz.csv
run_B_session_A001_50Hz.csv
```

If the maximum existing run is:

```text
B
```

then the new run should be:

```text
C
```

The device may still start from:

```text
A001
```

The logger should then create:

```text
run_C_session_A001_50Hz.csv
```

---

## Metadata decision

Recording session metadata should explicitly store:

```text
experiment_id
device_id
recording_run_id
device_session_id
sample_rate_hz
file_name
file_path
```

Example:

```json
{
  "experiment_id": "EXP01",
  "device_id": "m5_001",
  "recording_run_id": "B",
  "device_session_id": "A001",
  "sample_rate_hz": 50,
  "file_name": "run_B_session_A001_50Hz.csv",
  "file_path": "data/raw/EXP01/m5_001/run_B_session_A001_50Hz.csv",
  "status": "auto created. needs description."
}
```

Recommended `session_uid` format:

```text
[experiment_id]_[device_id]_[recording_run_id]_[device_session_id]
```

Example:

```text
EXP01_m5_001_B_A001
```

---

## CSV content decision

Inside the CSV, keep the device session id as received from firmware:

```csv
EVENT,A001,,,12345,,,,,,,,NEW_SESSION,
EVENT,A001,1,,13000,,,,,,,,START,
DATA,A001,1,1,13100,0.0123,-0.0341,0.9872,0.1200,-0.0300,0.0100,0.9880,,
EVENT,A001,1,,19000,,,,,,,,STOP,60
```

The file name and metadata provide the additional storage context:

```text
recording_run_id
sample_rate_hz
experiment_id
device_id
```

Do not rewrite `A001` inside CSV into a different session id.

---

## Relationship with selectable sampling rate

This decision should be implemented after the selectable sampling rate feature.

The intended order:

```text
1. DEVICE_INFO event with MAC address
2. Selectable sampling rate at device startup
3. Recording run id and safe session file names
```

The file naming decision depends on the selected sampling rate because the sampling rate is included in the file name:

```text
run_B_session_A001_50Hz.csv
```

---

## Future implementation branch

Recommended branch:

```text
feature/recording-runs-and-safe-file-names
```

Goal:

```text
Prevent overwriting old session files and preserve device-visible session ids.
```

Definition of Done:

* [ ] Logger scans `data/raw/[experiment_id]/[device_id]/` on startup.
* [ ] Logger detects existing `run_[letter]` values.
* [ ] Logger assigns the next available `recording_run_id`.
* [ ] Logger does not renumber `device_session_id`.
* [ ] File names use `run_[recording_run_id]_session_[device_session_id]_[sample_rate_hz]Hz.csv`.
* [ ] Metadata contains `recording_run_id`.
* [ ] Metadata contains `device_session_id`.
* [ ] Metadata contains `sample_rate_hz`.
* [ ] `session_uid` includes recording run id.
* [ ] Existing files are not overwritten.
* [ ] Old file names remain readable for backward compatibility where practical.

---

## Current position

Accepted future approach:

```text
Experiment remains stable.
Device session id remains unchanged.
Logger assigns recording_run_id.
File name includes run id, device session id, and sampling rate.
```

The key rule:

```text
Do not make the file disagree with the device display.
Add a recording run layer instead.
```
