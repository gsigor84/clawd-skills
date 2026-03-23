---
name: pattern-library
description: "## pattern-library (internal)"
---

## pattern-library (internal)

### Trigger
pattern-library

### Responsibility
Scan `~/clawd/.learnings/ERRORS.md` and build a ranked library of known crash patterns so agent-failure-debugger can match new crashes against past failures and return historically informed recovery prompts.

### Hard constraints
- Never require external dependencies.
- Use only **bash**, **grep**, **awk**, and **cat**.
- Never modify any files (read-only).
- All output must be plain text and directly usable by agent-failure-debugger.

### Steps (must run in this exact order)

1) **Library scan**
- Execute this bash command and capture the full output:
  - `cat ~/clawd/.learnings/ERRORS.md`
- If the file does not exist or the output is empty, output exactly:

PATTERN LIBRARY EMPTY — no historical data available.

…and stop.

2) **Pattern extraction**
- Parse the captured file and extract every **unique combination** of:
  - `FAILED TOOL`
  - `ERROR TYPE`
- For each unique tool name found, count occurrences using this bash command (run it once per unique tool name):
  - `grep -c "FAILED TOOL: TOOLNAME" ~/clawd/.learnings/ERRORS.md`
  - Replace `TOOLNAME` with each unique tool name you extracted.

Notes:
- Use `awk` to extract unique tool names and unique (FAILED TOOL, ERROR TYPE) combinations.
- Occurrence counts must come from the `grep -c` command above.

3) **Pattern ranking**
- Rank all extracted patterns by occurrence count from highest to lowest.
- For each pattern, extract the **most recent** `RECOVERY PROMPT` associated with that same `FAILED TOOL` and `ERROR TYPE` combination.
- The most recent recovery prompt becomes the **RECOMMENDED FIX** for that pattern.

4) **Output**
Produce a structured plain text report with these sections (exact headings):

PATTERN LIBRARY REPORT

1) TOTAL PATTERNS FOUND
- <count of unique FAILED TOOL + ERROR TYPE combinations>

2) RANKED PATTERNS
For each pattern (in ranked order), output:
- Rank: <n>
- FAILED TOOL: <tool>
- ERROR TYPE: <type>
- COUNT: <occurrence count>
- RECOMMENDED FIX: <most recent recovery prompt for this tool+type>

3) RECURRING ALERTS
- List any pattern with COUNT >= 3.
- For each, output:
  - FAILED TOOL: <tool>
  - ERROR TYPE: <type>
  - COUNT: <count>
  - FLAG: PROMOTE TO AGENTS.MD
- Only include it if it has **not** already been promoted.

Promotion detection (read-only):
- Check `~/clawd/AGENTS.md` for a line that contains both the tool name and the error type.
- If found, treat that pattern as already promoted and do not list it under RECURRING ALERTS.

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
   - Run: `/pattern-library <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/pattern-library <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/pattern-library/SKILL.md
```
Expected: `PASS`.

4. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/pattern-library/SKILL.md
```
Expected: `PASS`.
