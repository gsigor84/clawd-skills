---
name: evidence-extractor
description: Second stage of the /validate pipeline. Takes the structured research brief from assumption-deconstructor, executes KB text-search queries for all TESTABLE/PARTIALLY TESTABLE claims against the local Open Notebook KB, fetches full source content for the top positive result, extracts verbatim passages (≤300 words) with book+author citations, and outputs a structured evidence report for critical-evaluator. Called internally by the validate orchestrator; never triggered directly by the user.
---

# Evidence Extractor (internal)

## Trigger (internal)
- `evidence-extractor`

This sub-skill is **not** user-facing. It is invoked by the `/validate` orchestrator.

## Single responsibility
Turn a structured research brief (from `assumption-deconstructor`) into an **EVIDENCE REPORT** by running the included KB search queries, fetching the top source for each query, and extracting **verbatim** passages relevant to each claim.

## Hard constraints
- MUST use Open Notebook search with `type` set to `text` (never `vector`).
- MUST use `limit: 6` and `search_sources: true`.
- MUST execute searches and source fetches using **explicit curl commands** (no env-var assumptions).
- MUST NOT paraphrase, summarize, or rewrite extracted passages — verbatim only.
- MUST NOT invent/hallucinate passages.
- MUST NOT skip any claim tagged TESTABLE or PARTIALLY TESTABLE.
- MUST preserve UNTESTABLE FROM KB claims unchanged, including their real-world evidence notes.
- Output must be plain text with clear section headers, parseable by `critical-evaluator`.

## Input
The complete plain-text output of `assumption-deconstructor`, containing:
- ORIGINAL ASSUMPTION
- CORE CLAIMS (numbered claims)
- RESEARCH BRIEF (per-claim entries including Epistemic status and KB search query when applicable)
- SUMMARY

## Tools / commands (supported stack)
### Search KB (per query)
```bash
curl -s -X POST http://127.0.0.1:5055/api/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"QUERY","type":"text","limit":6,"search_sources":true}'
```

### Fetch source (by id)
```bash
curl -s 'http://127.0.0.1:5055/api/sources/SOURCE_ID'
```

## Procedure

### 1) Parse the research brief
From the input text:
- Read CORE CLAIMS to map claim numbers → claim text.
- Read RESEARCH BRIEF and for each claim extract:
  - Claim #
  - Epistemic status
  - KB search query (only if TESTABLE / PARTIALLY TESTABLE)
  - Real-world evidence needed (only if UNTESTABLE FROM KB)

### 2) For each claim

#### A) If Epistemic status is UNTESTABLE FROM KB
- Do not search.
- Output an entry that preserves:
  - Claim #
  - Claim text
  - Epistemic status: UNTESTABLE FROM KB
  - Real-world evidence needed (verbatim)

#### B) If Epistemic status is TESTABLE or PARTIALLY TESTABLE
1. Run the KB search curl command with the claim’s query.
2. Evaluate results:
   - If `results` is empty → mark `NO EVIDENCE FOUND`.
   - If all `relevance` scores are ≤ 0 → mark `NO EVIDENCE FOUND`.
3. Otherwise select the **top scoring source**:
   - choose the result with the **highest positive** `relevance`.
4. Fetch the source with curl GET `/api/sources/SOURCE_ID`.
   - If source fetch fails or returns empty/blank `full_text` → mark `SOURCE FETCH FAILED` and include the raw search result titles as fallback citations.
5. Passage extraction (from `full_text`):
   - Find the most relevant passage(s) that directly speak to the claim.
   - Output exactly **one** verbatim passage per claim entry.
   - The passage must be **≤ 300 words**.
   - Prefer passages containing concrete guidance, frameworks, checklists, definitions, interview scripts, testing methods, or named concepts.

### 3) Book + author citation
For each extracted passage, include:
- Top source: <source title> — <book author>

If the author is not explicitly present in the source title, infer author only when it clearly matches one of the 13 known KB books:
- The Mom Test — Rob Fitzpatrick
- Running Lean — Ash Maurya
- The Four Steps to the Epiphany — Steve Blank
- Testing Business Ideas — Alexander Osterwalder
- Crossing the Chasm — Geoffrey Moore
- Blue Ocean Strategy — W. Chan Kim and Renée Mauborgne
- Positioning — Al Ries and Jack Trout
- Obviously Awesome — April Dunford
- Traction — Gabriel Weinberg and Justin Mares
- Founding Sales — Peter Kazanjy
- The Startup Owner's Manual — Steve Blank
- KNOWN — Mark Schaefer
- The Lean Startup — Eric Ries

If you cannot confidently map to an author, still output the source title and write `— (author unknown in KB metadata)`.

## Output format (plain text; no markdown code blocks)

EVIDENCE REPORT

Claim #: <n>
Claim: <verbatim claim text>
Epistemic status: <TESTABLE|PARTIALLY TESTABLE|UNTESTABLE FROM KB>
KB search query executed: <query string | N/A>
Top source: <title> — <author>
Evidence status: <OK|NO EVIDENCE FOUND|SOURCE FETCH FAILED>
Extracted passage (verbatim, ≤300 words):
<verbatim passage or N/A>
Real-world evidence needed:
<verbatim note or N/A>

(repeat one entry per claim, in claim-number order)

EVIDENCE SUMMARY
<2–3 sentences: count of claims searched, count untestable, count OK vs NO EVIDENCE FOUND vs SOURCE FETCH FAILED, and how well the KB covers the assumption>

## Edge cases
- Multiple claims pick the same top source: still fetch and extract separately per claim.
- If the claim’s query seems mismatched to the claim text, do **not** rewrite it; execute exactly what was provided.
- Never switch to vector search.

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
   - Run: `/evidence-extractor <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/evidence-extractor <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/evidence-extractor/SKILL.md
```
Expected: `PASS`.
