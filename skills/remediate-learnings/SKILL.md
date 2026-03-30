---
name: remediate-learnings
description: "Trigger: /remediate-learnings --pattern <pattern-key>. Read recurring ERROR entries for a pattern, diagnose root cause, generate a patch proposal (no apply), save proposal JSON under ~/.learnings/PROPOSALS/, and notify Igor on WhatsApp."
---

# remediate-learnings

## Use

Turn recurring error patterns (logged in `.learnings/ERRORS.md`) into a concrete patch **proposal** (JSON) that Igor can approve, without applying any code changes.

## Trigger contract

Trigger when the user sends:
- `/remediate-learnings --pattern <pattern-key>`

Where:
- `<pattern-key>` is a non-empty string identifying the recurring failure pattern.

## Goal

Close the self-improvement loop by turning recurring logged errors into **concrete, reviewable patch proposals** without applying changes.

## Safety rules (hard)

- **Never apply patches**. This skill only writes proposals.
- Only propose changes to files under:
  - `/Users/igorsilva/clawd/skills/`
  - `/Users/igorsilva/clawd/tools/`
- Never touch (read/write/patch):
  - `/Users/igorsilva/clawd/config/`
  - `/Users/igorsilva/clawd/gateway/`
  - `openclaw.json` (any path)
  - secrets/key material
- Max **3 target files** per proposal.
- Only write under:
  - `/Users/igorsilva/clawd/.learnings/PROPOSALS/`
- If constraints cannot be met, refuse with one-line `ERROR:`.

## Inputs

One line command with flags:

Required:
- `--pattern <pattern-key>`

## Outputs

Plain text.

### Output A — Success
REMEDIATION_PROPOSAL_CREATED
PATTERN: <pattern-key>
REQUEST_ID: <pattern-key>-<timestamp>
PATH: <absolute path to proposal json>

### Output A2 — No-op (already resolved)
PATTERN_ALREADY_RESOLVED: <pattern-key> — no action needed

### Output B — Failure
Return exactly one line starting with `ERROR:`.

## Deterministic workflow (must follow)

### Tooling
- `read` (read error log + affected files)
- `write` (create proposal file)
- `sessions_send` (notify Igor on WhatsApp)

### Step 1 — Parse and validate input
1) Parse `--pattern`.
2) If missing/empty → fail:
   - `ERROR: invalid_input. Usage: /remediate-learnings --pattern <pattern-key>`

### Step 2 — Load error entries for pattern
1) Read: `/Users/igorsilva/clawd/.learnings/ERRORS.md`.
2) Extract every entry block whose header matches:
   - `## [ERR-*-*] error`
3) Filter to entries where the `- Pattern-Key:` line equals the requested `<pattern-key>`.
4) If none found → fail:
   - `ERROR: pattern_not_found. No ERRORS.md entries for Pattern-Key: <pattern-key>`

### Step 3 — Resolved check + unresolved subset
After extracting matched entries, check their status:
1) For each matched entry, read its `**Status**:` field (if missing, treat as `pending`).
2) If **all** matched entries are `resolved`:
   - Output exactly: `PATTERN_ALREADY_RESOLVED: <pattern-key> — no action needed`
   - Exit (do not create proposal; do not notify).
3) If some are `resolved` and some are `pending`:
   - Continue, but only use the **unresolved (pending)** entries for diagnosis and patch generation.
   - Record both sets in the proposal:
     - `source.matchedEntryIds` must include only unresolved entries
     - Add `source.alreadyResolvedEntryIds` listing resolved ones
     - Set `source.matchedCount` to the number of unresolved entries

### Step 4 — Extract file list (from unresolved entries only)
1) For each unresolved entry, parse the `Files:` line.
2) Build a de-duplicated list of file paths.
3) Discard any path not under `/Users/igorsilva/clawd/skills/` or `/Users/igorsilva/clawd/tools/`.
4) If no allowed files remain → fail:
   - `ERROR: no_allowed_files. Refusing because no affected files are within allowed directories.`
5) Keep at most 3 files (deterministic):
   - Sort paths lexicographically; take first 3.

### Step 5 — Read affected files
For each selected file:
- `read` the full file.

### Step 6 — Diagnose root cause
Produce a **specific** diagnosis:
- `rootCause.file`: exact file path
- `rootCause.locationHint`: function name + nearby snippet description (no giant paste)
- `rootCause.mechanism`: the concrete logic causing recurrence

If the root cause cannot be identified from the allowed files → fail:
- `ERROR: insufficient_evidence. Unable to identify root cause from allowed files.`

### Step 7 — GENERATE VARIANTS
Use the LLM to generate 3 different fix approaches for the root cause:

Prompt to LLM:
```
Generate 3 different approaches to fix this error:
- Error pattern: {error_pattern}
- Root cause: {root_cause}
- Affected code: {code_snippet}

For each variant provide:
- Approach name (one line)
- Exact code change (before/after)
- Why this approach works
- Risks/downsides
```

Receive 3 variants from LLM.

### Step 7b — SCORE VARIANTS
Score each variant using static analysis:

| Metric | Weight | How to measure |
|--------|--------|-----------------|
| Success rate | 40% | Does it address the root cause? (manual check) |
| Simplicity | 30% | Lines changed, dependencies added |
| Blast radius | 20% | Functions/files affected |
| Reversibility | 10% | Can it be easily reverted? |

Final score = 0.4×success + 0.3×simplicity + 0.2×blast + 0.1×reversibility

### Step 7c — PRESENT FOR APPROVAL
Show variants as a table:

| # | Approach | Lines Δ | Risk | Score |
|---|----------|---------|------|-------|
| 1 | Add null check | +2 | Low | 0.85 |
| 2 | Use default dict | +5 | Low | 0.78 |
| 3 | Wrap in try/except | +8 | Medium | 0.65 |

Then show actual code for top-ranked variant.

Human picks by number (e.g., "I pick variant 2"). Default to variant 1 if no response in 5 minutes.

### Step 7d — WRITE CHOSEN VARIANT
Write the human-chosen variant to the proposal as the main patch (same format as before).

### Step 8 — Persist proposal JSON
1) Ensure directory exists:
   - `/Users/igorsilva/clawd/.learnings/PROPOSALS/`
2) Compute timestamp in `YYYYMMDD-HHMMSS` from environment context.
3) Set `requestId = <pattern-key>-<timestamp>`.
4) Write proposal JSON to:
   - `/Users/igorsilva/clawd/.learnings/PROPOSALS/<requestId>.json`

Proposal schema (must match):
```json
{
  "schema": "clawd.remediation.proposal.v1",
  "requestId": "<pattern-key>-<timestamp>",
  "status": "pending",
  "patternKey": "<pattern-key>",
  "createdAt": "<ISO-8601>",
  "source": {
    "errorsLogPath": "/Users/igorsilva/clawd/.learnings/ERRORS.md",
    "matchedEntryIds": ["ERR-YYYYMMDD-XXX"],
    "alreadyResolvedEntryIds": ["ERR-YYYYMMDD-YYY"],
    "matchedCount": 1
  },
  "constraints": {
    "allowedRoots": [
      "/Users/igorsilva/clawd/skills/",
      "/Users/igorsilva/clawd/tools/"
    ],
    "maxFiles": 3,
    "neverTouch": [
      "/Users/igorsilva/clawd/config/",
      "/Users/igorsilva/clawd/gateway/",
      "openclaw.json"
    ]
  },
  "diagnosis": {
    "summary": "<one paragraph>",
    "rootCause": {
      "file": "<absolute path>",
      "locationHint": "<string>",
      "mechanism": "<string>"
    }
  },
  "patch": {
    "files": [
      {
        "path": "<absolute path>",
        "edits": [
          {
            "oldText": "<exact old text>",
            "newText": "<exact new text>",
            "rationale": "<string>"
          }
        ]
      }
    ]
  }
}
```

### Step 9 — Notify Igor on WhatsApp
Send a WhatsApp message to Igor via `sessions_send` (same account) containing:
- pattern key
- diagnosis summary (2–5 lines)
- files affected
- requestId
- next step: “approve by editing proposal status to approved, then run /apply-patch --proposal <requestId>”

## Failure modes

Return exactly one line:
- `ERROR: invalid_input. Usage: /remediate-learnings --pattern <pattern-key>`
- `ERROR: pattern_not_found. No ERRORS.md entries for Pattern-Key: <pattern-key>`
- `ERROR: no_allowed_files. Refusing because no affected files are within allowed directories.`
- `ERROR: insufficient_evidence. Unable to identify root cause from allowed files.`

## Toolset

- `read`
- `write`
- `sessions_send`

## Acceptance tests

1. **Behavioral (negative): missing pattern**
   - Run: `/remediate-learnings`
   - Expected (exact): `ERROR: invalid_input. Usage: /remediate-learnings --pattern <pattern-key>`

2. **Behavioral (negative): unknown pattern**
   - Precondition: ERRORS.md does not contain Pattern-Key: DOES_NOT_EXIST
   - Run: `/remediate-learnings --pattern DOES_NOT_EXIST`
   - Expected (exact): `ERROR: pattern_not_found. No ERRORS.md entries for Pattern-Key: DOES_NOT_EXIST`

3. **Behavioral: creates proposal file**
   - Precondition: ERRORS.md contains at least 1 entry with Pattern-Key: P and Files pointing to an allowed file
   - Run: `/remediate-learnings --pattern P`
   - Expected:
     - Output starts with `REMEDIATION_PROPOSAL_CREATED`
     - `PATTERN: P`
     - Written JSON contains `"status": "pending"`
     - Written JSON contains `"patternKey": "P"`

4. **Behavioral: refuses when only disallowed files referenced**
   - Precondition: ERRORS.md contains Pattern-Key: Q but only files outside allowed roots
   - Run: `/remediate-learnings --pattern Q`
   - Expected (exact): `ERROR: no_allowed_files. Refusing because no affected files are within allowed directories.`

5. **Behavioral: no-op when all entries resolved**
   - Precondition: all entries for Pattern-Key: R have `**Status**: resolved`
   - Run: `/remediate-learnings --pattern R`
   - Expected (exact): `PATTERN_ALREADY_RESOLVED: R — no action needed`

6. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/remediate-learnings/SKILL.md
```
Expected: `PASS`.

7. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/remediate-learnings/SKILL.md
```
Expected: `PASS`.

8. **Behavioral: proposal file path location**
   - Run: `/remediate-learnings --pattern P`
   - Expected: `PATH:` starts with `/Users/igorsilva/clawd/.learnings/PROPOSALS/`

9. **Behavioral: notify Igor**
   - Run: `/remediate-learnings --pattern P`
   - Expected: sends a WhatsApp message via `sessions_send` containing `REQUEST_ID:`
