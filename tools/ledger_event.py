#!/opt/anaconda3/bin/python3
"""ledger_event.py

Strict CLI wrapper around tools/run_ledger.py with invariant enforcement.

Usage:
  /opt/anaconda3/bin/python3 ledger_event.py create <pipeline> '<input_json>'
    -> prints run_id

  /opt/anaconda3/bin/python3 ledger_event.py start <run_id> <phase> <pipeline>
    -> prints STARTED

  /opt/anaconda3/bin/python3 ledger_event.py done <run_id> <phase> <pipeline> [artifacts...]
    -> prints DONE

  /opt/anaconda3/bin/python3 ledger_event.py fail <run_id> <phase> <pipeline> '<error>'
    -> prints FAILED

  /opt/anaconda3/bin/python3 ledger_event.py resume <run_id> <pipeline>
    -> prints last_done and next_phase as JSON

  /opt/anaconda3/bin/python3 ledger_event.py run <run_id> <phase> <pipeline> -- <shell command...>
    -> executes shell command with strict ledger accounting

Invariants enforced:
- done: refuse if phase was never started
- fail: refuse if phase was never started; require non-empty error
- start: refuse if phase is already DONE
- all: require run_id to exist (pipeline is required)

Exit codes:
- 0 success
- 2 usage/invalid args
- 3 invariant violation
- 4 run not found
- 5 other error

Run subcommand behaviour:
- calls start (refuses if already DONE)
- executes the shell command
- if exit 0 → calls done
- if exit non-0 → calls fail with stderr + exit code
- returns the underlying exit code
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List
import subprocess

sys.path.insert(0, "/Users/igorsilva/clawd/tools")

from run_ledger import (  # type: ignore
    RunLedgerError,
    complete_phase,
    create_run,
    fail_phase,
    get_resume_point,
    start_phase,
)


RUNS_ROOT = Path("/Users/igorsilva/clawd/tmp/runs")


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _usage() -> None:
    _eprint(__doc__.strip())


def _run_dir(pipeline: str, run_id: str) -> Path:
    return RUNS_ROOT / pipeline / run_id


def _load_run_json(pipeline: str, run_id: str) -> Dict[str, Any]:
    p = _run_dir(pipeline, run_id) / "run.json"
    if not p.exists():
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text(encoding="utf-8"))


def _phase_meta(run: Dict[str, Any], phase: str) -> Dict[str, Any] | None:
    phases = run.get("phases")
    if not isinstance(phases, dict):
        return None
    meta = phases.get(phase)
    return meta if isinstance(meta, dict) else None


def _require_run_exists(pipeline: str, run_id: str) -> None:
    rd = _run_dir(pipeline, run_id)
    if not rd.exists() or not rd.is_dir():
        raise RunLedgerError(f"run not found: {rd}")
    if not (rd / "run.json").exists():
        raise RunLedgerError(f"run.json not found: {rd / 'run.json'}")


def cmd_create(argv: List[str]) -> int:
    if len(argv) != 4:
        _usage()
        return 2
    _, _, pipeline, input_json = argv
    try:
        inputs = json.loads(input_json)
        if not isinstance(inputs, dict):
            raise ValueError("inputs must be a JSON object")
    except Exception as e:
        _eprint(f"ERROR: invalid input_json ({e})")
        return 2

    try:
        run_id, _ = create_run(pipeline, inputs)
        print(run_id)
        return 0
    except Exception as e:
        _eprint(f"ERROR: {e}")
        return 5


def cmd_start(argv: List[str]) -> int:
    if len(argv) != 5:
        _usage()
        return 2
    _, _, run_id, phase, pipeline = argv

    try:
        _require_run_exists(pipeline, run_id)
    except Exception as e:
        _eprint(f"ERROR: {e}")
        return 4

    try:
        run = _load_run_json(pipeline, run_id)
        meta = _phase_meta(run, phase)
        if meta and meta.get("status") == "DONE":
            _eprint(f"INVARIANT: phase already DONE; refusing start ({phase})")
            return 3

        start_phase(run_id, phase, pipeline_name=pipeline)
        print("STARTED")
        return 0
    except Exception as e:
        _eprint(f"ERROR: {e}")
        return 5


def cmd_done(argv: List[str]) -> int:
    if len(argv) < 5:
        _usage()
        return 2
    _, _, run_id, phase, pipeline, *artifacts = argv

    try:
        _require_run_exists(pipeline, run_id)
    except Exception as e:
        _eprint(f"ERROR: {e}")
        return 4

    try:
        run = _load_run_json(pipeline, run_id)
        meta = _phase_meta(run, phase)
        if not meta or meta.get("status") != "IN_PROGRESS":
            _eprint(f"INVARIANT: phase was never started (must be IN_PROGRESS) ({phase})")
            return 3

        complete_phase(run_id, phase, artifacts=artifacts, pipeline_name=pipeline)
        print("DONE")
        return 0
    except Exception as e:
        _eprint(f"ERROR: {e}")
        return 5


def cmd_fail(argv: List[str]) -> int:
    if len(argv) != 6:
        _usage()
        return 2
    _, _, run_id, phase, pipeline, error = argv
    if not str(error).strip():
        _eprint("INVARIANT: error must be non-empty")
        return 3

    try:
        _require_run_exists(pipeline, run_id)
    except Exception as e:
        _eprint(f"ERROR: {e}")
        return 4

    try:
        run = _load_run_json(pipeline, run_id)
        meta = _phase_meta(run, phase)
        if not meta or meta.get("status") != "IN_PROGRESS":
            _eprint(f"INVARIANT: phase was never started (must be IN_PROGRESS) ({phase})")
            return 3

        fail_phase(run_id, phase, error=error, pipeline_name=pipeline)
        print("FAILED")
        return 0
    except Exception as e:
        _eprint(f"ERROR: {e}")
        return 5


def cmd_resume(argv: List[str]) -> int:
    if len(argv) != 4:
        _usage()
        return 2
    _, _, run_id, pipeline = argv

    try:
        _require_run_exists(pipeline, run_id)
    except Exception as e:
        _eprint(f"ERROR: {e}")
        return 4

    try:
        rp = get_resume_point(run_id, pipeline_name=pipeline)
        print(json.dumps(rp, ensure_ascii=False))
        return 0
    except Exception as e:
        _eprint(f"ERROR: {e}")
        return 5


def cmd_run(argv: List[str]) -> int:
    if "--" not in argv:
        _usage()
        return 2

    dd = argv.index("--")
    head = argv[:dd]
    cmd = argv[dd + 1 :]

    if len(head) != 5 or not cmd:
        _usage()
        return 2

    _, _, run_id, phase, pipeline = head

    try:
        _require_run_exists(pipeline, run_id)
    except Exception as e:
        _eprint(f"ERROR: {e}")
        return 4

    # Start (enforces "not already DONE")
    start_rc = cmd_start([argv[0], "start", run_id, phase, pipeline])
    if start_rc != 0:
        return start_rc

    # Execute command, capture stderr (for failure recording)
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode == 0:
        done_rc = cmd_done([argv[0], "done", run_id, phase, pipeline])
        if done_rc != 0:
            return done_rc
        return 0

    # Failure: record stderr + exit code
    stderr = (p.stderr or "").strip()
    if not stderr:
        stderr = (p.stdout or "").strip()
    if not stderr:
        stderr = "(no stderr/stdout captured)"

    err = f"exit={p.returncode}; {stderr}"
    fail_rc = cmd_fail([argv[0], "fail", run_id, phase, pipeline, err])
    if fail_rc != 0:
        return fail_rc

    return int(p.returncode)


def main() -> int:
    if len(sys.argv) < 2:
        _usage()
        return 2

    cmd = sys.argv[1]

    if cmd == "create":
        return cmd_create(sys.argv)
    if cmd == "start":
        return cmd_start(sys.argv)
    if cmd == "done":
        return cmd_done(sys.argv)
    if cmd == "fail":
        return cmd_fail(sys.argv)
    if cmd == "resume":
        return cmd_resume(sys.argv)
    if cmd == "run":
        return cmd_run(sys.argv)

    _usage()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
