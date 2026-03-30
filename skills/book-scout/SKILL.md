---
name: book-scout
description: "Trigger: /book-scout --topic <topic> [--queries <number>]. Generate search queries, query OceanOfPDF via Tandem, extract and deduplicate book results, save to ~/clawd/tmp/book-scout/<topic>-<date>.md."
---

# book-scout

## Use

Find books on any topic via OceanOfPDF search using Tandem browser automation, deduplicate results, and save structured markdown output.

## Trigger contract

Trigger when the user sends:
- `/book-scout --topic <topic> [--queries <number>]`

Where:
- `<topic>` — one line, non-empty
- `<number>` — optional number of search queries (default: 3, max: 5)

## Goal

Find books on any topic via OceanOfPDF search using Tandem browser automation, dedupe results, save structured output.

## Constraints

- **Only** write to: `~/clawd/tmp/book-scout/`
- Never write elsewhere
- If Tandem fails → fail with one line
- If 0 results → still save with "Total found: 0"

## Inputs

Two flags:
- `--topic <topic>`
- `--queries <number>` (optional, default 3, max 5)

## Outputs

Plain text.

### Output A — Success
BOOK_SCOUT_COMPLETE
TOPIC: <topic>
TOTAL_FOUND: <N>
OUTPUT: ~/clawd/tmp/book-scout/<topic>-<date>.md

### Output B — Failure
One line: `ERROR: <reason>`

## Deterministic workflow

### Tooling
- `exec` — curl to Tandem API at http://127.0.0.1:8765
- `write` — save results markdown

### Tandem API reference
```
POST /tabs/open        {"url": "https://..."}         → open new tab, returns {"tab": {"id": "tab-N"}}
POST /tabs/focus       {"tabId": "tab-N"}            → focus tab
GET  /snapshot?compact=true                             → snapshot current tab
GET  /snapshot?compact=true  (header: X-Tab-Id: tab-N) → snapshot specific tab
POST /snapshot/click   {"ref": "@eN"}                → click element by accessibility ref
POST /find             {"by": "text", "value": "..."} → find element by text
GET  /tabs/list                                             → list all open tabs
```
Authentication: Authorization: Bearer <token> (token from ~/.tandem/api-token)

### Step 1 — Generate queries
1) Parse topic.
2) Generate query variations (fixed list, pick first N):
   - `<topic>`
   - `<topic> with code examples`
   - `<topic> practical guide`
   - `<topic> pdf download`
   - `<topic> 2024 2025`

Use first N (default 3).

### Step 2 — Query OceanOfPDF via Tandem
For each query:
- POST /tabs/open with {"url": "https://oceanofpdf.com/?s=<query>"}
- Wait 3s for page load
- POST /tabs/focus with {"tabId": "<tab-id>"}
- Wait 1s
- GET /snapshot?compact=true with X-Tab-Id header → get page tree

### Step 3 — Extract results
For each snapshot, extract lines matching:
- link pattern: `link "Title" [@eN]` — extract title and ref
- Skip nav links (short titles, skip links, site nav items)
- Strip [PDF] and [EPUB] markers from titles

### Step 4 — Deduplicate
- Normalize titles (lowercase, strip punctuation)
- Keep first occurrence only

### Step 5 — Save
Directory: `~/clawd/tmp/book-scout/`
Filename: `<topic>-<YYYY-MM-DD>.md`

Format:
```markdown
# Book Scout: <topic>
Date: <YYYY-MM-DD>
Total found: <N>

## Results

| # | Title |
|---|-------|
| 1 | ... |

## Failure modes

- `ERROR: invalid_input. Usage: /book-scout --topic <topic> [--queries <N>]`
- `ERROR: no_tandem. Could not reach Tandem API.`
- `ERROR: query_failed. OceanOfPDF query failed: <query>`

## Toolset

- `exec`
- `write`

## Acceptance tests

1. **Behavioral (negative): missing topic**
   - Run: `/book-scout`
   - Expected: `ERROR: invalid_input. Usage: /book-scout --topic <topic> [--queries <N>]`

2. **Behavioral: saves to correct directory**
   - Run: `/book-scout --topic "test"`
   - Expected: output starts with `BOOK_SCOUT_COMPLETE` and path includes `~/clawd/tmp/book-scout/`

3. **Behavioral: respects max queries**
   - Run: `/book-scout --topic "ai" --queries 5`
   - Expected: uses exactly 5 queries from the list

4. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/book-scout/SKILL.md
```
Expected: `PASS`.

5. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/book-scout/SKILL.md
```
Expected: `PASS`.