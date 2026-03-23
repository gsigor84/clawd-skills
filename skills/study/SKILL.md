---
name: study
description: "Trigger: /skill study: <input-text>. Takes STEP 1–3 (extract + backbone + mapping) and produces ONLY STEP 4 — WRITE STUDY GUIDE, STEP 5 — SAVE, STEP 6 — CONFIRM. Saves to ~/clawd/learn/<source-title>-study-guide.md."
---

## study — STEP 4–6 only

### Input format (required)
Paste a single block that contains:
- `SOURCE_TITLE: <short-title>` (used for the filename)
- `## STEP 1 — EXTRACT` list
- `## STEP 2 — IDENTIFY BACKBONE`
- `## STEP 3 — MAP RELATIONSHIPS`

If `SOURCE_TITLE:` is missing, ask the user for exactly one title string and stop.

### Hard rules
- Perform **ONLY**:
  - `STEP 4 — WRITE STUDY GUIDE`
  - `STEP 5 — SAVE`
  - `STEP 6 — CONFIRM`
- **Context-only**: use only the provided input text (STEP 1–3). Do not add new concepts.
- Prefer partial completion over guessing:
  - Skip concepts that cannot be supported by the provided text.
  - Report skipped concepts in STEP 6.

### STEP 4 format
For each concept that is supportable from the provided text, output:

```md
### [Number]. [Concept Name]
**Concept Note**
3–6 bullets, supported by the provided text.

**Evidence (verbatim)**
1–3 short quotes (verbatim) from the provided text that support the Concept Note.

**Backbone Link**
One sentence linking the concept to its assigned backbone from STEP 3.
```

If you cannot provide at least 1 verbatim quote for a concept, **skip** it.

### STEP 5 — SAVE
- Ensure directory:
  ```bash
  mkdir -p /Users/igorsilva/clawd/learn
  ```
- Lowercase + hyphenate `SOURCE_TITLE`.
- Save full study guide to:
  `/Users/igorsilva/clawd/learn/<source-title-lowercase-hyphenated>-study-guide.md`

### STEP 6 — CONFIRM
- Print the exact saved file path.
- If any concepts were skipped, include:
  `Skipped concepts due to insufficient support in source: ...`
- Then print:
  `Run /ingest <path> to load this into your knowledge base.`

## Use

Describe what the skill does and when to use it.

## Inputs

- Describe required inputs.

## Outputs

- Describe outputs and formats.

## Failure modes

- List hard blockers and expected exact error strings when applicable.

## Toolset

- `read`
- `write`
- `edit`
- `exec`

## Acceptance tests

1. **Behavioral: happy path**
   - Run: `/study <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/study <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/study/SKILL.md
```
Expected: `PASS`.
