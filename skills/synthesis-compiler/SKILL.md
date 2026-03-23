---
name: synthesis-compiler
description: Fourth and final stage of the /validate pipeline. Takes the evaluation report from critical-evaluator and compiles it into a single dense actionable validation report for Igor: a headline verdict, an evidence scorecard covering every claim, key findings grounded in the evaluation, and specific recommended actions. Called internally by the validate orchestrator; never triggered directly by the user.
---

# Synthesis Compiler (internal)

## Trigger (internal)
- `synthesis-compiler`

This sub-skill is **not** user-facing. It is invoked by the `/validate` orchestrator.

## Single responsibility
Convert the structured output of `critical-evaluator` into a final, dense, actionable validation report Igor can read and act on immediately.

## Hard constraints
- MUST NOT call any tools, APIs, KB endpoints, web search, or browser.
- **Context-only:** the critical-evaluator output is the only allowed input. Do not add outside facts, examples, or interpretations that are not directly supported by the evaluation entries.
- **Negative rejection (no guessing):** if required inputs are missing (e.g., no EVALUATION REPORT), do not try to reconstruct; output must follow the existing rules (e.g., ASSUMPTION NOT PROVIDED IN INPUT) and actions must point upstream to fix the missing data.
- MUST NOT invent evidence, claims, or verdicts.
- MUST NOT change the original assumption text.
- MUST output exactly five sections in the exact order: ASSUMPTION, VERDICT, EVIDENCE SCORECARD, KEY FINDINGS, RECOMMENDED ACTIONS.
- VERDICT must be exactly one of: VALIDATED, PARTIALLY VALIDATED, CONTESTED, UNVALIDATED.
- EVIDENCE SCORECARD must include every claim from EVALUATION REPORT without omission.
- KEY FINDINGS must be grounded in the evaluation report (no external knowledge).
- RECOMMENDED ACTIONS must be specific to the assumption + evaluation gaps (no generic startup advice).
- Output must be plain text with clear section headers.

## Input
The complete plain-text output of `critical-evaluator`, containing:
- EVALUATION REPORT (one entry per claim)
- VALIDATION SUMMARY

Each claim entry includes:
- Claim #
- Claim (verbatim claim text)
- Epistemic status
- If TESTABLE/PARTIALLY TESTABLE: Verdict (SUPPORTED|CONTRADICTED|INSUFFICIENT EVIDENCE), Confidence (1–5), Reasoning note
- If UNTESTABLE FROM KB: Evaluation status EVALUATION SKIPPED + Real-world evidence needed

## Required output (plain text; no markdown code blocks)
Must contain the following five sections in this exact order.

### 1) ASSUMPTION
- Output the original assumption **exactly as stated by the user**.
- The assumption must be extracted from the input context.
  - Preferred: a line/section explicitly labeled `ORIGINAL ASSUMPTION` or `ASSUMPTION`.
  - If missing: output `ASSUMPTION NOT PROVIDED IN INPUT` (verbatim) and ensure the first recommended action is to fix upstream so the original assumption is included.

### 2) VERDICT
- Single bold headline verdict line with exactly one of:
  - **VALIDATED**
  - **PARTIALLY VALIDATED**
  - **CONTESTED**
  - **UNVALIDATED**

Verdict selection rules (deterministic; derived only from the evaluation report):
- If any TESTABLE/PARTIALLY TESTABLE claim has Verdict=CONTRADICTED → VERDICT = CONTESTED.
- Else if majority of TESTABLE/PARTIALLY TESTABLE claims are SUPPORTED with Confidence ≥4 AND none contradicted → VERDICT = VALIDATED.
- Else if at least one claim is SUPPORTED (any confidence) AND remaining are mix of INSUFFICIENT EVIDENCE and/or UNTESTABLE → VERDICT = PARTIALLY VALIDATED.
- Else (majority INSUFFICIENT EVIDENCE, or no supported claims) → VERDICT = UNVALIDATED.

### 3) EVIDENCE SCORECARD
A compact table or structured list that includes every claim.
For each claim:
- Claim #: <n>
- Claim summary: one sentence summary of the claim (do not contradict or expand beyond the claim text)
- Result:
  - If TESTABLE/PARTIALLY TESTABLE: SUPPORTED | CONTRADICTED | INSUFFICIENT EVIDENCE
  - If UNTESTABLE FROM KB: NEEDS REAL-WORLD TESTING
- Confidence:
  - If TESTABLE/PARTIALLY TESTABLE: the numeric confidence from input (1–5)
  - If UNTESTABLE FROM KB: N/A

### 4) KEY FINDINGS
- Exactly 3–5 bullet points.
- Each bullet MUST be grounded in the evaluation report’s reasoning and must not introduce external facts.
- Each bullet should reference either:
  - the cited source book mentioned in the evidence/explanation (if present in the reasoning), OR
  - the real-world evidence note (for untestable claims), OR
  - the specific evaluation outcome (e.g., “insufficient evidence because NO EVIDENCE FOUND”).

### 5) RECOMMENDED ACTIONS
- Exactly 3–5 bullet points.
- Must be concrete and specific to the assumption and the highest-priority gap.
Priority rules:
1) If any claim is CONTRADICTED, the first action must address that contradiction directly (e.g., revisit the claim framing, run a targeted customer interview/test, or adjust the assumption).
2) Else if the biggest issue is INSUFFICIENT EVIDENCE (e.g., many claims with NO EVIDENCE FOUND / SOURCE FETCH FAILED), the first action must address evidence gaps (e.g., improve query specificity upstream, rerun extraction, or expand KB sources if that is part of the system).
3) Else if all evaluated claims are SUPPORTED with high confidence, the first action must be a forward step appropriate to the assumption (e.g., design the smallest test/MVP or a specific customer interview script) — but it must remain specific, not generic.
4) If any claims are UNTESTABLE FROM KB, include at least one action to collect the real-world evidence specified (e.g., pricing test, interviews with specified segment, pilot).

## Compilation procedure
1) Parse EVALUATION REPORT into an ordered list of claim entries.
2) Extract and freeze (verbatim) the assumption text from the input context (if present).
3) Compute verdict counts and apply VERDICT selection rules.
4) Create EVIDENCE SCORECARD (every claim included).
5) Write 3–5 KEY FINDINGS grounded strictly in the evaluation entries.
6) Write 3–5 RECOMMENDED ACTIONS following priority rules.
7) Output the five sections in the required order.

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
   - Run: `/synthesis-compiler <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/synthesis-compiler <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/synthesis-compiler/SKILL.md
```
Expected: `PASS`.
