---
name: self-improving-skill-builder
description: "Improve SKILL.md files across ~/clawd/skills/ via a bounded evaluation→patch loop. Manual trigger: /improve-skills. Automatic: runs after skillmd-builder-agent successfully builds a new skill."
---

# self-improving-skill-builder

## Use

Improve the quality and validator-compliance of all skills under `~/clawd/skills/` using a **bounded** loop:

1) Scan skills
2) Evaluate (deterministic validators + optional LLM-as-judge)
3) Categorize failures
4) Apply minimal patches
5) Repeat up to 3 iterations, then escalate
6) Persist traces to a daily log
7) Commit + push changes to GitHub

### Triggers
- Manual: `/improve-skills` (improves all skills in `~/clawd/skills/`)
- Automatic: after every new skill built by `skillmd-builder-agent` (implemented by calling this runner from `build_skill.py` when present)

## Inputs

- `skills_dir` (optional, default: `/Users/igorsilva/clawd/skills`)
- `targets` (optional): list of skill folder names or SKILL.md paths to restrict the run
- `max_iters` (optional, default: 3)
- `push` (optional flag): when set, commit + push changes to GitHub

## Outputs

- Updated skills in place: `~/clawd/skills/*/SKILL.md`
- Daily trace log:
  - `/Users/igorsilva/clawd/tmp/logs/skill-improvement-YYYYMMDD.log`
- Git commit(s) + push (when `--push` is set)

## Evaluation stack

### Deterministic (always)
- `validate_skillmd.py` on each SKILL.md
- `check_no_invented_tools.py` on each SKILL.md

### LLM-as-judge (optional)
- Only runs if `OPENAI_API_KEY` is available in the environment.
- If not available, the run still proceeds using deterministic checks only and logs `judge_skipped`.

## Failure modes

- If `OPENAI_API_KEY` is not configured, LLM-as-judge evaluation is skipped (deterministic validation still runs).
- If a skill cannot be made to pass deterministic validators in 3 iterations, it is marked `escalate` and left unchanged.
- Git push failures stop the run and print the git error.

## Failure taxonomy (categorize each failure)

- `boundary`
- `tool`
- `guardrail`
- `output`
- `test`
- `safety`

## Guardrails

- Minimal patches only (no large rewrites)
- Max iterations per skill: 3
- Never introduce non-allowed tools in the `## Toolset` section
- If deterministic validators still fail after 3 iterations: log `escalate` and skip the skill

## Toolset

- `read`
- `write`
- `edit`
- `exec`

## Acceptance tests

1. **Behavioral: run on a single skill (dry run)**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/self-improving-skill-builder/scripts/improve_skills.py \
  --skills-dir /Users/igorsilva/clawd/skills \
  --targets file-summarizer
```
Expected: exits 0, logs state transitions, and validators pass for the target skill.

2. **Behavioral: run on all skills and produce a summary**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/self-improving-skill-builder/scripts/improve_skills.py \
  --skills-dir /Users/igorsilva/clawd/skills
```
Expected: exits 0 and prints counts for scanned/changed/passed/escalated.

3. **Negative case: missing skills dir**
- Run: `/improve-skills /path/does/not/exist`
- Expected: clean error and no files modified.

4. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/self-improving-skill-builder/SKILL.md
```
Expected: `PASS`.

5. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/self-improving-skill-builder/SKILL.md
```
Expected: `PASS`.
