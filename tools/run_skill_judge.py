#!/opt/anaconda3/bin/python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/Users/igorsilva/clawd')
ARTIFACT_BASE = ROOT / 'tmp' / 'skill-judge'
OPENCLAW = Path.home() / '.nvm' / 'versions' / 'node' / 'v22.16.0' / 'bin' / 'openclaw'
JUDGE_MIN_AVG = 4.0
JUDGE_MIN_DIM = 3.0


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def judge_prompt(skill_name: str, md: str) -> str:
    return (
        "You are grading an OpenClaw SKILL.md file for quality and operational safety.\n"
        "Return ONLY valid JSON. No markdown.\n\n"
        "Score each dimension from 0 to 5 (integers or halves allowed), where 5 is excellent.\n"
        "Dimensions:\n"
        "- task_fidelity: Does the skill do what its Trigger/Use claims, without drift?\n"
        "- boundary_clarity: Are constraints explicit (what must/must not happen), and tool boundaries clear?\n"
        "- behavioral_test_adequacy: Are acceptance tests realistic, executable, and covering behavior + negative case?\n"
        "- operational_clarity: Can an operator run it reliably (inputs, outputs, steps, failure modes)?\n"
        "- safety_blast_radius: Is the blast radius bounded (no dangerous defaults), safe-by-default?\n\n"
        "Also include: avg (number), min_dim (number), pass (boolean), reasons (array of 3-8 short bullets).\n"
        f"Pass criteria:\n- avg >= {JUDGE_MIN_AVG}\n- no dimension below {JUDGE_MIN_DIM}\n\n"
        "JSON schema:\n"
        "{\n"
        '  "task_fidelity": 0,\n'
        '  "boundary_clarity": 0,\n'
        '  "behavioral_test_adequacy": 0,\n'
        '  "operational_clarity": 0,\n'
        '  "safety_blast_radius": 0,\n'
        '  "avg": 0,\n'
        '  "min_dim": 0,\n'
        '  "pass": false,\n'
        '  "reasons": []\n'
        "}\n\n"
        f"Skill name: {skill_name}\n\n"
        "SKILL.md:\n---\n" + md + "\n---\n"
    )


def classify(stdout: str, stderr: str, exit_code: int, parsed: dict[str, Any] | None) -> tuple[str, str | None]:
    combined = (stdout + '\n' + stderr).lower()
    infra_markers = [
        'failed to load', 'cannot find module', 'gateway', 'auth',
        'empty_payload_text', 'openclaw_agent_failed', 'openclaw_agent_output_parse_failed',
        'judge_timeout_after='
    ]
    if exit_code != 0:
        if any(m in combined for m in infra_markers):
            return 'JUDGE_INFRA_FAIL', 'judge command failed due to infrastructure/runtime issue'
        return 'JUDGE_FAIL', 'judge command exited non-zero'
    if parsed is None:
        if any(m in combined for m in infra_markers):
            return 'JUDGE_INFRA_FAIL', 'judge output polluted by infrastructure/runtime issue'
        return 'JUDGE_FAIL', 'judge stdout was not valid JSON'
    avg = float(parsed.get('avg', 0))
    min_dim = float(parsed.get('min_dim', 0))
    if avg >= JUDGE_MIN_AVG and min_dim >= JUDGE_MIN_DIM:
        return 'SKILL_PASS', None
    return 'SKILL_FAIL', 'judge scores below threshold'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--skill-name', required=True)
    ap.add_argument('--skill-md', required=True)
    ap.add_argument('--agent', default='main')
    ap.add_argument('--timeout-seconds', type=int, default=45)
    args = ap.parse_args()

    skill_md_path = Path(args.skill_md)
    md = skill_md_path.read_text(encoding='utf-8', errors='replace')
    out_dir = ARTIFACT_BASE / args.skill_name
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    stdout_path = out_dir / f'{stamp}.stdout.txt'
    stderr_path = out_dir / f'{stamp}.stderr.txt'
    result_path = out_dir / f'{stamp}.result.json'

    env = os.environ.copy()
    env['OPENCLAW_GATEWAY_TOKEN'] = env.get('OPENCLAW_GATEWAY_TOKEN') or json.load(open(Path.home()/'.openclaw'/'openclaw.json')).get('gateway', {}).get('auth', {}).get('token', '')
    cmd = [str(OPENCLAW), 'agent', '--agent', args.agent, '--json', '--timeout', '600', '--message', judge_prompt(args.skill_name, md)]
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=args.timeout_seconds)
        stdout = p.stdout
        stderr = p.stderr
        exit_code = p.returncode
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout or ''
        stderr = (e.stderr or '') + f'\njudge_timeout_after={args.timeout_seconds}s'
        exit_code = 124
    stdout_path.write_text(stdout, encoding='utf-8')
    stderr_path.write_text(stderr, encoding='utf-8')

    parsed = None
    raw = stdout
    i = raw.find('{')
    if i != -1:
        raw = raw[i:]
    try:
        outer = json.loads(raw)
        payloads = (((outer.get('result') or {}).get('payloads')) or []) if isinstance(outer, dict) else []
        text = ''.join([x.get('text', '') for x in payloads if isinstance(x, dict)]).strip()
        parsed = json.loads(text)
    except Exception:
        parsed = None

    status, summary = classify(stdout, stderr, exit_code, parsed)
    result = {
        'schema': 'skill-judge.result.v1',
        'status': status,
        'transport': {
            'exit_code': exit_code,
            'stdout_json_valid': parsed is not None,
            'stderr_nonempty': bool(stderr.strip()),
        },
        'judge': {
            'avg': None if parsed is None else float(parsed.get('avg', 0)),
            'min_dim': None if parsed is None else float(parsed.get('min_dim', 0)),
            'pass': None if parsed is None else bool(parsed.get('pass', False)),
            'raw': parsed,
        },
        'error': {
            'type': None if summary is None else status,
            'summary': summary,
        },
        'artifacts': {
            'stdout_path': str(stdout_path),
            'stderr_path': str(stderr_path),
            'result_json_path': str(result_path),
        },
        'created_at': utc_now(),
    }
    result_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
