---
name: learn-augment
description: "Trigger: /learn-augment. Generates a /learn-style study guide from a provided source, with optional Brave-based external augmentation under strict caps and labeled output."
---

## /learn-augment — Study Guide (+ optional external context)

### Trigger
- `/learn-augment <file-path-or-url>`
- or `/learn-augment` with a single attached file (PDF, TXT, DOCX, MD)

### Flags
- `--augment` (default: false)
- `--count <n>` (default: 5; clamp 1..10) — Brave search results to consider
- `--country <code>` (default: ALL)
- `--freshness <day|week|month|year>` (default: none)

### Output (required)
- A structured Markdown study guide saved to: `~/clawd/learn/[source-title-lowercase-hyphenated]-study-guide.md`
- Then a confirmation message with the exact saved path and: `Run /ingest [path] to load this into your knowledge base.`

### Hard rules (do not violate)
- Never skip any step.
- **Strict separation:** the main study guide MUST be grounded only in the provided source text.
- If `--augment` is enabled, external info MUST appear only in a clearly labeled section titled exactly: `## External context (Brave)`.
- Never invent URLs; external links must come from `web_search` results or `web_fetch` sources.
- Never paste full fetched pages. Summarize external sources only.
- If Brave returns **429 RATE_LIMITED**, skip external context and proceed with source-only output. No retries/loops.

### Tool caps (non-negotiable)
- Without `--augment`: **0** `web_search` calls and **0** `web_fetch` calls.
- With `--augment`: exactly **1** `web_search` call, and at most **3** `web_fetch` calls.

---

## Procedure (follow exactly, in order)

1) **Resolve input source**
- If user provided a file path, use it. If URL, fetch it as text.
- If user attached a file, use the first attachment.
- Determine `EXT` from the filename extension: `pdf | docx | md | txt | url`.

2) **Extract source text**
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
  - Use `web_fetch(url=URL, extractMode="markdown")` and treat the fetched content as the source text.

3) **Generate the study guide (SOURCE-ONLY)**
- Follow the same STEP 1→4 structure as `/learn`:
  - `STEP 1 — EXTRACT`
  - `STEP 2 — IDENTIFY BACKBONE` (4–6)
  - `STEP 3 — MAP RELATIONSHIPS` (complete for all non-backbone concepts)
  - `STEP 4 — WRITE STUDY GUIDE` (scenario challenge question + exactly two answer paragraphs per concept)
- Maintain all `/learn` constraints:
  - no “what is/define” questions
  - exactly two answer paragraphs per concept
  - each paragraph should be **5–7 sentences** long
  - use explicit connectors (e.g., “for example,” “in addition,” “consequently”)
  - each paragraph explicitly references the corresponding backbone concept

4) **Optional augmentation (ONLY if `--augment`)**
- Append a new section:
  - `## External context (Brave)`
- Run exactly **one** `web_search` call using the best short query derived from:
  - the source title + 2–4 backbone concepts
- Select up to **3** URLs and fetch them with `web_fetch`.
- Summarize each fetched source in 2–4 bullets.
- Each bullet MUST include the URL in parentheses.
- Do NOT add external claims into the source-only steps above.

5) **STEP 5 — SAVE**
- Create directory if needed:
  ```bash
  mkdir -p /Users/igorsilva/clawd/learn
  ```
- Save to:
  - `/Users/igorsilva/clawd/learn/[source-title-lowercase-hyphenated]-study-guide.md`

6) **STEP 6 — CONFIRM**
- Tell the user the exact saved file path.
- Then say exactly:
  - `Run /ingest [path] to load this into your knowledge base.`

7) **STEP 7 — AUTO-INGEST (run after confirmation)**
- Automatically run `/ingest` on the saved study guide path.

---

## Anti-lazy spec
### Acceptance criteria
1) Without `--augment`: no `web_search`/`web_fetch` calls.
2) With `--augment`: exactly 1 `web_search`, ≤3 `web_fetch`.
3) External context is labeled exactly `## External context (Brave)` and contains URLs.
4) No external claims appear in STEP 1–4 content.
5) On 429: no retries; still produce the source-only study guide.

### Tests (must pass)
- `/learn-augment fixtures/learn_test_source.md`
- `/learn-augment fixtures/learn_test_source.md --augment`
- `/learn-augment fixtures/learn_test_source.md --augment --country GB --freshness week`

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
   - Run: `/learn-augment <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/learn-augment <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/learn-augment/SKILL.md
```
Expected: `PASS`.
