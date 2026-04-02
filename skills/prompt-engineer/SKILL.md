---
name: prompt-engineer
description: "# prompt-engineer — Design, critique, and iterate prompts that reliably produce the desired output by enforcing structure (Persona/Task/Context/Format), adding grounding + permission-to-fail, and using multi-branch exploration + adversarial critique for complex tasks. Also supports video prompt engineering and Nietzschean analysis frames."
---

# prompt-engineer

Design, critique, and iterate prompts that reliably produce the desired output by enforcing structure (Persona/Task/Context/Format), adding grounding + "permission to fail", and using multi-branch exploration and adversarial critique when the task is complex.

## Workflows

### Full pipeline: strategy → concept → video asset

The complete chain has three distinct stages. **Do not skip or automate the handoff between stages 1 and 2** — that is where strategic intent becomes creative story, and that decision shapes everything that follows.

**Stage 1 — Strategy** (`/marketing-knowledge`)
Build the marketing strategy before anything else. This gives you the ICP, enemy, value thesis, and proof points that will govern the creative decisions.

**Stage 2 — Concept** (`/creativity-toolkit`)
Use the strategy output from Stage 1 to generate the actual marketing concept — headline, subheadline, proof bar, CTA, campaign package. This is the creative translation of strategic intent.

**Stage 3 — Video prompt** (`/prompt-engineer --video`)
Extract the narrative beats from the Stage 2 output (the hook, the proof moment, the CTA) and translate them into a structured video prompt using the core dimensions, camera instructions, and advanced techniques.

**Stage 4 — Asset generation**
Paste the Stage 3 prompt into your video model (Veo, Runway, Kling, Sora, etc.).

---

### The handoff rule

Between Stage 1 and Stage 2, stop and decide explicitly:
- What is the *one* thing this video needs to make someone feel?
- What is the single proof point that earns that feeling?
- What is the enemy we are defeating in the viewer's mind?

Do not proceed to Stage 2 until those three questions have answers. The output of Stage 2 should be directly traceable to the strategic decisions made at this handoff.

---

### Example full chain

```
/stage-1: /marketing-knowledge design a video campaign for OpenClaw targeting B2B SaaS teams done babysitting generic AI agents
→ ICP: B2B SaaS teams, Enemy: brittle generic assistants, Value: self-improving, Proof: learning receipts

/stage-2: /creativity-toolkit landing page hero for OpenClaw
→ Hook: "The AI agent that improves itself by surviving failure"
   Proof bar: learning receipts | error-reduction metrics | session logs
   CTA: Book a demo

/stage-3: /prompt-engineer --video 12-second cinematic demo showing an AI agent improving itself after a mistake
→ Structured video prompt with camera angles, multi-shot timing, anchor prompts

/stage-4: Paste into Veo/Runway/Kling → finished video asset
```

### When to use each skill

| Stage | Task | Skill to use |
|-------|------|-------------|
| 1 | Marketing strategy, ICP, positioning, enemy, proof | `/marketing-knowledge` |
| 2 | Build the marketing concept, copy, or campaign | `/creativity-toolkit` |
| 3 | Turn concept into video prompt | `/prompt-engineer --video` |
| 3-alt | Nietzschean conflict analysis | `/prompt-engineer --nietzsche` |
| 4 | Text/LLM prompt (not video) | `/prompt-engineer` (default) |

---

## Trigger
`/prompt-engineer <goal + constraints + context>`
`/prompt-engineer --video <goal + format + duration>`
`/prompt-engineer --nietzsche <text or idea>`

Use this skill when:
- A prompt is producing vague/generic/unpredictable output.
- You need a reusable prompt template for a recurring task (writing, coding, research, planning).
- You need to reduce hallucinations by adding grounding constraints and explicit failure behaviour.
- A task is complex enough to benefit from multi-branch ideation (Trees of Thought) or adversarial critique (playoff method).
- You are writing prompts for AI video generation tools (Veo, Runway, Kling, etc.).
- You want a Nietzschean analysis frame that translates conflict vs conformity into an actionable, everyday language.

---

## Use

### Default mode (prompt engineering)

1. **Clarify intent (offline first):** write a 1–3 sentence goal and what "good" looks like.
2. **Draft a structured prompt** using the Four Pillars:
   - Persona
   - Task
   - Context (ABC: Always Be Contexting)
   - Format (explicit output requirements)
3. **Add reliability constraints**:
   - "If you don't know / it's not in the provided context, say 'I don't know'."
   - Ask the model what questions it needs answered to do the task well.
4. **If complex:** choose one:
   - **CoT:** request step-by-step reasoning *internally*, then a clean final answer.
   - **ToT:** generate 2–4 distinct branches, evaluate, then synthesise a "golden path".
   - **Adversarial validation:** competing drafts + harsh critic + final synthesis.
5. **Iterate:** treat poor output as a signal that the prompt is missing constraints/context; refine and re-run.
6. **Save winners:** capture the final prompt as a template for reuse.

---

### --video mode (video prompt engineering)

When invoked as `/prompt-engineer --video <goal + format + duration>`, design prompts for AI video generation models. Video is *time + motion + audio + visual framing* — the Four Pillars still apply, but these additional dimensions must be governed explicitly.

#### The 5 Levels of Video Prompt Mastery

| Level | Name                  | What you control                                                 |
|-------|-----------------------|-------------------------------------------------------------------|
| 1     | Simple Idea           | Basic intent, no structure — high inconsistency                  |
| 2     | Structured Prompting  | Subject, action, camera, style                                   |
| 3     | Reference Control     | Image/video references for visual consistency                   |
| 4     | Leverage & Scaling    | Custom GPTs write optimised prompts for you                      |
| 5     | Full Pipeline         | Multi-tool production (storyboard → generate → voice → lip-sync)|

#### Core Dimensions (always specify)

- **Subject** — who or what is the focus
- **Environment** — where the scene takes place
- **Action** — what is happening
- **Camera shot** — framing (close-up, wide, over-the-shoulder)
- **Camera movement** — tracking shot, slow push-in, orbit, tilt, zoom
- **Visual style** — realistic, cinematic, anime, lo-fi, 1980s grainy film
- **Voice/Audio** — narration, on-screen text, SFX, music cues, silence
- **Duration** — target length in seconds
- **Mood/Tone** — tense, calm, energetic, authoritative, playful
- **Avoid** — known model weaknesses (text overlays, lip sync, large crowds, long continuous scenes)

#### Advanced Techniques

**Multi-Shot Prompting**
Define multiple sequential shots in a single prompt. For each cut, specify camera angle, movement, timing, and action. Two methods:

- **Timestamp prompting** — assign actions to exact time intervals
  *"0–3s: camera zooms in on astronaut. 3–6s: tilt down to recorder. 6–8s: tilt back up, astronaut looks at sky."*
- **Cutscene prompting** — use director commands to force a cut
  *"Cut to the boots of the astronaut walking."*

> ⚠️ Caution: cutting to a drastically different scene can break visual style consistency (e.g. shift from photorealistic to 3D animated). Keep cuts closely related to the establishing shot.

**Start & End Frame Prompting**
Upload an image for the first frame and a second image for the final frame. The AI calculates and renders the animated sequence between them. Best method for locking character appearance and environment across a shot.

**Anchor Prompts**
Explicitly remind the AI of details it may "forget" between shots or actions:

- Physical traits: *"character still has red embers and ash on face"*
- Spatial relationships: *"orc remains on the back of the direwolf"*
- Unseen angles: *"right shoulder has no armor — dark blue geometric tribal tattoos"*

**Reference Control (Level 3)**

- Upload character images to lock appearance across shots and angles
- Supply existing video to mimic choreography or camera movement patterns

#### Prompt Structure Templates

**Standard video prompt:**

```
[Visual style]. [Environment]. [Subject] [action].
Camera: [shot type], [movement].
Audio: [music/SFX/narration/silence].
Duration: [Xs]. Mood: [tone].
Avoid: [known model limitations].
```

**Multi-shot prompt:**

```
[Visual style]. [Environment].
0–Xs: [camera movement] — [subject] [action].
Xs–Xs: Cut to [new angle] — [subject] [action].
Xs–Xs: [camera movement] — [subject] [action].
Audio: [description]. Mood: [tone].
```

#### Level 5 Full Pipeline Steps

1. Use a Custom GPT to generate a 3×3 storyboard
2. Animate individual frames (simple prompts for basic shots, multi-shot for dynamic sequences)
3. Generate dialogue with a voice tool (e.g. ElevenLabs) — specify gender, accent, emotion, tonality
4. Merge visuals + dialogue using an AI lip-sync tool

#### Model Limitations to Document

Before writing video prompts, note what the target model struggles with:

- Exact text overlays rendered in-frame
- Long continuous scenes without cuts
- Large crowds or complex multi-character interactions
- Reliable lip sync
- Maintaining visual consistency across drastic scene changes

---

### --nietzsche mode (analysis frame)

When invoked as `/prompt-engineer --nietzsche <text or idea>`, produce an accessible analysis for everyday working people (not scholars) using this fixed framework:

**Persona:** Engaging Educator — accessible, conversational, no heavy jargon, use simple analogies.

**Three mandatory pillars:**

1. **HERD PRESSURE** — map conflict against conformity, Last Man comfort-seeking, Bad Conscience used as guilt tool.
2. **WILDERNESS** — Ontological Interval from breaking away, Active Nihilism destroying hollow values, Self-Overcoming in isolation.
3. **NEW COVENANT** — Übermensch path, Will to Power for self-perfection, Sublimation into new community, Amor Fati embracing the journey.

**Structure:** Introduction → The Problem → The Transition → The Solution.

**Output:** a single, readable analysis in plain language.

---

## Inputs

Provide at least:

- **Goal:** what you want and why.
- **Audience:** who's it for.
- **Constraints:** length, tone, do/don't, required inclusions.
- **Context:** facts, links, documents, examples to emulate (few-shot).
- **Output format:** bullets/table/JSON/sections, etc.

For video, also provide:

- **Media references:** character images, style references, sample videos to mimic.
- **Target model:** which video generator (Veo, Runway, Kling, etc.) and its known limitations.

Optional:

- **Examples (few-shot):** 1–3 short exemplars of ideal output.
- **Failure tolerance:** what to do when info is missing (ask questions vs say "I don't know").
- **Exploration mode:** none | CoT | ToT | adversarial.

---

## Outputs

- A **power prompt** (ready to paste) with Persona/Task/Context/Format.
- For video: a structured prompt using the core dimensions template, with advanced techniques applied where relevant.
- If requested, **variants** (branches) + evaluation + a synthesised best version.
- A short **prompt checklist** to prevent regressions.

---

## Failure modes

- **Messy thinking → messy prompts:** goal and success criteria are unclear.
  - Fix: rewrite goal + success criteria; simplify the task.
- **Video inconsistency:** character appearance or style shifts between shots.
  - Fix: add anchor prompts; use image references; avoid drastic cutscene jumps.
- **Video model ignores instructions:** prompt is too vague or exceeds model capability.
  - Fix: use structured template; document and avoid model limitations; use a Custom GPT trained on the model's official docs.
- **Vague prompts → generic "garbage" output:** missing persona, missing constraints, or missing context.
  - Fix: enforce Four Pillars; add explicit constraints and context.
- **Hallucinations:** model fills gaps due to missing info or ambiguous requirements.
  - Fix: add "permission to fail"; require citations/grounding to provided context.
- **Wrong tone/format:** output is correct but unusable.
  - Fix: specify format, length, and tone; use few-shot exemplars.
- **Complex tasks solved "averagely":** first answer is statistically bland.
  - Fix: ToT branches + evaluation; adversarial critique/playoff.

---

## Toolset

- exec (shell): run greps, run the skill validators
- read: inspect existing prompt templates/examples
- write: save finalised prompt templates (optional)

---

## Acceptance tests

1. Run `/skill-forge --topic "prompt engineering" --skill-name prompt-engineer --web-research` — expected output: `~/clawd/skills/prompt-engineer/SKILL.md` exists and the validators return PASS/PASS.

2. Run `grep -nE '^## (Trigger|Use|Inputs|Outputs|Failure modes|Toolset|Acceptance tests)$' ~/clawd/skills/prompt-engineer/SKILL.md` — expected output: each required heading appears exactly once.

3. Negative case: delete the `## Toolset` heading and re-run `validate_skillmd.py` — expected error message: validator FAIL mentioning missing required section(s).

4. When given a concrete task + constraints, the skill produces a prompt that contains **Persona**, **Task**, **Context**, and **Format**, and includes a "permission to fail" clause (behavioural expectation).

5. When invoked with `--video`, the skill applies the core dimensions template and advanced techniques appropriate to the level described.

### Optional local checks

```bash
set -euo pipefail
FILE="/Users/igorsilva/clawd/skills/prompt-engineer/SKILL.md"
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py "$FILE"
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py "$FILE"
```
