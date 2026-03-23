---
name: upgrade-trigger
description: "Trigger: /upgrade-trigger: <context>. Detect when a system should move from MVP to next level using concrete signals."
---

upgrade-trigger

Goal  
Detect when constraints have changed enough to require a system upgrade.

Trigger  
/upgrade-trigger: <context>

Inputs  
- context (required): short description of system state

Output (strict)  
Return EXACTLY one of:

A) If context unclear:  
provide context

B) Otherwise EXACTLY 3 lines:
Signal: <observable trigger>
Meaning: <what it implies about system maturity>
Action: <what to implement next>

Rules  
- Each line: one sentence max  
- No paragraphs  
- No extra text  
- No multiple options  
- Base ONLY on given context  
- Single-pass only  
- No tools, no storage  

Upgrade logic (implicit, do not output)  
- Security critical → Agent Authentication & Authorization  
- Event scale → Event-Driven Reactivity  
- Governance need → Real-Time Compliance Monitoring  
- Multi-agent coordination → Tool & Agent Registry  

Operational signals (implicit)  
- near-miss / incident  
- debugging > building  
- integration drift  
- need for repeatability  

Acceptance criteria  
1) Exactly 3 lines OR failure string  
2) Signal must be observable (real-world symptom)  
3) Meaning must explain system shift  
4) Action must be specific and actionable

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
   - Run: `/upgrade-trigger <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/upgrade-trigger <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/upgrade-trigger/SKILL.md
```
Expected: `PASS`.
