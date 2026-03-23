---
name: learn-compare
description: "Trigger: /learn-compare. Runs source-only /learn-style study guide, then optional Brave-augmented context under strict caps, and outputs a comparison + merged final guide with clear provenance."
---

## /learn-compare — Source vs Augmented study guide (with comparison)

### Trigger
- `/learn-compare <file-path-or-url>`
- or `/learn-compare` with a single attached file (PDF, TXT, DOCX, MD)

### Flags
- `--augment` (default: true)
- `--count <n>` (default: 5; clamp 1..10)
- `--country <code>` (default: ALL)
- `--freshness <day|week|month|year>` (default: none)

### Hard requirements (non-negotiable)
- **/learn baseline is sacred:** always generate the baseline study guide using ONLY the provided source text.
- **Strict separation:** any external info must be confined to clearly labeled sections and must not contaminate the baseline content.
- **Tool budgets:**
  - If `--augment=false`: **0** `web_search` calls, **0** `web_fetch` calls.
  - If `--augment=true`: exactly **1** `web_search` call, and at most **3** `web_fetch` calls.
- **No full-page dumps:** never paste full fetched pages; summarize only.
- **Rate limits:** if Brave returns **429 RATE_LIMITED**, skip augmentation and continue with baseline-only output (no retries/loops).
- **Always cite URLs** for any external context.

### Output structure (must follow)
Your final output must have these top-level sections, in order:

1) `## Baseline (source-only)`
2) `## External context (Brave)` (only if augment succeeded; otherwise a one-line note that it was skipped)
3) `## Comparison` (what the external context adds/changes; 5–10 bullets max)
4) `## Final study guide` (the full /learn-style study guide; baseline content + optional appended external section; provenance preserved)

---

## Procedure

### 1) Resolve input source
- If user provided a file path, use it.
- If user attached a file, use the first attachment.
- If input is a URL, fetch it.

### 2) Extract source text
- PDF:
  ```bash
  /opt/anaconda3/bin/python3 -c "from pdfminer.high_level import extract_text; import sys; print(extract_text(sys.argv[1]))" "FILE_PATH"
  ```
- DOCX:
  ```bash
  /opt/anaconda3/bin/python3 -c "import docx, sys; d=docx.Document(sys.argv[1]); print('\\n'.join(p.text for p in d.paragraphs))" "FILE_PATH"
  ```
- MD/TXT:
  ```bash
  cat "FILE_PATH"
  ```
- URL:
  - Use `web_fetch(url=URL, extractMode="markdown")` and treat that as the source text.

### 3) Build the baseline study guide (SOURCE-ONLY)
Follow `/learn` structure and constraints exactly:
- `STEP 1 — EXTRACT`
- `STEP 2 — IDENTIFY BACKBONE` (4–6)
- `STEP 3 — MAP RELATIONSHIPS` (complete mapping before questions)
- `STEP 4 — WRITE STUDY GUIDE`
  - scenario challenge question (never “what is/define”)
  - exactly two answer paragraphs per concept
  - paragraph length: **5–7 sentences**
  - use explicit connectors (“for example,” “in addition,” “consequently”)
  - each paragraph explicitly references the corresponding backbone concept

Output this entire baseline study guide under `## Baseline (source-only)`.

### 4) Optional augmentation with Brave (ONLY if `--augment=true`)
- Derive a short search query from:
  - source title + 2–4 backbone concepts
- Run exactly one:
  - `web_search(query=..., count=..., country=..., freshness=...)`
- Select up to 3 highest-signal URLs (prefer official docs/primary sources).
- Fetch each with `web_fetch(url=..., extractMode="markdown")`.
- Produce `## External context (Brave)` as 2–6 bullets per source, each bullet ends with the URL.

### 5) Comparison section
Under `## Comparison`, write 5–10 bullets answering:
- What did the external context add that the source did not contain?
- Which baseline concepts become clearer or need revision (if any)?
- Any contradictions found (if any) with citations.

Important: do NOT rewrite baseline content based on external context. Only *recommend* changes.

### 6) Final study guide
Under `## Final study guide`, output:
- The full baseline study guide (unchanged), and then
- Append `## External context (Brave)` (if available).

---

## Anti-lazy spec
### Acceptance criteria
1) Baseline contains no external claims.
2) Augment tool cap enforced: 1× `web_search`, ≤3× `web_fetch`.
3) External bullets include URLs.
4) No full-page dumps.
5) 429 → skip augmentation (no retries).

### Tests (must pass)
- `/learn-compare fixtures/learn_test_source.md --augment=false`
- `/learn-compare fixtures/learn_test_source.md --augment=true`
- `/learn-compare fixtures/learn_test_source.md --augment=true --country GB --freshness week`

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
   - Run: `/learn-compare <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/learn-compare <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/learn-compare/SKILL.md
```
Expected: `PASS`.
