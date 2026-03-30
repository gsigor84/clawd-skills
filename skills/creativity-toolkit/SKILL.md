---
name: creativity-toolkit
description: "Trigger: /creativity-toolkit <task>. A collaborative creativity framework modeled on the Inklings with resonators who encourage, critics who oppose honestly, and group flow."
---

# creativity-toolkit

## Description
A collaborative creativity framework modeled on the Inklings — C.S. Lewis, J.R.R. Tolkien, Charles Williams, and Owen Barfield. Four agents (Researcher, Selector, Generator, Critic) collaborate with:
- **Resonators** who encourage good ideas with unstinted, specific praise
- **Critics** who oppose honestly through "dialectical swordplay" and "rational opposition"
- **Group flow** where blended perspectives produce better output than any single agent could alone

The skill implements a 6-phase pipeline that cycles through research, selection, strategic disruption, creative variation, generation, and critique — with built-in stagnation detection to trigger re-framing when progress stalls.

## Trigger
`/creativity-toolkit <task>`

## Pipeline Overview

```
RESEARCHER → SELECTOR → STAGNATION CHECK → OBLIQUE STRATEGY → SCAMPER → GENERATOR → CRITIC
                                                    ↓ (if stagnated)
                                              OBLIQUE STRATEGY → RE-SELECT
```

## The 4 Agents

### 1. RESEARCHER
- **Role**: Gather raw material, discover analogies, find external stimuli
- **Temperature**: 0.7 (exploratory, wide-ranging)
- **Output**: Raw research, facts, analogies, external references, "small sparks"
- **Handoff**: Passes candidate concepts to SELECTOR with 3-5 promising directions

### 2. SELECTOR
- **Role**: Evaluate, rank, and choose the most promising directions
- **Temperature**: 0.3 (discriminating, focused)
- **Output**: Shortlisted concepts (1-2) with rationale
- **Handoff**: Passes selected concept to GENERATOR with explicit rejection notes on what was discarded

### 3. GENERATOR
- **Role**: Produce actual creative outputs — drafts, ideas, solutions, variations
- **Temperature**: 0.9 (associative, divergent)
- **Output**: Multiple variations, "half-formed notions", draft concepts
- **Handoff**: Passes raw outputs to CRITIC with "paint still wet" framing

### 4. CRITIC
- **Role**: Apply "brutal frankness" — rigorous, specific critique that improves work
- **Temperature**: 0.4 (constructive, tough but fair)
- **Output**: Specific, actionable criticism + praise for what works
- **Handoff**: Returns to SELECTOR with revision direction OR declares complete

## The Inklings Collaboration Model

### Resonators (Built into all agents)
- Provide **unstinted, specific praise** before criticism
- Show genuine interest in rough, half-formed ideas
- Apply friendly pressure: "You can do better than that. Better, please!"
- Help push work from private sphere to public completion

### Critics (Designated role in CRITIC phase)
- Practice **"dialectical swordplay"** — fierce intellectual conflict without personal malice
- Offer **specific, actionable suggestions** not just diagnoses
- Distinguish between "I don't like this" (subjective) and "This isn't working" (objective)
- Never cross into **dismissive condemnation** (the Hugo Dyson failure mode)

### Group Flow Conditions
1. **Clear but open-ended goal** — enough focus for problem-finding creativity
2. **Deep listening** — no "writing the script in your head"
3. **"Yes, and..." principle** — accept and build on others' ideas
4. **Equal participation** — no dominant egos
5. **Blended egos** — group success over individual glory
6. **Psychological safety** — safe to share "notions" and fail

## Step-by-Step Procedure

### Phase 1: RESEARCHER (temperature: 0.7)
1. Receive the creative task
2. Conduct divergent search for:
   - Analogies from unrelated domains
   - Historical precedents
   - Cross-disciplinary references
   - "Small sparks" — fragmentary ideas worth exploring
3. Output: Raw material bundle with 5+ promising directions

### Phase 2: SELECTOR (temperature: 0.3)
1. Review RESEARCHER output
2. Apply criteria: originality, resonance, feasibility, "impossible-beautiful" potential
3. Rank and select 1-2 directions
4. Explicitly document what was rejected and why
5. Output: Selected concept + rejection notes

### Phase 3: STAGNATION CHECK
1. Assess if current direction shows:
   - Repetitive output
   - Diminishing novelty
   - Circular reasoning
   - Energy drop
2. If stagnated → trigger OBLIQUE STRATEGY
3. If moving → proceed to GENERATOR

### Phase 4: OBLIQUE STRATEGY (when stagnated)
1. Introduce strategic disruption:
   - Random constraint injection
   - Perspective inversion (invert assumptions)
   - Analogy transposition (apply solution from unrelated field)
   - "What would a beginner do?" question
   - "What would the opposite approach be?"
2. Output: Re-framed problem + 3+ new angles

### Phase 5: SCAMPER (sub-phase before GENERATOR)
Apply SCAMPER operators to selected concept:
- **S**ubstitute — what if X instead of Y?
- **C**ombine — merge with another concept?
- **A**dapt — how does this apply elsewhere?
- **M**odify — change scale, intensity, context?
- **P**ut to another use — what else could this be?
- **E**liminate — remove what?
- **R**everse — do the opposite?

### Phase 6: GENERATOR (temperature: 0.9)
1. Receive selected concept + SCAMPER variations
2. Produce multiple outputs rapidly:
   - 3+ distinct variations
   - Include intentionally "bad" options to normalize failure
   - Treat as "notions" — half-formed, fluid
3. Output: Draft concepts with explicit "still wet" framing

### Phase 7: CRITIC (temperature: 0.4)
1. Receive GENERATOR output
2. Apply "brutal frankness":
   - Start with specific praise ("This works because...")
   - Identify specific weaknesses ("X fails because...")
   - Offer actionable alternatives ("Try instead...")
3. Distinguish critique of work from critique of person
4. Either:
   - Return to SELECTOR with revision direction (loop)
   - Declare complete with summary

## Failure modes

| Failure Mode | Symptom | Recovery |
|--------------|---------|----------|
| **Groupthink** | Harmony prioritized over critical analysis | Assign devil's advocate; force dissent |
| **Production blocking** | One agent dominates, others passive | Rotate facilitation; use "brainwriting" (independent first) |
| **Social inhibition** | Ideas withheld from fear of judgment | Increase psychological safety; normalize "dumb questions" |
| **Dismissive condemnation** | Criticism crosses into shutdown (Hugo Dyson mode) | Reset to "care first"; rebuild trust |
| **Stagnation loop** | Circular refinement without progress | Trigger OBLIQUE STRATEGY |
| **Collaboration overload** | Too connected, diminishing returns | Introduce breaks; allow solo incubation |
| **Ego-clash** | Dominant personality silences others | Enforce equal participation; blend egos |

## Acceptance tests

1. **Behavioral (positive): generates output**
   - Run: `/creativity-toolkit write a tagline for coffee`
   - Expected: Contains tagline text

2. **Behavioral (negative): no task**
   - Run: `/creativity-toolkit`
   - Expected: `ERROR: no_task_provided`

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py   /Users/igorsilva/clawd/skills/creativity-toolkit/SKILL.md
```
Expected: `PASS`

4. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py   /Users/igorsilva/clawd/skills/creativity-toolkit/SKILL.md
```
Expected: `PASS`

## Example Invocation

```
/creativity-toolkit Design a new brand identity for an eco-tech startup
```

The pipeline will:
1. RESEARCHER gathers analogies from nature, technology, and business history
2. SELECTOR narrows to 1-2 promising directions
3. STAGNATION CHECK evaluates momentum
4. If needed, OBLIQUE STRATEGY introduces constraint: "Design for a world without color"
5. SCAMPER applies variation operators
6. GENERATOR produces 3+ distinct brand concepts
7. CRITIC provides specific, actionable feedback with praise first

The cycle continues until the output demonstrates group flow — creative work that no single agent could have produced alone.
## Use

Run with `/creativity-toolkit <your creative task in plain english>`. The skill runs a 6-agent pipeline that cycles through research, selection, stagnation check, oblique strategy, SCAMPER, generation, and critique — with Inklings-style collaboration.

## Inputs

Plain english task:
- `/creativity-toolkit write a tagline for X`
- `/creativity-toolkit generate video prompts for Y`
- `/creativity-toolkit create a marketing campaign for Z`

No required flags — just describe your task.

## Outputs

Plain text creative output:
- Taglines, video prompts, campaign concepts, story ideas
- Multiple variations ranked by originality + quality


- `ERROR: no_task_provided` — Use `/creativity-toolkit <task>`
- `ERROR: all_stagnated` — Try a completely different task type


1. **Behavioral: generates output**
   - Run: `/creativity-toolkit write a tagline for coffee`
   - Expected: Contains tagline text

2. **Structural validator**
   - Run: `validate_skillmd.py ~/clawd/skills/creativity-toolkit/SKILL.md`
   - Expected: `PASS`

3. **No invented tools**
   - Run: `check_no_invented_tools.py ~/clawd/skills/creativity-toolkit/SKILL.md`
   - Expected: `PASS`

## Toolset

- `read` — consult research files
- `write` — record observations
- `sessions_spawn` — invoke sub-agents for each pipeline phase


- `read` — consult research files
- `write` — record creative outputs
- `sessions_spawn` — invoke sub-agents
