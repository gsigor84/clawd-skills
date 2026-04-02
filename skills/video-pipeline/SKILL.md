---
name: video-pipeline
description: "# video-pipeline — Run the full marketing video pipeline: strategy → concept → video prompt. Also handles pure creative visions — goes direct to video prompt design. Use when you want to go from a product description or creative vision to a finished video prompt in one command."
---

# video-pipeline

Run the video pipeline in a single command. Automatically detects the input type:

- **Creative/artistic vision** (cyberpunk city, aerial shot, mood piece) → goes direct to video prompt design, no marketing wrapper
- **Product/marketing brief** (landing page hero, SaaS campaign) → runs the full strategy → concept → video prompt pipeline

## Trigger
`/video-pipeline <product description or creative vision>`

## Tool
Script: `~/clawd/skills/video-pipeline/run_video_pipeline.py`

## Use

### Single command mode
```
/video-pipeline 2050 Tokyo cyberpunk cinematic — sky descent into neon city at night
```

```
/video-pipeline a landing page hero video for OpenClaw — B2B SaaS teams done babysitting generic AI agents
```

The script auto-detects which mode to use based on the input.

### Creative vision mode

Triggered when the input contains words like: cinematic, sky, neon, cyberpunk, night, city, dawn, aerial, mood, atmosphere, anime, etc.

The script skips marketing strategy and concept stages, and goes straight to designing the video prompt from the creative vision directly.

**Output:** A structured video prompt including:
- Creative vision summary
- Multi-shot timeline with timestamp prompting
- Camera instructions (shot type, movement, lighting)
- Anchor prompts for visual consistency
- Audio direction
- Mood / tone
- Explicit avoid list

### Marketing brief mode

Triggered when the input contains words like: product, platform, SaaS, landing page, hero, campaign, launch, OpenClaw, agent, etc.

Runs all three stages internally:

**Stage 1 — Strategy** (inferred): ICP, enemy, value thesis, proof points
**Stage 2 — Concept**: Headline, subheadline, proof bar, CTA
**Stage 3 — Video prompt**: Structured prompt from the concept

**Output:** A structured video prompt derived from the marketing concept.

## The handoff rule (marketing mode)

Before proceeding from Stage 1 to Stage 2, the pipeline pauses to confirm three decisions explicitly:

1. **The one feeling** this video needs to create
2. **The single proof point** that earns that feeling
3. **The enemy** we are defeating in the viewer's mind

## Inputs

- **Single input:** a product description or creative vision string
  - For creative visions: include visual/style keywords (cinematic, neon, aerial, mood, etc.)
  - For marketing briefs: include product/platform keywords (landing page, hero, campaign, OpenClaw, agent, etc.)

## Outputs

- **Creative vision mode:** a structured video prompt with creative vision summary, multi-shot timeline, camera instructions, anchor prompts, audio, mood, and avoid list
- **Marketing brief mode:** a structured video prompt derived from the marketing concept, including hook, proof, camera instructions, multi-shot timeline, audio, mood, and avoid list

## Limitations

- Does not generate the actual video — only the prompt
- A video model API (Veo/Runway/Kling) must be used separately
- Creative visions skip the marketing strategy stage — no ICP, enemy, or proof design

## Failure modes

- **Creative vision misclassified as marketing brief:** if a creative vision contains product words like "agent" or "platform", it may trigger marketing mode incorrectly.
  - Fix: reframe the creative vision without product-specific keywords.
- **Marketing brief classified as creative vision:** if a product description has no clear marketing trigger words, it goes to creative mode with generic output.
  - Fix: include product keywords like "platform", "landing page", "campaign" in the input.
- **Vague input → generic output:** if no ICP, enemy, or creative vision is clear, the pipeline uses defaults.
  - Fix: add specificity to the input description.

## Toolset

- exec (shell): run the video pipeline script
- read: inspect previous pipeline outputs

## Acceptance tests

1. Run:
```bash
/opt/anaconda3/bin/python3 ~/clawd/skills/video-pipeline/run_video_pipeline.py "2050 Tokyo cyberpunk cinematic — sky descent into neon city at night"
```
Expected: creative vision detected, skips marketing stages, outputs a cinematic video prompt with neon/Tokyo/cyberpunk aesthetics, no marketing copy

2. Run:
```bash
/opt/anaconda3/bin/python3 ~/clawd/skills/video-pipeline/run_video_pipeline.py "landing page hero for OpenClaw"
```
Expected: marketing brief detected, runs full pipeline, outputs video prompt derived from a marketing concept

3. Negative case — run with no arguments:
```bash
/opt/anaconda3/bin/python3 ~/clawd/skills/video-pipeline/run_video_pipeline.py
```
Expected: script exits 1 with usage error message

4. Invoke via skill: `/video-pipeline a landing page hero for OpenClaw`
Expected: agent reads SKILL.md, runs the pipeline script, returns the final video prompt
