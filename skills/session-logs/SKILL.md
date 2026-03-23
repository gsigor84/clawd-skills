---
name: session-logs
description: "Trigger: /session-logs <query>. Search local OpenClaw JSONL session transcripts under ~/.clawdbot/agents/<agentId>/sessions/ and return matching snippets with file + line hints (no secrets)."
---

# session-logs

## Trigger contract

Trigger when the user asks to search prior conversations and provides either:
- `/session-logs <keyword-or-phrase>`
- `/session-logs session=<session-id> | <keyword-or-phrase>`
- `/session-logs day=YYYY-MM-DD | <keyword-or-phrase>`

Rules:
- Query must be non-empty.
- This skill reads local session logs only; it does not call the web.

## Use

Use this skill to find what was said in older chats when that context is not in current memory. It searches OpenClaw session JSONL transcripts and returns short, human-readable text snippets.

## Inputs

One plain-text query.

Optional filters:
- `session=<session-id>`: restrict to a single `.jsonl` session file
- `day=YYYY-MM-DD`: restrict to sessions whose first timestamp matches the day (best-effort)

Examples:
- `/session-logs whatsapp`
- `/session-logs day=2026-03-23 | BSATauqhG5V6hBQaS2y0_SSNf8i1fVe`
- `/session-logs session=abcd-1234.jsonl | gateway restart`

## Outputs

Plain text with this exact structure:

SESSION_LOG_SEARCH
QUERY: <query>
FILTER: <none|session=...|day=...>
RESULTS:
- FILE: <path>
  HITS: <n>
  SNIPPETS:
  1) <single-line snippet>
  2) <single-line snippet>

Constraints:
- Max 5 files returned.
- Max 3 snippets per file.
- Snippets must be text-only (from message.content.type=="text").
- Do not output tool calls or tokens; redact any substring matching `X-Subscription-Token:` or `Authorization:` by replacing the value with `[REDACTED]`.

## Deterministic workflow (must follow)

### Tooling
- `exec`

### Global caps (hard limits)
- Max files scanned: **200**
- Max results files returned: **5**
- Max snippets per file: **3**
- Max snippet length: **240** characters

### Boundary rules (privacy + safety)

- Only read from: `~/.clawdbot/agents/*/sessions/`.
- Never write, edit, or delete logs.
- Do not output secrets/tokens; always redact.
- Only extract human-readable text content (ignore tool call payloads).

### Step 1 — Resolve log directory
The log directory pattern is:
- `~/.clawdbot/agents/*/sessions/`

If no matching directory exists or no `.jsonl` files exist, fail.

### Step 2 — Build a deterministic search command
Search strategy:

1) Find candidate files:
- If `session=` provided, scan only that file.
- Else scan up to 200 `.jsonl` files under the sessions directory.
- If `day=` provided, keep only files whose first line `.timestamp` starts with that date.

2) Extract text lines (jq):
- Use jq to output only text content:
  - `select(.type=="message") | .message.content[]? | select(.type=="text") | .text`

3) Search for query:
- Use ripgrep case-insensitive:
  - `rg -n -i --fixed-string "<query>"`

All of the above is executed via `exec` using a single bash command pipeline.

### Step 3 — Post-process into report
- For each matched file, count hits.
- Emit up to 3 snippets (single-line, trimmed, max 240 chars).
- Redact any token-like headers.

## Failure modes

Return exactly one line and nothing else:

- Missing query:
  - `ERROR: missing_query. Usage: /session-logs <keyword-or-phrase>`

- No session logs:
  - `ERROR: no_session_logs. Expected ~/.clawdbot/agents/*/sessions/*.jsonl to exist.`

- No matches:
  - `ERROR: no_matches. No session log entries matched the query.`

## Toolset

- `exec`

## Acceptance tests

1. **Behavioral (negative): missing query**
   - Run: `/session-logs`
   - Expected output (exact): `ERROR: missing_query. Usage: /session-logs <keyword-or-phrase>`

2. **Behavioral: output header is stable**
   - Run: `/session-logs gateway`
   - Expected: output starts with `SESSION_LOG_SEARCH` and includes `QUERY:` and `RESULTS:`.

3. **Behavioral: respects max files returned**
   - Run: `/session-logs the`
   - Expected: at most 5 `FILE:` blocks appear.

4. **Behavioral: redacts token headers**
   - Run: `/session-logs X-Subscription-Token:`
   - Expected: no snippet contains the literal token value after `X-Subscription-Token:`; it must show `[REDACTED]`.

5. **Behavioral (negative): no matches returns exact error**
   - Run: `/session-logs this-string-should-not-exist-1234567890`
   - Expected output (exact): `ERROR: no_matches. No session log entries matched the query.`

6. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/session-logs/SKILL.md
```
Expected: `PASS`.

7. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/session-logs/SKILL.md
```
Expected: `PASS`.
