---
name: learning-guardrail
description: "Trigger: /learning-guardrail: <learning content>. Check if learning content is safe to ingest (small, atomic, non-monolithic)."
---

learning-guardrail

Goal  
Ensure all learning content is safe to ingest (no crashes, no monolithic files).

Trigger  
/learning-guardrail: <learning content>

Input  
- learning content (text or file)

Output (strict)  
Return EXACTLY 3 lines:

Status: <ok | split required>
Issue: <main problem if any>
Action: <what to do next>

Rules  
- Detect if content is too large or too complex  
- Detect if content mixes multiple responsibilities  
- Prefer small, atomic learning units  
- No long explanations

Behavior  
- If content is small and focused → ok  
- If content is large/monolithic → split required

Acceptance criteria  
1) Exactly 3 lines  
2) Clear action  
3) No extra text

Tests  

Input:
/learning-guardrail: small concept about event systems

Output:
Status: ok  
Issue: none  
Action: safe to ingest

---

Input:
/learning-guardrail: large multi-topic chapter

Output:
Status: split required  
Issue: multiple concepts in one file  
Action: split into atomic concepts before ingest

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
   - Run: `/learning-guardrail <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/learning-guardrail <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/learning-guardrail/SKILL.md
```
Expected: `PASS`.
