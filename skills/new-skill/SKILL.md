---
name: new-skill
description: Orchestrator that builds and deploys new SKILL.md files for Adam. Triggered when the user types /new-skill followed by a plain English description of what the skill should do. Automatically chains skill-intake, skill-designer, skill-writer, and skill-deployer in sequence, passing only direct input to each stage.
---

## Skill Builder Orchestrator

You are the **single user-facing entry point** for the skill builder pipeline.

Hard rule: building new skills should be done via `/new-skill` (not `/vibe`, not `skillmd-builder-agent`). Your single responsibility is to chain the 4 sub-skills in strict sequence, pass only the direct output of each stage to the next, handle all rejection and failure states, and keep the user informed at every stage.

### Input
The user's plain English description provided after /new-skill.

### Pipeline

Global settings (hard critic):
- CRITIC_MODE: HARD (block commit and route back)
- RETRY_LIMIT_DEFAULT: 2 (Stages 0/2/4)
- RETRY_LIMIT_WRITE: 3 (Stage 3 — Write)
- Retry semantics: on critic failure, **re-run the same stage** with the same inputs plus the critic failure reason as an added constraint. If the retry limit is exceeded, abort cleanly with the blocking issue.

STAGE 0 — DISCIPLINED-INQUIRY PREFLIGHT
Announce: "⚙️ Stage 0 — Preflight: tightening your request..."
Goal: transform the user's raw description into a focused, evidence-aware request so the pipeline can build a better skill *without* requiring the user to format anything manually.

ANTI-CRASH STANDARD (MANDATORY)
- Detect multi-stage workflows early. If the user request includes multiple logical stages (e.g., extract + transform + store + analyze), do NOT design a single monolithic skill.
- Instead, either:
  1) Split the request into multiple single-responsibility skills (preferred), each with one clear trigger and one responsibility; OR
  2) Ask the user exactly one confirmation question: "This workflow has multiple stages. Do you want it split into separate skills?"
- Guiding principle: "Monolithic skills die silently. Modular skills complete reliably."

Process (internal; do not output the full structure unless the user asks):
- TOPIC: "I am working on building a new skill that [does X]"
- Generate 2–4 HOW/WHY guiding questions about what success means.
- Choose 1 guiding question.
- State the PROBLEM (why it matters to the user) + success criteria.
- Extract constraints (tools, environment, inputs/outputs, failure modes) from the user's text.
- Identify missing info that would block design.

Output of Stage 0 (this is what you pass to Stage 1):
- A single refined plain-English description (call it REFINED_DESCRIPTION) that includes:
  - what the skill does
  - trigger phrase
  - inputs/outputs expectations
  - constraints and non-goals
  - at least 1 example invocation

Stage 0 Critic Gate (HARD):
- Before proceeding, verify REFINED_DESCRIPTION contains all required bullets above.
- Verify every added detail is traceable to: (a) user message or (b) explicit prior stage output.
- If any check fails:
  - If user input is required: ask **one** clarifying question.
  - Else: re-run Stage 0 with the critic failure reason as a constraint.
  - Enforce RETRY_LIMIT_DEFAULT.

STAGE 1 — INTAKE
Announce: "⚙️ Stage 1 — Intake: analysing your request..."
Pass to skill-intake: REFINED_DESCRIPTION only.
Evaluate output:
- INTAKE_STATUS: CLARIFICATION_NEEDED → relay the QUESTION to the user, wait for reply, then:
  - update REFINED_DESCRIPTION by incorporating the user's reply (repeat Stage 0 quickly if needed), then re-run skill-intake
- INTAKE_STATUS: COMPLETE → proceed to Stage 2

Stage 1 Critic Gate (HARD):
- Verify the intake schema is COMPLETE and contains required fields (skill name, trigger, inputs/outputs, tools needed, constraints/non-goals).
- If not: force CLARIFICATION_NEEDED (no guessing). Re-run intake as many times as needed.

STAGE 2 — DESIGN
Announce: "⚙️ Stage 2 — Design: mapping to Adam's stack..."
Pass to skill-designer: the completed intake schema only.

Stage 2 Anti-crash rules (MANDATORY)
- Each skill must have ONE responsibility only.
- Do not chain multiple logical operations inside a single skill.
- Prefer multiple small skills over one large skill (split pipelines into separate skills).
Evaluate output:
- DESIGN_STATUS: REJECTED → output "❌ Pipeline aborted at Design: [REASON]" and stop. After delivering the failure message to the user, write an error log entry as specified in **Self-improvement logging (mandatory)**.
- DESIGN_STATUS: COMPLETE → proceed to Stage 3

Stage 2 Critic Gate (HARD):
- Verify every STEP has: TOOL, exact runnable COMMAND, and OUTPUT USED FOR.
- Verify all tools/commands are within Adam’s supported stack.
- Verify there are no placeholders or missing parameters.
- If any check fails, produce an internal failure report (do not show unless user asks):
  - FAIL_REASON: one sentence
  - MISSING: bullets
  - FIX_INSTRUCTION: one sentence
- Then re-run Stage 2 using the same intake schema plus FIX_INSTRUCTION as an added constraint (enforce RETRY_LIMIT_DEFAULT). If still failing, abort at Design with the blocking reason.

STAGE 3 — WRITE
Announce: "⚙️ Stage 3 — Writing: generating SKILL.md..."
Pass to skill-writer: the completed blueprint only.
Evaluate output:
- WRITER_STATUS: REJECTED → output "❌ Pipeline aborted at Write: [REASON]" and stop. After delivering the failure message to the user, write an error log entry as specified in **Self-improvement logging (mandatory)**.
- WRITER_STATUS: COMPLETE → proceed to Stage 4

Stage 3 Critic Gate (HARD):
- Verify SKILL_CONTENT:
  - Starts with valid YAML frontmatter (`---`) containing `name` and `description`.
  - Contains the exact trigger phrase in the description.
  - Has numbered, atomic steps.
  - Has no placeholder/TODO text.
  - Includes section: `## Agent Loop Contract (agentic skills only)`.
  - If blueprint has `HALLUCINATION_GUARDRAILS: on`, includes section: `## Anti-hallucination / context discipline` (per skill-writer rules).

- Anti-crash modularity gate (CRITICAL): Reject SKILL_CONTENT if any of the following are true:
  - It contains multiple responsibilities (extract + parse + save + notify, etc.) in one skill.
  - It implements a multi-stage pipeline internally.
  - It implies long execution time or large single-run output.
  - It includes overly long instructions (prefer concise SKILL.md).
  - It lacks best-effort / partial-output behavior where applicable.

- If any check fails, produce an internal failure report (do not show unless user asks):
  - FAIL_REASON: one sentence
  - MISSING: bullets
  - FIX_INSTRUCTION: one sentence (must push modular decomposition)
- Then re-run Stage 3 using the same blueprint plus FIX_INSTRUCTION as an added constraint (enforce RETRY_LIMIT_WRITE). If still failing, abort at Write with the blocking reason.

STAGE 4 — DEPLOY
Announce: "⚙️ Stage 4 — Deploying: saving to filesystem..."
Pass to skill-deployer: the SKILL_CONTENT only.
Evaluate output:
- DEPLOY_STATUS: FAILED → output "❌ Pipeline aborted at Deploy: [REASON]" and stop. After delivering the failure message to the user, write an error log entry as specified in **Self-improvement logging (mandatory)**.
- DEPLOY_STATUS: COMPLETE → output final confirmation, then write a learning log entry as specified in **Self-improvement logging (mandatory)**. This must not add any user-visible text.

Stage 4 Critic Gate (HARD):
- Treat deployment as the final commit. Do not proceed to deploy unless Stage 3 Critic Gate passed.

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

### Anti-hallucination / context discipline (mandatory)
This pipeline is prone to “contextual hallucination” when the model invents requirements, tools, or constraints that the user did not provide.

Guardrails:
- **Context-only:** treat the user’s request + the direct outputs of prior stages as the only allowed context. Do not import outside facts, tool capabilities, APIs, or conventions not present in the stage outputs.
- **Negative rejection (no guessing):** if required details are missing (domain, inputs/outputs, trigger, tools, constraints), do **not** guess. Force clarification by ensuring Stage 1 returns `INTAKE_STATUS: CLARIFICATION_NEEDED` and relay the question to the user.
- **Explicit context referencing (internal):** when refining the request in Stage 0, ensure every added detail is traceable to a specific phrase from the user message or an explicit stage output. If not traceable, omit it.
- **Scope control:** if the user request is out of scope for Adam’s environment/tools, prefer early rejection at Design (Stage 2) with a concrete reason rather than attempting a “best effort” invention.

### Rules
- Never skip a stage
- Never pass more than the direct output of the previous stage to the next
- Never deploy if any stage returns a rejection or failure
- Always announce each stage before executing it
- Always relay rejection reasons clearly to the user
- Re-run intake as many times as needed until INTAKE_STATUS: COMPLETE is reached

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
   - Run: `/new-skill <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/new-skill <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/new-skill/SKILL.md
```
Expected: `PASS`.
