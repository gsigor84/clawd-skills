---
name: vibe
description: "DEPRECATED. Internal orchestrator prototype for skill building; use /new-skill instead. Not intended as a user entry point."
---

# vibe (orchestrator)

## Trigger contract

This skill is **deprecated**.

Do not trigger for normal users. Prefer `/new-skill`.

Accepted invocation patterns (operator/debug only):
- `/vibe <plain-English workflow description>`

Rules:
- The workflow description must be non-empty.
- This skill orchestrates other internal skills in a fixed order.
- This skill may require a second user turn if tool installation is needed (explicit confirmation).

## Use

Deprecated. Historical/experimental orchestrator for building+launching skills. Keep only for reference or operator debugging.

Primary entry point for building skills is `/new-skill`.

## Inputs

One string:
- `workflow` (required): plain-English description of what the user wants.

Example:
- `/vibe build a /sumurl command that takes one https url and returns 5 key points, main argument, 3 quotes, and caveats`

## Outputs

This skill outputs exactly one of the following:

### Output A — Missing input
If `workflow` is missing/whitespace, output exactly:
- `ERROR: missing_workflow. Usage: /vibe <plain-English workflow description>`

### Output B — Waiting for tool-install confirmation
If tools are missing and tool-installer requests approval, output exactly the `tool-installer` confirmation block (verbatim), and then stop.

### Output C — Final completion
On success or final failure, output exactly the `skill-launcher` output (verbatim). No extra lines.

## Deterministic workflow (must follow)

Tools used: none.

### Hard constraints (non-negotiable)
- Never skip a stage.
- Never change the stage order.
- Pass only the direct output of the previous stage to the next stage (no commentary, no wrappers).
- Never install anything without explicit user confirmation (handled by tool-installer).
- Do not invent stage outputs.
- Final response must be exactly the `skill-launcher` output (verbatim).

### Stage order (fixed)
1) `intent-parser`
2) `tool-auditor`
3) `tool-installer`
4) `skill-intake`
5) `skill-designer`
6) `skill-writer`
7) `skill-deployer`
8) `skill-launcher`

### Step 0 — Validate input
- If workflow missing/whitespace → Output A.

### Step 1 — intent-parser
- Input: the workflow text (everything after `/vibe`).
- Output: an INTENT DOCUMENT.

### Step 2 — tool-auditor
- Input: INTENT DOCUMENT (verbatim).
- Output: TOOL AUDIT REPORT (verbatim) including `VERDICT:`.

### Step 3 — tool-installer (branch)
Read `VERDICT:` from TOOL AUDIT REPORT and follow exactly one branch:

#### Branch 3A — VERDICT: ALL TOOLS READY
- Do not call tool-installer.
- Proceed to Stage 4 with the original INTENT DOCUMENT (verbatim).

#### Branch 3B — VERDICT: AUDIT INCOMPLETE
- Abort the pipeline.
- Output exactly:
  - `ERROR: tool_audit_incomplete. Rerun /vibe when tool checks can complete.`

#### Branch 3C — VERDICT: TOOLS MISSING
- Call tool-installer with the TOOL AUDIT REPORT (verbatim).

Then branch by tool-installer output:
- If tool-installer outputs an `INSTALL CONFIRMATION` block:
  - Output it verbatim (Output B) and stop (wait for user reply).
- If tool-installer outputs `INSTALLATION CANCELLED`:
  - Output it verbatim and stop.
- If tool-installer outputs `INSTALLATION FAILED`:
  - Output it verbatim and stop.
- If tool-installer outputs `INSTALLATION COMPLETE`:
  - Proceed to Stage 4 with the original INTENT DOCUMENT (verbatim).

### Step 4 — skill-intake
- Input: INTENT DOCUMENT (verbatim).
- Output: an intake schema.
- If `INTAKE_STATUS: CLARIFICATION_NEEDED`, output the intake schema verbatim and stop.

### Step 5 — skill-designer
- Input: intake schema (verbatim).
- Output: either `DESIGN_STATUS: REJECTED` or `DESIGN_STATUS: COMPLETE` blueprint.
- If rejected, output the rejection verbatim and stop.

### Step 6 — skill-writer
- Input: blueprint (verbatim).
- Output: either `WRITER_STATUS: REJECTED` or `WRITER_STATUS: COMPLETE` with SKILL_CONTENT.
- If rejected, output the rejection verbatim and stop.

### Step 7 — skill-deployer
- Input: skill-writer COMPLETE output (verbatim).
- Output: either `DEPLOY_STATUS: FAILED` or `DEPLOY_STATUS: COMPLETE`.
- If failed, output it verbatim and stop.

### Step 8 — skill-launcher
- Input: skill-deployer COMPLETE output (verbatim).
- Output: final user message.
- Output exactly that message (Output C).

## Failure modes

- Missing workflow:
  - `ERROR: missing_workflow. Usage: /vibe <plain-English workflow description>`

- Tool audit incomplete:
  - `ERROR: tool_audit_incomplete. Rerun /vibe when tool checks can complete.`

All other failures must be surfaced verbatim from the stage that produced them (no paraphrasing).

## Boundary rules (privacy + safety)

- Do not request secrets.
- Do not install tools without explicit confirmation (delegated to tool-installer).
- Do not write files directly in this orchestrator.
- Do not add any network/tool actions beyond invoking the fixed internal stages.

## Toolset

- (none)

## Acceptance tests

1. **Behavioral (negative): missing workflow hard-stop**
   - Run: `/vibe`
   - Expected output (exact): `ERROR: missing_workflow. Usage: /vibe <plain-English workflow description>`

2. **Behavioral: stage order is fixed (no skipping)**
   - Run: `/vibe build a simple summarizer skill`
   - Expected: the orchestrator invokes stages in the exact order listed under Stage order (intent-parser→tool-auditor→...→skill-launcher).

3. **Behavioral: tool audit incomplete aborts with exact error**
   - Given a TOOL AUDIT REPORT containing `VERDICT: AUDIT INCOMPLETE`, expected output is exactly:
     - `ERROR: tool_audit_incomplete. Rerun /vibe when tool checks can complete.`

4. **Behavioral: tools missing pauses and outputs tool-installer confirmation verbatim**
   - Given a TOOL AUDIT REPORT containing `VERDICT: TOOLS MISSING` and tool-installer returns `INSTALL CONFIRMATION ...`, expected:
     - `/vibe` outputs exactly that confirmation block and stops.

5. **Behavioral: pass-through invariants**
   - Expected: at every stage boundary, the next stage input is exactly the previous stage output with no added commentary, prefixes, or wrappers.

6. **Behavioral: final output is exactly skill-launcher output**
   - Given skill-launcher returns `SKILL READY: ...`, expected:
     - `/vibe` outputs exactly `SKILL READY: ...` with no extra lines.

7. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/vibe/SKILL.md
```
Expected: `PASS`.

8. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/vibe/SKILL.md
```
Expected: `PASS`.
