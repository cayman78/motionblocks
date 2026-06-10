# Takeaways — Raw Data and Metadata Format

## Date

2026-06-09

## Status

Accepted as current working approach

## Summary

We agreed on the first practical data format for MotionBlocks.

The format should remain simple enough for children and educational use, but should also be structured in a way that can later be transformed into an FDAM-compatible motion domain model.

The current approach:

```text
raw CSV files      — simple wide-format sensor data
metadata JSONL     — descriptions of experiments and recording sessions
future FDAM layer  — normalized model generated later from CSV + JSONL
```

The key design decision is to use simple files now, but with stable identifiers, controlled metadata, schema versions, and channel descriptions.

---

## Conceptual hierarchy

The agreed hierarchy is:

```text
Experiment
  → RecordingSession
      → DataFile
      → MotionRecord
          → MotionSample
              → Sensor values / channels
```

Educational explanation:

```text
Experiment       — серия замеров с общей целью
RecordingSession — один файл / одна группа однотипных записей
DataFile         — физический CSV-файл
MotionRecord     — одна попытка внутри файла
MotionSample     — одна строка измерений
Sensor values    — ax, ay, az, gx, gy, gz, acc_norm, later heart_rate, temperature, etc.
```

FDAM-oriented interpretation:

```text
Experiment        → class / object
RecordingSession  → class / object
DataFile          → class / object
MotionRecord      → class / object
MotionSample      → fact table / time-series fact
SensorChannel     → registry / reference data
MovementType      → enumeration / reference data
DataStatus        → enumeration / reference data
```

---

## Directory structure

Recommended initial structure:

```text
data/
├── raw/
│   ├── session_0001.csv
│   ├── session_0002.csv
│   └── session_0003.csv
│
└── metadata/
    ├── experiments.jsonl
    └── recording_sessions.jsonl
```

`data/raw/` contains raw sensor CSV files.

`data/metadata/experiments.jsonl` describes experiment-level context.

`data/metadata/recording_sessions.jsonl` describes each recording session / data file.

---

## Raw data format

For the first stages, raw sensor data is stored in **wide CSV format**.

This is preferred for education and quick analysis because it is easy to inspect in Excel, pandas, or simple plotting tools.

Example file:

```text
data/raw/session_0001.csv
```

Recommended CSV columns:

```csv
row_type,file_id,record_id,sample_id,device_timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm,event_type,sample_count
```

Example content:

```csv
row_type,file_id,record_id,sample_id,device_timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm,event_type,sample_count
EVENT,1,,,83000,,,,,,,,NEW_FILE,
EVENT,1,1,,85000,,,,,,,,START,
DATA,1,1,1,85100,0.0123,-0.0341,0.9872,0.1200,-0.0300,0.0100,0.9880,,
DATA,1,1,2,85200,0.0130,-0.0338,0.9869,0.1100,-0.0400,0.0200,0.9878,,
EVENT,1,1,,91000,,,,,,,,STOP,60
EVENT,1,2,,95000,,,,,,,,START,
DATA,1,2,1,95100,0.0210,-0.0300,0.9901,0.1300,-0.0500,0.0300,0.9908,,
EVENT,1,2,,101000,,,,,,,,STOP,60
```

Interpretation:

```text
file_id            — id of current file/session shown by device
record_id          — id of one attempt inside the file
sample_id          — id of one data row inside the record
device_timestamp_ms — timestamp from the device
ax, ay, az         — accelerometer values
gx, gy, gz         — gyroscope values
acc_norm           — sqrt(ax*ax + ay*ay + az*az)
event_type         — NEW_FILE / START / STOP for event rows
sample_count       — number of samples reported at STOP
```

---

## Why wide CSV for raw data

Wide CSV is chosen for the raw layer because it is:

* easy to inspect manually;
* easy to use with pandas;
* easy to plot;
* easy to explain to children;
* sufficient for the first IMU-only prototype.

The limitation is that adding new sensors changes the columns. This is acceptable at the raw layer, because metadata will describe the available channels.

Later, FDAM conversion may transform wide CSV into a normalized long/fact model.

---

## Alternative future normalized format

A future FDAM or database layer may transform raw data into long format:

```csv
session_id,record_id,sample_id,t_ms,channel,value,unit
session_0001,1,15,1500,ax,0.123,g
session_0001,1,15,1500,ay,-0.041,g
session_0001,1,15,1500,az,0.982,g
session_0001,1,15,1500,heart_rate,86,bpm
```

This is more universal, but less convenient for the first educational raw files.

Decision:

```text
Raw layer now: wide CSV
FDAM/database layer later: normalized model if needed
```

---

## Experiment metadata format

Experiment-level metadata is stored in:

```text
data/metadata/experiments.jsonl
```

One JSONL row describes one experiment / series of measurements.

Example:

```jsonl
{"experiment_id":"exp_20260609_ordinary_home_movements","title":"Замеры ординарных движений дома","started_at":"2026-06-09T15:30:00","ended_at":null,"location":"home","environment":"indoor","goal":"Collect baseline recordings of ordinary home movements for the first MotionBlocks dataset.","participants":["child_01","adult_01"],"operator_id":"adult_01","device_ids":["m5_001"],"default_device_position":"wrist","default_wrist":"left","default_sample_rate_hz":10,"protocol":"Button-controlled recording. Button A starts/stops records. Button B switches to next session/file.","comments":"Initial educational dataset. Button press artifacts are expected at record boundaries.","status":"raw","tags":["baseline","home","ordinary_movements","education"]}
```

Recommended fields:

```text
experiment_id
title
started_at
ended_at
location
environment
goal
participants
operator_id
device_ids
default_device_position
default_wrist
default_sample_rate_hz
protocol
comments
status
tags
```

Notes:

* `experiment_id` should be stable and human-readable.
* Real names should not be stored in the repository.
* Use aliases such as `child_01`, `child_02`, `adult_01`, `mentor_01`.

Example `experiment_id` naming:

```text
exp_20260609_ordinary_home_movements
exp_20260610_fall_like_tests
exp_20260611_walking_stairs_home
```

---

## Recording session metadata format

Session/file-level metadata is stored in:

```text
data/metadata/recording_sessions.jsonl
```

One JSONL row describes one recording session / one raw CSV file.

Example:

```jsonl
{"session_id":"session_0001","experiment_id":"exp_20260609_ordinary_home_movements","file_id":1,"file_name":"session_0001.csv","file_role":"raw_data","data_format":"wide_csv","schema_version":"motionblocks.sample.v0.1","movement_type":"jumping","movement_label":"jumps_basic","subject_id":"child_01","device_id":"m5_001","started_at":"2026-06-09T15:35:00","sample_rate_hz":10,"records_expected":5,"records_actual":null,"channels":[{"name":"ax","kind":"acceleration","axis":"x","unit":"g"},{"name":"ay","kind":"acceleration","axis":"y","unit":"g"},{"name":"az","kind":"acceleration","axis":"z","unit":"g"},{"name":"gx","kind":"angular_velocity","axis":"x","unit":"deg_per_sec"},{"name":"gy","kind":"angular_velocity","axis":"y","unit":"deg_per_sec"},{"name":"gz","kind":"angular_velocity","axis":"z","unit":"deg_per_sec"},{"name":"acc_norm","kind":"derived_acceleration_norm","unit":"g"}],"comment":"Several jump attempts. Button press artifacts expected.","status":"raw"}
```

Recommended fields:

```text
session_id
experiment_id
file_id
file_name
file_role
data_format
schema_version
movement_type
movement_label
subject_id
device_id
started_at
sample_rate_hz
records_expected
records_actual
channels
comment
status
```

---

## Channel description

Each recording session should describe available measurement channels.

Current IMU channels:

```json
[
  {"name": "ax", "kind": "acceleration", "axis": "x", "unit": "g"},
  {"name": "ay", "kind": "acceleration", "axis": "y", "unit": "g"},
  {"name": "az", "kind": "acceleration", "axis": "z", "unit": "g"},
  {"name": "gx", "kind": "angular_velocity", "axis": "x", "unit": "deg_per_sec"},
  {"name": "gy", "kind": "angular_velocity", "axis": "y", "unit": "deg_per_sec"},
  {"name": "gz", "kind": "angular_velocity", "axis": "z", "unit": "deg_per_sec"},
  {"name": "acc_norm", "kind": "derived_acceleration_norm", "unit": "g"}
]
```

Possible future channels:

```json
[
  {"name": "heart_rate", "kind": "heart_rate", "unit": "bpm"},
  {"name": "skin_temperature", "kind": "temperature", "unit": "celsius"},
  {"name": "battery_voltage", "kind": "battery_voltage", "unit": "volt"},
  {"name": "step_count", "kind": "step_count", "unit": "count"}
]
```

Principle:

```text
New sensor values can be added as new CSV columns and described in metadata.channels.
```

This keeps raw files simple while preserving a path to a more universal FDAM model.

---

## Controlled vocabulary

Avoid uncontrolled labels such as:

```text
jump
jumps
jumping
прыжок
```

Use controlled values.

Initial `movement_type` candidates:

```text
idle
walking
running
jumping
shaking
stairs_up
stairs_down
falling_like
unknown
```

Example:

```text
movement_type  = jumping
movement_label = jumps_basic
```

`movement_type` is a broad controlled category.

`movement_label` is a more specific project-level label.

Future FDAM mapping:

```text
movement_type → MovementType enumeration / reference data
status        → DataStatus enumeration / reference data
file_role     → DataFileRole enumeration / reference data
data_format   → DataFormat enumeration / reference data
```

---

## Schema version

Each session should include a schema version:

```json
"schema_version": "motionblocks.sample.v0.1"
```

Purpose:

* track changes in raw CSV columns;
* support migration later;
* make future FDAM conversion safer.

Possible future versions:

```text
motionblocks.sample.v0.1 — IMU only: ax, ay, az, gx, gy, gz, acc_norm
motionblocks.sample.v0.2 — IMU + additional channels
motionblocks.sample.v0.3 — event-triggered high-rate windows
```

---

## Stable identifiers

Use stable ids at every level:

```text
experiment_id
session_id
file_id
record_id
sample_id
subject_id
device_id
```

Do not rely only on file names.

Recommended pattern:

```text
experiment_id = exp_YYYYMMDD_short_description
session_id    = session_0001
file_id       = 1
record_id     = 1, 2, 3...
sample_id     = 1, 2, 3...
device_id     = m5_001
subject_id    = child_01 / child_02 / adult_01
```

---

## Privacy rule

Do not store real child names in repository metadata.

Use aliases:

```text
child_01
child_02
adult_01
mentor_01
```

The mapping between aliases and real people should be stored separately and outside GitHub.

---

## FDAM compatibility

Current structure is not full FDAM yet, but should be FDAM-compatible.

Current prototype:

```text
experiments.jsonl
recording_sessions.jsonl
raw CSV files
```

Later FDAM mapping:

```text
experiments.jsonl
  → Experiment

recording_sessions.jsonl
  → RecordingSession
  → DataFile
  → references to Device, Subject, MovementType

raw CSV files
  → MotionSample fact table

channels[]
  → SensorChannel / MeasurementChannel registry

movement_type
  → MovementType enumeration

status
  → DataStatus enumeration

file_role
  → DataFileRole enumeration

data_format
  → DataFormat enumeration
```

This allows the project to remain simple now while keeping a clear path toward a formal FDAM motion domain.

---

## Current decision

Use this practical model now:

```text
1. Raw sensor data in wide CSV files.
2. Experiment metadata in experiments.jsonl.
3. Session/file metadata in recording_sessions.jsonl.
4. Stable identifiers and controlled vocabulary.
5. Channel descriptions in metadata.
6. FDAM conversion later, not now.
```

Do not introduce full FDAM modeling into the educational workflow for children.

The children-facing model remains:

```text
experiment → file/session → attempt/record → rows of data
```

The architecture-facing model remains ready for:

```text
CSV + JSONL → SQLite → FDAM YAML/domain model
```

---

## Open questions

* Should `channels` be repeated in every session row or moved to a separate device/schema registry?
* Should `file_id` be assigned by the device or by the Python logger?
* Should `records_actual` be filled manually or computed by the logger?
* Should events and data live in the same CSV or should events be separated into an event log?
* Should the first Python logger create draft metadata records automatically?
* When should we introduce SQLite as the next structured layer?

---

## Action items

* [ ] Create `data/metadata/experiments.jsonl`.
* [ ] Create `data/metadata/recording_sessions.jsonl`.
* [ ] Keep raw files in `data/raw/`.
* [ ] Use wide CSV for first raw data files.
* [ ] Include `experiment_id` in every session metadata row.
* [ ] Include `schema_version` and `channels` in session metadata.
* [ ] Avoid real names in metadata.
* [ ] Later create a converter from CSV + JSONL to SQLite / FDAM-compatible structure.

---

## Tags

#motionblocks #data-format #metadata #jsonl #csv #fdam #motion-domain #sensor-data
