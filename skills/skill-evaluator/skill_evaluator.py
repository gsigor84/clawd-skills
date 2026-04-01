#!/opt/anaconda3/bin/python3
"""skill_evaluator.py

Execution-grade evaluator for OpenClaw skills.

Given a target skill directory containing SKILL.md, this tool:
- extracts acceptance tests from SKILL.md (fenced code blocks)
- classifies each test as:
  - DETERMINISTIC: safe to execute locally (no network writes, no destructive ops)
  - MANUAL_REQUIRED: needs human judgement or external credentials/env
- executes deterministic tests and records evidence:
  - command
  - cwd
  - exit code
  - stdout/stderr paths
  - duration
- records artefact hashes (sha256) for requested paths
- writes a signed PASS/FAIL report (json + markdown)

Design principle: make claims costly and truth cheap.
"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha256_path(path: Path) -> Dict[str, str]:
    """Return mapping of relative file paths to sha256 for a file or directory."""
    if path.is_file():
        return {path.name: sha256_file(path)}
    out: Dict[str, str] = {}
    for p in sorted(path.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(path))
            out[rel] = sha256_file(p)
    return out


_CODEBLOCK_RE = re.compile(r"```(?:bash|sh|zsh|shell)?\n(.*?)\n```", re.DOTALL)


@dataclasses.dataclass
class AcceptanceTest:
    idx: int
    name: str
    raw_block: str
    command: str
    classification: str  # DETERMINISTIC|MANUAL_REQUIRED
    reason: str


def extract_acceptance_tests(skill_md: str) -> List[AcceptanceTest]:
    """Extract acceptance tests fenced code blocks under '## Acceptance tests' (best-effort).

    We treat each fenced block in that section as a runnable candidate.
    """
    # slice to acceptance tests section if present
    lower = skill_md.lower()
    start = lower.find("## acceptance tests")
    if start != -1:
        skill_md_section = skill_md[start:]
    else:
        skill_md_section = skill_md

    blocks = _CODEBLOCK_RE.findall(skill_md_section)

    tests: List[AcceptanceTest] = []
    for i, b in enumerate(blocks, start=1):
        cmd = b.strip()
        name = f"acceptance-test-{i}"
        classification, reason = classify_command(cmd)
        tests.append(
            AcceptanceTest(
                idx=i,
                name=name,
                raw_block=b,
                command=cmd,
                classification=classification,
                reason=reason,
            )
        )
    return tests


_DESTRUCTIVE_PATTERNS = [
    r"\brm\b.*\b-rf\b",
    r"\bsudo\b",
    r"\bpkill\b",
    r"\bkill\b",
    r"\blaunchctl\b",
    r"\bbrew\s+install\b",
    r"\bpip\s+install\b",
    r"\bnpm\s+install\b",
    r"\bgit\s+push\b",
]


def classify_command(cmd: str) -> Tuple[str, str]:
    c = cmd.strip()
    if not c:
        return "MANUAL_REQUIRED", "empty command"

    # multi-line: allow but classify if contains risky lines
    if any(re.search(p, c) for p in _DESTRUCTIVE_PATTERNS):
        return "MANUAL_REQUIRED", "potentially destructive or privileged operation detected"

    # network calls are deterministic in principle but non-reproducible without pinning; require manual unless explicitly local.
    if re.search(r"\bcurl\b|\bwget\b|\bhttp[s]?://", c):
        if "127.0.0.1" in c or "localhost" in c:
            return "DETERMINISTIC", "local network call"
        return "MANUAL_REQUIRED", "network dependency: requires stable external connectivity/service"

    # requires external creds / env vars
    if re.search(r"OPENAI_API_KEY|BRAVE_API_KEY|AWS_|GCP_|AZURE_|NOTION_|SLACK_", c):
        return "MANUAL_REQUIRED", "requires external credentials/env"

    # if it references /Users/igorsilva/clawd and runs python validators, allow.
    return "DETERMINISTIC", "appears safe to execute locally"


@dataclasses.dataclass
class CommandResult:
    command: str
    cwd: str
    exit_code: int
    duration_ms: int
    stdout_path: str
    stderr_path: str


def run_command(cmd: str, cwd: Path, evidence_dir: Path, idx: int) -> CommandResult:
    stdout_path = evidence_dir / f"cmd_{idx:03d}.stdout.txt"
    stderr_path = evidence_dir / f"cmd_{idx:03d}.stderr.txt"

    start = time.time()
    p = subprocess.run(
        cmd,
        cwd=str(cwd),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy(),
    )
    dur_ms = int((time.time() - start) * 1000)

    stdout_path.write_text(p.stdout, encoding="utf-8", errors="replace")
    stderr_path.write_text(p.stderr, encoding="utf-8", errors="replace")

    return CommandResult(
        command=cmd,
        cwd=str(cwd),
        exit_code=p.returncode,
        duration_ms=dur_ms,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
    )


def load_signing_key(key_path: Path) -> bytes:
    b = key_path.read_bytes()
    b = b.strip()
    # allow raw 32 bytes or base64
    if len(b) == 32:
        return b
    try:
        return base64.b64decode(b)
    except Exception as e:
        raise SystemExit(f"invalid signing key format: {e}")


def sign_report(report_bytes: bytes, key: bytes) -> str:
    """HMAC-like signing using sha256(key||report).

    This is *not* public-key signing; it is intentionally low-dependency.
    If you need public verification, swap to pynacl/cryptography.
    """
    h = hashlib.sha256()
    h.update(key)
    h.update(report_bytes)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", required=True, help="Path to target skill directory")
    ap.add_argument("--out-dir", required=True, help="Directory to write reports/evidence")
    ap.add_argument("--signing-key", required=False, help="Path to signing key (32 raw bytes or base64)")
    ap.add_argument("--hash", action="append", default=[], help="Additional file/dir paths to hash (repeatable)")
    ap.add_argument("--allow-run", action="store_true", help="Execute deterministic tests (otherwise classify-only)")

    args = ap.parse_args()

    skill_dir = Path(args.skill_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir = out_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    skill_md_path = skill_dir / "SKILL.md"
    if not skill_md_path.exists():
        print(f"ERROR: SKILL.md not found: {skill_md_path}", file=sys.stderr)
        return 2

    md = skill_md_path.read_text(encoding="utf-8", errors="replace")
    tests = extract_acceptance_tests(md)

    results: List[Dict[str, Any]] = []
    overall_pass = True

    cmd_idx = 0
    for t in tests:
        tr: Dict[str, Any] = dataclasses.asdict(t)
        if t.classification == "DETERMINISTIC" and args.allow_run:
            cmd_idx += 1
            r = run_command(t.command, cwd=skill_dir, evidence_dir=evidence_dir, idx=cmd_idx)
            tr["execution"] = dataclasses.asdict(r)
            tr["pass"] = r.exit_code == 0
            if r.exit_code != 0:
                overall_pass = False
        else:
            tr["execution"] = None
            tr["pass"] = None
            if t.classification == "MANUAL_REQUIRED":
                overall_pass = False
        results.append(tr)

    # hashes
    hash_targets = [skill_md_path] + [Path(p).expanduser().resolve() for p in args.hash]
    hash_manifest: Dict[str, Dict[str, str]] = {}
    for p in hash_targets:
        if not p.exists():
            continue
        hash_manifest[str(p)] = sha256_path(p)

    report: Dict[str, Any] = {
        "tool": "skill-evaluator",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "skill_dir": str(skill_dir),
        "skill_md": str(skill_md_path),
        "allow_run": bool(args.allow_run),
        "overall": "PASS" if overall_pass else "FAIL",
        "tests": results,
        "hashes": hash_manifest,
    }

    report_json_path = out_dir / "report.json"
    report_json_bytes = json.dumps(report, indent=2, sort_keys=True).encode("utf-8")
    report_json_path.write_bytes(report_json_bytes)

    sig = None
    if args.signing_key:
        key = load_signing_key(Path(args.signing_key))
        sig = sign_report(report_json_bytes, key)

    # markdown report
    md_lines = []
    md_lines.append(f"# skill-evaluator report")
    md_lines.append("")
    md_lines.append(f"Skill: `{skill_dir}`")
    md_lines.append(f"Overall: **{report['overall']}**")
    md_lines.append(f"Allow run: `{args.allow_run}`")
    if sig:
        md_lines.append(f"Signature: `{sig}`")
    md_lines.append("")
    md_lines.append("## Tests")
    for t in results:
        md_lines.append(f"- {t['name']}: {t['classification']} — {t['reason']}")
        if t.get("execution"):
            ex = t["execution"]
            md_lines.append(f"  - exit_code: {ex['exit_code']} duration_ms: {ex['duration_ms']}")
            md_lines.append(f"  - stdout: `{ex['stdout_path']}`")
            md_lines.append(f"  - stderr: `{ex['stderr_path']}`")
            md_lines.append(f"  - command: `{ex['command']}`")
    md_lines.append("")
    md_lines.append("## Hash manifest (sha256)")
    for tgt, files in hash_manifest.items():
        md_lines.append(f"- {tgt}")
        for rel, h in list(files.items())[:50]:
            md_lines.append(f"  - {rel}: `{h}`")
        if len(files) > 50:
            md_lines.append(f"  - ... ({len(files)-50} more)")

    report_md_path = out_dir / "report.md"
    report_md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # write signature sidecar
    if sig:
        (out_dir / "report.sig").write_text(sig + "\n", encoding="utf-8")

    print(str(report_json_path))
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
