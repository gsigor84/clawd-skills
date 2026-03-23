---
name: decision-flow
description: "Trigger: /decision-flow: <concept + optional constraints>. Turn a concept into insights, a decision, and a learning in one lightweight flow."
---

decision-flow

Goal  
Create a lightweight orchestrator that turns a concept into a decision and learning in one flow.

Trigger / Description  
- Trigger: `/decision-flow: <concept + optional constraints>`  
- Description: Run extract → analyze → adapt → decide → learn in one controlled flow.

Inputs  
- concept (required)  
- constraints (optional)

Output (strict)  
Return EXACTLY 4 sections:

Concept: <short concept>
Insights:
- <3–5 bullets>
Decision:
- Decision: <...>
- Why: <...>
- Risk: <...>
Learning:
- Learning: <...>

Flow (internal)  
1) Extract concept (or use input directly if simple)  
2) Analyze using analyze-lens  
3) If constraints provided → run constraint-adapter  
4) Run decision-maker  
5) Simulate outcome → generate learning (decision-memory style)

Rules  
- Keep everything SHORT  
- No long reasoning  
- No extra text  
- Do NOT expose chain-of-thought  
- Focus on clarity + action

Constraints  
- No tools  
- No storage  
- No bash/python  
- Must stay lightweight

Acceptance criteria  
1) Output always has 4 sections  
2) Insights are short and relevant  
3) Decision is decisive (no “it depends”)  
4) Learning is actionable

Test  
/decision-flow: Event-driven system, startup MVP, small team  

Expected:  
- Insights → short  
- Decision → clear  
- Learning → practical

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
   - Run: `/decision-flow <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/decision-flow <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/decision-flow/SKILL.md
```
Expected: `PASS`.
