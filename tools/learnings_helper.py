#!/opt/anaconda3/bin/python3
"""Shared helpers for writing structured learnings/errors entries.

This module centralises the ERR entry update/append logic used by automation
scripts so they can:
- de-duplicate recurring issues via Pattern-Key
- increment Recurrence-Count
- update Last-Seen
- avoid logging secrets or large payloads

Primary consumer: automation scripts under /Users/igorsilva/clawd/skills/**/scripts/

Log file:
- /Users/igorsilva/clawd/.learnings/ERRORS.md

Entry fields written are aligned to tools/promote_learnings.py expectations:
- Pattern-Key
- Recurrence-Count
- First-Seen
- Last-Seen
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

LEARNINGS_ERRORS_PATH = Path("/Users/igorsilva/clawd/.learnings/ERRORS.md")


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_today() -> str:
    d = dt.datetime.now(dt.timezone.utc).date()
    return d.isoformat()


def next_err_id(existing_text: str) -> str:
    ymd = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    ids = re.findall(rf"\bERR-{ymd}-(\d{{3}})\b", existing_text)
    n = (max([int(x) for x in ids]) + 1) if ids else 1
    return f"ERR-{ymd}-{n:03d}"


def update_or_append_err(
    *,
    pattern_key: str,
    summary: str,
    error_lines: list[str],
    context_lines: list[str],
    suggested_fix_lines: list[str],
    priority: str = "high",
    area: str = "infra",
    stage: str = "notebooklm-fetcher",
) -> None:
    """Write a structured ERR entry to ~/clawd/.learnings/ERRORS.md.

    If an entry with the same Pattern-Key exists, increment Recurrence-Count
    and update Last-Seen instead of creating a duplicate.

    Notes:
    - Keep inputs small. Do not pass secrets/tokens or large payloads.
    - stage is used for the markdown header label only.
    """

    LEARNINGS_ERRORS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = ""
    if LEARNINGS_ERRORS_PATH.exists():
        existing = LEARNINGS_ERRORS_PATH.read_text(encoding="utf-8", errors="ignore")
    else:
        existing = "# Errors Log\n\n---\n\n"

    today = utc_today()

    # Try to find existing block containing Pattern-Key.
    key_pat = re.compile(rf"^\s*-\s*Pattern-Key:\s*{re.escape(pattern_key)}\s*$", re.M)
    m = key_pat.search(existing)
    if m:
        # Update the nearest preceding '## [' header block by scanning outward.
        start = existing.rfind("## [", 0, m.start())
        end = existing.find("\n---\n", m.end())
        if start == -1:
            start = 0
        if end == -1:
            end = len(existing)
        block = existing[start:end]

        # Update recurrence count
        rc_re = re.compile(r"^\s*-\s*Recurrence-Count:\s*(\d+)\s*$", re.M)
        rc_m = rc_re.search(block)
        if rc_m:
            rc = int(rc_m.group(1)) + 1
            block2 = rc_re.sub(f"- Recurrence-Count: {rc}", block, count=1)
        else:
            # Insert after Pattern-Key line if missing
            block2 = re.sub(
                rf"(^\s*-\s*Pattern-Key:\s*{re.escape(pattern_key)}\s*$)",
                rf"\1\n- Recurrence-Count: 2",
                block,
                flags=re.M,
                count=1,
            )

        # Update Last-Seen
        ls_re = re.compile(r"^\s*-\s*Last-Seen:\s*(\d{4}-\d{2}-\d{2})\s*$", re.M)
        if ls_re.search(block2):
            block3 = ls_re.sub(f"- Last-Seen: {today}", block2, count=1)
        else:
            block3 = block2 + f"\n- Last-Seen: {today}\n"

        LEARNINGS_ERRORS_PATH.write_text(existing[:start] + block3 + existing[end:], encoding="utf-8")
        return

    # Append new entry
    err_id = next_err_id(existing)
    entry = [
        f"## [{err_id}] {stage}",
        "",
        f"**Logged**: {utc_now_iso()}",
        f"**Priority**: {priority}",
        "**Status**: pending",
        f"**Area**: {area}",
        "",
        "### Summary",
        summary.strip(),
        "",
        "### Error",
        *[f"- {ln}" for ln in error_lines if ln.strip()],
        "",
        "### Context",
        *[f"- {ln}" for ln in context_lines if ln.strip()],
        "",
        "### Suggested Fix",
        *[f"- {ln}" for ln in suggested_fix_lines if ln.strip()],
        "",
        "### Metadata",
        "- Source: error",
        "- Tags: automation",
        f"- Pattern-Key: {pattern_key}",
        "- Recurrence-Count: 1",
        f"- First-Seen: {today}",
        f"- Last-Seen: {today}",
        "",
        "---",
        "",
    ]
    LEARNINGS_ERRORS_PATH.write_text(existing + "\n".join(entry), encoding="utf-8")
