---
name: ingestion-engine
description: "Trigger: /ingest. Ingest a *-study-guide.md produced by /learn (current STEP 1–8 format) and write a local retrieval library under ~/clawd/learn/json/ (one JSON file per concept). LLM-only: no bash, no python, no external execution."
---

# Ingestion Engine (/ingest) — LLM-only

## Contract (do not drift)
- **Input:** a single Markdown file path, typically named `*-study-guide.md`.
- **Output:** local JSON files for retrieval in `~/clawd/learn/json/`.
- **No external execution:** do not call bash, python, or any scripts.
- **No KB push:** do not call Open Notebook or any external KB API.

## If user provides no path
Reply with exactly:

send the path to the *-study-guide.md file produced by /learn

## Parsing model (current learn format)
- Only parse the section:
  - `## STEP 4 — WRITE STUDY GUIDE`
- Ignore everything else (STEP 1–3, STEP 5–8).

### Concept structure (strict)
Inside STEP 4, each concept block must match:
- `### <number>. <Concept Name>`
- `**Concept Note**` (text)
- `**Evidence (verbatim)**` (text)
- `**Backbone Link**` (text)

If any of the three fields are missing, skip the concept (best-effort default).

## Output layout (fixed)
- Base: `~/clawd/learn/json/`
- Per-run folder: `~/clawd/learn/json/<source-title>/`
  - `index.json`
  - `001-<concept-slug>.json`, `002-...json`, etc.

## Implementation (LLM-only; mandatory)

### STEP 1 — READ FILE
- Use the built-in file read capability to load the markdown file.
- If file cannot be read: output exactly:
  - `ERROR: Unable to read file. Please check path.`

### STEP 2 — EXTRACT STEP 4
- Locate the heading line exactly:
  - `## STEP 4 — WRITE STUDY GUIDE`
- Extract all text until the next heading that starts with:
  - `## STEP `
- If STEP 4 is missing: best-effort mode should output a debug summary with `total concepts found: 0` and a skip reason noting STEP 4 missing.

### STEP 3 — PARSE CONCEPTS
- Each `### <number>. <Concept Name>` inside STEP 4 starts a concept.
- For each concept, extract:
  - `concept_name`
  - `concept_note` (raw text under **Concept Note**)
  - `evidence` (raw text under **Evidence (verbatim)**)
  - `backbone_link` (raw text under **Backbone Link**)
- If any are missing: skip the concept and record the reason.

### STEP 4 — CREATE OUTPUT STRUCTURE
- Compute `source-title` from the input filename stem:
  - e.g., `/path/chapter-10-foo-study-guide.md` → `chapter-10-foo`
- Slugify:
  - lowercase
  - non-alphanumerics → `-`
  - collapse multiple `-`
- Create output dir:
  - `~/clawd/learn/json/<source-title>/`

### STEP 5 — WRITE FILES (filesystem write tool only)
- Write `index.json` including:
  - `concepts_total`
  - `ingested_count`
  - `skipped_count`
  - `ingested` list (index, concept, file)
  - `skipped` list (index, concept, problems)
  - `md_path`, `source_title`, `source_slug`, `generated_at_utc`
- Write numbered concept JSON files:
  - schema: `clawd.learn.concept.v2`
  - fields: `concept`, `index`, `concept_note`, `evidence`, `backbone_link`, `source`, `retrieval.tags`

### STEP 6 — DEBUG OUTPUT (MANDATORY)
After writing, ALWAYS print:
- `out_dir: <path>`
- `total concepts found: <n>`
- `successfully ingested: <n>`
- `skipped: <n>`
- If skipped > 0:
  - `skip reasons:`
  - `- 001 Concept Name: reason1, reason2`

## Strict mode (optional)
- If the user includes `--strict` in the command, hard-fail on the first concept parsing error.

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
   - Run: `/ingestion-engine <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/ingestion-engine <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/ingestion-engine/SKILL.md
```
Expected: `PASS`.
