---
name: study
description: "Turn STEP 1–3 concept notes into a saved study guide markdown file, then confirm the path (steps 4–6 only)."
---

## Trigger contract

Activate when the user message matches:
- `/study <input-block>`
- `/skill study: <input-block>`

Where `<input-block>` is a single pasted text block containing:
- `SOURCE_TITLE: <title>`
- a STEP 1 extract list
- STEP 2 backbone
- STEP 3 mapping

Disambiguation:
- If `SOURCE_TITLE:` is missing → Failure modes.
- If the block does not contain STEP 1–3 markers → Failure modes.

## Deterministic agent workflow

### Step 1 — Parse input
1) Extract `SOURCE_TITLE` as the text after `SOURCE_TITLE:` on that line.
2) Confirm the input contains these headings (string match):
   - `STEP 1` (or `## STEP 1`)
   - `STEP 2` (or `## STEP 2`)
   - `STEP 3` (or `## STEP 3`)

If any required element is missing → stop with the exact error in Failure modes.

### Step 2 — Generate study guide (STEP 4)
Produce a Markdown study guide with:

- `# <SOURCE_TITLE> — Study Guide`
- `## STEP 4 — WRITE STUDY GUIDE`

For each concept mentioned in the STEP 1 list, create a section using this exact template:

```md
### <n>. <CONCEPT NAME>

**Concept Note**
- 3–6 bullets derived only from the provided STEP 1–3 text.

**Evidence (verbatim)**
- 1–3 short verbatim quotes copied from the provided input block.

**Backbone Link**
- One sentence linking this concept to a backbone concept explicitly named in STEP 2/3.
```

Hard rules:
- If you cannot provide at least **one verbatim quote** for a concept, skip that concept.
- Do not introduce new concepts not present in the input.

At the end of STEP 4, include a section:
- `## Skipped concepts`
  - List skipped concept names (or `None`).

### Step 3 — Save study guide (STEP 5)
Compute filename:
- slugify SOURCE_TITLE: lowercase, spaces/underscores → hyphens, remove non `[a-z0-9-]`, collapse repeated hyphens.
- path: `/Users/igorsilva/clawd/learn/<slug>-study-guide.md`

Then save using `write` to that path (create parent dirs if needed).

### Step 4 — Confirm (STEP 6)
Output exactly:
- `Saved: <full-path>`
- If any skipped concepts: `Skipped concepts due to insufficient support in source: <comma-separated list>`
- `Next: /ingest <full-path>`

## Boundary rules

- No web access.
- Write only to `/Users/igorsilva/clawd/learn/`.
- Do not overwrite unrelated files; only the computed `<slug>-study-guide.md` path.
- Do not claim you quoted evidence unless it is copied verbatim from the input block.

## Use

Use this skill to convert the earlier extraction/mapping output (STEP 1–3) into a quotable study guide and save it locally for later ingestion.

## Inputs

A single text block containing:
- `SOURCE_TITLE: ...`
- STEP 1 extract content
- STEP 2 backbone content
- STEP 3 mapping content

## Outputs

1) A saved Markdown file at:
- `/Users/igorsilva/clawd/learn/<slug>-study-guide.md`

2) A confirmation message in chat:
- `Saved: ...`
- optional skipped list
- `Next: /ingest ...`

## Failure modes

- Missing SOURCE_TITLE:
  - `ERROR: missing SOURCE_TITLE. Add a line: SOURCE_TITLE: <title>`

- Missing STEP 1–3 markers:
  - `ERROR: input must include STEP 1, STEP 2, and STEP 3 sections.`

## Toolset

- `write`

## Acceptance tests

1. **Happy path: saves into learn/**
   - Run: `/study <block with SOURCE_TITLE + STEP1–3>`
   - Expected output: writes exactly one file under `/Users/igorsilva/clawd/learn/` and prints `Saved: /Users/igorsilva/clawd/learn/<slug>-study-guide.md`.

2. **Evidence requirement enforced**
   - Run: `/study <block where one concept has no supporting quotes>`
   - Expected output: concept appears under `## Skipped concepts` and is listed in `Skipped concepts due to insufficient support in source: ...`.

3. **Missing SOURCE_TITLE**
   - Run: `/study <block without SOURCE_TITLE>`
   - Expected error message (exact): `ERROR: missing SOURCE_TITLE. Add a line: SOURCE_TITLE: <title>`

4. **Missing STEP sections**
   - Run: `/study SOURCE_TITLE: X (no STEP headings)`
   - Expected error message (exact): `ERROR: input must include STEP 1, STEP 2, and STEP 3 sections.`

5. **Sensitive boundary: write location**
   - Run: `/study <any valid block>`
   - Expected: output file path always starts with `/Users/igorsilva/clawd/learn/` (never elsewhere).

6. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/study/SKILL.md
```
Expected: `PASS`.

7. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/study/SKILL.md
```
Expected: `PASS`.
