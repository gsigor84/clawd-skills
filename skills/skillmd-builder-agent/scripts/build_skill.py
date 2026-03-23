#!/opt/anaconda3/bin/python3
"""skillmd-builder-agent runner.

Purpose
- Deterministically generate a draft SKILL.md from a minimal spec (name + goal)
- Enforce the FSM checklist (State 0 → 0.5 → 1 → 2 → 3 → 4 → 5)
- Run deterministic validators:
  - validate_skillmd.py
  - check_no_invented_tools.py
- Log each state transition to: ~/clawd/tmp/logs/skillmd-builder-YYYYMMDD.log

This is intentionally conservative: it generates a structurally-valid, behaviorally-specified skill skeleton
with strict I/O, explicit failure modes, and executable acceptance tests.

It is NOT an LLM and does not attempt deep domain heuristics beyond a small set of baked-in patterns.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path("/Users/igorsilva/clawd")
SKILLS_DIR = ROOT / "skills"
LOGS_DIR = ROOT / "tmp" / "logs"
VALIDATE = SKILLS_DIR / "skillmd-builder-agent" / "scripts" / "validate_skillmd.py"
NO_INVENTED = SKILLS_DIR / "skillmd-builder-agent" / "scripts" / "check_no_invented_tools.py"
PY = Path("/opt/anaconda3/bin/python3")


NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")


def log_path_for_today() -> Path:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return LOGS_DIR / f"skillmd-builder-{dt.datetime.utcnow().strftime('%Y%m%d')}.log"


def log_line(msg: str) -> None:
    lp = log_path_for_today()
    ts = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    lp.write_text(lp.read_text(encoding="utf-8") + f"{ts} | {msg}\n" if lp.exists() else f"{ts} | {msg}\n", encoding="utf-8")


def die(msg: str, code: int = 2) -> "never":
    print(msg, file=sys.stderr)
    log_line(f"ERROR | {msg}")
    raise SystemExit(code)


def sanitize_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"[^a-z0-9-]", "-", name)
    name = re.sub(r"-+", "-", name)
    name = name.strip("-")
    return name


def find_reference_skills(goal: str, k: int = 3) -> list[Path]:
    """Cheap heuristic: score skills by keyword overlap with goal + known categories."""
    goal_l = goal.lower()
    hints = []
    if any(w in goal_l for w in ["summar", "summary", "summarize"]):
        hints += ["summarize", "url-arg-summarizer"]
    if any(w in goal_l for w in ["extract", "concept"]):
        hints += ["auto-extract", "extract-concept"]
    if any(w in goal_l for w in ["validate", "validator"]):
        hints += ["skillmd-builder-agent"]

    # candidate skills are directories with SKILL.md
    candidates = []
    for d in sorted(SKILLS_DIR.iterdir()):
        if not d.is_dir():
            continue
        sp = d / "SKILL.md"
        if sp.exists():
            candidates.append(sp)

    scores: list[tuple[int, Path]] = []
    for sp in candidates:
        txt = sp.read_text(encoding="utf-8", errors="ignore")
        t = txt.lower()
        score = 0
        for h in hints:
            if h in t or h in sp.as_posix().lower():
                score += 10
        # overlap on generic words
        for w in ["summary", "summarize", "text file", "txt", "output", "strict", "acceptance tests", "failure"]:
            if w in goal_l and w in t:
                score += 1
        # slight preference to shorter skills (often tighter contracts)
        score -= min(len(txt) // 5000, 3)
        scores.append((score, sp))

    scores.sort(key=lambda x: x[0], reverse=True)
    # remove self if present
    out = [p for s, p in scores if p.parent.name != "skillmd-builder-agent"]
    return out[:k]


def build_skill_md(name: str, goal: str, refs: list[Path]) -> str:
    """Generate a conservative SKILL.md for a file-based text summarizer."""

    # State 0.5 constraint architecture (embedded as explicit Guardrails/Failure modes)
    musts = [
        "Return 3–5 sentences.",
        "Include a short list of key topics.",
        "If the file is missing/unreadable, return the exact error output.",
        "Single-turn: read → summarize → output.",
    ]
    must_nots = [
        "Do not use web tools.",
        "Do not write any files.",
        "Do not run exec/process.",
        "Do not invent details not present in the text.",
    ]
    preferences = [
        "Prefer plain language over jargon.",
        "Prefer concrete nouns/verbs over abstract phrasing.",
        "If the text is long, summarize the central thesis + 2–4 main supporting points.",
    ]
    escalations = [
        "If the user asks for summarization of non-text (pdf/image/audio) → ask for a .txt export.",
    ]

    ref_lines = "\n".join([f"- {p.as_posix()}" for p in refs]) if refs else "- (none found)"

    return f"""---
name: {name}
description: \"Trigger: /{name} <absolute-file-path>. Read a local .txt file and output a 3–5 sentence summary plus key topics.\"
---

# {name}

## Use

Summarize a local **.txt** file into **3–5 sentences** and list the **key topics**.

### Trigger
- `/{name} <absolute-file-path>`

### Steps

#### STEP 1 — Validate input
1) Confirm `<absolute-file-path>` exists and is readable.
   - If not, output exactly and **Then stop.**
     ❌ File not found: <path>
     💡 Check the path is correct and the file exists.
2) Confirm file extension is `.txt`.
   - If not, output exactly and **Then stop.**
     ❌ This skill only supports .txt files. Got: <extension>
     💡 Convert your file to .txt first, then re-run.

#### STEP 2 — Read source
Use `read` to load the full file.

#### STEP 3 — Produce summary
- Output a 3–5 sentence summary grounded in the text.
- Then output `Key topics:` followed by 3–8 bullets.
- Do not invent facts; if the text is too thin, state that explicitly in the summary.

## Inputs

- `absolute-file-path` (required)
  - Must be an absolute path to a readable `.txt` file.

## Outputs

### Success
Output exactly:
- `Summary:` then 3–5 sentences.
- `Key topics:` then 3–8 bullets.

### Errors (exact strings)
- Missing/unreadable file:
  - `❌ File not found: <path>`
  - `💡 Check the path is correct and the file exists.`
- Wrong extension:
  - `❌ This skill only supports .txt files. Got: <extension>`
  - `💡 Convert your file to .txt first, then re-run.`

## Failure modes

### Musts
{os.linesep.join([f"- {m}" for m in musts])}

### Must-nots
{os.linesep.join([f"- {m}" for m in must_nots])}

### Preferences
{os.linesep.join([f"- {p}" for p in preferences])}

### Escalation triggers
{os.linesep.join([f"- {e}" for e in escalations])}

## Toolset

- `read`

## Acceptance tests

1. **Behavioral: missing file**
   - Run: `/{name} /path/does/not/exist.txt`
   - Expected: exactly the 2-line file-not-found error.

2. **Behavioral: wrong extension**
   - Run: `/{name} /abs/path/to/file.pdf`
   - Expected: exactly the 2-line wrong-extension error.

3. **Behavioral: output shape**
   - Run: `/{name} /abs/path/to/file.txt`
   - Expected:
     - Starts with `Summary:`
     - Contains 3–5 sentences
     - Contains `Key topics:` followed by 3–8 bullets

4. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/{name}/SKILL.md
```
Expected: `PASS`.

5. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/{name}/SKILL.md
```
Expected: `PASS`.

## References (retrieved patterns)

Closest skills used as pattern references:
{ref_lines}
"""


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="Skill name (kebab-case)")
    ap.add_argument("--goal", required=True, help="Goal description")
    ap.add_argument("--out-dir", required=True, help="Output directory (skill folder)")
    args = ap.parse_args()

    log_line(f"START name={args.name} out_dir={args.out_dir}")

    # State 0 — INTAKE
    log_line("STATE 0 INTAKE")
    name = sanitize_name(args.name)
    if not NAME_RE.match(name):
        die(f"invalid_skill_name: {args.name} -> {name}")
    goal = (args.goal or "").strip()
    if len(goal) < 10:
        die("goal_too_short")

    # State 0.5 — CONSTRAINT_ARCHITECTURE
    log_line("STATE 0.5 CONSTRAINT_ARCHITECTURE")
    # (In this deterministic runner, constraints are embedded as Failure modes buckets.)

    # State 1 — RETRIEVE
    log_line("STATE 1 RETRIEVE")
    refs = find_reference_skills(goal, k=3)

    # State 2 — DRAFT
    log_line("STATE 2 DRAFT")
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    skill_md_path = out_dir / "SKILL.md"
    md = build_skill_md(name=name, goal=goal, refs=refs)
    skill_md_path.write_text(md, encoding="utf-8")

    # State 3 — VALIDATE
    log_line("STATE 3 VALIDATE")
    vcode, vout = run([str(PY), str(VALIDATE), str(skill_md_path)])
    tcode, tout = run([str(PY), str(NO_INVENTED), str(skill_md_path)])

    if vcode == 0 and tcode == 0:
        log_line("STATE 5 FINALIZE")
        print("VALIDATION: PASS")
        print(vout.rstrip())
        print(tout.rstrip())
        print(f"WROTE: {skill_md_path}")
        return 0

    # State 4 — REPAIR (bounded: 1 deterministic pass)
    log_line("STATE 4 REPAIR")
    # Deterministic repair: if validators fail, stop with diagnostics (no guessing).
    print("VALIDATION: FAIL")
    print("--- validate_skillmd.py ---")
    print(vout.rstrip())
    print("--- check_no_invented_tools.py ---")
    print(tout.rstrip())
    log_line(f"FAIL validate_code={vcode} invented_code={tcode}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
