#!/opt/anaconda3/bin/python3
"""Deterministic validator for OpenClaw SKILL.md files.

Designed to support the skillmd-builder-agent FSM.

Checks (hard requirements):
- YAML frontmatter exists and is delimited by ---
- Frontmatter contains ONLY: name, description
- name matches: lowercase letters/digits/hyphens, <=64 chars
- description non-empty
- Body contains required sections:
  - how to use / steps
  - inputs/outputs
  - failure modes / hard blockers
  - acceptance tests (must-pass)

Exit codes:
- 0: PASS
- 2: FAIL (validation errors)
- 3: IO/parse error
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")

REQUIRED_SECTION_PATTERNS = {
    "use": re.compile(r"^##\s+Use\b", re.M),
    "inputs": re.compile(r"^##\s+Inputs\b", re.M),
    "outputs": re.compile(r"^##\s+Outputs\b", re.M),
    "failure_modes": re.compile(r"^##\s+(Failure modes|Hard blockers)\b", re.M),
    "acceptance_tests": re.compile(r"^##\s+Acceptance tests\b", re.M),
}


def parse_frontmatter(md: str):
    # Must start with --- on line 1
    if not md.startswith("---\n") and md.strip()[:3] != "---":
        raise ValueError("missing_frontmatter_start")

    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)\Z", md, re.S)
    if not m:
        raise ValueError("frontmatter_not_closed")

    fm_raw = m.group(1)
    body = m.group(2)

    fm = {}
    for ln in fm_raw.splitlines():
        if not ln.strip():
            continue
        if ln.lstrip().startswith("#"):
            continue
        if ":" not in ln:
            raise ValueError(f"frontmatter_bad_line: {ln}")
        k, v = ln.split(":", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if not k:
            raise ValueError(f"frontmatter_bad_key: {ln}")
        if k in fm:
            raise ValueError(f"frontmatter_duplicate_key: {k}")
        fm[k] = v

    return fm, body


def validate_skillmd(path: Path) -> list[str]:
    errs: list[str] = []
    try:
        md = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"io_error: {e}"]

    try:
        fm, body = parse_frontmatter(md)
    except Exception as e:
        return [f"frontmatter_error: {e}"]

    keys = set(fm.keys())
    if keys != {"name", "description"}:
        errs.append(f"frontmatter_keys_must_be_exactly_name_and_description: got={sorted(keys)}")

    name = (fm.get("name") or "").strip()
    if not name:
        errs.append("frontmatter_missing_name")
    elif not NAME_RE.match(name):
        errs.append("frontmatter_invalid_name_format")

    desc = (fm.get("description") or "").strip()
    if not desc:
        errs.append("frontmatter_missing_description")

    # Body section checks
    for sec, pat in REQUIRED_SECTION_PATTERNS.items():
        if not pat.search(body or ""):
            errs.append(f"missing_required_section:{sec}")

    # Acceptance tests should contain at least 2 items AND include executable/behavioral coverage
    acc_block = re.search(r"^##\s+Acceptance tests\b(.*?)(?:\n##\s+|\Z)", body, re.S | re.M)
    if not acc_block:
        errs.append("acceptance_tests_block_not_found")
    else:
        acc = acc_block.group(1)

        # count items (numbered or checkboxes)
        numbered = len(re.findall(r"^\s*\d+\.\s+", acc, re.M))
        checkboxes = len(re.findall(r"^\s*[-*]\s+\[ \]\s+", acc, re.M))
        if numbered + checkboxes < 2:
            errs.append("acceptance_tests_too_few_items")

        acc_lower = acc.lower()

        # Must include at least one test that exercises the skill behavior (not just file-format validators).
        # Behavioral invocation: a slash command or Run/Invoke line.
        has_slash_command = bool(re.search(r"`/[^`\s]+(?:\s+[^`]+)?`", acc))
        has_run_invoke = bool(re.search(r"^\s*(run|invoke):\s*/[a-z0-9\-]+\b", acc_lower, re.M))
        has_behavioral_invocation = has_slash_command or has_run_invoke

        # Runtime expectation: explicit Expected + output-related keywords.
        mentions_runtime_expectation = bool(re.search(r"\bexpected\b", acc_lower)) and bool(
            re.search(r"\b(output|json|array|file|saved|error message|starts with|contains|parses as)\b", acc_lower)
        )

        # Executability: at least one concrete command (code fence or backticked shell/python).
        has_code_fence = bool(re.search(r"```(?:bash|sh|zsh|shell)?\n.*?\n```", acc, re.S))
        has_backticked_command = bool(re.search(r"`/(?:[^`\s]+)`", acc)) or bool(re.search(r"`/opt/anaconda3/bin/python3\b", acc))
        if not (has_code_fence or has_backticked_command):
            errs.append("acceptance_tests_should_include_executable_commands")

        # If the block mentions only structural validators and contains no behavioral invocation, fail.
        mentions_structural_validators = bool(re.search(r"validate_skillmd\.py|check_no_invented_tools\.py", acc))
        only_structural = mentions_structural_validators and not has_behavioral_invocation

        if not (has_behavioral_invocation and mentions_runtime_expectation) or only_structural:
            errs.append("acceptance_tests_must_include_behavioral_tests")

        # Encourage at least one negative/edge-case test (heuristic).
        # We treat this as required because most skills have failure modes and need at least one hard-stop test.
        has_negative = bool(re.search(r"\b(not found|wrong|invalid|error|fails|refuse|blocked|missing)\b", acc_lower))
        if not has_negative:
            errs.append("acceptance_tests_should_include_negative_case")

    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Path to SKILL.md")
    args = ap.parse_args()

    p = Path(args.path)
    errs = validate_skillmd(p)
    if errs:
        sys.stdout.write("FAIL\n")
        for e in errs:
            sys.stdout.write(f"- {e}\n")
        return 2

    sys.stdout.write("PASS\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
