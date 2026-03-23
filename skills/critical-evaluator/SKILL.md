---
name: critical-evaluator
description: Third stage of the /validate pipeline. Takes the evidence report from evidence-extractor and evaluates each claim with a verdict (SUPPORTED | CONTRADICTED | INSUFFICIENT EVIDENCE), a confidence score (1–5), and a 2–4 sentence reasoning note grounded strictly in the provided verbatim passages. UNTESTABLE FROM KB claims are preserved unchanged and marked EVALUATION SKIPPED. Called internally by the validate orchestrator; never triggered directly by the user.
---

# Critical Evaluator (internal)

## Trigger (internal)
- `critical-evaluator`

This sub-skill is **not** user-facing. It is invoked by the `/validate` orchestrator.

## Single responsibility
Consume the plain-text output of `evidence-extractor` and produce an **EVALUATION REPORT** that assigns, for every claim, an objective verdict + confidence + reasoning **using only the provided verbatim passages** (no external knowledge).

## Hard constraints
- MUST NOT call any tools, APIs, KB endpoints, web search, or browser.
- MUST NOT introduce any external knowledge, opinions, or facts not present in the provided passages.
- MUST NOT change or rewrite the original claim text.
- MUST evaluate every claim entry (no skipping).
- Verdict MUST be exactly one of: SUPPORTED, CONTRADICTED, INSUFFICIENT EVIDENCE.
- MUST include a confidence score (1–5) for every TESTABLE or PARTIALLY TESTABLE claim.
- MUST preserve UNTESTABLE FROM KB claims unchanged and mark them EVALUATION SKIPPED.
- Output must be plain text with clear section headers, directly parseable by `synthesis-compiler`.

## Input
The complete plain-text output of `evidence-extractor`, containing:
- EVIDENCE REPORT (one entry per claim)
- EVIDENCE SUMMARY

Each EVIDENCE REPORT entry includes (at minimum):
- Claim #
- Claim (verbatim claim text)
- Epistemic status
- Evidence status (e.g., OK / NO EVIDENCE FOUND / SOURCE FETCH FAILED) and/or extracted passage
- Extracted passage (verbatim) when available
- For UNTESTABLE FROM KB: Real-world evidence needed

## Output format (plain text; no markdown code blocks)
Must contain exactly these top-level sections, in this order:

1) EVALUATION REPORT
2) VALIDATION SUMMARY

### EVALUATION REPORT (one entry per claim, in claim-number order)
For each claim:

Claim #: <n>
Claim: <verbatim claim text>
Epistemic status: <TESTABLE|PARTIALLY TESTABLE|UNTESTABLE FROM KB>

If Epistemic status is TESTABLE or PARTIALLY TESTABLE:
Verdict: <SUPPORTED|CONTRADICTED|INSUFFICIENT EVIDENCE>
Confidence: <1|2|3|4|5>
Reasoning note:
<2–4 sentences grounded strictly in the provided passage(s) and/or evidence status.>

If Epistemic status is UNTESTABLE FROM KB:
Evaluation status: EVALUATION SKIPPED
Reason: No KB evidence available for this claim.
Real-world evidence needed: <verbatim note from input>

### VALIDATION SUMMARY (3–5 sentences)
Must include:
- Counts: total claims; evaluated (testable+partially testable); supported; contradicted; insufficient evidence; untestable.
- Overall assessment: strongly supported / partially supported / contested / unsupported.
- Next step guidance for Igor (actionable): what to test next, focusing on highest-importance claims with insufficient evidence or contradictions.

## Verdict rules (deterministic)
For TESTABLE / PARTIALLY TESTABLE claims:
1) If the evidence entry indicates `NO EVIDENCE FOUND` or `SOURCE FETCH FAILED` OR there is no verbatim passage available:
   - Verdict = INSUFFICIENT EVIDENCE
   - Confidence should be 1–2
2) If a verbatim passage directly affirms the claim’s proposition (explicitly or with clear, specific alignment):
   - Verdict = SUPPORTED
   - Confidence typically 4–5 depending on directness and specificity
3) If a verbatim passage directly refutes the claim’s proposition or recommends the opposite approach (clear conflict):
   - Verdict = CONTRADICTED
   - Confidence typically 4–5 depending on directness and specificity
4) Otherwise (passage is adjacent, generic, conditional, or addresses method but not truth of the claim):
   - Verdict = INSUFFICIENT EVIDENCE
   - Confidence typically 2–3

## Reasoning note rules
- Must reference specific phrases/ideas present in the verbatim passage (or explicitly reference the evidence status NO EVIDENCE FOUND / SOURCE FETCH FAILED).
- Must not extrapolate beyond the passage.
- Must not cite other books or general startup advice unless it appears in the passage.

## Confidence scoring rubric (1–5)
1 = Very low: no passage, fetch failed, or only tangential relation.
2 = Low: weak/indirect relation; mostly methodological guidance.
3 = Medium: some alignment/conflict but conditional or not explicit.
4 = High: clear alignment/conflict with specific statements.
5 = Very high: explicit, direct statements that squarely address the claim.

## Non-goals
- Do not generate new KB queries.
- Do not perform any KB search.
- Do not synthesize a final business recommendation beyond the constrained VALIDATION SUMMARY.

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
   - Run: `/critical-evaluator <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/critical-evaluator <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/critical-evaluator/SKILL.md
```
Expected: `PASS`.
