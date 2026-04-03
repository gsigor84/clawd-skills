#!/opt/anaconda3/bin/python3
"""check_resume_contract.py

Guardrail test: verifies a pipeline satisfies the resume contract.

Usage:
  /opt/anaconda3/bin/python3 ~/clawd/tools/check_resume_contract.py <pipeline_name>

Checks:
1. At least one run exists in ~/clawd/tmp/runs/<pipeline>/
2. The latest run has a valid run.json with phases recorded
3. At least one phase is marked DONE
4. At least one phase is marked FAILED or IN_PROGRESS (proves it didn't just succeed cleanly)
5. A --resume flag exists in the pipeline script
6. Failures record phase, error, and timestamp

Notes:
- "pipeline script" discovery is heuristic: we search ~/clawd/skills/<pipeline>/** for a .py containing "--resume".
- Ledger source of truth: ~/clawd/tmp/runs/<pipeline>/<run_id>/run.json
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


RUNS_ROOT = Path("/Users/igorsilva/clawd/tmp/runs")
SKILLS_ROOT = Path("/Users/igorsilva/clawd/skills")


@dataclass
class CheckResult:
    ok: bool
    msg: str


def fail(msg: str) -> CheckResult:
    return CheckResult(False, msg)


def ok(msg: str) -> CheckResult:
    return CheckResult(True, msg)


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"invalid json: {path} ({e})")


def _latest_run_dir(pipeline: str) -> Tuple[Path, str]:
    root = RUNS_ROOT / pipeline
    if not root.exists() or not root.is_dir():
        raise RuntimeError(f"no runs dir: {root}")

    run_dirs = [p for p in root.iterdir() if p.is_dir()]
    if not run_dirs:
        raise RuntimeError(f"no run dirs found in: {root}")

    # run_id is directory name; sort lexicographically descending (run_ledger uses sortable timestamps)
    run_dirs.sort(key=lambda p: p.name, reverse=True)
    return run_dirs[0], run_dirs[0].name


def _get_phases(run: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    phases = run.get("phases")
    if not isinstance(phases, dict) or not phases:
        raise RuntimeError("run.json has no phases recorded")
    # ensure dict values are dict-ish
    out: Dict[str, Dict[str, Any]] = {}
    for k, v in phases.items():
        if isinstance(v, dict):
            out[str(k)] = v
        else:
            out[str(k)] = {"_raw": v}
    return out


def _phase_status_counts(phases: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for meta in phases.values():
        s = str(meta.get("status") or "")
        counts[s] = counts.get(s, 0) + 1
    return counts


def _assert_failure_fields(phases: Dict[str, Dict[str, Any]]) -> Optional[str]:
    # Find at least one FAILED phase and ensure it has error + failed_at
    for name, meta in phases.items():
        if meta.get("status") == "FAILED":
            if not meta.get("error"):
                return f"FAILED phase missing error field: {name}"
            if not meta.get("failed_at"):
                return f"FAILED phase missing failed_at timestamp: {name}"
            return None
    # If no failed phases, the check #6 isn't applicable; caller should enforce presence of FAILED elsewhere.
    return None


def _find_pipeline_resume_source(pipeline: str) -> Optional[Path]:
    """Find evidence that the pipeline supports --resume.

    Accept either:
    - a Python script containing --resume
    - OR a SKILL.md containing a --resume trigger
    """
    base = SKILLS_ROOT / pipeline

    candidates: List[Path] = []
    if base.exists():
        candidates.extend(list(base.rglob("*.py")))
        candidates.extend(list(base.rglob("SKILL.md")))
    else:
        # fallback: search all skills for a directory matching pipeline name
        for d in SKILLS_ROOT.iterdir():
            if d.is_dir() and d.name == pipeline:
                candidates.extend(list(d.rglob("*.py")))
                candidates.extend(list(d.rglob("SKILL.md")))

    for p in sorted(set(candidates)):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "--resume" in txt:
            return p
    return None


def check(pipeline: str) -> List[CheckResult]:
    results: List[CheckResult] = []

    # 1
    runs_dir = RUNS_ROOT / pipeline
    if not runs_dir.exists() or not runs_dir.is_dir():
        return [fail(f"missing runs directory: {runs_dir}")]

    run_dirs = [p for p in runs_dir.iterdir() if p.is_dir()]
    if not run_dirs:
        return [fail(f"no runs found in: {runs_dir}")]
    results.append(ok(f"found {len(run_dirs)} run(s) in {runs_dir}"))

    # 2
    try:
        latest_dir, run_id = _latest_run_dir(pipeline)
    except Exception as e:
        return results + [fail(str(e))]

    run_json_path = latest_dir / "run.json"
    if not run_json_path.exists():
        return results + [fail(f"latest run missing run.json: {run_json_path}")]

    try:
        run = _load_json(run_json_path)
    except Exception as e:
        return results + [fail(str(e))]

    try:
        phases = _get_phases(run)
    except Exception as e:
        return results + [fail(f"latest run {run_id} invalid: {e}")]

    results.append(ok(f"latest run {run_id} has {len(phases)} phase(s)"))

    # 3
    counts = _phase_status_counts(phases)
    if counts.get("DONE", 0) < 1:
        return results + [fail("no phase marked DONE")]
    results.append(ok("at least one phase is DONE"))

    # 4
    if counts.get("FAILED", 0) < 1 and counts.get("IN_PROGRESS", 0) < 1:
        return results + [fail("no phase marked FAILED or IN_PROGRESS")]
    results.append(ok("at least one phase is FAILED or IN_PROGRESS"))

    # 5
    src = _find_pipeline_resume_source(pipeline)
    if not src:
        return results + [fail("could not find --resume in either a .py script or SKILL.md under skills/<pipeline>/")]
    results.append(ok(f"--resume found in: {src}"))

    # 6
    if counts.get("FAILED", 0) >= 1:
        err = _assert_failure_fields(phases)
        if err:
            return results + [fail(err)]
        results.append(ok("FAILED phase(s) record error + failed_at"))
    else:
        # If we only saw IN_PROGRESS (allowed by check #4), still require timestamp presence.
        # run_ledger uses started_at for IN_PROGRESS.
        missing = None
        for name, meta in phases.items():
            if meta.get("status") == "IN_PROGRESS" and not meta.get("started_at"):
                missing = f"IN_PROGRESS phase missing started_at timestamp: {name}"
                break
        if missing:
            return results + [fail(missing)]
        results.append(ok("IN_PROGRESS phase(s) record started_at"))

    return results


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1].strip() in {"-h", "--help"}:
        print("Usage: /opt/anaconda3/bin/python3 ~/clawd/tools/check_resume_contract.py <pipeline_name>")
        return 2

    pipeline = sys.argv[1].strip()
    results = check(pipeline)

    bad = [r for r in results if not r.ok]
    if bad:
        # Print only first failure as requested.
        print(f"❌ FAIL: {bad[0].msg}")
        return 1

    print(f"✅ PASS: {pipeline} satisfies resume contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
