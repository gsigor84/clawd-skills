---
name: agent-failure-debugger
description: "## agent-failure-debugger"
---

## agent-failure-debugger

### Trigger
- debug agent
- fix crash
- trace error

### Output format
Plain English. When you generate the recovery instruction, output it exactly as a single line prefixed with:

RECOVERY PROMPT:

(That line may contain technical detail and must be precise and actionable.)

### Steps (must run in this exact order)

1) **Log retrieval (capture output)**

Run this command first and capture its output:

- `tail -n 100 ~/.openclaw/logs/agent.log`

If that file does not exist **or** returns empty output, try these fallback paths in order, capturing the first non-empty output:

- `tail -n 100 ~/.openclaw/logs/gateway.log`
- `tail -n 100 ~/clawd/logs/agent.log`
- `tail -n 100 ~/clawd/logs/gateway.log`

Implementation requirement (bash only):
- Use bash built-ins to test file existence/emptiness and run `tail` only on files that exist.
- Store the chosen log path in `LOG_PATH` and the captured text in `LOG_TEXT`.

If all paths are missing or empty, output exactly:

No logs found. Workspace appears stable. If you are seeing crashes, check that logging is enabled in your clawdbot config.

…and stop.

2) **Pattern recognition (scan for failure signatures)**

Parse `LOG_TEXT` and search for these failure signatures in this order (most severe first). Stop at the first match.

- **CRITICAL**: stack trace containing `fatal` or `uncaught exception`
- **HIGH**: malformed JSON output from a tool call
- **HIGH**: missing required tool parameter
- **MEDIUM**: infinite loop detection (same tool called more than 3 times with identical parameters)
- **MEDIUM**: timeout on external API call
- **LOW**: rate limit hit on Brave Search or any API

If `LOG_TEXT` is too large to process within context, use this fallback command instead:

- `grep -i "fatal|error|timeout|malformed|uncaught" ~/.openclaw/logs/agent.log | tail -n 20`

Notes:
- Use only `grep` and `awk` for parsing.
- Treat matches case-insensitively.

3) **Failure identification (extract fields)**

From the matched pattern and surrounding lines in the captured logs, extract **exactly** these fields:

- **FAILED TOOL:** the tool name that crashed (e.g., exec, browser, web_fetch, web_search, read, write, edit, process, nodes, message, sessions_spawn, etc.)
- **ERROR TYPE:** one of `CRITICAL | HIGH | MEDIUM | LOW`
- **ERROR REASON:** one sentence, plain English, describing what went wrong
- **LAST SUCCESSFUL STEP:** the last step that completed before the failure (e.g., “log retrieval”, “pattern recognition”, a named tool call, etc.)

If the FAILED TOOL cannot be confidently determined from logs, set:
- FAILED TOOL: unknown

4) **Recovery injection (generate recovery prompt)**

Based on **ERROR TYPE** and the matched signature, generate a specific recovery prompt using these rules:

- Malformed JSON → instruct the agent to re-run the last tool call with explicit JSON formatting instructions.
- Missing required tool parameter → instruct the agent to re-run with the missing parameter filled in explicitly.
- Infinite loop → instruct the agent to break the task into smaller subtasks and retry each one separately.
- Timeout → instruct the agent to retry with a shorter timeout and a fallback data source.
- Rate limit → instruct the agent to wait 60 seconds and retry with exponential backoff.
- Fatal/uncaught exception → instruct the agent to restart the failed stage from the last successful step.

Output the recovery prompt directly to the user **prefixed** with:

RECOVERY PROMPT:

5) **Self-improvement logging (permanent record + promotion)**

After injecting the recovery prompt, log the failure to:

- `~/clawd/.learnings/ERRORS.md`

Requirements:
- Use the ID format: `ERR-YYYYMMDD-XXX`.
- `YYYYMMDD` must be today’s date.
- `XXX` must be a 3-digit sequence for that date (001, 002, …). Determine the next sequence by scanning the existing file with `awk` (do not use external utilities beyond `tail`, `grep`, `awk`). If the file does not exist, start at 001.

The entry must include:
- FAILED TOOL
- ERROR TYPE
- ERROR REASON
- LAST SUCCESSFUL STEP
- the **exact** RECOVERY PROMPT that was injected
- the chosen `LOG_PATH`

Also check for recurrence:

- Run: `grep -c "FAILED TOOL: [tool name]" ~/clawd/.learnings/ERRORS.md`

If the same **ERROR TYPE** and **FAILED TOOL** combination has appeared **3 or more times**, automatically promote the recovery rule to:

- `~/clawd/AGENTS.md`

Promotion requirements:
- Append a short, plain-English prevention rule that mentions the FAILED TOOL + ERROR TYPE combination and the prevention action.
- Before appending, use `grep` to avoid adding the exact same rule twice.

If you promoted a rule, tell the user exactly:

This crash pattern has been seen 3+ times. I have added a permanent prevention rule to AGENTS.md.

### Hard constraints
- Never require external dependencies, virtual environments, conda, or any package manager.
- Use only bash, tail, grep, and awk.
- Never modify skill files or log files.
- Writing to `~/clawd/.learnings/ERRORS.md` and `~/clawd/AGENTS.md` is permitted.
- All user-facing messages must be plain English with no technical jargon, **except** the recovery instruction line prefixed `RECOVERY PROMPT:`.

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
   - Run: `/agent-failure-debugger <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/agent-failure-debugger <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/agent-failure-debugger/SKILL.md
```
Expected: `PASS`.

4. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/agent-failure-debugger/SKILL.md
```
Expected: `PASS`.
