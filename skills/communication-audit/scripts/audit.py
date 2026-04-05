#!/usr/bin/env python3
"""
communication-audit — Analyze Igor's message history and generate a communication insight report.
Reads from: ~/.openclaw/workspace/.active-session-log.md
"""
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

SESSION_LOG = Path.home() / ".openclaw/workspace/.active-session-log.md"


def parse_session_log(path: Path) -> list[dict]:
    """Parse the active session log into structured exchanges."""
    if not path.exists():
        return []
    
    content = path.read_text()
    
    # Split into entries by ## headers
    entries = re.split(r"(?=## )", content)
    
    exchanges = []
    for entry in entries:
        lines = entry.strip().split("\n")
        if not entry.strip():
            continue
        
        # Extract timestamp from header
        timestamp = ""
        topic = ""
        igor_msg = ""
        agent_msg = ""
        outcome = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith("## "):
                # Extract date and topic
                rest = line[3:]
                if "]" in rest:
                    ts_part = rest.split("]")[0] + "]"
                    topic = rest.split("]")[1].strip(" —").strip() if "—" in rest else ""
                    timestamp = ts_part
            elif line.startswith("Igor:"):
                igor_msg = line[5:].strip()
            elif line.startswith("Agent:"):
                agent_msg = line[6:].strip()
            elif line.startswith("Outcome:"):
                outcome = line[7:].strip()
        
        if igor_msg or agent_msg:
            exchanges.append({
                "timestamp": timestamp,
                "topic": topic,
                "igor": igor_msg,
                "agent": agent_msg,
                "outcome": outcome,
            })
    
    return exchanges


def score_brief_quality(text: str) -> tuple[int, str]:
    """Score how well-formed a message is. Returns (score, reason)."""
    if not text:
        return 1, "empty message"
    
    score = 5  # baseline
    reasons = []
    
    # Length check
    word_count = len(text.split())
    if word_count < 3:
        score -= 2
        reasons.append("very short")
    elif word_count > 100:
        score -= 1
        reasons.append("overly long")
    elif 5 <= word_count <= 30:
        score += 1
        reasons.append("good length")
    
    # Contains context markers
    if any(marker in text.lower() for marker in ["this", "that", "it", "the"]):
        score -= 1
        reasons.append("uses vague references without context")
    
    # Contains specific constraints
    specific_markers = [
        "exactly", "only", "just", "no", "don't", "make sure",
        "specifically", "must", "should be", "needs to"
    ]
    if any(marker in text.lower() for marker in specific_markers):
        score += 1
        reasons.append("has specific constraints")
    
    # Is a question vs command
    is_question = "?" in text
    is_command = any(text.lower().startswith(w) for w in ["do", "make", "create", "check", "fix", "tell", "show", "give", "what", "how", "why", "can you", "please"])
    
    if is_question or is_command:
        score += 1
        reasons.append("clear request type")
    
    # Contains format/medium specifier
    if any(word in text.lower() for word in ["prompt", "script", "list", "summary", "video", "email", "message", "write"]):
        score += 1
        reasons.append("specifies output format")
    
    score = max(1, min(10, score))
    reason = "; ".join(reasons) if reasons else "neutral"
    return score, reason


def score_ask_clarity(text: str) -> tuple[int, str]:
    """Score how specific and focused a request is. Returns (score, reason)."""
    if not text:
        return 1, "empty"
    
    score = 5
    reasons = []
    
    # Count question marks or command structure
    questions = text.count("?")
    commands = text.count(".")
    
    # Multiple asks bundled together
    command_verbs = ["and", "also", "plus", "then", "after that"]
    ask_count = sum(1 for v in command_verbs if v in text.lower())
    if ask_count >= 2:
        score -= 2
        reasons.append("multiple asks bundled")
    elif ask_count == 1:
        score -= 1
        reasons.append("slightly bundled")
    
    # Single clear ask
    if questions == 1 and ask_count == 0:
        score += 2
        reasons.append("single focused question")
    elif "?" not in text and ask_count == 0 and len(text.split()) < 20:
        score += 1
        reasons.append("short focused command")
    
    # Vague words that dilute the ask
    vague = ["something", "stuff", "things", "whatever", "it", "that thing", "sort of"]
    vague_count = sum(1 for v in vague if v in text.lower())
    if vague_count >= 2:
        score -= 2
        reasons.append(f"vague references ({vague_count}x)")
    elif vague_count == 1:
        score -= 1
        reasons.append("one vague reference")
    
    score = max(1, min(10, score))
    reason = "; ".join(reasons) if reasons else "neutral"
    return score, reason


def detect_low_alignment_patterns(exchanges: list[dict]) -> list[dict]:
    """Find exchanges where communication caused rework or confusion."""
    patterns = []
    
    low_alignment_indicators = [
        "fix", "again", "wrong", "not what", "that's not", "retry",
        "re-do", "rebuild", "different", "other option", "try again",
        "skip it", "not that", "confused", "unclear"
    ]
    
    vague_requests = [
        "do it", "do something", "handle it", "figure it out",
        "make it better", "improve it", "fix it", "check it"
    ]
    
    for ex in exchanges:
        igor = ex.get("igor", "")
        agent = ex.get("agent", "")
        outcome = ex.get("outcome", "")
        
        if not igor:
            continue
        
        igor_lower = igor.lower()
        
        # Check for low-alignment indicators
        has_low_indicator = any(ind in igor_lower for ind in low_alignment_indicators)
        
        # Check for vague requests
        is_vague = any(vr in igor_lower for vr in vague_requests)
        
        if has_low_indicator or is_vague:
            patterns.append({
                "igor": igor[:100],
                "topic": ex.get("topic", ""),
                "type": "vague_request" if is_vague else "rewind",
                "score": 3 if is_vague else 5,
                "reason": "vague — no specifics" if is_vague else "needed correction/rewind",
            })
    
    return patterns


def detect_high_alignment_patterns(exchanges: list[dict]) -> list[dict]:
    """Find exchanges where communication led to clean output."""
    patterns = []
    
    high_quality_markers = [
        "prompt", "video", "check", "give me", "I need", "create",
        "write", "build", "generate", "show", "list"
    ]
    
    for ex in exchanges:
        igor = ex.get("igor", "")
        topic = ex.get("topic", "")
        outcome = ex.get("outcome", "")
        
        if not igor:
            continue
        
        igor_lower = igor.lower()
        
        # Has format specifier + specific constraint
        has_format = any(m in igor_lower for m in high_quality_markers)
        has_constraint = any(c in igor_lower for c in ["exactly", "only", "just", "no ", "don't", "specifically"])
        is_short = len(igor.split()) < 15
        no_vague = not any(v in igor_lower for v in ["something", "stuff", "it", "that thing"])
        
        if has_format and has_constraint and is_short and no_vague:
            patterns.append({
                "igor": igor[:100],
                "topic": topic,
                "type": "clean_brief",
                "score": 9,
                "reason": "specific + format + constraint",
            })
    
    return patterns


def generate_report() -> dict:
    """Build the full audit report."""
    exchanges = parse_session_log(SESSION_LOG)
    
    # Score all igor messages
    brief_scores = []
    ask_scores = []
    
    for ex in exchanges:
        igor = ex.get("igor", "")
        if igor:
            b_score, _ = score_brief_quality(igor)
            a_score, _ = score_ask_clarity(igor)
            brief_scores.append(b_score)
            ask_scores.append(a_score)
    
    avg_brief = round(sum(brief_scores) / len(brief_scores), 1) if brief_scores else 0
    avg_ask = round(sum(ask_scores) / len(ask_scores), 1) if ask_scores else 0
    
    # Overall clarity = average of brief + ask
    overall = round((avg_brief + avg_ask) / 2, 1) if (brief_scores and ask_scores) else 0
    
    # Find best and worst exchanges
    high_align = detect_high_alignment_patterns(exchanges)
    low_align = detect_low_alignment_patterns(exchanges)
    
    # Sort by score
    high_align.sort(key=lambda x: x["score"], reverse=True)
    low_align.sort(key=lambda x: x["score"])
    
    return {
        "exchanges_analyzed": len(exchanges),
        "avg_brief_quality": avg_brief,
        "avg_ask_clarity": avg_ask,
        "overall_clarity": overall,
        "best_exchanges": high_align[:3],
        "needs_work_exchanges": low_align[:3],
    }


if __name__ == "__main__":
    report = generate_report()
    import json
    print(json.dumps(report, indent=2))
