# Current State

## Date

2026-06-14

## Current project phase

Stage 6 — Async HTTP transport, чистые данные, анализ качества.

Проект завершил wireless HTTP batch logging, device identity, selectable sampling rate, recording_run_id, safe file names, metadata v2, motion browser, analyze_recordings и async HTTP через FreeRTOS.

Первый датасет с подтверждённым качеством (EXP13): `effective_hz = 100.0 Hz`, `gaps = 0`.

Текущий рабочий pipeline:

```text
M5StickC Plus2 (v0.8.1)
  → Wi-Fi
  → HTTP POST /line (async, FreeRTOS queue, ядро 0)
  → tools/http_logger.py
  → run_A_session_A001_100Hz.csv
  → tools/analyze_recordings.py
  → data/analysis/EXP__/session_quality.csv + plots
  → tools/compute_features.py
  → data/analysis/features/EXP__/features.csv
  → Orange Data Mining / scikit-learn
```

Предыдущий USB Serial pipeline остаётся для отладки.

---

## Project identity

* Laboratory / team: **Stofendez Lab** (100FNDZ)
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
motionblocks.logger.v0.8.1 — async HTTP via FreeRTOS + selectable sampling rate + battery indicator
```

Current active branch:

```text
feature/ml-pipeline
```

Current firmware capabilities:

* reads IMU data from M5StickC Plus2;
* calculates `acc_norm`;
* supports button-controlled recording;
* manages device-local sessions and records;
* reports technical device identity through `EVENT,DEVICE_INFO`;
* supports sampling-rate selection at startup;
* reports selected rate through `EVENT,SAMPLE_RATE`;
* sends protocol through Serial (immediate) and HTTP (async queue);
* connects to Wi-Fi using local `wifi_config.h`;
* HTTP задача работает на ядре 0, `loop()` и IMU на ядре 1 — без взаимной блокировки;
* FreeRTOS очередь 500 строк буферизует DATA между IMU и HTTP задачами;
* батч 20 DATA строк или 200ms, свежий HTTPClient на каждый батч;
* задержка 500ms между SAMPLE_RATE и NEW_SESSION — корректное имя файла;
* показывает стартовый splash screen;
* показывает Wi-Fi статус / IP на READY экране;
* показывает выбранную частоту на READY экране;
* показывает текущие метрики записи на REC экране;
* shows Wi-Fi status text + RATE + battery % on status bar (top line, both screens);
* shows SESSION and NEXT REC number on READY screen;
* shows SAVED экран 1.2s после остановки записи.

Confirmed behavior:

* Device starts with session `A001`.
* Button A double click (600 ms window) starts a new record.
* Button A single click stops the current record.
* Button B switches to the next session.
* `record_id` resets to `1` when session changes.
* `sample_id` increments inside each record.
* IMU data is sampled only while recording.
* `acc_norm` is calculated as `sqrt(ax*ax + ay*ay + az*az)`.
* In rest position, `acc_norm` should be close to `1.0 g`.
* Firmware does not know `experiment_id`, project-level `device_id`, `subject_id`, `movement_type`, or `movement_label`.

Known firmware / transport limits:

* `session_id` is device-local and can repeat after device reset (handled by logger-side `recording_run_id`).
* `sample_rate_hz` means configured / selected rate, not verified effective rate.
* Effective sampling rate calculated by `analyze_recordings.py` from timestamps.
* При длинных записях (>500 строк в очереди) возможны единичные потери — `[WARN] HTTP queue full`. В EXP13 потерь не зафиксировано.
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

Status: working / useful for debugging. Serial output immediate.

### Wireless working path

```text
M5StickC Plus2
  → Wi-Fi
  → HTTP POST /line (FreeRTOS async, ядро 0)
  → tools/http_logger.py
  → CSV / metadata
```

Status: working. Подтверждено на EXP13: `effective_hz = 100.0 Hz`, `gaps = 0`.

Current HTTP behavior:

```text
IMU / loop() — ядро 1 (Arduino default)
task_http    — ядро 0 (FreeRTOS, pinned)

task_http:
  DATA  → батч 20 строк, flush каждые 200ms или при заполнении
  EVENT → flush DATA, потом one-shot POST
  свежий HTTPClient на каждый батч (setReuse убран)
```

Batch parameters:

```cpp
HTTP_QUEUE_SIZE      = 500   // строк в FreeRTOS очереди
HTTP_BATCH_MAX_LINES = 20
HTTP_BATCH_MAX_AGE_MS = 200
HTTP_TIMEOUT_MS      = 2000
task_http stack      = 16384 байт
```

The Python HTTP logger is launched from repository root:

```powershell
python tools/http_logger.py --host 0.0.0.0 --port 8080 --experiment-id EXP01 --device-id m5-01 --create-metadata
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
feature/async-http
```

---

## Current next actions

### 1. Собрать расширенный датасет

```text
— несколько субъектов (минимум 2-3)
— классы: idle, walking, running, jumping,
  squats, stairs_up/down, shake, fall-like
— 10+ записей на класс на субъекта
```

### 2. FFT фичи в compute_features.py

Частотные характеристики для ритмических движений.
Улучшит разделение walking / running / jumping.

### 3. scikit-learn baseline

Воспроизводимая модель в коде. Сравнение алгоритмов.
Сохранение модели (.pkl).

### 4. Edge Impulse — firmware_2_classifier

Задеплоить модель на устройство. Real-time классификация на экране.

### 5. Guardian PoC — firmware_3_guardian

Тревожная кнопка + автосрабатывание при аномальных движениях.
Анализ ошибок 1/2 рода с детьми. Выбор порога специфичности.

---

## Analysis and browser tools

### tools/analyze_recordings.py

Status: **working**.

```powershell
python tools/analyze_recordings.py --file data\raw\EXP01\m5-01\run_A_session_A001_100Hz.csv
python tools/analyze_recordings.py --experiment EXP01
python tools/analyze_recordings.py --all
```

Outputs:

```text
data/analysis/[experiment_id]/session_quality.csv
data/analysis/[experiment_id]/plots/[file]_acc_norm.png
data/analysis/[experiment_id]/plots/[file]_dt_ms.png
```

Качество подтверждено на EXP13: все файлы `✅ OK`, `effective_hz = 100.0 Hz`.

### tools/motion_browser.py

Status: **working**.

```powershell
streamlit run tools/motion_browser.py
```

Modes: 🗂 Обзор / 📈 Просмотр / ✏️ Редактор.

Редактор: свободный ввод movement_type (text + подсказки),
удаление отдельных записей из CSV по record_id.

### tools/compute_features.py

Status: **working**.

```powershell
python tools/compute_features.py --experiment EXP14
python tools/compute_features.py --experiment EXP14 --window-sec 2.0 --step-sec 0.5
```

Параметры окна по умолчанию из `data/metadata/feature_config.json`.
CLI аргументы переопределяют дефолты.

Output: `data/analysis/features/[experiment_id]/features.csv`

Первый эксперимент EXP14: CA = 99.5% в Orange Data Mining (Random Forest, 5-fold CV).

---

## Known Issues / Limitations

* `serial_logger.py` not yet updated with `recording_run_id` — still writes `session_A001.csv`.
* `sample_rate_hz` currently means configured / selected rate, not verified effective rate.
* При длинных активных записях (>500 строк в FreeRTOS очереди) возможны единичные потери DATA строк — `[WARN] HTTP queue full`. В EXP13 не зафиксировано.
* Long-record stability at 100 Hz still needs measurement beyond EXP13 test recordings.
* Battery life in Wi-Fi async HTTP mode is not yet measured.
* Metadata still requires manual completion after recording (motion_browser.py облегчает, но не автоматизирует).
* `records_actual` is not automatically updated after STOP.

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

---

## Recent Changes

### 2026-06-14 (вечер)

* Firmware v0.8.1: батарея на READY и REC экранах, NEXT REC на READY,
  единая `drawStatusBar()`, убран зелёный кружок Wi-Fi с REC.
* `tools/compute_features.py` создан — скользящее окно 2s/0.5s,
  параметры из `data/metadata/feature_config.json`.
* Первый ML эксперимент: Orange Data Mining, CA = 99.5%, Random Forest.
* `tools/motion_browser.py` — удаление записей из CSV, свободный ввод movement_type.
* Branding: 100FNDZ как короткий идентификатор Stofendez Lab.
* Ветка: `feature/async-http` → `feature/ml-pipeline`.
* Phase transition: от сбора данных → к ML pipeline.

### 2026-06-14 (утро)

* Обнаружен и исправлен критический дефект: HTTP POST блокировал IMU опрос → `effective_hz ≈ 48 Hz` при gaps ~300ms.
* Firmware v0.8.0: async HTTP через FreeRTOS. `task_http` на ядре 0, `loop()` на ядре 1.
* Первый подтверждённо чистый датасет EXP13: `effective_hz = 100.0 Hz`, `gaps = 0`, статус `OK`.
* `tools/analyze_recordings.py` создан и подтверждён.
* `tools/motion_browser.py` v2: режимы Обзор / Просмотр / Редактор.
* Metadata v2: `subjects.json`, `schema.json`, упрощённый формат сессий.
* `docs/guides/01_setup.md` и `02_usage.md` написаны.
* Ветковая стратегия: feature ветки от последней feature ветки, в `main` не мержим.
* `data/analysis/` добавлен в `.gitignore`.
* Phase transition: от отладки транспорта → к сбору чистого датасета.

### 2026-06-13 (end of day)

* Implemented `recording_run_id` in `tools/http_logger.py`.
* Safe file names: `run_A_session_A001_100Hz.csv`.
* Firmware bumped to v0.7.0.
* Branch `feature/recording-runs-and-safe-file-names` merged to `main`.

### 2026-06-13 (earlier)

* Added `EVENT,DEVICE_INFO` and MAC-based device resolution.
* Added startup sampling-rate selection: 5 / 10 / 25 / 50 / 100 Hz.
* HTTP batch mode implemented and confirmed at 100 Hz.

### 2026-06-10

* Wireless HTTP logging verified and working.
* Phase transition from wired Serial debugging to wireless HTTP data collection.
