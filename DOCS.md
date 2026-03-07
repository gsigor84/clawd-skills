# Clawdbot Project Reference (~/clawd)

This file is the living reference for this repo and the Clawdbot assistant running inside it.

**Workspace root:** `/Users/igorsilva/clawd`

## Quick start (what to type)

### Intelligence pipeline
- `/intel <target>`
  - Example: `/intel Notion`

### Assumption validation pipeline
- `/validate <plain-English business assumption>`

### Skill builder pipeline
- `/new-skill <what you want the skill to do>`

---

## Core pipelines

### /intel (strategic intelligence)
**Trigger:** `/intel <target>`  
**Output:** a 7-section strategic intelligence report (see `intelligence-reporter`).

**Stages (strict sequence; no skipping; pass only direct outputs):**
1) `vector-mapper`
2) `digital-scout`
3) `signal-extractor`
4) `intelligence-reporter`

**User-facing status messages (must match exactly):**
- Before Stage 1: `researching your target, this will take about 90 seconds.`
- Before Stage 2: `stage 2 of 4, scouting for sources.`
- Before Stage 3: `stage 3 of 4, extracting signals from sources.`
- Before Stage 4: `stage 4 of 4, compiling your intelligence report.`

**Failure rules (intel orchestrator):**
- Stage 1: if fewer than 5 vectors → abort; ask user to provide a more specific target.
- Stage 2: if every vector is `NO QUALITY SOURCES FOUND` → abort; suggest a more specific/well-known target.
- Stage 3: if every URL is `FAILED` → abort; say sources blocked/empty; suggest retry later or different target.
- Stage 4: if final report missing required sections → abort; ask user to try again.


### /validate (business assumption validation)
**Trigger:** `/validate <assumption>`  
**Output:** a 5-section validation report (verbatim from `synthesis-compiler`).

**Stages (strict sequence):**
1) `assumption-deconstructor`
2) `evidence-extractor`
3) `critical-evaluator`
4) `synthesis-compiler`

**Status messages (must match exactly):**
- `validating your assumption, this will take about 60 seconds.`
- `stage 2 of 4, searching knowledge base for evidence.`
- `stage 3 of 4, evaluating evidence against your assumption.`
- `stage 4 of 4, compiling your validation report.`

---

## /intel sub-skills (contracts)

### 1) vector-mapper (Stage 1)
**Trigger:** `vector-mapper` (internal)  
**Responsibility:** Map a target into a strict set of research vectors + queries.

**Hard constraints:**
- Always output **exactly 5 core vectors** in this order:
  1. Pricing
  2. Product
  3. Positioning
  4. Vulnerabilities
  5. Competitive Moves
- May add **0–2 domain-specific vectors** as #6–#7 only if genuinely target-specific.
- Never output <5 vectors or >7.
- Queries must include the target verbatim and be time-bounded where possible.

**Special fixed-query rules:**
- **Vulnerabilities** must always output exactly these 3 queries:
  1) `[target] reviews complaints site:g2.com 2025 2026`
  2) `[target] negative reviews site:trustpilot.com`
  3) `[target] problems frustrations site:news.ycombinator.com`

- **Competitive Moves** must always output exactly these 3 queries (tech press/news oriented):
  1) `[target] acquisition partnership integration 2025 2026`
  2) `[target] competitor response market expansion site:techcrunch.com OR site:venturebeat.com`
  3) `[target] vs competitors announcement 2025 2026 site:news.ycombinator.com`


### 2) digital-scout (Stage 2)
**Trigger:** `digital-scout` (internal)  
**Responsibility:** Execute every query under every vector and pick the best 2–3 URLs per vector.

**Hard constraints:**
- Must run **every query** for **every vector** (no skipping).
- Must never hallucinate URLs — select only from tool output.
- Must select **≤ 3 URLs per vector**.

**Search tool (current): Brave Search API**
Command template used per query:

```bash
curl -s "https://api.search.brave.com/res/v1/web/search?q=QUERY_URL_ENCODED&count=5" \
  -H "Accept: application/json" \
  -H "X-Subscription-Token: <token>" \
| /opt/anaconda3/bin/python3 -c "import sys, json
data = json.load(sys.stdin)
for r in data.get('web', {}).get('results', []):
    print(r['title'])
    print(r['url'])
    print((r.get('description', '') or '')[:200])
    print('---')"
```

**Encoding rule:** `QUERY_URL_ENCODED` = query with spaces replaced by `+`.

**Selection fields per chosen URL:**
- URL
- SOURCE TYPE: `OFFICIAL` | `REVIEW` | `PRESS` | `ANALYST`
- FRESHNESS: `FRESH` (2025–2026) | `RECENT` (2023–2024) | `UNKNOWN`
- RELEVANCE NOTE: one sentence


### 3) signal-extractor (Stage 3)
**Trigger:** `signal-extractor` (internal)  
**Responsibility:** Fetch each URL (curl first unless Playwright-first applies), extract 3–7 concrete signals per URL.

**Fetch methods:**
- **curl-first** (default)
- **Playwright fallback** if curl blocked/insufficient

**Playwright-first rule (important)**
Skip curl and go directly to Playwright if the URL matches any of:
- contains `/product/` or `/products/`
- contains `/help/` or `/support/`
- contains `/features/`
- contains `/enterprise/`
- contains `/pricing/` **and** is on the target’s own domain

**curl fetch template:**
```bash
curl -sL URL | /opt/anaconda3/bin/python3 -c "import sys, re; html = sys.stdin.read(); text = re.sub(r'<[^>]+>', ' ', html); text = re.sub(r'\s+', ' ', text).strip(); print(text[:5000])"
```

**Playwright fetch template (timeout 60s; domcontentloaded):**
```bash
/opt/anaconda3/bin/python3 -c "from playwright.sync_api import sync_playwright
import re
pw = sync_playwright().start()
browser = pw.chromium.launch(headless=True)
page = browser.new_page()
try:
    page.goto('URL', wait_until='domcontentloaded', timeout=60000)
    content = page.content()
except Exception as e:
    print('PLAYWRIGHT_ERROR: ' + str(e))
    browser.close()
    pw.stop()
    exit()
browser.close()
pw.stop()
text = re.sub(r'<[^>]+>', ' ', content)
text = re.sub(r'\s+', ' ', text).strip()
print(text[:5000])"
```

**Signals format:**
- 3–7 numbered, **one sentence each**, each prefixed with `[Vector Name]`.
- No vague statements; must be concrete (prices, dates, named features, named partners, explicit complaints, numeric limits, etc.).

**Extraction quality:**
- `STRONG` (≥3 good signals)
- `WEAK` (<3 or borderline)
- `FAILED` (no usable content)
  - failure reason: `BLOCKED` | `EMPTY` | `TIMEOUT` | `ERROR`


### 4) intelligence-reporter (Stage 4)
**Trigger:** `intelligence-reporter` (internal)  
**Responsibility:** Turn a signal report into a final strategic intel brief.

**Hard constraints:**
- Must output **exactly 7 sections** in this order:
  1) TARGET (target + Month Year)
  2) VECTORS RESEARCHED (vector list with signal counts)
  3) SIGNALS (8–15 bullets, each with [Vector] and (URL))
  4) DELTA (3–5 sentences grounded in signals)
  5) THREATS (3–5 bullets)
  6) VULNERABILITIES (3–5 bullets; include leverage note)
  7) OPPORTUNITIES (3–5 bullets; actionable in next 30 days)
- No external knowledge: everything must be traceable to extracted signals.

---

## Skill builder pipeline (/new-skill)

**Trigger:** `/new-skill <description>`

**Stages:**
1) `skill-intake` → converts user request into a structured schema (asks one consolidated question if needed).
2) `skill-designer` → maps schema to exact commands using Adam’s supported stack.
3) `skill-writer` → writes the SKILL.md content.
4) `skill-deployer` → saves the SKILL.md to `~/clawd/skills/<name>/SKILL.md`.

**Hard constraints:** never skip stages; pass only direct outputs; abort cleanly on rejection.

---

## Research rules (AGENTS.md)

These rules apply whenever using the **researcher** skill (market/competitor research):
- MUST query local Open Notebook KB first:
  - `curl -s -X POST http://127.0.0.1:5055/api/search ... type:"text"`
- MUST use `/opt/anaconda3/bin/python3` for DuckDuckGo (when DDG is used).
- Never answer research questions from memory alone — show tool evidence.

See: `~/clawd/AGENTS.md`.

---

## Open Notebook (local KB) reference

- UI: http://127.0.0.1:8502
- API: http://127.0.0.1:5055
- Swagger: http://127.0.0.1:5055/docs
- OpenAPI spec: http://127.0.0.1:5055/openapi.json

**Health check:**
```bash
curl -sS http://127.0.0.1:5055/health | cat
```

**Text search (recommended):**
```bash
curl -s -X POST http://127.0.0.1:5055/api/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"YOUR QUERY","type":"text","limit":6,"search_sources":true}'
```

---

## Skills inventory (local)

Paths: `~/clawd/skills/<skill>/SKILL.md`

### Orchestrators
- `intel` (trigger: `/intel`) — strategic intel pipeline
- `validate` (trigger: `/validate`) — assumption validation pipeline
- `new-skill` (trigger: `/new-skill`) — build/deploy skills

### Intel pipeline sub-skills
- `vector-mapper` (trigger: `vector-mapper`)
- `digital-scout` (trigger: `digital-scout`)
- `signal-extractor` (trigger: `signal-extractor`)
- `intelligence-reporter` (trigger: `intelligence-reporter`)

### Validate pipeline sub-skills
- `assumption-deconstructor`
- `evidence-extractor`
- `critical-evaluator`
- `synthesis-compiler`

### Other utilities
- `researcher` — business research (KB-first + web)
- `open-notebook-local` — manage/query local KB via API
- `ddg-search` — DuckDuckGo search utility
- `url-arg-summarizer` — argument summary of a URL
- `summarize` — summarize URLs/files (CLI)
- `notebooklm` — NotebookLM CLI wrapper
- `code-executor` — run ad-hoc Python/JS/Bash
- `create-cli` — CLI UX/spec design helper
- `byterover` — knowledge/context tree management
- `self-improvement` — capture failures/corrections as learnings
- `wacli` — WhatsApp CLI integration (skill name in repo: `mh-wacli`)

---

## Troubleshooting

### 1) Search failures / rate limits
- DuckDuckGo (`duckduckgo_search`) can rate-limit or time out. This is why `digital-scout` moved to Brave Search.
- If Brave returns empty results, check query encoding (spaces → `+`) and token validity.

### 2) Scraping failures
Common causes:
- JavaScript-rendered sites: curl yields boilerplate; Playwright needed.
- Blocks: Cloudflare/captcha/subscribe walls.

Signal-extractor rules:
- Use Playwright fallback when curl output <500 chars or contains block phrases.
- Use Playwright-first for the URL patterns listed above.

### 3) Playwright timeouts
- If you see `Timeout 60000ms exceeded`, reduce the `wait_until` strictness (already using `domcontentloaded`) or choose alternate sources.
- Some sites may require login/cookies; treat as `BLOCKED`.

### 4) WhatsApp gateway disconnects
You may see periodic:
- status 428 / 408 / 503 disconnects then reconnects.
These are usually transient transport/session issues.

Restart command (correct for this project):
```bash
pkill -f clawdbot-gateway && sleep 2 && clawdbot-gateway &
```

### 5) Where to look for logs/artifacts
During ad-hoc debugging, temporary artifacts are often written to `/tmp` (e.g., `brave_*.txt`, `intel_*_signal_report.json`). The orchestrator itself is intended to keep state in memory.

---

## Security notes
- API tokens (e.g., Brave Search) should ideally live in config/env, not hard-coded into SKILL.md. Current implementation includes a token in the `digital-scout` command template.
- When sharing logs externally, redact tokens and any user/session identifiers.
