---
name: apply-patch
description: "Trigger: /apply-patch --proposal <request-id>. Apply an approved remediation proposal (JSON) by backing up target files, applying exact edits, logging via self-improving-agent, and updating proposal status with monitoring outcomes."
---

# apply-patch

## Use

Apply an **approved** remediation proposal from `.learnings/PROPOSALS/` by backing up files, applying exact text replacements, updating proposal status, and notifying Igor if monitoring indicates the fix failed.

## Trigger contract

Trigger when the user sends:
- `/apply-patch --proposal <request-id>`

Where:
- `<request-id>` matches a proposal file name under `/Users/igorsilva/clawd/.learnings/PROPOSALS/`.

## Safety rules (hard)

- Refuse unless proposal `status` is exactly **"approved"**.
- Only write to files under:
  - `/Users/igorsilva/clawd/skills/`
  - `/Users/igorsilva/clawd/tools/`
- Create a backup before every patch write.
- Refuse if any target file is outside allowed directories.
- Patch must be applied using **exact replace** semantics (OpenClaw `edit`).
- Never touch (read/write/patch):
  - `/Users/igorsilva/clawd/config/`
  - `/Users/igorsilva/clawd/gateway/`
  - `openclaw.json` (any path)

## Inputs

Required:
- `--proposal <request-id>`

## Outputs

Plain text.

### Output A — Success
PATCH_APPLIED
REQUEST_ID: <request-id>
UPDATED_PROPOSAL: <absolute path>

### Output B — Failure
Return exactly one line starting with `ERROR:`.

## Deterministic workflow (must follow)

### Tooling
- `read` (read proposal + read current file contents)
- `write` (write backups)
- `edit` (apply exact replacements; update proposal status)
- `sessions_send` (notify Igor on WhatsApp on failure/monitoring outcomes)

### Step 1 — Load proposal
1) Compute proposal path:
   - `/Users/igorsilva/clawd/.learnings/PROPOSALS/<request-id>.json`
2) `read` it.
3) Parse JSON.
4) If missing/unreadable → fail:
   - `ERROR: proposal_not_found. No proposal at /Users/igorsilva/clawd/.learnings/PROPOSALS/<request-id>.json`

### Step 2 — Verify approval
1) If `status` != "approved" → fail:
   - `ERROR: not_approved. Proposal status must be approved.`

### Step 3 — Validate constraints
1) Ensure `patch.files` exists and is non-empty.
2) Ensure number of files ≤ 3.
3) For each file path:
   - Must be under `/Users/igorsilva/clawd/skills/` or `/Users/igorsilva/clawd/tools/`.
   - Must not contain `/config/` or `/gateway/`.
   - Must not end with or equal `openclaw.json`.
4) If any violation → fail:
   - `ERROR: unsafe_target. Refusing to write outside allowed directories.`

### Step 4 — Backup target files
For each target file `X`:
1) `read` file contents.
2) Compute backup path:
   - `/Users/igorsilva/clawd/.learnings/PROPOSALS/backups/<request-id>/<relative-path-from-clawd-root>.bak`
3) `write` backup file with original content.

### Step 5 — Apply patch edits
For each file:
- For each edit:
  - Use `edit` with `oldText` → `newText`.

If an `edit` fails due to non-unique match or not found:
- Stop immediately and fail:
  - `ERROR: patch_failed. oldText not found or not unique.`

### Step 6 — Log change via self-improving-agent
Append a learning entry using the **self-improving-agent** skill contract (no tool call required in this spec; but do the equivalent action):
- Type: learning
- Summary: `Applied remediation patch for <patternKey> (<request-id>)`
- Details: include backup path + files touched
- Goal: `reduce recurrence of <patternKey>`

Implementation note: this skill must directly append using tools, not invoke other skills.

### Step 7 — Update proposal status
Update proposal JSON (using `edit` with exact replace of the status field line):
- Set `status` to `resolved_pending_monitoring`
- Add fields:
  - `appliedAt` (ISO-8601)
  - `backupsPath`
  - `monitoring`: { `windowCount`: 0, `recurrenceCountAfterFix`: 0 }

### Step 8 — Monitoring rule (bounded)
This skill does not run continuously. It performs a bounded check at apply-time:
1) Read `/Users/igorsilva/clawd/.learnings/ERRORS.md`.
2) Count entries for `Pattern-Key: <patternKey>` whose `Last-Seen` is **after** `appliedAt` date (string compare on YYYY-MM-DD).
3) If count >= 2:
   - Mark proposal `status` to `failed`
   - Notify Igor via `sessions_send`.
4) If count == 0:
   - Mark proposal `status` to `resolved`.

If unable to compare dates reliably → leave as `resolved_pending_monitoring`.

## Failure modes

Return exactly one line:
- `ERROR: invalid_input. Usage: /apply-patch --proposal <request-id>`
- `ERROR: proposal_not_found. No proposal at /Users/igorsilva/clawd/.learnings/PROPOSALS/<request-id>.json`
- `ERROR: not_approved. Proposal status must be approved.`
- `ERROR: unsafe_target. Refusing to write outside allowed directories.`
- `ERROR: patch_failed. oldText not found or not unique.`

## Toolset

- `read`
- `write`
- `edit`
- `sessions_send`

## Acceptance tests

1. **Behavioral (negative): missing proposal**
   - Run: `/apply-patch`
   - Expected (exact): `ERROR: invalid_input. Usage: /apply-patch --proposal <request-id>`

2. **Behavioral (negative): not approved**
   - Precondition: proposal exists with status pending
   - Run: `/apply-patch --proposal SOMEID`
   - Expected (exact): `ERROR: not_approved. Proposal status must be approved.`

3. **Behavioral: applies approved patch + creates backup**
   - Precondition: proposal SOMEID exists with status approved and patch targets an allowed file
   - Run: `/apply-patch --proposal SOMEID`
   - Expected:
     - Output starts with `PATCH_APPLIED`
     - Backup file exists under `/Users/igorsilva/clawd/.learnings/PROPOSALS/backups/SOMEID/`
     - Proposal status becomes `resolved_pending_monitoring`

4. **Behavioral: refuses unsafe targets**
   - Precondition: proposal BAD exists with status approved but patch targets `/Users/igorsilva/clawd/config/...`
   - Run: `/apply-patch --proposal BAD`
   - Expected (exact): `ERROR: unsafe_target. Refusing to write outside allowed directories.`

5. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/apply-patch/SKILL.md
```
Expected: `PASS`.

6. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/apply-patch/SKILL.md
```
Expected: `PASS`.

7. **Behavioral: marks failed if recurrence >= 2**
   - Precondition: after apply, ERRORS.md contains 2+ entries for the pattern after appliedAt
   - Run: `/apply-patch --proposal SOMEID`
   - Expected: proposal status becomes `failed` and a WhatsApp notification is sent

8. **Behavioral: marks resolved if no recurrence**
   - Precondition: after apply, ERRORS.md contains 0 entries for the pattern after appliedAt
   - Run: `/apply-patch --proposal SOMEID`
   - Expected: proposal status becomes `resolved`
