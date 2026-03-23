---
name: skill-intake
description: "Pipeline stage 1: turn a plain-English skill request into a strict intake schema, or ask one consolidated clarification question for missing required fields."
---

# skill-intake (internal)

## Trigger contract

This is stage 1 of the skill builder pipeline.

Trigger only when the input is a plain-English description of a skill the user wants built.

Accepted invocation patterns:
- Internal (preferred): orchestrator calls `skill-intake` with the user’s raw request text.
- Manual debug (operator only): `/skill-intake <paste user request>`

If the input is empty/whitespace, return `INTAKE_STATUS: CLARIFICATION_NEEDED` with the exact missing list and question defined below.

## Use

Use this stage to extract deterministic requirements from a user’s request without designing implementation details. It outputs either:
- a complete, parseable intake schema, or
- one consolidated clarifying question that requests all missing required fields at once.

This stage does not call tools, does not browse, and does not invent features.

## Inputs

A single plain-text request describing the desired skill.

Examples:
- `Make a command that summarizes a URL into bullet points and quotes.`
- `I want a skill that checks my repo for TODOs and writes them to a file.`

## Outputs

Exactly one of the following envelopes (and nothing else):

### Output A — Clarification needed
INTAKE_STATUS: CLARIFICATION_NEEDED
MISSING: <comma-separated list of missing required fields>
QUESTION: <one question that asks for all missing fields at once>

### Output B — Complete
INTAKE_STATUS: COMPLETE
SKILL_NAME: <kebab-case-name>
TRIGGER: <exact trigger phrase>
PURPOSE: <one sentence>
MODE: <factual|creative|automation|mixed>
TOOLS_NEEDED: <none|web_fetch|web_search|read|write|edit|exec|cron|sessions_*>
INPUT: <what the user provides after the trigger>
OUTPUT_FORMAT: <plain_text|structured_plain_text|json>
OUTPUT_LENGTH: <short|medium|long>
STEPS:
1) <step>
2) <step>

Hard constraints:
- `SKILL_NAME` must match regex: `^[a-z0-9]+(-[a-z0-9]+)*$`.
- `TRIGGER` must start with `/` and contain no spaces before the first argument delimiter.
- `TOOLS_NEEDED` must be a comma-separated list from the allowed set above (or `none`).
- `STEPS` must be a numbered list with 3–10 items.

## Deterministic workflow (must follow)

Tools used: none.

### Step 1 — Normalize and sanity-check input
- Trim leading/trailing whitespace.
- If empty after trimming: go to Output A.

### Step 2 — Extract candidate fields from the request
Derive the following from the text if explicitly stated or strongly implied:
- Desired skill purpose
- Likely user trigger phrase (if user provided one; otherwise propose `/` + `SKILL_NAME`)
- Inputs the user will provide (URL/file/text/none)
- Output format preference (plain text vs JSON) if specified
- Any required tools implied by the task (choose minimal set)

### Step 3 — MODE classification (always set; never a reason to clarify)
Choose MODE deterministically:
- `automation` if the user wants file/system changes, scheduled tasks, or command execution.
- `creative` if the user wants ideation/writing/naming.
- `factual` if the user wants summarization/extraction/QA where correctness matters.
- `mixed` only if the request explicitly combines creative + factual/automation.

If ambiguous between `factual` and `mixed`, choose `factual`.

### Step 4 — Required fields and clarification rule
Required fields to be considered complete:
- SKILL_NAME
- TRIGGER
- PURPOSE
- INPUT
- OUTPUT_FORMAT
- OUTPUT_LENGTH
- TOOLS_NEEDED
- STEPS

Clarification rule:
- If any required field cannot be determined from the request without guessing, emit Output A.
- `MODE` is never considered missing.

### Step 5 — Construct Output A (one consolidated question)
If clarification is needed:
- `MISSING:` must list every missing required field.
- `QUESTION:` must be exactly one sentence ending with `?` that asks for all missing fields.

### Step 6 — Construct Output B
If complete:
- Generate `SKILL_NAME` as kebab-case derived from a short skill title in the request.
- If user did not provide a trigger, set `TRIGGER: /<SKILL_NAME>`.
- Keep `TOOLS_NEEDED` minimal and only include tools implied by the request.
- Create 3–10 deterministic steps describing *what* the skill will do (not tool commands).

## Failure modes

This stage does not emit `ERROR:` strings. The only non-complete outcome is `INTAKE_STATUS: CLARIFICATION_NEEDED`.

## Boundary rules (privacy + safety)

- Do not request secrets, tokens, passwords, or personal data unless the skill itself explicitly requires it.
- Do not design implementation commands or write code; only requirements.
- Do not add features not explicitly requested.
- No tool calls, no network, no filesystem writes.

## Toolset

- (none)

## Acceptance tests

1. **Behavioral: empty input triggers clarification**
   - Run: `/skill-intake "   "`
   - Expected output contains exactly:
     - `INTAKE_STATUS: CLARIFICATION_NEEDED`
     - `MISSING:` includes `SKILL_NAME`.

2. **Behavioral: MODE is always present**
   - Run: `/skill-intake Make a command that summarizes a URL into bullet points.`
   - Expected: output contains a `MODE:` line in either COMPLETE or CLARIFICATION_NEEDED state.

3. **Behavioral: consolidated single-question clarification**
   - Run: `/skill-intake Build me a tool to help with my business.`
   - Expected:
     - `INTAKE_STATUS: CLARIFICATION_NEEDED`
     - `QUESTION:` is exactly one line ending with `?`.

4. **Behavioral: complete schema shape is exact**
   - Run: `/skill-intake Create /sumurl that takes one https URL and outputs 5 bullet points and 3 quotes, no outside facts.`
   - Expected:
     - `INTAKE_STATUS: COMPLETE`
     - Contains fields: `SKILL_NAME:`, `TRIGGER:`, `PURPOSE:`, `MODE:`, `TOOLS_NEEDED:`, `INPUT:`, `OUTPUT_FORMAT:`, `OUTPUT_LENGTH:`, and `STEPS:`.

5. **Behavioral: kebab-case SKILL_NAME**
   - Run: `/skill-intake Create a skill called "URL Argument Summarizer" that summarizes a URL.`
   - Expected:
     - If COMPLETE, `SKILL_NAME:` matches `^[a-z0-9]+(-[a-z0-9]+)*$`.

6. **Behavioral (negative): no feature invention**
   - Run: `/skill-intake Summarize a URL into bullets.`
   - Expected:
     - Output does not mention unrelated tools like `cron` or `sessions_send` unless explicitly requested.

7. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/skill-intake/SKILL.md
```
Expected: `PASS`.

8. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/skill-intake/SKILL.md
```
Expected: `PASS`.
