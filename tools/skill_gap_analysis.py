#!/usr/bin/env python3
"""
skill_gap_analysis.py — NetworkX gap analysis for skill-forge research corpus

Reads .response.txt files from pass1/ → builds co-occurrence graph → finds structural gaps
→ generates bridging + transcend questions.

Usage:
    python3 skill_gap_analysis.py --input-dir ~/clawd/tmp/research-to-skill/<skill>/pass1 \
                                 --output-dir ~/clawd/tmp/research-to-skill/<skill>/gaps
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import networkx as nx

# ── Stopwords ────────────────────────────────────────────────────────────────

STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of",
    "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "s", "t", "can",
    "will", "just", "don", "should", "now", "d", "ll", "m", "o", "re", "ve",
    "y", "ain", "aren", "couldn", "didn", "doesn", "hadn", "hasn", "haven",
    "isn", "ma", "mightn", "mustn", "needn", "shan", "shouldn", "wasn",
    "weren", "won", "wouldn",
    "like", "just", "know", "think", "get", "got", "going", "one", "would",
    "could", "also", "even", "really", "want", "need", "use", "used", "using",
    "make", "made", "said", "say", "says", "see", "look", "way", "thing",
    "things", "lot", "many", "much", "well", "back", "still", "take", "come",
    "came", "let", "first", "new", "good", "bad", "big", "small", "right",
    "wrong", "best", "worst", "high", "low", "sure", "maybe", "actually",
    "probably", "definitely", "always", "never", "im", "ive", "id", "youre",
    "theyre", "hes", "shes", "its", "thats", "theres", "whats", "hows",
    "wheres", "whens", "cant", "wont", "dont", "didnt", "isnt", "arent",
    "wasnt", "werent", "hasnt", "havent", "hadnt", "doesnt", "couldnt",
    "wouldnt", "shouldnt", "every", "something", "anything", "nothing",
    "someone", "anyone", "everyone", "already", "though", "although",
}

# ── Keyword extraction ──────────────────────────────────────────────────────

def extract_keywords(text, top_n=60):
    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    words = [w for w in text.split() if len(w) > 4 and w not in STOPWORDS]
    bigrams = []
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i+1]
        if not any(c.isdigit() for c in w1) and not any(c.isdigit() for c in w2):
            bigrams.append(f"{w1}_{w2}")
    unigram_counts = Counter(words)
    bigram_counts = Counter(bigrams)
    combined = dict(unigram_counts)
    for b, c in bigram_counts.items():
        combined[b] = c + combined.get(b, 0)
    return [k for k, v in sorted(combined.items(), key=lambda x: -x[1]) if v >= 2][:top_n]

# ── Graph building ─────────────────────────────────────────────────────────

def build_graph(files, min_degree=2):
    G = nx.Graph()
    keyword_sets = []
    for fp in files:
        text = fp.read_text(encoding="utf-8", errors="ignore")
        keywords = extract_keywords(text)
        keyword_sets.append(set(keywords))
        for kw in keywords:
            G.add_node(kw, count=G.nodes.get(kw, {}).get("count", 0) + 1)
    for kws in keyword_sets:
        kws = list(kws)
        for i in range(len(kws)):
            for j in range(i + 1, len(kws)):
                w1, w2 = kws[i], kws[j]
                if G.has_edge(w1, w2):
                    G[w1][w2]["weight"] += 1
                else:
                    G.add_edge(w1, w2, weight=1)
    for node in list(G.nodes()):
        if G.degree(node) < min_degree:
            G.remove_node(node)
    return G

# ── Gap detection ─────────────────────────────────────────────────────────

def find_gaps(G):
    if G.number_of_nodes() == 0:
        return []
    degree_dict = dict(G.degree())
    try:
        pagerank = nx.pagerank(G)
    except Exception:
        pagerank = {n: 1.0 / G.number_of_nodes() for n in G.nodes()}
    max_degree = max(degree_dict.values()) or 1
    max_pr = max(pagerank.values()) or 1
    gaps = []
    for node in G.nodes():
        d = degree_dict[node]
        pr = pagerank[node]
        gaps.append({
            "keyword": node,
            "degree": d,
            "pagerank": round(pr, 6),
            "count": G.nodes[node].get("count", 1),
        })
    for g in gaps:
        g["degree_norm"] = round(g["degree"] / max_degree, 4)
        g["pagerank_norm"] = round(g["pagerank"] / max_pr, 4)
        g["gap_score"] = round(g["pagerank_norm"] * (1 - g["degree_norm"]) * 100, 4)
    gaps.sort(key=lambda x: x["gap_score"], reverse=True)
    return gaps

# ── Gap question generation ───────────────────────────────────────────────

def generate_gap_questions(gaps, top_n=8):
    """Generate bridging + transcend questions from top gap keywords."""
    questions = []
    for g in gaps[:top_n]:
        kw = g["keyword"].replace("_", " ")
        questions.append(f"- **{kw}** (gap score {g['gap_score']}): How does '{kw}' connect to the core use case? What is missing between '{kw}' and the main workflow?")
    return questions

def generate_bridging_questions(gaps):
    """Generate questions that bridge disconnected topic clusters."""
    if len(gaps) < 4:
        return []
    top = gaps[:4]
    q1 = top[0]["keyword"].replace("_", " ")
    q2 = top[1]["keyword"].replace("_", " ")
    q3 = top[2]["keyword"].replace("_", " ")
    return [
        f"**Bridging Q1**: How would adding '{q1}' to a workflow that currently only covers '{q2}' change its value proposition?",
        f"**Bridging Q2**: What would break if '{q1}' and '{q3}' were tightly coupled in the same workflow?",
    ]

def generate_transcend_questions(gaps):
    """Transcend questions — what is NOT being talked about at all."""
    if len(gaps) < 2:
        return []
    q = gaps[-1]["keyword"].replace("_", " ")
    return [
        f"**Transcend Q**: What assumption in the research would be invalidated if '{q}' became a primary concern?",
        f"**Transcend Q**: Which users are completely underserved because no research covers '{q}'?",
    ]

# ── Output ────────────────────────────────────────────────────────────────

def write_gap_prompts(output_dir, gaps, all_questions):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    bridging = generate_bridging_questions(gaps)
    transcend = generate_transcend_questions(gaps)
    gap_questions = generate_gap_questions(gaps)

    lines = [
        "# Gap Analysis — Skill Forge\n",
        "## Top Structural Gaps (underserved topics)\n",
        *gap_questions, "\n",
        "## Bridging Questions (connect isolated topics)\n",
        *["- " + q for q in bridging], "\n",
        "## Transcend Questions (what is NOT being discussed)\n",
        *["- " + q for q in transcend], "\n",
    ]

    out = output_dir / "gap-prompts.md"
    out.write_text("\n".join(lines))
    print(f"[OK] gap-prompts.md written ({len(gaps)} gaps, {len(bridging)} bridging, {len(transcend)} transcend)")

    # Also write a gap-rules.md for Phase 4 synthesis
    rules = output_dir / "gap-rules.md"
    rules.write_text(
        "# Gap Rules for Synthesis\n"
        "- Prioritize topics with gap_score > 10\n"
        "- Bridging questions reveal integration gaps\n"
        "- Transcend questions reveal coverage gaps\n"
        "- Each gap becomes a requirement in the SKILL.md spec\n"
    )
    print(f"[OK] gap-rules.md written")

    # Write JSON for tools that want structured data
    meta = output_dir / "gap-meta.json"
    meta.write_text(json.dumps({
        "total_gaps": len(gaps),
        "top_gaps": gaps[:10],
        "bridging_questions": bridging,
        "transcend_questions": transcend,
    }, indent=2))
    print(f"[OK] gap-meta.json written")

    return out

# ── Main ─────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="NetworkX gap analysis for skill-forge")
    ap.add_argument("--input-dir", required=True, help="pass1 directory with .response.txt files")
    ap.add_argument("--output-dir", required=True, help="gaps/ output directory")
    ap.add_argument("--top-gaps", type=int, default=8, help="Number of top gaps to report")
    ap.add_argument("--min-degree", type=int, default=3, help="Min degree for graph nodes")
    args = ap.parse_args()

    input_dir = Path(args.input_dir)
    response_files = list(input_dir.glob("*.response.txt"))

    if not response_files:
        print(f"[ERROR] No .response.txt files found in {input_dir}")
        return

    print(f"[INFO] Found {len(response_files)} response files")

    print("[INFO] Building co-occurrence graph...")
    G = build_graph(response_files, min_degree=args.min_degree)
    print(f"[INFO] Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    print("[INFO] Finding structural gaps...")
    gaps = find_gaps(G)

    print(f"\n=== TOP {args.top_gaps} GAP KEYWORDS ===")
    for i, g in enumerate(gaps[:args.top_gaps], 1):
        print(f"  {i:2}. {g['keyword']:<35} score={g['gap_score']:.2f}  degree={g['degree']}")

    write_gap_prompts(args.output_dir, gaps[:args.top_gaps], None)

    print(f"\n[OK] All artifacts written to {args.output_dir}/")

if __name__ == "__main__":
    main()
