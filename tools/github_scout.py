#!/opt/anaconda3/bin/python3
"""github_scout.py

Lightweight GitHub discovery helper.

Goal: return up to N candidate repos with a simple heuristic score.

This is intentionally simple and deterministic: it does not attempt to be a
full recommender.

Output:
- default: human-readable lines
- --json: machine-readable

Notes:
- Uses GitHub Search API for repositories.
- Requires either env var GITHUB_TOKEN or --github-token.

Example:
  /opt/anaconda3/bin/python3 ~/clawd/tools/github_scout.py --limit 5
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import urllib.request


def _http_json(url: str, headers: Dict[str, str]) -> Any:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8", errors="replace")
    return json.loads(data)


def _score_repo(item: Dict[str, Any]) -> Tuple[int, str]:
    """Return (score, reason). Score is 0-10."""
    full_name = (item.get("full_name") or "").lower()
    desc = (item.get("description") or "").lower()
    topics = [t.lower() for t in (item.get("topics") or [])]
    stars = int(item.get("stargazers_count") or 0)
    updated_at = item.get("updated_at") or ""

    text = " ".join([full_name, desc, " ".join(topics)])

    score = 0

    # Relevance keywords (agents + automation)
    if re.search(r"\b(agent|agents|autonomous|orchestrat|workflow|scheduler|cron)\b", text):
        score += 3
    if re.search(r"\b(mcp|openclaw|claude code|codex|openai|llm|rag)\b", text):
        score += 2
    if re.search(r"\b(tmux|worktree|git worktree|cli)\b", text):
        score += 1

    # Stars
    if stars >= 50000:
        score += 3
    elif stars >= 10000:
        score += 2
    elif stars >= 2000:
        score += 1

    # Recently updated (rough)
    try:
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - dt).days
        if age_days <= 30:
            score += 1
        if age_days <= 7:
            score += 1
    except Exception:
        pass

    if score > 10:
        score = 10

    # Reason (one sentence)
    reason_bits = []
    if any(k in text for k in ["agent", "orchestr", "workflow", "mcp", "llm"]):
        reason_bits.append("agent/workflow relevant")
    if stars >= 2000:
        reason_bits.append(f"{stars}⭐")
    if "openclaw" in text:
        reason_bits.append("mentions OpenClaw")

    reason = ", ".join(reason_bits) if reason_bits else "potentially relevant"
    return score, reason


def main() -> int:
    ap = argparse.ArgumentParser(description="Discover GitHub repos (scored)")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN", ""))
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--query",
        default=(
            "(agent OR agents OR orchestration OR workflow OR mcp) "
            "language:Python stars:>200 pushed:>2025-01-01"
        ),
        help="GitHub search query (GitHub Search API syntax)",
    )

    args = ap.parse_args()

    if not args.github_token:
        print("ERROR: missing GitHub token. Set GITHUB_TOKEN or pass --github-token.")
        return 2

    url = (
        "https://api.github.com/search/repositories?sort=stars&order=desc&per_page=30&q="
        + urllib.request.quote(args.query)
    )

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {args.github_token}",
        "User-Agent": "clawd-github-scout",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    data = _http_json(url, headers=headers)
    items = data.get("items") or []

    scored: List[Dict[str, Any]] = []
    for item in items:
        score, reason = _score_repo(item)
        scored.append(
            {
                "score": score,
                "full_name": item.get("full_name"),
                "html_url": item.get("html_url"),
                "stars": int(item.get("stargazers_count") or 0),
                "description": item.get("description") or "",
                "reason": reason,
            }
        )

    scored.sort(key=lambda x: (x["score"], x["stars"]), reverse=True)
    top = scored[: max(0, args.limit)]

    if args.json:
        print(json.dumps({"results": top}, indent=2))
    else:
        for r in top:
            print(
                f"[{r['score']}] {r['full_name']} (⭐{r['stars']}) — {r['reason']}\n{r['html_url']}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
