# MotionBlocks Journal

This is the working project journal for **MotionBlocks** by **Stofendez Lab**.

The journal records important project events, decisions, experiments, problems, and next steps.

It is not a full documentation file.
Stable decisions should later be moved to the relevant documentation files.

---

## 2026-06-08

### Project identity fixed

We selected the project naming structure:

* **Stofendez Lab** — laboratory / team
* **MotionBlocks** — main project
* **MotionLink** — future technology for connecting the personal motion domain to external dashboards

Rationale:

* MotionBlocks is short and understandable for children.
* It connects well with LEGO / Roblox-style block thinking.
* It also describes the idea of a motion library built from reusable movement blocks.
* MotionLink can later describe the connection between the motion domain and family / medical dashboards.

### Development environment

Initial development stack:

* VS Code
* PlatformIO
* Arduino framework through PlatformIO
* Python
* SQLite / DBeaver
* GitHub

Optional tools for later stages:

* Edge Impulse
* ChatGPT Data Analysis
* Orange Data Mining

### PlatformIO installed

PlatformIO IDE extension was installed in VS Code.

Check command:

```powershell
pio --version
```

Working result:

```text
PlatformIO Core, version 6.1.19
```

### Device detected

M5StickC Plus2 was detected in Windows Device Manager as:

```text
USB-Enhanced-SERIAL CH9102 (COM6)
```

The correct device port for upload and serial monitor is:

```text
COM6
```

Bluetooth COM ports should not be used for firmware upload.

### First firmware uploaded

The first firmware was successfully built and uploaded using:

```powershell
pio run --target upload --upload-port COM6
```

Result:

```text
[SUCCESS]
```

The device screen showed:

```text
MotionBlocks
Stage 1
Hello!
```

Serial output worked and printed:

```text
MotionBlocks first firmware started
alive
alive
alive
```

### Confirmed

The first firmware bring-up is complete.

Confirmed:

* PlatformIO works.
* ESP32 toolchain was downloaded.
* Arduino framework was downloaded by PlatformIO.
* M5Unified and M5GFX libraries were downloaded.
* `main.cpp` was compiled.
* Firmware was uploaded to M5StickC Plus2.
* Display output works.
* Serial output works.

### Next steps

* Commit the first firmware.
* Push branch `feature/first-firmware` to GitHub.
* Create Pull Request.
* Add IMU serial logger firmware.
* Print IMU data as CSV:

  * `timestamp_ms`
  * `ax`
  * `ay`
  * `az`
  * `gx`
  * `gy`
  * `gz`
* Start preparing Python serial logger.
* Start preparing SQLite schema:

  * `records`
  * `recorddata`

---


## 2026-06-08 — IMU logger v0.1

### Expected result

M5StickC Plus2 should read IMU data and print it to Serial Monitor in CSV format.

### Actual result

IMU logger works after adding `M5.Imu.update()` before reading data with `M5.Imu.getImuData()`.

Serial Monitor prints CSV rows:

```csv
timestamp_ms,ax,ay,az,gx,gy,gz
... 



## 2026-06-08 — IMU logger v0.1

### Context

Continued first firmware bring-up for **M5StickC Plus2** in the MotionBlocks project.

Current branch:

```text
feature/imu-serial-logger
```

The branch was created from:

```text
feature/first-firmware
```

### Expected result

M5StickC Plus2 should read IMU data and print it to Serial Monitor in CSV format.

Expected CSV format:

```csv
timestamp_ms,ax,ay,az,gx,gy,gz
```

### What was done

* Confirmed that the first firmware works:

  * screen output works;
  * serial output works;
  * firmware builds and uploads through PlatformIO.
* Created / used branch:

```text
feature/imu-serial-logger
```

* Updated `main.cpp` to read IMU data.
* Initially, IMU values were printed but did not change when the device was moved.
* Fixed the issue by adding:

```cpp
M5.Imu.update();
```

before reading data through:

```cpp
M5.Imu.getImuData();
```

### Actual result

IMU logger v0.1 works.

Serial Monitor prints continuous CSV rows with:

```csv
timestamp_ms,ax,ay,az,gx,gy,gz
```

IMU values change when the device is moved or shaken.

### Decision

When reading IMU data through M5Unified, call:

```cpp
M5.Imu.update();
```

before:

```cpp
M5.Imu.getImuData();
```

### Current status

```text
[✓] Firmware builds
[✓] Firmware uploads to M5StickC Plus2
[✓] Serial Monitor works
[✓] IMU data is printed as CSV
[✓] IMU values change when the device is moved
```

### Next steps

* Commit IMU logger v0.1.
* Update Stage 1 Definition of Done.
* Prepare button-controlled recording:

  * double click starts recording;
  * single click stops recording;
  * record number is shown on the screen;
  * data is sent as structured START / DATA / STOP events.
* Later: implement Python serial logger to save records into numbered CSV files.
* Later: evaluate Wi-Fi transport instead of COM/Serial.


### Near-term plan

The next technical work should continue in small, testable steps.

#### Step 1 — Commit current IMU logger

Current branch:

```text
feature/imu-serial-logger
```

Expected result:

* IMU logger v0.1 is committed.
* Branch is pushed to GitHub.
* Current working firmware state is not lost.

Action items:

* [ ] Commit updated `main.cpp`.
* [ ] Push `feature/imu-serial-logger`.
* [ ] Add evidence to journal if needed.

---

#### Step 2 — Button-controlled recording over Serial

Goal:

Turn the device from a continuous IMU stream into a simple recording tool.

Expected behavior:

* double click on Button A starts a new record;
* single click on Button A stops the current record;
* current record number is displayed on the screen;
* data is printed to Serial only while recording.

Proposed serial protocol:

```csv
EVENT,START,record_id,timestamp_ms
DATA,record_id,timestamp_ms,ax,ay,az,gx,gy,gz
EVENT,STOP,record_id,timestamp_ms
```

Example:

```csv
EVENT,START,7,125000
DATA,7,125100,0.0123,-0.0341,0.9872,0.1200,-0.0300,0.0100
DATA,7,125200,0.0130,-0.0338,0.9869,0.1100,-0.0400,0.0200
EVENT,STOP,7,130000
```

Definition of Done:

* [ ] Firmware builds successfully.
* [ ] Firmware uploads to M5StickC Plus2.
* [ ] Screen shows `IDLE` and next record number.
* [ ] Double click starts recording.
* [ ] Screen changes to `REC #...`.
* [ ] Serial Monitor prints `EVENT,START,...`.
* [ ] Serial Monitor prints `DATA,...` rows while recording.
* [ ] Single click stops recording.
* [ ] Serial Monitor prints `EVENT,STOP,...`.
* [ ] No `DATA` rows are printed after stop.

Possible branch:

```text
feature/button-controlled-logger
```

---

#### Step 3 — Python serial logger

Goal:

Save records from Serial Monitor into numbered CSV files on the computer.

Important note:

M5StickC Plus2 does not create files on the computer directly.
It sends data through Serial, and the Python script creates files.

Expected flow:

```text
M5StickC Plus2
  → COM6 / Serial
  → Python serial_logger.py
  → data/raw/record_0007.csv
```

Expected behavior:

* Python listens to `COM6`;
* when it receives `EVENT,START`, it opens a new CSV file;
* when it receives `DATA`, it writes rows to the current file;
* when it receives `EVENT,STOP`, it closes the file.

Definition of Done:

* [ ] `tools/serial_logger.py` exists.
* [ ] Script can connect to `COM6`.
* [ ] Script detects `EVENT,START`.
* [ ] Script creates a numbered CSV file.
* [ ] Script writes `DATA` rows to the file.
* [ ] Script closes the file after `EVENT,STOP`.
* [ ] At least one test record is saved in `data/raw/`.

Possible branch:

```text
feature/python-serial-logger
```

---

#### Step 4 — SQLite motion database

Goal:

Create the first simple database for motion records.

Initial tables:

```text
records
recorddata
```

`records` stores metadata for each recording:

* `record_id`;
* movement type;
* recording time;
* duration;
* sample rate;
* subject id;
* operator id;
* device id;
* source file;
* comment;
* `payload` JSON.

`recorddata` stores IMU time-series data linked to `record_id`:

* `record_id`;
* `t_ms`;
* `ax`, `ay`, `az`;
* `gx`, `gy`, `gz`;
* optional `payload` JSON.

Definition of Done:

* [ ] SQLite schema exists.
* [ ] `records` table exists.
* [ ] `recorddata` table exists.
* [ ] A CSV file can be imported into the database.
* [ ] Basic SQL queries work:

  * list records;
  * show data for one record;
  * count records by movement type.

Possible branch:

```text
feature/sqlite-motion-db
```

---

#### Step 5 — Wireless transport research

Goal:

Decide how to move from USB/Serial logging to wireless logging.

Current preference:

```text
Wi-Fi first, Bluetooth/BLE later
```

Rationale:

* Wi-Fi is easier to connect to a local Python/FastAPI server.
* Wi-Fi is easier to debug.
* Wi-Fi fits the future MotionLink / dashboard architecture.
* BLE is closer to real wearable products, but more complex for the first version.

Possible future flow:

```text
M5StickC Plus2
  → Wi-Fi
  → local Python server
  → data/raw/*.csv
  → SQLite
  → dashboard
```

Open questions:

* Should data be sent by HTTP POST or UDP?
* Should the device send every sample or only record events?
* Should Wi-Fi be introduced before or after the first SQLite database?
* How should Wi-Fi credentials be stored safely?

---

### Short priority list

Immediate next actions:

* [ ] Commit IMU logger v0.1.
* [ ] Add button-controlled recording over Serial.
* [ ] Add Python serial logger.
* [ ] Save first numbered CSV record.
* [ ] Create initial SQLite schema.
* [ ] Later: move transport from Serial to Wi-Fi.


## 2026-06-08 PlatformIO build / upload reminder

Firmware project location:

```text
firmware/m5stickc-plus2
```

Main firmware file:

```text
firmware/m5stickc-plus2/src/main.cpp
```

Before running PlatformIO commands, go to the firmware project folder:

```powershell
cd firmware/m5stickc-plus2
```

### Build firmware

Compile firmware without uploading it to the device:

```powershell
pio run
```

Expected result:

```text
[SUCCESS]
```

### Upload firmware to M5StickC Plus2

Upload firmware to the device connected as `COM6`:

```powershell
pio run --target upload --upload-port COM6
```

Expected result:

```text
Hard resetting via RTS pin...
[SUCCESS]
```

### Open Serial Monitor

Open Serial Monitor at `115200` baud:

```powershell
pio device monitor --port COM6 --baud 115200
```

Exit Serial Monitor:

```text
Ctrl + C
```

### Full command sequence

```powershell
cd firmware/m5stickc-plus2
pio run
pio run --target upload --upload-port COM6
pio device monitor --port COM6 --baud 115200
```

### Notes

* `COM6` is the current M5StickC Plus2 USB serial port.
* Bluetooth COM ports such as `COM3` / `COM4` should not be used.
* If upload fails, check that Serial Monitor is closed.
* If the port changes, run:

```powershell
pio device list
```

and find the device named similar to:

```text
USB-Enhanced-SERIAL CH9102
```
## 2026-06-09 — Button-controlled IMU logger v0.2

### Result

Implemented and tested button-controlled IMU recording on M5StickC Plus2.

### Behavior

- Device starts in `IDLE` mode.
- Double click on Button A starts a new record.
- Single click on Button A stops the current record.
- Current record number is shown on the screen.
- Sample count is shown during recording.
- IMU data is sent to Serial only while recording.

### Serial protocol

```csv
EVENT,START,record_id,timestamp_ms
DATA,record_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm
EVENT,STOP,record_id,timestamp_ms,sample_count

## 2026-06-10 — Session-aware IMU logger v0.3

### Context

Continued development of the MotionBlocks firmware after successful button-controlled IMU recording.

Current branch:

```text
feature/session-aware-logger
```

Previous working version:

```text
IMU logger v0.2 — button-controlled recording
```

The goal of this iteration was to add the concept of a recording session without making the firmware aware of experiment-level context.

### Design decision

The firmware should not know:

```text
experiment_id
device_id
subject_id
movement_type
movement_label
```

These belong to the Python logger and metadata layer.

The firmware should only manage:

```text
session_id
record_id
sample_id
sensor data
```

This keeps the device generic and reusable across experiments.

### Implemented behavior

* Device starts with session `A001`.
* Button A double click starts a record.
* Button A single click stops the current record.
* Button B switches to the next session.
* When session changes:

  * `session_id` increments: `A001`, `A002`, `A003`, ...
  * `record_id` resets to `1`;
  * `sample_id` resets when a new record starts.
* Data is sent only while recording.
* Screen shows current session, record number, and sample count.

### Serial protocol

```csv
EVENT,NEW_SESSION,session_id,timestamp_ms
EVENT,START,session_id,record_id,timestamp_ms
DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm
EVENT,STOP,session_id,record_id,timestamp_ms,sample_count
```

### Example Serial output

```csv
EVENT,NEW_SESSION,A001,12345
EVENT,START,A001,1,13000
DATA,A001,1,1,13100,0.0123,-0.0341,0.9872,0.1200,-0.0300,0.0100,0.9880
DATA,A001,1,2,13200,0.0130,-0.0338,0.9869,0.1100,-0.0400,0.0200,0.9878
EVENT,STOP,A001,1,19000,60
EVENT,NEW_SESSION,A002,22000
```

### Result

Session-aware firmware works.

Confirmed:

```text
[✓] firmware builds successfully
[✓] firmware uploads to M5StickC Plus2
[✓] device starts with session A001
[✓] Button A double click starts recording
[✓] Button A single click stops recording
[✓] Button B switches to next session
[✓] DATA rows include session_id, record_id, sample_id
[✓] record_id resets when session changes
[✓] firmware does not know experiment_id
```

### File and metadata architecture

Experiment context is assigned outside the firmware.

Planned raw data path:

```text
data/raw/[experiment_id]/[device_id]/session_[session_id].csv
```

Example:

```text
data/raw/EXP01/m5_001/session_A001.csv
data/raw/EXP01/m5_001/session_A002.csv
data/raw/EXP01/m5_002/session_A001.csv
```

The firmware only sends `session_id`.
The Python logger will provide:

```text
experiment_id
device_id
file_path
```

Metadata will provide:

```text
subject_id
movement_type
movement_label
location
comments
status
```

### Next step

Implement Python serial logger.

Possible next branch:

```text
feature/python-serial-logger
```

Expected command:

```powershell
python tools/serial_logger.py --port COM6 --experiment-id EXP01 --device-id m5_001
```

Expected output files:

```text
data/raw/EXP01/m5_001/session_A001.csv
data/raw/EXP01/m5_001/session_A002.csv
```

### Commit

Recommended commit message:

```text
Add session id to button-controlled logger
```



## 2026-06-10 — Session-aware IMU logger v0.3

### Context

Continued development of the MotionBlocks firmware after successful button-controlled IMU recording.

Current branch:

```text
feature/session-aware-logger
```

Previous working version:

```text
IMU logger v0.2 — button-controlled recording
```

The goal of this iteration was to add the concept of a recording session without making the firmware aware of experiment-level context.

### Design decision

The firmware should not know:

```text
experiment_id
device_id
subject_id
movement_type
movement_label
```

These belong to the Python logger and metadata layer.

The firmware should only manage:

```text
session_id
record_id
sample_id
sensor data
```

This keeps the device generic and reusable across experiments.

### Implemented behavior

* Device starts with session `A001`.
* Button A double click starts a record.
* Button A single click stops the current record.
* Button B switches to the next session.
* When session changes:

  * `session_id` increments: `A001`, `A002`, `A003`, ...
  * `record_id` resets to `1`;
  * `sample_id` resets when a new record starts.
* Data is sent only while recording.
* Screen shows current session, record number, and sample count.

### Serial protocol

```csv
EVENT,NEW_SESSION,session_id,timestamp_ms
EVENT,START,session_id,record_id,timestamp_ms
DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm
EVENT,STOP,session_id,record_id,timestamp_ms,sample_count
```

### Example Serial output

```csv
EVENT,NEW_SESSION,A001,12345
EVENT,START,A001,1,13000
DATA,A001,1,1,13100,0.0123,-0.0341,0.9872,0.1200,-0.0300,0.0100,0.9880
DATA,A001,1,2,13200,0.0130,-0.0338,0.9869,0.1100,-0.0400,0.0200,0.9878
EVENT,STOP,A001,1,19000,60
EVENT,NEW_SESSION,A002,22000
```

### Result

Session-aware firmware works.

Confirmed:

```text
[✓] firmware builds successfully
[✓] firmware uploads to M5StickC Plus2
[✓] device starts with session A001
[✓] Button A double click starts recording
[✓] Button A single click stops recording
[✓] Button B switches to next session
[✓] DATA rows include session_id, record_id, sample_id
[✓] record_id resets when session changes
[✓] firmware does not know experiment_id
```

### File and metadata architecture

Experiment context is assigned outside the firmware.

Planned raw data path:

```text
data/raw/[experiment_id]/[device_id]/session_[session_id].csv
```

Example:

```text
data/raw/EXP01/m5_001/session_A001.csv
data/raw/EXP01/m5_001/session_A002.csv
data/raw/EXP01/m5_002/session_A001.csv
```

The firmware only sends `session_id`.
The Python logger will provide:

```text
experiment_id
device_id
file_path
```

Metadata will provide:

```text
subject_id
movement_type
movement_label
location
comments
status
```

### Next step

Implement Python serial logger.

Possible next branch:

```text
feature/python-serial-logger
```

Expected command:

```powershell
python tools/serial_logger.py --port COM6 --experiment-id EXP01 --device-id m5_001
```

Expected output files:

```text
data/raw/EXP01/m5_001/session_A001.csv
data/raw/EXP01/m5_001/session_A002.csv
```

### Commit

Recommended commit message:

```text
Add session id to button-controlled logger
```

## 2026-06-10 — Python Serial logger and draft metadata generation

### Context

Continued development of the MotionBlocks data collection pipeline after successful session-aware firmware.

Current branch:

```text
feature/python-serial-logger
```

Previous firmware branch:

```text
feature/session-aware-logger
```

The goal of this iteration was to implement a Python logger that listens to the M5StickC Plus2 Serial output and saves session-based CSV files.

### Implemented behavior

Python logger now listens to the device protocol:

```csv
EVENT,NEW_SESSION,session_id,timestamp_ms
EVENT,START,session_id,record_id,timestamp_ms
DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm
EVENT,STOP,session_id,record_id,timestamp_ms,sample_count
```

The logger is launched from the repository root:

```powershell
python tools/serial_logger.py --port COM6 --experiment-id EXP01 --device-id m5_001 --create-metadata
```

The logger creates raw CSV files under:

```text
data/raw/[experiment_id]/[device_id]/session_[session_id].csv
```

Example:

```text
data/raw/EXP01/m5_001/session_A001.csv
data/raw/EXP01/m5_001/session_A002.csv
```

### Metadata generation

Added optional metadata generation using the flag:

```powershell
--create-metadata
```

When enabled, the logger creates or updates:

```text
data/metadata/experiments.json
data/metadata/recording_sessions.json
```

If `experiments.json` does not exist, it is created.

If the current `experiment_id` is missing, the logger adds a draft experiment record.

If `recording_sessions.json` does not exist, it is created.

If the current `session_uid` is missing, the logger adds a draft recording session record.

Existing metadata records are preserved and are not overwritten.

### Draft metadata status

Automatically created metadata records receive status:

```text
auto created. needs description.
```

This means the record was generated by the logger and should later be reviewed and completed manually.

### Responsibility split

The firmware does not know:

```text
experiment_id
device_id
subject_id
movement_type
movement_label
```

The firmware only sends:

```text
session_id
record_id
sample_id
sensor data
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
```

### Result

Confirmed:

```text
[✓] Python logger connects to COM6
[✓] Logger receives device Serial protocol
[✓] Logger creates session CSV files
[✓] Logger creates data/raw/EXP01/m5_001/ structure
[✓] Logger writes EVENT and DATA rows to CSV
[✓] Logger supports --create-metadata flag
[✓] Logger creates experiments.json if needed
[✓] Logger creates recording_sessions.json if needed
[✓] Logger adds draft experiment metadata when EXP01 is missing
[✓] Logger adds draft session metadata when session_uid is missing
[✓] Existing metadata records are not overwritten
```

### Next steps

* Review generated metadata records.
* Manually fill missing experiment fields:

  * `short_name`
  * `title`
  * `location`
  * `goal`
  * `participants`
  * `comments`
* Manually fill missing session fields:

  * `movement_type`
  * `movement_label`
  * `subject_id`
  * `comment`
  * `tags`
* Collect first real experiment data.
* Later implement basic plotting for `acc_norm`.

### Recommended commit message

```text
Add draft metadata generation to serial logger
```




# Journal entry template

## YYYY-MM-DD

### Topic

Short title of the work session.

### What was done

* ...

### Decisions

* ...

### Problems

* ...

### Results

* ...

### Next steps

* [ ] ...
* [ ] ...

### Related files

* `path/to/file`
* `path/to/file`

