---
name: extract
description: "Trigger: /skill extract: <pasted-text>. Extract a raw, ungrouped list of named concepts/frameworks/principles/mental models from pasted source text. Performs ONLY STEP 1 — EXTRACT. No file access. No shell commands."
---

## extract — STEP 1 only (chat text only)

### Trigger
- Run as:
  - `/skill extract: <PASTE SOURCE TEXT HERE>`

### Hard rules
- Perform **ONLY**: `STEP 1 — EXTRACT`.
- **No file paths**. Treat the user’s pasted content as the full source.
- **No shell commands, no Python, no subprocess/tool execution.**
- **Context-only**: output only items explicitly present in the pasted text.
- **No grouping, no analysis, no backbone, no mapping.**

### Safety check
- If the provided text is empty or not meaningful (e.g., just a filename/path, a couple words, or whitespace), output exactly:
  - `ERROR: Please paste source text`

### Output format (must match exactly)
Output exactly one section:

```md
## STEP 1 — EXTRACT
- <item 1>
- <item 2>
...
```

### Extraction requirements
- Extract **every named**:
  - concept
  - framework
  - principle
  - mental model
- One bullet per item.
- Do not add items that are not present in the pasted text.
- Do not expand abbreviations unless the expansion appears in the pasted text.
- Only merge obvious duplicates (case/punctuation variants).

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
   - Run: `/extract <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/extract <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/extract/SKILL.md
```
Expected: `PASS`.
