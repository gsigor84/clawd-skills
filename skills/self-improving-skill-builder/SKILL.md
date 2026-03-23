---
name: self-improving-skill-builder
description: "Trigger: /improve-skills [--targets ...]. Run deterministic validator checks across skills and apply bounded, minimal patches until PASS or ESCALATE."
---

# self-improving-skill-builder

## Trigger contract

Manual trigger:
- `/improve-skills` optionally with:
  - `--targets <comma-separated skill names>`

Automatic trigger (internal):
- called by the build pipeline after a new skill is created, with `--targets <new-skill-name>`.

This skill only operates inside:
- `/Users/igorsilva/clawd/skills/`

If the skills directory is missing or targets are invalid, it must fail with an exact error string (see Failure modes).

## Use

Use this skill to iteratively improve SKILL.md files so they pass the deterministic validators:
- `validate_skillmd.py`
- `check_no_invented_tools.py`

It applies minimal edits (no rewrites) within a strict cap of iterations, and produces a plain-text summary of what passed, changed, or escalated.

## Inputs

- `--skills-dir <path>` (optional, default: `/Users/igorsilva/clawd/skills`)
- `--targets <comma-separated>` (optional)
  - Each target is either a skill folder name under skills-dir (e.g., `url-arg-summarizer`) or an absolute path to a `SKILL.md` within skills-dir.
- `--max-iters <n>` (optional, default: 3, max: 5)

If no targets are provided, all skills under skills-dir are scanned.

## Outputs

A plain-text report with these headings exactly:

IMPROVEMENT RUN
SKILLS_SCANNED: <n>
SKILLS_CHANGED: <n>
SKILLS_PASSING: <n>
SKILLS_ESCALATED: <n>

CHANGED:
- <skill-name> — <one-line change summary>

ESCALATED:
- <skill-name> — <one-line reason>

No file contents are printed.

## Deterministic workflow (must follow)

### Tooling
- `exec` (to run deterministic validators)
- `read` / `edit` (to apply minimal patches)

### Global caps (hard limits)
- Max iterations per skill: **3** by default (hard max 5)
- Max skills processed per run: **200**
- Max patch size per skill per iteration: **6000** characters

### Boundary rules (privacy + safety)

- Do not run any network calls.
- Do not commit, push, or modify git state.
- Only edit files under `/Users/igorsilva/clawd/skills/`.
- Never create new skills; only patch existing `SKILL.md`.
- Minimal patches only: change the smallest text necessary to satisfy validators.

### Step 1 — Resolve targets
1) Determine `skills_dir`.
2) If `skills_dir` does not exist → fail.
3) If `--targets` provided:
   - Resolve each target to an absolute `.../<skill>/SKILL.md` under skills_dir.
   - If any target cannot be resolved → fail.
4) Else:
   - Enumerate all `SKILL.md` files exactly one directory deep under skills_dir.

### Step 2 — For each SKILL.md, run validators
For each target SKILL.md:
1) Run:
   - `/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py <path>`
2) Run:
   - `/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py <path>`

If both PASS → mark skill PASSING.

If either FAIL → proceed to Step 3.

### Step 3 — Apply bounded minimal patch loop
For up to `max_iters` iterations:
1) Parse validator failure lines (those beginning with `- `).
2) Apply one minimal patch addressing the highest-priority failure:
   - missing required section headers → insert empty but non-placeholder section stubs.
   - acceptance tests issues → add one concrete behavioral test line with a `/skill-name ...` run and an Expected output assertion.
   - frontmatter issues → normalize frontmatter to exactly `name` and `description`.
   - invented tools → remove non-allowed tools from Toolset.
3) Re-run both validators.
4) If PASS → mark CHANGED + PASSING.

If still failing after max_iters → mark ESCALATED and leave the last attempted file state as-is.

### Step 4 — Emit report
Print the Output format exactly as specified.

## Failure modes

Return exactly one line and nothing else:

- Missing skills directory:
  - `ERROR: skills_dir_missing. Provide a valid --skills-dir.`

- Invalid targets:
  - `ERROR: invalid_targets. Targets must resolve to SKILL.md under the skills dir.`

- Too many skills:
  - `ERROR: too_many_skills. Refusing to process more than 200 skills.`

## Toolset

- `read`
- `edit`
- `exec`

## Acceptance tests

1. **Behavioral: run on a single target**
   - Run: `/improve-skills --targets url-arg-summarizer`
   - Expected: output includes `IMPROVEMENT RUN` and a non-negative integer on `SKILLS_SCANNED:`.

2. **Behavioral: invalid targets hard-stop**
   - Run: `/improve-skills --targets /tmp/not-a-skill.md`
   - Expected output (exact): `ERROR: invalid_targets. Targets must resolve to SKILL.md under the skills dir.`

3. **Behavioral: missing skills dir hard-stop**
   - Run: `/improve-skills --skills-dir /path/does/not/exist`
   - Expected output (exact): `ERROR: skills_dir_missing. Provide a valid --skills-dir.`

4. **Behavioral: bounded iterations enforced**
   - Given a skill that cannot be fixed within 3 iterations, expected:
     - It appears under `ESCALATED:` in the report.

5. **Behavioral: never prints full file contents**
   - Run: `/improve-skills --targets url-arg-summarizer`
   - Expected: output does not include the literal frontmatter fence `---` from any target skill.

6. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/self-improving-skill-builder/SKILL.md
```
Expected: `PASS`.

7. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/self-improving-skill-builder/SKILL.md
```
Expected: `PASS`.
