---
name: assumption-deconstructor
description: First stage of the /validate pipeline. Takes a raw plain-English business assumption and outputs a structured research brief: explicit core claims (>=2), epistemic status (TESTABLE | PARTIALLY TESTABLE | UNTESTABLE FROM KB), KB text-search queries for testable claims (optimized for the 13 embedded startup books), and real-world evidence notes for untestable claims. Called internally by the validate orchestrator; never triggered directly by the user.
---

# Assumption Deconstructor (internal)

## Trigger (internal)
- `assumption-deconstructor`

This sub-skill is **not** user-facing. It is invoked by the `/validate` orchestrator.

## Single responsibility
Transform **one raw business assumption** into a clean, parseable **research brief** that the next stage (`evidence-extractor`) can run against the Open Notebook KB without further interpretation.

## Hard constraints
- Do **not** call any tools, APIs, search endpoints, KB queries, DuckDuckGo, or web scraping.
- Do **not** invent or guess evidence.
- Do **not** output final answers.
- Do **not** skip epistemic status tagging.
- Do **not** output fewer than **two** distinct claims for any assumption.
- Always flag **UNTESTABLE FROM KB** when a claim can’t be evaluated from the 13-book KB.
- Output must be plain text with clear section headers and unambiguous fields.

## Knowledge base scope (for query optimization only)
Queries must be keyword-optimized for these embedded books:
- The Mom Test (Fitzpatrick)
- Running Lean (Maurya)
- The Four Steps to the Epiphany (Blank)
- Testing Business Ideas (Osterwalder)
- Crossing the Chasm (Moore)
- Blue Ocean Strategy (Kim & Mauborgne)
- Positioning (Ries & Trout)
- Obviously Awesome (Dunford)
- Traction (Weinberg & Mares)
- Founding Sales (Kazanjy)
- The Startup Owner's Manual (Blank)
- KNOWN (Schaefer)
- The Lean Startup (Ries)

## Input
A single raw business assumption in plain English (may be vague or specific).

## Output format (plain text; no markdown code blocks)
Must contain exactly these sections, in this order:

1) ORIGINAL ASSUMPTION
2) CORE CLAIMS
3) RESEARCH BRIEF
4) SUMMARY

### Section rules
- **ORIGINAL ASSUMPTION**: echo verbatim.
- **CORE CLAIMS**: numbered list only (1., 2., 3., ...). Each claim is a clear declarative sentence. Never fewer than 2.
- **RESEARCH BRIEF**: one entry per claim, containing 4 fields:
  - Claim #: <number>
  - Epistemic status: TESTABLE | PARTIALLY TESTABLE | UNTESTABLE FROM KB
  - KB search query: <string> (only for TESTABLE/PARTIALLY TESTABLE; otherwise blank or N/A)
  - Real-world evidence needed: <brief note> (only for UNTESTABLE FROM KB; otherwise blank or N/A)
- **SUMMARY**: 1–2 sentences describing scope and counts (how many testable vs untestable).

## Epistemic status tagging guidance
- **TESTABLE**: The claim is directly addressable by concepts, frameworks, or guidance in the 13 books (e.g., customer discovery, positioning, channel testing, early adopters, willingness-to-pay methods).
- **PARTIALLY TESTABLE**: The books can inform it indirectly (analogy, heuristics, frameworks), but the claim still depends on context-specific facts.
- **UNTESTABLE FROM KB**: Requires primary research or external market data (e.g., “X% conversion in our market”, “our ICP is CTOs at Series A in London”, “trust is the biggest barrier in our niche”).

## Query generation rules (for TESTABLE/PARTIALLY TESTABLE claims)
- Produce a **specific** keyword query designed for `type:"text"` search with `limit:6`.
- Avoid single generic terms (e.g., avoid just “pricing”).
- Include:
  - the concept (e.g., willingness to pay, early adopters, problem/solution fit),
  - the mechanism (e.g., customer interviews, smoke test, channels, positioning),
  - and any domain nouns from the assumption (e.g., B2B founders, CTOs, Series A) *when they help retrieval*.

## Deconstruction procedure
1) Read the assumption once for gist.
2) Extract the explicit claim.
3) Surface implicit/bundled claims (at minimum: customer/problem, solution/approach, willingness/behavior, segment/channel/positioning, constraints).
4) Rewrite each as a clean claim sentence.
5) Tag epistemic status per claim.
6) For TESTABLE/PARTIALLY TESTABLE claims, draft a query.
7) For UNTESTABLE FROM KB claims, specify what evidence is needed (interviews, surveys, pricing tests, cohort data, market sizing, experiments).
8) Write the final structured output.

## Output length
- Aim ~300 words for 2–3 claims.
- Scale up to ~500 words for 5+ claims.

## Example (format only; do not reuse content verbatim)
ORIGINAL ASSUMPTION
<verbatim>

CORE CLAIMS
1. <claim>
2. <claim>
3. <claim>

RESEARCH BRIEF
Claim #: 1
Epistemic status: TESTABLE
KB search query: <query>
Real-world evidence needed: N/A

Claim #: 2
Epistemic status: UNTESTABLE FROM KB
KB search query: N/A
Real-world evidence needed: <note>

SUMMARY
<1–2 sentences with counts>

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
   - Run: `/assumption-deconstructor <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/assumption-deconstructor <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/assumption-deconstructor/SKILL.md
```
Expected: `PASS`.
