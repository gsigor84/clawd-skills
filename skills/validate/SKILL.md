---
name: validate
description: "Validate a business assumption by running a strict 4-stage evidence pipeline and returning a 5-section decision memo."
---

## Trigger contract

Activate when the user message matches either:
- `/validate <assumption>`
- `validate this assumption: <assumption>`

Where `<assumption>` is a single plain-English business assumption sentence or short paragraph.

Disambiguation:
- If the user provides multiple unrelated assumptions, treat it as invalid input (Failure modes).
- If `<assumption>` is empty or just whitespace, treat it as missing input.

## Deterministic agent workflow

This is an orchestrator skill. It must run four internal stages in order and pass only the previous stage output to the next stage.

Stages (strict order; never skip):
1) `assumption-deconstructor`
2) `evidence-extractor`
3) `critical-evaluator`
4) `synthesis-compiler`

### Step 0 — Announce start
Output exactly:
- `validating your assumption, this will take about 60 seconds.`

### Step 1 — Run assumption-deconstructor
Input: the raw `<assumption>` only.

Success criteria (must all be true):
- output contains `ORIGINAL ASSUMPTION`
- output contains `CORE CLAIMS`
- at least 2 claims are listed in CORE CLAIMS

If criteria fail → stop with Failure modes.

### Step 2 — Run evidence-extractor
Output exactly:
- `stage 2 of 4, searching knowledge base for evidence.`

Input: Step 1 output only (verbatim).

Success criteria:
- output contains `EVIDENCE REPORT`
- output contains at least 1 extracted evidence passage OR explicitly marks some claims as UNTESTABLE FROM KB

If all claims are `NO EVIDENCE FOUND` → stop with Failure modes.

### Step 3 — Run critical-evaluator
Output exactly:
- `stage 3 of 4, evaluating evidence against your assumption.`

Input: Step 2 output only.

Success criteria:
- output contains `EVALUATION REPORT`

If criteria fail → stop with Failure modes.

### Step 4 — Run synthesis-compiler
Output exactly:
- `stage 4 of 4, compiling your validation report.`

Input: Step 3 output only.

Success criteria:
- final output contains the five sections in order:
  1) `ASSUMPTION`
  2) `VERDICT`
  3) `EVIDENCE SCORECARD`
  4) `KEY FINDINGS`
  5) `RECOMMENDED ACTIONS`

If criteria fail → stop with Failure modes.

### Final output rule
On success, output the Step 4 output **verbatim** with no extra commentary.

## Boundary rules

- No external facts: never add facts not present in the pipeline outputs.
- No tool use: do not call web_search/web_fetch/exec/read/write/edit here.
- Privacy: treat the assumption as potentially sensitive; do not paste it into external searches.
- Deterministic routing: only the previous stage output may be provided to the next stage.

## Use

Use `/validate` when you want a strict, evidence-grounded validation memo for a single business assumption, including what is supported, what is contradicted, and what needs real-world testing.

## Inputs

- One assumption string.

Examples:
- `/validate Mid-market SaaS buyers will pay £49/month for a personal finance forecasting dashboard.`

## Outputs

On success: a plain-text memo with exactly five sections:
- ASSUMPTION
- VERDICT
- EVIDENCE SCORECARD
- KEY FINDINGS
- RECOMMENDED ACTIONS

On failure: one of the exact error strings in Failure modes.

## Failure modes

- Missing input:
  - `ERROR: missing assumption. Usage: /validate <single assumption>`

- Multiple assumptions detected:
  - `ERROR: provide exactly one assumption (one sentence/paragraph).`

- Stage 1 failed structure/too few claims:
  - `ERROR: could not deconstruct assumption into at least 2 testable claims. Provide more detail.`

- Stage 2 no evidence anywhere:
  - `ERROR: no relevant evidence found in knowledge base for any claim.`

- Stage 3 missing evaluation report:
  - `ERROR: evaluation stage failed. Try again.`

- Stage 4 missing final sections:
  - `ERROR: could not compile final validation report. Try again.`

## Toolset

- (none)

## Acceptance tests

1. **Happy path: single assumption**
   - Run: `/validate Customers will pay $20/mo for an AI email triage tool.`
   - Expected output: emits 4 status lines in order, then outputs a 5-section memo with headers in order (ASSUMPTION, VERDICT, EVIDENCE SCORECARD, KEY FINDINGS, RECOMMENDED ACTIONS).

2. **Missing input**
   - Run: `/validate`
   - Expected error message (exact): `ERROR: missing assumption. Usage: /validate <single assumption>`

3. **Multiple assumptions**
   - Run: `/validate Assumption A. Assumption B.`
   - Expected error message (exact): `ERROR: provide exactly one assumption (one sentence/paragraph).`

4. **No evidence anywhere**
   - Run: `/validate <assumption that yields no KB evidence>`
   - Expected error message (exact): `ERROR: no relevant evidence found in knowledge base for any claim.`

5. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/validate/SKILL.md
```
Expected: `PASS`.

6. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/validate/SKILL.md
```
Expected: `PASS`.
