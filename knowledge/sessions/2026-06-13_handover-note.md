# Handover Note — MotionBlocks

## What Feels Important

The project is no longer mainly a firmware experiment. It has quietly shifted into a **data identity and data quality project**.

The device now works well enough that the main risks are no longer “can we read IMU?” or “can we send data?” but:

```text
can we trust what each file means?
can we avoid mixing recordings?
can we later explain why one signal is good or bad?
```

The next chat should treat file identity, metadata identity, and analysis quality as first-class concerns.

A recurring implicit rule has been:

```text
the child-facing model must stay simple,
but the internal data model must not become sloppy.
```

This tension matters. The system should remain explainable to children while still being robust enough for later ML work.

Another important intuition: **do not make the firmware smarter just because it is possible**. The firmware is deliberately kept generic. Most “meaning” should live in the logger, metadata, and analysis layers.

The negative HTTP keep-alive result is more important than it looks. It clarified a general design pattern:

```text
optimize architecture by changing the transaction model,
not by micro-optimizing the wrong model.
```

This may apply again later.

## Emerging Ideas

The first real “wow” moment for children should probably not be fall detection. It should be a small classifier that recognizes a few simple movement classes:

```text
idle
walking
shake
impact-like movement
jump
```

The best path may be:

```text
collect clean small dataset
generate features.csv
show Orange / Edge Impulse / scikit-learn result
then connect it back to the device
```

There is an emerging layered analysis concept:

```text
raw data quality first
simple features second
visual plots third
ML classification fourth
```

Skipping the first two and jumping to ML would probably create confusion.

The project may benefit from a “lab notebook” mindset: every recording should be treated like an experiment specimen, not just a CSV file.

The safe filename branch is not just a cleanup task. It is the point where MotionBlocks starts becoming a small data platform.

There is also a promising educational theme:

```text
configured sampling rate vs effective sampling rate
```

This is a very teachable concept: what we ask the system to do versus what the system actually does.

## Risks and Concerns

The biggest technical risk is silent data corruption by meaning, not by bytes.

Examples:

```text
A001 from yesterday and A001 from today look similar.
A001 at 10 Hz and A001 at 100 Hz look similar.
The file exists but nobody remembers the movement.
The metadata exists but points to the wrong file.
The configured sample rate is trusted without checking effective rate.
```

The biggest architectural risk is letting implementation convenience leak into conceptual model.

Examples:

```text
renumbering device sessions silently;
putting project-level ids into firmware;
treating filenames as cosmetic;
treating sample_rate_hz as measured truth;
letting current JSON structure become accidental permanent schema.
```

The biggest educational risk is overbuilding before children see something exciting. The project needs quick visible results soon: plots, classification, movement comparison.

Another risk: the project has several artifacts now, and they may drift. Future updates should check consistency across:

```text
project_brief.md
current_state.md
glossary.md
takeaways
session summaries
journal
```

There is a weak but important concern around “too many layers too early.” SQLite, FDAM, browser UI, ML, metadata editor, and dashboards are all tempting. The next chat should keep asking:

```text
What is the smallest useful next layer?
```

## Suggested Directions

First, finish safe file names and `recording_run_id`.

Do not start the browser or ML layer before this is done. The browser and ML tools will be much cleaner if every recording has stable identity.

For the next implementation, pay attention to these details:

```text
old files must not be overwritten;
device_session_id must stay visible;
recording_run_id must be assigned by logger;
sample_rate_hz should appear in filename;
metadata must preserve manual edits;
old file formats should remain readable where practical.
```

After that, build `tools/analyze_recordings.py` before Streamlit.

The first analysis script should answer:

```text
is this recording usable?
did the device actually keep the selected rate?
where are gaps or timing problems?
what does acc_norm look like?
```

Then use its outputs as the basis for the browser.

For children-facing demos, prefer:

```text
Orange Data Mining for no-code visual ML;
Edge Impulse for embedded/wearable “wow”;
scikit-learn for reproducible local baseline.
```

Do not start with deep learning. Simple features plus Random Forest or kNN will probably be enough for an impressive first demo.

For plots, start with:

```text
acc_norm over time
ax / ay / az over time
gx / gy / gz over time
dt_ms over sample index
```

The `dt_ms` plot may be the most educational and diagnostic one.

## Notes for the Next Chat

The user is building this as both an engineering project and an educational project with children. Responses should preserve both modes.

Good answers should usually separate:

```text
what to do now
what to postpone
why the boundary matters
```

The user tends to prefer structured artifacts and workflow discipline. When a decision is made, it is often useful to ask whether it belongs in:

```text
current_state
project_brief
glossary
takeaway
session summary
journal
```

Avoid turning every discussion into a large document. The user is trying to keep the knowledge base useful, not merely complete.

When proposing implementation, preserve the current architectural instinct:

```text
firmware = simple recorder
logger = transport + files + draft metadata
metadata = meaning
analysis = truth from data
browser = inspection
ML = later classification
```

A useful recurring question for future work:

```text
Is this knowledge device-local, logger-local, metadata-level, or analysis-level?
```

That question has repeatedly led to better design decisions.

The next chat should be careful with the term `session_id`. It is now semantically dangerous unless clarified. Prefer:

```text
device_session_id
recording_run_id
```

when discussing file identity.

The most important immediate engineering move is to make the data safe before generating lots of recordings.
