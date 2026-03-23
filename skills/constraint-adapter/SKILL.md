---
name: constraint-adapter
description: "name: constraint-adapter"
---

name: constraint-adapter
description: "Trigger: /constraint-adapter: <insights + constraints>. Reweight or filter insights based on real-world constraints."

constraint-adapter

Goal  
Adjust a given set of insights/trade-offs to better fit real-world constraints (reweight/filter/short edit only).

Trigger / Description  
- Trigger: /constraint-adapter: <insights + constraints>  
- Description: Reweight or filter existing insight bullets based on provided constraints (startup/speed/budget/security/team size/scale).

Inputs  
- insights (required): 3–6 bullets preferred (accept 1–8)  
- constraints (required): one short line

Output (strict)  
Return EXACTLY one of:

A) If constraints missing/empty:  
provide constraints

B) Otherwise:  
- 3–5 bullets max (no extra text)  
- Each bullet is one line: - <adjusted insight>  
- No explanations, no paragraphs

Rules (hard)  
- Do NOT create new concepts  
- Only reweight, prioritize, filter, or slightly modify existing insights  
- Prefer preserving original wording; only edit minimally to reflect constraints  
- Emphasize what matters MORE under constraints  
- De-emphasize or remove what matters LESS  
- If reducing bullets, remove the least relevant insights first (based on constraints)  
- Keep bullets short (one line)  
- No decision-making (that’s decision-maker)  
- No analysis frameworks (that’s analyze-lens)  
- No storage, no memory writes  
- No bash, no python, no tools  
- Single-pass, single-turn only  

Constraint mapping  
- startup / speed / MVP → favor simplicity, fast delivery, low overhead  
- enterprise / security / compliance → favor control, reliability, auditability  
- small team → reduce coordination and maintenance burden  
- scale → favor decoupling and robustness  

Acceptance criteria  
1) Output is either the failure string OR 3–5 bullets only  
2) Each bullet maps to original insights  
3) Output reflects constraints  
4) No extra commentary

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
   - Run: `/constraint-adapter <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/constraint-adapter <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/constraint-adapter/SKILL.md
```
Expected: `PASS`.
