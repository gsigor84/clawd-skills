---
name: skill-intake
description: "Pipeline stage 1: run a duplicate-skill check, then turn a plain-English skill request into a strict intake schema (or ask one consolidated clarification question)."
---

# skill-intake (internal)

## Trigger contract

This is stage 1 of the skill builder pipeline.

Trigger only when the input is a plain-English description of a skill the user wants built.

Accepted invocation patterns:
- Internal (preferred): orchestrator calls `skill-intake` with the user’s raw request text.
- Manual debug (operator only): `/skill-intake <paste user request>`

If the input is empty/whitespace, return `INTAKE_STATUS: CLARIFICATION_NEEDED`.

## Use

Use this stage to extract deterministic requirements from a user’s request **without** designing implementation details.

New hard rule: **duplicate/overlap check runs first**. If a similar skill already exists, this stage must stop and ask Igor whether to proceed.

## Inputs

A single plain-text request describing the desired skill.

Examples:
- `Make a command that summarizes a URL into bullet points and quotes.`
- `I want a skill that checks my repo for TODOs and writes them to a file.`

## Outputs

Exactly one of the following envelopes (and nothing else):

### Output A — Overlap check confirmation required (must run first)
INTAKE_STATUS: CLARIFICATION_NEEDED
MISSING: OVERLAP_CHECK_CONFIRMATION
OVERLAPS:
- <skill-name> | similarity=<high|medium|low> | why=<one line>
QUESTION: <one sentence ending with ?>

Rules:
- Emit Output A **before** producing any COMPLETE schema if any overlap is detected.
- The QUESTION must ask Igor to choose exactly one:
  - proceed anyway
  - improve an existing skill (name it)
  - cancel

### Output B — Clarification needed (normal)
INTAKE_STATUS: CLARIFICATION_NEEDED
MISSING: <comma-separated list of missing required fields>
QUESTION: <one question that asks for all missing fields at once>

### Output C — Complete
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

Tools used: `read`, `exec`.

### Step 0 — Normalize and sanity-check input
- Trim leading/trailing whitespace.
- If empty after trimming: emit Output B with `MISSING:` including `SKILL_NAME,TRIGGER,PURPOSE,INPUT,OUTPUT_FORMAT,OUTPUT_LENGTH,TOOLS_NEEDED,STEPS` and a single consolidated QUESTION.

### Step 1 — Duplicate/overlap check (mandatory, must run before schema)

Goal: avoid building a duplicate skill.

1) Scan all skills:
   - Use `exec` to list skill directories under `/Users/igorsilva/clawd/skills/`.
2) For each `<skill>/SKILL.md`:
   - Use `read` to load the file.
   - Extract the YAML frontmatter `name` and `description`.
3) Compare the user request to existing skills using this deterministic heuristic:
   - Normalize both strings: lowercase; remove punctuation; split into tokens.
   - Compute overlap score = count(shared tokens) excluding stopwords: `the,a,an,to,of,and,or,for,with,on,in`.
   - Flag overlap if ANY of these is true:
     - the request explicitly names an existing skill trigger (e.g. `/summarize`) OR
     - overlap score >= 6 OR
     - overlap score >= 4 AND the request contains the same core verb+noun pair implied by description (e.g., "summarize url", "build skill", "improve skills").

Similarity label:
- high: overlap score >= 8 OR explicitly same trigger
- medium: overlap score 6–7
- low: overlap score 4–5 (only if also matches a core verb+noun pair)

4) If any overlaps are found:
   - Emit Output A.
   - Include up to 5 overlaps, sorted by similarity (high→low).
   - QUESTION must be exactly one sentence ending with `?`, asking:
     - proceed anyway
     - improve an existing skill (choose one)
     - cancel

Hard rule:
- If Output A is emitted, **stop**. Do not produce any COMPLETE schema until Igor explicitly says “yes, proceed anyway”.

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
- If any required field cannot be determined from the request without guessing, emit Output B.
- `MODE` is never considered missing.

### Step 5 — Construct Output B (one consolidated question)
If clarification is needed:
- `MISSING:` must list every missing required field.
- `QUESTION:` must be exactly one sentence ending with `?` that asks for all missing fields.

### Step 6 — Construct Output C
If complete:
- Generate `SKILL_NAME` as kebab-case derived from a short skill title in the request.
- If user did not provide a trigger, set `TRIGGER: /<SKILL_NAME>`.
- Keep `TOOLS_NEEDED` minimal and only include tools implied by the request.
- Create 3–10 deterministic steps describing *what* the skill will do (not tool commands).

## Failure modes

This stage does not emit `ERROR:` strings. Non-complete outcomes are `INTAKE_STATUS: CLARIFICATION_NEEDED`.

## Boundary rules (privacy + safety)

- Do not request secrets, tokens, passwords, or personal data unless the skill itself explicitly requires it.
- Do not design implementation commands or write code; only requirements.
- Do not add features not explicitly requested.
- Duplicate check reads SKILL.md files locally only; do not use network.

## Toolset

- `read`
- `exec`

## Acceptance tests

1. **Overlap check blocks duplicate build**
   - Run: `/skill-intake Create a /summarize command that summarizes URLs and local files.`
   - Expected: `INTAKE_STATUS: CLARIFICATION_NEEDED` with `MISSING: OVERLAP_CHECK_CONFIRMATION` and `OVERLAPS:` including `summarize`.

2. **Overlap check asks proceed/improve/cancel**
   - Run: `/skill-intake Build a skill that improves existing SKILL.md files to pass validators.`
   - Expected: Output A with a QUESTION that asks whether to proceed anyway, improve an existing skill, or cancel.

3. **Behavioral: empty input triggers clarification**
   - Run: `/skill-intake "   "`
   - Expected: `INTAKE_STATUS: CLARIFICATION_NEEDED`.

4. **Behavioral: MODE is always present in COMPLETE output**
   - Run: `/skill-intake Create /sumurl that takes one https URL and outputs 5 bullet points.`
   - Expected: if COMPLETE, output contains `MODE:`.

5. **Behavioral: complete schema shape is exact**
   - Run: `/skill-intake Create /sumurl that takes one https URL and outputs 5 bullet points and 3 quotes, no outside facts.`
   - Expected: if COMPLETE, contains fields: `SKILL_NAME:`, `TRIGGER:`, `PURPOSE:`, `MODE:`, `TOOLS_NEEDED:`, `INPUT:`, `OUTPUT_FORMAT:`, `OUTPUT_LENGTH:`, and `STEPS:`.

6. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/skill-intake/SKILL.md
```
Expected: `PASS`.

7. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/skill-intake/SKILL.md
```
Expected: `PASS`.
