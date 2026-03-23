---
name: skill-writer
description: "Pipeline stage 3: convert a COMPLETE blueprint into a validator-clean OpenClaw SKILL.md (or REJECT with an exact reason)."
---

# skill-writer (internal)

## Trigger contract

This is an internal pipeline skill used by the skill builder pipeline.

Trigger **only** when the input message body is a blueprint produced by `skill-designer` and contains:
- `DESIGN_STATUS: COMPLETE`
- `BLUEPRINT FOR:`
- `MODE:`
- at least one `STEP` block that includes `TOOL:` and `COMMAND:`

Accepted invocation patterns:
- Internal (preferred): the orchestrator calls `skill-writer` with the full blueprint text as the message body.
- Manual debug (operator only): `/skill-writer <paste blueprint text>`

If the input does not satisfy the blueprint requirements above, the skill must output **WRITER_STATUS: REJECTED** with an exact failure reason (see **Failure modes**).

## Deterministic workflow (must follow)

Tools used: none. This stage is a single-pass text transform.

### Step 1 — Validate blueprint structure
Hard checks (string/pattern checks):
1) Must contain `DESIGN_STATUS: COMPLETE`.
2) Must contain `BLUEPRINT FOR:` with a non-empty skill name value.
3) Must contain `MODE:` with one of: `factual | creative | automation | mixed`.
4) Must contain at least one `STEP` block with both:
   - `TOOL:` (non-empty)
   - `COMMAND:` (non-empty)

If any check fails → reject.

### Step 2 — Reject placeholder commands
Reject if **any** `COMMAND:` line contains obvious placeholders (case-insensitive substring match):
- `YOUR QUERY`
- `QUERY_URL_ENCODED`
- `URL`
- `<` or `>` (angle-bracket placeholders)
- `PATH_TO_`

If found → reject.

### Step 3 — Build SKILL.md deterministically
Produce SKILL.md with:

#### 3A) Frontmatter
- `name`: kebab-case from `BLUEPRINT FOR:` (lowercase, spaces→hyphens, strip non `[a-z0-9-]`, collapse hyphens).
- `description`: must include the exact trigger phrase.
  - If the blueprint provides a trigger line (any line starting with `TRIGGER:`), use it.
  - Else default trigger phrase: `/` + `<name>`.

#### 3B) Required sections (in this order)
The generated SKILL.md must include these section headers in this exact order:
1) `## Trigger`
2) `## Use`
3) `## Inputs`
4) `## Outputs`
5) `## Failure modes`
6) `## Toolset`
7) `## Execution steps`
8) `## Acceptance tests`

#### 3C) Execution steps
- Convert each blueprint STEP into a numbered execution step.
- Each step must include:
  - Tool name (verbatim from blueprint)
  - The exact command (verbatim from blueprint)
  - One sentence describing what output is extracted/used next (from `OUTPUT USED FOR:` if present; otherwise: `Use the command output as input to the next step.`)

#### 3D) Conditional anti-hallucination injection
If the blueprint contains a line `HALLUCINATION_GUARDRAILS: on`, include a section titled exactly:
- `## Anti-hallucination / context discipline`

with these bullets (verbatim):
- **Context-only:** answer strictly from the provided context/tool outputs; do not use pre-trained knowledge.
- **Negative rejection (no guessing):** if context is missing/insufficient/conflicting, say you cannot answer from the provided context.
- **Evidence referencing:** explicitly reference which snippet/tool output supports each key claim.
- **Scope control:** refuse out-of-scope queries rather than speculate.

If `HALLUCINATION_GUARDRAILS: off` or missing: do not include this section.

### Step 4 — Emit writer output envelope
Output must be exactly one of:

#### Output A — Rejected
WRITER_STATUS: REJECTED
REASON: <one-line reason>

#### Output B — Complete
WRITER_STATUS: COMPLETE
SKILL_CONTENT:
<full SKILL.md starting with `---`>

No other text.

## Use

Use this stage when you already have a fully populated technical blueprint (commands + tools) and you need a validator-clean OpenClaw `SKILL.md` with a deterministic structure and strict failure on placeholders.

## Inputs

One plain-text blueprint that includes, at minimum:
- `DESIGN_STATUS: COMPLETE`
- `BLUEPRINT FOR: <skill name>`
- `MODE: factual|creative|automation|mixed`
- At least one `STEP n:` block with `TOOL:` and `COMMAND:`

## Outputs

Either:

1) Rejection:
- `WRITER_STATUS: REJECTED`
- `REASON: ...`

or

2) Complete:
- `WRITER_STATUS: COMPLETE`
- `SKILL_CONTENT:` followed by a full OpenClaw `SKILL.md` file.

## Failure modes

- Missing or invalid blueprint header:
  - Reject with:
    - `WRITER_STATUS: REJECTED`
    - `REASON: invalid_blueprint. Expected DESIGN_STATUS: COMPLETE and required fields.`

- Missing skill name:
  - Reject with:
    - `WRITER_STATUS: REJECTED`
    - `REASON: missing_skill_name. Expected BLUEPRINT FOR: <name>.`

- Missing/invalid MODE:
  - Reject with:
    - `WRITER_STATUS: REJECTED`
    - `REASON: invalid_mode. Expected MODE: factual|creative|automation|mixed.`

- Missing STEP tool/command:
  - Reject with:
    - `WRITER_STATUS: REJECTED`
    - `REASON: missing_steps. Expected at least one STEP with TOOL and COMMAND.`

- Placeholder command detected:
  - Reject with:
    - `WRITER_STATUS: REJECTED`
    - `REASON: placeholder_command_detected. Remove placeholders like URL/YOUR QUERY/<...>.`

## Toolset

- (none)

## Acceptance tests

1) **Negative: invalid blueprint rejected**
   - Input: `hello`.
   - Expected output (exact first two lines):
     - `WRITER_STATUS: REJECTED`
     - `REASON: invalid_blueprint. Expected DESIGN_STATUS: COMPLETE and required fields.`

2) **Negative: placeholder command rejected**
   - Input includes:
     - `DESIGN_STATUS: COMPLETE`
     - `BLUEPRINT FOR: test-skill`
     - `MODE: factual`
     - a `COMMAND:` line containing `URL`
   - Expected output (exact):
     - `WRITER_STATUS: REJECTED`
     - `REASON: placeholder_command_detected. Remove placeholders like URL/YOUR QUERY/<...>.`

3) **Behavioral: completion envelope is exact**
   - Input: a minimal valid blueprint with one STEP and no placeholders.
   - Expected:
     - Output starts with `WRITER_STATUS: COMPLETE` then `SKILL_CONTENT:`.
     - `SKILL_CONTENT:` begins with `---` on the next line.

4) **Behavioral: required section ordering in generated SKILL.md**
   - Input: a valid blueprint.
   - Expected: within SKILL_CONTENT, the section headers appear in this exact order:
     - `## Trigger`, `## Use`, `## Inputs`, `## Outputs`, `## Failure modes`, `## Toolset`, `## Execution steps`, `## Acceptance tests`.

5) **Behavioral: conditional anti-hallucination section**
   - Input: blueprint containing `HALLUCINATION_GUARDRAILS: on`.
   - Expected: SKILL_CONTENT includes a section titled exactly `## Anti-hallucination / context discipline` and contains the four mandatory bullets.

6) **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/skill-writer/SKILL.md
```
Expected: `PASS`.

7) **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/skill-writer/SKILL.md
```
Expected: `PASS`.
