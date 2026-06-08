# MotionBlocks

**MotionBlocks** is a wearable motion intelligence project by **Stofendez Lab**.

The project explores how a small wearable device can collect, label, analyze, and classify human motion patterns.

## Idea

MotionBlocks treats human movements as reusable "motion blocks":

- walking
- standing up
- sitting down
- shaking hand
- falling-like events
- unusual motion patterns

The long-term vision is to build a personal motion domain connected to external dashboards through **MotionLink** technology.

## Project structure

```text
firmware/      Device firmware for M5StickC Plus2
server/        Local server for wireless data collection
data/          Raw, processed, example data, and SQLite database
tools/         Python scripts for logging, import, and analysis
notebooks/     Data exploration notebooks
docs/          Project documentation and meeting notes
experiments/   Rapid insight tools: Edge Impulse, ChatGPT analysis, Orange
tests/         Tests and validation scripts