---
name: url-arg-summarizer
description: "Summarise a single webpage URL into key points, main argument, supporting quotes, and caveats using web_fetch only (context-only, no guessing)."
---

# url-arg-summarizer

## Trigger contract

Trigger when the user provides exactly one HTTP(S) URL.

Accepted invocation patterns:
- `/url-arg-summarizer <url>`
- `/url-arg-summarizer <url> | focus: <optional instructions>`

Rules:
- Only one URL is supported per run.
- If the message contains multiple URLs, hard-stop with the exact error in **Failure modes**.

## Use

Use this skill to quickly understand what a webpage is arguing and how it supports that argument, without adding any outside facts. Output includes key points, the main argument, verbatim supporting quotes, and caveats/unknowns.

## Inputs

One plain-text line containing:
- a single `http://` or `https://` URL
- optional focus instructions (anything after `| focus:`)

Examples:
- `/url-arg-summarizer https://example.com/article`
- `/url-arg-summarizer https://example.com/report | focus: assumptions, evidence, and what is missing`

## Outputs

A plain-text report with these headings **exactly** and in this order:

1) `KEY POINTS`
- 5–10 bullets.

2) `MAIN ARGUMENT`
- 2–3 sentences.

3) `SUPPORTING QUOTES`
- Exactly 3 quote blocks, each with:
  - `Quote: "..."`
  - `Where: <best-available location>`

4) `CAVEATS / UNKNOWNS`
- 3–8 bullets.

Constraints:
- Context-only: derive everything strictly from fetched page text.
- No guessing: if the page text does not support a claim, do not invent it.

## Deterministic workflow (must follow)

### Tooling
- `web_fetch`

### Global caps (hard limits)
- Max fetched characters: **20000**
- Max quote length: **240** characters per quote
- Max output length target: **~350 words** excluding quotes (if over, shorten KEY POINTS first)

### Boundary rules (privacy + safety)

- Only fetch the single provided URL.
- Never fetch non-http/https URLs.
- Never fetch localhost or private network targets. Hard block if host matches any of:
  - `localhost`, `127.0.0.1`, `0.0.0.0`, `::1`
  - any host ending with `.local`, `.internal`, `.lan`, `.home`, `.corp`
- Do not follow links discovered on the page.
- Do not include any secrets: if fetched text includes strings like `api key`, `token`, `password`, or `BEGIN PRIVATE KEY`, do not quote them.

### Step 1 — Parse input
1) Extract URL.
   - URL is the first token that starts with `http://` or `https://`.
2) Extract optional focus instructions.
   - If the input contains `| focus:` then everything after it (trimmed) is `FOCUS`.
   - Otherwise `FOCUS` is empty.
3) If more than one URL appears → fail.

### Step 2 — Fetch
Call:
- `web_fetch(url=<url>, extractMode="markdown", maxChars=20000)`

If fetched content is unusable (any condition true):
- length after trimming < **1200** characters
- contains any of these block signals (case-insensitive substring match):
  - `enable javascript`
  - `access denied`
  - `captcha`
  - `cloudflare`
  - `subscribe to continue`

Then fail with the exact error in **Failure modes**.

### Step 3 — Extract (context-only)
From the fetched content:

1) KEY POINTS
- Produce 5–10 bullets.
- Prefer concrete claims (numbers, dates, names, explicit causal statements).
- If `FOCUS` is non-empty, prioritize points relevant to it.

2) MAIN ARGUMENT
- 2–3 sentences: what the author is trying to convince you of, and the primary reason(s) offered.
- If the page is not argumentative (e.g., directory/product landing), state the page’s purpose instead.

3) SUPPORTING QUOTES
- Select exactly 3 short verbatim quotes (≤240 chars each) that support the main argument or key points.
- For each quote, add `Where:` using the best available location signal from the extracted markdown:
  - Prefer nearby headings (e.g., lines starting with `#`, `##`, `###`).
  - If no headings exist, use `Where: body`.

4) CAVEATS / UNKNOWNS
- Include 3–8 bullets about:
  - missing evidence
  - unclear methodology
  - potential bias
  - extraction limitations (if the text appears incomplete)
  - what would be needed to validate claims

### Step 4 — Enforce no-guessing
If the fetched content does not contain enough material to produce 3 quotes and 5 key points without speculation:
- still output all headings
- reduce KEY POINTS count as needed
- put the missing items explicitly in `CAVEATS / UNKNOWNS`

## Failure modes

Return exactly one of the following lines and nothing else:

- Missing URL:
  - `ERROR: missing_url. Usage: /url-arg-summarizer <https-url> [| focus: ...]`

- Multiple URLs:
  - `ERROR: multiple_urls_not_supported. Provide exactly one URL.`

- Disallowed URL (non-http/https or private/localhost):
  - `ERROR: disallowed_url. Only public http(s) URLs are allowed.`

- Fetch failed or content blocked/too short:
  - `ERROR: fetch_failed_or_blocked. Could not extract sufficient readable content.`

## Toolset

- `web_fetch`

## Acceptance tests

1. **Behavioral (negative): missing URL**
   - Input: `/url-arg-summarizer`
   - Expected output (exact):
     - `ERROR: missing_url. Usage: /url-arg-summarizer <https-url> [| focus: ...]`

2. **Behavioral (negative): multiple URLs rejected**
   - Input: `/url-arg-summarizer https://a.com x https://b.com`
   - Expected output (exact):
     - `ERROR: multiple_urls_not_supported. Provide exactly one URL.`

3. **Behavioral (negative): localhost blocked**
   - Input: `/url-arg-summarizer http://127.0.0.1/test`
   - Expected output (exact):
     - `ERROR: disallowed_url. Only public http(s) URLs are allowed.`

4. **Behavioral: output headings are exact and ordered**
   - Input: any fetchable public URL.
   - Expected: output contains headings exactly in this order:
     - `KEY POINTS`
     - `MAIN ARGUMENT`
     - `SUPPORTING QUOTES`
     - `CAVEATS / UNKNOWNS`

5. **Behavioral: exactly three quote blocks**
   - Input: any fetchable long-form article URL.
   - Expected: under `SUPPORTING QUOTES`, there are exactly 3 occurrences of `Quote:` and exactly 3 occurrences of `Where:`.

6. **Behavioral: focus instructions change prioritization**
   - Input A: `/url-arg-summarizer <same-url>`
   - Input B: `/url-arg-summarizer <same-url> | focus: methodology, evidence, and what is missing`
   - Expected: Output B includes caveats/unknowns that mention evidence/methodology more explicitly than Output A.

7. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/url-arg-summarizer/SKILL.md
```
Expected: `PASS`.

8. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/url-arg-summarizer/SKILL.md
```
Expected: `PASS`.
