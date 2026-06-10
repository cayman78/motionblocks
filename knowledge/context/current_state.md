# Current State

## Date

2026-06-10

## Current project phase

Stage 2 — Button-controlled recording and file/session-aware data collection.

The project has moved beyond initial device bring-up. The M5StickC Plus2 can now read IMU data, start and stop recordings by button, and manage recording sessions.

The next major step is to implement the Python Serial logger that will save device output into structured CSV files.

---

## Project identity

* Laboratory / team: **Stofendez Lab**
* Project: **MotionBlocks**
* Future technology layer: **MotionLink**

MotionBlocks is an educational and technical project for collecting, labeling, and analyzing human motion data from wearable sensors.

---

## Current firmware status

Current working firmware:

```text
IMU logger v0.3 — session-aware button-controlled logger
```

Current firmware branch:

```text
feature/session-aware-logger
```

Confirmed behavior:

* Device starts with session `A001`.
* Button A double click starts a new record.
* Button A single click stops the current record.
* Button B switches to the next session.
* `record_id` resets to `1` when session changes.
* `sample_id` increments inside each record.
* IMU data is sent only while recording.
* `acc_norm` is calculated as:

```text
sqrt(ax*ax + ay*ay + az*az)
```

* In rest position, `acc_norm` should be close to `1.0 g`.
* Firmware does not know `experiment_id`, `device_id`, `subject_id`, `movement_type`, or `movement_label`.

---

## Firmware responsibility

The firmware manages only device-local recording state:

```text
session_id
record_id
sample_id
sensor data
```

The firmware does **not** manage experiment-level or dataset-level context.

The following are assigned outside the firmware:

```text
experiment_id
device_id
subject_id
movement_type
movement_label
file_path
metadata
```

This keeps the device generic and reusable across experiments.

---

## Current Serial protocol

The current firmware prints the following protocol to Serial:

```csv
EVENT,NEW_SESSION,session_id,timestamp_ms
EVENT,START,session_id,record_id,timestamp_ms
DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm
EVENT,STOP,session_id,record_id,timestamp_ms,sample_count
```

Example:

```csv
EVENT,NEW_SESSION,A001,12345
EVENT,START,A001,1,13000
DATA,A001,1,1,13100,0.0123,-0.0341,0.9872,0.1200,-0.0300,0.0100,0.9880
DATA,A001,1,2,13200,0.0130,-0.0338,0.9869,0.1100,-0.0400,0.0200,0.9878
EVENT,STOP,A001,1,19000,60
EVENT,NEW_SESSION,A002,22000
```

---

## Current data format decision

Use simple raw CSV files for sensor data and readable JSON files for metadata.

Current raw data path convention:

```text
data/raw/[experiment_id]/[device_id]/session_[session_id].csv
```

Example:

```text
data/raw/EXP01/m5_001/session_A001.csv
data/raw/EXP01/m5_001/session_A002.csv
data/raw/EXP01/m5_002/session_A001.csv
```

The experiment is defined by the folder and metadata, not by the firmware.

---

## Current metadata files

Use readable JSON files for manual editing:

```text
data/metadata/experiments.json
data/metadata/recording_sessions.json
```

JSONL may be introduced later for append-only automated logging, but for now readable JSON is preferred.

### Experiment identifiers

Use short technical experiment ids:

```text
EXP01
EXP02
EXP03
```

Human-readable names live in metadata:

```text
short_name
title
goal
comments
```

Example:

```json
{
  "experiment_id": "EXP01",
  "short_name": "ordinary_home_movements",
  "title": "Замеры ординарных движений дома"
}
```

### Session identifiers

Use short session ids inside each device/experiment context:

```text
A001
A002
A003
```

Use globally unique session uid in metadata:

```text
session_uid = EXP01_m5_001_A001
```

Example session metadata:

```json
{
  "experiment_id": "EXP01",
  "device_id": "m5_001",
  "session_id": "A001",
  "session_uid": "EXP01_m5_001_A001",
  "file_name": "session_A001.csv",
  "file_path": "data/raw/EXP01/m5_001/session_A001.csv",
  "subject_id": "child_01",
  "movement_type": "jumping",
  "movement_label": "jumps_basic"
}
```

---

## Current raw CSV format

Current raw CSV is wide format.

Recommended columns:

```csv
row_type,session_id,record_id,sample_id,device_timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm,event_type,sample_count
```

Example:

```csv
row_type,session_id,record_id,sample_id,device_timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm,event_type,sample_count
EVENT,A001,,,12345,,,,,,,,NEW_SESSION,
EVENT,A001,1,,13000,,,,,,,,START,
DATA,A001,1,1,13100,0.0123,-0.0341,0.9872,0.1200,-0.0300,0.0100,0.9880,,
EVENT,A001,1,,19000,,,,,,,,STOP,60
```

Wide CSV is chosen because it is easy to inspect, plot, and explain to children.

Future FDAM / database layers may transform it into a normalized fact model.

---

## Current schema version

Current sample schema version:

```text
motionblocks.sample.v0.1
```

Current channels:

```text
ax
ay
az
gx
gy
gz
acc_norm
```

Possible future channels:

```text
heart_rate
skin_temperature
battery_voltage
step_count
```

Each recording session metadata row should describe available channels.

---

## Current sampling decision

Default sampling rate for the current educational prototype:

```text
10 Hz
```

Rationale:

* simple to debug;
* small CSV files;
* enough for first motion experiments;
* easy to transmit over Serial;
* good for idle, walking, slow movements, basic jumps.

Future target rates:

```text
25 Hz   — normal motion classification
50 Hz   — fall-like events and sharper movements
100 Hz  — research / stress-test mode
```

Adaptive high-rate event-triggered sampling is a future idea, not a current priority.

---

## Current architecture decisions

* Use VS Code + PlatformIO + Arduino framework.
* Use M5StickC Plus2 as the first device.
* Use Serial / COM6 as the current transport.
* Use feature branches for meaningful changes.
* Use `main` as stable branch.
* Use private GitHub repository at the start.
* Use raw CSV files for first data collection.
* Use readable JSON files for metadata.
* Use SQLite later, after first real data files are collected.
* Do not store real names of children in repository data or metadata.
* Use aliases such as:

```text
child_01
child_02
adult_01
mentor_01
```

---

## Transport decision

Current transport:

```text
M5StickC Plus2 → USB Serial / COM6 → Python logger
```

Wireless transport is postponed.

Current position:

```text
First stabilize wired pipeline.
Then implement Wi-Fi HTTP proof of concept.
Later introduce MQTT as IoT/event-bus lesson.
```

MQTT is considered useful for future MotionLink/event-bus architecture, but not as the first wireless protocol.

---

## FDAM compatibility

Current structure is intentionally simple, but should remain compatible with a future FDAM motion domain.

Current practical model:

```text
Experiment
  → RecordingSession
      → DataFile
      → MotionRecord
          → MotionSample
              → Sensor values / channels
```

Future FDAM mapping:

```text
experiments.json
  → Experiment

recording_sessions.json
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

Children should not be exposed to FDAM concepts directly. The children-facing model remains:

```text
experiment → device → session/file → attempt/record → rows of data
```

---

## Done

* Project identity selected:

  * Stofendez Lab
  * MotionBlocks
  * MotionLink
* GitHub repository created.
* Basic repository structure planned.
* `llm/` project memory structure discussed.
* PlatformIO installed and tested.
* M5StickC Plus2 detected as USB serial device.
* First firmware uploaded successfully.
* Screen output works.
* Serial output works.
* IMU logger v0.1 works.
* `M5.Imu.update()` issue discovered and fixed.
* Button-controlled IMU logger v0.2 works.
* Session-aware IMU logger v0.3 works.
* Button A start/stop logic works.
* Button B next-session logic works.
* Metadata format agreed:

  * `experiments.json`
  * `recording_sessions.json`
* Raw data path convention agreed:

  * `data/raw/[experiment_id]/[device_id]/session_[session_id].csv`

---

## Current branch status

Completed / working branches:

```text
feature/first-firmware
feature/imu-serial-logger
feature/button-controlled-logger
feature/session-aware-logger
```

Next branch:

```text
feature/python-serial-logger
```

---

## Next actions

### 1. Commit current firmware

Commit message:

```text
Add session id to button-controlled logger
```

### 2. Create Python serial logger branch

```text
feature/python-serial-logger
```

### 3. Implement Python Serial logger

Expected command:

```powershell
python tools/serial_logger.py --port COM6 --experiment-id EXP01 --device-id m5_001
```

Expected output:

```text
data/raw/EXP01/m5_001/session_A001.csv
data/raw/EXP01/m5_001/session_A002.csv
```

Logger responsibilities:

* listen to COM6;
* parse `EVENT,NEW_SESSION`;
* create the proper experiment/device folder;
* open `session_[session_id].csv`;
* write START / DATA / STOP rows;
* flush data safely;
* close or switch files when session changes.

### 4. Collect first real dataset

Initial experiment:

```text
EXP01 — Замеры ординарных движений дома
```

Possible sessions:

```text
A001 — jumping / jumps_basic
A002 — walking / walking_normal
A003 — idle / standing_idle
A004 — shaking / hand_shaking
```

### 5. Basic plotting

After first CSV files are collected, implement a simple plotting script:

```text
tools/plot_session.py
```

Minimum goal:

* read one session CSV;
* plot `acc_norm` over time;
* separate records by `record_id`.

---

### 6. Planned utility — minimal metadata tool

A small metadata utility is planned, but it should remain intentionally limited.

Purpose:

* inspect existing experiments;
* inspect recording sessions;
* find sessions that still need description;
* check consistency between metadata and raw CSV files;
* mark unnecessary or bad sessions without physically deleting data.

Working name:

```text
tools/metadata_tool.py
```

Initial commands:

```text
list-experiments
list-sessions --experiment-id EXP01
list-sessions --status "auto created. needs description."
show-session --session-uid EXP01_m5_001_A001
mark-session --session-uid EXP01_m5_001_A001 --status bad
check-files
```

Current boundary:

```text
This is not a database layer.
This is not a GUI browser.
This is not a full data management application.
```

Do not implement yet:

* physical deletion of CSV files;
* interactive UI;
* full metadata editor;
* complex search;
* schema migrations.

Rationale:

The current JSON-based metadata layer is temporary and lightweight.
For serious data management, a database will be more appropriate later.

The utility should only reduce manual friction while we are still collecting early prototype data.

Status:

```text
planned
```
### 7. Planned analysis layer — experimental IMU-only displacement features

Later we plan to explore experimental derived motion features based on IMU-only trajectory approximation.

This should not be implemented in firmware now.

Current rule:

```text
Device stays simple.
Serial logger stays simple.
Trajectory-like features are computed later in Python analysis scripts.
```

Possible future script:

```text
tools/compute_features.py
```

Possible output:

```text
data/features/[experiment_id]/[device_id]/session_[session_id]_features.json
```

or:

```text
data/processed/[experiment_id]/[device_id]/session_[session_id]_features.csv
```

The goal is not to reconstruct the true physical trajectory with high precision.

The goal is to compute experimental metrics that may correlate with fall-like events:

```text
estimated_path_length
estimated_displacement_norm
estimated_vertical_displacement
vertical_drop_score
peak_velocity_estimate
impact_after_drop_score
```

Basic idea:

```text
For each record:
  velocity = 0 at record start
  position = 0 at record start
  estimate initial gravity from first samples
  estimate orientation from gyro integration
  transform acceleration to approximate world frame
  subtract gravity
  integrate acceleration to velocity
  integrate velocity to position
  compute displacement/path metrics
```

Important limitation:

```text
These are experimental IMU-only estimates.
They are not reliable physical coordinates.
They may drift due to sensor bias, gravity compensation error, and orientation error.
```

Reason for still keeping this idea:

```text
Even noisy displacement-like metrics may be useful as weak features for fall-like classification, especially for short records reset at each record_id.
```

Implementation status:

```text
planned / future
```

Do not implement yet:

* on-device trajectory calculation;
* firmware-side orientation tracking;
* real-time fall detection;
* use of displacement estimate as a single decisive fall signal.

Next step before implementation:

```text
Collect labeled examples first:
idle
walking
jumping
shaking
fall_like
```

Then evaluate whether displacement-like metrics are actually useful.


## Open questions

* Should Python logger create draft metadata records automatically?
* Should metadata be updated manually first, or generated by logger with `status = needs_description`?
* Should `channels` be repeated in each recording session or moved to a shared schema/device registry?
* Should events and DATA rows live in the same CSV, or should event logs be separated later?
* Should `device_id` ever be stored in firmware, or always supplied by the logger?
* When should SQLite be introduced?
* When should Wi-Fi HTTP proof of concept be introduced?
* When should MQTT be introduced as a separate IoT lesson?
* Should Button A double click remain the start action, or should UX be simplified to start/stop toggle later?
