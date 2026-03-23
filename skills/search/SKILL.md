---
name: search
description: Brave-first web search with optional brief/deep summarization (trigger: /search).
---

# /search (Brave Search)

## Trigger
`/search`

## Purpose
Search the web using **Brave Search** and return concise, source-linked results.

## Input
A query string plus optional flags:
- `--mode` = `links|brief|deep` (default: `brief`)
- `--count` = integer (default: `5`, max: `10`, min: `1`)
- `--country` = `GB|US|ALL|...` (default: `ALL`)
- `--freshness` = `day|week|month|year` (default: none)

Examples:
- `/search openclaw docs`
- `/search --mode links --count 10 "claude code permission-mode"`
- `/search --mode deep "Brave Search API 429"`
- `/search --country GB --freshness day "UK inflation"`

## Output
- Always include **source URLs**.
- `links` mode: bullets with **Title — URL — snippet**.
- `brief` mode: same, plus **one-line takeaway per result**.
- `deep` mode: merged short summary + bullet list of fetched sources.

## Tooling
- Use `web_search` (Brave) for the search.
- Use `web_fetch` for deep mode page reads.

## Anti-lazy spec (non-negotiable)
### Acceptance criteria
1) Always include URLs.
2) Exactly **1** `web_search` call per run.
3) If mode is `deep`: at most **3** `web_fetch` calls.
4) Clamp `--count` to `1..10`.
5) If Brave returns **429 RATE_LIMITED**: stop and tell the user to retry later (no retry loops).

### Tests (must pass)
- `/search openclaw docs`
- `/search --mode links --count 10 "claude code permission-mode"`
- `/search --mode deep "Brave Search API 429"`

## Execution steps

### 1) Parse inputs
- Extract the query (everything that is not a flag).
- Parse flags; apply defaults.
- Clamp `count` to `[1,10]`.

### 2) Run Brave Search (exactly once)
Call:
- `web_search(query=<query>, count=<count>, country=<country>, freshness=<freshness-if-provided>)`

If the tool returns a 429 / rate limit error:
- Respond: `Brave Search is rate-limiting (429). Retry in ~60–120s.`
- Stop (no retries).

### 3) Render results
- `links` mode: output top `count` results as bullets: `- <title> — <url> — <snippet>`.
- `brief` mode: for each result, add one short takeaway derived from the snippet/title only. Do not browse additional pages.

### 4) Deep mode (optional fetch)
If `--mode deep`:
- Select the best 2–3 results (prefer primary sources / docs).
- Fetch each selected URL with `web_fetch(url=..., extractMode="markdown")`.
- Produce a short merged summary grounded in fetched content.
- Then list the fetched source URLs.

## Notes
- Prefer fewer, higher-signal results.
- Never invent URLs; only use what `web_search` returns.

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
   - Run: `/search <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/search <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/search/SKILL.md
```
Expected: `PASS`.
