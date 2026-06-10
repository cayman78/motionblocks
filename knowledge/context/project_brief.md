# MotionBlocks — Project Brief

## Project

MotionBlocks is a wearable motion intelligence project by Stofendez Lab.

The project explores how a small wearable device can collect, label, analyze, and later classify human motion patterns.

Current hardware target:

```text
M5StickC Plus2
```

Current working mode:

```text
wearable device → Wi-Fi → HTTP logger → CSV files → metadata
```

The previous wired Serial mode is still kept for debugging and fallback.

## Key idea

Human movements are treated as reusable "motion blocks".

Examples:

- idle / standing still;
- walking;
- standing up;
- sitting down;
- jumping;
- shaking hand;
- fall-like events;
- unusual motion patterns.

The system collects motion records, stores them as session-based raw data, links them with metadata, analyzes patterns, and later may detect unusual or risky motion sequences.

The current focus is not yet advanced classification. The current focus is a stable data collection pipeline.

## Long-term vision

MotionBlocks may become a personal motion domain inside the Human-by-Wire architecture.

The motion domain can be connected through MotionLink technology to:

- family dashboard;
- caregiver dashboard;
- medical dashboard;
- external Human-by-Wire domains.

MotionLink is the future communication / integration layer for connecting the personal motion domain to external systems.

## Current stage

Stage 4: Wireless HTTP logging and first wearable dataset.

Completed earlier stages:

- GitHub repository and basic project workflow;
- M5StickC Plus2 firmware bring-up;
- IMU reading;
- acceleration norm calculation;
- button-controlled recording;
- session-aware logging;
- Python Serial logger;
- draft metadata generation;
- improved device display layout;
- Python HTTP logger;
- Wi-Fi configuration layer;
- wireless HTTP output from firmware.

Current goals:

- stabilize wireless recording;
- collect first real wearable mini-dataset;
- manually complete experiment and session metadata;
- implement simple plotting for session CSV files;
- later implement basic feature extraction.

Current working pipeline:

```text
M5StickC Plus2
  → Wi-Fi
  → HTTP POST /line
  → tools/http_logger.py
  → data/raw/[experiment_id]/[device_id]/session_[session_id].csv
  → data/metadata/experiments.json
  → data/metadata/recording_sessions.json
```

Fallback / debugging pipeline:

```text
M5StickC Plus2
  → USB Serial
  → tools/serial_logger.py
  → CSV files
  → metadata
```

## Hardware

Current device:

```text
M5StickC Plus2
```

Current sensors used:

- accelerometer;
- gyroscope.

Current derived value calculated on device:

```text
acc_norm = sqrt(ax^2 + ay^2 + az^2)
```

Current button behavior:

```text
Button A double click → start record
Button A single click during recording → stop record
Button B → next session
```

## Development stack

- VS Code
- PlatformIO
- Arduino framework
- M5Unified
- Python
- CSV
- JSON metadata
- GitHub
- optional later: SQLite, Edge Impulse, ChatGPT Data Analysis, Orange Data Mining

SQLite remains a likely future storage layer, but the current stage intentionally stays with readable CSV and JSON files.

## Repository

Repository name:

```text
motionblocks
```

Current important folders:

```text
firmware/      Device firmware projects
tools/         Python tools for logging and analysis
data/          Local generated data, ignored by Git except placeholders/docs
docs/          Human-readable project documentation and journal
llm/           LLM-oriented project context and takeaways
tests/         Future tests and validation scripts
```

Generated local data should normally not be committed to Git:

```text
data/raw/
data/processed/
data/features/
data/metadata/
data/db/
```

Only placeholders, documentation, or intentionally prepared examples should be version-controlled.

## Naming

- Stofendez Lab — laboratory / team
- MotionBlocks — project
- MotionLink — future technology for linking the personal motion domain to external dashboards
- HTTP logger — Python receiver for wireless device data
- Serial logger — Python receiver for wired USB Serial data

## Firmware protocol

The firmware sends the same protocol through Serial and HTTP.

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
EVENT,STOP,A001,1,19000,60
```

Design rule:

```text
The transport may change.
The protocol should remain stable.
```

## Responsibility split

The firmware intentionally remains simple.

The device knows:

```text
session_id
record_id
sample_id
sensor data
```

The device does not know:

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

The metadata layer provides:

```text
subject_id
movement_type
movement_label
location
comments
status
tags
```

This keeps the device generic and reusable across experiments.

## Data layout

Raw data path:

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

Session UID format:

```text
[experiment_id]_[device_id]_[session_id]
```

Example:

```text
EXP01_m5_001_A001
```

## Metadata generation

Both `serial_logger.py` and `http_logger.py` can create draft metadata records.

Metadata generation is explicit and controlled by:

```powershell
--create-metadata
```

Automatically created records use status:

```text
auto created. needs description.
```

Important rule:

```text
Existing metadata records are preserved and not overwritten.
```

This prevents manually completed metadata from being destroyed by the logger.

## Current Python tools

Current tools:

```text
tools/serial_logger.py
tools/http_logger.py
```

`serial_logger.py`:

```text
reads protocol lines from COM port
writes session CSV files
optionally creates draft metadata
```

`http_logger.py`:

```text
starts local HTTP server
accepts POST /line
writes session CSV files
optionally creates draft metadata
```

HTTP logger run command:

```powershell
python tools/http_logger.py --host 0.0.0.0 --port 8080 --experiment-id EXP01 --device-id m5_001 --create-metadata
```

Health check:

```text
GET /health
```

Data endpoint:

```text
POST /line
```

## Wi-Fi configuration

Firmware uses a local Wi-Fi config file:

```text
firmware/m5stickc-plus2/src/wifi_config.h
```

This file contains:

```cpp
WIFI_SSID
WIFI_PASSWORD
LOGGER_URL
```

The real `wifi_config.h` must not be committed to Git.

The repository keeps only the example file:

```text
firmware/m5stickc-plus2/src/wifi_config.example.h
```

Example logger endpoint:

```cpp
#define LOGGER_URL "http://192.168.8.129:8080/line"
```

The actual IP depends on the notebook Wi-Fi address.

Important Windows network note:

```text
For iPad / M5StickC to reach the HTTP logger,
Windows network profile must be Private, not Public.
```

## Sampling decision

Current default sampling rate:

```text
10 Hz
```

Rationale:

- small files;
- simple debugging;
- sufficient for first educational experiments;
- stable enough for initial HTTP logging.

Future sampling modes:

```text
10 Hz   — first prototype / education
25 Hz   — normal educational motion recording
50 Hz   — fall-like events / sharper movements
100 Hz  — experimental / research mode
```

## Current next step

The immediate next step is to collect the first real mini-dataset in wireless mode.

Suggested experiment:

```text
EXP01 — ordinary_home_movements
```

Suggested sessions:

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

## Near-term planned tools

Planned next tools:

```text
tools/plot_session.py
tools/compute_features.py
tools/metadata_tool.py
```

`plot_session.py`:

```text
read one session CSV
plot acc_norm over time
plot ax/ay/az
plot gx/gy/gz
```

`compute_features.py`:

```text
compute simple features per record
acc_norm_max
acc_norm_mean
acc_norm_std
gyro_norm_max
record_duration
sample_count
```

`metadata_tool.py`:

```text
small helper for metadata inspection
list experiments
list sessions
show session
mark session status
check file consistency
```

Important boundary:

```text
metadata_tool.py is not a database layer.
metadata_tool.py is not a GUI browser.
metadata_tool.py should remain small.
```

## Future analysis ideas

Reliable / near-term derived features:

```text
acc_norm
gyro_norm
jerk_norm
acc_norm_max_window
gyro_norm_max_window
post_event_rest_ratio
orientation_change_proxy
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

These trajectory-like features should be computed later in Python analysis scripts, not in firmware and not in the logger.

Important terminology:

```text
Use: experimental IMU-only displacement features
Avoid: exact trajectory / true coordinates
```

## Design principles

Current project principles:

```text
Keep the device simple.
Keep loggers simple.
Do not overbuild before real data appears.
Use readable CSV for raw data.
Use readable JSON for metadata.
Preserve Serial output for debugging.
Use Wi-Fi HTTP as the first wireless transport.
Do not move to database too early.
Stay compatible with future FDAM-style modeling.
Keep the project understandable for children.
```

## Open questions

Current open questions:

```text
How stable is HTTP POST at 10 Hz during real wrist motion?
Do we need batching or buffering on the device?
Should HTTP logger update records_actual automatically after STOP?
Should metadata contain connection/transport information?
What is the practical battery life in Wi-Fi logging mode?
When should we move from JSON metadata to SQLite?
When should we implement plot_session.py?
When should we introduce 25 Hz / 50 Hz modes?
```
