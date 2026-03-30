#!/usr/bin/env /opt/anaconda3/bin/python3
"""
book-scout.py — Find books via OceanOfPDF using Tandem browser automation.

API:
  POST /tabs/open         {"url": "..."}          → open new tab
  POST /tabs/focus        {"tabId": "..."}       → focus tab
  GET  /snapshot?compact=true&X-Tab-Id:<id>        → get page tree
  POST /snapshot/click    {"ref": "@eN"}         → click element
  POST /find              {"by": "text", "value": "..."} → find element

Usage:
  python3 book-scout.py --topic "creative collaboration" --queries 3
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

TANDEM_URL = "http://127.0.0.1:8765"
TOKEN_PATH = os.path.expanduser("~/.tandem/api-token")
OUTPUT_DIR = os.path.expanduser("~/clawd/tmp/book-scout")


def get_token():
    with open(TOKEN_PATH) as f:
        return f.read().strip()


def api_get(path, token, headers_extra=None):
    headers = {"Authorization": f"Bearer {token}"}
    if headers_extra:
        headers.update(headers_extra)
    req = urllib.request.Request(f"{TANDEM_URL}{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def api_post(path, data, token, headers_extra=None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if headers_extra:
        headers.update(headers_extra)
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{TANDEM_URL}{path}", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def focus_tab(token, tab_id):
    api_post("/tabs/focus", {"tabId": tab_id}, token)


def snapshot_tab(token, tab_id, compact=True):
    params = "?compact=true" if compact else ""
    h = {"X-Tab-Id": tab_id} if tab_id else {}
    return api_get(f"/snapshot{params}", token, h)


def open_tab(token, url):
    result = api_post("/tabs/open", {"url": url}, token)
    return result.get("tab", {}).get("id", "")


def click_ref(token, ref):
    return api_post("/snapshot/click", {"ref": ref}, token)


def find_text(token, text):
    return api_post("/find", {"by": "text", "value": text}, token)


def extract_links(snapshot_text):
    """Extract clickable links from accessibility tree."""
    links = re.findall(r'link "([^"]+)" \[@([^\]]+)\]', snapshot_text)
    results = []
    skip = {'skip to', 'oceanofpdf', 'search', 'donate', 'promote', 'request',
            'contact', 'mission', 'home', 'genres', 'authors', 'languages',
            'new releases', 'webnovels', 'magazines', 'listopia', 'thumbnail'}
    for title, ref in links:
        t = title.strip()
        norm = t.lower()
        if len(t) < 15:
            continue
        if any(s in norm for s in skip):
            continue
        # Strip PDF/EPUB markers
        t = re.sub(r'^\[PDF\]\s*\[EPUB\]\s*|\s*\[EPUB\]\s*|\s*\[PDF\]\s*', '', t).strip()
        results.append({"title": t, "ref": f"@{ref}"})
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Book scout via OceanOfPDF + Tandem")
    parser.add_argument("--topic", required=True, help="Search topic")
    parser.add_argument("--queries", type=int, default=3, help="Number of query variations (max 5)")
    args = parser.parse_args()

    topic = args.topic.strip()
    n_queries = min(max(1, args.queries), 5)
    token = get_token()

    # Query variations
    query_templates = [
        "{topic}",
        "{topic} practical guide",
        "{topic} pdf download",
        "{topic} 2024 2025",
        "{topic} with code examples",
    ]
    queries = [q.format(topic=topic) for q in query_templates[:n_queries]]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    seen_titles = {}
    today = date.today().strftime("%Y-%m-%d")

    for q in queries:
        try:
            tab_id = open_tab(token, f"https://oceanofpdf.com/?s={urllib.parse.quote(q)}")
            time.sleep(3)
            focus_tab(token, tab_id)
            time.sleep(1)

            data = snapshot_tab(token, tab_id)
            links = extract_links(data.get("snapshot", ""))

            for item in links:
                norm = item["title"].lower()
                if norm not in seen_titles:
                    seen_titles[norm] = item["title"]

        except Exception as e:
            print(f"Query failed '{q}': {e}", file=sys.stderr)

    # Save results
    out_path = os.path.join(OUTPUT_DIR, f"{re.sub(r'[^a-z0-9]+', '-', topic.lower())}-{today}.md")
    lines = [f"# Book Scout: {topic}", f"Date: {today}", f"Total found: {len(seen_titles)}", "", "## Results", "", "| # | Title |", "|---|-------|"]
    for i, title in enumerate(list(seen_titles.values())[:20], 1):
        lines.append(f"| {i} | {title} |")

    content = "\n".join(lines)
    with open(out_path, "w") as f:
        f.write(content + "\n")

    print(f"BOOK_SCOUT_COMPLETE")
    print(f"TOPIC: {topic}")
    print(f"TOTAL_FOUND: {len(seen_titles)}")
    print(f"OUTPUT: {out_path}")


if __name__ == "__main__":
    main()