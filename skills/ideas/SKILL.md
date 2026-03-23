---
name: ideas
description: "Trigger: /ideas <topic-or-problem> [| inputs: ...]. Generate and prune ideas via SPINE→INPUTS→SCRATCHING→GROUP→PRUNING→TOP IDEAS (pure text, no tools)."
---

# ideas

## Trigger

Trigger when the user types:
- `/ideas <topic-or-problem>`

Optional add-on (same line):
- `| inputs: <references/observations/existing ideas>`

Rules:
- Exactly one topic/problem per run.
- If the topic is missing or only whitespace, fail with the exact error in **Failure modes**.

## Use

Use this skill to generate high-volume, non-obvious ideas without drifting into vagueness.

It follows a deterministic creative loop grounded in three principles:
- **Spine first** (core intention before generating): every output must align to a single underlying motive.
- **Scratching** (remix/borrow/mutate/invert/combine): nothing comes from nowhere; ideas are deliberate recombinations.
- **Editing is the creative act** (prune aggressively): generate many, then score and keep the few that are executable, aligned, and surprising.

## Inputs

One line:
- `topic_or_problem` (required): what you want ideas for.

Optional:
- `inputs` (optional): raw material you already have (references, observations, constraints, existing ideas).

Accepted formats:
- `/ideas Improve onboarding for a B2B SaaS`
- `/ideas Improve onboarding for a B2B SaaS | inputs: target users=finance ops; current flow=7 steps; biggest drop-off=step 3; 3 existing ideas=...`

## Outputs

Output is structured plain text with the following sections in this exact order:

1) `SPINE`
2) `RAW INPUTS`
3) `SCRATCHING IDEAS (15)`
4) `CATEGORIES (3–5)`
5) `PRUNING SCORES`
6) `TOP IDEAS (5–7)`

### Section rules

- **SPINE**: exactly 1 sentence beginning with `Spine:`.
- **RAW INPUTS**: either:
  - `Inputs: (none provided)`
  - OR `Inputs:` followed by 3–8 short bullets.
- **SCRATCHING IDEAS (15)**: exactly 15 items numbered `1)` through `15)`. Each is one sentence.
- **CATEGORIES (3–5)**: 3 to 5 category blocks. Each block:
  - starts with `Category: <name>`
  - lists idea numbers included (e.g., `Ideas: 1, 4, 9`)
  - category names must be drawn from this set only:
    - `practical`
    - `weird`
    - `long-term`
    - `remix`
    - `invert`
- **PRUNING SCORES**: a 15-line table (one per idea) in this exact format:
  - `<n>) E=<0-5> A=<0-5> S=<0-5> TOTAL=<0-15>`
  - where:
    - `E` = executable soon
    - `A` = aligned to spine
    - `S` = surprising
    - `TOTAL` = E+A+S
- **TOP IDEAS (5–7)**: output the 5 to 7 highest TOTAL ideas.
  - Each top idea block must include exactly these fields:
    - `Name:`
    - `One-liner:`
    - `Why non-obvious:`
    - `Next step:`
    - `Collaboration:` with exactly `YES` or `NO`

## Deterministic workflow (must follow)

Tools used: none. Single-pass text transform.

### Boundary rules (privacy + safety)

- Do not request or output secrets.
- Do not include personal data beyond what the user provided.
- No web browsing, no file access, no external calls.
- If the user provides references/notes, treat them as raw material (do not claim they are true beyond what is stated).

### Step 1 — SPINE (core intention)
Write the SPINE as one sentence:
- `Spine: <core intention>`

Deterministic spine rule:
- Convert the user topic into: `help <target> achieve <outcome> under <constraint>`.
- If constraints are present in inputs, use the tightest constraint; otherwise use `limited time/attention` as the default constraint phrase.

### Step 2 — Ask for raw inputs (explicit branch)
If the user did not provide an `| inputs:` segment:
- Still produce the full output.
- In `RAW INPUTS`, write `Inputs: (none provided)`.

If the user did provide `| inputs:`:
- Convert it into 3–8 bullets (split on `;` or `,` where possible).

### Step 3 — SCRATCHING (generate 15)
Generate exactly 15 ideas using only these transformations (each idea must be clearly traceable to one):
- Remix (borrow a pattern from another domain)
- Borrow (copy a known mechanism and adapt)
- Mutate (change one parameter drastically)
- Invert (flip an assumption)
- Combine (merge two mechanisms)

Deterministic coverage rule:
- Ideas 1–5 must be primarily `practical`.
- Ideas 6–10 must be primarily `remix` or `invert`.
- Ideas 11–15 must be primarily `weird` or `long-term`.

### Step 4 — Group into categories (3–5)
Create 3–5 category blocks using only the allowed names.
Deterministic category rule:
- Always include `practical`, `remix`, and `invert`.
- Add `weird` if at least one idea is intentionally odd.
- Add `long-term` if at least one idea requires >30 days.

### Step 5 — PRUNING (score 15 ideas)
Score each idea on:
- E (0–5): could a single person start within 48 hours?
- A (0–5): does it directly serve the SPINE?
- S (0–5): is it meaningfully different from the obvious baseline?

Deterministic scoring rule:
- If an idea requires external partners, legal approval, or new infrastructure, cap E at 2.
- If an idea is a direct restatement of the topic (no new mechanism), cap S at 2.
- TOTAL is computed exactly as E+A+S.

### Step 6 — Select TOP IDEAS (5–7)
Pick the 5–7 ideas with highest TOTAL.
Tie-breakers (in order):
1) higher A
2) higher E
3) earlier idea number

### Step 7 — Add collaboration flag
Set `Collaboration: YES` if the idea requires any of:
- another person/team to ship
- user interviews
- external data
- partnerships

Else `Collaboration: NO`.

## Failure modes

Return exactly one line and nothing else:

- Missing topic:
  - `ERROR: missing_topic. Usage: /ideas <topic-or-problem> [| inputs: ...]`

- Multiple topics:
  - `ERROR: multiple_topics_not_supported. Provide exactly one topic or problem.`

## Toolset

- (none)

## Acceptance tests

1. **Behavioral (negative): missing topic hard-stop**
   - Run: `/ideas`
   - Expected output (exact): `ERROR: missing_topic. Usage: /ideas <topic-or-problem> [| inputs: ...]`

2. **Behavioral: section order is exact**
   - Run: `/ideas Improve onboarding for a B2B SaaS`
   - Expected: output contains the headings in this exact order:
     1) `SPINE`
     2) `RAW INPUTS`
     3) `SCRATCHING IDEAS (15)`
     4) `CATEGORIES (3–5)`
     5) `PRUNING SCORES`
     6) `TOP IDEAS (5–7)`

3. **Behavioral: exactly 15 ideas are produced**
   - Run: `/ideas Improve onboarding for a B2B SaaS`
   - Expected: under `SCRATCHING IDEAS (15)`, there are exactly 15 numbered items `1)` through `15)`.

4. **Behavioral: categories are limited to the allowed set**
   - Run: `/ideas Improve onboarding for a B2B SaaS`
   - Expected: every `Category:` name is one of: `practical`, `weird`, `long-term`, `remix`, `invert`.

5. **Behavioral: pruning table has 15 lines and correct fields**
   - Run: `/ideas Improve onboarding for a B2B SaaS`
   - Expected: PRUNING SCORES contains exactly 15 lines matching:
     - `<n>) E=<0-5> A=<0-5> S=<0-5> TOTAL=<0-15>`

6. **Behavioral: top ideas include required fields**
   - Run: `/ideas Improve onboarding for a B2B SaaS`
   - Expected: each entry under `TOP IDEAS (5–7)` includes exactly these field labels:
     - `Name:`
     - `One-liner:`
     - `Why non-obvious:`
     - `Next step:`
     - `Collaboration:`

7. **Behavioral: inputs branch works**
   - Run: `/ideas Improve onboarding for a B2B SaaS | inputs: drop-off at step 3; users are finance ops; must ship in 2 weeks`
   - Expected: `RAW INPUTS` is not `Inputs: (none provided)` and contains bullets derived from the provided inputs.

8. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/ideas/SKILL.md
```
Expected: `PASS`.

9. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/ideas/SKILL.md
```
Expected: `PASS`.
