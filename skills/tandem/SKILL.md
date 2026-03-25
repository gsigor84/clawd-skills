---
name: tandem
description: "Trigger: /tandem <task>. Use the local Tandem Browser API at http://127.0.0.1:8765 to inspect pages and interact safely in a separate tab (no clobbering the user’s active tab)."
---

# tandem (browser helper)

## Trigger contract

Trigger when the user asks to browse/inspect/interact with a webpage using Tandem, using either:
- `/tandem <task>`
- `/tandem url=<http(s)://...> | <task>`

Rules:
- If a URL is provided, it must be `http://` or `https://`.
- This skill targets a local API only: `http://127.0.0.1:8765`.
- This skill must not modify the user’s active tab unless explicitly instructed.

## Use

Use this skill to:
- open a new “work” tab for a URL without stealing focus,
- focus that tab only when needed for snapshot/interactions,
- capture a compact snapshot for analysis,
- optionally click/fill using snapshot refs or semantic finders,
- close the temporary tab when finished,
- escalate to the user if blocked by login/captcha/MFA.

## Inputs

A single plain-text instruction.

Supported fields (optional):
- `url=`: the target URL to open
- `task=`: what to inspect or do (if not provided, treat the rest of the message as the task)

Examples:
- `/tandem url=https://example.com | summarize what’s on the page`
- `/tandem open https://example.com and find the pricing section`
- `/tandem check what the user is currently looking at`

## Outputs

Output is plain text.

### Output A — Error
If hard-blocked, output exactly one line starting with `ERROR:` (see Failure modes).

### Output B — Result
Otherwise output a structured block:

TANDEM_RESULT
ACTIVE_CONTEXT_URL: <url or empty>
WORK_TAB_ID: <tab-id or empty>
ACTIONS_TAKEN:
- <action>
- <action>
FINDINGS:
- <finding>
- <finding>
NEXT:
- <next step or "done">

Constraints:
- Do not include the Tandem API token in output.
- Do not paste large page content; keep findings high-level.

## Deterministic workflow (must follow)

### Tooling
- `read` (to read `~/.tandem/api-token`)
- `exec` (to run `curl` calls to the Tandem API)

### Global caps (hard limits)
- Max Tandem API calls per run: **12**
- Max snapshot/page text included in agent reasoning: **compact=true only** (never full HTML dumps in output)
- Max work tabs opened per run: **1**

### Boundary rules (privacy + safety)

- Never call non-local hosts: all network calls must be to `http://127.0.0.1:8765`.
- Never call destructive endpoints:
  - Disallowed: `/emergency-stop`, `/network/mock`, `/network/unmock`, `/sessions/fetch`, `/execute-js`, `/execute-js/confirm`.
- Never interact with login/password fields.
  - If the task requires login/MFA/captcha: call `POST /wingman-alert` and stop.
- Do not take screenshots unless explicitly requested.
- Prefer a new tab via `POST /tabs/open` with `focus:false` and `source:"wingman"`.
- Close the work tab at the end if it was opened by this skill.

### Step 1 — Load token
1) Read the token from `~/.tandem/api-token`.
2) If missing/empty → fail.

Set constants:
- `API=http://127.0.0.1:8765`
- `AUTH_HEADER=Authorization: Bearer <token>`
- `JSON_HEADER=Content-Type: application/json`

### Step 2 — Get active-tab context (awareness)
Call:
- `GET /active-tab/context`

Record `activeTab.url` as `ACTIVE_CONTEXT_URL` (may be empty).

### Step 3 — Decide whether to open a work tab
If input includes a URL:
- Open a new tab:
  - `POST /tabs/open` with JSON: `{ "url": "<url>", "focus": false, "source": "wingman" }`
- Extract `WORK_TAB_ID` from response.
- Focus it:
  - `POST /tabs/focus` with `{ "tabId": "<WORK_TAB_ID>" }`

If no URL:
- Do not open a new tab.
- Do not change focus.

### Step 4 — Capture snapshot for analysis
Call:
- `GET /snapshot?compact=true`

If snapshot is empty/failed → fail.

### Step 5 — Optional interaction (only if explicitly requested)
If the user’s task includes an explicit interaction request like “click”, “press”, “fill”, “type”:
- Prefer semantic find first:
  - `POST /find` with `by=text|label|role|placeholder`.
- If a ref is given/derived, use snapshot routes:
  - `POST /snapshot/click` or `POST /snapshot/fill`.

If the interaction target appears to be a password/login field (heuristic: label contains `password`, `sign in`, `log in`, `mfa`, `2fa`) → send wingman alert and stop.

### Step 6 — Clean up
If a work tab was opened:
- `POST /tabs/close` with `{ "tabId": "<WORK_TAB_ID>" }`.

### Step 7 — Emit result
Emit `TANDEM_RESULT` with actions taken and findings.

## Failure modes

Return exactly one of these lines and nothing else:

### Deterministic ERR logging via /self-improving-agent (mandatory on failures)

On any emitted `ERROR: ...` failure mode below, do this deterministically:

1) Emit the `ERROR: ...` line (as required by the Failure mode contract).
2) Immediately call `/self-improving-agent` to log one ERR entry.

Priority mapping:
- All failures here are hard-stop failures → `priority: high`

Never log secrets:
- Never include Tandem bearer tokens.
- Never include full snapshots/page content.

#### Exact /self-improving-agent call format (ERR)

Call (single line):
- `/self-improving-agent error | <one-line summary> | details: <details> | files: skills/tandem/SKILL.md`

The logged ERR entry must include these fields (keep short; no payloads):
- `Pattern-Key:` use the exact key from the mapping table below
- `Recurrence-Count:` start at `1`
- `First-Seen:` and `Last-Seen:` set to today

Include these context fields inside the entry:
- `stage: tandem`
- `priority: high`
- `status: hard_stop`
- `reason:` the exact `ERROR: ...` string
- `active_context_url:` from `GET /active-tab/context` (or empty)
- `requested_url:` user-provided URL if any; else empty
- `task:` first 120 chars of the user task
- `suggested_fix:` one line specific to the error

#### Pattern-Key mapping (use exact key)

| Failure | Pattern-Key |
|---|---|
| `ERROR: missing_token...` | `tandem:missing_token` |
| `ERROR: tandem_unreachable...` | `tandem:unreachable` |
| `ERROR: tandem_unauthorized...` | `tandem:unauthorized` |
| `ERROR: invalid_url...` | `tandem:invalid_url` |
| `ERROR: human_required...` | `tandem:human_required` |
| `ERROR: snapshot_failed...` | `tandem:snapshot_failed` |

- Missing token:
  - `ERROR: missing_token. Expected ~/.tandem/api-token to exist and be non-empty.`

- Tandem API not reachable:
  - `ERROR: tandem_unreachable. Expected Tandem at http://127.0.0.1:8765.`

- Unauthorized:
  - `ERROR: tandem_unauthorized. Bearer token rejected.`

- Invalid URL:
  - `ERROR: invalid_url. Provide a single http(s) URL.`

- Blocked by login/captcha/MFA:
  - `ERROR: human_required. Login/captcha/MFA encountered; sent wingman alert.`

- Snapshot failed:
  - `ERROR: snapshot_failed. Could not capture page snapshot.`

## Toolset

- `read`
- `write`
- `exec`

## Acceptance tests

1. **Behavioral (negative): missing token hard-stop**
   - Run: `/tandem check active tab`
   - Precondition: `~/.tandem/api-token` missing or empty.
   - Expected output (exact):
     - `ERROR: missing_token. Expected ~/.tandem/api-token to exist and be non-empty.`

2. **Behavioral (negative): invalid URL rejected**
   - Run: `/tandem url=ftp://example.com | inspect`
   - Expected output (exact):
     - `ERROR: invalid_url. Provide a single http(s) URL.`

3. **Behavioral: does not clobber user tab when URL not provided**
   - Run: `/tandem check what the user is currently looking at`
   - Expected:
     - No call to `POST /tabs/open`.
     - Output includes `ACTIVE_CONTEXT_URL:` populated from `/active-tab/context`.

4. **Behavioral: opens and closes exactly one work tab when URL provided**
   - Run: `/tandem url=https://example.com | inspect`
   - Expected:
     - Exactly one `POST /tabs/open` and one `POST /tabs/close` for the same `WORK_TAB_ID`.

5. **Behavioral: snapshot is compact**
   - Run: any valid URL flow.
   - Expected:
     - Snapshot call is exactly `GET /snapshot?compact=true` (not full snapshot).

6. **Behavioral (negative): disallowed endpoint never used**
   - Run: `/tandem url=https://example.com | execute javascript`
   - Expected:
     - The skill does not call `/execute-js` or `/execute-js/confirm`.
     - Output is either a TANDEM_RESULT describing refusal or a relevant ERROR.

7. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/tandem/SKILL.md
```
Expected: `PASS`.

8. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/tandem/SKILL.md
```
Expected: `PASS`.
