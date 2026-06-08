# Current State

## Date

2026-06-08

## Current project phase

Stage 1 — Device bring-up and team workflow.

## Done

- Project name selected: MotionBlocks.
- Laboratory name selected: Stofendez Lab.
- Technology name selected: MotionLink.
- GitHub repository created.
- Basic repository structure planned.
- Initial database concept discussed:
  - `records`
  - `recorddata`
  - optional future `recordfeatures`

## Current decisions

- Use private GitHub repository at the start.
- Use VS Code + PlatformIO + Arduino framework.
- Use CSV for raw data.
- Use SQLite as the motion database.
- Use `records.payload` as flexible JSON field.
- Do not store real names of children in the database.
- Use GitHub feature branches and pull requests.
- Use `main` as stable branch.
- Possible future `dev` branch for integration.

## Next actions

- Create folder structure in repository.
- Commit initial structure.
- Add `llm/` knowledge folder.
- Create PlatformIO project.
- Upload first firmware.
- Read IMU data.
- Log first CSV.

## Open questions

- Whether to introduce `dev` immediately or later.
- Whether to use Edge Impulse in Stage 1 or Stage 2.
- Exact format of CSV logs.
- Exact database schema version 0.1.