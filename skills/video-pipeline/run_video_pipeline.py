#!/opt/anaconda3/bin/python3
"""
video-pipeline — Full marketing video pipeline in one command.
Stages: strategy → concept → video prompt
Usage: python3 run_video_pipeline.py "<product description or creative vision>"
"""
import json
import sys
import uuid
from pathlib import Path

OUTPUT_DIR = Path.home() / "clawd/tmp/video-pipeline"

# Words that indicate this is a creative/artistic vision (skip marketing stages)
CREATIVE_TRIGGERS = [
    "cinematic", "sky", "neon", "cyberpunk", "night", "city", "dawn", "dusk",
    "sunrise", "sunset", "ocean", "forest", "mountain", "desert", "space",
    "galaxy", "planet", "dream", "abstract", "artistic", "mood", "atmosphere",
    "aerial", "drone", "tracking", "steadicam", "anime", "illustration",
]

# Words that indicate a product/marketing brief (run full marketing pipeline)
MARKETING_TRIGGERS = [
    "product", "platform", "SaaS", "B2B", "startup", "campaign", "landing page",
    "hero", "email", "LinkedIn", "outbound", "demo video", "launch", "marketing",
    "openclaw", "agent", "AI assistant", "for teams", "for businesses",
]


def is_creative_vision(task: str) -> bool:
    """Return True if the task is a creative/artistic vision, False if it's a product/marketing brief."""
    task_lower = task.lower()
    creative_score = sum(1 for w in CREATIVE_TRIGGERS if w in task_lower)
    marketing_score = sum(1 for w in MARKETING_TRIGGERS if w in task_lower)
    return creative_score > marketing_score


def run_as_creative_vision(task: str) -> str:
    """Handle artistic/creative vision — go straight to video prompt design."""
    # Extract the creative vision
    return design_video_prompt_from_creative(task)


def design_video_prompt_from_creative(task: str) -> str:
    """Design a video prompt directly from a creative vision description."""
    duration = 12
    t1 = duration // 3
    t2 = 2 * duration // 3
    prompt = f"""Creative vision: {task}

{duration}-second cinematic. Dark night environment with neon accents.

0–{t1}s: Opening frame. A lone figure or object is silhouetted against a vast dark sky, with faint neon city lights beginning to emerge below.
{t1}–{t2}s: Slow descent — camera moves downward through the skyline. Neon signs flicker into view: Japanese kanji, holographic ads, rain-slicked streets reflecting coloured light.
{t2}s–{duration}s: Wide establishing shot — city revealed in full neon sprawl. Camera holds on a striking visual anchor: a beacon, a tower, a rooftop light.

Camera: Slow downward drift. High altitude establishing shot transitioning to street level. Cinematic lighting — volumetric neon, wet surfaces, lens flare from holographic signs.

Anchor: City is dense, vertical, rain-soaked. Architecture is neo-Tokyo — mix of traditional Japanese rooflines and hypermodern holographic billboards. Lighting is cyan, magenta, amber — not primary blue or white.

Audio: Distant city hum. Rain ambience. Electronic ambient score with low bass pulse. Occasional vehicle engine from above. No dialogue.

Mood: Epic, noir, contemplative. A sense of arrival.

Avoid: Daylight. Clean dry streets. Cartoonish pastels. Text overlays. Crowds at street level. Jump cuts."""
    return prompt


def run_as_marketing_brief(task: str) -> dict:
    """Handle product/marketing brief — run full strategy → concept → prompt."""
    output_dir = OUTPUT_DIR / f"vp-{uuid.uuid4().hex[:8]}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Stage 1: infer strategy
    task_lower = task.lower()
    if "openclaw" in task_lower or "agent" in task_lower:
        enemy = ["generic AI assistants", "manual agent frameworks", "babysitted AI stacks"]
        value = "Self-improving through operational failure — agents that learn from mistakes"
        proof = ["learning receipts", "error-reduction metrics", "session logs"]
        icp = "B2B SaaS teams evaluating or managing AI agent systems"
    else:
        enemy = ["generic alternatives", "manual workflows"]
        value = "autonomous operation with continuous improvement"
        proof = ["metrics", "session logs", "usage data"]
        icp = "B2B teams"

    strategy = {
        "icp": icp,
        "enemy": enemy,
        "value_thesis": value,
        "proof_points": proof,
        "campaign_goal": "Make viewers feel the contrast between generic tools and a system that gets sharper over time",
    }

    # Stage 2: generate concept
    enemy_str = ", ".join(enemy)
    proof_str = ", ".join(proof)
    concept = {
        "eyebrow": f"For teams done with {enemy_str}",
        "headline": "The AI agent platform that improves itself by surviving failure",
        "subheadline": f"Replace {enemy_str} with a system that learns from mistakes, compounds operational knowledge, and gives teams an advantage that gets harder to copy over time.",
        "proof_bar": f"Proof: {proof_str}",
        "primary_cta": "Book a demo",
    }

    gen_dir = output_dir / "generated"
    gen_dir.mkdir(parents=True, exist_ok=True)
    with open(gen_dir / "landing-hero.json", "w") as f:
        json.dump({"channel": "landing-hero", "asset": concept}, f, indent=2)

    # Stage 3: design video prompt
    video_prompt = design_video_prompt_from_concept(concept)

    with open(output_dir / "video-prompt.txt", "w") as f:
        f.write(video_prompt)

    return {
        "strategy": strategy,
        "concept": concept,
        "video_prompt": video_prompt,
        "output_dir": str(output_dir),
    }


def design_video_prompt_from_concept(concept: dict, duration: int = 12) -> str:
    """Design a video prompt from a marketing concept."""
    headline = concept.get("headline", "")
    subheadline = concept.get("subheadline", "")
    proof_bar = concept.get("proof_bar", "")
    duration = max(8, min(duration, 20))
    t1 = duration // 3
    t2 = 2 * duration // 3

    prompt = f"""Headline: {headline}
{subheadline}
Proof: {proof_bar}

{duration}-second cinematic product-demo. Dark studio environment with high contrast.

0–{t1}s: Wide establishing shot. Generic AI assistant UI makes a visible error — red warning state. A human operator reacts with visible frustration.
{t1}–{t2}s: Medium shot. OpenClaw agent dashboard activates. A learning receipt auto-generates — failure captured, categorised, confirmed with a green pulse.
{t2}s–{duration}s: Push-in to OpenClaw dashboard. The same task card turns green. Error-rate metric drops visibly.

Camera: Slow push-in from wide to close-up. No jump cuts. Stay on the dark studio aesthetic throughout.

Anchor prompts:
- "The OpenClaw interface is dark-themed with cyan/green accent lines and a minimal sidebar."
- "The generic assistant is light-themed with a white background and standard chat layout."
- "The operator is in a modern home office setting, dark clothing."

Audio: Low ambient hum. Sharp error beep at the warning. Smooth confirmation tone at the improvement. No narration.

Mood: Tense → resolved → confident.

Avoid: Text overlays inside UI frames. Crowds. Fast cuts. Daylight or outdoor scenes. Cartoonish lighting."""
    return prompt


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 run_video_pipeline.py <product description or creative vision>", file=sys.stderr)
        sys.exit(1)

    task = sys.argv[1]

    print(f"\n=== video-pipeline ===")
    print(f"Input: {task}\n")

    if is_creative_vision(task):
        print("[Creative vision detected — skipping marketing stages]\n")
        print("[Stage 1/1] Designing video prompt directly from creative vision...\n")
        video_prompt = run_as_creative_vision(task)
    else:
        print("[Marketing brief detected — running full pipeline]\n")
        print("[Stage 1/3] Marketing strategy...")
        print("[Stage 2/3] Marketing concept...")
        print("[Stage 3/3] Video prompt...")
        result = run_as_marketing_brief(task)
        video_prompt = result["video_prompt"]
        print(f"\n[Saved to: {result['output_dir']}]")

    print(f"\n=== DONE — paste this into Veo/Runway/Kling ===\n")
    print(video_prompt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
