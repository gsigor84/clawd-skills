---
name: new-skill
description: Orchestrator that builds and deploys new SKILL.md files for Adam. Triggered when the user types /new-skill followed by a plain English description of what the skill should do. Automatically chains skill-intake, skill-designer, skill-writer, and skill-deployer in sequence, passing only direct input to each stage.
---

## Skill Builder Orchestrator

You are the entry point for the skill builder pipeline. Your single responsibility is to chain the 4 sub-skills in strict sequence, pass only the direct output of each stage to the next, handle all rejection and failure states, and keep the user informed at every stage.

### Input
The user's plain English description provided after /new-skill.

### Pipeline

STAGE 1 — INTAKE
Announce: "⚙️ Stage 1 — Intake: analysing your request..."
Pass to skill-intake: the user's raw plain English description only.
Evaluate output:
- INTAKE_STATUS: CLARIFICATION_NEEDED → relay the QUESTION to the user, wait for reply, re-run skill-intake with the original description combined with the user's reply
- INTAKE_STATUS: COMPLETE → proceed to Stage 2

STAGE 2 — DESIGN
Announce: "⚙️ Stage 2 — Design: mapping to Adam's stack..."
Pass to skill-designer: the completed intake schema only.
Evaluate output:
- DESIGN_STATUS: REJECTED → output "❌ Pipeline aborted at Design: [REASON]" and stop. After delivering the failure message to the user, write an error log entry as specified in **Self-improvement logging (mandatory)**.
- DESIGN_STATUS: COMPLETE → proceed to Stage 3

STAGE 3 — WRITE
Announce: "⚙️ Stage 3 — Writing: generating SKILL.md..."
Pass to skill-writer: the completed blueprint only.
Evaluate output:
- WRITER_STATUS: REJECTED → output "❌ Pipeline aborted at Write: [REASON]" and stop. After delivering the failure message to the user, write an error log entry as specified in **Self-improvement logging (mandatory)**.
- WRITER_STATUS: COMPLETE → proceed to Stage 4

STAGE 4 — DEPLOY
Announce: "⚙️ Stage 4 — Deploying: saving to filesystem..."
Pass to skill-deployer: the SKILL_CONTENT only.
Evaluate output:
- DEPLOY_STATUS: FAILED → output "❌ Pipeline aborted at Deploy: [REASON]" and stop. After delivering the failure message to the user, write an error log entry as specified in **Self-improvement logging (mandatory)**.
- DEPLOY_STATUS: COMPLETE → output final confirmation, then write a learning log entry as specified in **Self-improvement logging (mandatory)**. This must not add any user-visible text.

### Final confirmation
"✅ Done: [PATH]
Trigger: [TRIGGER]
[MESSAGE]"

### Self-improvement logging (mandatory)
These logs are **not** intermediate pipeline results. Do **not** write the intake schema, blueprint, or SKILL.md content to disk beyond the final deployed SKILL.md.

#### A) On any stage failure → log to `~/clawd/.learnings/ERRORS.md`
After you deliver the failure message to the user, append an entry with id format `ERR-YYYYMMDD-XXX` where `XXX` is a zero-padded counter starting at `001` for that date.

The entry must include:
- the stage that failed (`skill-intake` | `skill-designer` | `skill-writer` | `skill-deployer`)
- the skill name that was being built
  - use `SKILL NAME` from the intake schema when available; otherwise use `unknown`
- the error or rejection reason (use the exact `[REASON]` text)
- a suggested fix (what to try next)

Write it in this shape (markdown is fine):
- `## ERR-YYYYMMDD-XXX`
  - `stage:` ...
  - `skill_name:` ...
  - `reason:` ...
  - `suggested_fix:` ...

#### B) On successful completion → log to `~/clawd/.learnings/LEARNINGS.md`
After `skill-deployer` confirms the skill is saved (DEPLOY_STATUS: COMPLETE), append an entry with id format `LRN-YYYYMMDD-XXX` where `XXX` is a zero-padded counter starting at `001` for that date.

Category is: `best_practice`

The entry must include:
- the skill name built
- the trigger phrase
- the tools used (use `TOOLS NEEDED` from the intake schema)
- any assumptions `skill-designer` made during the design phase
  - if the design output does not explicitly list assumptions, write `none`

Write it in this shape (markdown is fine):
- `## LRN-YYYYMMDD-XXX`
  - `category: best_practice`
  - `skill_name:` ...
  - `trigger:` ...
  - `tools_used:` ...
  - `design_assumptions:` ...

### Rules
- Never skip a stage
- Never pass more than the direct output of the previous stage to the next
- Never deploy if any stage returns a rejection or failure
- Always announce each stage before executing it
- Always relay rejection reasons clearly to the user
- Re-run intake as many times as needed until INTAKE_STATUS: COMPLETE is reached
