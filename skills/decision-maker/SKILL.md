---
name: decision-maker
description: "Trigger: /decision-maker: <insights>. Convert 3–6 short insights/trade-offs into a single clear decision."
---

decision-maker

Inputs
- insights (required): 3–6 bullets preferred

Output (strict)
Return EXACTLY one of:

A) If input is unclear/vague/empty:
provide clear insights or trade-offs

B) Otherwise output EXACTLY 3 lines (no extra text):
Decision: <clear choice or direction>
Why: <core reason based on given insights/trade-offs>
Risk: <main downside to accept>

Rules
- Each line: one sentence max, short
- No paragraphs
- No “it depends”, no multiple options
- Base decision ONLY on provided insights (no invention)
- If trade-offs are balanced, choose the option that minimizes irreversible risk
- Single-pass, single-turn
- No chaining
- No storage or memory writes
- No bash, no python, no tools
- If output exceeds 3 lines → compress to required format

Acceptance criteria (must-pass)
1) Output is either the exact failure string OR exactly the 3 required lines
2) Decision is singular and actionable
3) Why and Risk are grounded in provided insights only
4) No extra commentary

Tests
1) /decision-maker: - Faster shipping but more bugs - Better reliability but slower releases - Team is small
2) /decision-maker: - Open increases flexibility but raises security risk - Closed improves reliability but slows adoption
3) /decision-maker: make a decision for my startup

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
   - Run: `/decision-maker <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/decision-maker <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/decision-maker/SKILL.md
```
Expected: `PASS`.
