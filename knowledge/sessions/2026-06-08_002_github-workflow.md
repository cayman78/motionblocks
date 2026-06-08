# LLM Session — GitHub Workflow

## Date

2026-06-08

## Participants

- Scientific lead
- LLM assistant

## Topic

GitHub workflow for MotionBlocks team development.

## Context

The project will be developed by several children, a mentor, and a scientific lead. The goal is to use the project as a training ground for group development.

## Main discussion

We discussed:

- branch workflow;
- local and remote branches;
- pull requests;
- merge process;
- possible rights separation between `dev` and `main`.

## Key decisions

1. Use branches for separate tasks.
2. Use `main` as stable branch.
3. Use `feature/...` branches for development tasks.
4. Use Pull Requests for merging.
5. Consider adding `dev` as integration branch when the team grows.

## Recommended workflow

```text
feature/... → dev → main