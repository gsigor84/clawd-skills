---
name: signal-extractor
description: "Stage 3 of /intel. Fetch every URL from a SOURCE MAP and extract concrete, vector-tagged signals with strict anti-hallucination, redaction, and bounded fetching."
---

# signal-extractor (internal)

## Trigger contract

This is an internal pipeline skill for `/intel`.

Trigger **only** when the message body is the full plain-text output of `digital-scout` and contains:
- `INTELLIGENCE TARGET`
- a `SOURCE MAP` section
- for each vector: `PRIORITY: <HIGH|MEDIUM|LOW>` and **1–3** `URL:` lines

Accepted invocation patterns:
- Internal (preferred): the orchestrator calls `signal-extractor` with the full `digital-scout` output.
- Manual debug (operator only): `/signal-extractor <paste digital-scout output>`

If the input does not contain a parseable `SOURCE MAP` with at least one URL, fail with the exact error in **Failure modes**.

## Deterministic workflow (must follow)

### Tooling
- Primary fetch: `web_fetch`
- Fallback fetch: `exec` (Playwright via `/opt/anaconda3/bin/python3`)

### Global caps (hard limits)
- Max vectors processed: **25** (if more, fail)
- Max URLs processed: **75** total (if more, fail)
- Per-URL fetch attempts: **2** (web_fetch, then optional Playwright)
- `web_fetch` maxChars: **12000**
- Playwright navigation timeout: **30000 ms**

### Step 1 — Parse and validate input
1) Extract `INTELLIGENCE TARGET` value exactly as provided.
2) Parse `SOURCE MAP` into an ordered list of vectors. For each vector, capture:
   - `Vector Name`
   - `PRIORITY` (must be HIGH|MEDIUM|LOW)
   - URLs (from `URL:` lines)
3) Hard validation:
   - If `SOURCE MAP` missing → Failure.
   - If any vector has 0 URLs → Failure.
   - If total vectors > 25 or total URLs > 75 → Failure.

### Step 2 — URL allow/deny gating (hard safety)
Before fetching any URL, apply these deterministic rules:

#### 2A) Allowed schemes
- Only allow `http://` and `https://`.

#### 2B) Hard-deny hosts / private networks
Hard block (do not fetch) any URL whose host matches any of:
- `localhost`, `127.0.0.1`, `0.0.0.0`, `::1`
- any host ending with: `.local`, `.internal`, `.lan`, `.home`, `.corp`

Also hard block URLs that appear to target RFC1918/private ranges (string-prefix heuristic, case-insensitive):
- host starts with `10.`
- host starts with `192.168.`
- host starts with `172.16.` through `172.31.` (heuristic: host starts with `172.` and second octet is between 16 and 31)

If blocked:
- Do not call any tools for that URL.
- Mark the source as `EXTRACTION QUALITY: FAILED`, `FAILURE REASON: ERROR`, and include `SIGNALS: - (none)`.

#### 2C) Optional allowlist from upstream
If the input contains a line:
- `ALLOWED_DOMAINS: <comma-separated domains>`

Then additionally enforce:
- Only fetch URLs whose host is exactly one of those domains, or a subdomain of one of those domains.
- If a URL is outside the allowlist, treat it as blocked (same handling as above).

### Step 3 — For each URL, fetch readable text
Process vectors in the same order as the `SOURCE MAP`. For each URL that is not blocked:

#### 3A) Decide fetch strategy (Playwright-first heuristic)
Use **Playwright first** (skip `web_fetch`) only if URL path contains any of:
- `/product/` or `/products/`
- `/help/` or `/support/`
- `/features/`
- `/enterprise/`

Also use Playwright first if:
- path contains `/pricing/` AND the URL host appears to be the target’s own domain (heuristic: the host string appears inside `INTELLIGENCE TARGET` case-insensitively)

Otherwise default to `web_fetch` first.

#### 3B) Primary fetch (web_fetch)
Call:
- `web_fetch(url=<url>, extractMode="markdown", maxChars=12000)`

After `web_fetch`, evaluate **insufficiency/block**. If any are true, run Playwright fallback:
- Extracted text length (after trimming) < **800** characters
- Contains any of these block/paywall signals (case-insensitive substring match):
  - `enable javascript`
  - `access denied`
  - `subscribe`
  - `cloudflare`
  - `captcha`
  - `verify you are human`

#### 3C) Fallback fetch (Playwright via exec)
Run exactly (substitute URL):

```bash
/opt/anaconda3/bin/python3 -c "from playwright.sync_api import sync_playwright
import re
url='URL'
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=30000)
        content = page.content()
    except Exception as e:
        print('PLAYWRIGHT_ERROR: ' + str(e))
        browser.close()
        raise
    browser.close()
text = re.sub(r'<[^>]+>', ' ', content)
text = re.sub(r'\\s+', ' ', text).strip()
print(text[:12000])"
```

Interpretation:
- If the command prints a line starting with `PLAYWRIGHT_ERROR:` → treat as fetch failure.
- Otherwise treat stdout as fetched text.

### Step 4 — Extract signals (context-only + redaction)
For each URL’s final fetched text:

1) Extract **3–7** signals when possible.
2) Each signal MUST:
   - Be exactly one sentence.
   - Begin with the vector tag: `[<Vector Name>] `
   - Contain at least one concrete data point (examples: a price, tier name, numeric limit, date, named integration/partner, quoted complaint with specifics, version number).
3) Disallow vague signals:
   - If a candidate signal does not contain concrete detail, do not output it.

#### Redaction (hard privacy boundary)
Before outputting any signal, apply this deterministic redaction rule:
- If the signal text contains any of these case-insensitive substrings:
  - `api key`, `secret`, `token`, `password`, `bearer`, `private key`
  - or contains a PEM marker like `BEGIN PRIVATE KEY`

Then **do not output** that signal. (Skip it; do not attempt to paraphrase.)

If you cannot produce ≥1 non-sensitive concrete signal, the source must become `FAILED` with `FAILURE REASON: EMPTY`.

4) If you can only extract 1–2 truly concrete, non-sensitive signals, output those and mark `WEAK`.

### Step 5 — Assign extraction quality
For each URL, set:
- `STRONG` if ≥ 3 signals
- `WEAK` if 1–2 signals
- `FAILED` if:
  - blocked by allow/deny rules, OR
  - fetch produced no usable text after allowed attempts, OR
  - redaction rules eliminate all otherwise-valid signals

If `FAILED`, set `FAILURE REASON` to exactly one of:
- `BLOCKED` (block/paywall/captcha signals from fetched content)
- `EMPTY` (returned too little meaningful text OR no non-sensitive signals after redaction)
- `TIMEOUT` (Playwright timeout)
- `ERROR` (blocked by URL allow/deny OR any other failure)

### Step 6 — Emit output (strict schema)
Output must be structured **plain text** with the following sections and headings **exactly** in this order:

## INTELLIGENCE TARGET
<Target exactly as provided>

## SIGNAL REPORT

### Vector — <Vector Name>
PRIORITY: <HIGH|MEDIUM|LOW>

#### Source <n>
URL: <url>
FETCH METHOD: <WEB_FETCH|PLAYWRIGHT>
SIGNALS:
1) [<Vector Name>] <signal>
2) ...

If EXTRACTION QUALITY is FAILED, replace the list with exactly:
- `SIGNALS:`
- `- (none)`

EXTRACTION QUALITY: <STRONG|WEAK|FAILED>
FAILURE REASON: <BLOCKED|EMPTY|TIMEOUT|ERROR>  (only if FAILED)

(Repeat per URL; repeat per vector; preserve SOURCE MAP order.)

## EXTRACTION SUMMARY
3–5 sentences including:
- total URLs
- succeeded count
- Playwright-used count
- failed count
- which vectors are strongest/weakest by coverage

## Use

Use this sub-skill inside `/intel` after `digital-scout` has produced a `SOURCE MAP`. It fetches each URL (subject to safety deny rules), extracts concrete, vector-tagged signals grounded in the fetched text, and reports failures explicitly (no hallucinations).

## Inputs

One plain-text blob: the full output from `digital-scout`, containing:
- `INTELLIGENCE TARGET`
- `SOURCE MAP` with vectors + priorities + URLs
- Optional: `ALLOWED_DOMAINS: ...` allowlist line

## Outputs

A structured plain-text report with:
- `## INTELLIGENCE TARGET`
- `## SIGNAL REPORT` (every URL included exactly once)
- `## EXTRACTION SUMMARY`

## Failure modes

Hard-stop failures (priority HIGH):
- Missing/invalid SOURCE MAP:
  - `ERROR: invalid_source_map. Provide full digital-scout output with INTELLIGENCE TARGET and SOURCE MAP.`
- Too many vectors/URLs:
  - `ERROR: source_map_too_large. Max 25 vectors and 75 URLs.`
- Malformed SOURCE MAP:
  - `ERROR: malformed_source_map. Each vector must include PRIORITY and at least one URL.`

Partial/blocked states (priority MEDIUM):
- Not a hard-stop in this skill’s public contract, but treat high failure rates as “partial” for logging:
  - if a run completes structurally but yields `EXTRACTION QUALITY: FAILED` for all URLs, treat as `status: partial` for logging purposes.

### Deterministic ERR logging via /self-improving-agent (mandatory on failures/partials)

Write ERR entries via `/self-improving-agent` for:

Hard-stop failures (priority HIGH):
- Any run that outputs an `ERROR: ...` line.

Partial/blocked states (priority MEDIUM):
- Any run that completes structurally but yields `EXTRACTION QUALITY: FAILED` for **all** URLs (no signals extracted anywhere).

Never log secrets or large payloads:
- Do not copy fetched page contents.
- Do not include tokens/headers.

#### Exact /self-improving-agent call format (ERR)

Call (single line):
- `/self-improving-agent error | <one-line summary> | details: <details> | files: skills/signal-extractor/SKILL.md`

The logged ERR entry must include these fields (keep short; no payloads):
- `Pattern-Key:` use the exact key from the mapping table below
- `Recurrence-Count:` start at `1`
- `First-Seen:` and `Last-Seen:` set to today

Context fields to include inside the entry:
- `stage: signal-extractor`
- `priority: high|medium`
- `status: hard_stop|partial`
- `reason:` one-line reason (include the exact ERROR line if present)
- `intelligence_target:` extracted target
- `vectors_total:` integer
- `urls_total:` integer
- `urls_failed:` integer
- `urls_succeeded:` integer
- `playwright_used_count:` integer
- `allowed_domains:` if present; else empty
- `suggested_fix:` one line

#### Pattern-Key mapping (use exact key)

| Condition | Pattern-Key | priority | status |
|---|---|---|---|
| `ERROR: invalid_source_map...` | `signal-extractor:invalid_source_map` | high | hard_stop |
| `ERROR: source_map_too_large...` | `signal-extractor:source_map_too_large` | high | hard_stop |
| `ERROR: malformed_source_map...` | `signal-extractor:malformed_source_map` | high | hard_stop |
| all URLs `EXTRACTION QUALITY: FAILED` | `signal-extractor:all_urls_failed` | medium | partial |

## Boundary rules (privacy + safety)

- Never invent URLs or signals.
- Fetch only from the URLs in the SOURCE MAP.
- Do not follow links discovered on pages.
- Enforce URL allow/deny gating (Step 2).
- Enforce redaction by skipping any secret-like signals (Step 4).
- Caps are mandatory; no retry loops.

## Toolset

- `web_fetch`
- `write`
- `exec`

## Acceptance tests

1. **Negative: missing SOURCE MAP**
   - Input: `hello` (no INTELLIGENCE TARGET / SOURCE MAP).
   - Expected output is exactly:
     - `ERROR: invalid_source_map. Provide full digital-scout output with INTELLIGENCE TARGET and SOURCE MAP.`

2. **Negative: too many URLs**
   - Input: a SOURCE MAP containing 76 URLs.
   - Expected output is exactly:
     - `ERROR: source_map_too_large. Max 25 vectors and 75 URLs.`

3. **Behavioral: blocked localhost URL still reported (no skip)**
   - Run: `/signal-extractor <paste a digital-scout SOURCE MAP containing URL: http://127.0.0.1/private>`
   - Expected in output:
     - That URL appears under SIGNAL REPORT.
     - `EXTRACTION QUALITY: FAILED`
     - `FAILURE REASON: ERROR`
     - `SIGNALS:` followed by `- (none)`

4. **Behavioral: allowlist blocks out-of-scope domains**
   - Input fixture includes:
     - `ALLOWED_DOMAINS: example.com`
     - a URL `https://not-example.com/x`
   - Expected:
     - That URL is present and marked `FAILED` with `FAILURE REASON: ERROR` and `SIGNALS: - (none)`.

5. **Behavioral: structure and ordering is stable**
   - Input fixture with 2 vectors and 3 URLs total.
   - Expected:
     - Vectors appear in the same order as SOURCE MAP.
     - Exactly 3 `URL:` lines appear in the output.
     - Each URL appears exactly once.

6. **Behavioral: redaction skips secret-like signals**
   - Given a fetched page text containing `api key`/`token`-style strings, expected:
     - No signal line includes those secret markers.
     - If all candidate signals are removed by redaction, source becomes `FAILED` with `FAILURE REASON: EMPTY`.

7. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/signal-extractor/SKILL.md
```
Expected: `PASS`.

8. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/signal-extractor/SKILL.md
```
Expected: `PASS`.
