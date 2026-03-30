#!/usr/bin/env python3
"""
web_research.py - Search arXiv/OpenAlex for papers and generate research context.

Uses AutoResearchClaw literature clients for robust paper discovery with
circuit breakers, rate limiting, and structured Paper objects.
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

# Add AutoResearchClaw research tools to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESEARCH_DIR = os.path.join(SCRIPT_DIR, "research")
AUTORESEARCH_CLAW = os.path.join(RESEARCH_DIR, "autoresearch_install")
if os.path.exists(AUTORESEARCH_CLAW):
    sys.path.insert(0, AUTORESEARCH_CLAW)

try:
    from researchclaw.literature.arxiv_client import search_arxiv
    from researchclaw.literature.openalex_client import search_openalex
    from researchclaw.literature.models import Paper
    HAS_AUTORESEARCH = True
except ImportError:
    HAS_AUTORESEARCH = False


def search_brave(topic, limit=5):
    """Search Brave API for web results."""
    api_key = os.environ.get("BRAVE_API_KEY")
    if not api_key:
        return []
    
    url = f"https://api.search.brave.com/res/web/v1/search?q={urllib.parse.quote(topic)}&count={limit}"
    headers = {
        "X-Tokens-Account-Email": api_key,
        "Accept": "application/json"
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Brave search error: {e}", file=sys.stderr)
        return []
    
    results = []
    for item in data.get("web", {}).get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "description": item.get("description", "")
        })
    return results


def extract_keywords_from_papers(papers):
    """Extract key concepts from paper titles using keyword frequency."""
    concepts = {}
    for paper in papers[:10]:
        title = paper.title.lower()
        keywords = re.findall(r'\b(AI|agent|autonomous|reinforcement|learning|model|neural|language|transformer|autonomous|proactive|prediction|behavior|user|adaptiv|personal|context|attention|memory|policy|utility)\b', title, re.I)
        for kw in keywords:
            concepts[kw.lower()] = concepts.get(kw.lower(), 0) + 1
    sorted_concepts = sorted(concepts.items(), key=lambda x: -x[1])
    return [k for k, v in sorted_concepts[:8]]


def paper_to_dict(paper):
    """Convert Paper object to dict for JSON serialization."""
    if paper is None:
        return {}
    return {
        "paper_id": getattr(paper, "paper_id", ""),
        "title": getattr(paper, "title", ""),
        "authors": [a.name for a in getattr(paper, "authors", [])],
        "year": getattr(paper, "year", 0),
        "abstract": getattr(paper, "abstract", ""),
        "doi": getattr(paper, "doi", ""),
        "citation_count": getattr(paper, "citation_count", 0),
    }


def generate_context_block(task):
    """Generate structured context block for a task using AutoResearchClaw literature clients."""
    
    if not HAS_AUTORESEARCH:
        return f"# Research Context for: {task}\n\n(No AutoResearchClaw literature clients available)"
    
    # Use AutoResearchClaw's robust clients (with graceful fallback)
    try:
        arxiv_papers = search_arxiv(task, limit=10, sort_by="relevance")
    except Exception as e:
        print(f"arXiv search error (fallback to []): {e}", file=sys.stderr)
        arxiv_papers = []
    
    # Retry with date sort if arXiv rate-limited
    openalex_papers = search_openalex(task, limit=5)
    
    # Brave web search
    web_results = search_brave(task, 5) if os.environ.get("BRAVE_API_KEY") else []
    
    # Extract key concepts
    all_papers = arxiv_papers + openalex_papers
    keywords = extract_keywords_from_papers(all_papers)
    
    lines = []
    lines.append(f"## Research Context for: {task}")
    lines.append("")
    
    # Key concepts
    if keywords:
        lines.append("### Key Concepts")
        for kw in keywords:
            lines.append(f"- {kw}")
        lines.append("")
    
    # Papers from arXiv
    if arxiv_papers:
        lines.append("### arXiv Papers")
        for paper in arxiv_papers[:5]:
            title = paper.title[:70]
            authors = [a.name for a in paper.authors[:3]]
            author_str = ", ".join(authors) if authors else "Unknown"
            year = paper.year
            abstract = paper.abstract[:120] if paper.abstract else ""
            lines.append(f"- **{title}** — {author_str} ({year}): {abstract}...")
        lines.append("")
    
    # Papers from OpenAlex
    if openalex_papers:
        lines.append("### OpenAlex Papers (Most Cited)")
        for paper in openalex_papers[:5]:
            title = paper.title[:70]
            authors = [a.name for a in paper.authors[:3]]
            author_str = ", ".join(authors) if authors else "Unknown"
            year = paper.year
            cited = paper.citation_count or 0
            abstract = paper.abstract[:120] if paper.abstract else ""
            lines.append(f"- **{title}** — {author_str} ({year}, {cited} cites): {abstract}...")
        lines.append("")
    
    # Web facts
    if web_results:
        lines.append("### Web Facts")
        for r in web_results[:3]:
            desc = r.get("description", "")
            if desc:
                lines.append(f"- {desc[:120]}...")
        lines.append("")
    
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Research context generator using AutoResearchClaw")
    parser.add_argument("--context-for", help="Task for context")
    parser.add_argument("--topic", help="Legacy: topic")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    
    task = args.context_for or args.topic or ""
    if not task:
        print("Error: --context-for or --topic required", file=sys.stderr)
        sys.exit(1)
    
    os.makedirs(args.output_dir, exist_ok=True)
    context = generate_context_block(task)
    with open(os.path.join(args.output_dir, "context.md"), "w") as f:
        f.write(context)
    print(f"Written: {args.output_dir}/context.md")
    
    # Also write structured JSON
    if HAS_AUTORESEARCH:
        arxiv_papers = search_arxiv(task, limit=10)
        openalex_papers = search_openalex(task, limit=5)
        structured = {
            "task": task,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "arxiv_count": len(arxiv_papers),
            "openalex_count": len(openalex_papers),
            "arxiv_papers": [paper_to_dict(p) for p in arxiv_papers[:5]],
            "openalex_papers": [paper_to_dict(p) for p in openalex_papers[:5]],
        }
        with open(os.path.join(args.output_dir, "papers.json"), "w") as f:
            json.dump(structured, f, indent=2)
        print(f"Written: {args.output_dir}/papers.json")


if __name__ == "__main__":
    main()