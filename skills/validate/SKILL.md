---
name: validate
description: Validates a plain-English business assumption by chaining four internal sub-skills in strict sequence—assumption-deconstructor → evidence-extractor → critical-evaluator → synthesis-compiler—and returning the final five-section validation report. Triggered when the user types /validate followed by a business assumption.
---

# Validate (orchestrator)

## Trigger
User types:
- `/validate <plain English business assumption>`

## Role
This is the **entry point** for the validation pipeline.

Single responsibility:
- Receive one raw business assumption from the user.
- Run four internal sub-skills **in strict sequence**.
- Pass **only the direct output** of each stage to the next stage.
- Deliver the final synthesis-compiler output to the user **verbatim** (no paraphrase, no extra commentary).

## Pipeline (must run in this exact order)
1) `assumption-deconstructor`
2) `evidence-extractor`
3) `critical-evaluator`
4) `synthesis-compiler`

## State handling
- Keep all intermediate state in memory.
- Do not write intermediate results to disk.

## Status messages (must match exactly)
- Before Stage 1: `validating your assumption, this will take about 60 seconds.`
- Before Stage 2: `stage 2 of 4, searching knowledge base for evidence.`
- Before Stage 3: `stage 3 of 4, evaluating evidence against your assumption.`
- Before Stage 4: `stage 4 of 4, compiling your validation report.`

## Execution algorithm

### Stage 1 of 4 — assumption-deconstructor
1) Emit status message:
   - `validating your assumption, this will take about 60 seconds.`
2) Call `assumption-deconstructor` with the **raw user assumption only**.
3) Capture output as `stage1_out`.
4) Validate `stage1_out`:
   - Must contain headers: ORIGINAL ASSUMPTION, CORE CLAIMS, RESEARCH BRIEF, SUMMARY.
   - Must contain **at least two** distinct claims in CORE CLAIMS.
5) Failure handling:
   - If fewer than two claims are produced:
     - Abort.
     - Tell user: the assumption could not be deconstructed into testable claims and ask them to provide more detail.
     - After delivering the failure message to the user, write an error log entry as specified in **Self-improvement logging (mandatory)**.

### Stage 2 of 4 — evidence-extractor
1) Emit status message:
   - `stage 2 of 4, searching knowledge base for evidence.`
2) Call `evidence-extractor` with **stage1_out only**.
3) Capture output as `stage2_out`.
4) Validate `stage2_out`:
   - Must contain headers: EVIDENCE REPORT and EVIDENCE SUMMARY.
5) Failure handling:
   - If the EVIDENCE REPORT indicates every searched claim is `NO EVIDENCE FOUND` (i.e., no evidence extracted anywhere):
     - Abort.
     - Tell user: the knowledge base does not contain relevant material for this assumption and suggest they try a different assumption or add relevant books to the knowledge base.
     - After delivering the failure message to the user, write an error log entry as specified in **Self-improvement logging (mandatory)**.

### Stage 3 of 4 — critical-evaluator
1) Emit status message:
   - `stage 3 of 4, evaluating evidence against your assumption.`
2) Call `critical-evaluator` with **stage2_out only**.
3) Capture output as `stage3_out`.
4) Validate `stage3_out`:
   - Must contain header: EVALUATION REPORT.
5) Failure handling:
   - If missing EVALUATION REPORT header:
     - Abort.
     - Tell user: the evaluation stage failed and to try again.
     - After delivering the failure message to the user, write an error log entry as specified in **Self-improvement logging (mandatory)**.

### Stage 4 of 4 — synthesis-compiler
1) Emit status message:
   - `stage 4 of 4, compiling your validation report.`
2) Call `synthesis-compiler` with **stage3_out only**.
3) Capture output as `stage4_out`.
4) Validate `stage4_out`:
   - Must contain all five required sections, in order:
     1) ASSUMPTION
     2) VERDICT
     3) EVIDENCE SCORECARD
     4) KEY FINDINGS
     5) RECOMMENDED ACTIONS
5) Failure handling:
   - If any section is missing or out of order:
     - Abort.
     - Tell user: the final report could not be compiled and to try again.
     - After delivering the failure message to the user, write an error log entry as specified in **Self-improvement logging (mandatory)**.

## Final output rule (hard constraint)
- When Stage 4 completes successfully: output **stage4_out exactly as-is** with **no additional commentary**.
- After delivering `stage4_out`, write a learning log entry as specified in **Self-improvement logging (mandatory)**. This must not add any user-visible text.

## Self-improvement logging (mandatory)
These logs are **not** intermediate pipeline results. Do **not** write deconstruction briefs, evidence reports, evaluation reports, or synthesis outputs to disk.

### A) On any stage failure → log to `~/clawd/.learnings/ERRORS.md`
After you deliver the failure message to the user, append an entry with id format `ERR-YYYYMMDD-XXX` where `XXX` is a zero-padded counter starting at `001` for that date.

The entry must include:
- the stage that failed (`assumption-deconstructor` | `evidence-extractor` | `critical-evaluator` | `synthesis-compiler`)
- the assumption that was tested (the raw `/validate ...` string)
- the error or rejection reason (use the exact failure condition text)
- a suggested fix (what the user should try next)

Write it in this shape (markdown is fine):
- `## ERR-YYYYMMDD-XXX`
  - `stage:` ...
  - `assumption:` ...
  - `reason:` ...
  - `suggested_fix:` ...

### B) On successful completion → log to `~/clawd/.learnings/LEARNINGS.md`
After `synthesis-compiler` delivers the final report, append an entry with id format `LRN-YYYYMMDD-XXX` where `XXX` is a zero-padded counter starting at `001` for that date.

Category is: `best_practice`

The entry must include:
- the original assumption tested
- the verdict (`VALIDATED`, `PARTIALLY VALIDATED`, `CONTESTED`, or `UNVALIDATED`)
- which claims had the strongest evidence
- which claims had insufficient evidence

Write it in this shape (markdown is fine):
- `## LRN-YYYYMMDD-XXX`
  - `category: best_practice`
  - `assumption:` ...
  - `verdict:` ...
  - `strongest_evidence_claims:` ...
  - `insufficient_evidence_claims:` ...

## Hard constraints (must never violate)
- Never skip a stage.
- Never pass more than the direct output of the previous stage to the next.
- **Context-only orchestration:** treat the previous stage output as the only allowed context for the next stage. Do not add facts, examples, numbers, definitions, or claims from your own knowledge.
- **Negative rejection (no guessing):** if any stage output is missing required structure/content, abort per failure handling. Do not “patch” or “complete” missing sections yourself.
- Never answer the assumption from memory or prior knowledge.
- Always run all four stages in sequence even if you think you know the answer.
- Always deliver synthesis-compiler output as the final response with no paraphrasing or summarizing.
