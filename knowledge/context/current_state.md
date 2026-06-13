# Current State

## Date

2026-06-13 (updated end of day)

## Current project phase

Stage 5 — Safe data collection with recording_run_id and firmware UX improvements.

The project has completed wireless HTTP batch logging, device identity, selectable sampling rate, recording_run_id implementation, safe file names, and firmware UX improvements.

The current working pipeline is:

```text
M5StickC Plus2 (v0.7.0)
  → Wi-Fi
  → HTTP POST /line
  → one-line service events + batched DATA during recording
  → tools/http_logger.py
  → run_A_session_A001_100Hz.csv
  → draft metadata with recording_run_id
```

The previous USB Serial pipeline still exists and remains useful for debugging and fallback.

Current immediate goal:

```text
update serial_logger.py with recording_run_id and safe file names
then build tools/analyze_recordings.py
```

---

## Project identity

* Laboratory / team: **Stofendez Lab**
* Project: **MotionBlocks**
* Future technology layer: **MotionLink**

MotionBlocks is an educational and technical project for collecting, labeling, analyzing, and later classifying human motion data from wearable sensors.

The current hardware target is:

```text
M5StickC Plus2
```

---

## Current firmware status

Current working firmware:

```text
motionblocks.logger.v0.7.0 — selectable sampling rate + HTTP batch + UX improvements
```

Current active branch:

```text
main (feature/recording-runs-and-safe-file-names merged)
```

Current firmware capabilities:

* reads IMU data from M5StickC Plus2;
* calculates `acc_norm`;
* supports button-controlled recording;
* manages device-local sessions and records;
* reports technical device identity through `EVENT,DEVICE_INFO`;
* supports sampling-rate selection at startup;
* reports selected rate through `EVENT,SAMPLE_RATE`;
* sends the same protocol lines through Serial and HTTP;
* connects to Wi-Fi using local `wifi_config.h`;
* uses HTTP batch mode for `DATA` rows during recording;
* keeps Serial output immediate for debugging;
* shows a startup splash screen;
* shows Wi-Fi status / IP address on the READY screen;
* shows selected sample rate on the READY screen;
* shows current record metrics on the REC screen;
* shows Wi-Fi indicator (green/red dot) on the REC screen;
* shows SAVED screen with sample count after stopping a record.

Confirmed behavior:

* Device starts with session `A001`.
* Button A double click (600 ms window) starts a new record.
* Button A single click stops the current record.
* Button B switches to the next session.
* `record_id` resets to `1` when session changes.
* `sample_id` increments inside each record.
* IMU data is sampled only while recording.
* `acc_norm` is calculated as:

```text
sqrt(ax*ax + ay*ay + az*az)
```

* In rest position, `acc_norm` should be close to `1.0 g`.
* Firmware does not know `experiment_id`, project-level `device_id`, `subject_id`, `movement_type`, or `movement_label`.

Known firmware / transport limits:

* `session_id` is device-local and can repeat after device reset (handled by logger-side `recording_run_id`).
* `sample_rate_hz` means configured / selected rate, not verified effective rate.
* Effective sampling rate must be calculated later from `DATA.device_timestamp_ms`.
* Long recording stability and battery life are not yet measured.

---

## Firmware responsibility

The firmware manages only device-local and technical state:

```text
session_id
record_id
sample_id
sensor data
technical device identity
firmware version
configured sample rate
```

The firmware does **not** manage experiment-level or dataset-level context.

The following are assigned outside the firmware:

```text
experiment_id
project-level device_id
recording_run_id
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
EVENT,DEVICE_INFO,mac_address,firmware_version,timestamp_ms
EVENT,SAMPLE_RATE,sample_rate_hz,timestamp_ms
EVENT,NEW_SESSION,session_id,timestamp_ms
EVENT,START,session_id,record_id,timestamp_ms
DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm
EVENT,STOP,session_id,record_id,timestamp_ms,sample_count
```

Example:

```csv
EVENT,DEVICE_INFO,F0:24:F9:97:ED:08,motionblocks.logger.v0.6.2,6972
EVENT,SAMPLE_RATE,100,7200
EVENT,NEW_SESSION,A001,7425
EVENT,START,A001,1,13000
DATA,A001,1,1,13100,0.0123,-0.0341,0.9872,0.1200,-0.0300,0.0100,0.9880
DATA,A001,1,2,13110,0.0130,-0.0338,0.9869,0.1100,-0.0400,0.0200,0.9878
EVENT,STOP,A001,1,19000,600
```

Current design decision:

```text
The protocol format remains stable.
Transport may change.
HTTP batch mode does not change the protocol.
It only changes how multiple DATA lines are transported.
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

Serial output remains immediate line-by-line.

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

Current HTTP behavior:

```text
IDLE:
  DEVICE_INFO  → one-shot HTTP POST
  SAMPLE_RATE  → one-shot HTTP POST
  NEW_SESSION  → one-shot HTTP POST

RECORDING:
  START → immediate HTTP POST through recording client
  DATA  → buffered and sent in batches
  STOP  → flush DATA batch first, then send STOP
```

Current batch parameters:

```cpp
HTTP_BATCH_MAX_LINES = 25
HTTP_BATCH_MAX_AGE_MS = 500
```

Confirmed transport result:

```text
100 Hz works in the current HTTP batch test
```

Earlier findings:

```text
per-sample HTTP POST was insufficient for 25 / 50 Hz
HTTP keep-alive per sample did not solve the problem
HTTP batch mode solved the current transport bottleneck
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

`POST /line` may contain either:

```text
one protocol line
```

or:

```text
newline-separated batch of protocol lines
```

The logger treats both forms the same by splitting the HTTP body into lines.

Current local network note:

```text
For iPad / M5StickC to reach the Python HTTP logger,
Windows network profile must be Private, not Public.
```

If HTTP fails with `code=-1`, check:

```text
http_logger.py is running
LOGGER_URL IP is correct
Windows network profile is Private
firewall allows Python on Private networks
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

Example logger endpoint:

```cpp
#define LOGGER_URL "http://192.168.8.129:8080/line"
```

The actual IP depends on the notebook Wi-Fi address.

---

## Device display status

The display behaves like a small logger instrument panel.

Startup splash screen:

```text
MOTIONBLOCKS
LOGGER
Stofendez Lab
```

Sampling-rate selection screen:

```text
SAMPLE RATE
  5 Hz
> 10 Hz       ← selected, green, size 2
  25 Hz
  50 Hz
  100 Hz
auto in 5s    ← only in auto-mode
```

All 5 options are visible simultaneously. Button hints removed to avoid layout overflow. Selected option highlighted with `>` in green.

Selection behavior:

```text
If no button is pressed, 10 Hz is selected after 5s timeout.
If Button A is pressed at least once, timeout is disabled.
Button B confirms selection.
```

READY screen:

```text
WiFi <device_ip>          RATE <hz>Hz
READY
SESSION A001
A x2 START     B NEXT
```

REC screen:

```text
REC  ●         ← red dot + green/red Wi-Fi dot (top right)
A001 / R1
SMP <sample_count>
ACC <acc_norm> g
A STOP
```

SAVED screen (shown 1.2s after STOP):

```text
SAVED
R<record_id>
<sample_count> smp
```

Display status:

```text
working / acceptable for prototype
```

---

## Current data format decision

Use simple raw CSV files for sensor data and readable JSON files for metadata.

Current raw data path convention:

```text
data/raw/[experiment_id]/[device_id]/run_[recording_run_id]_session_[device_session_id]_[sample_rate_hz]Hz.csv
```

Example:

```text
data/raw/EXP01/m5_001/run_A_session_A001_100Hz.csv
data/raw/EXP01/m5_001/run_A_session_A002_100Hz.csv
data/raw/EXP01/m5_001/run_B_session_A001_50Hz.csv
```

`recording_run_id` is a single uppercase letter (A, B, C, … Z, AA, AB, …) assigned by the logger at startup by scanning the device folder. It prevents file conflicts when the device resets and emits `A001` again.

Old files from before this change (`session_A001.csv`) are not overwritten — the scanner ignores them.

Generated data is local and normally ignored by Git.

---

## Current metadata files

Use readable JSON files for manual editing:

```text
data/metadata/experiments.json
data/metadata/recording_sessions.json
data/metadata/devices.json
```

Both loggers can create draft metadata records when launched with:

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

### Device identifiers

The device reports technical identity:

```text
mac_address
firmware_version
```

The logger resolves or validates project-level `device_id` through:

```text
data/metadata/devices.json
```

### Session and run identifiers

Current firmware session ids are device-local:

```text
A001 / A002 / A003
```

Current `session_uid` format includes `recording_run_id`:

```text
[experiment_id]_[device_id]_[recording_run_id]_[device_session_id]
```

Example:

```text
EXP01_m5_001_A_A001
```

Current metadata record includes:

```json
{
  "experiment_id": "EXP01",
  "device_id": "m5_001",
  "recording_run_id": "A",
  "device_session_id": "A001",
  "session_id": "A001",
  "session_uid": "EXP01_m5_001_A_A001",
  "sample_rate_hz": 100,
  "file_name": "run_A_session_A001_100Hz.csv",
  "file_path": "data/raw/EXP01/m5_001/run_A_session_A001_100Hz.csv"
}

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

The CSV schema is unchanged by HTTP batch mode.

Future analysis will calculate quality metrics from timestamps, especially:

```text
effective_sample_rate_hz
dt_ms statistics
gap count
```

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

Sampling rate is selectable at device startup.

Supported rates:

```text
5 Hz
10 Hz
25 Hz
50 Hz
100 Hz
```

Default:

```text
10 Hz
```

Default selection rule:

```text
If the user does not press Button A, 10 Hz is selected after timeout.
If the user presses Button A at least once, timeout is disabled and the device waits for Button B.
```

Current interpretation:

```text
sample_rate_hz = configured / selected sampling rate
```

Effective sampling rate must be calculated from raw timestamps:

```text
effective_sample_rate_hz = measured from DATA.device_timestamp_ms
```

Current transport status:

```text
HTTP batch mode supports 100 Hz in the current test.
```

Future analysis should verify effective sampling rate for each recording.

---

## Current architecture decisions

* Use VS Code + PlatformIO + Arduino framework.
* Use M5StickC Plus2 as the first device.
* Use feature branches for meaningful changes.
* Use `main` as stable branch.
* Use private GitHub repository at the start.
* Use raw CSV files for first data collection.
* Use readable JSON files for metadata.
* Use Wi-Fi HTTP batch mode as the current wireless transport.
* Keep USB Serial available for debugging.
* Keep firmware simple and experiment-agnostic.
* Keep loggers responsible for experiment context and file paths.
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
feature/device-info-event
feature/selectable-sampling-rate
feature/recording-runs-and-safe-file-names
```

Current active branch:

```text
main
```

Next planned branch:

```text
feature/serial-logger-recording-runs
feature/analyze-recordings
```

---

## Current next actions

### 1. Update serial_logger.py with recording_run_id

Apply the same changes as `http_logger.py`:

```text
recording_run_id assigned by logger
safe file names: run_A_session_A001_100Hz.csv
session_uid includes recording_run_id
metadata fields: recording_run_id, device_session_id
```

### 2. Create quick analysis tooling

Planned next tool:

```text
tools/analyze_recordings.py
```

Minimum useful behavior:

```text
read one CSV file or all CSV files for one experiment
calculate duration_sec
calculate effective_sample_rate_hz
calculate dt_ms statistics
calculate basic acc_norm / gyro statistics
save session_quality.csv
save acc_norm and dt_ms plots
```

This is the next practical step before building a metadata browser.

---

## Planned utility — basic metadata and plot browser

A small local browser is planned after safe filenames and quick analysis tooling.

Preferred first implementation:

```text
tools/motion_browser.py
```

Likely stack:

```text
Streamlit
```

Initial scope:

```text
read recording_sessions.json
list sessions / recording runs
filter by experiment_id, device_id, sample_rate_hz, movement label, status
open one CSV file
show acc_norm plot
show ax / ay / az plot
show gx / gy / gz plot
show dt_ms plot
show basic quality metrics
```

Current boundary:

```text
This is a local lab tool.
This is not a product dashboard.
This is not a full metadata editor yet.
```

Status:

```text
planned after safe file names and quick analysis
```

---

## Planned analysis layer — quick quality and ML features

The immediate planned analysis layer should focus on quick, useful metrics for collected CSV files.

Working name:

```text
tools/analyze_recordings.py
```

Initial outputs:

```text
data/analysis/[experiment_id]/session_quality.csv
data/analysis/[experiment_id]/plots/
```

Minimum metrics:

```text
rows
duration_sec
configured sample_rate_hz
effective_sample_rate_hz
mean_dt_ms
median_dt_ms
min_dt_ms
max_dt_ms
p95_dt_ms
gap count
acc_norm_mean
acc_norm_std
acc_norm_max
gyro_norm_mean
gyro_norm_max
quality_status
```

Possible quality statuses:

```text
OK
WARN_GAPS
WARN_SHORT
WARN_RATE_MISMATCH
BAD_EMPTY
```

Near-term ML / education path:

```text
MotionBlocks CSV
  → features.csv
  → Orange Data Mining / scikit-learn / Edge Impulse
```

Children-facing quick-win classes:

```text
idle
walking
shake
impact
fall_like
```

Status:

```text
planned after safe file names
```

---

## Known Issues / Limitations

* `serial_logger.py` not yet updated with `recording_run_id` — still writes `session_A001.csv`.
* `sample_rate_hz` currently means configured / selected rate, not verified effective rate.
* Effective sample rate is not yet calculated automatically.
* Long-record stability at 25 / 50 / 100 Hz still needs measurement.
* Battery life in Wi-Fi batch logging mode is not yet measured.
* Metadata still requires manual completion after recording.
* `records_actual` is not automatically updated after STOP.
* There is no plot viewer yet.
* There is no quick quality report yet.
* There is no metadata browser yet.

---

## Open questions

* Should `sample_rate_hz` be renamed to `configured_sample_rate_hz`, or should a separate field be added later?
* Should `effective_sample_rate_hz` be written back to metadata or kept in `data/analysis/`?
* Should `records_actual` be updated by the logger after STOP?
* Should metadata contain transport information such as `http_batch`, `serial`, and batch parameters?
* Should `channels` be repeated in each recording session or moved to a shared schema/device registry?
* Should events and DATA rows live in the same CSV, or should event logs be separated later?
* Should `device_id` ever be stored in firmware, or always resolved by the logger?
* When should SQLite be introduced?
* Which first ML demo should be used with children: Edge Impulse, Orange Data Mining, or local scikit-learn?

---

## Recent Changes

### 2026-06-13 (end of day)

* Implemented `recording_run_id` in `tools/http_logger.py`.
* Safe file names: `run_A_session_A001_100Hz.csv`.
* `session_uid` now includes `recording_run_id`: `EXP01_m5_001_A_A001`.
* `SessionWriter` made thread-safe with `threading.Lock`.
* `IMU_NOT_UPDATED` event now written to CSV.
* Logger console: DATA lines no longer printed per-sample; replaced with `[REC]` status every 2s and `[STOP]` summary with duration and file name.
* Firmware bumped to v0.7.0.
* Sample rate selection screen: all 5 options visible simultaneously, button hints removed.
* Double-click window increased from 400 ms to 600 ms.
* Wi-Fi indicator (green/red dot) added to REC screen.
* SAVED screen shown 1.2s after STOP.
* Screen refresh changed from sample counter to time-based (200 ms).
* DATA line in firmware uses `snprintf` static buffer instead of `String` concatenation.
* Branch `feature/recording-runs-and-safe-file-names` merged to `main`.

### 2026-06-13 (earlier)

* Added `EVENT,DEVICE_INFO` and MAC-based device resolution.
* Added startup sampling-rate selection: 5 / 10 / 25 / 50 / 100 Hz.
* Added `EVENT,SAMPLE_RATE` to the protocol.
* Tested per-sample HTTP POST and found it insufficient for 25 / 50 Hz.
* Tested HTTP keep-alive and rejected it as insufficient.
* Implemented HTTP batch mode for `DATA` rows during recording.
* Confirmed 100 Hz works in current HTTP batch test.

### 2026-06-10

* Wireless HTTP logging verified and working.
* Phase transition from wired Serial debugging to wireless HTTP data collection.
* Device display layout improved.
* Draft JSON metadata generation working.
