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

## 2026-06-10 — Device logger display layout update

### Context

After implementing the session-aware firmware and Python Serial logger, we reviewed the on-device display layout on M5StickC Plus2.

The previous display was functional but hard to read:

* text was too small;
* `IDLE` and `REC` screens used different visual structure;
* too much information was shown at once;
* during early layout experiments, old `samples` / `acc` text overlapped with the new `REC` screen.

### Design decision

The device screen should behave like a small instrument panel, not like a full dashboard.

Working principle:

```text
one screen = one main purpose
```

For the idle screen:

```text
READY / current session / button hints
```

For the recording screen:

```text
REC / session + record / samples / acceleration norm / stop hint
```

The project name should not occupy working screen space.
Instead, project identity is shown on a short splash screen.

### Implemented changes

Added a splash screen shown at startup:

```text
MOTIONBLOCKS
LOGGER
Stofendez Lab
```

The splash screen is shown for approximately 3 seconds.

Added fixed landscape display orientation:

```cpp
M5.Display.setRotation(1);
```

If needed, it can be changed to:

```cpp
M5.Display.setRotation(3);
```

Added a vertical `LOGGER` label on the left side of working screens.

Updated `READY` screen:

```text
LOGGER | READY
       | SESSION
       | A001
       | A x2 START     B NEXT
```

Updated `REC` screen:

```text
LOGGER | REC ●
       | A001 / R1
       | SMP  <sample_count>
       | ACC  <acc_norm> g
       | A STOP
```

### Important cleanup

Removed old direct screen drawing from `sendImuSample()`:

```cpp
M5.Display.fillRect(...)
M5.Display.printf("samples: ...")
M5.Display.printf("acc: ...")
```

This old code was causing text overlap on the new `REC` screen.

The screen is now updated through dedicated display functions.

### Result

Confirmed:

```text
[✓] Firmware builds
[✓] Firmware uploads to M5StickC Plus2
[✓] Splash screen appears on startup
[✓] READY screen is readable
[✓] REC screen is readable
[✓] samples and acc values no longer overlap
[✓] Serial protocol remains unchanged
[✓] Recording logic remains unchanged
[✓] Python logger compatibility remains unchanged
```

### Current position

The display is now acceptable for the current prototype.

Further visual polishing can be done later, but the next priority should remain the data pipeline:

```text
collect first real dataset → complete metadata → plot session data
```

### Recommended commit message

```text
Improve device logger display layout
```

## 2026-06-10 — HTTP logger receiver

### Context

Started the transition from wired Serial logging to wireless data collection.

The current Serial-based pipeline works, but it limits real motion experiments because the device must remain connected by USB cable.

Next goal:

```text
M5StickC Plus2 → Wi-Fi → Python HTTP logger → CSV / metadata
```

### Implemented

Added first version of the Python HTTP logger:

```text
tools/http_logger.py
```

The logger starts a local HTTP server and accepts MotionBlocks protocol lines through:

```text
POST /line
```

Health check endpoint:

```text
GET /health
```

The HTTP logger uses the same protocol lines as the Serial logger:

```csv
EVENT,NEW_SESSION,session_id,timestamp_ms
EVENT,START,session_id,record_id,timestamp_ms
DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm
EVENT,STOP,session_id,record_id,timestamp_ms,sample_count
```

This keeps the data format stable while changing only the transport layer.

### Run command

From the repository root:

```powershell
python tools/http_logger.py --host 0.0.0.0 --port 8080 --experiment-id EXP01 --device-id m5_001 --create-metadata
```

### Tested

Local health check works:

```text
http://localhost:8080/health
```

Health check by notebook Wi-Fi IP works:

```text
http://192.168.8.129:8080/health
```

External access from iPad also works after changing the Windows network profile to:

```text
Private network
```

### Important network note

For other devices in the same Wi-Fi network to reach the Python HTTP logger, Windows must allow inbound connections.

Current finding:

```text
If Windows network profile is Public, iPad cannot reach the logger.
If Windows network profile is Private, iPad can reach the logger.
```

### Result

Confirmed:

```text
[✓] HTTP logger starts
[✓] GET /health works locally
[✓] GET /health works through notebook Wi-Fi IP
[✓] GET /health works from iPad in the same network
[✓] Windows Private network profile fixes external access
[✓] Logger is ready for M5StickC Wi-Fi client testing
```

### Next step

Add Wi-Fi configuration for firmware:

```text
firmware/m5stickc-plus2/src/wifi_config.example.h
firmware/m5stickc-plus2/src/wifi_config.h
```

The real `wifi_config.h` must not be committed to Git because it will contain Wi-Fi credentials.

Expected logger endpoint for current network:

```cpp
#define LOGGER_URL "http://192.168.8.129:8080/line"
```

### Recommended commit message

```text
Add HTTP logger receiver
```

## 2026-06-10 — Wireless HTTP logging works

### Context

Continued the transition from wired Serial logging to wireless data collection.

The previous limitation was that the device had to remain connected by USB cable, which made realistic wrist-based motion testing impossible.

Target wireless pipeline:

```text
M5StickC Plus2
  → Wi-Fi
  → HTTP POST
  → Python HTTP logger
  → CSV files
  → draft metadata
```

### Implemented

Updated firmware to send the same MotionBlocks protocol lines through two channels:

```text
Serial
HTTP POST
```

The protocol itself remains unchanged:

```csv
EVENT,NEW_SESSION,session_id,timestamp_ms
EVENT,START,session_id,record_id,timestamp_ms
DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm
EVENT,STOP,session_id,record_id,timestamp_ms,sample_count
```

The firmware now uses:

```cpp
WiFi.h
HTTPClient.h
wifi_config.h
```

The local `wifi_config.h` contains:

```cpp
WIFI_SSID
WIFI_PASSWORD
LOGGER_URL
```

The real `wifi_config.h` is excluded from Git.

### Tested

The Python HTTP logger was running on the notebook:

```powershell
python tools/http_logger.py --host 0.0.0.0 --port 8080 --experiment-id EXP01 --device-id m5_001 --create-metadata
```

The device connected to Wi-Fi successfully.

The device sent MotionBlocks protocol lines to:

```text
POST /line
```

The HTTP logger received the data and wrote it to CSV files.

### Result

Confirmed:

```text
[✓] M5StickC connects to Wi-Fi
[✓] READY screen shows Wi-Fi IP
[✓] Python HTTP logger is reachable from local network
[✓] Firmware sends EVENT lines over HTTP
[✓] Firmware sends DATA lines over HTTP
[✓] HTTP logger writes received data to CSV
[✓] Draft metadata generation still works
[✓] Serial output remains available for debugging
[✓] Wireless recording mode works
```

### Current wireless pipeline

```text
M5StickC Plus2
  → Wi-Fi
  → HTTP POST /line
  → tools/http_logger.py
  → data/raw/EXP01/m5_001/session_A001.csv
  → data/metadata/experiments.json
  → data/metadata/recording_sessions.json
```

### Important notes

The wireless mode depends on local network settings.

For access from other devices, Windows network profile must be set to:

```text
Private network
```

The logger notebook IP in the current network was:

```text
192.168.8.129
```

The firmware endpoint was:

```cpp
#define LOGGER_URL "http://192.168.8.129:8080/line"
```

### Next steps

* Test the device on a table without USB cable.
* Test the device on wrist.
* Collect the first real mini-dataset.
* Check whether 10 Hz HTTP POST is stable during movement.
* Later consider batching / buffering if packet loss or delays appear.

### Recommended commit message

```text
Add Wi-Fi HTTP output to device logger
```


## 2026-06-11 — Device info event and MAC-based device resolution

### Context

Continued work on the wireless MotionBlocks pipeline.

Previous working pipeline:

```text
M5StickC Plus2
  → Wi-Fi
  → HTTP POST /line
  → tools/http_logger.py
  → CSV files
  → draft metadata
```

The next improvement was to let the device report its own hardware identity, so that the logger can validate or resolve the project-level `device_id`.

### Branch

```text
feature/device-info-event
```

### Design decision

The device reports its technical hardware identity:

```text
mac_address
firmware_version
```

The firmware does not assign the project-level `device_id`.

The logger maps:

```text
mac_address → device_id
```

using the local device registry:

```text
data/metadata/devices.json
```

The command-line `--device-id` remains supported as an explicit override.

### Implemented firmware change

Firmware version updated to:

```text
motionblocks.logger.v0.5
```

Added startup event:

```csv
EVENT,DEVICE_INFO,mac_address,firmware_version,timestamp_ms
```

Example received from the device:

```csv
EVENT,DEVICE_INFO,F0:24:F9:97:ED:08,motionblocks.logger.v0.5,6972
EVENT,NEW_SESSION,A001,7425
```

The event is sent before the first session event.

The same event is sent through both channels:

```text
Serial
HTTP POST
```

### Implemented HTTP logger change

Updated:

```text
tools/http_logger.py
```

The HTTP logger now supports:

```text
EVENT,DEVICE_INFO,...
```

The logger can read a device registry from:

```text
data/metadata/devices.json
```

An example registry file was added:

```text
data/metadata/devices.example.json
```

The real `devices.json` is local and may contain real device MAC addresses.

### Device ID resolution rule

If `--device-id` is provided:

```text
use --device-id as the effective device_id
```

If `DEVICE_INFO` is received, the logger checks the MAC address against `devices.json`.

If the resolved device id matches the explicit `--device-id`, the logger prints:

```text
DEVICE OK
```

If the resolved device id differs from `--device-id`, the logger prints:

```text
WARNING
```

but continues using the explicit `--device-id`.

If the MAC address is not registered, the logger also prints:

```text
WARNING
```

but continues using the explicit `--device-id`.

If `--device-id` is not provided:

```text
DEVICE_INFO is required
```

The logger resolves:

```text
mac_address → device_id
```

through `devices.json`.

If the MAC address cannot be resolved, the logger fails with an explicit error.

The logger does not silently create data under `unknown_device`.

### Current limitation

The current HTTP logger instance is intended for one active device at a time.

Current rule:

```text
one logger instance = one active device stream
```

`device_id` is not added to every `DATA` row.

Reason:

* the file already lives under the device folder;
* session metadata stores device information;
* mixing multiple device streams in one logger would require routing, clock handling, multiple open files, and different sampling rates;
* multi-device logging is a separate future feature.

If two devices must be used simultaneously, the current practical approach is to run two logger instances on different ports.

### Tested

Confirmed:

```text
[✓] Firmware builds successfully
[✓] Firmware uploads to M5StickC Plus2
[✓] DEVICE_INFO is emitted by the device
[✓] DEVICE_INFO contains MAC address
[✓] DEVICE_INFO contains firmware version
[✓] DEVICE_INFO is emitted before NEW_SESSION
[✓] HTTP logger receives DEVICE_INFO
[✓] HTTP logger continues to receive NEW_SESSION / START / DATA / STOP
[✓] Wireless logging still works
[✓] CSV writing still works
[✓] Existing --device-id workflow still works
```

### Operational note

During testing, Windows changed the Wi-Fi network profile from Private to Public after an update.

This blocked inbound HTTP connections to the Python logger.

Required setting:

```text
Windows Wi-Fi network profile = Private
```

If HTTP POST fails with:

```text
HTTP POST failed, code=-1
```

check:

```text
1. http_logger.py is running
2. LOGGER_URL IP is correct
3. Windows network profile is Private
4. firewall allows Python on Private networks
```

### Result

The branch successfully adds the first device identity layer.

Current startup sequence:

```csv
EVENT,DEVICE_INFO,F0:24:F9:97:ED:08,motionblocks.logger.v0.5,...
EVENT,NEW_SESSION,A001,...
```

The logger can now validate or resolve the device identity before registering sessions.

### Recommended commit message

```text
Add device registry and MAC-based device resolution
```

### Next branch

```text
feature/selectable-sampling-rate
```

Goal:

```text
Allow selecting sampling rate at device startup: 5 / 10 / 25 / 50 / 100 Hz.
```



## 2026-06-11 — Selectable sampling rate and HTTP batch logging

### Context

Continued development after `feature/device-info-event`.

Planned branch sequence:

```text
feature/device-info-event
feature/selectable-sampling-rate
feature/recording-runs-and-safe-file-names
```

The first branch was completed. The next goal was to let the M5StickC Plus2 choose the IMU sampling rate at startup and report the selected rate to the logger.

### Branch

```text
feature/selectable-sampling-rate
```

### Firmware changes

Firmware version was advanced through the experimental iterations:

```text
motionblocks.logger.v0.6
motionblocks.logger.v0.6.1
motionblocks.logger.v0.6.2
```

Added selectable sampling rate at device startup.

Supported rates:

```text
5 Hz
10 Hz
25 Hz
50 Hz
100 Hz
```

Startup behavior:

```text
Button A → select next sampling rate
Button B → confirm selected sampling rate
```

Default behavior:

```text
If no button is pressed, the device automatically selects 10 Hz after timeout.
```

UX adjustment:

```text
If Button A is pressed at least once, timeout is disabled.
The device waits for Button B confirmation.
```

This prevents the device from moving to the next screen while the user is still choosing a rate.

### Added protocol event

The firmware now sends:

```csv
EVENT,SAMPLE_RATE,sample_rate_hz,timestamp_ms
```

Example:

```csv
EVENT,SAMPLE_RATE,50,11143
```

Startup sequence became:

```csv
EVENT,DEVICE_INFO,F0:24:F9:97:ED:08,motionblocks.logger.v0.6.2,...
EVENT,SAMPLE_RATE,50,...
EVENT,NEW_SESSION,A001,...
```

The Python HTTP logger stores the selected rate in draft session metadata:

```json
"sample_rate_hz": 50
```

Important interpretation:

```text
sample_rate_hz currently means configured / selected sampling rate
```

It is not automatically a verified effective sampling rate.

### Initial HTTP limitation found

When sending one HTTP POST per sample, the selected rate was not achieved at higher frequencies.

Observed behavior:

```text
5 Hz  → slows down correctly
10 Hz → works approximately as before
25 Hz → not reached reliably
50 Hz → not reached reliably
```

At 25 / 50 Hz, actual `DATA` timestamp intervals were still close to the previous per-sample HTTP limitation.

Conclusion:

```text
The sampling-rate selection logic works.
The bottleneck is the transport model.
```

The issue is not payload size.

The issue is:

```text
one sample = one synchronous HTTP request/response
```

### HTTP keep-alive experiment

An intermediate experiment tested whether reusing the HTTP connection would be enough.

Transport model tested:

```text
IDLE:
    service events → one-shot HTTP POST

RECORDING:
    START / DATA / STOP → one reused HTTPClient connection
```

Result:

```text
HTTP keep-alive did not solve the problem sufficiently.
```

Even with keep-alive, one POST per sample remained too expensive for reliable 25 / 50 Hz logging.

Decision:

```text
Do not continue optimizing per-sample HTTP POST.
```

### HTTP batch logging

Next, HTTP batch mode was implemented during active recording.

Current transport model:

```text
IDLE:
    DEVICE_INFO  → one-shot HTTP POST
    SAMPLE_RATE  → one-shot HTTP POST
    NEW_SESSION  → one-shot HTTP POST

RECORDING:
    START → immediate HTTP POST through recording client
    DATA  → buffered and sent in batches
    STOP  → flush DATA batch first, then send STOP
    after STOP → close recording HTTP client
```

Batch parameters:

```cpp
static const uint16_t HTTP_BATCH_MAX_LINES = 25;
static const uint32_t HTTP_BATCH_MAX_AGE_MS = 500;
```

Flush conditions:

```text
1. batch has 25 DATA rows;
2. batch age reaches 500 ms;
3. STOP is pressed.
```

Serial output remains immediate:

```text
Each DATA row is still printed to Serial as soon as it is sampled.
```

HTTP output is batched only for `DATA` rows during recording.

Control events remain ordered.

Required order on STOP:

```text
1. flush buffered DATA
2. send EVENT,STOP
3. close recording HTTP client
```

This preserves CSV order:

```csv
DATA,...
DATA,...
DATA,...
EVENT,STOP,...
```

### HTTP logger update

`tools/http_logger.py` already supported multiple lines in one POST body because it used:

```python
for line in body.splitlines():
    handle_protocol_line(line, self.writer)
```

The logger was updated mainly in comments and diagnostics.

The documented behavior is now:

```text
POST /line may contain one protocol line or a newline-separated batch.
```

The logger treats transport batching as transparent:

```text
one POST with 25 DATA rows
```

is processed as:

```text
25 normal DATA protocol lines
```

CSV schema remains unchanged.

### Test result

HTTP batch mode works.

Observed result:

```text
25 Hz works
50 Hz works
100 Hz works in current test
```

This confirms that the previous bottleneck was not Wi-Fi bandwidth and not firmware sampling-rate selection.

The bottleneck was per-sample synchronous HTTP transaction overhead.

### Design decision

Use HTTP batch mode as the primary wireless transport for the current prototype.

Current position:

```text
HTTP per-sample mode → acceptable for 5 / 10 Hz and debugging
HTTP keep-alive per-sample → not sufficient
HTTP batch mode → current working wireless mode for 25 / 50 / 100 Hz
TCP stream → future option only if batch mode becomes insufficient
```

### Current protocol

```csv
EVENT,DEVICE_INFO,mac_address,firmware_version,timestamp_ms
EVENT,SAMPLE_RATE,sample_rate_hz,timestamp_ms
EVENT,NEW_SESSION,session_id,timestamp_ms
EVENT,START,session_id,record_id,timestamp_ms
DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm
EVENT,STOP,session_id,record_id,timestamp_ms,sample_count
```

Batch mode does not change the protocol.

It only changes how multiple `DATA` lines are transported over HTTP.

### Confirmed

```text
[✓] Firmware builds
[✓] Firmware uploads to M5StickC Plus2
[✓] Startup sample-rate selection works
[✓] Button A cycles through rates
[✓] Button B confirms selected rate
[✓] Timeout selects 10 Hz only if user did not press Button A
[✓] Firmware emits EVENT,SAMPLE_RATE
[✓] HTTP logger receives SAMPLE_RATE
[✓] recording_sessions.json stores selected sample_rate_hz for new sessions
[✓] Per-sample HTTP limitation was reproduced
[✓] HTTP keep-alive was tested and rejected as insufficient
[✓] HTTP batch mode works
[✓] 100 Hz works in current HTTP batch test
[✓] CSV schema remains unchanged
[✓] Serial output remains immediate
```

### Related files

```text
firmware/m5stickc-plus2/src/main.cpp
tools/http_logger.py
docs/journal.md
```

### Recommended commit message

```text
Add selectable sampling rate and HTTP batch logging
```

### Next step

Continue to the next planned branch:

```text
feature/recording-runs-and-safe-file-names
```

Goal:

```text
Introduce recording_run_id and safer file names so repeated runs do not overwrite or conflict with existing session files.
```


## 2026-06-14 — Async HTTP, анализ качества данных, guides

### Критический дефект обнаружен и исправлен

Запустили `analyze_recordings.py` на реальных данных EXP10 и обнаружили неожиданную картину: `median_dt_ms = 10ms` и `p95 = 10ms` — но `effective_hz ≈ 48 Hz` вместо 100. На `dt_ms` графике был явный паттерн: ровные 10ms, потом gap 260-300ms, снова 10ms. Периодичность gap'ов совпадала с размером HTTP батча — каждые 25 сэмплов. Стало ясно что HTTP POST блокирует `loop()` и IMU в это время просто не опрашивается.

Попытка перенести HTTP в отдельный поток через FreeRTOS `xTaskCreatePinnedToCore` поначалу не дала результата — обе задачи оказались на одном ядре (ядро 1, где по умолчанию работает Arduino `loop()`). Исправление: `task_http` явно пинируется на ядро 0. После этого `dt_ms` график стал идеально ровным — `min/max = 10.0/10.0 ms`, `gaps = 0`, `effective_hz = 100.0 Hz`.

Дополнительно исправили проблему с именем файла: файлы называлась `10Hz` вместо `100Hz` потому что `NEW_SESSION` уходил в очередь раньше чем logger успевал обработать `SAMPLE_RATE`. Решение — задержка 500ms между событиями при старте.

Также убрали `setReuse(true)` из HTTPClient — он ненадёжен при высокой нагрузке и был причиной `code=-1` ошибок. Свежий клиент на каждый батч оказался надёжнее.

Firmware обновлён до v0.8.0. EXP13 — первый датасет с чистыми данными: все три файла получили статус `✅ OK`.

### Попутно

Разобрались с ветковой стратегией: в `main` не мержим без необходимости, каждая фича — ветка от предыдущей рабочей ветки. Добавили `data/analysis/` в `.gitignore` — файлы анализа туда попали случайно. Написали два guides на русском: `01_setup.md` (окружение) и `02_usage.md` (рабочий цикл от запуска logger'а до анализа).

### Next steps

* [ ] Закоммитить firmware v0.8.0
* [ ] Закоммитить analyze_recordings.py, guides, session summary
* [ ] Собрать первый чистый датасет движений


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


## 2026-06-14 — ML pipeline, tech debt, дорожная карта

### ML pipeline и первый классификатор

Запустили `analyze_recordings.py` на EXP14 — все 9 файлов `✅ OK`, 100 Hz, gaps = 0. Написали `compute_features.py` со скользящим окном 2s / шаг 0.5s / обрезка 1s краёв. Параметры вынесены в `feature_config.json`. Загрузили `features.csv` в Orange Data Mining и получили CA = 99.5% на обучающих данных с первой попытки. На новых данных EXP15 — около 70%, что ожидаемо для одного субъекта. Confusion matrix показала что ходьба, бег, приседания и idle разделяются отлично; малые классы (1-3 примера) путаются — нужно добирать данные.

### Tech debt

Закрыли весь накопившийся tech debt в одной ветке. Firmware v0.8.1: индикатор заряда батареи и NEXT REC на экране READY, единая верхняя строка статуса на READY и REC, убран конфликтующий зелёный кружок Wi-Fi. motion_browser.py: удаление отдельных записей из CSV по record_id через multiselect, свободный ввод movement_type вместо строгого selectbox.

### Дорожная карта и долгосрочное видение

Долго обсуждали следующие шаги и долгосрочное видение. Согласовали цепочку: расширенный датасет → FFT фичи → scikit-learn → Edge Impulse → Guardian PoC. Обсудили медицинское применение — непрерывный EWS как альтернатива ручному NEWS2, сенсоры MAX30102 и температура через Grove. Говорили о железе: M5StickC для PoC достаточен с доп аккумулятором на ремешке, для суточного мониторинга — Android / Samsung Watch. JLCPCB как путь к малой серии при наличии гранта. Зафиксировали название 100FNDZ как короткий бренд-идентификатор Stofendez Lab — история происхождения оказалась неожиданно сильной конкурсной нарративой.

### Next steps

* [ ] Большой коммит ветки feature/ml-pipeline
* [ ] Собрать расширенный датасет — несколько субъектов, 10+ записей на класс
* [ ] FFT фичи в compute_features.py
