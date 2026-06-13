# `knowledge/` folder structure

## Purpose

The `knowledge/` folder contains compact project knowledge intended primarily for LLM-assisted work.

It is not a replacement for `docs/`, `README.md`, or source code comments.

Its purpose is to preserve the current project understanding in a form that can be quickly reused in future ChatGPT / LLM sessions.

In simple terms:

```text
docs/      → documentation for humans
knowledge/ → structured context for LLM
```

---

## Role in the project

The `knowledge/` folder should answer questions like:

```text
What is this project?
What has already been decided?
What is the current architecture?
What conventions are we following?
What should the LLM remember before continuing work?
What are the current open questions?
```

It should reduce repeated explanation and help continue the project without reconstructing context from scratch.

---

## Proposed structure

```text
knowledge/
  current_state.md
  project_brief.md
  glossary.md
  architecture.md
  conventions.md
  decisions/
  takeaways/
  prompts/
  archive/
```

---

## `current_state.md`

Current working state of the project.

This is the most important file for continuing work with an LLM.

It should contain:

```text
current branch
current firmware version
current protocol
current data pipeline
what works
what is being tested now
known problems
next immediate steps
```

This file should be kept short and updated frequently.

Recommended use:

```text
Attach or paste this file at the beginning of a new LLM session.
```

---

## `project_brief.md`

Stable high-level description of the project.

It should explain:

```text
project name
purpose
target users
educational goal
technical goal
main components
long-term vision
```

Unlike `current_state.md`, this file should not change after every small implementation step.

It is the compact “what is MotionBlocks?” document.

---

## `glossary.md`

Project vocabulary.

It should define terms such as:

```text
MotionBlocks
MotionLink
recording session
recording run
device_session_id
recording_run_id
sample_rate_hz
effective_sample_rate_hz
DATA row
EVENT row
metadata
raw data
experiment
subject
movement_type
movement_label
```

The glossary prevents terminology drift.

---

## `architecture.md`

Current architecture of the system.

It should describe the main data flow:

```text
M5StickC Plus2
  → Serial / Wi-Fi
  → Python logger
  → raw CSV
  → metadata JSON
  → analysis tools
  → browser / viewer
```

It should also describe responsibility boundaries:

```text
Firmware:
  session_id
  record_id
  sample_id
  sensor data
  technical device identity
  configured sample rate

Python logger:
  experiment_id
  device_id
  file path
  recording_run_id
  metadata draft creation

Metadata:
  subject_id
  movement_type
  movement_label
  comments
  tags
  status

Analysis layer:
  effective sample rate
  quality metrics
  plots
  ML features
```

---

## `conventions.md`

Project conventions.

This file should contain practical rules that must stay consistent across code and metadata.

Examples:

```text
file naming convention
branch naming convention
event protocol convention
metadata field naming
sample rate interpretation
CSV schema rules
device identity rules
```

Example topics:

```text
sample_rate_hz means configured sample rate
effective_sample_rate_hz is calculated from timestamps
firmware does not know experiment_id
firmware does not know project-level device_id
HTTP batch mode does not change protocol format
```

---

## `decisions/`

Stable architectural decisions.

One file per important decision.

Example:

```text
knowledge/decisions/
  2026-06-10_firmware-does-not-know-experiment-id.md
  2026-06-11_device-id-resolved-by-mac.md
  2026-06-11_http-batch-is-primary-wireless-transport.md
  2026-06-11_sample-rate-is-selected-at-startup.md
```

Each decision file should contain:

```text
context
decision
rationale
alternatives considered
consequences
status
```

Use this folder for decisions that should remain valid for a while.

---

## `takeaways/`

Reusable summaries from important discussions.

These are more informal than `decisions/`.

Use this folder for compact lessons learned, experimental conclusions, and working conclusions.

Example:

```text
knowledge/takeaways/
  2026-06-09_sampling-rate-choice.takeaways.md
  2026-06-10_raw-data-and-metadata-format.takeaways.md
  2026-06-11_device-identity-and-mac-address.takeaways.md
  2026-06-11_http-keep-alive-negative-result.takeaways.md
```

A takeaway may later become a formal decision or part of documentation.

---

## `prompts/`

Reusable prompts for working with LLMs.

Example:

```text
knowledge/prompts/
  continue-motionblocks-work.md
  review-firmware-changes.md
  generate-journal-entry.md
  analyze-data-pipeline.md
  prepare-next-branch.md
```

This folder should contain prompts that help restart work quickly.

Example use:

```text
Paste current_state.md + continue-motionblocks-work.md into a new LLM session.
```

---

## `archive/`

Old or superseded knowledge.

Use this folder when a file is no longer current but may still be useful historically.

Example:

```text
knowledge/archive/
  old_protocol_notes.md
  early_metadata_structure.md
  abandoned_transport-options.md
```

Do not delete useful reasoning too early.

Move it to `archive/` when it becomes outdated.

---

## What should not go into `knowledge/`

Do not put the following into `knowledge/`:

```text
large raw CSV files
generated plots
Python virtual environments
firmware build artifacts
temporary logs
private Wi-Fi credentials
large screenshots
long unstructured chat dumps
```

These belong elsewhere:

```text
data/raw/       → raw recordings
data/analysis/  → generated analysis results
docs/           → human-readable documentation
firmware/       → firmware source code
tools/          → Python scripts
```

---

## Relationship with `docs/`

Recommended distinction:

```text
docs/
  stable human documentation
  project journal
  user-facing explanations
  setup guides
  how-to instructions

knowledge/
  compact LLM context
  current state
  decisions
  takeaways
  conventions
  prompts
```

The same topic may appear in both places, but in different form.

Example:

```text
docs/journal.md
  long chronological history

knowledge/current_state.md
  short current state only

knowledge/takeaways/
  reusable conclusions from the journal and discussions
```

---

## Minimal initial version

At the current stage, the folder does not need to be too complex.

A practical starting structure is:

```text
knowledge/
  current_state.md
  project_brief.md
  glossary.md
  conventions.md
  takeaways/
  prompts/
```

Add `architecture.md` and `decisions/` when the project grows.

---

## Maintenance rule

The `knowledge/` folder should stay useful for continuation.

After each meaningful work session, update at least one of:

```text
current_state.md
journal.md
takeaways/
decisions/
```

Suggested rule:

```text
journal.md records what happened;
current_state.md records where we are now;
takeaways/ records what we learned;
decisions/ records what we decided.
```

---

## Current recommendation

Use `knowledge/` as the LLM-facing operational memory of MotionBlocks.

Keep it compact, structured, and current.

Do not turn it into a dumping ground.

The most important file is:

```text
knowledge/current_state.md
```

If only one file is updated regularly, it should be this one.
