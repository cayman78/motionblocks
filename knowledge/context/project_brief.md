---
Version: 0.3
Status: Active
Created: 2026-06-13
Last Updated: 2026-06-14
---

# MotionBlocks — Project Brief

## What's New

### 0.3 (2026-06-14)

- Added 100FNDZ as short brand identifier for Stofendez Lab.
- Updated Current Stage to reflect async HTTP transport, ML pipeline, and first classifier result.
- Extended Architecture / Pipeline to include ML layer (compute_features → features.csv → classifier).
- Extended Long-Term Vision: Guardian PoC, суточный мониторинг, медицинский EWS.
- Updated Current Next Step: датасет → FFT → scikit-learn → Edge Impulse → Guardian PoC.
- Cleaned Open Questions: removed resolved questions.
- Updated Future Ideas: removed implemented items, added Guardian / monitoring / medical.
- Added new Design Principle: optimize by changing the transaction model, not by micro-optimizing the wrong model.

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

MotionBlocks is a wearable motion intelligence project by Stofendez Lab (100FNDZ).

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

**Near-term vision — Guardian:**

A wearable device that detects anomalous movement patterns and triggers alerts.
Combines manual SOS button with automatic detection of fall-like or unusual events.
Demonstrates Type I / Type II error tradeoffs and threshold selection to children.

**Medium-term vision — daily pattern monitoring:**

Not just event detection but continuous profiling of a person's daily rhythm.
The system learns what "normal" looks like for this specific person and flags deviations:
unusual wake time, slower gait than usual, missed meal pattern, night-time activity.
Analogy: anti-fraud systems that detect anomalies in personal behavior patterns.

**Long-term vision — medical early warning:**

Continuous automated EWS (Early Warning System) as an alternative to manual NEWS2 scoring.
Additional sensors: MAX30102 (pulse/SpO2), skin temperature, respiratory rate from IMU.
Predicts pre-critical states hours before clinical deterioration.
Target applications: hospital ward monitoring, home care, elderly independence support.

**Integration and product path:**

```text
MotionLink integration layer
family / caregiver / medical dashboard
custom wearable hardware (accessibility design for elderly)
production via JLCPCB for small series
```

The long-term direction is:

```text
from raw wearable motion data
to understandable personal motion intelligence
to real-time safety and health monitoring
```

---

## Current Stage

Current stage:

```text
ML pipeline — feature extraction, first classifier, Guardian PoC preparation
```

Completed earlier stages:

```text
repository setup
M5StickC Plus2 firmware bring-up
IMU reading and acc_norm calculation
button-controlled recording
session-aware logging
Python Serial logger
draft metadata generation
device display layout
Python HTTP logger and Wi-Fi firmware output
DEVICE_INFO event and MAC-based device resolution
selectable sampling rate (5 / 10 / 25 / 50 / 100 Hz)
recording_run_id and safe file names
async HTTP transport via FreeRTOS (firmware v0.8.x)
analyze_recordings.py — quality metrics and plots
motion_browser.py — session viewer and metadata editor
compute_features.py — sliding window feature extraction
first ML experiment: Orange Data Mining, CA = 99.5%
```

Current confirmed capability:

```text
M5StickC Plus2 records clean IMU data at 100 Hz over Wi-Fi.
effective_hz = 100.0 Hz, gaps = 0 (confirmed EXP13, EXP14).
Sliding window features extracted and classified in Orange.
First real dataset collected (EXP14): walking, running, jumping,
squats, idle, petting-the-cat and other classes.
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
  -> analyze_recordings.py (quality metrics, plots)
  -> compute_features.py (sliding window features)
  -> features.csv
  -> classifier (Orange / scikit-learn / Edge Impulse)
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

```text
1. Collect expanded dataset — multiple subjects, 10+ recordings per class
2. Add FFT features to compute_features.py
3. scikit-learn baseline — reproducible model in code
4. Edge Impulse — firmware_2_classifier, real-time on device
5. Guardian PoC — firmware_3_guardian, anomaly detection + alert
```

Details in `current_state.md`.

---

## Design Principles

Current project principles:

```text
Keep the device simple.
Keep the protocol stable.
Keep transport replaceable.
Optimize by changing the transaction model, not by micro-optimizing the wrong model.
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

```text
Should records_actual be updated by the logger after STOP?
Should metadata contain transport information (http_batch, serial, batch parameters)?
Should channels be repeated in each recording session or moved to a shared schema?
Should events and DATA rows live in the same CSV, or should event logs be separated later?
Should device_id ever be stored in firmware, or always resolved by the logger?
When should SQLite be introduced?
Which Android / Watch hardware is best for daily monitoring phase?
When should MAX30102 (pulse/SpO2) be added as next sensor?
```

---

## Future Ideas

Near-term:

```text
Guardian PoC — firmware_3_guardian
  anomaly detection, SOS button, Type I/II error demo with children

scikit-learn baseline
  reproducible classifier in code, model persistence

Edge Impulse
  deploy model to device, real-time movement classification on screen

FFT features
  frequency-domain features for better rhythm detection
```

Medium-term:

```text
daily pattern profiling
  personal baseline, deviation detection, anomaly score

additional sensors
  MAX30102 (pulse, SpO2) via Grove
  skin temperature

Android / Samsung Watch
  continuous monitoring platform for daily rhythm analysis
```

Long-term:

```text
medical EWS — continuous early warning system
custom wearable hardware (accessibility design for elderly)
MotionLink integration layer
LLM agent for pattern interpretation and risk assessment
family / caregiver / medical dashboard
```
