#!/usr/bin/env python3
"""
report.py — Format audit results into a readable communication insights report.
"""
import json
import sys
from datetime import datetime

SESSION_LOG = __import__('pathlib').Path.home() / ".openclaw/workspace/.active-session-log.md"


def load_raw_messages() -> list[dict]:
    """Load raw messages from the session log for pattern analysis."""
    import re
    path = SESSION_LOG
    if not path.exists():
        return []
    
    content = path.read_text()
    entries = re.split(r"(?=## )", content)
    
    exchanges = []
    for entry in entries:
        lines = entry.strip().split("\n")
        if not entry.strip():
            continue
        
        timestamp = ""
        topic = ""
        igor = ""
        outcome = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith("## "):
                rest = line[3:]
                if "]" in rest:
                    ts_part = rest.split("]")[0] + "]"
                    topic = rest.split("]")[1].strip(" —").strip() if "—" in rest else ""
                    timestamp = ts_part
            elif line.startswith("Igor:"):
                igor = line[5:].strip()
            elif line.startswith("Outcome:"):
                outcome = line[7:].strip()
        
        if igor:
            exchanges.append({
                "timestamp": timestamp,
                "topic": topic,
                "igor": igor,
                "outcome": outcome,
            })
    
    return exchanges


def score_brief(text: str) -> tuple[int, str]:
    """Score brief quality."""
    if not text:
        return 1, "empty"
    score = 5
    reasons = []
    
    words = text.split()
    wc = len(words)
    
    if wc < 3:
        score -= 2
        reasons.append("very short")
    elif wc > 80:
        score -= 1
        reasons.append("overly long")
    elif 5 <= wc <= 25:
        score += 1
        reasons.append("good length")
    
    vague = ["something", "stuff", "things", "it", "that", "this", "whatever"]
    vague_count = sum(1 for v in vague if v in text.lower())
    if vague_count >= 3:
        score -= 2
        reasons.append("many vague refs")
    elif vague_count >= 1:
        score -= 1
        reasons.append("vague refs")
    
    if any(c in text.lower() for c in ["exactly", "only", "just", "don't", "specifically", "must"]):
        score += 1
        reasons.append("has constraints")
    
    if any(f in text.lower() for f in ["prompt", "video", "script", "list", "message", "write", "create"]):
        score += 1
        reasons.append("specifies format")
    
    score = max(1, min(10, score))
    return score, "; ".join(reasons) if reasons else "neutral"


def score_clarity(text: str) -> tuple[int, str]:
    """Score ask clarity."""
    if not text:
        return 1, "empty"
    score = 5
    reasons = []
    
    question_marks = text.count("?")
    
    if question_marks == 1:
        score += 2
        reasons.append("single question")
    elif question_marks > 2:
        score -= 1
        reasons.append("multiple questions")
    
    if any(text.lower().startswith(w) for w in ["do", "make", "create", "check", "fix", "give"]):
        score += 1
        reasons.append("clear command")
    
    vague_commands = ["do it", "handle it", "fix it", "make it", "improve it", "something"]
    if any(vc in text.lower() for vc in vague_commands):
        score -= 3
        reasons.append("vague command")
    
    score = max(1, min(10, score))
    return score, "; ".join(reasons) if reasons else "neutral"


def format_report(data: dict) -> str:
    """Format the audit data into a readable report."""
    lines = []
    lines.append("=== COMMUNICATION INSIGHTS ===")
    lines.append("")
    
    # Scores
    lines.append("SCORES:")
    lines.append(f"  Brief quality:   {data['avg_brief']}/10")
    lines.append(f"  Ask clarity:     {data['avg_ask']}/10")
    lines.append(f"  Overall:         {data['overall']}/10")
    lines.append("")
    
    # What's working
    lines.append("WHAT'S WORKING:")
    if data.get("best_exchanges"):
        for ex in data["best_exchanges"]:
            lines.append(f"  • \"{ex['igor'][:60]}\"")
            lines.append(f"    → Score: {ex['score']}/10 ({ex['reason']})")
    else:
        lines.append("  (not enough data yet — keep communicating!)")
    lines.append("")
    
    # Needs work
    lines.append("COULD IMPROVE:")
    if data.get("needs_work"):
        for ex in data["needs_work"]:
            lines.append(f"  • \"{ex['igor'][:60]}\"")
            lines.append(f"    → {ex['reason']}")
    else:
        lines.append("  (no problematic patterns detected yet)")
    lines.append("")
    
    # Key pattern
    if data.get("key_pattern"):
        lines.append("PATTERN:")
        lines.append(f"  {data['key_pattern']}")
        lines.append("")
    
    # Focus
    if data.get("focus"):
        lines.append("THIS WEEK'S FOCUS:")
        lines.append(f"  {data['focus']}")
        lines.append("")
    
    return "\n".join(lines)


def run() -> str:
    """Run the full audit and return formatted report."""
    exchanges = load_raw_messages()
    
    brief_scores = []
    ask_scores = []
    best = []
    needs_work = []
    
    vague_commands = ["do it", "handle it", "fix it", "make it", "improve it", "something", "check something"]
    
    for ex in exchanges:
        igor = ex.get("igor", "")
        if not igor:
            continue
        
        b_score, b_reason = score_brief(igor)
        a_score, a_reason = score_clarity(igor)
        brief_scores.append(b_score)
        ask_scores.append(a_score)
        
        # Low clarity = needs work
        if a_score <= 4 or any(vc in igor.lower() for vc in vague_commands):
            needs_work.append({
                "igor": igor[:80],
                "topic": ex.get("topic", ""),
                "score": a_score,
                "reason": a_reason,
            })
        
        # High clarity + good brief = best
        if b_score >= 7 and a_score >= 7:
            best.append({
                "igor": igor[:80],
                "topic": ex.get("topic", ""),
                "score": (b_score + a_score) // 2,
                "reason": b_reason + "; " + a_reason,
            })
    
    avg_brief = round(sum(brief_scores)/len(brief_scores), 1) if brief_scores else 0
    avg_ask = round(sum(ask_scores)/len(ask_scores), 1) if ask_scores else 0
    overall = round((avg_brief + avg_ask) / 2, 1) if brief_scores else 0
    
    # Generate key pattern
    key_pattern = None
    if avg_brief < 6:
        key_pattern = "Adding more context and constraints to requests → fewer revisions"
    elif avg_ask < 6:
        key_pattern = "Phrasing requests as single specific questions → better first-shot outputs"
    
    # Generate focus
    focus = None
    if avg_ask < avg_brief:
        focus = "Work on ask clarity — one clear request at a time"
    elif avg_brief < avg_ask:
        focus = "Work on brief quality — add format/constraint details"
    else:
        focus = "Both dimensions balanced — keep refining specifics"
    
    data = {
        "avg_brief": avg_brief,
        "avg_ask": avg_ask,
        "overall": overall,
        "best_exchanges": sorted(best, key=lambda x: x["score"], reverse=True)[:3],
        "needs_work": sorted(needs_work, key=lambda x: x["score"])[:3],
        "key_pattern": key_pattern,
        "focus": focus,
    }
    
    return format_report(data)


if __name__ == "__main__":
    print(run())
