---
name: extract-concept
description: "Trigger: /extract-concept: <file-path | pasted text>. Extract 1–3 high-signal, reusable concepts (3–8 words each) with no analysis or explanation."
---

## extract-concept

### Responsibility (single-purpose)
Extract **1–3** key concepts from either a **file path** or **pasted text**.

### Inputs
- **Either** a file path (string that looks like a path) **or** pasted text.

### Output (hard rules)
- Return **1–3 bullets only**.
- Each bullet is a **short phrase (3–8 words)**.
- **No explanations. No sentences.**
- **No formatting except**:
  - `- Concept`

### Steps (single-pass)
1) Determine input type:
   - If it looks like a readable file path → read it with the built-in `read` capability and use the file contents as the text.
   - Else treat the input as pasted text.
2) If the text is too short/unclear to extract from → output exactly:
   - `provide more content to extract concepts`
3) Select **1–3** concepts that are:
   - high-signal and reusable (general, portable)
   - not examples/details
   - not duplicates or near-duplicates
4) Output only the bullet list.

### Failure condition
- If a file path was provided but the file cannot be read → output exactly:
  - `ERROR: Unable to read file. Please check path.`

## Guardrails (anti-crash)
- No analysis, no lenses, no interpretation.
- No storage, ingestion, or memory writes.
- No bash, no python, no external tools.
- No multi-step pipeline; single-turn only.

## Acceptance criteria (must-pass)
- Output is **only** 1–3 bullet points.
- Each bullet is **3–8 words** and a **concept phrase**, not a sentence.
- On unreadable file: exact error string.
- On too-short/unclear input: exact prompt string.

## Tests
1) Input: `/extract-concept: /path/that/does/not/exist.txt`
   - Output: `ERROR: Unable to read file. Please check path.`
2) Input: `/extract-concept: hello`
   - Output: `provide more content to extract concepts`
3) Input: `/extract-concept: <a 2–3 paragraph article pasted>`
   - Output: 1–3 bullets; no other text.

## Agent Loop Contract (agentic skills only)
- Single-turn: read (optional) → extract → output.
- No retries, no background work, no external calls.

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
   - Run: `/extract-concept <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/extract-concept <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/extract-concept/SKILL.md
```
Expected: `PASS`.
