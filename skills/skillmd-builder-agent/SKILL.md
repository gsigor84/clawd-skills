---
name: skillmd-builder-agent
description: Design and run a graph-constrained (finite state machine) agent that generates valid OpenClaw SKILL.md files from a user request. Use when Igor asks to create a new skill reliably (retrieve → draft → validate → repair), with deterministic validation and bounded autonomy. Triggers: “build a SKILL.md agent”, “skill generator”, “generate SKILL.md”, “create new OpenClaw skill”, “SKILL.md builder”.
---

# skillmd-builder-agent

## Use

Build **reliable SKILL.md files** by running a **constrained agent loop** (finite state machine) that:
- does boundary-aware intake (what problem are we solving, what is out of scope?)
- retrieves authoritative constraints + closest skill patterns
- drafts a behaviorally-specified SKILL.md (not just a skeleton)
- validates deterministically
- repairs with a bounded loop

### CST overlay (how this agent stays sane)
This builder treats “skill design” as a small **socio-technical system** and applies Critical Systems Thinking (CST) ideas:
- **Boundary critique:** define what the skill is responsible for vs what it must not do (side effects, external APIs, scope creep).
- **Systemic pluralism:** borrow heuristics/guardrails from 2–3 closest existing skills rather than relying on one template.
- **Feedback loops:** validation results feed directly into minimal repairs; strict stop conditions prevent infinite loops.
- **EPIC cycle:**
  - **Explore** = Intake + Retrieve + Boundary
  - **Produce** = Draft
  - **Intervene** = Write files + run checks
  - **Check** = Deterministic validation + acceptance tests

## Inputs

- User request describing the new skill:
  - goal / job-to-be-done
  - triggers (what the user will type)
  - allowed tools
  - inputs/outputs (files, formats)
  - constraints / safety / guardrails
- Optional: target folder path (default: `~/clawd/skills/<skill-name>/`)

## Outputs

- A new skill folder:
  - `~/clawd/skills/<skill-name>/SKILL.md`
  - optional scripts under `~/clawd/skills/<skill-name>/scripts/`
  - optional references under `~/clawd/skills/<skill-name>/references/`
- Deterministic validation results:
  - `validate_skillmd.py` PASS/FAIL
  - `check_no_invented_tools.py` PASS/FAIL

## Toolset

- `read` — load templates, policies, and example skills
- `write` — create new SKILL.md / scripts
- `edit` — apply minimal patches during repair
- `exec` — run deterministic validators and small shell checks
- `web_search` / `web_fetch` — only if the requested skill explicitly needs current external info (strict caps)

## Finite State Machine (FSM)

### State 0 — INTAKE (boundary + requirements)
**Goal:** capture the skill’s boundary and success definition before drafting.

**Actions:**
- Extract:
  - candidate `name` (kebab-case)
  - user-facing triggers (phrases + slash command)
  - allowed toolset
  - required outputs + formats
  - **non-goals / out-of-scope** (boundary critique)
  - must-pass acceptance criteria
- If critical info is missing: ask **ONE** clarifying question.

**Exit criteria:**
- request is sufficiently specified to draft without guessing.

### State 0.5 — CONSTRAINT_ARCHITECTURE (must/must-not/preferences/escalations)
**Goal:** convert the intake into a durable “rules file” structure so long-running agent work doesn’t drift.

**Actions:**
Create (in working notes) four buckets and fill each with 3–10 bullets:
- **Musts:** non-negotiable requirements (format, sections, caps, deterministic outputs).
- **Must-nots:** prohibited actions (unsafe writes/deletes, invented tools, web usage, etc.).
- **Preferences:** tie-breakers when multiple valid choices exist (brevity vs completeness, conservative filtering, etc.).
- **Escalation triggers:** when to stop and ask Igor (ambiguity, missing tool, unsafe side effect).

**Exit criteria:**
- at least 1 explicit escalation trigger exists.

### State 1 — RETRIEVE (authoritative constraints + systemic pluralism)
**Goal:** gather enough constraints + patterns to specify real behavior **without writing a monolithic prompt**.

**Required retrieval set:**
- The OpenClaw SKILL.md format constraints (frontmatter keys, required sections).
- Local project constraints (tool availability, integration guardrails).
- **2–3 closest skills** from `~/clawd/skills/` (same “type”):
  - match on IO shape (file→json, url→summary, orchestration, validator, etc.)
  - match on safety needs (writes, deletes, network access)

**Use retrieved skills as pattern references for:**
- heuristics (how to decide, what to skip)
- guardrails (what must never happen)
- exact error strings (when outputs are contractually strict)
- **behavioral acceptance tests** (runtime output), not just structural checks

**Exit criteria:**
- enough patterns to write concrete steps + failure handling.

### State 2 — DRAFT (Produce)
**Goal:** write SKILL.md that is structurally valid *and* behaviorally specific.

**Actions:**
- Frontmatter: exactly `name`, `description`.
- Body: must include sections:
  - `## Use`, `## Inputs`, `## Outputs`, `## Failure modes`, `## Acceptance tests`, `## Toolset`
- Add:
  - step-by-step procedure
  - failure modes with exact output strings if needed
  - guardrails (tool limits, write boundaries, no “rogue” behavior)
  - acceptance tests including at least one behavioral test

**Exit criteria:**
- draft SKILL.md created.

### State 3 — VALIDATE (Check)
**Goal:** detect violations deterministically, and prevent “looks-right” output from shipping.

**Actions:**
- Run:
  - `/opt/anaconda3/bin/python3 ~/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py <path>`
  - `/opt/anaconda3/bin/python3 ~/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py <path>`

**Exit criteria:**
- PASS → State 5
- FAIL → State 4 with concrete error list

### State 4 — REPAIR (bounded feedback loop)
**Goal:** minimal diffs to reach PASS without scope creep.

**Loop constraints:**
- Max iterations: **3**
- Each iteration must:
  - address only the reported failures
  - preserve the skill boundary
- After 3 failures: stop and ask Igor **ONE** decision question.

**Exit criteria:**
- validation PASS or hard-stop.

### State 5 — FINALIZE (Intervene + audit)
**Goal:** write deliverables and provide an audit trail.

**Actions:**
- Write final files to disk.
- Re-run validation.
- Report:
  - files created/changed
  - test commands to run

**Exit criteria:**
- Done.

## Failure modes

Hard blockers (stop immediately):
- The requested skill would require tools not available in this environment.
- The request implies unsafe side effects without explicit user approval (e.g., destructive deletes, external API writes) and no guardrails.
- Retrieval cannot find any relevant example skills and the request is ambiguous → ask 1 clarifying question.

Common failure patterns (and how to guardrail):
- **Skeleton-only skills:** missing heuristics/edge cases → enforce loading 2–3 closest skills in RETRIEVE.
- **Monolithic-spec rot:** huge, everything-is-important spec → force “constraint architecture” buckets + keep instructions minimal/high-signal.
- **God-agent creep:** too much autonomy → keep FSM states explicit; cap repair iterations.
- **Tool hallucination:** referencing non-existent tools → run `check_no_invented_tools.py`.
- **Looks-right shipping:** output is fluent but wrong → require behavioral acceptance tests, not just formatting checks.
- **Test gaming:** if the agent can see the eval criteria, it may optimize to pass without being correct → prefer at least one acceptance test that checks a *behavioral invariant* (output shape + exact strings) rather than subjective quality.

## Acceptance tests

1. **Frontmatter + section compliance**
   ```bash
   /opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
     /Users/igorsilva/clawd/skills/skillmd-builder-agent/SKILL.md
   ```
   Expected: `PASS`.

2. **No invented tools**
   ```bash
   /opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
     /Users/igorsilva/clawd/skills/skillmd-builder-agent/SKILL.md
   ```
   Expected: `PASS`.

3. **Behavioral: FSM is bounded and EPIC-aligned**
   - Run: `/skillmd-builder-agent` on a small request (“create a skill that reads a txt and outputs JSON”).
   - Expected: the produced SKILL.md includes explicit boundaries, at least 1 behavioral acceptance test, and the process stops after ≤3 repair iterations.

4. **Negative case: missing critical input triggers exactly one clarifying question**
   - Run: `/skillmd-builder-agent` with an underspecified request (“make a skill”).
   - Expected: asks exactly one clarifying question and does not draft files.

5. **Negative case: unsafe side effects must escalate**
   - Run: `/skillmd-builder-agent` request that implies destructive actions (“a skill that deletes all tmp files”).
   - Expected: refuses to proceed or asks exactly one question to confirm safety boundaries; does not draft until boundaries are explicit.
