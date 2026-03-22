#!/opt/anaconda3/bin/python3
"""Run the full NotebookLM flow end-to-end.

- For prompt 1..14:
  - run notebooklm-fetcher (clipboard) for that prompt
  - run notebooklm-processor after each prompt to update progress
- After all prompts:
  - write notebooklm-final-summary.md from the processor progress file

This script is deterministic orchestration only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


PROMPT_NAME_BY_N: Dict[int, str] = {
    1: "core-questions",
    2: "beginner-friendly-lesson-builder",
    3: "concept-connection-mapper",
    4: "active-learning-session-planner",
    5: "surprising-insights",
    6: "what-s-missing",
    7: "contradictions",
    8: "project-multi-sources",
    9: "decision-graph-vs-loops",
    10: "action-plan",
    11: "troubleshoot-skillmd",
    12: "gap-analysis",
    13: "rubric",
    14: "final-spec",
    15: "decision-graph-vs-autonomous-loops",
    16: "operating-rubric-systemic-improvement",
    17: "final-spec-living-system",
}


def run(cmd: List[str]) -> int:
    p = subprocess.run(cmd)
    return int(p.returncode)


def build_final_summary(progress_text: str) -> str:
    # Extract per-prompt blocks from notebooklm-progress.md produced by processor.
    parts = re.split(r"^### Prompt (\d{2})\s*$", progress_text, flags=re.M)
    entries: List[Tuple[int, str, str, int, str, List[str]]] = []

    for i in range(1, len(parts), 2):
        num = int(parts[i])
        body = parts[i + 1]
        status_m = re.search(r"^- Status: `([^`]*)`", body, flags=re.M)
        status = (status_m.group(1) if status_m else "").strip()
        mode_m = re.search(r"^- Extraction mode: `([^`]*)`", body, flags=re.M)
        mode = (mode_m.group(1) if mode_m else "").strip()
        run_m = re.search(r"^- Run: `([^`]*)`", body, flags=re.M)
        run_id = (run_m.group(1) if run_m else "").strip()

        raw_match = re.search(r"\*\*Raw extracted\*\*\n```\n(.*?)\n```", body, flags=re.S)
        raw = (raw_match.group(1).strip() if raw_match else "")
        raw_lines = [l.strip() for l in raw.splitlines() if l.strip()]

        entries.append((num, status, mode, len(raw_lines), run_id, raw_lines[:12]))

    lines: List[str] = []
    lines.append("# NotebookLM — Final Summary (14 prompts)")
    lines.append("")
    lines.append("## Status")
    lines.append("")
    lines.append("| Prompt | Status | Extraction | Lines | Run |")
    lines.append("|---:|---|---|---:|---|")
    for n, status, mode, nlines, run_id, _ in sorted(entries, key=lambda x: x[0]):
        lines.append(f"| {n} | {status} | {mode} | {nlines} | `{run_id}` |")

    lines.append("")
    lines.append("## Per-prompt previews (first lines)")
    lines.append("")
    for n, status, mode, nlines, run_id, preview in sorted(entries, key=lambda x: x[0]):
        lines.append(f"### Prompt {n:02d}")
        for l in preview:
            lines.append(f"- {l}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--notebook-url", required=True)
    ap.add_argument("--prompts-dir", required=True)
    ap.add_argument("--runs-dir", required=True)
    ap.add_argument("--progress-file", required=True)
    ap.add_argument("--final-summary", required=True)
    ap.add_argument("--max-checks", type=int, default=720)
    ap.add_argument("--sleep-seconds", type=float, default=2.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    prompts_dir = Path(args.prompts_dir)
    runs_dir = Path(args.runs_dir)
    progress_file = Path(args.progress_file)
    final_summary = Path(args.final_summary)

    plan = [(n, PROMPT_NAME_BY_N[n], prompts_dir / f"p{n:02d}.txt") for n in range(1, 18)]

    if args.dry_run:
        for n, name, p in plan:
            print(f"{n:02d} {name} -> {p}")
        return 0

    fetcher = Path("/Users/igorsilva/clawd/skills/notebooklm-fetcher/scripts/fetch_clipboard.py")
    processor = Path("/Users/igorsilva/clawd/skills/notebooklm-processor/scripts/process_runs.py")

    for n, name, p in plan:
        if not p.exists():
            print(f"ERROR: missing prompt file: {p}", file=sys.stderr)
            return 2

        code = run(
            [
                "/opt/anaconda3/bin/python3",
                str(fetcher),
                "--prompt-number",
                str(n),
                "--prompt-name",
                name,
                "--prompt-text",
                p.read_text(encoding="utf-8"),
                "--notebook-url",
                args.notebook_url,
                "--outdir",
                str(runs_dir),
                "--max-checks",
                str(args.max_checks),
                "--sleep-seconds",
                str(args.sleep_seconds),
            ]
        )
        if code not in (0, 1):
            print(f"ERROR: fetcher failed prompt={n} exit={code}", file=sys.stderr)
            return 3

        code2 = run(
            [
                "/opt/anaconda3/bin/python3",
                str(processor),
                "--runs-dir",
                str(runs_dir),
                "--progress-file",
                str(progress_file),
            ]
        )
        if code2 != 0:
            print(f"ERROR: processor failed prompt={n} exit={code2}", file=sys.stderr)
            return 4

    if not progress_file.exists():
        print("ERROR: progress file missing after run", file=sys.stderr)
        return 5

    summary = build_final_summary(progress_file.read_text(encoding="utf-8", errors="replace"))
    final_summary.parent.mkdir(parents=True, exist_ok=True)
    final_summary.write_text(summary, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
