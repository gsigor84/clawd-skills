#!/opt/anaconda3/bin/python3
"""Batch skill rewrite runner with WhatsApp notifications.

Purpose
- Orchestrate a long-running rewrite batch by delegating each rewrite/judge step to the OpenClaw agent.
- On completion: trigger /notify done <summary>
- On halt (double-fail): trigger /notify halt <skill>

This runner uses OpenClaw's configured model/routing (openclaw.json) via:
  npx --yes openclaw agent --agent main --session-id <uuid> --json --message <prompt>

It does NOT call vendor APIs directly.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import uuid
from pathlib import Path


def run_openclaw_agent(message: str, *, agent_id: str = "main", timeout_s: int = 2400, session_id: str | None = None) -> str:
    # Force a fresh session-id by default to avoid cached/stale context influencing judge runs.
    sid = session_id or str(uuid.uuid4())
    cmd = [
        "npx",
        "--yes",
        "openclaw",
        "agent",
        "--agent",
        agent_id,
        "--session-id",
        sid,
        "--json",
        "--timeout",
        str(timeout_s),
        "--message",
        message,
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stdout)
    data = json.loads(p.stdout)
    payloads = (data.get("result") or {}).get("payloads") or []
    text = "".join([p.get("text", "") for p in payloads if isinstance(p, dict)]).strip()
    if not text:
        raise RuntimeError("empty_agent_payload_text")
    return text


LOG_DIR = Path("/Users/igorsilva/clawd/tmp/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_path_today() -> Path:
    return LOG_DIR / f"rewrite-batch-{dt.datetime.utcnow().strftime('%Y%m%d')}.log"


def log(line: str) -> None:
    ts = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    p = log_path_today()
    p.write_text(p.read_text(encoding="utf-8") + f"{ts} | {line}\n" if p.exists() else f"{ts} | {line}\n", encoding="utf-8")


JUDGE_PROMPT_PREFIX = (
    "You are grading an OpenClaw SKILL.md file for quality and operational safety.\n"
    "Return ONLY valid JSON. No markdown.\n\n"
    "Score each dimension from 0 to 5 (integers or halves allowed), where 5 is excellent.\n"
    "Dimensions:\n"
    "- task_fidelity\n- boundary_clarity\n- behavioral_test_adequacy\n- operational_clarity\n- safety_blast_radius\n\n"
    "Also include: avg (number), min_dim (number), pass (boolean), reasons (array of 3-8 short bullets).\n"
    "Pass criteria:\n- avg >= 4.0\n- no dimension below 3.0\n\n"
    "JSON schema: {\"task_fidelity\":0,\"boundary_clarity\":0,\"behavioral_test_adequacy\":0,\"operational_clarity\":0,\"safety_blast_radius\":0,\"avg\":0,\"min_dim\":0,\"pass\":false,\"reasons\":[]}\n\n"
)


def judge_skill(skill: str, *, agent_id: str = "main") -> dict:
    md_path = Path(f"/Users/igorsilva/clawd/skills/{skill}/SKILL.md")
    md = md_path.read_text(encoding="utf-8", errors="ignore")
    prompt = JUDGE_PROMPT_PREFIX + f"Skill name: {skill}\n\nSKILL.md:\n---\n{md}\n---\n"
    raw = run_openclaw_agent(prompt, agent_id=agent_id, timeout_s=600, session_id=str(uuid.uuid4()))
    j = json.loads(raw)
    # enforce policy regardless of judge claim
    dims = [
        float(j.get("task_fidelity", 0)),
        float(j.get("boundary_clarity", 0)),
        float(j.get("behavioral_test_adequacy", 0)),
        float(j.get("operational_clarity", 0)),
        float(j.get("safety_blast_radius", 0)),
    ]
    avg = sum(dims) / 5.0
    min_dim = min(dims)
    j["avg"] = float(j.get("avg", avg))
    j["min_dim"] = float(j.get("min_dim", min_dim))
    j["pass"] = j["avg"] >= 4.0 and j["min_dim"] >= 3.0
    return j


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="main")
    ap.add_argument("--skills", nargs="+", required=True)
    ap.add_argument("--start-from", default="")
    args = ap.parse_args()

    skills = args.skills
    if args.start_from:
        if args.start_from not in skills:
            raise SystemExit(f"start-from not in skills list: {args.start_from}")
        skills = skills[skills.index(args.start_from) :]

    passed = 0
    failed = 0

    for skill in skills:
        log(f"SKILL {skill} START")

        # Attempt 1: rewrite (agent does file ops + validators)
        rewrite_prompt = (
            f"Read /Users/igorsilva/clawd/skills/{skill}/SKILL.md, then rewrite it from scratch per rubric: trigger contract; deterministic workflow using OpenClaw tools with explicit branches; boundary rules (privacy/consent + disallowed + caps); required sections Use/Inputs/Outputs/Failure modes (no placeholders); and at least 5 behavioral acceptance tests with exact expectations. "
            f"Save the full rewrite in place at /Users/igorsilva/clawd/skills/{skill}/SKILL.md. "
            "Then run these deterministic checks via exec and ensure both PASS: "
            "(1) /opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py <path> "
            "(2) /opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py <path>. "
            "Do not run any judge; I will run judge externally."
        )
        _ = run_openclaw_agent(rewrite_prompt, agent_id=args.agent, timeout_s=2400, session_id=str(uuid.uuid4()))

        j1 = judge_skill(skill, agent_id=args.agent)
        log(f"SKILL {skill} JUDGE1 {json.dumps(j1, ensure_ascii=False)}")
        if j1.get("pass") is True:
            passed += 1
            log(f"SKILL {skill} PASS")
            continue

        # Attempt 2: targeted fix based on judge reasons
        reasons = j1.get("reasons") or []
        fix_prompt = (
            f"The skill '{skill}' failed the quality judge. Here are the judge reasons:\n" + "\n".join([f"- {r}" for r in reasons]) + "\n\n"
            "Fix ONLY what these reasons point to. Rewrite SKILL.md in place (full rewrite permitted), keep it deterministic, and keep validator compliance. "
            "Then re-run the same two deterministic validators via exec and ensure both PASS. Do not run any judge; I will re-judge."
        )
        _ = run_openclaw_agent(fix_prompt, agent_id=args.agent, timeout_s=2400, session_id=str(uuid.uuid4()))

        j2 = judge_skill(skill, agent_id=args.agent)
        log(f"SKILL {skill} JUDGE2 {json.dumps(j2, ensure_ascii=False)}")
        if j2.get("pass") is True:
            passed += 1
            log(f"SKILL {skill} PASS_AFTER_FIX")
            continue

        failed += 1
        log(f"SKILL {skill} DOUBLE_FAIL")
        # Halt condition: double-fail
        run_openclaw_agent(f"/notify halt {skill}", agent_id=args.agent, timeout_s=600, session_id=str(uuid.uuid4()))
        return 2

    run_openclaw_agent(f"/notify done {passed} pass, {failed} fail", agent_id=args.agent, timeout_s=600, session_id=str(uuid.uuid4()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
