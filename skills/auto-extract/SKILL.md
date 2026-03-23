---
name: auto-extract
description: "Trigger: /auto-extract <absolute-file-path> [--save]. Read a .txt file, extract up to 15 concepts, and output a single fenced JSON array (clawd.learn.concept.v1). Optional --save writes the same JSON array to ~/clawd/tmp/<topic-slug>.json."
---

## auto-extract

### Responsibility (single-purpose)
Read a local **.txt** file and output **up to 15** extracted concepts as a **single JSON array** inside **one** fenced ```json code block.

### Trigger
- `/auto-extract <absolute-file-path>`
- `/auto-extract <absolute-file-path> --save`

### Inputs
- `absolute-file-path` (must be an absolute path to a readable `.txt` file)
- Optional flag: `--save` (when present, also write the JSON array to `~/clawd/tmp/<topic-slug>.json`)

### Output (strict)
Output **exactly**:

Suggested slug: <topic-slug>
```json
[ { ... }, { ... } ]
```
Extracted <N> concepts. Review above then run /save-concepts <slug> and paste this block.

If `--save` was present, add exactly these two lines after the summary line:
💾 Saved to ~/clawd/tmp/<topic-slug>.json
👉 Next step: /save-concepts <slug> --file ~/clawd/tmp/<slug>.json

Rules:
- Exactly **one** fenced `json` block.
- No other fenced blocks.
- If `--save` is absent: nothing after the summary line.
- If `--save` is present: only the two lines:
  - `💾 Saved to ~/clawd/tmp/<topic-slug>.json`
  - `👉 Next step: /save-concepts <slug> --file ~/clawd/tmp/<slug>.json`
- If 0 concepts found: output exactly:
❌ No extractable concepts found in <path>
💡 The file may be too short, too generic, or mostly boilerplate. Try a different chapter or section.
Then stop.

---

## Steps

### STEP 1 — VALIDATE INPUT
1) Check the file exists at the given absolute path.
2) If not found or unreadable: output exactly:
❌ File not found: <path>
💡 Check the path is correct and the file exists. Use tab-completion or Finder to verify.
Then stop.
3) If the file extension is not `.txt`: output exactly:
❌ This skill only supports .txt files. Got: <extension>
💡 Convert your file to .txt first, then re-run.
Then stop.
4) If found and is a `.txt`: read full file content using the built-in `read` capability.

### STEP 2 — FILTER FLUFF (conservative)
Remove only sentences that match these **exact** boilerplate patterns (case-insensitive):
- Starts with: `In this chapter`
- Starts with: `In this section`
- Starts with: `We will`
- Starts with: `We begin`
- Starts with: `We now`
- Starts with: `Having established`
- Starts with: `Having laid`
- Starts with: `As mentioned`
- Starts with: `This chapter`
- Starts with: `This section`
- Starts with: `In the next`
- Starts with: `In previous chapters`
- Starts with: `In prior chapters`
- Pure section heading restatements (heading text repeated verbatim as a sentence)

CRITICAL:
- When in doubt — **KEEP** the sentence.
- Never delete anything not matching these exact patterns.

### STEP 3 — DETECT CONTENT SHAPE
For each section, identify shape and choose extraction unit:
- Paired/contrasting concepts (X vs Y / “X refers to… Y refers to…”) → **one JSON per pair** (name it like `X vs Y (distinction)`)
- Definition list (“X is defined as…”) → **one JSON per definition**
- Process/steps (numbered or sequential) → **one JSON per step** (group only if truly inseparable)
- Paradigm shift (from X to Y / reframing) → **one JSON per shift**
- Framework (named system with components) → **one JSON per component**
- Mixed → decide per section; use the most granular useful unit

Never ask the user which shape — decide and proceed.

A concept is worth extracting if it answers at least one of:
- What is X?
- How does X work?
- What is the difference between X and Y?
- What rule governs X?
- What are the steps of X?

If it only answers “what will we cover?” or “what did a previous chapter say?” → skip.

### STEP 4 — EXTRACT CONCEPTS (cap + grounding)
- Hard cap: **15** concepts maximum.
- If more than 15: pick the 15 most distinct/useful; avoid near-duplicates.

For each concept object:
- `concept`: short descriptive name
- `index`: 1-based integer, sequential across the output array
- `challenge_question`: a question a student could fail without reading the source; derived from source only
- `answer_p1`: direct core answer, no fluff; derived from source only
- `answer_p2`: a **genuine** connection to another **named concept in this same extracted set**, only if explicit in source; else `null`
- `backbone`: always `null`

Never invent content not present in the source.

### STEP 5 — DERIVE TOPIC SLUG (filename only)
From the filename only:
1) Strip extension
2) Strip leading patterns: `chapter_\d+_`, `ch_\d+_`, `part_\d+_`
3) Lowercase
4) Replace spaces and underscores with hyphens
5) Strip all characters not in `[a-z0-9-]`
6) Collapse multiple hyphens to one
7) Strip leading/trailing hyphens

### STEP 6 — FORMAT AS JSON (clawd.learn.concept.v1)
Each concept must match this schema exactly:
```json
{
  "schema": "clawd.learn.concept.v1",
  "concept": "<name>",
  "index": 1,
  "challenge_question": "<tests understanding>",
  "answer_p1": "<core answer, direct>",
  "answer_p2": "<genuine connection or null>",
  "backbone": null,
  "source": {
    "type": "auto-ingest-txt",
    "md_path": "<absolute path exactly as provided>",
    "source_title": "<topic-slug>",
    "generated_at_utc": "<UTC timestamp>"
  },
  "retrieval": {
    "keywords": [],
    "tags": ["auto-ingest", "concept"]
  }
}
```

## STEP 7 — OPTIONAL SAVE (--save)
If `--save` is present:
1) Attempt to write the exact JSON array you output to a file at: `~/clawd/tmp/<topic-slug>.json`.
2) If `~/clawd/tmp/` does not exist or is not writable (or the write fails): output exactly:
❌ Could not save to ~/clawd/tmp/<slug>.json — folder may not exist.
💡 Run: mkdir -p ~/clawd/tmp and try again.
Then stop.
3) If the write succeeds, the saved file must contain only the raw JSON array (pretty-printed ok).

## Guardrails
- If `--save` is absent: no filesystem writes.
- If `--save` is present: write only to `~/clawd/tmp/<topic-slug>.json` (or hard-fail with the specified save error message).
- No bash / python / external tools.
- Single-turn.

## Acceptance criteria (must-pass)
- Output includes exactly one fenced ```json block containing a JSON array.
- ≤15 concept objects.
- Every object includes `schema: clawd.learn.concept.v1` and required fields.
- `answer_p2` is `null` unless explicitly supported.
- With `--save`, a JSON file exists at `~/clawd/tmp/<topic-slug>.json` matching the output array.

## Tests
1) `/auto-extract /path/does/not/exist.txt` →
❌ File not found: /path/does/not/exist.txt
💡 Check the path is correct and the file exists. Use tab-completion or Finder to verify.

2) `/auto-extract /path/to/file.pdf` →
❌ This skill only supports .txt files. Got: .pdf
💡 Convert your file to .txt first, then re-run.

3) `/auto-extract /path/to/very-short.txt` (no real concepts) →
❌ No extractable concepts found in /path/to/very-short.txt
💡 The file may be too short, too generic, or mostly boilerplate. Try a different chapter or section.

4) `/auto-extract /path/to/file.txt --save` when tmp folder missing/unwritable →
❌ Could not save to ~/clawd/tmp/<slug>.json — folder may not exist.
💡 Run: mkdir -p ~/clawd/tmp and try again.

5) `/auto-extract /path/to/file.txt --save` success → output includes:
💾 Saved to ~/clawd/tmp/<slug>.json
👉 Next step: /save-concepts <slug> --file ~/clawd/tmp/<slug>.json

## Agent Loop Contract (agentic skills only)
- Single-turn: validate → read → filter → extract → output.
- No retries, no background work, no persistence.

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
   - Run: `/auto-extract <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/auto-extract <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/auto-extract/SKILL.md
```
Expected: `PASS`.
