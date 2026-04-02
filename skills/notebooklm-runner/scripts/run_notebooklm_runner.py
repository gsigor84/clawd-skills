#!/opt/anaconda3/bin/python3
"""Run the full NotebookLM flow end-to-end.

- For each prompt file present (pNN.txt):
  - run notebooklm-fetcher (clipboard) for that prompt
  - run notebooklm-processor after each prompt to update progress
- After all prompts:
  - write notebooklm-final-summary.md from the processor progress file

This script is deterministic orchestration only.

Enhancements:
- Uses tools/run_ledger.py for phase tracking.
- Supports --resume to skip already-completed prompts.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Shared learnings logger (ERR entries)
sys.path.insert(0, "/Users/igorsilva/clawd/tools")
from learnings_helper import update_or_append_err  # type: ignore

# Run ledger (authoritative run.json)
from run_ledger import complete_phase, create_run, fail_phase, start_phase  # type: ignore


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


def _ledger_phase_for_prompt(prompt_n: int, prompt_name: str) -> str:
    # Deterministic, stable phase names.
    return f"prompt:{prompt_n:02d}:{prompt_name}"


def _phase_is_done(run_json: Dict[str, object], phase_name: str) -> bool:
    phases = (run_json.get("phases") or {})  # type: ignore[assignment]
    if not isinstance(phases, dict):
        return False
    meta = phases.get(phase_name)  # type: ignore[arg-type]
    if not isinstance(meta, dict):
        return False
    return meta.get("status") == "DONE"


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

    ap.add_argument("--resume", action="store_true", help="Skip prompts already marked DONE in the run ledger")
    ap.add_argument("--run-id", help="Resume/append to an existing run ledger run_id")

    args = ap.parse_args()

    prompts_dir = Path(args.prompts_dir)
    runs_dir = Path(args.runs_dir)
    progress_file = Path(args.progress_file)
    final_summary = Path(args.final_summary)

    # Build plan from actual prompt files present, rather than assuming p01..p17.
    prompt_files = sorted(
        prompts_dir.glob("p[0-9][0-9].txt"),
        key=lambda p: int(re.search(r"p(\d{2})\.txt$", p.name).group(1)),  # type: ignore
    )
    plan: List[Tuple[int, str, Path]] = []
    for p in prompt_files:
        m = re.search(r"p(\d{2})\.txt$", p.name)
        if not m:
            continue
        n = int(m.group(1))
        name = PROMPT_NAME_BY_N.get(n, f"prompt-{n:02d}")
        plan.append((n, name, p))

    if args.dry_run:
        for n, name, p in plan:
            print(f"{n:02d} {name} -> {p}")
        return 0

    if not plan:
        print(f"ERROR: no prompt files found in {prompts_dir} (expected pNN.txt)", file=sys.stderr)
        return 2

    # Ledger run id
    pipeline_name = "notebooklm-runner"
    run_id = args.run_id
    if run_id and not args.resume:
        print("ERROR: --run-id requires --resume (safety: only attach to an existing run when resuming)", file=sys.stderr)
        return 2

    if args.resume:
        if not run_id:
            print("ERROR: --resume requires --run-id", file=sys.stderr)
            return 2
        run_dir = Path("/Users/igorsilva/clawd/tmp/runs") / pipeline_name / run_id
        run_json_path = run_dir / "run.json"
        if not run_json_path.exists():
            print(f"ERROR: run ledger not found for --run-id={run_id} ({run_json_path})", file=sys.stderr)
            return 2
        run_json = json.loads(run_json_path.read_text(encoding="utf-8"))
    else:
        run_id, run_dir = create_run(
            pipeline_name,
            inputs={
                "notebook_url": args.notebook_url,
                "prompts_dir": str(prompts_dir),
                "runs_dir": str(runs_dir),
                "progress_file": str(progress_file),
                "final_summary": str(final_summary),
                "max_checks": args.max_checks,
                "sleep_seconds": args.sleep_seconds,
            },
        )
        run_json = {}

    fetcher = Path("/Users/igorsilva/clawd/skills/notebooklm-fetcher/scripts/fetch_clipboard.py")
    processor = Path("/Users/igorsilva/clawd/skills/notebooklm-processor/scripts/process_runs.py")

    for n, name, p in plan:
        phase_name = _ledger_phase_for_prompt(n, name)

        if args.resume:
            # Re-load run.json each loop (authoritative; supports concurrent/manual edits)
            run_json_path = (Path("/Users/igorsilva/clawd/tmp/runs") / pipeline_name / run_id) / "run.json"
            run_json = json.loads(run_json_path.read_text(encoding="utf-8"))
            if _phase_is_done(run_json, phase_name):
                continue

        if not p.exists():
            err = f"missing prompt file: {p}"
            fail_phase(run_id, phase_name, err, pipeline_name=pipeline_name)
            update_or_append_err(
                pattern_key="notebooklm-runner:missing-prompt-file",
                summary="NotebookLM runner missing prompt file; cannot continue.",
                error_lines=[err, f"prompt_number={n}", f"prompt_name={name}"],
                context_lines=[
                    f"notebook_url={args.notebook_url}",
                    f"prompts_dir={prompts_dir}",
                    f"runs_dir={runs_dir}",
                    f"progress_file={progress_file}",
                    f"final_summary={final_summary}",
                    f"run_id={run_id}",
                ],
                suggested_fix_lines=[
                    "Ensure prompts-dir contains p01.txt..p17.txt.",
                    "Re-run notebooklm-runner after regenerating missing prompt file.",
                ],
                priority="high",
                area="infra",
                stage="notebooklm-runner",
            )
            print(f"ERROR: {err}", file=sys.stderr)
            return 2

        start_phase(run_id, phase_name, pipeline_name=pipeline_name)

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
        if code == 1:
            # Fetcher signals partial/blocked completion.
            # Special-case the known NotebookLM failure where the page is ready but
            # the copy button selector drifts. In practice, clearing chat history and
            # resuming from the current prompt recovers the run.
            latest_meta = sorted(runs_dir.glob(f"*_prompt-{n:02d}_{name}.meta.json"))
            partial_error = None
            if latest_meta:
                try:
                    meta = json.loads(latest_meta[-1].read_text(encoding="utf-8"))
                    partial_error = (((meta.get("result") or {}).get("error")) if isinstance(meta, dict) else None)
                except Exception:
                    partial_error = None

            err = f"fetcher returned partial/blocked prompt={n} exit={code}"
            fail_phase(run_id, phase_name, err, pipeline_name=pipeline_name)
            update_or_append_err(
                pattern_key="notebooklm-runner:fetcher-partial-or-blocked",
                summary="NotebookLM runner stopped because fetcher returned partial/blocked.",
                error_lines=[f"fetcher exit={code}", f"prompt_number={n}", f"prompt_name={name}", f"partial_error={partial_error}"],
                context_lines=[
                    f"notebook_url={args.notebook_url}",
                    f"prompts_dir={prompts_dir}",
                    f"runs_dir={runs_dir}",
                    f"progress_file={progress_file}",
                    f"final_summary={final_summary}",
                    f"run_id={run_id}",
                ],
                suggested_fix_lines=[
                    "Check Tandem is reachable at 127.0.0.1:8765.",
                    "If partial_error=copy_button_not_found: clear NotebookLM chat history, then re-run the runner with --resume --run-id <run_id>.",
                    "If NotebookLM UI drifted, update selectors in notebooklm-fetcher.",
                ],
                priority="medium",
                area="infra",
                stage="notebooklm-runner",
            )
            if partial_error == "copy_button_not_found":
                print(
                    f"RECOVERABLE: prompt {n:02d} failed with copy_button_not_found. Clear NotebookLM chat history, then resume with: --resume --run-id {run_id}",
                    file=sys.stderr,
                )
            else:
                print(f"ERROR: {err}", file=sys.stderr)
            return 3

        if code != 0:
            err = f"fetcher failed prompt={n} exit={code}"
            fail_phase(run_id, phase_name, err, pipeline_name=pipeline_name)
            update_or_append_err(
                pattern_key="notebooklm-runner:fetcher-hard-failure",
                summary="NotebookLM runner stopped because fetcher hard-failed.",
                error_lines=[f"fetcher exit={code}", f"prompt_number={n}", f"prompt_name={name}"],
                context_lines=[
                    f"notebook_url={args.notebook_url}",
                    f"prompts_dir={prompts_dir}",
                    f"runs_dir={runs_dir}",
                    f"progress_file={progress_file}",
                    f"final_summary={final_summary}",
                    f"run_id={run_id}",
                ],
                suggested_fix_lines=[
                    "Run notebooklm-fetcher directly for the failing prompt to reproduce.",
                    "Inspect tmp/notebooklm-runs meta.json/snapshot.json for the failing run.",
                ],
                priority="high",
                area="infra",
                stage="notebooklm-runner",
            )
            print(f"ERROR: {err}", file=sys.stderr)
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
            err = f"processor failed prompt={n} exit={code2}"
            fail_phase(run_id, phase_name, err, pipeline_name=pipeline_name)
            update_or_append_err(
                pattern_key="notebooklm-runner:processor-failed",
                summary="NotebookLM runner stopped because processor failed.",
                error_lines=[f"processor exit={code2}", f"prompt_number={n}", f"prompt_name={name}"],
                context_lines=[
                    f"runs_dir={runs_dir}",
                    f"progress_file={progress_file}",
                    f"run_id={run_id}",
                ],
                suggested_fix_lines=[
                    "Run notebooklm-processor directly on the runs dir to reproduce.",
                    "Check for malformed snapshot/meta files in tmp/notebooklm-runs.",
                ],
                priority="high",
                area="infra",
                stage="notebooklm-runner",
            )
            print(f"ERROR: {err}", file=sys.stderr)
            return 4

        complete_phase(
            run_id,
            phase_name,
            artifacts=[str(progress_file)],
            pipeline_name=pipeline_name,
        )

    if not progress_file.exists():
        err = "progress file missing after run"
        # Use a synthetic final phase name so it shows in the ledger.
        phase_name = "final:progress"
        fail_phase(run_id, phase_name, err, pipeline_name=pipeline_name)
        update_or_append_err(
            pattern_key="notebooklm-runner:progress-file-missing",
            summary="NotebookLM runner finished prompts but progress file was missing.",
            error_lines=[err],
            context_lines=[f"progress_file={progress_file}", f"runs_dir={runs_dir}", f"run_id={run_id}"],
            suggested_fix_lines=[
                "Re-run notebooklm-processor on the runs dir to regenerate progress.",
                "Check filesystem permissions for the progress file path.",
            ],
            priority="high",
            area="infra",
            stage="notebooklm-runner",
        )
        print(f"ERROR: {err}", file=sys.stderr)
        return 5

    summary = build_final_summary(progress_file.read_text(encoding="utf-8", errors="replace"))
    final_summary.parent.mkdir(parents=True, exist_ok=True)
    final_summary.write_text(summary, encoding="utf-8")

    # Mark overall completion
    complete_phase(
        run_id,
        "final:summary",
        artifacts=[str(progress_file), str(final_summary)],
        pipeline_name=pipeline_name,
    )

    # Print run_id to make resume easy.
    print(run_id)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
