---
name: save-concepts
description: "Trigger: /save-concepts <topic-slug> + one JSON array (pasted) OR /save-concepts <topic-slug> --file <absolute-path-to-json-file>. Validate clawd.learn.concept.v1 objects and write one file per concept to ~/clawd/learn/json/<topic-slug>/, updating index.json while preserving existing schema version (v1/v2)."
---

## save-concepts

### Responsibility (single-purpose)
Validate a pasted JSON array of `clawd.learn.concept.v1` concept objects and write them to disk under:
- `~/clawd/learn/json/<topic-slug>/`

Also write/update `index.json` in that folder, **preserving** existing `index.json` schema version if present.

### Trigger
- `/save-concepts <topic-slug>`
- `/save-concepts <topic-slug> --file <absolute-path-to-json-file>`

### Input (required)
Provide concept JSON in one of two ways:
1) Preferred: exactly **one** fenced code block whose opening line is ```json or ```JSON and whose content is a JSON array (`[...]`).
2) Fallback: a raw JSON array substring that starts with `[` and ends with `]` somewhere in the message body (used only when no fenced json block is present).

### Hard constraints
- Never touch `MEMORY.md`.
- Never touch any file outside `~/clawd/learn/json/<sanitized-slug>/`.
- Prefer ```json / ```JSON fences; if none found, accept a raw JSON array substring. (Not plain ```.)
- Hard-fail on invalid JSON parse: write nothing.
- Best-effort per-object after valid parse.
- Preserve existing `index.json` schema version (v1 or v2); new folders default to v1.

---

## Steps

### STEP 1 — PARSE AND SANITIZE SLUG
Sanitize topic slug in this sequence:
1) lowercase
2) replace spaces and underscores with hyphens
3) strip all characters not in `[a-z0-9-]`
4) collapse multiple hyphens into one
5) strip leading/trailing hyphens
6) if result is empty → output exactly:
❌ Invalid topic name. Could not derive a valid slug from: <input>
💡 Use a simple name like: /save-concepts agentic-ai-architecture --file ...
Then stop.

Use sanitized slug silently for all operations; only show it as first line of final report: `Topic: <sanitized-slug>`. 

### STEP 2 — FIND JSON INPUT (FILE MODE OR PASTED MODE)

If the message contains `--file <path>`:
- Treat this as **file mode**.
- Read the file at `<path>` and use the entire file content as the JSON input.
- If the file cannot be read (missing/unreadable) → output exactly:
❌ File not found: <path>
💡 Did you forget --save when running /auto-extract? 
Run: /auto-extract <your-file.txt> --save
Then check ~/clawd/tmp/ for the saved file.
Available files in ~/clawd/tmp/: <list files in ~/clawd/tmp/>
(Implementation note: generate the list by running `ls -1 ~/clawd/tmp` via exec; if the folder is missing/empty, show an empty list.)
Then stop.
- Additionally (file mode sanity check): derive a **suggested slug** by sanitizing the `--file` filename stem.
  - If the suggested slug differs from the sanitized slug from STEP 1, print (before writing anything):
📂 Topic folder will be: ~/clawd/learn/json/<sanitized-slug>/
✋ Is this correct? If not, re-run with the right slug.
  - Then proceed automatically (do not wait).

Otherwise, treat this as **pasted mode**.

Pasted mode (fenced preferred):
- Accept opening fences: ```json or ```JSON (case-insensitive), optional trailing whitespace.
- Count matching fenced blocks in the message body.
  - If more than one → output exactly:
❌ Found <N> JSON blocks. Paste exactly one array.
💡 Remove the extra blocks and re-run.
and stop.
  - If exactly one → extract its content and use it.

Raw fallback (only if **no** fenced json block was found):
- Search the message body for a raw JSON array that starts with `[` and ends with `]`.
- If a raw array is found, extract that substring and use it.

If neither a fenced json block nor a raw array is found:
- Output exactly:
❌ No JSON found. You need to either:
A) Paste a JSON array directly in this message, or
B) Use: /save-concepts <slug> --file ~/clawd/tmp/<slug>.json
💡 Tip: always use --save with /auto-extract to avoid pasting:
/auto-extract <your-file.txt> --save
Then stop.

### STEP 3 — PARSE JSON (HARD FAIL)
- Parse extracted content as JSON.
- If parse fails in **file mode** → output exactly:
❌ Could not parse JSON from: <path>
💡 The file may be corrupted or incomplete. Re-run:
/auto-extract <your-file.txt> --save
Then stop (write nothing).
- If parse fails in pasted mode → output exactly:
❌ Could not parse JSON.
💡 Re-run /auto-extract — the output should be a [...] array.
Then stop (write nothing).
- If valid but not an array → output exactly:
❌ Expected a JSON array [...] but got <type>.
💡 Re-run /auto-extract — the output should be a [...] array.
Then stop.

### STEP 4 — VALIDATE EACH OBJECT (BEST-EFFORT)
After valid parse, validate each object individually.
Required fields:
- `schema`, `concept`, `index`, `challenge_question`, `answer_p1`, `source`
Rules:
- `schema` must equal exactly `clawd.learn.concept.v1`
- invalid objects are skipped with a reason (e.g., `missing field: answer_p1`, `wrong schema value`)

If **all** objects are invalid (0 validated concepts): output exactly:
❌ Saved 0 concepts — all objects failed validation.
💡 Check that each object has schema: "clawd.learn.concept.v1" and required fields:
concept, index, challenge_question, answer_p1, source.
💡 Re-run /auto-extract to generate a fresh valid array.
Then stop (write nothing).

### STEP 5 — DERIVE FILENAMES
Pattern:
- `<index 3-digit padded>-<kebab-concept-name>.json`

Kebab:
1) lowercase
2) spaces → hyphens
3) strip all characters not in `[a-z0-9-]`
4) collapse multiple hyphens
5) strip leading/trailing hyphens

Collision rule:
- If two concepts produce same filename, append `-b`, `-c`, ... to later ones.

### STEP 6 — PREPARE FOLDER
- Ensure directory exists: `/Users/igorsilva/clawd/learn/json/<sanitized-slug>/`
- Never wipe existing files.

### STEP 7 — LOAD EXISTING INDEX AND HANDLE RENAMES
If `/Users/igorsilva/clawd/learn/json/<sanitized-slug>/index.json` exists:
- Load it and read `schema` to detect index version (`clawd.learn.study-guide-index.v1` or `.v2`).
- For each incoming **validated** concept:
  - If its `index` exists in `ingested[]` and the prior `file` differs from the newly derived filename:
    - Delete the old file **only if**:
      a) it is inside `/Users/igorsilva/clawd/learn/json/<sanitized-slug>/`
      b) filename matches regex: `^[0-9]{3}-[a-z0-9-]+\.json$`
    - Record deletion as `old-filename → replaced by new-filename`
    - If delete fails: record it in skipped list (do not crash)

If index.json does not exist:
- Treat as new folder; index version will be v1.

### STEP 8 — WRITE CONCEPT FILES
For each validated concept:
- Write one JSON file to `/Users/igorsilva/clawd/learn/json/<sanitized-slug>/<derived-filename>.json`
- Overwrite if same filename exists.
- If write fails: skip + record reason.

### STEP 9 — WRITE OR UPDATE index.json (PRESERVE VERSION)
Version rule:
- If index.json existed → preserve its schema version (v1 or v2)
- Else → write fresh v1

**V1 structure** (`clawd.learn.study-guide-index.v1`):
- top-level fields: `schema, source, backbone, concepts_total, ingested_count, skipped_count, ingested, skipped`
- `backbone`: always `[]`
- `ingested` entries include: `{ index, concept, file, backbone: null }`

**V2 structure** (`clawd.learn.study-guide-index.v2`):
- top-level fields: `schema, source, concepts_total, ingested_count, skipped_count, ingested, skipped`
- `ingested` entries include: `{ index, concept, file }`

For both versions:
- `source.type`: `auto-ingest-txt`
- `source.md_path`: from `source.md_path` of the first valid concept (or empty string if missing)
- `source.source_title`: `<sanitized-slug>`
- `source.source_slug`: `<sanitized-slug>`
- `source.generated_at_utc`: UTC now

Merge rules (if index existed):
- Merge `ingested[]` by `index` (overwrite matching, append new)
- Merge `skipped[]` by `index` (overwrite matching, append new)
- Recalculate counts from merged arrays
- Sort `ingested[]` and `skipped[]` ascending by index

### STEP 10 — REPORT (STRICT)
Output exactly:

Topic: <sanitized-slug>
✅ Saved <N> concepts to ~/clawd/learn/json/<sanitized-slug>/

If skipped count > 0:
⚠️ Skipped <N> concepts:
 - index <N>: <reason>

If renames occurred:
🗑️ Deleted (renamed):
 - <old-filename> → replaced by <new-filename>

📄 Files written:
 <file1>
 <file2>
 ...

📋 index.json updated (schema: <version used>).

## Acceptance criteria (must-pass)
1) With invalid JSON parse, **writes nothing** and returns the specified helpful error.
2) With valid array, writes only to `~/clawd/learn/json/<slug>/`.
3) Preserves existing index schema version if index.json exists.
4) Supports either pasted JSON (one fenced block / raw fallback) **or** `--file <absolute-path-to-json-file>`.
5) If 0 validated concepts, writes nothing and returns the specified validation failure message.

## Tests
1) `/save-concepts bad$$$ --file /tmp/x.json` →
❌ Invalid topic name. Could not derive a valid slug from: bad$$$
💡 Use a simple name like: /save-concepts agentic-ai-architecture --file ...

2) `/save-concepts topic --file /path/missing.json` → includes:
❌ File not found: /path/missing.json
… and lists available files in ~/clawd/tmp/

3) `/save-concepts topic --file /path/bad.json` (not valid JSON) →
❌ Could not parse JSON from: /path/bad.json
💡 The file may be corrupted or incomplete. Re-run:
/auto-extract <your-file.txt> --save

4) `/save-concepts topic` with no JSON and no --file →
❌ No JSON found. You need to either:
A) Paste a JSON array directly in this message, or
B) Use: /save-concepts <slug> --file ~/clawd/tmp/<slug>.json

5) `/save-concepts topic` with two fenced json blocks →
❌ Found 2 JSON blocks. Paste exactly one array.
💡 Remove the extra blocks and re-run.

6) `/save-concepts topic` with valid JSON object (not array) →
❌ Expected a JSON array [...] but got object.
💡 Re-run /auto-extract — the output should be a [...] array.

7) `/save-concepts topic` with an array where all objects fail validation →
❌ Saved 0 concepts — all objects failed validation.
💡 Check that each object has schema: "clawd.learn.concept.v1" and required fields:
concept, index, challenge_question, answer_p1, source.

## Agent Loop Contract (agentic skills only)
- Single-turn: parse → validate → write → report.
- No background tasks.

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
   - Run: `/save-concepts <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/save-concepts <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/save-concepts/SKILL.md
```
Expected: `PASS`.
