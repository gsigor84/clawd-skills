#!/opt/anaconda3/bin/python3
"""run_ledger.py

Run ledger standard for clawd pipelines.

Provides a tiny, deterministic API for creating a run directory and tracking
phase status in a single authoritative run.json.

Directory layout:
  ~/clawd/tmp/runs/<pipeline>/<run_id>/
    run.json

Run id:
  UTC timestamp with seconds resolution: YYYYMMDDTHHMMSSZ

Notes:
- All writes are atomic (write to tmp then rename).
- Locking: best-effort file lock (fcntl) on macOS/Linux.

Public API:
- create_run(pipeline_name, inputs) -> (run_id, run_dir)
- start_phase(run_id, phase_name)
- complete_phase(run_id, phase_name, artifacts)
- fail_phase(run_id, phase_name, error)
- get_resume_point(run_id) -> {last_done, next_phase}
- list_runs(pipeline_name) -> list[{run_id,status,updated_at,dir}]

"""

from __future__ import annotations

import json
import os
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


RUNS_ROOT = Path("/Users/igorsilva/clawd/tmp/runs")
RUN_ID_RE = re.compile(r"^\d{8}T\d{6}(?:\.\d{6})?Z$")


class RunLedgerError(Exception):
    pass


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_run_id() -> str:
    # Use microseconds to avoid collisions when creating multiple runs quickly.
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def _atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass


@contextmanager
def _file_lock(lock_path: Path):
    """Best-effort advisory lock.

    IMPORTANT: Do not create the run directory as a side-effect of locking.
    Lock files live alongside the run directory (in the pipeline dir).
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    f = open(lock_path, "a", encoding="utf-8")
    try:
        try:
            import fcntl

            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        except Exception:
            # If fcntl not available, proceed without lock.
            pass
        yield
    finally:
        try:
            import fcntl

            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        f.close()


def _run_dir_for(pipeline_name: str, run_id: str) -> Path:
    return RUNS_ROOT / pipeline_name / run_id


def _load_run_json(run_dir: Path) -> Dict[str, Any]:
    p = run_dir / "run.json"
    if not p.exists():
        raise RunLedgerError(f"run.json not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _save_run_json(run_dir: Path, obj: Dict[str, Any]) -> None:
    obj["updated_at"] = _utc_now_iso()
    _atomic_write_json(run_dir / "run.json", obj)


def create_run(pipeline_name: str, inputs: Dict[str, Any]) -> Tuple[str, Path]:
    """Create a new run dir and run.json.

    Returns: (run_id, run_dir)
    """
    run_id = _new_run_id()
    run_dir = _run_dir_for(pipeline_name, run_id)

    run = {
        "pipeline": pipeline_name,
        "run_id": run_id,
        "status": "IN_PROGRESS",
        "inputs": inputs,
        "phases": {},
        "created_at": _utc_now_iso(),
        "updated_at": _utc_now_iso(),
    }

    # Lock in the pipeline directory to avoid creating the run dir as a side effect.
    lock = (RUNS_ROOT / pipeline_name) / ".lock"
    with _file_lock(lock):
        if run_dir.exists():
            raise RunLedgerError(f"run already exists: {run_dir}")
        run_dir.mkdir(parents=True, exist_ok=False)
        _atomic_write_json(run_dir / "run.json", run)

    return run_id, run_dir


def start_phase(run_id: str, phase_name: str, pipeline_name: Optional[str] = None) -> None:
    run_dir = _resolve_run_dir(run_id, pipeline_name)
    lock = run_dir.parent / ".lock"
    with _file_lock(lock):
        run = _load_run_json(run_dir)
        phases = run.setdefault("phases", {})
        phases[phase_name] = {
            "status": "IN_PROGRESS",
            "started_at": _utc_now_iso(),
        }
        _save_run_json(run_dir, run)


def complete_phase(
    run_id: str,
    phase_name: str,
    artifacts: Iterable[str],
    pipeline_name: Optional[str] = None,
) -> None:
    run_dir = _resolve_run_dir(run_id, pipeline_name)
    lock = run_dir.parent / ".lock"
    with _file_lock(lock):
        run = _load_run_json(run_dir)
        phases = run.setdefault("phases", {})
        phases[phase_name] = {
            "status": "DONE",
            "completed_at": _utc_now_iso(),
            "artifacts": list(artifacts),
        }
        _save_run_json(run_dir, run)


def fail_phase(
    run_id: str,
    phase_name: str,
    error: str,
    pipeline_name: Optional[str] = None,
) -> None:
    run_dir = _resolve_run_dir(run_id, pipeline_name)
    lock = run_dir.parent / ".lock"
    with _file_lock(lock):
        run = _load_run_json(run_dir)
        phases = run.setdefault("phases", {})
        phases[phase_name] = {
            "status": "FAILED",
            "failed_at": _utc_now_iso(),
            "error": error,
        }
        run["status"] = "FAILED"
        _save_run_json(run_dir, run)


def get_resume_point(run_id: str, pipeline_name: Optional[str] = None) -> Dict[str, Optional[str]]:
    """Return last DONE phase and next phase to run.

    If there are no phases, last_done=None, next_phase=None.

    NOTE: This does not know the canonical phase order.
    It uses run.json insertion order as recorded.
    """
    run_dir = _resolve_run_dir(run_id, pipeline_name)
    run = _load_run_json(run_dir)
    phases: Dict[str, Any] = run.get("phases") or {}

    last_done = None
    for name, meta in phases.items():
        if (meta or {}).get("status") == "DONE":
            last_done = name

    # next phase is first non-DONE encountered after last_done in recorded order
    next_phase = None
    found_last = last_done is None
    for name, meta in phases.items():
        if not found_last:
            if name == last_done:
                found_last = True
            continue
        if (meta or {}).get("status") != "DONE":
            next_phase = name
            break

    return {"last_done": last_done, "next_phase": next_phase}


def list_runs(pipeline_name: str) -> List[Dict[str, Any]]:
    """List runs for a pipeline."""
    root = RUNS_ROOT / pipeline_name
    if not root.exists():
        return []

    out: List[Dict[str, Any]] = []
    for run_dir in sorted(root.iterdir()):
        if not run_dir.is_dir():
            continue
        p = run_dir / "run.json"
        if not p.exists():
            continue
        try:
            run = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        out.append(
            {
                "run_id": run.get("run_id"),
                "status": run.get("status"),
                "updated_at": run.get("updated_at"),
                "dir": str(run_dir),
            }
        )

    # newest first
    out.sort(key=lambda x: x.get("run_id") or "", reverse=True)
    return out


def _resolve_run_dir(run_id: str, pipeline_name: Optional[str]) -> Path:
    if pipeline_name:
        run_dir = _run_dir_for(pipeline_name, run_id)
        if not run_dir.exists():
            raise RunLedgerError(f"run not found: {run_dir}")
        return run_dir

    # Search all pipelines (bounded)
    if not RUN_ID_RE.match(run_id):
        raise RunLedgerError(f"invalid run_id: {run_id}")

    if not RUNS_ROOT.exists():
        raise RunLedgerError("runs root does not exist")

    matches = []
    for pipeline_dir in RUNS_ROOT.iterdir():
        if not pipeline_dir.is_dir():
            continue
        candidate = pipeline_dir / run_id
        if candidate.exists():
            matches.append(candidate)

    if not matches:
        raise RunLedgerError(f"run_id not found: {run_id}")
    if len(matches) > 1:
        raise RunLedgerError(f"ambiguous run_id (multiple pipelines): {run_id}")

    return matches[0]
