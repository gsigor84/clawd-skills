---
name: integration-guardrail
description: "Trigger: /integration-guardrail: <idea or code>. Enforce that every API/tool goes through a wrapper."
---

integration-guardrail

Goal  
Enforce a simple rule: every API/tool must go through a wrapper.

Trigger  
/integration-guardrail: <idea or code>

Input  
- idea or code snippet

Output (strict)  
Return EXACTLY 2 lines:

Rule: <what wrapper is needed>
Example: <simple wrapper function name>

Rules  
- Keep it very short  
- No explanations  
- No long code  
- Just name the wrapper clearly

Behavior  
- If input mentions API/tool → suggest wrapper name  
- If unclear →  
clarify integration

Acceptance criteria  
1) Exactly 2 lines  
2) Clear wrapper name  
3) No extra text

Tests  

Input:
/integration-guardrail: Stripe payments

Output:
Rule: use a payment wrapper
Example: chargePayment()

---

Input:
/integration-guardrail: OpenAI call

Output:
Rule: use an AI wrapper
Example: generateText()

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
   - Run: `/integration-guardrail <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/integration-guardrail <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/integration-guardrail/SKILL.md
```
Expected: `PASS`.
