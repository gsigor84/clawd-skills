#!/opt/anaconda3/bin/python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/Users/igorsilva/clawd')
RUNS_DIR = ROOT / 'tmp' / 'runs' / 'skill-forge'
NOTEBOOKLM_RUNS_DIR = ROOT / 'tmp' / 'runs' / 'notebooklm-runner'
RESEARCH_DIR = ROOT / 'tmp' / 'research-to-skill'
SKILL_FORGE_TMP = ROOT / 'tmp' / 'skill-forge'
SKILLS_DIR = ROOT / 'skills'

PHASE_ORDER = ['phase-0.5', 'phase-1', 'phase-2', 'phase-3', 'phase-4', 'phase-5', 'phase-6', 'phase-6.5', 'phase-7']
TERMINAL_COMPLETE = {'DONE', 'DONE_WITH_WARNINGS', 'SKIPPED', 'NO_OP'}

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return None


def read_json(path: Path) -> dict[str, Any] | None:
    txt = read_text(path)
    if txt is None:
        return None
    try:
        data = json.loads(txt)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def iso_from_file(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    except Exception:
        return None


def latest_run_id() -> str:
    candidates = [p.name for p in RUNS_DIR.iterdir() if p.is_dir()] if RUNS_DIR.exists() else []
    if not candidates:
        raise SystemExit('No skill-forge runs found.')
    return sorted(candidates)[-1]


def parse_progress(progress_text: str | None) -> tuple[list[int], list[int], list[int]]:
    if not progress_text:
        return [], [], []
    def grab(label: str) -> list[int]:
        m = re.search(rf"- {re.escape(label)}: \[([^\]]*)\]", progress_text)
        if not m:
            return []
        raw = m.group(1).strip()
        if not raw:
            return []
        out = []
        for part in raw.split(','):
            part = part.strip()
            if part.isdigit():
                out.append(int(part))
        return out
    return grab('OK'), grab('Partial'), grab('Missing')


def find_notebooklm_child(inputs: dict[str, Any], pass1_dir: Path) -> tuple[str | None, Path | None]:
    target_notebook = inputs.get('notebook_url')
    target_prompts = str((SKILL_FORGE_TMP / inputs.get('skill_name', '') / 'prompts').resolve())
    target_runs = str(pass1_dir.resolve())
    if not NOTEBOOKLM_RUNS_DIR.exists():
        return None, None
    best: tuple[str, Path] | None = None
    for run_dir in NOTEBOOKLM_RUNS_DIR.iterdir():
        if not run_dir.is_dir():
            continue
        run_json = run_dir / 'run.json'
        data = read_json(run_json)
        if not data:
            continue
        i = data.get('inputs') or {}
        if not isinstance(i, dict):
            continue
        if i.get('notebook_url') == target_notebook and i.get('prompts_dir') == target_prompts and i.get('runs_dir') == target_runs:
            best = (str(data.get('run_id') or run_dir.name), run_json)
    if best:
        return best
    return None, None


def prompt_files_info(prompts_dir: Path) -> tuple[int, list[str], list[str]]:
    missing, empty = [], []
    count = 0
    for i in range(1, 18):
        p = prompts_dir / f'p{i:02d}.txt'
        if p.exists():
            count += 1
            if not (read_text(p) or '').strip():
                empty.append(p.name)
        else:
            missing.append(p.name)
    return count, missing, empty


def latest_partial_error(pass_dir: Path) -> str | None:
    metas = sorted(pass_dir.glob('*.meta.json'), key=lambda p: p.stat().st_mtime)
    last_err = None
    for meta in metas:
        data = read_json(meta) or {}
        result = data.get('result') or {}
        if isinstance(result, dict) and result.get('partial'):
            last_err = str(result.get('error') or 'partial_error')
    return last_err


def count_gap_prompts(gap_prompts: Path) -> int:
    txt = read_text(gap_prompts) or ''
    return len(re.findall(r'^##+\s+Prompt\b|^###\s+Prompt\b', txt, re.M))


def validate_skill(skill_md: Path) -> tuple[bool, bool]:
    import subprocess
    validate = ROOT / 'skills' / 'skillmd-builder-agent' / 'scripts' / 'validate_skillmd.py'
    invented = ROOT / 'skills' / 'skillmd-builder-agent' / 'scripts' / 'check_no_invented_tools.py'
    v = subprocess.run(['/opt/anaconda3/bin/python3', str(validate), str(skill_md)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    i = subprocess.run(['/opt/anaconda3/bin/python3', str(invented), str(skill_md)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return v.returncode == 0, i.returncode == 0


def parse_critic_summary(log_path: Path, skill_name: str) -> dict[str, Any]:
    txt = read_text(log_path) or ''
    lines = [ln for ln in txt.splitlines() if f'SKILL {skill_name} ' in ln or 'INFO judge_' in ln]
    judge_errors = sum(1 for ln in lines if 'JUDGE_ERROR' in ln)
    pass_with_judge_error = any('PASS_WITH_JUDGE_ERROR' in ln for ln in lines)
    pass_clean = any(re.search(rf'SKILL {re.escape(skill_name)} PASS$', ln) for ln in lines)
    return {
        'critic_output_exists': log_path.exists(),
        'critic_passed': pass_with_judge_error or pass_clean,
        'judge_passed': any(' JUDGE {' in ln and '"pass": true' in ln for ln in lines),
        'judge_failed': any('FAIL_JUDGE' in ln for ln in lines),
        'judge_errors': judge_errors,
    }


def build_state(run_id: str) -> dict[str, Any]:
    run_dir = RUNS_DIR / run_id
    run_json_path = run_dir / 'run.json'
    run_json = read_json(run_json_path)
    if not run_json:
        raise SystemExit(f'Run not found or unreadable: {run_json_path}')
    inputs = run_json.get('inputs') or {}
    if not isinstance(inputs, dict):
        inputs = {}
    skill_name = str(inputs.get('skill_name') or '')
    base = RESEARCH_DIR / skill_name
    prompts_dir = SKILL_FORGE_TMP / skill_name / 'prompts'
    pass1_dir = base / 'pass1'
    gaps_dir = base / 'gaps'
    pass2_dir = base / 'pass2'
    synthesis_dir = base / 'synthesis'
    skill_md = SKILLS_DIR / skill_name / 'SKILL.md'
    pipeline_report = SKILL_FORGE_TMP / skill_name / 'pipeline-report.md'
    task_state = SKILL_FORGE_TMP / skill_name / 'task-state.json'

    state: dict[str, Any] = {
        'schema': 'skill-forge.state.v2',
        'run_id': run_id,
        'pipeline': 'skill-forge',
        'version': 2,
        'created_at': str(run_json.get('created_at') or utc_now()),
        'updated_at': utc_now(),
        'inputs': {
            'skill_name': skill_name,
            'topic': inputs.get('topic'),
            'goal': inputs.get('goal'),
            'notebook_url': inputs.get('notebook_url'),
            'mode': 'notebooklm' if inputs.get('notebook_url') else 'web-research',
            'creative': bool(inputs.get('creative', False)),
        },
        'paths': {
            'skill_forge_run_json': str(run_json_path),
            'task_state_json': str(task_state) if task_state.exists() else None,
            'prompts_dir': str(prompts_dir),
            'pass1_dir': str(pass1_dir),
            'gaps_dir': str(gaps_dir),
            'pass2_dir': str(pass2_dir),
            'synthesis_dir': str(synthesis_dir),
            'skill_md': str(skill_md),
            'pipeline_report': str(pipeline_report),
        },
        'children': {},
        'phases': {},
        'canonical_status': {},
        'resume': {},
        'warnings': [],
        'history': [],
    }

    child_id, child_run_json = find_notebooklm_child(inputs, pass1_dir)
    if child_id and child_run_json:
        state['children']['phase-1:notebooklm-runner'] = {
            'kind': 'pipeline', 'pipeline': 'notebooklm-runner', 'phase': 'phase-1', 'run_id': child_id,
            'status_hint': 'UNKNOWN', 'registered_at': iso_from_file(child_run_json) or utc_now(),
            'run_json': str(child_run_json), 'log_path': None,
            'resume_command': f"/opt/anaconda3/bin/python3 ~/clawd/skills/notebooklm-runner/scripts/run_notebooklm_runner.py --notebook-url \"{inputs.get('notebook_url')}\" --prompts-dir \"{prompts_dir}\" --runs-dir \"{pass1_dir}\" --progress-file \"{pass1_dir / 'progress.md'}\" --final-summary \"{pass1_dir / 'summary.md'}\" --resume --run-id {child_id}",
            'notes': []
        }

    critic_log = ROOT / 'tmp' / 'logs' / 'skill-improvement-20260401.log'
    if critic_log.exists():
        state['children']['phase-6:critic'] = {
            'kind': 'log-only', 'pipeline': 'self-improving-skill-builder', 'phase': 'phase-6', 'run_id': None,
            'status_hint': 'UNKNOWN', 'registered_at': iso_from_file(critic_log) or utc_now(), 'run_json': None,
            'log_path': str(critic_log), 'resume_command': None, 'notes': []
        }

    ledger_phases = (run_json.get('phases') or {}) if isinstance(run_json.get('phases'), dict) else {}

    def ledger_status(name: str) -> str:
        ph = ledger_phases.get(name) if isinstance(ledger_phases, dict) else None
        return str((ph or {}).get('status') or 'MISSING') if isinstance(ph, dict) else 'MISSING'

    # phase-0.5
    count, missing_pf, empty_pf = prompt_files_info(prompts_dir)
    p05_complete = prompts_dir.exists() and count == 17 and not missing_pf and not empty_pf
    state['phases']['phase-0.5'] = {
        'status': 'DONE' if p05_complete else ('IN_PROGRESS' if ledger_status('phase-0.5') == 'IN_PROGRESS' else 'PENDING'),
        'started_at': (ledger_phases.get('phase-0.5') or {}).get('started_at') if isinstance(ledger_phases.get('phase-0.5'), dict) else None,
        'completed_at': (ledger_phases.get('phase-0.5') or {}).get('completed_at') if isinstance(ledger_phases.get('phase-0.5'), dict) else None,
        'failed_at': (ledger_phases.get('phase-0.5') or {}).get('failed_at') if isinstance(ledger_phases.get('phase-0.5'), dict) else None,
        'source_of_truth': {'ledger': ledger_status('phase-0.5'), 'artifacts': 'COMPLETE' if p05_complete else 'PARTIAL', 'child_run': 'NOT_APPLICABLE'},
        'child_ref': None,
        'artifacts': {'prompts_dir': str(prompts_dir)},
        'checks': {'prompts_dir_exists': prompts_dir.exists(), 'prompt_count': count, 'missing_prompt_files': missing_pf, 'empty_prompt_files': empty_pf},
        'blocker': {'type': None, 'summary': None, 'since': None, 'recoverable': False},
        'resume': {'resume_kind': 'none' if p05_complete else 'parent-phase', 'command': None if p05_complete else f'/opt/anaconda3/bin/python3 ~/clawd/tools/skill_forge_resume.py --run-id {run_id} --from phase-0.5', 'why': None},
        'warnings': [], 'notes': []
    }

    # phase-1
    prog1 = pass1_dir / 'progress.md'
    sum1 = pass1_dir / 'summary.md'
    ok1, partial1, missing1 = parse_progress(read_text(prog1))
    child_json = read_json(child_run_json) if child_run_json else None
    child_top = str(child_json.get('status') or 'UNKNOWN') if child_json else 'NOT_APPLICABLE'
    latest_err = latest_partial_error(pass1_dir)
    p1_complete = prog1.exists() and sum1.exists() and len(missing1) == 0 and len(ok1) == 17
    p1_blocked = (latest_err is not None) and not p1_complete
    p1_status = 'DONE' if p1_complete else ('BLOCKED' if p1_blocked else ('IN_PROGRESS' if ledger_status('phase-1') in {'IN_PROGRESS', 'DONE'} or prog1.exists() else 'PENDING'))
    p1_warnings = []
    if p1_complete and child_top == 'FAILED':
        p1_warnings.append('child notebooklm-runner top-level ledger appears stale; artifacts complete')
        state['warnings'].append('child notebooklm-runner top-level ledger appears stale; artifacts complete')
    state['phases']['phase-1'] = {
        'status': p1_status,
        'started_at': (ledger_phases.get('phase-1') or {}).get('started_at') if isinstance(ledger_phases.get('phase-1'), dict) else None,
        'completed_at': (ledger_phases.get('phase-1') or {}).get('completed_at') if isinstance(ledger_phases.get('phase-1'), dict) else None,
        'failed_at': (ledger_phases.get('phase-1') or {}).get('failed_at') if isinstance(ledger_phases.get('phase-1'), dict) else None,
        'source_of_truth': {'ledger': ledger_status('phase-1'), 'artifacts': 'COMPLETE' if p1_complete else ('PARTIAL' if prog1.exists() else 'MISSING'), 'child_run': ('STALE' if p1_complete and child_top == 'FAILED' else child_top)},
        'child_ref': 'phase-1:notebooklm-runner' if child_id else None,
        'artifacts': {'progress_md': str(prog1), 'summary_md': str(sum1)},
        'checks': {'progress_md_exists': prog1.exists(), 'summary_md_exists': sum1.exists(), 'ok_prompts': ok1, 'partial_prompts': partial1, 'missing_prompts': missing1, 'latest_partial_error': latest_err},
        'blocker': {'type': 'CHILD_RUN_BLOCKED' if p1_blocked else None, 'summary': f'NotebookLM runner stalled: {latest_err}' if p1_blocked else None, 'since': iso_from_file(prog1) if p1_blocked else None, 'recoverable': bool(p1_blocked)},
        'resume': {'resume_kind': 'child-run' if (not p1_complete and child_id) else 'none', 'command': state['children'].get('phase-1:notebooklm-runner', {}).get('resume_command'), 'why': 'resume notebooklm child run' if (not p1_complete and child_id) else None},
        'warnings': p1_warnings, 'notes': []
    }

    # phase-2
    gap_prompts = gaps_dir / 'gap-prompts.md'
    gap_rules = gaps_dir / 'gap-rules.md'
    gap_count = count_gap_prompts(gap_prompts) if gap_prompts.exists() else 0
    p2_complete = gap_prompts.exists() and gap_rules.exists()
    p2_notes = ['gap analysis produced zero prompts'] if p2_complete and gap_count == 0 else []
    state['phases']['phase-2'] = {
        'status': 'DONE' if p2_complete else ('IN_PROGRESS' if ledger_status('phase-2') == 'IN_PROGRESS' else 'PENDING'),
        'started_at': (ledger_phases.get('phase-2') or {}).get('started_at') if isinstance(ledger_phases.get('phase-2'), dict) else None,
        'completed_at': (ledger_phases.get('phase-2') or {}).get('completed_at') if isinstance(ledger_phases.get('phase-2'), dict) else None,
        'failed_at': (ledger_phases.get('phase-2') or {}).get('failed_at') if isinstance(ledger_phases.get('phase-2'), dict) else None,
        'source_of_truth': {'ledger': ledger_status('phase-2'), 'artifacts': 'COMPLETE' if p2_complete else 'MISSING', 'child_run': 'NOT_APPLICABLE'},
        'child_ref': None,
        'artifacts': {'gap_prompts': str(gap_prompts), 'gap_rules': str(gap_rules)},
        'checks': {'gap_prompts_exists': gap_prompts.exists(), 'gap_rules_exists': gap_rules.exists(), 'gap_prompt_count': gap_count},
        'blocker': {'type': None, 'summary': None, 'since': None, 'recoverable': False},
        'resume': {'resume_kind': 'none' if p2_complete else 'parent-phase', 'command': None if p2_complete else f'/opt/anaconda3/bin/python3 ~/clawd/tools/skill_forge_resume.py --run-id {run_id} --from phase-2', 'why': None},
        'warnings': [], 'notes': p2_notes
    }

    # phase-3
    prog2 = pass2_dir / 'progress.md'
    sum2 = pass2_dir / 'summary.md'
    p3_noop = p2_complete and gap_count == 0
    p3_complete = p3_noop or (prog2.exists() and sum2.exists())
    p3_status = 'NO_OP' if p3_noop else ('DONE' if p3_complete else ('IN_PROGRESS' if ledger_status('phase-3') == 'IN_PROGRESS' else 'PENDING'))
    state['phases']['phase-3'] = {
        'status': p3_status,
        'started_at': (ledger_phases.get('phase-3') or {}).get('started_at') if isinstance(ledger_phases.get('phase-3'), dict) else None,
        'completed_at': (ledger_phases.get('phase-3') or {}).get('completed_at') if isinstance(ledger_phases.get('phase-3'), dict) else None,
        'failed_at': (ledger_phases.get('phase-3') or {}).get('failed_at') if isinstance(ledger_phases.get('phase-3'), dict) else None,
        'source_of_truth': {'ledger': ledger_status('phase-3'), 'artifacts': 'NOT_APPLICABLE' if p3_noop else ('COMPLETE' if p3_complete else 'MISSING'), 'child_run': 'NOT_APPLICABLE'},
        'child_ref': None,
        'artifacts': {'pass2_progress': str(prog2), 'pass2_summary': str(sum2)},
        'checks': {'pass2_progress_exists': prog2.exists(), 'pass2_summary_exists': sum2.exists(), 'pass2_effective_prompt_count': 0 if p3_noop else None},
        'blocker': {'type': None, 'summary': None, 'since': None, 'recoverable': False},
        'resume': {'resume_kind': 'none' if p3_complete else 'parent-phase', 'command': None if p3_complete else f'/opt/anaconda3/bin/python3 ~/clawd/tools/skill_forge_resume.py --run-id {run_id} --from phase-3', 'why': None},
        'warnings': [], 'notes': ['No-op phase due to zero gap prompts.'] if p3_noop else []
    }

    # phase-4
    enriched = synthesis_dir / 'enriched-summary.md'
    synth_rules = synthesis_dir / 'gap-rules.md'
    p4_complete = enriched.exists() and synth_rules.exists() and bool((read_text(enriched) or '').strip())
    p4_warnings = []
    if p4_complete and enriched.stat().st_size < 100000:
        p4_warnings.append('enriched-summary.md below heuristic 100KB threshold')
    state['phases']['phase-4'] = {
        'status': 'DONE' if p4_complete else ('IN_PROGRESS' if ledger_status('phase-4') == 'IN_PROGRESS' else 'PENDING'),
        'started_at': (ledger_phases.get('phase-4') or {}).get('started_at') if isinstance(ledger_phases.get('phase-4'), dict) else None,
        'completed_at': (ledger_phases.get('phase-4') or {}).get('completed_at') if isinstance(ledger_phases.get('phase-4'), dict) else None,
        'failed_at': (ledger_phases.get('phase-4') or {}).get('failed_at') if isinstance(ledger_phases.get('phase-4'), dict) else None,
        'source_of_truth': {'ledger': ledger_status('phase-4'), 'artifacts': 'COMPLETE' if p4_complete else 'MISSING', 'child_run': 'NOT_APPLICABLE'},
        'child_ref': None,
        'artifacts': {'enriched_summary': str(enriched), 'gap_rules': str(synth_rules)},
        'checks': {'enriched_summary_exists': enriched.exists(), 'gap_rules_exists': synth_rules.exists(), 'enriched_summary_bytes': enriched.stat().st_size if enriched.exists() else 0},
        'blocker': {'type': None, 'summary': None, 'since': None, 'recoverable': False},
        'resume': {'resume_kind': 'none' if p4_complete else 'parent-phase', 'command': None if p4_complete else f'/opt/anaconda3/bin/python3 ~/clawd/tools/skill_forge_resume.py --run-id {run_id} --from phase-4', 'why': None},
        'warnings': p4_warnings, 'notes': []
    }

    # phase-5
    v_ok, i_ok = validate_skill(skill_md) if skill_md.exists() else (False, False)
    p5_complete = skill_md.exists() and v_ok and i_ok
    state['phases']['phase-5'] = {
        'status': 'DONE' if p5_complete else ('FAILED' if skill_md.exists() else ('IN_PROGRESS' if ledger_status('phase-5') == 'IN_PROGRESS' else 'PENDING')),
        'started_at': (ledger_phases.get('phase-5') or {}).get('started_at') if isinstance(ledger_phases.get('phase-5'), dict) else None,
        'completed_at': (ledger_phases.get('phase-5') or {}).get('completed_at') if isinstance(ledger_phases.get('phase-5'), dict) else None,
        'failed_at': (ledger_phases.get('phase-5') or {}).get('failed_at') if isinstance(ledger_phases.get('phase-5'), dict) else None,
        'source_of_truth': {'ledger': ledger_status('phase-5'), 'artifacts': 'COMPLETE' if p5_complete else ('PARTIAL' if skill_md.exists() else 'MISSING'), 'child_run': 'NOT_APPLICABLE'},
        'child_ref': None,
        'artifacts': {'skill_md': str(skill_md)},
        'checks': {'skill_md_exists': skill_md.exists(), 'validator_pass': v_ok, 'no_invented_tools_pass': i_ok},
        'blocker': {'type': 'VALIDATION_FAILED' if skill_md.exists() and not p5_complete else None, 'summary': 'skill validators failing' if skill_md.exists() and not p5_complete else None, 'since': iso_from_file(skill_md) if skill_md.exists() and not p5_complete else None, 'recoverable': bool(skill_md.exists() and not p5_complete)},
        'resume': {'resume_kind': 'none' if p5_complete else 'parent-phase', 'command': None if p5_complete else f'/opt/anaconda3/bin/python3 ~/clawd/tools/skill_forge_resume.py --run-id {run_id} --from phase-5', 'why': None},
        'warnings': [], 'notes': []
    }

    # phase-6
    critic = parse_critic_summary(critic_log, skill_name) if critic_log.exists() else {'critic_output_exists': False, 'critic_passed': False, 'judge_passed': False, 'judge_failed': False, 'judge_errors': 0}
    p6_status = 'DONE_WITH_WARNINGS' if critic['critic_passed'] and critic['judge_errors'] > 0 else ('DONE' if critic['critic_passed'] else ('PENDING' if ledger_status('phase-6') == 'MISSING' else ledger_status('phase-6')))
    p6_warnings = []
    if critic['judge_errors'] > 0:
        p6_warnings.append('judge runtime emitted infrastructure errors unrelated to skill correctness')
        state['warnings'].append('critic completed with judge infrastructure warnings')
    state['phases']['phase-6'] = {
        'status': p6_status,
        'started_at': (ledger_phases.get('phase-6') or {}).get('started_at') if isinstance(ledger_phases.get('phase-6'), dict) else None,
        'completed_at': (ledger_phases.get('phase-6') or {}).get('completed_at') if isinstance(ledger_phases.get('phase-6'), dict) else None,
        'failed_at': (ledger_phases.get('phase-6') or {}).get('failed_at') if isinstance(ledger_phases.get('phase-6'), dict) else None,
        'source_of_truth': {'ledger': ledger_status('phase-6'), 'artifacts': 'COMPLETE' if critic['critic_output_exists'] else 'MISSING', 'child_run': 'NOT_APPLICABLE'},
        'child_ref': 'phase-6:critic' if critic_log.exists() else None,
        'artifacts': {'critic_log': str(critic_log) if critic_log.exists() else None},
        'checks': {**critic, 'deterministic_validators_pass': p5_complete},
        'blocker': {'type': None if critic['critic_passed'] else 'INFRA_BLOCKER', 'summary': None if critic['critic_passed'] else 'critic did not pass', 'since': iso_from_file(critic_log) if critic_log.exists() and not critic['critic_passed'] else None, 'recoverable': not critic['critic_passed']},
        'resume': {'resume_kind': 'none' if critic['critic_passed'] else 'parent-phase', 'command': None if critic['critic_passed'] else f'/opt/anaconda3/bin/python3 ~/clawd/skills/self-improving-skill-builder/scripts/improve_skills.py --skills-dir {SKILLS_DIR} --targets {skill_name}', 'why': None},
        'warnings': p6_warnings, 'notes': []
    }

    # phase-6.5 optional
    state['phases']['phase-6.5'] = {
        'status': 'PENDING', 'started_at': None, 'completed_at': None, 'failed_at': None,
        'source_of_truth': {'ledger': ledger_status('phase-6.5'), 'artifacts': 'NOT_APPLICABLE', 'child_run': 'NOT_APPLICABLE'},
        'child_ref': None, 'artifacts': {}, 'checks': {},
        'blocker': {'type': None, 'summary': None, 'since': None, 'recoverable': False},
        'resume': {'resume_kind': 'none', 'command': None, 'why': None}, 'warnings': [], 'notes': ['Phase 6.5 not implemented in current run.']
    }

    # phase-7
    p7_complete = pipeline_report.exists() and pipeline_report.stat().st_size > 0
    state['phases']['phase-7'] = {
        'status': 'DONE' if p7_complete else ('IN_PROGRESS' if ledger_status('phase-7') == 'IN_PROGRESS' else 'PENDING'),
        'started_at': (ledger_phases.get('phase-7') or {}).get('started_at') if isinstance(ledger_phases.get('phase-7'), dict) else None,
        'completed_at': (ledger_phases.get('phase-7') or {}).get('completed_at') if isinstance(ledger_phases.get('phase-7'), dict) else None,
        'failed_at': (ledger_phases.get('phase-7') or {}).get('failed_at') if isinstance(ledger_phases.get('phase-7'), dict) else None,
        'source_of_truth': {'ledger': ledger_status('phase-7'), 'artifacts': 'COMPLETE' if p7_complete else 'MISSING', 'child_run': 'NOT_APPLICABLE'},
        'child_ref': None,
        'artifacts': {'pipeline_report': str(pipeline_report)},
        'checks': {'pipeline_report_exists': pipeline_report.exists(), 'pipeline_report_bytes': pipeline_report.stat().st_size if pipeline_report.exists() else 0},
        'blocker': {'type': None, 'summary': None, 'since': None, 'recoverable': False},
        'resume': {'resume_kind': 'none' if p7_complete else 'parent-phase', 'command': None if p7_complete else f"/opt/anaconda3/bin/python3 ~/clawd/tools/pipeline_report.py --skill-name {skill_name} --mode notebooklm --notebook-url \"{inputs.get('notebook_url')}\"", 'why': None},
        'warnings': [], 'notes': []
    }

    # overall canonical status
    overall = 'PENDING'
    blocking_phase = None
    blocker_type = None
    blocker_summary = None
    for ph in PHASE_ORDER:
        st = state['phases'][ph]['status']
        if st == 'BLOCKED':
            overall = 'BLOCKED'; blocking_phase = ph; blocker_type = state['phases'][ph]['blocker']['type']; blocker_summary = state['phases'][ph]['blocker']['summary']; break
        if st == 'FAILED':
            overall = 'FAILED'; blocking_phase = ph; blocker_type = state['phases'][ph]['blocker']['type']; blocker_summary = state['phases'][ph]['blocker']['summary']; break
    else:
        if all(state['phases'][ph]['status'] in TERMINAL_COMPLETE for ph in PHASE_ORDER if ph != 'phase-6.5') and state['phases']['phase-5']['checks'].get('skill_md_exists'):
            overall = 'DONE_WITH_WARNINGS' if state['warnings'] or any(state['phases'][ph]['status'] == 'DONE_WITH_WARNINGS' for ph in PHASE_ORDER) else 'DONE'
        elif any(state['phases'][ph]['status'] in {'IN_PROGRESS'} for ph in PHASE_ORDER):
            overall = 'IN_PROGRESS'
        else:
            overall = 'PENDING'
    current_phase = None
    for ph in PHASE_ORDER:
        if state['phases'][ph]['status'] not in TERMINAL_COMPLETE:
            current_phase = ph
            break
    if current_phase is None:
        current_phase = 'phase-7'
    state['canonical_status'] = {
        'overall': overall,
        'current_phase': current_phase,
        'blocking_phase': blocking_phase,
        'blocker_type': blocker_type,
        'blocker_summary': blocker_summary,
        'ready_for_use': bool(state['phases']['phase-5']['checks'].get('skill_md_exists') and state['phases']['phase-5']['checks'].get('validator_pass') and state['phases']['phase-5']['checks'].get('no_invented_tools_pass')),
        'fully_clean': overall == 'DONE'
    }

    # resume section
    resolved_phase = None
    resolved_owner = None
    recommended = None
    next_action = None
    for ph in PHASE_ORDER:
        if state['phases'][ph]['status'] not in TERMINAL_COMPLETE:
            resolved_phase = ph
            child_ref = state['phases'][ph].get('child_ref')
            if child_ref and state['children'].get(child_ref, {}).get('resume_command'):
                resolved_owner = 'child'
                recommended = state['children'][child_ref]['resume_command']
            else:
                resolved_owner = 'parent'
                recommended = state['phases'][ph]['resume'].get('command')
            next_action = 'resume current incomplete phase'
            break
    state['resume'] = {
        'resume_supported': resolved_phase is not None,
        'next_action': next_action,
        'recommended_command': recommended,
        'resolved_phase': resolved_phase,
        'resolved_owner': resolved_owner,
    }

    if p1_blocked:
        state['history'].append({'at': iso_from_file(prog1) or utc_now(), 'event': 'phase blocked', 'phase': 'phase-1', 'reason': latest_err, 'details': 'recoverable partial NotebookLM failure'})
    return state


def render_md(state: dict[str, Any]) -> str:
    cs = state['canonical_status']
    lines = [
        '# skill-forge state',
        f"Run: {state['run_id']}",
        f"Skill: {state['inputs']['skill_name']}",
        f"Overall: {cs['overall']}",
        f"Ready for use: {'yes' if cs['ready_for_use'] else 'no'}",
        f"Fully clean: {'yes' if cs['fully_clean'] else 'no'}",
        '',
        '## Phases'
    ]
    for ph in PHASE_ORDER:
        pobj = state['phases'][ph]
        lines.append(f"- {ph} — {pobj['status']}")
        if pobj.get('child_ref'):
            child = state['children'].get(pobj['child_ref'], {})
            if child:
                lines.append(f"  - child: {child.get('pipeline')} {child.get('run_id') or ''}".rstrip())
        for note in pobj.get('notes', []):
            lines.append(f'  - note: {note}')
        for warning in pobj.get('warnings', []):
            lines.append(f'  - warning: {warning}')
    if state['warnings']:
        lines += ['', '## Warnings']
        lines.extend([f'- {w}' for w in state['warnings']])
    lines += ['', '## Resume']
    if state['resume']['recommended_command']:
        lines.append(state['resume']['recommended_command'])
    else:
        lines.append('No resume needed.')
    return '\n'.join(lines) + '\n'


def write_state(state: dict[str, Any]) -> tuple[Path, Path]:
    run_dir = RUNS_DIR / state['run_id']
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / 'state.json'
    md_path = run_dir / 'state.md'
    json_path.write_text(json.dumps(state, indent=2), encoding='utf-8')
    md_path.write_text(render_md(state), encoding='utf-8')
    return json_path, md_path


def cmd_status(state: dict[str, Any], as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(state, indent=2))
        return
    cs = state['canonical_status']
    print(f"RUN {state['run_id']}")
    print(f"SKILL: {state['inputs']['skill_name']}")
    print(f"OVERALL: {cs['overall']}")
    print(f"READY_FOR_USE: {'yes' if cs['ready_for_use'] else 'no'}")
    print(f"FULLY_CLEAN: {'yes' if cs['fully_clean'] else 'no'}")
    print('')
    if cs['overall'] == 'BLOCKED':
        print('CURRENT PHASE')
        print(f"- {cs['blocking_phase']}")
        print('')
        print('BLOCKER')
        print(f"- type: {cs['blocker_type']}")
        print(f"- summary: {cs['blocker_summary']}")
        phase = state['phases'][cs['blocking_phase']]
        if phase['blocker']['since']:
            print(f"- since: {phase['blocker']['since']}")
        print(f"- recoverable: {'yes' if phase['blocker']['recoverable'] else 'no'}")
        print('')
    elif cs['overall'] == 'IN_PROGRESS':
        print('CURRENT PHASE')
        print(f"- {cs['current_phase']}")
        print('')
        print('STATE')
        print(f"- {cs['current_phase']} is actively progressing")
        print('- no blocker currently detected')
        print('')
    else:
        print('FINAL STATE')
        if cs['ready_for_use']:
            print('- skill artifact exists')
            print('- deterministic validators passed')
        if state['phases']['phase-7']['checks'].get('pipeline_report_exists'):
            print('- pipeline report exists')
        if 'critic completed with judge infrastructure warnings' in state['warnings']:
            print('- critic completed with judge infrastructure warning')
        print('')
    print('PHASES')
    for ph in PHASE_ORDER:
        pobj = state['phases'][ph]
        print(f"- {ph}: {pobj['status']}")
        if pobj.get('child_ref'):
            child = state['children'].get(pobj['child_ref'], {})
            print(f"  child: {child.get('pipeline')} {child.get('run_id') or ''}".rstrip())
        if ph == 'phase-1':
            checks = pobj['checks']
            if checks.get('ok_prompts'):
                print(f"  ok_prompts: {checks.get('ok_prompts')}")
            if checks.get('missing_prompts'):
                print(f"  missing_prompts: {checks.get('missing_prompts')}")
        for note in pobj.get('notes', []):
            print(f"  note: {note}")
        for warning in pobj.get('warnings', []):
            print(f"  warning: {warning}")
    if state['warnings']:
        print('')
        print('WARNINGS')
        for w in state['warnings']:
            print(f'- {w}')
    print('')
    print('NEXT ACTION')
    print(state['resume']['recommended_command'] or '- none')


def cmd_brief(state: dict[str, Any]) -> None:
    cs = state['canonical_status']
    if cs['overall'] == 'IN_PROGRESS':
        p1 = state['phases'].get('phase-1', {})
        ok = len(p1.get('checks', {}).get('ok_prompts', []))
        total = ok + len(p1.get('checks', {}).get('missing_prompts', []))
        print(f"IN_PROGRESS | {state['inputs']['skill_name']} | {cs['current_phase']} | ok={ok}/{total or 17} | blocker=none")
    elif cs['overall'].startswith('DONE'):
        print(f"{cs['overall']} | {state['inputs']['skill_name']} | ready={'yes' if cs['ready_for_use'] else 'no'} | clean={'yes' if cs['fully_clean'] else 'no'} | report={'yes' if state['phases']['phase-7']['checks'].get('pipeline_report_exists') else 'no'}")
    elif cs['overall'] == 'BLOCKED':
        print(f"BLOCKED | {state['inputs']['skill_name']} | {cs['blocking_phase']} | blocker={cs['blocker_type']}")
    else:
        print(f"{cs['overall']} | {state['inputs']['skill_name']}")


def cmd_explain(state: dict[str, Any], phase: str) -> None:
    if phase not in state['phases']:
        raise SystemExit(f'Unknown phase: {phase}')
    pobj = state['phases'][phase]
    print(f"{phase} canonical status = {pobj['status']}")
    print('')
    print('Reasoning:')
    if pobj.get('child_ref'):
        child = state['children'].get(pobj['child_ref'], {})
        print(f"- child run registered: {child.get('pipeline')} {child.get('run_id')}")
    for k, v in pobj.get('checks', {}).items():
        print(f'- {k}={v}')
    if pobj['status'] == 'DONE' and pobj['source_of_truth']['child_run'] == 'STALE':
        print('- therefore artifact completion rule is satisfied')
        print('- child top-level FAILED status ignored as stale because required outputs are complete')
    if pobj['blocker']['summary']:
        print(f"- blocker: {pobj['blocker']['summary']}")


def cmd_resume(state: dict[str, Any], do_exec: bool) -> None:
    if not state['resume']['resume_supported']:
        print('No resume needed.')
        return
    cmd = state['resume']['recommended_command']
    print(cmd)
    if do_exec and cmd:
        os.execvp('/bin/zsh', ['/bin/zsh', '-lc', cmd])


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ['status', 'brief', 'resume', 'recompute', 'explain']:
        sp = sub.add_parser(name)
        sp.add_argument('run_id', nargs='?', help='skill-forge run id (defaults to latest)')
        if name == 'status':
            sp.add_argument('--json', action='store_true')
        if name == 'resume':
            sp.add_argument('--exec', action='store_true', dest='do_exec')
        if name == 'explain':
            sp.add_argument('--phase', required=True)
    args = ap.parse_args()
    run_id = args.run_id or latest_run_id()
    state = build_state(run_id)
    write_state(state)
    if args.cmd == 'status':
        cmd_status(state, as_json=args.json)
    elif args.cmd == 'brief':
        cmd_brief(state)
    elif args.cmd == 'resume':
        cmd_resume(state, do_exec=args.do_exec)
    elif args.cmd == 'recompute':
        print(f"RECOMPUTED {run_id}")
        print(f"OVERALL: {state['canonical_status']['overall']}")
        print(f"READY_FOR_USE: {'yes' if state['canonical_status']['ready_for_use'] else 'no'}")
    elif args.cmd == 'explain':
        cmd_explain(state, args.phase)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
