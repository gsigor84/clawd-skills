#!/opt/anaconda3/bin/python3
"""Promotion proposal scanner for ~/.learnings.

Scans .learnings/*.md for entries with:
- Pattern-Key
- Recurrence-Count
- Last-Seen

If Recurrence-Count >= 3 and Last-Seen is within the last 30 days,
prints a proposal to promote a 1–2 line rule to AGENTS.md or SOUL.md.

This script is proposals-only: it does not write any files.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

ROOT = Path("/Users/igorsilva/clawd")
LEARN_DIR = ROOT / ".learnings"
FILES = [
    LEARN_DIR / "LEARNINGS.md",
    LEARN_DIR / "ERRORS.md",
    LEARN_DIR / "FEATURE_REQUESTS.md",
]

RE_PATTERN_KEY = re.compile(r"^\s*-\s*Pattern-Key:\s*(?P<key>[^\n]+)\s*$", re.M)
RE_RECURRENCE = re.compile(r"^\s*-\s*Recurrence-Count:\s*(?P<n>\d+)\s*$", re.M)
RE_LAST_SEEN = re.compile(r"^\s*-\s*Last-Seen:\s*(?P<d>\d{4}-\d{2}-\d{2})\s*$", re.M)
RE_FIRST_SEEN = re.compile(r"^\s*-\s*First-Seen:\s*(?P<d>\d{4}-\d{2}-\d{2})\s*$", re.M)
RE_SUMMARY = re.compile(r"^### Summary\s*\n(?P<s>[^\n]+)", re.M)


@dataclass
class Candidate:
    pattern_key: str
    recurrence: int
    last_seen: datetime
    first_seen: Optional[datetime]
    summary: str
    source_file: Path


def parse_date(s: str) -> datetime:
    return datetime.strptime(s.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)


def split_entries(text: str) -> Iterable[str]:
    # Entries are typically separated by a line containing only '---'
    # Keep it forgiving: split on '\n---\n'.
    parts = text.split("\n---\n")
    for p in parts:
        if "Pattern-Key:" in p and "Recurrence-Count:" in p:
            yield p


def recommend_target(summary: str, pattern_key: str) -> str:
    s = (summary + " " + pattern_key).lower()

    # Workflow / coordination / pipeline reliability → AGENTS
    if any(k in s for k in ["workflow", "pipeline", "hook", "automation", "stop downstream", "fail hard", "hard-fail", "orchestrator"]):
        return "AGENTS.md"

    # Behaviour / communication / mode switching → SOUL
    if any(k in s for k in ["tone", "communication", "ask one question", "clinical", "creative", "no guessing", "discipline"]):
        return "SOUL.md"

    # Default: AGENTS, since most Pattern-Keys here are operational.
    return "AGENTS.md"


def main() -> int:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)

    candidates: list[Candidate] = []

    for f in FILES:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for entry in split_entries(text):
            m_key = RE_PATTERN_KEY.search(entry)
            m_rec = RE_RECURRENCE.search(entry)
            m_last = RE_LAST_SEEN.search(entry)
            if not (m_key and m_rec and m_last):
                continue

            key = m_key.group("key").strip()
            rec = int(m_rec.group("n"))
            last = parse_date(m_last.group("d"))

            m_first = RE_FIRST_SEEN.search(entry)
            first = parse_date(m_first.group("d")) if m_first else None

            m_sum = RE_SUMMARY.search(entry)
            summary = m_sum.group("s").strip() if m_sum else "(no summary)"

            candidates.append(Candidate(key, rec, last, first, summary, f))

    promotable = [c for c in candidates if c.recurrence >= 3 and c.last_seen >= cutoff]
    promotable.sort(key=lambda c: (-c.recurrence, c.pattern_key))

    print("PROMOTION PROPOSALS")
    print(f"cutoff: {cutoff.date().isoformat()} (last 30 days)")

    if not promotable:
        print("(none)")
        return 0

    for c in promotable:
        target = recommend_target(c.summary, c.pattern_key)
        print(f"- {c.pattern_key} | rec={c.recurrence} | last_seen={c.last_seen.date().isoformat()} | target={target}")
        print(f"  summary: {c.summary}")
        print(f"  source: {c.source_file}")
        print("  next: promote a 1–2 line prevention rule; then set Status: promoted and add Promoted: <target> in the entry")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
