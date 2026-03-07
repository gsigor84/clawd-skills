---
name: pattern-library
description: Trigger phrase "pattern-library". Internal-only skill called by agent-failure-debugger (not triggered directly by users). Scans ~/clawd/.learnings/ERRORS.md, extracts and ranks known crash patterns (unique FAILED TOOL + ERROR TYPE combinations) by occurrence count, identifies recurring failures (3+ occurrences) that should be promoted to AGENTS.md if not already promoted, and outputs a structured plain text PATTERN LIBRARY REPORT that agent-failure-debugger uses to provide historically informed recovery prompts.
tools: bash
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
