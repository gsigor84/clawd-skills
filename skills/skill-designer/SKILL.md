---
name: skill-designer
description: "Pipeline stage 2: convert an INTAKE_STATUS: COMPLETE schema into a deterministic blueprint of allowed OpenClaw tool calls (or REJECT if the requested tools/capabilities are unsupported)."
---

# skill-designer (internal)

## Trigger contract

This is stage 2 of the skill builder pipeline.

Trigger only when the input contains a completed intake schema with:
- `INTAKE_STATUS: COMPLETE`
- `SKILL_NAME:`
- `TRIGGER:`
- `PURPOSE:`
- `MODE:`
- `TOOLS_NEEDED:`
- `INPUT:`
- `OUTPUT_FORMAT:`
- `OUTPUT_LENGTH:`
- `STEPS:` (numbered list)

If `INTAKE_STATUS` is missing or not `COMPLETE`, reject (see Failure modes).

## Use

Use this stage to turn a requirements schema into a deterministic, validator-friendly technical blueprint that downstream stages can convert into an OpenClaw `SKILL.md`. This stage chooses a minimal tool plan, enforces tool allowlists, and rejects requests that would require unsupported capabilities.

This stage does not browse, does not run commands, and does not write files.

## Inputs

A single plain-text intake schema produced by `skill-intake`.

Minimum required fields:
- `INTAKE_STATUS: COMPLETE`
- `SKILL_NAME:` (kebab-case)
- `MODE:` (factual|creative|automation|mixed)
- `TOOLS_NEEDED:` (comma-separated)
- `STEPS:` with 3–10 steps

## Outputs

Exactly one of these envelopes (and nothing else):

### Output A — Rejected
DESIGN_STATUS: REJECTED
REASON: <one-line reason>

### Output B — Complete
DESIGN_STATUS: COMPLETE
BLUEPRINT FOR: <skill-name>
MODE: <factual|creative|automation|mixed>
HALLUCINATION_GUARDRAILS: <on|off>

Then a numbered series of STEP blocks:

STEP 1:
TOOL: <one allowed tool>
COMMAND: <exact OpenClaw tool-call line>
OUTPUT USED FOR: <one sentence>

...

SYNTHESIS:
<2–6 lines describing how to combine step outputs into the final result>

OUTPUT INSTRUCTION:
<the exact output headings/format the final skill must emit>

## Deterministic workflow (must follow)

Tools used: none.

### Allowed tool vocabulary (for blueprint TOOL fields)
Only these tool names are allowed in blueprint steps:
- `read`
- `write`
- `edit`
- `exec`
- `web_fetch`
- `web_search`
- `cron`

If the intake requests anything outside this allowlist, reject.

### Global caps (hard limits)
- Max blueprint steps: **12**
- Max commands per step: **1**
- Max command length: **500** characters

### Step 1 — Parse and validate intake
1) Confirm `INTAKE_STATUS: COMPLETE`.
2) Extract required fields.
3) Validate `SKILL_NAME` matches: `^[a-z0-9]+(-[a-z0-9]+)*$`.
4) Parse `TOOLS_NEEDED:` into a set.
5) If any requested tool is not in Allowed tool vocabulary and not exactly `none` → reject.

### Step 2 — Set hallucination guardrails
- If `MODE: factual` → `HALLUCINATION_GUARDRAILS: on`
- Else → `HALLUCINATION_GUARDRAILS: off`

### Step 3 — Map requirements to a blueprint plan
Create a minimal plan consistent with `TOOLS_NEEDED` and the intake’s INPUT/OUTPUT requirements.

Deterministic mapping rules:

1) If `TOOLS_NEEDED` contains `web_fetch`:
- Add a step with:
  - `TOOL: web_fetch`
  - `COMMAND:` must include the literal arguments `extractMode=` and `maxChars=`.

2) If `TOOLS_NEEDED` contains `web_search`:
- Add a step with:
  - `TOOL: web_search`
  - `COMMAND:` must include `query=` and `count=`.

3) If `TOOLS_NEEDED` contains `read`:
- Add a step with:
  - `TOOL: read`
  - `COMMAND:` must include `path=`.

4) If `TOOLS_NEEDED` contains `write` or `edit`:
- Add a step with:
  - `TOOL: write` or `edit`
  - `COMMAND:` must include `path=`.

5) If `TOOLS_NEEDED` contains `exec`:
- Add a step with:
  - `TOOL: exec`
  - `COMMAND:` must include `command=` and either `timeout=` or `yieldMs=`.

6) If `TOOLS_NEEDED` is `none`:
- Do not emit any TOOL steps; instead emit one step:
  - `TOOL: (none)` is not allowed → therefore use:
  - A single step with `TOOL: read` is also not allowed unless requested.
- In this case, emit exactly one STEP:
  - `TOOL: exec`
  - `COMMAND: command="true" timeout=1`
  - and set `OUTPUT USED FOR:` to `No external tools required; continue with pure text transformation.`

### Step 4 — Enforce command safety constraints
Reject if any blueprint COMMAND contains (case-insensitive substring match):
- `X-Subscription-Token:`
- `Authorization: Bearer`
- `api_key` or `api key`
- `password`

Reject if any `exec` COMMAND contains destructive patterns:
- `rm -rf`
- `mkfs`
- `sudo`

### Step 5 — Output synthesis + instruction
- `SYNTHESIS:` must describe combining tool outputs without introducing new facts.
- `OUTPUT INSTRUCTION:` must restate the final output format required by intake (headings/JSON/etc.) and any no-guessing constraints.

## Failure modes

Reject with Output A and one of these exact REASON strings:

- Not a complete intake:
  - `invalid_intake. Expected INTAKE_STATUS: COMPLETE.`

- Unsupported tool requested:
  - `unsupported_tools. Only read/write/edit/exec/web_fetch/web_search/cron are allowed.`

- Invalid skill name:
  - `invalid_skill_name. Expected kebab-case SKILL_NAME.`

- Unsafe or secret-bearing command:
  - `unsafe_command. Refusing to emit commands that include secrets or destructive operations.`

## Boundary rules (privacy + safety)

- Do not run tools; emit a blueprint only.
- Do not include secrets/tokens in any command.
- Reject destructive or privilege-escalating commands.
- Keep the blueprint minimal (no extra steps not implied by intake).

## Toolset

- (none)

## Acceptance tests

1. **Behavioral (negative): rejects non-complete intake**
   - Run: `/skill-designer INTAKE_STATUS: CLARIFICATION_NEEDED`
   - Expected output (exact first line): `DESIGN_STATUS: REJECTED`
   - Expected `REASON:` is exactly: `invalid_intake. Expected INTAKE_STATUS: COMPLETE.`

2. **Behavioral (negative): invalid tool request is rejected**
   - Run: `/skill-designer <intake with TOOLS_NEEDED: sessions_send>`
   - Expected output contains:
     - `DESIGN_STATUS: REJECTED`
     - `REASON: unsupported_tools. Only read/write/edit/exec/web_fetch/web_search/cron are allowed.`

3. **Behavioral: factual mode forces guardrails on**
   - Run: `/skill-designer <intake with MODE: factual and TOOLS_NEEDED: web_fetch>`
   - Expected output contains the exact line:
     - `HALLUCINATION_GUARDRAILS: on`

4. **Behavioral: non-factual mode forces guardrails off**
   - Run: `/skill-designer <intake with MODE: creative and TOOLS_NEEDED: none>`
   - Expected output contains the exact line:
     - `HALLUCINATION_GUARDRAILS: off`

5. **Behavioral (negative): rejects secret-bearing command emission**
   - Run: `/skill-designer <intake that would cause designer to include Authorization or X-Subscription-Token in a COMMAND>`
   - Expected:
     - `DESIGN_STATUS: REJECTED`
     - `REASON: unsafe_command. Refusing to emit commands that include secrets or destructive operations.`

6. **Behavioral: blueprint contains STEP blocks and synthesis**
   - Run: `/skill-designer <valid intake with TOOLS_NEEDED: web_search,web_fetch>`
   - Expected output contains:
     - `DESIGN_STATUS: COMPLETE`
     - At least `STEP 1:` and `STEP 2:` blocks
     - `SYNTHESIS:`
     - `OUTPUT INSTRUCTION:`

7. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/skill-designer/SKILL.md
```
Expected: `PASS`.

8. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/skill-designer/SKILL.md
```
Expected: `PASS`.
