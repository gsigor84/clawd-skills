---
name: synthesis-compiler
description: "Compile a critical-evaluator report into a final 5-section /validate decision memo (no tools, no new facts)."
---

## Trigger contract

This is an internal pipeline skill used by `/validate`.

Trigger it when (and only when) the input payload is a **critical-evaluator output** that contains:
- a clearly marked assumption line/section (e.g. `ASSUMPTION:` or `ORIGINAL ASSUMPTION:`)
- an `EVALUATION REPORT` with one entry per claim

Accepted invocation patterns:
- Internal: the orchestrator calls the skill with the full critical-evaluator text as the message body.
- Manual debug (operator only): `/synthesis-compiler <paste critical-evaluator output>`

## Deterministic agent workflow

Tools: none. Single-pass text transform.

1) **Parse the assumption**
   - If the input contains a line starting with `ASSUMPTION:` or `ORIGINAL ASSUMPTION:` → extract everything after the colon as the assumption string.
   - Else set assumption string to `ASSUMPTION NOT PROVIDED IN INPUT`.

2) **Parse claim entries (ordered)**
   - Split the input into claim blocks by `Claim #` markers (or equivalent numbered claim headers).
   - For each claim block, extract:
     - claim number (required)
     - claim text (required)
     - epistemic status (TESTABLE | PARTIALLY TESTABLE | UNTESTABLE FROM KB)
     - verdict for testable claims (SUPPORTED | CONTRADICTED | INSUFFICIENT EVIDENCE)
     - confidence (1–5) for testable claims
     - reasoning note (verbatim-ish; do not expand)

3) **Compute overall verdict (deterministic)**
   - If any testable claim has verdict CONTRADICTED → overall verdict = `CONTESTED`.
   - Else if majority of testable claims are SUPPORTED with confidence >= 4 → `VALIDATED`.
   - Else if at least one claim is SUPPORTED and the rest are INSUFFICIENT EVIDENCE and/or UNTESTABLE FROM KB → `PARTIALLY VALIDATED`.
   - Else → `UNVALIDATED`.

4) **Emit final memo (exact 5 sections, exact order)**
   Output must be plain text with these headers:
   1. `ASSUMPTION`
   2. `VERDICT`
   3. `EVIDENCE SCORECARD`
   4. `KEY FINDINGS`
   5. `RECOMMENDED ACTIONS`

5) **Key findings rules (3–5 bullets)**
   - Every bullet must explicitly reference at least one claim number.
   - No external facts, no new evidence, no invented citations.

6) **Recommended actions rules (3–5 bullets)**
   - First action must address the highest-severity gap, in this priority order:
     1) any CONTRADICTED claim
     2) many INSUFFICIENT EVIDENCE claims
     3) many UNTESTABLE FROM KB claims
     4) otherwise: propose the smallest real-world test implied by the assumption

## Boundary rules

- Must not call tools.
- Must not add facts, examples, citations, or reasoning beyond what appears in the critical-evaluator input.
- Must not change the assumption wording (if provided).
- Must include every claim in the Evidence Scorecard (no omissions).

## Use

Use this skill as the final formatting and decision layer of `/validate`: it turns a structured evaluation report into a single memo Igor can act on immediately.

## Inputs

A single plain-text blob: the full output of `critical-evaluator`.

Required fields inside that blob:
- an assumption line/section (`ASSUMPTION:` or `ORIGINAL ASSUMPTION:`) OR it will be treated as missing
- an evaluation report with claim entries that include verdict/confidence for testable claims

## Outputs

Plain text memo with exactly five sections in order:

ASSUMPTION
<one line>

VERDICT
**<VALIDATED|PARTIALLY VALIDATED|CONTESTED|UNVALIDATED>**

EVIDENCE SCORECARD
- Claim #n: <claim text>
  - Status: <SUPPORTED|CONTRADICTED|INSUFFICIENT EVIDENCE|NEEDS REAL-WORLD TESTING>
  - Confidence: <1–5|N/A>

KEY FINDINGS
- <bullet>

RECOMMENDED ACTIONS
- <bullet>

## Failure modes

- If the input does not contain any parseable claims, return exactly:
  - `ERROR: no claims found in input. Provide full critical-evaluator output.`

- If the input contains claims but no verdicts for testable claims, return exactly:
  - `ERROR: missing verdict/confidence in claim entries. Re-run critical-evaluator.`

## Toolset

- (none)

## Acceptance tests

1. **Behavioral: happy path (mixed claim set)**
   - Run: `/synthesis-compiler <critical-evaluator-output>`
   - Input fixture: 3 claims where verdicts are SUPPORTED(4), INSUFFICIENT EVIDENCE(3), UNTESTABLE FROM KB, and an `ASSUMPTION:` line.
   - Expected: output contains the 5 section headers in order (ASSUMPTION/VERDICT/EVIDENCE SCORECARD/KEY FINDINGS/RECOMMENDED ACTIONS); VERDICT is `**PARTIALLY VALIDATED**`; all 3 claims appear in EVIDENCE SCORECARD.

2. **Behavioral: contradiction forces CONTESTED**
   - Run: `/synthesis-compiler <critical-evaluator-output-with-contradicted-claim>`
   - Expected: VERDICT is exactly `**CONTESTED**`.

3. **Behavioral: missing assumption string**
   - Run: `/synthesis-compiler <critical-evaluator-output-without-assumption-line>`
   - Expected: ASSUMPTION section contains exactly `ASSUMPTION NOT PROVIDED IN INPUT`.

4. **Negative: no claims found**
   - Run: `/synthesis-compiler this is not an evaluation report`
   - Expected: returns exactly `ERROR: no claims found in input. Provide full critical-evaluator output.`

5. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/synthesis-compiler/SKILL.md
```
Expected: `PASS`.

6. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/synthesis-compiler/SKILL.md
```
Expected: `PASS`.
