---
name: tool-auditor
description: "Stage 2 of /vibe. Given an INTENT DOCUMENT, run real deterministic checks (via exec) to classify required tool categories as READY|MISSING|UNKNOWN and emit a parseable TOOL AUDIT REPORT + INSTALL PLAN (no secrets)."
---

# tool-auditor (internal)

## Trigger contract

This is stage 2 of the `/vibe` pipeline.

Trigger only when the input contains an INTENT DOCUMENT with:
- `SKILL NAME:`
- `TRIGGER:`
- `TOOLS LIKELY NEEDED:` (comma-separated categories)

Allowed categories (case-insensitive):
- `web search`
- `web scraping`
- `knowledge base`
- `file system`
- `email`
- `reddit api`
- `calendar`
- `other`

If the document is missing required fields or includes unsupported categories, return the exact error in **Failure modes**.

## Use

Use this stage to determine whether the system has the required capabilities to build the requested skill. It executes deterministic availability checks and produces an INSTALL PLAN for missing items.

This stage must never embed or print secrets (API tokens). It should prefer local, non-network checks when possible.

## Inputs

One plain-text INTENT DOCUMENT produced by `intent-parser`.

Minimum example:

INTENT DOCUMENT
SKILL NAME: example
TRIGGER: /example
TOOLS LIKELY NEEDED: web scraping, file system
WORKFLOW STEPS:
1) ...

## Outputs

A structured plain-text report with sections in this exact order:

TOOL AUDIT REPORT
SKILL NAME: <from intent>
TRIGGER: <from intent>

AUDIT RESULTS
- TOOL: <category>
  STATUS: <READY|MISSING|UNKNOWN>
  CHECK: <exact check command used>
  INSTALL COMMAND: <present only if MISSING>

VERDICT: <ALL TOOLS READY|TOOLS MISSING|AUDIT INCOMPLETE>

INSTALL PLAN
1. <install command> — <plain-English explanation>
2. ...

Rules:
- Include INSTALL PLAN only when VERDICT is `TOOLS MISSING`.
- Do not include any API tokens in CHECK or INSTALL commands.

## Deterministic workflow (must follow)

### Tooling
- `exec`

### Global caps (hard limits)
- Max categories processed: **10**
- Per-check timeout: **20 seconds**
- Total exec calls: **12**

### Boundary rules (privacy + consent + disallowed)

- No installs are executed in this stage.
- Do not print or embed tokens or secrets.
- Do not run destructive commands.
- For any check that would require a secret (e.g., Brave token), mark the tool as `UNKNOWN` unless a local, secret-free check exists.

### Step 1 — Parse intent
1) Extract `SKILL NAME`, `TRIGGER`, and `TOOLS LIKELY NEEDED`.
2) Normalize categories to lowercase.
3) If categories list is empty → fail.
4) If any category is not in the allowed set → fail.

### Step 2 — Run checks per category
For each category, run the exact check below and set STATUS:

#### web search
Do not perform a live Brave request (would require a secret token). Instead:
- Check whether `web_search` capability is available in this OpenClaw environment by verifying the tool name is present in this repository’s tooling assumptions is not possible here.
- Therefore set:
  - STATUS: `UNKNOWN`
  - CHECK: `N/A (requires secret for live check)`
  - INSTALL COMMAND: (none)

#### web scraping
Run:
- `command -v curl >/dev/null && echo ok || echo missing`
- `/opt/anaconda3/bin/python3 -c "from playwright.sync_api import sync_playwright; print('ok')"`

STATUS rules:
- If curl missing → `UNKNOWN` (do not invent OS install commands)
- If playwright import fails → `MISSING`

INSTALL COMMAND (if missing playwright):
- `/opt/anaconda3/bin/python3 -m pip install playwright --break-system-packages`

#### knowledge base
Run:
- `curl -s -m 3 -X POST http://127.0.0.1:5055/api/search -H 'Content-Type: application/json' -d '{"query":"test","type":"text","limit":1,"search_sources":false}' | /opt/anaconda3/bin/python3 -c "import sys,json; d=json.load(sys.stdin); print('ok' if isinstance(d, dict) and ('results' in d or 'data' in d) else 'bad')"`

STATUS rules:
- `ok` → READY
- `bad` or curl error → UNKNOWN

#### file system
Run:
- `command -v bash >/dev/null && echo ok || echo missing`

STATUS rules:
- `ok` → READY
- else → UNKNOWN

#### email
Run:
- `/opt/anaconda3/bin/python3 -c "import yagmail; print('ok')"`

STATUS rules:
- `ok` → READY
- ImportError → MISSING

INSTALL COMMAND:
- `/opt/anaconda3/bin/python3 -m pip install yagmail --break-system-packages`

#### reddit api
Run:
- `/opt/anaconda3/bin/python3 -c "import praw; print('ok')"`

STATUS rules:
- `ok` → READY
- ImportError → MISSING

INSTALL COMMAND:
- `/opt/anaconda3/bin/python3 -m pip install praw --break-system-packages`

#### calendar
Run:
- `/opt/anaconda3/bin/python3 -c "import gcsa; print('ok')"`

STATUS rules:
- `ok` → READY
- ImportError → MISSING

INSTALL COMMAND:
- `/opt/anaconda3/bin/python3 -m pip install gcsa --break-system-packages`

#### other
Infer a python import to check based on WORKFLOW STEPS (case-insensitive keyword match):
- contains `google sheets` or `spreadsheet` → import `gspread`
- contains `slack` → import `slack_sdk`
- contains `notion` → import `notion_client`
- contains `twitter` or `x.com` → import `tweepy`
- contains `pdf` → import `pypdf`
- contains `image` or `png` or `jpg` → import `PIL`

If no inference possible → STATUS: UNKNOWN.

If inferred import is `PIL`, treat package name as `pillow` for install.

Check command:
- `/opt/anaconda3/bin/python3 -c "import <import_name>; print('ok')"`

STATUS rules:
- ok → READY
- ImportError → MISSING

INSTALL COMMAND (if MISSING):
- `/opt/anaconda3/bin/python3 -m pip install <package_name> --break-system-packages`

### Step 3 — Compute verdict
- If any STATUS is MISSING → `VERDICT: TOOLS MISSING`
- Else if any STATUS is UNKNOWN → `VERDICT: AUDIT INCOMPLETE`
- Else → `VERDICT: ALL TOOLS READY`

### Step 4 — Build INSTALL PLAN
Only when VERDICT is TOOLS MISSING:
- List each install command exactly once.
- Add a plain-English explanation.

## Failure modes

Return exactly one line and nothing else:

- Missing required fields:
  - `ERROR: invalid_intent_document. Expected SKILL NAME, TRIGGER, and TOOLS LIKELY NEEDED.`

- Unsupported category:
  - `ERROR: unsupported_tool_category. Allowed: web search, web scraping, knowledge base, file system, email, reddit api, calendar, other.`

## Toolset

- `exec`

## Acceptance tests

1. **Behavioral (negative): missing intent fields**
   - Run: `/tool-auditor hello`
   - Expected output (exact): `ERROR: invalid_intent_document. Expected SKILL NAME, TRIGGER, and TOOLS LIKELY NEEDED.`

2. **Behavioral (negative): unsupported category rejected**
   - Run: `/tool-auditor SKILL NAME: x\nTRIGGER: /x\nTOOLS LIKELY NEEDED: bluetooth`
   - Expected output (exact): `ERROR: unsupported_tool_category. Allowed: web search, web scraping, knowledge base, file system, email, reddit api, calendar, other.`

3. **Behavioral: report sections and ordering**
   - Run: `/tool-auditor <valid intent>`
   - Expected: output contains, in order:
     - `TOOL AUDIT REPORT`
     - `AUDIT RESULTS`
     - `VERDICT:`

4. **Behavioral: MISSING tool produces INSTALL PLAN**
   - Given an intent requiring `email` and yagmail import fails, expected:
     - One AUDIT RESULTS entry with `STATUS: MISSING` and an INSTALL COMMAND.
     - `VERDICT: TOOLS MISSING`
     - `INSTALL PLAN` present.

5. **Behavioral: UNKNOWN tool yields AUDIT INCOMPLETE**
   - Given an intent requiring `web search`, expected:
     - `STATUS: UNKNOWN` for web search
     - `VERDICT: AUDIT INCOMPLETE`

6. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/tool-auditor/SKILL.md
```
Expected: `PASS`.

7. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/tool-auditor/SKILL.md
```
Expected: `PASS`.
