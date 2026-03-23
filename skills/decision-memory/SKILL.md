---
name: decision-memory
description: "Trigger: /decision-memory: <decision + outcome>. Track decisions and extract lessons."
---

decision-memory

Goal  
Record a decision outcome and extract one clear learning.

Trigger  
/decision-memory: <decision + outcome>

Inputs  
- decision (required): short decision statement  
- outcome (required): what happened after

Output (strict)  
Return EXACTLY 3 lines:

Decision: <what was decided>
Outcome: <what happened>
Learning: <what to do differently next time>

Rules  
- Each line: one sentence max  
- No paragraphs  
- No extra text  
- Learning must be actionable  
- No vague statements  
- No theory — only practical adjustment  

Behavior  
- If outcome is negative → identify failure cause  
- If outcome is positive → reinforce what worked  
- Focus on improving next decision  

Constraints  
- No tools, no storage, no memory writes (external)  
- Single-pass only  

Failure  
- If input missing →  
provide decision and outcome  

Acceptance criteria  
1) Exactly 3 lines  
2) Learning is concrete and usable  
3) No generic advice

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
   - Run: `/decision-memory <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/decision-memory <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/decision-memory/SKILL.md
```
Expected: `PASS`.
