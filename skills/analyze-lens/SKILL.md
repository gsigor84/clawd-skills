---
name: analyze-lens
description: "Trigger: /analyze-lens: <concept>. Analyze a concept using a small set of thinking lenses (Linear↔Painterly, Surface↔Depth, Closed↔Open, Multiple↔Fused, Absolute↔Relative clarity) to produce concise, insight-focused bullets."
---

## analyze-lens

### Inputs
- **concept**: a short phrase (preferred) or 1–2 sentences.
- Optional: **context** (one line) if the concept is ambiguous.

### Output (strict)
- 3–5 bullets preferred (max 6)
- Include only relevant lenses (skip the rest)
- Each bullet is: Lens: insight (one line only)

Insight quality:
- Each insight should (when possible) include:
  • implication
  • optimization
  • or trade-off
- Do NOT force this if it reduces clarity

Optional:
- One final bullet allowed:
  Implication: <short takeaway>
- Only include if high value (max 10 words)

Rules:
- No paragraphs
- No explanations outside bullets
- No repetition
- Compress if output becomes verbose

### Steps (single responsibility)
1) Restate the concept in 5–12 words (only if needed for clarity).
2) Select **2–4** lenses that create the most contrast/insight for this concept.
3) For each selected lens, write one sharp insight describing what the concept implies, optimizes for, or risks along that axis (keep one line only).
4) If useful, add **one** final bullet: `Implication: ...` (optional; keep short).

### Lenses (choose selectively)
- **Linear vs Painterly** — rigid plan/sequence vs adaptive, iterative shaping.
- **Surface vs Depth** — immediate features/symptoms vs underlying drivers/causes.
- **Closed vs Open** — self-contained/internal vs interactive with an environment.
- **Multiple vs Fused** — separable parts/interfaces vs unified, tightly coupled whole.
- **Absolute vs Relative clarity** — fully specified vs deliberately scoped/spotlit.

## Guardrails (anti-crash)
- Do **not** call other skills.
- Do **not** store anything.
- Do **not** use bash/python/tools.
- Do **not** turn this into a multi-step pipeline.
- If the concept is too broad/ambiguous, ask **one** clarifying question and stop.

## Acceptance criteria (must-pass)
- Produces ≤6 bullets and avoids long reasoning chains.
- Uses only relevant lenses (can be as few as 1–2).
- Each included lens yields a concrete insight (implication/optimization/risk), not a definition.

## Tests
1) Input: `/analyze-lens: Event-Driven Reactivity`
   - Output includes 3–5 bullets; likely includes **Painterly**, **Depth**, **Open**, **Multiple** (or a relevant subset).
2) Input: `/analyze-lens: "A checklist for weekly planning"`
   - Output is short; likely includes **Linear** and **Absolute clarity**; skips unrelated lenses.
3) Input: `/analyze-lens: "Freedom"`
   - Skill asks exactly **one** clarifying question (scope/context) and stops.

## Agent Loop Contract (agentic skills only)
- This skill is **single-turn**: one analysis output (or one clarifying question) per invocation.
- No background tasks, no retries, no external calls.

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
   - Run: `/analyze-lens <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/analyze-lens <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/analyze-lens/SKILL.md
```
Expected: `PASS`.
