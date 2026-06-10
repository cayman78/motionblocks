# Current State

## Date

2026-06-10

## Current project phase

Stage 4 — Wireless HTTP logging and first wearable data collection.

The project has moved beyond initial device bring-up, wired Serial logging, and display cleanup.

The current working pipeline is:

```text
M5StickC Plus2
  → Wi-Fi
  → HTTP POST /line
  → tools/http_logger.py
  → session CSV files
  → draft metadata
```

The previous USB Serial pipeline still exists and remains useful for debugging, but the main practical path for real movement experiments is now wireless HTTP logging.

Current immediate goal:

```text
collect the first real mini-dataset in wireless mode
```

---

## Project identity

* Laboratory / team: **Stofendez Lab**
* Project: **MotionBlocks**
* Future technology layer: **MotionLink**

MotionBlocks is an educational and technical project for collecting, labeling, and analyzing human motion data from wearable sensors.

The current hardware target is:

```text
M5StickC Plus2
```

---

## Current firmware status

Current working firmware:

```text
IMU logger v0.4 — Wi-Fi HTTP session-aware button-controlled logger
```

Current working branch:

```text
feature/wifi-http-logger
```

Current firmware capabilities:

* reads IMU data from M5StickC Plus2;
* calculates `acc_norm`;
* supports button-controlled recording;
* manages sessions and records;
* sends the same protocol lines through Serial and HTTP;
* connects to Wi-Fi using local `wifi_config.h`;
* sends protocol lines to Python HTTP logger using `HTTPClient`;
* shows a startup splash screen;
* shows Wi-Fi status / IP address on the READY screen;
* shows current record metrics on the REC screen.

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

## Current protocol

The firmware sends the same protocol through both Serial and HTTP:

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

Current design decision:

```text
The protocol format remains stable.
Only the transport changes: Serial and/or HTTP.
```

---

## Current transport status

### Wired debug path

```text
M5StickC Plus2 → USB Serial / COM6 → tools/serial_logger.py
```

Status:

```text
working / useful for debugging
```

### Wireless working path

```text
M5StickC Plus2
  → Wi-Fi
  → HTTP POST /line
  → tools/http_logger.py
  → CSV / metadata
```

Status:

```text
working
```

The Python HTTP logger is launched from repository root:

```powershell
python tools/http_logger.py --host 0.0.0.0 --port 8080 --experiment-id EXP01 --device-id m5_001 --create-metadata
```

HTTP endpoints:

```text
GET  /health
POST /line
```

Current local network note:

```text
For iPad / M5StickC to reach the Python HTTP logger,
Windows network profile must be Private, not Public.
```

During the first successful test, the notebook Wi-Fi IP was:

```text
192.168.8.129
```

The corresponding firmware logger endpoint was:

```cpp
#define LOGGER_URL "http://192.168.8.129:8080/line"
```

---

## Wi-Fi configuration

Firmware uses a local config file:

```text
firmware/m5stickc-plus2/src/wifi_config.h
```

It contains:

```cpp
WIFI_SSID
WIFI_PASSWORD
LOGGER_URL
```

The real `wifi_config.h` contains Wi-Fi credentials and must not be committed to Git.

Repository contains only:

```text
firmware/m5stickc-plus2/src/wifi_config.example.h
```

Current rule:

```text
wifi_config.example.h → committed
wifi_config.h         → local only / ignored by Git
```

---

## Device display status

The display was cleaned up and now behaves like a small logger instrument panel.

Startup splash screen:

```text
MOTIONBLOCKS
LOGGER
Stofendez Lab
```

READY screen:

```text
WiFi <device_ip>
READY
SESSION A001
A x2 START     B NEXT
```

REC screen:

```text
REC
A001 / R1
SMP <sample_count>
ACC <acc_norm> g
A STOP
```

Display status:

```text
working / acceptable for prototype
```

Further visual polishing is not a priority now.

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

Generated data is local and normally ignored by Git.

---

## Current metadata files

Use readable JSON files for manual editing:

```text
data/metadata/experiments.json
data/metadata/recording_sessions.json
```

Both loggers can create draft metadata records:

```text
tools/serial_logger.py
tools/http_logger.py
```

Metadata generation is explicit and controlled by:

```powershell
--create-metadata
```

Automatically created metadata records use status:

```text
auto created. needs description.
```

Important rule:

```text
Existing metadata records are preserved and not overwritten.
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
* stable enough for initial HTTP logging;
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
* Use feature branches for meaningful changes.
* Use `main` as stable branch.
* Use private GitHub repository at the start.
* Use raw CSV files for first data collection.
* Use readable JSON files for metadata.
* Use Wi-Fi HTTP as the first wireless transport.
* Keep USB Serial available for debugging.
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
* Python Serial logger works.
* Draft metadata generation works.
* Generated data is ignored by Git.
* Metadata format agreed:

  * `experiments.json`
  * `recording_sessions.json`
* Raw data path convention agreed:

  * `data/raw/[experiment_id]/[device_id]/session_[session_id].csv`
* Device display layout improved.
* `wifi_config.example.h` added.
* Real `wifi_config.h` excluded from Git.
* Python HTTP logger works.
* HTTP logger reachable from iPad on local network.
* M5StickC connects to Wi-Fi.
* Firmware sends protocol lines over HTTP.
* Wireless recording works.

---

## Current branch status

Completed / working branches:

```text
feature/first-firmware
feature/imu-serial-logger
feature/button-controlled-logger
feature/session-aware-logger
feature/python-serial-logger
feature/display-layout
feature/wifi-http-logger
```

Current active branch:

```text
feature/wifi-http-logger
```

---

## Current next actions

### 1. Commit wireless HTTP firmware

Commit message:

```text
Add Wi-Fi HTTP output to device logger
```

Expected files:

```text
firmware/m5stickc-plus2/src/main.cpp
docs/journal.md
```

Do not commit:

```text
firmware/m5stickc-plus2/src/wifi_config.h
data/raw/
data/metadata/
```

### 2. Update project context files

Update:

```text
llm/context/project_brief.md
llm/context/current_state.md
```

Recommended commit message:

```text
Update project context after wireless logging milestone
```

### 3. Collect first real mini-dataset

Initial experiment:

```text
EXP01 — Замеры ординарных движений дома
```

Possible sessions:

```text
A001 — standing_idle
A002 — walking_normal
A003 — hand_shaking
A004 — jumps_basic
A005 — sitting_to_standing
```

For each session:

```text
3–5 records
short controlled movements
manual metadata review after recording
```

### 4. Basic plotting

After first CSV files are collected, implement a simple plotting script:

```text
tools/plot_session.py
```

Minimum goal:

* read one session CSV;
* plot `acc_norm` over time;
* separate records by `record_id`;
* optionally plot `ax/ay/az` and `gx/gy/gz`.

---

## Planned utility — minimal metadata tool

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

---

## Planned analysis layer — experimental IMU-only displacement features

Later we plan to explore experimental derived motion features based on IMU-only trajectory approximation.

This should not be implemented in firmware now.

Current rule:

```text
Device stays simple.
Serial / HTTP loggers stay simple.
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

---

## Open questions

* How stable is HTTP POST at 10 Hz during real wrist motion?
* Do we need batching or buffering on the device?
* What is the practical battery life in Wi-Fi logging mode?
* Should Python logger update `records_actual` automatically after STOP?
* Should metadata contain connection / transport information?
* Should `channels` be repeated in each recording session or moved to a shared schema/device registry?
* Should events and DATA rows live in the same CSV, or should event logs be separated later?
* Should `device_id` ever be stored in firmware, or always supplied by the logger?
* When should SQLite be introduced?
* When should MQTT be introduced as a separate IoT lesson?
* Should Button A double click remain the start action, or should UX be simplified to start/stop toggle later?
* When should 25 Hz / 50 Hz modes be introduced?
