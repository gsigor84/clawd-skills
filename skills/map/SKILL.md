---
name: map
description: "Trigger: /skill map: <input-text>. Takes the raw concept list from /skill extract (STEP 1 output) and produces ONLY STEP 2 — IDENTIFY BACKBONE and STEP 3 — MAP RELATIONSHIPS (backbone concepts + mapping)."
---

## map — STEP 2–3 only

### Input format
Paste the full output from `/skill extract` (must include the header `## STEP 1 — EXTRACT` and the bullet list).

### Hard rules
- Perform **ONLY**:
  - `STEP 2 — IDENTIFY BACKBONE`
  - `STEP 3 — MAP RELATIONSHIPS`
- **No STEP 1 re-extraction. No STEP 4 writing. No saving.**
- **Context-only**: treat the provided STEP 1 list as the exclusive source of truth.
- No hallucination: do not add concepts that are not in STEP 1.

### Procedure

1) Parse STEP 1 list
- Read the bullets under `## STEP 1 — EXTRACT`.
- If the list is missing/empty: return a short error asking the user to paste STEP 1 output.

2) STEP 2 — IDENTIFY BACKBONE (4–6 items)
- Choose **4–6** items from the STEP 1 list that are the best structural “bridges”.
- Output:

```md
## STEP 2 — IDENTIFY BACKBONE
**Backbone Concepts**
- <backbone 1>
- <backbone 2>
...
```

3) STEP 3 — MAP RELATIONSHIPS
- For every **non-backbone** item from STEP 1:
  - assign it to exactly **one** backbone concept
  - explain **WHY** (mechanism-level). Since you only have the list (no definitions), your justification must be conservative and based on the *structure/signals in the names* (e.g., “X is a monitoring metric → belongs under Observability”), and if you cannot justify, assign it to the closest backbone and explicitly note: “(name-only mapping; insufficient detail in STEP 1 list)”.
- Output:

```md
## STEP 3 — MAP RELATIONSHIPS
- <concept> → **<backbone>** (why)
...
```

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
   - Run: `/map <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/map <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/map/SKILL.md
```
Expected: `PASS`.
