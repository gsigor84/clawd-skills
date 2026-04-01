#!/opt/anaconda3/bin/python3
"""creativity_toolkit.py

A deterministic runner for the `creativity-toolkit` skill.

This runner exists to make the skill *real*:
- durable run_id + phase tracking via tools/ledger_event.py
- artefact-per-phase written under ~/clawd/tmp/creativity-toolkit/<run_id>/
- schema checks after each phase
- stagnation + Nietzsche gate budgets
- final prompt refinement via /prompt-engineer

Usage:
  /opt/anaconda3/bin/python3 ~/clawd/skills/creativity-toolkit/creativity_toolkit.py \
    --task "write a video prompt for a futuristic Tokyo skyline at dawn"

Output:
  Prints the absolute path to phase-8-final.md

Constraints:
- LLM work is delegated to `openclaw agent` (Gateway) with a single message per phase.
- This runner does NOT deliver replies to chat; it only writes artefacts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


CWD = Path("/Users/igorsilva/clawd")
LEDGER_EVENT = CWD / "tools" / "ledger_event.py"
TMP_ROOT = CWD / "tmp" / "creativity-toolkit"


class RunnerError(Exception):
    pass


def sh(cmd: List[str], timeout: int = 60, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(CWD),
        text=True,
        capture_output=capture,
        timeout=timeout,
    )


def create_run(task: str) -> str:
    p = sh(
        [
            "/opt/anaconda3/bin/python3",
            str(LEDGER_EVENT),
            "create",
            "creativity-toolkit",
            json.dumps({"task": task}, ensure_ascii=False),
        ],
        timeout=30,
    )
    if p.returncode != 0:
        raise RunnerError(f"ledger create failed: {p.stderr.strip()}")
    run_id = (p.stdout or "").strip().splitlines()[-1].strip()
    if not run_id:
        raise RunnerError("ledger create produced empty run_id")
    return run_id


def ledger_run(run_id: str, phase: str, argv: List[str], timeout: int) -> None:
    p = sh(
        [
            "/opt/anaconda3/bin/python3",
            str(LEDGER_EVENT),
            "run",
            run_id,
            phase,
            "creativity-toolkit",
            "--",
            *argv,
        ],
        timeout=timeout,
    )
    if p.returncode != 0:
        raise RunnerError(
            f"phase failed: {phase} exit={p.returncode}\nstdout={p.stdout.strip()}\nstderr={p.stderr.strip()}"
        )


def openclaw_agent(message: str, to: str, timeout: int = 600) -> str:
    # Use --json so we can parse reliably.
    p = sh(
        [
            "openclaw",
            "agent",
            "--to",
            to,
            "--json",
            "--timeout",
            str(timeout),
            "--message",
            message,
        ],
        timeout=timeout + 30,
    )
    if p.returncode != 0:
        raise RunnerError(f"openclaw agent failed exit={p.returncode}: {p.stderr.strip()}")

    try:
        obj = json.loads(p.stdout)
    except Exception as e:
        raise RunnerError(f"openclaw agent returned non-JSON: {e}\n{p.stdout[:500]}")

    # Gateway JSON shapes observed:
    # 1) { ok:true, result:{ output:[{content:[{type:'output_text', text:'...'}]}] } }
    # 2) { status:'ok', summary:'completed', result:{ payloads:[{text:'...'}], meta:{...} } }

    result = obj.get("result")
    if isinstance(result, dict):
        # Shape (2)
        payloads = result.get("payloads")
        if isinstance(payloads, list) and payloads:
            texts: List[str] = []
            for p in payloads:
                if isinstance(p, dict):
                    t = p.get("text")
                    if isinstance(t, str) and t.strip():
                        texts.append(t.strip())
            if texts:
                return "\n".join(texts).strip()

        # Shape (1)
        out = result.get("output")
        if isinstance(out, list):
            texts2: List[str] = []
            for item in out:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if not isinstance(content, list):
                    continue
                for c in content:
                    if isinstance(c, dict):
                        if c.get("type") == "output_text":
                            t = c.get("text")
                            if isinstance(t, str) and t.strip():
                                texts2.append(t.strip())
                        t2 = c.get("text")
                        if isinstance(t2, str) and t2.strip():
                            texts2.append(t2.strip())
            if texts2:
                return "\n".join(texts2).strip()

    # Never treat top-level summary='completed' as the model output.

    # Back-compat fallbacks
    text = obj.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    for k in ("message", "reply", "output"):
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()

    raise RunnerError(f"could not extract text from openclaw agent JSON output (keys={list(obj.keys())})")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def require_headings(path: Path, headings: List[str]) -> None:
    t = path.read_text(encoding="utf-8", errors="replace")
    for h in headings:
        if re.search(rf"^##\s+{re.escape(h)}\s*$", t, re.M) is None:
            raise RunnerError(f"schema fail: {path.name} missing heading: ## {h}")


def count_bullets_under(path: Path, heading: str) -> int:
    t = path.read_text(encoding="utf-8", errors="replace")
    # crude: find heading block until next ##
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$", t, re.M)
    if not m:
        return 0
    start = m.end()
    rest = t[start:]
    m2 = re.search(r"^##\s+", rest, re.M)
    block = rest[: m2.start()] if m2 else rest
    return len(re.findall(r"^\s*[-*]\s+", block, re.M))


def ensure_single_paragraph(path: Path) -> None:
    # Legacy helper (no longer used for Phase 8 after structured output change)
    t = path.read_text(encoding="utf-8", errors="replace").strip()
    if not t:
        raise RunnerError("final prompt empty")
    paras = [p.strip() for p in re.split(r"\n\s*\n", t) if p.strip()]
    if len(paras) != 1:
        raise RunnerError(f"schema fail: expected exactly one paragraph; got {len(paras)}")


def detect_stagnation(variations_text: str) -> bool:
    # Minimal heuristic: if fewer than 3 distinct variation bullets/blocks, or too repetitive.
    # We keep it crude; the point is to cap retries.
    v = variations_text.lower()
    # repetition signal: many identical lines
    lines = [ln.strip() for ln in v.splitlines() if ln.strip()]
    if not lines:
        return True
    uniq = len(set(lines))
    if uniq / max(1, len(lines)) < 0.4:
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--to", default="+447533464436")
    ap.add_argument("--max-stagnation", type=int, default=2)
    ap.add_argument("--max-gate-rewrites", type=int, default=2)
    args = ap.parse_args()

    task = args.task.strip()
    if not task:
        print("ERROR: no_task_provided", file=sys.stderr)
        return 2

    run_id = create_run(task)
    root = TMP_ROOT / run_id
    root.mkdir(parents=True, exist_ok=True)

    # Phase 1: Research
    p1 = root / "phase-1-research.md"

    def phase1_cmd() -> List[str]:
        prompt = (
            "You are the RESEARCHER. Produce a markdown artefact for Phase 1.\n"
            f"Task: {task}\n\n"
            "Write ONLY markdown with exactly these headings:\n"
            "## Sparks\n\n"
            "Under Sparks, include at least 5 bullet points, each a distinct creative spark/analogy/reference."
        )
        text = openclaw_agent(prompt, to=args.to, timeout=600)
        write_text(p1, text)
        return ["/usr/bin/true"]

    # We ledger-run a no-op command; ledger events are still recorded.
    ledger_run(run_id, "phase-1", ["/usr/bin/true"], timeout=30)
    phase1_cmd()
    require_headings(p1, ["Sparks"])
    if count_bullets_under(p1, "Sparks") < 5:
        raise RunnerError("schema fail: phase-1 Sparks must have >=5 bullets")

    # Phase 2: Selection
    p2 = root / "phase-2-selection.md"
    ledger_run(run_id, "phase-2", ["/usr/bin/true"], timeout=30)
    text2 = openclaw_agent(
        "You are the SELECTOR. Using the Phase 1 artefact below, select one direction and reject others.\n\n"
        f"Phase 1:\n{p1.read_text(encoding='utf-8', errors='replace')}\n\n"
        "Write ONLY markdown with headings:\n"
        "## Selected\n## Rejected\n"
        "Under Selected: pick 1 direction with a 2-4 sentence rationale.\n"
        "Under Rejected: list at least 3 bullets of rejected directions with one-line reasons.",
        to=args.to,
        timeout=600,
    )
    write_text(p2, text2)
    require_headings(p2, ["Selected", "Rejected"])

    # Phase 5: SCAMPER synthesis
    p5 = root / "phase-5-scamper.md"
    ledger_run(run_id, "phase-5", ["/usr/bin/true"], timeout=30)
    text5 = openclaw_agent(
        "Apply SCAMPER to the Selected direction and synthesize into a single candidate prompt spine.\n\n"
        f"Task: {task}\n\n{p2.read_text(encoding='utf-8', errors='replace')}\n\n"
        "Write ONLY markdown with heading:\n"
        "## Synthesized_prompt\n"
        "Under it, write a single paragraph describing the prompt spine.",
        to=args.to,
        timeout=600,
    )
    write_text(p5, text5)
    require_headings(p5, ["Synthesized_prompt"])

    # Phase 6: Generate variations (with stagnation retries)
    p6 = root / "phase-6-generated.md"
    stagnation_tries = 0
    while True:
        ledger_run(run_id, "phase-6", ["/usr/bin/true"], timeout=30)
        text6 = openclaw_agent(
            "You are the GENERATOR. Produce variations from the synthesized prompt.\n\n"
            f"Task: {task}\n\n{p5.read_text(encoding='utf-8', errors='replace')}\n\n"
            "Write ONLY markdown with heading:\n"
            "## Variations\n"
            "Provide at least 3 variations (use bullets or numbered items). Make them meaningfully distinct.",
            to=args.to,
            timeout=600,
        )
        write_text(p6, text6)
        require_headings(p6, ["Variations"])

        if detect_stagnation(p6.read_text(encoding="utf-8", errors="replace")):
            stagnation_tries += 1
            if stagnation_tries > int(args.max_stagnation):
                raise RunnerError("stagnation budget exceeded")
            # Oblique strategy: rewrite phase-5 with a constraint injection
            text_oblique = openclaw_agent(
                "OBLIQUE STRATEGY: inject a constraint to break stagnation.\n"
                f"Task: {task}\n\n"
                f"Current synthesized prompt:\n{p5.read_text(encoding='utf-8', errors='replace')}\n\n"
                "Rewrite Phase 5 artefact with the same schema (## Synthesized_prompt) but add a bold, specific constraint.",
                to=args.to,
                timeout=600,
            )
            write_text(p5, text_oblique)
            continue

        # ensure >=3 variations
        body = p6.read_text(encoding="utf-8", errors="replace")
        if len(re.findall(r"^\s*[-*]\s+", body, re.M)) + len(re.findall(r"^\s*\d+\.\s+", body, re.M)) < 3:
            stagnation_tries += 1
            if stagnation_tries > int(args.max_stagnation):
                raise RunnerError("variation count budget exceeded")
            continue

        break

    # Phase 7: Critic
    p7 = root / "phase-7-critic.md"
    ledger_run(run_id, "phase-7", ["/usr/bin/true"], timeout=30)
    text7 = openclaw_agent(
        "You are the CRITIC. Provide praise, critique, and a revision.\n\n"
        f"Task: {task}\n\n{p6.read_text(encoding='utf-8', errors='replace')}\n\n"
        "Write ONLY markdown with headings:\n"
        "## Praise\n## Critique\n## Revision\n"
        "Under Revision: provide the best single revised direction (not just notes).",
        to=args.to,
        timeout=600,
    )
    write_text(p7, text7)
    require_headings(p7, ["Praise", "Critique", "Revision"])

    # Phase 6.5: Nietzsche Gate
    p65 = root / "phase-65-gate.md"
    warnings_path = root / "WARNINGS.md"
    gate_rewrites = 0
    gate_pass = False
    gate_reason = ""

    philosophy = (CWD / "PHILOSOPHY.md").read_text(encoding="utf-8", errors="replace")

    while True:
        ledger_run(run_id, "phase-65", ["/usr/bin/true"], timeout=30)
        gate_text = openclaw_agent(
            "Apply the Nietzsche Gate to the CRITIC revision.\n\n"
            "Return ONLY markdown with heading ## Gate_result and one of:\n"
            "PASS\n"
            "FAIL_with_reason: <one line>\n\n"
            "Use these tests: Last Man (comfort), Style (single thesis/taste), Übermensch (raised standard), Recurrence (endorse repeating).\n\n"
            f"PHILOSOPHY.md:\n{philosophy}\n\n"
            f"Phase 7:\n{p7.read_text(encoding='utf-8', errors='replace')}\n",
            to=args.to,
            timeout=600,
        )
        write_text(p65, gate_text)
        require_headings(p65, ["Gate_result"])

        txt = p65.read_text(encoding="utf-8", errors="replace")
        mpass = re.search(r"^##\s+Gate_result\s*$\s*^PASS\s*$", txt, re.M)
        if mpass:
            gate_pass = True
            break

        mfail = re.search(r"^FAIL_with_reason:\s*(.+)$", txt, re.M)
        gate_reason = mfail.group(1).strip() if mfail else "gate_failed"

        gate_rewrites += 1
        if gate_rewrites > int(args.max_gate_rewrites):
            # Done with warnings; stamp final.
            write_text(warnings_path, f"UNPROVEN/LOW_VOLTAGE\nreason: {gate_reason}\n")
            break

        # Ask generator to increase voltage; rewrite Phase 7 revision in-place.
        rewrite7 = openclaw_agent(
            "Nietzsche Gate failed. Rewrite the Phase 7 artefact with higher tension/voltage and a clearer thesis.\n\n"
            f"Task: {task}\n\n"
            f"Current Phase 7:\n{p7.read_text(encoding='utf-8', errors='replace')}\n\n"
            "Return ONLY markdown with headings ## Praise, ## Critique, ## Revision.\n"
            "Revision must be more specific, higher standard, less comfort.",
            to=args.to,
            timeout=600,
        )
        write_text(p7, rewrite7)

    # Phase 8: Final prompt via prompt-engineer
    p8 = root / "phase-8-final.md"
    ledger_run(run_id, "phase-8", ["/usr/bin/true"], timeout=30)

    # Final output: structured, actionable (no walls of text)
    base = p7.read_text(encoding="utf-8", errors="replace")
    prompt8 = (
        "Synthesize a structured marketing campaign concept from the critic revision.\n"
        "Return ONLY markdown with this exact structure and constraints:\n\n"
        "## Concept\n"
        "One paragraph (2-5 sentences).\n\n"
        "## Tagline\n"
        "One line.\n\n"
        "## Campaign direction\n"
        "3-5 bullet points describing what the campaign looks/feels like.\n\n"
        "## Visual/tone\n"
        "One sentence describing the aesthetic.\n\n"
        "No extra headings. No preamble. No fences.\n\n"
        f"Task: {task}\n\n"
        f"Input (critic revision):\n{base}\n"
    )
    out8 = openclaw_agent(prompt8, to=args.to, timeout=600)

    # Stamp if low voltage
    if not gate_pass and warnings_path.exists():
        out8 = "UNPROVEN/LOW_VOLTAGE\n\n" + out8.strip()

    write_text(p8, out8)

    # Minimal schema enforcement for phase 8
    require_headings(p8, ["Concept", "Tagline", "Campaign direction", "Visual/tone"])

    print(str(p8))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
