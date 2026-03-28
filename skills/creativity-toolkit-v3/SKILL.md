---
name: creativity-toolkit-v3
description: "Mid-task creativity reset toolkit. Invoke when stuck — blank page, fear, scattered thoughts, overthinking, low energy, endless tweaking. Selects the right technique for your exact situation and tells you what to do in the next 5 minutes."
---

# creativity-toolkit-v3

## Trigger

```bash
/creativity-toolkit-v3 --task "<what you are working on>" --problem "<blank page|fear|scattered|overthinking|low energy|tweaking>"
```

## Goal
Pick 1–3 short, actionable techniques that get you moving *now* (5–15 minutes) based on the failure mode you’re in, then end with a single concrete first action for the next 5 minutes.

## Use
- Blank page — no idea where to start
- Fear or perfectionism blocking you from shipping
- Scattered thoughts, can't focus
- Overthinking, analytical lock
- Low energy, physical inertia
- Endless tweaking, can't declare done

## Inputs
- `--task`: what you are working on right now (video prompt, marketing copy, strategy doc, etc.)
- `--problem`: the failure mode you are in (blank page | fear | scattered | overthinking | low energy | tweaking)

## Outputs
- 1-3 technique cards matched to your problem
- Each card includes: Name, Timer, Steps, Template, Failure-mode fix
- Final line: "Your next 5 minutes: [exact first action]"

## Failure modes
- No --problem provided: ask "What's stopping you right now?" and map answer to nearest problem type
- Technique doesn't resonate: offer the next technique in the same problem group
- All techniques tried: run /creativity-toolkit-v3 with --problem "blank page" as a reset

## When invoked

1) Read `--task` and `--problem`.
2) Match `--problem` to the technique library.
3) Select **1–3** most relevant techniques.
4) For each technique output:
   - Name
   - Timer
   - Steps
   - Template
   - Failure-mode fix
5) End with:

> **Your next 5 minutes:** [exact first action]

## Technique selection rules (deterministic)

- If `--problem` is **blank page**: prioritise techniques that create an immediate entry point (questions, quotas, rewriting, first-impulse).
- If `--problem` is **fear**: prioritise techniques that demote fear / flip blurts / restore agency.
- If `--problem` is **scattered**: prioritise techniques that turn chaos into order (coins/arranging, static dump, clean sweep, box).
- If `--problem` is **overthinking**: prioritise techniques that inject randomness/noise or bypass judgement (quota, mashup, lexical edges, physical verb).
- If `--problem` is **low energy**: prioritise physical resets / grooming / expand-from-compression.
- If `--problem` is **tweaking**: prioritise shipping thresholds and stop rules (violent execution / leaving-without-you style).  
  If no dedicated “shipping” technique is available, fall back to the closest quota/timebox technique.

## Technique library (grouped lookup)

### blank page (starting)
- Verb Embodiment
- The 20-Question Probe
- The 5-Way Rewrite
- The 20-Question Primer
- The 20-Question Excavation
- The 20-Question Micro-Dive
- First Impulse Retrieval
- The Aggressive Idea Quota
- The Aggressive Quota Sprint
- Lexical Edge-Scratching

### fear / perfectionism
- The Boundary Defense Letter
- The Blurt-to-Affirmation Flip
- The Passenger-Seat Demotion
- True North Calibration

### scattered / overwhelmed
- Micro-Chaos Arranging
- Order from Chaos (Coin Arrangement)
- The Coin Chaos Resolution
- The Chaos Arranger
- The Mental Static Dump

### overthinking / analytical lock
- Lexical Edge-Scratching
- The 20-Minute Visual Mashup
- 20-Minute Image Tear
- The Aggressive Idea Quota
- The Aggressive Quota Sprint

### low energy / inertia
- Physical Verb Translation
- Do a Verb Physical Reset
- The Shrink-and-Expand Reset
- The Expansive Egg
- The "Dress for the Affair" Refresh
- The Shandy Shift

### tweaking / endless editing
- The Objective Validation Check

## Acceptance tests

```bash
1. blank page selection
   Invoke: `/creativity-toolkit-v3 --task "video prompt" --problem "blank page"`
   Expected: output contains 1–3 technique cards from the "blank page" group
             and ends with: "Your next 5 minutes:".

2. fear selection
   Invoke: `/creativity-toolkit-v3 --task "marketing copy" --problem "fear"`
   Expected: output includes at least one of:
             - The Boundary Defense Letter
             - The Blurt-to-Affirmation Flip
             - The Passenger-Seat Demotion

3. missing problem (negative case)
   Invoke: `/creativity-toolkit-v3 --task "strategy doc"`
   Expected: asks exactly: "What's stopping you right now?" (and does not hallucinate a problem).

4. scattered ordering
   Invoke: `/creativity-toolkit-v3 --task "writing" --problem "scattered"`
   Expected: output includes at least one of:
             - Micro-Chaos Arranging
             - The Coin Chaos Resolution
             - The Mental Static Dump
```

## Technique cards (canonical)

> Each technique below is the canonical card the skill should output when selected.

### Verb Embodiment
- **Timer:** 5–10 minutes
- **Steps:** Pick an action verb (e.g., "squirm," "dart," "twirl") and physically act it out. Extend it into a complete physical sequence. Notice new angles/rhythms.
- **Template:** Verb chosen: [ ] -> Physical actions taken: [ ] -> New movement/idea discovered: [ ].
- **Failure-mode fix:** If self-conscious, do a mindless chore (e.g., dishes), hum a rhythm, and match movement to the beat.

### Micro-Chaos Arranging
- **Timer:** 5 minutes
- **Steps:** Toss small objects (coins/paper clips). Rearrange into a pattern that feels resolved/harmonious.
- **Template:** Objects used: [ ] -> Starting state: Random -> Final shape: [ ] -> Application to current project: [ ].
- **Failure-mode fix:** If no pleasing pattern emerges, force a simple cross/star grouping to trigger order.

### The 20-Question Probe
- **Timer:** 15 minutes
- **Steps:** Write the subject. Write 20 rapid-fire questions (environment, lighting, history, etc.). Don’t answer yet.
- **Template:** Subject: [ ] -> Q1: [ ] -> ... -> Q20: [ ].
- **Failure-mode fix:** If stuck at 10, switch to sensory/spatial questions.

### Lexical Edge-Scratching
- **Timer:** 10 minutes
- **Steps:** Look up your project’s primary word in a dictionary. Read before/after adjacent words. Force unexpected connections.
- **Template:** Core Word: [ ] -> Preceding Word: [ ] -> Following Word: [ ] -> Unexpected Connection: [ ].
- **Failure-mode fix:** If adjacent words are just variants, skip ahead three pages and pick a random word.

### The 5-Way Rewrite
- **Timer:** 5 minutes
- **Steps:** Copy your best sentence in the middle of a page. Write two different lead-in sentences and two different follow-on sentences. Cross out the original.
- **Template:** Pre 1: [ ] -> Pre 2: [ ] -> [CROSS OUT ORIGINAL] -> Post 1: [ ] -> Post 2: [ ].
- **Failure-mode fix:** If stuck, say the sentence aloud in 5 emotional tones and write the best variation.

### 20-Minute Image Tear
- **Timer:** 20 minutes
- **Steps:** Tear through magazines fast; collect images relevant to the problem; arrange into a cluster.
- **Template:** Base problem: [ ] -> Images collected: [ ] -> Theme/solution discovered: [ ].
- **Failure-mode fix:** No magazines: draw speech balloons on paper, mute TV, invent dialogue.

### The Shrink-and-Expand Reset
- **Timer:** 5 minutes
- **Steps:** Curl into the smallest ball possible (floor). Hold until you need to move. Expand into a new shape, then start the task.
- **Template:** Curled small -> Expansion taken: [ ] -> Resulting idea/momentum: [ ].
- **Failure-mode fix:** Can’t get on floor: cluster desk items tightly, then stretch them into a wide pattern.

### Order from Chaos (Coin Arrangement)
- **Timer:** 5–10 minutes
- **Steps:** Toss coins/objects. Move them into geometries until it feels harmonious. Then start work immediately.
- **Template:** Toss -> Observe -> Arrange into harmony.
- **Failure-mode fix:** Force order by aligning into a rigid square.

### The 20-Minute Visual Mashup
- **Timer:** 20 minutes
- **Steps:** Tear through magazines/books for images/words; glue into an intuitive arrangement.
- **Template:** Rapid selection -> Tearing -> Intuitive arrangement.
- **Failure-mode fix:** If overthinking, restrict to tearing out only one colour.

### The 20-Question Primer
- **Timer:** 10–15 minutes
- **Steps:** Before starting, write 20 questions about the subject. Don’t answer; use it to prime investigation.
- **Template:** 1..20 questions.
- **Failure-mode fix:** At Q10, apply 5Ws to a mundane detail.

### Physical Verb Translation
- **Timer:** 5 minutes
- **Steps:** Stand up. Choose a verb (squirm/dart/twirl). Act it out fully. Return to work with momentum.
- **Template:** Verb -> Embodiment -> Exaggeration -> Work entry.
- **Failure-mode fix:** Too self-conscious: curl into a tight ball then stretch fast.

### Do a Verb Physical Reset
- **Timer:** 5 minutes
- **Steps:** Pick an action verb and act it out physically. Extend into a continuous phrase to break loops.
- **Template:** Verb: [ ] -> Physical extension: [ ] -> Mental shift: [ ].
- **Failure-mode fix:** Use a microscopic verb (blink/tap) rhythmically until you find a groove.

### The Aggressive Idea Quota
- **Timer:** 2 minutes
- **Steps:** Generate 60 ideas/variations as fast as possible; push past obvious tier.
- **Template:** Target: [ ] -> Ideas 1–20 obvious -> 21–40 weird -> 41–60 stretch.
- **Failure-mode fix:** If you freeze, lower to 20 but keep the same 2-minute timer.

### The Coin Chaos Resolution
- **Timer:** 5–10 minutes
- **Steps:** Toss coins/objects and arrange until visually resolved.
- **Template:** Initial state: [ ] -> Final arrangement: [ ].
- **Failure-mode fix:** Sort objects by size/type to force immediate order.

### The 20-Question Excavation
- **Timer:** 15 minutes
- **Steps:** Write 20 questions about the specific component you’re tackling.
- **Template:** Topic: [ ] -> Questions 1–20.
- **Failure-mode fix:** Use 5Ws on tiny mundane details.

### The Boundary Defense Letter
- **Timer:** 5 minutes
- **Steps:** Write a firm letter to fear: it can be present but cannot decide/drive.
- **Template:** "Dear Fear… you may [panic], but you may not [decide/drive]."
- **Failure-mode fix:** Speak the boundary out loud and do one tiny mechanical action.

### The "Dress for the Affair" Refresh
- **Timer:** 15–20 minutes
- **Steps:** Groom/change clothes; clear desk; open window; return as if meeting inspiration.
- **Template:** [ ] Groom [ ] Dress sharply [ ] Clear desk [ ] Refresh room.
- **Failure-mode fix:** If you can’t leave, tidy the immediate desk surface and put on a jacket/accessory.

### The Blurt-to-Affirmation Flip
- **Timer:** 10 minutes
- **Steps:** Write negative blurts. Rewrite each into a positive (or possible) affirmation. Read aloud.
- **Template:** Blurt: [ ] -> Flip: [ ].
- **Failure-mode fix:** If it feels fake, phrase as possibility: “I am capable of learning…”

### The Aggressive Quota Sprint
- **Timer:** 5 minutes
- **Steps:** Pick mundane object. Write 60 uses before timer ends. Then pivot to your task.
- **Template:** Target object: [ ] -> 1…60 uses.
- **Failure-mode fix:** If you freeze, list physically impossible uses to keep moving.

### The Chaos Harmonizer
- **Timer:** 5–10 minutes
- **Steps:** Toss small uniform items; arrange into balanced geometry; then start work.
- **Template:** Scatter -> Arrange -> Resume.
- **Failure-mode fix:** If frustrating, sweep items up and re-toss to reset.

### The Shandy Shift
- **Timer:** 15–30 minutes
- **Steps:** Step away; groom; dress sharply; clear workspace; change atmosphere; return and work.
- **Template:** Checklist: [ ] step away [ ] groom [ ] dress [ ] clear desk [ ] refresh room [ ] resume.
- **Failure-mode fix:** Strut for 1 minute to embody upgraded posture.

### The Ten-Year-Old Clarity Check
- **Timer:** 10 minutes
- **Steps:** Explain what you’re doing as if to a 10-year-old. Distil into one intention (spine).
- **Template:** "I intend to [ ] . The main point is [ ]."
- **Failure-mode fix:** Use only 1–2 syllable words or draw a stick figure.

### First Impulse Retrieval
- **Timer:** 5 minutes
- **Steps:** Find the very first note/research item from project start. Write what compelled you.
- **Template:** "My original impulse was [ ]. Does my work support this? [Y/N]"
- **Failure-mode fix:** If first item doesn’t spark, check first three; pick the most exciting.

### True North Calibration
- **Timer:** 10 minutes
- **Steps:** Write ultimate project goal. Identify emotional true north. Decide based on maximising it.
- **Template:** Goal: [ ] -> True north emotion: [ ] -> Choose path that maximises it.
- **Failure-mode fix:** If unclear, list 3 emotions and allocate 10 points across them.

### The Objective Validation Check
- **Timer:** 15 minutes
- **Steps:** Get a trusted validator. Show raw work for 5 mins. Ask: “Do we care about this?” Listen.
- **Template:** "Please tell me honestly: Do we care about this?"
- **Failure-mode fix:** If they start fixing, redirect to feelings/impact only.

### The Witness-Only Sync
- **Timer:** 10 minutes
- **Steps:** One speaker shares for 5 mins; others witness only; no fixing; return to work.
- **Template:** "I need you to witness only. No fixing."
- **Failure-mode fix:** If interrupted, restate boundary and continue.

### The Self-Reliance Audit
- **Timer:** 5 minutes
- **Steps:** Ask: if collaborator removed, does my part stand? Identify weak spot; fortify it.
- **Template:** "I’m expecting [X] to save me. Instead I will do [Y]."
- **Failure-mode fix:** If can’t fix now, explicitly flag vulnerability to collaborator.

### The Competitor-to-Collaborator Pivot
- **Timer:** 5 minutes
- **Steps:** Identify competitor’s strength; write why it works; integrate; propose micro-collab.
- **Template:** "Your approach to [ ] is strong — can we combine for 5 minutes?"
- **Failure-mode fix:** If unavailable, isolate their mechanism and apply it solo.

### The Chaos Arranger
- **Timer:** 5–10 minutes
- **Steps:** Toss small items and arrange into a resolved pattern; then resume work.
- **Template:** Toss -> Arrange -> Acknowledge resolution -> Resume.
- **Failure-mode fix:** If frustrating, sweep items away aggressively as the reset.

### The Mental Static Dump
- **Timer:** 15–20 minutes
- **Steps:** Write 3 pages stream-of-consciousness dumping distractions. Discard/hide pages. Resume.
- **Template:** "Right now I am distracted by…"
- **Failure-mode fix:** Write “I don’t know what to write” until a real thought appears.

### The Expansive Egg
- **Timer:** 5 minutes
- **Steps:** Curl into tight ball; hold; then expand/stretch; carry momentum into work.
- **Template:** N/A
- **Failure-mode fix:** Hold 60 seconds; breathe; stand arms wide.

### The 20-Question Micro-Dive
- **Timer:** 10–15 minutes
- **Steps:** Write 20 questions; pick most intriguing; answering it becomes next action.
- **Template:** 1..20 questions -> pick #?
- **Failure-mode fix:** Use absurd micro-details to reach 20.

### The Passenger-Seat Demotion
- **Timer:** 5 minutes
- **Steps:** Name the fear; declare it has a seat but no vote; execute the scary choice.
- **Template:** "Dearest Fear… you may sit, but you may not drive."
- **Failure-mode fix:** Do it in a sandbox/duplicate file first, then patch.
