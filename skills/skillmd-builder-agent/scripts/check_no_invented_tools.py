#!/opt/anaconda3/bin/python3
"""Check a SKILL.md doesn't mention invented tools.

Heuristic: collect backticked identifiers that look like tool names in the "Toolset" section
and ensure they are in an allowlist.

Exit codes:
- 0 PASS
- 2 FAIL
- 3 IO/PARSE
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ALLOWED_TOOLS = {
    # OpenClaw core tools available in this workspace (per environment/tooling policy)
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
    "image",
    "memory_get",
    "memory_search",
    "sessions_spawn",
    "sessions_yield",
}


def extract_toolset_block(md: str) -> str:
    # naive: find "## Toolset" block
    m = re.search(r"^##\s+Toolset\b(.*?)(?:\n##\s+|\Z)", md, re.S | re.M)
    return m.group(1) if m else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Path to SKILL.md")
    args = ap.parse_args()

    p = Path(args.path)
    try:
        md = p.read_text(encoding="utf-8")
    except Exception as e:
        print(f"IO_ERROR: {e}")
        return 3

    block = extract_toolset_block(md)
    if not block.strip():
        print("FAIL")
        print("- missing_toolset_section")
        return 2

    # collect backticked tokens
    toks = re.findall(r"`([a-zA-Z0-9_\-]+)`", block)
    # only consider ones that look like tool names
    candidates = [t for t in toks if re.match(r"^[a-z_][a-z0-9_]*$", t)]

    bad = sorted({t for t in candidates if t not in ALLOWED_TOOLS})
    if bad:
        print("FAIL")
        for t in bad:
            print(f"- invented_tool:{t}")
        return 2

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
