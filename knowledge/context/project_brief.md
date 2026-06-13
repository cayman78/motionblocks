---
Version: 0.2
Status: Active
Created: 2026-06-13
Last Updated: 2026-06-13
---

# MotionBlocks — Project Brief

## What's New

### 0.2 (2026-06-13)

- Promoted `device_session_id` and `recording_run_id` as stable data identity concepts.
- Clarified that `recording_run_id` belongs to the logger / data layer, not firmware.
- Strengthened the distinction between configured and effective sampling rate.
- Clarified that safe file names are part of data identity, not cosmetic naming.
- Clarified that the analysis layer owns data quality metrics, gap detection, plots, and ML-ready features.

### 0.1 (2026-06-13)

- Created the first versioned project brief.
- Reframed the brief as a stable identity document for humans and LLMs.
- Updated the current stage to reflect selectable sampling rates and HTTP batch logging.
- Clarified responsibility boundaries between firmware, loggers, metadata, and analysis.
- Added the next planned step: recording runs and safe file names.

---

## Project

MotionBlocks is a wearable motion intelligence project by Stofendez Lab.

The project explores how a small wearable device can collect, store, describe, analyze, and later classify human motion patterns.

Current hardware target:

```text
M5StickC Plus2
```

Current working mode:

```text
wearable device
  -> Wi-Fi HTTP batch logger
  -> raw CSV files
  -> JSON metadata
  -> analysis tools
```

The previous wired USB Serial mode remains available for debugging, fallback, and comparison.

MotionBlocks is both:

```text
an educational engineering project
```

and:

```text
a prototype of a personal motion data domain
```

---

## Key Idea

Human movements are treated as reusable **motion blocks**.

Examples:

```text
idle
walking
standing up
sitting down
jumping
hand shaking
impact-like events
fall-like events
unusual motion patterns
```

The system records short motion sessions, links them with metadata, analyzes their structure, and later may classify or detect movement patterns.

The current goal is not advanced fall detection yet.

The current goal is to build a reliable end-to-end motion data pipeline:

```text
record -> store -> describe -> inspect -> analyze -> classify later
```

---

## Long-Term Vision

MotionBlocks may become a personal motion domain inside a broader Human-by-Wire architecture.

In this vision, a person has a structured motion data layer that can be connected to external systems through a future integration layer called **MotionLink**.

Possible future connections:

```text
family dashboard
caregiver dashboard
medical dashboard
personal analytics
Human-by-Wire domains
```

MotionLink is the future communication and integration concept for connecting the personal motion domain to external dashboards and services.

The long-term direction is:

```text
from raw wearable motion data
to understandable personal motion intelligence
```

---

## Current Stage

Current stage:

```text
wireless motion logging with selectable sampling rates and HTTP batch transport
```

Completed earlier stages:

```text
repository setup
M5StickC Plus2 firmware bring-up
IMU reading
acc_norm calculation
button-controlled recording
session-aware logging
Python Serial logger
draft metadata generation
device display layout
Python HTTP logger
Wi-Fi firmware output
DEVICE_INFO event and MAC-based device resolution
selectable sampling rate
HTTP batch mode for higher-rate wireless logging
```

Current confirmed capability:

```text
M5StickC Plus2 can record IMU data wirelessly over Wi-Fi.
The device can select 5 / 10 / 25 / 50 / 100 Hz at startup.
HTTP batch mode works in the current tests, including 100 Hz.
```

Important experimental result:

```text
one sample = one HTTP POST
```

is not suitable for higher-rate recording.

Current wireless mode therefore uses:

```text
HTTP batch mode during recording
```

---

## Architecture / Pipeline

Current conceptual pipeline:

```text
M5StickC Plus2
  -> Serial and/or Wi-Fi
  -> Python logger
  -> raw CSV files
  -> JSON metadata
  -> analysis tools
  -> future browser / viewer
```

Current wireless pipeline:

```text
M5StickC Plus2
  -> Wi-Fi
  -> HTTP POST /line
  -> tools/http_logger.py
  -> data/raw/[experiment_id]/[device_id]/...
  -> data/metadata/experiments.json
  -> data/metadata/recording_sessions.json
```

Debugging / fallback pipeline:

```text
M5StickC Plus2
  -> USB Serial
  -> tools/serial_logger.py
  -> CSV files
  -> metadata
```

Transport rule:

```text
The protocol should remain stable.
The transport may evolve.
```

Current transport interpretation:

```text
Serial:
  line-by-line immediate protocol output

HTTP:
  service events are sent immediately
  DATA rows during recording are sent in newline-separated batches
```

---

## Main Components

### Firmware

Location:

```text
firmware/m5stickc-plus2/
```

Responsibilities:

```text
read IMU
calculate acc_norm
manage device-local session and record state
display current state
emit protocol lines
connect to Wi-Fi
send protocol through Serial and HTTP
```

### Python loggers

Current tools:

```text
tools/serial_logger.py
tools/http_logger.py
```

Responsibilities:

```text
receive protocol lines
write raw CSV files
create draft metadata when requested
preserve existing metadata records
resolve device identity when possible
```

### Metadata layer

Current files:

```text
data/metadata/experiments.json
data/metadata/recording_sessions.json
data/metadata/devices.json
```

Responsibilities:

```text
experiment context
device registry
session descriptions
movement labels
subject information
review status
human comments
tags
```

### Raw data layer

Current format:

```text
wide CSV
```

Each file contains both:

```text
EVENT rows
DATA rows
```

### Analysis layer

Near-term planned tools:

```text
quick analysis scripts
plot generation
effective sample rate checks
data quality metrics
gap detection
motion feature extraction
classification-ready feature tables
```

Future possible tools:

```text
metadata browser
plot viewer
Orange Data Mining workflow
Edge Impulse experiment
scikit-learn baseline
SQLite storage layer
```

---

## Responsibility Split

The firmware intentionally remains simple and generic.

### Firmware knows

```text
session_id
record_id
sample_id
sensor data
device timestamp
technical device identity
firmware version
configured sample rate
```

### Firmware does not know

```text
experiment_id
project-level device_id
subject_id
movement_type
movement_label
recording_run_id
file path
```

### Python logger provides

```text
experiment_id
effective device_id
file path
metadata draft creation
device registry lookup
transport handling
recording_run_id
safe raw file naming
```

`recording_run_id` is a logger-side / data-layer concept.

It should not be generated by firmware.

### Metadata provides

```text
subject_id
movement_type
movement_label
location
comments
tags
status
human interpretation
```

### Analysis layer provides

```text
effective sample rate
duration
configured-vs-effective rate comparison
signal quality checks
gap detection
derived features
plots
classification-ready feature tables
```

Analysis derives quality and feature truth from raw recorded data.

It should not assume that configured sample rate is identical to measured effective sample rate.

This split keeps the device reusable and prevents experiment-specific meaning from being embedded in firmware.

---

## Protocol

The firmware sends the same logical protocol through Serial and HTTP.

Current protocol:

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
EVENT,STOP,A001,1,19000,600
```

HTTP batch mode does not change the protocol.

It changes only how multiple `DATA` lines are transported:

```text
one HTTP POST body may contain several newline-separated DATA rows
```

---

## Data / Storage Model

Current raw data root:

```text
data/raw/
```

Current metadata root:

```text
data/metadata/
```

Current metadata files:

```text
experiments.json
recording_sessions.json
devices.json
```

Generated local data should normally not be committed to Git:

```text
data/raw/
data/processed/
data/features/
data/analysis/
data/db/
```

Only placeholders, documentation, and intentionally prepared examples should be version-controlled.

### Current file naming limitation

The current session-based file naming is not safe enough for repeated device resets:

```text
session_A001.csv
```

because the device can start again from:

```text
A001
```

after reset.

Safe file names are part of data identity, not cosmetic naming.

File names must encode enough identity to prevent accidental overwriting or mixing of repeated device-local sessions.

### Target next file naming model

The next planned improvement is to introduce logger-side recording runs:

```text
device_session_id
recording_run_id
```

Stable interpretation:

```text
device_session_id = session id generated by firmware, for example A001
recording_run_id  = unique logger-side identifier of a physical recording run
```

Responsibility boundary:

```text
device_session_id belongs to firmware / device-local state
recording_run_id belongs to logger / data layer
```

Target example:

```text
run_0001_session_A001_100Hz.csv
run_0002_session_A001_50Hz.csv
run_0003_session_A002_25Hz.csv
```

This prevents accidental overwrite or mixing of different physical recordings that reuse the same device-local session id.

---

## Sampling and Transport

Supported configured sample rates:

```text
5 Hz
10 Hz
25 Hz
50 Hz
100 Hz
```

Interpretation:

```text
sample_rate_hz = configured / selected sampling rate
```

The effective rate should be measured from timestamps:

```text
effective_sample_rate_hz = calculated from DATA timestamp intervals
```

Stable rule:

```text
Never assume configured sample rate equals measured effective sample rate.
Effective rate is an analysis result, not firmware truth.
```

Current transport conclusion:

```text
per-sample HTTP POST is too slow for higher rates
HTTP keep-alive per sample is not enough
HTTP batch mode works in current tests
```

Current batch parameters:

```text
25 DATA rows per batch
500 ms maximum batch age
flush before STOP
```

---

## Development Stack

Current stack:

```text
VS Code
PlatformIO
Arduino framework
M5Unified
Python
CSV
JSON metadata
GitHub
```

Near-term analysis / ML options:

```text
matplotlib
pandas
scikit-learn
Orange Data Mining
Edge Impulse
```

Possible future storage layer:

```text
SQLite
```

SQLite is intentionally not introduced yet because readable CSV and JSON are sufficient for the current prototype stage.

---

## Repository

Repository name:

```text
motionblocks
```

Important folders:

```text
firmware/      device firmware
tools/         Python loggers and analysis tools
data/          local generated data and metadata
docs/          human-readable documentation and journal
knowledge/     LLM-oriented project context, decisions and takeaways
tests/         future tests and validation scripts
```

Recommended distinction:

```text
docs/      -> documentation for humans
knowledge/ -> compact project memory for LLM-assisted work
```

---

## Naming

Stable names:

```text
Stofendez Lab  -> laboratory / team
MotionBlocks   -> project
MotionLink     -> future integration layer
```

Current operational terms:

```text
HTTP logger       -> Python receiver for wireless data
Serial logger     -> Python receiver for USB Serial data
device_session_id -> session id generated by firmware, for example A001
recording_run_id  -> logger-side unique identifier of a physical recording run
sample_rate_hz    -> configured / selected sample rate
effective_sample_rate_hz -> measured rate from timestamps
```

---

## Current Next Step

Immediate next branch:

```text
feature/recording-runs-and-safe-file-names
```

Goal:

```text
introduce logger-side recording_run_id and safer file names
```

Expected result:

```text
repeated device resets do not overwrite or mix old files
A001 can repeat safely
different sample rates produce separate identifiable files
metadata records can reference unique recording runs
```

After that, planned quick-win work:

```text
feature/quick-analysis-tools
```

Expected focus:

```text
analyze generated CSV files
calculate effective sample rate
detect gaps and suspicious intervals
generate simple plots
produce features.csv for Orange / scikit-learn / Edge Impulse experiments
```

---

## Design Principles

Current project principles:

```text
Keep the device simple.
Keep the protocol stable.
Keep transport replaceable.
Preserve Serial output for debugging.
Use readable CSV for raw data.
Use readable JSON for metadata.
Do not move to a database too early.
Do not embed experiment meaning in firmware.
Do not overwrite human-completed metadata.
Treat safe file names as part of data identity.
Keep logger-side run identity out of firmware.
Measure effective sampling rate from data.
Do not assume configured rate equals effective rate.
Let analysis derive quality metrics and features from raw data.
Prefer quick observable results before overbuilding.
Keep the project understandable for children.
Keep the architecture compatible with future FDAM / Human-by-Wire ideas.
```

---

## Open Questions

Current important open questions:

```text
What exact recording_run_id format should be used?
Should safe file names include sample_rate_hz, date, or both?
Where should effective_sample_rate_hz be stored?
Should loggers update records_actual automatically after STOP?
How should quick analysis outputs be organized under data/analysis?
When should a Streamlit metadata browser be introduced?
When should metadata editing be added?
When should JSON metadata move to SQLite?
What is the practical battery life in Wi-Fi batch mode?
How stable is 100 Hz during longer real wearable sessions?
```

---

## Future Ideas

Near-term analysis ideas:

```text
session quality report
acc_norm plots
dt_ms plots
feature extraction per recording
features.csv for Orange Data Mining
baseline scikit-learn classifier
Edge Impulse demonstration
```

Possible first movement classes:

```text
idle
walking
shake
impact-like event
jump
sit-to-stand
```

Longer-term ideas:

```text
motion library
movement similarity search
fall-like event detection
anomaly detection
family dashboard
caregiver dashboard
MotionLink integration layer
```
