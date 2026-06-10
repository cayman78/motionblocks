# MotionBlocks

**MotionBlocks** is a wearable motion intelligence project by **Stofendez Lab**.

The project explores how a small wearable device can collect, label, analyze, and later classify human motion patterns.

Current hardware target:

```text
M5StickC Plus2
```

Current development stack:

```text
VS Code
PlatformIO
Arduino framework
Python
CSV / JSON metadata
```

---

## Idea

MotionBlocks treats human movements as reusable **motion blocks**:

* idle / standing still;
* walking;
* standing up;
* sitting down;
* jumping;
* shaking hand;
* fall-like events;
* unusual motion patterns.

The long-term vision is to build a personal motion domain connected to external dashboards through **MotionLink** technology.

At the current stage, the project is intentionally simple:

```text
device → Serial → Python logger → CSV files → metadata → analysis
```

---

## Current status

The current working prototype can:

* read IMU data from M5StickC Plus2;
* compute acceleration norm on the device;
* start and stop motion records using device buttons;
* switch recording sessions using a device button;
* send structured Serial events and data rows;
* save session-based CSV files using a Python logger;
* optionally create draft metadata records for experiments and sessions.

Current firmware protocol:

```csv
EVENT,NEW_SESSION,session_id,timestamp_ms
EVENT,START,session_id,record_id,timestamp_ms
DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm
EVENT,STOP,session_id,record_id,timestamp_ms,sample_count
```

---

## Current project structure

```text
firmware/      Device firmware projects
tools/         Python tools for logging, metadata, plotting, and analysis
data/          Local generated data, ignored by Git except placeholders/docs
docs/          Human-readable project documentation and journal
llm/           LLM-oriented project context and takeaways
tests/         Future tests and validation scripts
```

Recommended data subfolders:

```text
data/
├── raw/          Generated raw CSV files
├── processed/    Future processed datasets
├── features/     Future extracted feature files
├── metadata/     Local generated metadata JSON files
├── db/           Future local SQLite databases
└── examples/     Small version-controlled examples, if needed
```

Generated local data should normally not be committed to Git.

---

## Firmware

Current firmware target:

```text
firmware/m5stickc-plus2
```

Build firmware:

```powershell
cd firmware/m5stickc-plus2
pio run
```

Upload firmware:

```powershell
pio run --target upload --upload-port COM6
```

Open Serial Monitor:

```powershell
pio device monitor --port COM6 --baud 115200
```

Close Serial Monitor before running the Python logger, because only one program can use `COM6` at a time.

---

## Python environment

Run Python tools from the repository root:

```powershell
cd C:\Users\XPS\Documents\proj\motionblocks
```

Create virtual environment:

```powershell
python -m venv .venv
```

Activate virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install pyserial
```

---

## Serial logger

Current logger:

```text
tools/serial_logger.py
```

Run from the repository root:

```powershell
python tools/serial_logger.py --port COM6 --experiment-id EXP01 --device-id m5_001
```

Run with draft metadata generation:

```powershell
python tools/serial_logger.py --port COM6 --experiment-id EXP01 --device-id m5_001 --create-metadata
```

Expected raw data output:

```text
data/raw/EXP01/m5_001/session_A001.csv
data/raw/EXP01/m5_001/session_A002.csv
```

Expected metadata output when `--create-metadata` is used:

```text
data/metadata/experiments.json
data/metadata/recording_sessions.json
```

Automatically created metadata records use status:

```text
auto created. needs description.
```

Existing metadata records are preserved and are not overwritten.

---

## Data model

Current practical hierarchy:

```text
Experiment
  → RecordingSession
      → DataFile
      → MotionRecord
          → MotionSample
              → Sensor values
```

Current raw CSV format:

```csv
row_type,session_id,record_id,sample_id,device_timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm,event_type,sample_count
```

Example raw path:

```text
data/raw/EXP01/m5_001/session_A001.csv
```

Example session uid:

```text
EXP01_m5_001_A001
```

---

## Responsibility split

The device firmware intentionally stays simple.

The firmware knows:

```text
session_id
record_id
sample_id
sensor data
```

The firmware does not know:

```text
experiment_id
device_id
subject_id
movement_type
movement_label
```

The Python logger provides:

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

---

## Metadata

Experiment metadata:

```text
data/metadata/experiments.json
```

Recording session metadata:

```text
data/metadata/recording_sessions.json
```

Metadata is currently stored as readable JSON files.

Draft metadata can be created automatically by the logger, but semantic fields should be completed manually later.

Typical fields to complete manually:

```text
short_name
title
location
goal
participants
movement_type
movement_label
subject_id
comment
tags
status
```

Privacy rule:

```text
Do not store real names of children in repository metadata.
Use aliases such as child_01, child_02, adult_01.
```

---

## Current sampling decision

Current default sampling mode:

```text
10 Hz
```

This is sufficient for:

* first IMU experiments;
* educational demonstrations;
* idle / rest detection;
* walking-like movements;
* slow arm movements;
* simple comparison of motion patterns.

Future modes:

```text
25 Hz   — normal educational motion recording
50 Hz   — fall-like events and sharper movements
100 Hz  — experimental / research mode
```

---

## Planned tools

Near-term planned tools:

```text
tools/plot_session.py
tools/compute_features.py
tools/metadata_tool.py
```

Planned purpose:

```text
plot_session.py      Plot raw session data
compute_features.py  Compute derived features from raw CSV
metadata_tool.py     Inspect and lightly manage JSON metadata
```

The metadata tool should remain intentionally small. It is not a database layer and not a full GUI browser.

---

## Future analysis ideas

Simple derived features:

```text
acc_norm_max
acc_norm_mean
acc_norm_std
gyro_norm
gyro_norm_max
jerk_norm
record_duration
sample_count
```

Experimental future features:

```text
estimated_path_length
estimated_displacement_norm
estimated_vertical_displacement
vertical_drop_score
peak_velocity_estimate
impact_after_drop_score
```

These future trajectory-like features should be computed in Python analysis scripts, not on the device and not in the Serial logger.

---

## Branch workflow

Use feature branches for development.

Examples:

```text
feature/first-firmware
feature/imu-serial-logger
feature/button-controlled-logger
feature/session-aware-logger
feature/python-serial-logger
```

`main` should remain stable.

Typical workflow:

```powershell
git status
git add .
git commit -m "Commit message"
git push
```

---

## Current next steps

1. Keep generated data ignored by Git.
2. Commit current logger and metadata updates.
3. Collect the first small real dataset.
4. Complete metadata manually.
5. Implement simple plotting for session CSV files.
6. Implement basic feature extraction.
7. Evaluate which features are useful for motion classification.

---

## Project principles

* Keep the device simple.
* Keep the Serial logger simple.
* Store raw data in readable CSV.
* Store metadata in readable JSON.
* Avoid premature database complexity.
* Do not overbuild tools before real data appears.
* Keep the structure compatible with future FDAM-style modeling.
* Make the project understandable for children and useful for serious analysis later.
