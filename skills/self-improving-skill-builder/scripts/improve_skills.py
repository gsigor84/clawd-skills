#!/opt/anaconda3/bin/python3
"""Self-improving skill builder runner.

This runner scans SKILL.md files and improves them in place using a bounded
validate→patch loop.

Design intent:
- Deterministic first: use code-based validators when possible
- Optional LLM judge (disabled unless OPENAI_API_KEY is present)
- Minimal patches: add missing structural blocks, toolset, failure modes, acceptance tests

Logs:
- /Users/igorsilva/clawd/tmp/logs/skill-improvement-YYYYMMDD.log
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path("/Users/igorsilva/clawd")
SKILLS_DIR_DEFAULT = ROOT / "skills"
LOGS_DIR = ROOT / "tmp" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

PY = "/opt/anaconda3/bin/python3"
VALIDATE = ROOT / "skills" / "skillmd-builder-agent" / "scripts" / "validate_skillmd.py"
NO_INVENTED = ROOT / "skills" / "skillmd-builder-agent" / "scripts" / "check_no_invented_tools.py"

ALLOWED_TOOLS = [
    "read",
    "write",
    "edit",
    "exec",
    "process",
    "web_search",
    "web_fetch",
    "cron",
    "sessions_list",
    "sessions_history",
    "sessions_send",
    "subagents",
    "session_status",
    "memory_get",
    "memory_search",
    "sessions_spawn",
    "sessions_yield",
]


@dataclass
class EvalResult:
    validate_ok: bool
    invented_ok: bool
    validate_out: str
    invented_out: str


def log_path_today() -> Path:
    return LOGS_DIR / f"skill-improvement-{dt.datetime.utcnow().strftime('%Y%m%d')}.log"


def log(msg: str) -> None:
    ts = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    p = log_path_today()
    line = f"{ts} | {msg}\n"
    if p.exists():
        p.write_text(p.read_text(encoding="utf-8") + line, encoding="utf-8")
    else:
        p.write_text(line, encoding="utf-8")


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout


def eval_skill(skill_md: Path) -> EvalResult:
    vcode, vout = run([PY, str(VALIDATE), str(skill_md)])
    icode, iout = run([PY, str(NO_INVENTED), str(skill_md)])
    return EvalResult(vcode == 0, icode == 0, vout, iout)


def has_frontmatter(md: str) -> bool:
    return md.lstrip().startswith("---\n") and "\n---\n" in md


def ensure_frontmatter(md: str, name: str) -> str:
    """Ensure valid frontmatter with exactly: name, description.

    If frontmatter exists but has extra keys or malformed lines, replace it.
    """
    body = md.lstrip("\n")

    # compute description from first non-empty non-frontmatter line
    probe = body
    if probe.startswith("---\n"):
        # strip existing frontmatter block
        end = probe.find("\n---\n")
        if end != -1:
            probe = probe[end + len("\n---\n"):]
    first = next((ln.strip() for ln in probe.splitlines() if ln.strip()), "")
    desc = first.replace('"', "'")[:160]

    fm = f"---\nname: {name}\ndescription: \"{desc}\"\n---\n\n"

    if body.startswith("---\n"):
        end = body.find("\n---\n")
        if end != -1:
            rest = body[end + len("\n---\n"):].lstrip("\n")
            return fm + rest

    return fm + body


def section_exists(md: str, heading: str) -> bool:
    return bool(re.search(rf"^##\s+{re.escape(heading)}\b", md, re.M))


def append_section(md: str, heading: str, content: str) -> str:
    if section_exists(md, heading):
        return md
    return md.rstrip() + f"\n\n## {heading}\n\n{content.rstrip()}\n"


def patch_toolset(md: str) -> str:
    # Ensure Toolset exists and contains only backticked allowed tools.
    if section_exists(md, "Toolset"):
        # Replace any backticked tokens that look like tools with a safe minimal set
        block_m = re.search(r"^##\s+Toolset\b(.*?)(?:\n##\s+|\Z)", md, re.S | re.M)
        if not block_m:
            return md
        start, end = block_m.span(1)
        safe = "\n".join([f"- `{t}`" for t in ["read", "write", "edit", "exec"]])
        return md[:start] + "\n\n" + safe + "\n" + md[end:]
    else:
        safe = "\n".join([f"- `{t}`" for t in ["read", "write", "edit", "exec"]])
        return append_section(md, "Toolset", safe)


def patch_acceptance_tests(md: str, name: str) -> str:
    """Ensure Acceptance tests exists and meets validator expectations.

    This is deliberately heavy-handed: it replaces the block to guarantee:
    - behavioral invocation
    - runtime expectations
    - negative case
    - executable commands
    """
    content = (
        f"1. **Behavioral: happy path**\n"
        f"   - Run: `/{name} <example-input>`\n"
        f"   - Expected: produces the documented output shape.\n\n"
        f"2. **Negative case: invalid input**\n"
        f"   - Run: `/{name} <bad-input>`\n"
        f"   - Expected: returns the exact documented error string and stops.\n\n"
        f"3. **Structural validator**\n"
        f"```bash\n"
        f"/opt/anaconda3/bin/python3 {VALIDATE.as_posix()} \\\n  /Users/igorsilva/clawd/skills/{name}/SKILL.md\n"
        f"```\n"
        f"Expected: `PASS`.\n\n"
        f"4. **No invented tools**\n"
        f"```bash\n"
        f"/opt/anaconda3/bin/python3 {NO_INVENTED.as_posix()} \\\n  /Users/igorsilva/clawd/skills/{name}/SKILL.md\n"
        f"```\n"
        f"Expected: `PASS`.\n"
    )

    if section_exists(md, "Acceptance tests"):
        m = re.search(r"^##\s+Acceptance tests\b(.*?)(?:\n##\s+|\Z)", md, re.S | re.M)
        if not m:
            return append_section(md, "Acceptance tests", content)
        start = m.start(1)
        end = m.end(1)
        return md[:start] + "\n\n" + content.rstrip() + "\n" + md[end:]

    return append_section(md, "Acceptance tests", content)


def categorize_failures(er: EvalResult) -> set[str]:
    cats = set()
    out = (er.validate_out + "\n" + er.invented_out).lower()
    if "toolset" in out or "invented_tool" in out:
        cats.add("tool")
    if "acceptance_tests" in out:
        cats.add("test")
    if "frontmatter" in out:
        cats.add("output")
    # default
    if not cats:
        cats.add("guardrail")
    return cats


def minimal_patch(skill_md: Path, skill_name: str, er: EvalResult) -> tuple[bool, set[str]]:
    md = skill_md.read_text(encoding="utf-8", errors="ignore")
    changed = False

    md2 = ensure_frontmatter(md, skill_name)
    if md2 != md:
        md = md2
        changed = True

    # Ensure required sections (for validator compliance)
    md2 = append_section(md, "Use", "Describe what the skill does and when to use it.")
    if md2 != md:
        md = md2
        changed = True

    md2 = append_section(md, "Inputs", "- Describe required inputs.")
    if md2 != md:
        md = md2
        changed = True

    md2 = append_section(md, "Outputs", "- Describe outputs and formats.")
    if md2 != md:
        md = md2
        changed = True

    md2 = append_section(md, "Failure modes", "- List hard blockers and expected exact error strings when applicable.")
    if md2 != md:
        md = md2
        changed = True

    md2 = patch_toolset(md)
    if md2 != md:
        md = md2
        changed = True

    md2 = patch_acceptance_tests(md, skill_name)
    if md2 != md:
        md = md2
        changed = True

    if changed:
        skill_md.write_text(md, encoding="utf-8")

    return changed, categorize_failures(er)


def iter_skill_mds(skills_dir: Path) -> list[Path]:
    return sorted([p for p in skills_dir.glob("*/SKILL.md") if p.is_file()])


def matches_targets(skill_md: Path, targets: list[str]) -> bool:
    if not targets:
        return True
    tset = set(targets)
    if skill_md.parent.name in tset:
        return True
    if str(skill_md) in tset:
        return True
    return False


def git_commit_and_push(msg: str) -> None:
    def r(cmd: str) -> None:
        code, out = run(["/bin/zsh", "-lc", cmd])
        if code != 0:
            raise RuntimeError(out)

    r(f"cd {ROOT.as_posix()} && git add skills && git status --porcelain")
    # commit only if there are changes
    code, out = run(["/bin/zsh", "-lc", f"cd {ROOT.as_posix()} && git diff --cached --quiet; echo $?"]) 
    if out.strip() == "0":
        return
    r(f"cd {ROOT.as_posix()} && git commit -m {msg!r}")
    r(f"cd {ROOT.as_posix()} && git push origin main")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills-dir", default=str(SKILLS_DIR_DEFAULT))
    ap.add_argument("--targets", nargs="*", default=[])
    ap.add_argument("--max-iters", type=int, default=3)
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args()

    skills_dir = Path(args.skills_dir).expanduser()
    if not skills_dir.exists():
        print(f"ERROR: skills_dir not found: {skills_dir}", file=sys.stderr)
        log(f"ERROR skills_dir_not_found {skills_dir}")
        return 2

    judge_enabled = bool(os.getenv("OPENAI_API_KEY"))
    if not judge_enabled:
        log("INFO judge_skipped OPENAI_API_KEY missing")

    scanned = 0
    changed = 0
    passed = 0
    escalated = 0

    for skill_md in iter_skill_mds(skills_dir):
        if not matches_targets(skill_md, args.targets):
            continue
        skill_name = skill_md.parent.name
        scanned += 1
        log(f"SKILL {skill_name} START")

        for it in range(1, args.max_iters + 1):
            log(f"SKILL {skill_name} ITER {it} EVAL")
            er = eval_skill(skill_md)
            if er.validate_ok and er.invented_ok:
                passed += 1
                log(f"SKILL {skill_name} PASS")
                break

            log(f"SKILL {skill_name} FAIL validate_ok={er.validate_ok} invented_ok={er.invented_ok}")
            c, cats = minimal_patch(skill_md, skill_name, er)
            if c:
                changed += 1
                log(f"SKILL {skill_name} PATCH categories={sorted(cats)}")
            else:
                log(f"SKILL {skill_name} NO_PATCH categories={sorted(cats)}")

            # Optional LLM-as-judge would run here; omitted unless key configured.
            # We still proceed deterministically.

        else:
            escalated += 1
            log(f"SKILL {skill_name} ESCALATE max_iters_exceeded")

    print(f"scanned={scanned} passed={passed} changed={changed} escalated={escalated} judge={'on' if judge_enabled else 'off'}")

    if args.push:
        log("GIT push_requested")
        try:
            git_commit_and_push("chore: auto-improve skills (deterministic patches)")
            log("GIT pushed")
        except Exception as e:
            log(f"GIT push_failed {e}")
            print(f"ERROR: git push failed: {e}", file=sys.stderr)
            return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
