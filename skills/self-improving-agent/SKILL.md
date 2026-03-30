---
name: self-improving-agent
description: "Trigger: /self-improving-agent <type> | <summary>. Append one structured entry to .learnings/{LEARNINGS,ERRORS,FEATURE_REQUESTS}.md with deterministic IDs and safe redaction."
---

# self-improving-agent

## Trigger contract

Trigger when the user (or an orchestrator) sends:
- `/self-improving-agent <type> | <summary> [| details: <optional>] [| goal: <optional>] [| files: <optional>] [| status: <optional>]`

Where:
- `<type>` is one of: `learning` | `error` | `feature`
- `<summary>` is a non-empty one-line description

This is a single-entry append action. No multi-entry batching.

## Use

Use this skill to log learnings, errors, and feature requests into a local, append-only `.learnings/` directory so later work can improve skills and workflows.

This skill is intentionally minimal and deterministic:
- it appends exactly one entry per invocation
- it redacts secrets
- it never edits or deletes existing entries

## Inputs

One plain-text line with fields separated by `|`:

Required:
- `type` — `learning` or `error` or `feature`
- `summary` — one line

Optional:
- `details:` — free text (may span multiple sentences)
- `goal:` — what you were trying to accomplish when this happened (optional, one line)
- `files:` — comma-separated paths (informational; not opened)
- `status:` — `pending` or `resolved` (optional; default: `pending`)

Examples:
- `/self-improving-agent learning | Validator failed because acceptance tests were placeholders | details: Rewrite tests with exact expected outputs | files: skills/tool-installer/SKILL.md`
- `/self-improving-agent error | notebooklm froze | details: page freeze after 8 min | goal: building creativity-toolkit-v3 with skill-forge`
- `/self-improving-agent feature | Add allowlist support to signal-extractor | details: optional ALLOWED_DOMAINS line in input`

## Outputs

Plain text.

### Output A — Success
SELF_IMPROVEMENT_LOGGED
TYPE: <learning|error|feature>
ID: <LRN-YYYYMMDD-XXX|ERR-YYYYMMDD-XXX|FEAT-YYYYMMDD-XXX>
PATH: <absolute path to the log file>

### Output B — Failure
Return exactly one line starting with `ERROR:` (see Failure modes).

## Deterministic workflow (must follow)

### Tooling
- `read` (to check existing logs for next ID)
- `write` (to create logs if missing)
- `edit` (to append)

### Global caps (hard limits)
- Max summary length: **180** characters
- Max details length: **2000** characters
- Max files list length: **500** characters
- Max total appended entry size: **3000** characters

### Boundary rules (privacy + safety)

- Only write under: `/Users/igorsilva/clawd/.learnings/`.
- Never read or write outside `.learnings/`.
- Never include secrets:
  - Redact substrings that look like tokens/keys/passwords.
  - If details include `X-Subscription-Token:` or `Authorization:` headers, replace header values with `[REDACTED]`.
- Never copy full session transcripts into logs.

### Step 1 — Parse and validate
1) Parse `type` and `summary` from the input.
2) If type not in {learning,error,feature} → fail.
3) If summary missing/whitespace → fail.
4) Truncate summary to 180 characters.
5) If details present, truncate to 2000 characters.

### Step 2 — Choose file + ID prefix
Map type → (file, prefix):
- learning → `/Users/igorsilva/clawd/.learnings/LEARNINGS.md`, `LRN`
- error → `/Users/igorsilva/clawd/.learnings/ERRORS.md`, `ERR`
- feature → `/Users/igorsilva/clawd/.learnings/FEATURE_REQUESTS.md`, `FEAT`

### Step 3 — Ensure .learnings exists
- If directory missing, create it by writing a placeholder header file (see Step 4) using `write` with parent directory creation.

### Step 4 — Ensure log file exists
If the target file does not exist, create it with `write`:
- First line must be: `# <FILE_NAME>` (e.g., `# LEARNINGS`)
- Followed by a blank line.

### Step 5 — Compute next ID (deterministic)
1) Determine today’s date in `YYYYMMDD` by reading from the environment context (no tool call).
2) Read the log file.
3) Find existing IDs with regex: `\[(PREFIX)-(YYYYMMDD)-(\d{3})\]`.
4) If none exist for today → XXX = 001.
5) Else XXX = max + 1.
6) Construct ID: `PREFIX-YYYYMMDD-XXX`.

### Step 6 — Redact
Apply redaction to details and files fields:
- Replace any occurrences of:
  - `X-Subscription-Token: <anything>` → `X-Subscription-Token: [REDACTED]`
  - `Authorization: <anything>` → `Authorization: [REDACTED]`
  - any substring containing `api key`, `token`, `password`, `secret` followed by `:` → replace value with `[REDACTED]`.

### Step 7 — Append entry
Append exactly this entry format to the end of the file:

For learning:
```
## [LRN-YYYYMMDD-XXX] learning

- Pattern-Key: <string>
- Recurrence-Count: <int>
- First-Seen: <YYYY-MM-DD>
- Last-Seen: <YYYY-MM-DD>
- User-Goal: <goal or "(none)">

Summary: <summary>
Details: <details or "(none)">
Files: <files or "(none)">
Status: <status or "pending">

---
```

For error:
```
## [ERR-YYYYMMDD-XXX] error

- Pattern-Key: <string>
- Recurrence-Count: <int>
- First-Seen: <YYYY-MM-DD>
- Last-Seen: <YYYY-MM-DD>
- User-Goal: <goal or "(none)">

Summary: <summary>
Details: <details or "(none)">
Files: <files or "(none)">
Status: <status or "pending">

---
```

For feature:
```
## [FEAT-YYYYMMDD-XXX] feature

- Pattern-Key: <string>
- Recurrence-Count: <int>
- First-Seen: <YYYY-MM-DD>
- Last-Seen: <YYYY-MM-DD>
- User-Goal: <goal or "(none)">

Summary: <summary>
Details: <details or "(none)">
Files: <files or "(none)">
Status: <status or "pending">

---
```

Use `edit` to append (do not rewrite the file).

### Step 8 — Emit success output
Emit Output A.

## Failure modes

Return exactly one line and nothing else:

- Missing/invalid input:
  - `ERROR: invalid_input. Usage: /self-improving-agent <learning|error|feature> | <summary> [| details: ...] [| files: ...]`

- Summary too long:
  - `ERROR: summary_too_long. Max 180 characters.`

- Unsafe path:
  - `ERROR: unsafe_path. Refusing to write outside /Users/igorsilva/clawd/.learnings/.`

## Toolset

- `read`
- `write`
- `edit`

## Acceptance tests

1. **Behavioral (negative): missing fields**
   - Run: `/self-improving-agent`
   - Expected output (exact): `ERROR: invalid_input. Usage: /self-improving-agent <learning|error|feature> | <summary> [| details: ...] [| files: ...]`

2. **Behavioral: learning logs to LEARNINGS.md**
   - Run: `/self-improving-agent learning | test summary`
   - Expected:
     - Output starts with `SELF_IMPROVEMENT_LOGGED`
     - `TYPE: learning`
     - `PATH: /Users/igorsilva/clawd/.learnings/LEARNINGS.md`

3. **Behavioral: error logs to ERRORS.md**
   - Run: `/self-improving-agent error | something failed | goal: validate new node-connect skill`
   - Expected:
     - `PATH: /Users/igorsilva/clawd/.learnings/ERRORS.md`
     - Logged entry contains `User-Goal: validate new node-connect skill`

4. **Behavioral: feature logs to FEATURE_REQUESTS.md**
   - Run: `/self-improving-agent feature | add x`
   - Expected: `PATH: /Users/igorsilva/clawd/.learnings/FEATURE_REQUESTS.md`

5. **Behavioral: redaction applied**
   - Run: `/self-improving-agent error | token leak | details: X-Subscription-Token: abc123`
   - Expected:
     - Logged entry contains `X-Subscription-Token: [REDACTED]`.

6. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/self-improving-agent/SKILL.md
```
Expected: `PASS`.

7. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/self-improving-agent/SKILL.md
```
Expected: `PASS`.
