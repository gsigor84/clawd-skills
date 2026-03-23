---
name: rule-check
description: "Trigger: /rule-check: <action>. Check an action against learned rules and return ok/wrong with a minimal fix."
---

rule-check

Goal  
Check actions against learned rules.

Trigger  
/rule-check: <action>

Input  
- action (required): one short action statement

Output (strict)  
Return EXACTLY:

Status: <ok | wrong>  
Fix: <only if wrong>

Rules  
- No explanation  
- Short  
- Use stored learning as rules  
- If no applicable rule is known, treat as wrong and request the missing rule

Acceptance criteria  
1) Output is exactly 1–2 lines (Fix line only when Status is wrong)  
2) Fix is a concrete rewrite of the action (or a request for the missing rule)

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
   - Run: `/rule-check <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/rule-check <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/rule-check/SKILL.md
```
Expected: `PASS`.
