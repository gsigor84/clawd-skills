---
name: analyze-file
description: "name: analyze-file"
---

name: analyze-file
description: "Trigger: /analyze-file: <path + optional constraints>. Run extract → analyze → adapt → decide → upgrade in one flow."

analyze-file

Goal  
Take a file, extract key concepts, analyze them, adapt to constraints, make a decision, and detect upgrade signals.

Trigger  
/analyze-file: <path + optional constraints>

Inputs  
- path (required): file path  
- constraints (optional): one short line  

Output (strict)  
Return EXACTLY:

Concept: <selected concept>
Decision: <clear choice>
Risk: <main downside>
Upgrade: <next system upgrade trigger>

Rules  
- Select ONE best concept (highest impact)  
- Do NOT list multiple concepts  
- Keep output to 4 lines only  
- No explanations  
- No paragraphs  

Execution (internal, do not output)  
1) extract-concept → get concepts  
2) pick best concept  
3) analyze-lens  
4) if constraints exist → constraint-adapter  
5) decision-maker  
6) upgrade-trigger  

Constraints  
- No tools, no scripts  
- No storage  
- Single-pass execution  
- Keep it fast  

Failure  
- If file unreadable →  
ERROR: Unable to read file

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
   - Run: `/analyze-file <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/analyze-file <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/analyze-file/SKILL.md
```
Expected: `PASS`.
