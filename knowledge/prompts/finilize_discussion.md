You are helping maintain the project knowledge base for a GitHub repository.

Your task is to process the provided discussion transcript and produce structured project memory artifacts.

The project uses the following knowledge structure:

```text
llm/
├── context/
│   ├── project_brief.md
│   ├── current_state.md
│   ├── architecture_context.md
│   └── glossary.md
├── sessions/
├── takeaways/
└── prompts/
```

The discussion may contain ideas, decisions, open questions, plans, terminology, architecture notes, and implementation details.

You must produce three outputs:

1. A takeaway file for the specific discussion.
2. An updated `current_state.md`.
3. An updated `glossary.md`.

Do not invent facts. If something is only a proposal, mark it as a proposal. If something is uncertain, mark it as an open question. Separate accepted decisions from ideas and options.

Use concise, reusable project language. The result should be suitable for future loading into an LLM as project context.

---

# Input

You will receive:

1. Current project context, if available.
2. Current `current_state.md`, if available.
3. Current `glossary.md`, if available.
4. Discussion transcript.

If current files are not provided, create reasonable first versions based only on the transcript.

---

# Output format

Produce the following three markdown blocks.

---

## 1. Takeaway file

Suggest a filename in this format:

```text
llm/takeaways/YYYY-MM-DD_short-topic.takeaways.md
```

Then produce the file content:

```markdown
# Takeaways — <Short Topic>

## Date

<YYYY-MM-DD>

## Status

Draft / Accepted / Superseded

## Summary

<3–7 concise lines explaining what was discussed and why it matters.>

## Decisions

- <Accepted decision 1>
- <Accepted decision 2>

## Proposed ideas

- <Idea or option that was discussed but not finally accepted>
- <Another proposal>

## Rationale

- <Why the decisions or proposals make sense>
- <Important trade-offs>

## Open questions

- <Question 1>
- <Question 2>

## Action items

- [ ] <Concrete next action>
- [ ] <Concrete next action>

## Related repository areas

- `path/to/file_or_folder`
- `path/to/file_or_folder`

## Tags

#project #llm #takeaway
```

Rules for the takeaway:

* Keep it short but meaningful.
* Do not include long transcript fragments.
* Do not include private irrelevant conversation.
* Preserve important names, technical terms, architectural decisions, and unresolved questions.
* If the discussion includes several topics, either split them into sections or suggest multiple takeaway files.

---

## 2. Updated `current_state.md`

Produce the full updated content for:

```text
llm/context/current_state.md
```

Use this structure:

```markdown
# Current State

## Date

<YYYY-MM-DD>

## Project phase

<Current stage or phase>

## Project identity

- Project:
- Laboratory / team:
- Related technology:
- Repository:

## Current goals

- <Goal 1>
- <Goal 2>

## Done

- <Completed item>
- <Completed item>

## Current decisions

- <Accepted project decision>
- <Accepted project decision>

## Current architecture notes

- <Important architecture note>
- <Important architecture note>

## Current technical stack

- <Tool / technology>
- <Tool / technology>

## Current repository structure notes

- <Folder or file decision>
- <Folder or file decision>

## Open questions

- <Open question>
- <Open question>

## Next actions

- [ ] <Next action>
- [ ] <Next action>

## Recently added knowledge

- <Short note about what was added from the latest discussion>
```

Rules for `current_state.md`:

* It should represent the latest reliable state of the project.
* Remove outdated items if they are clearly superseded.
* Keep stable decisions, current goals, and next steps.
* Do not over-expand. This file should remain readable and compact.
* Mark uncertain points as open questions.
* If the transcript contradicts previous state, explicitly note the change.

---

## 3. Updated `glossary.md`

Produce the full updated content for:

```text
llm/context/glossary.md
```

Use this structure:

```markdown
# Glossary

## <Term 1>

<Definition.>

## <Term 2>

<Definition.>

## <Term 3>

<Definition.>
```

Rules for glossary:

* Add only terms that are important for future understanding of the project.
* Preserve existing terms unless they are clearly obsolete.
* Prefer short, precise definitions.
* If a term is still tentative, mark it as “tentative”.
* Include project-specific terms, architecture terms, database terms, workflow terms, and tool names when they are important.
* Do not add generic programming terms unless the project uses them in a specific way.

---

# Quality rules

Before finalizing, check:

1. Are decisions separated from ideas?
2. Are open questions clearly marked?
3. Are action items concrete?
4. Is the language concise enough for future LLM context loading?
5. Are repository paths written consistently?
6. Are sensitive personal details removed or anonymized?
7. Is the output usable as markdown files without extra editing?

---

# Discussion transcript

Paste the discussion transcript below:

```text
<PASTE DISCUSSION HERE>
```
