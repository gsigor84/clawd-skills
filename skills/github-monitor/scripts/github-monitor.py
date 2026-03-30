#!/usr/bin/env /opt/anaconda3/bin/python3
"""
github-monitor: Monitor GitHub repos for releases, filter by semver, score relevance, deduplicate.
"""
import os
import re
import json
import sys
import argparse
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.expanduser("~/clawd/tmp/github-monitor")
STATE_FILE = os.path.join(STATE_DIR, "seen-releases.json")
OUTPUT_DIR = STATE_DIR

os.makedirs(STATE_DIR, exist_ok=True)


def parse_version(tag_name):
    """Extract semver components from tag like v1.2.3 or v2026.3.28"""
    if not tag_name:
        return None
    tag_name = tag_name.strip()
    # Handle v2026.3.28 format (date-based versioning) — treat as major
    if re.match(r'^v?\d{4}\.\d+\.\d+$', tag_name):
        parts = re.findall(r'\d+', tag_name)
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    # Standard semver: v1.2.3
    match = re.match(r'^v?(\d+)\.(\d+)\.(\d+)', tag_name)
    if match:
        return tuple(map(int, match.groups()))
    return None


def version_level(tag_name):
    """Determine level: patch, minor, major based on semver.
    
    OpenClaw date-based (v2026.3.28):
      - v2026.3.0 or v2026.3.28 (no second patch digit) = minor (monthly release)
      - v2026.3.28-beta.1 or v2026.3.28-1 = patch (pre-release/hotfix)
    Standard semver (v1.2.3): major.minor.patch as expected.
    """
    if not tag_name:
        return "unknown"
    
    # Pre-release / hotfix markers
    if any(x in tag_name.lower() for x in ['-beta', '-alpha', '-rc', '-hotfix', '-1', '-2']):
        return "patch"
    
    v = parse_version(tag_name)
    if v is None:
        return "unknown"
    
    major, minor, patch = v
    
    # Date-based versioning: v2026.3.28 (year.month.release)
    if major >= 1000:
        # v2026.3.x where x >= 28 = monthly release (minor equivalent)
        # v2026.3.x where x < 28 = patch/hotfix
        if patch >= 28:
            return "minor"
        return "patch"
    
    # Standard semver: v1.2.3
    if patch == 0 and minor == 0:
        return "major"
    if patch == 0:
        return "minor"
    return "patch"


def relevance_score(release, keywords):
    """Score 0-1 based on keyword presence in release name + body"""
    text = (release.get('name', '') + ' ' + release.get('body', '')).lower()
    if not keywords:
        return 0.5
    score = sum(1 for kw in keywords if kw.lower() in text)
    return min(score / len(keywords), 1.0)


def get_seen():
    """Load previously seen release IDs."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_seen(seen):
    """Save seen release IDs."""
    with open(STATE_FILE, "w") as f:
        json.dump(seen, f, indent=2)


def fetch_releases(owner, repo, token=None):
    """Fetch releases from GitHub API."""
    import urllib.request
    import urllib.error
    
    url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=30"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Adam-GitHub-Monitor/1.0"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} for {owner}/{repo}: {e.reason}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error fetching {owner}/{repo}: {e}", file=sys.stderr)
        return []


def generate_release_id(release):
    """Generate a stable release ID for deduplication."""
    repo = release.get('repo', '')
    tag = release.get('tag_name', '')
    return f"{repo}::{tag}"


def main():
    parser = argparse.ArgumentParser(description='GitHub Release Monitor')
    parser.add_argument('--repos', type=str,
                        default='openclaw/openclaw,microsoft/autogen,crewAI-inc/crewAI,aiming-lab/AutoResearchClaw,Ramsbaby/openclaw-self-healing',
                        help='Comma-separated list of owner/repo')
    parser.add_argument('--github-token', type=str, help='GitHub token')
    parser.add_argument('--min-version', type=str, default='minor',
                        choices=['major', 'minor', 'patch'])
    parser.add_argument('--keywords', type=str,
                        default='agent,llm,ai,openai,anthropic,tool,skill,pipeline,automation,orchestration,browser')
    parser.add_argument('--output-format', type=str, default='briefing',
                        choices=['briefing', 'json'])
    parser.add_argument('--config', type=str, help='Config file path')
    parser.add_argument('--force', action='store_true', help='Ignore seen-releases.json, show all')
    args = parser.parse_args()

    # Load repos from config or CLI
    repos = []
    if args.config and os.path.exists(args.config):
        try:
            import yaml
            with open(args.config) as f:
                cfg = yaml.safe_load(f)
                repos = cfg.get('repos', [])
        except Exception as e:
            print(f"Config error: {e}", file=sys.stderr)

    if not repos:
        repos = [r.strip() for r in args.repos.split(',') if r.strip()]

    if not repos:
        print("No repos specified. Use --repos or --config", file=sys.stderr)
        sys.exit(1)

    keywords = [k.strip() for k in args.keywords.split(',') if k.strip()]
    token = args.github_token or os.environ.get('GITHUB_TOKEN')
    seen = get_seen() if not args.force else {}

    # Fetch and process releases
    all_releases = []
    for repo in repos:
        if '/' not in repo:
            continue
        owner, name = repo.split('/', 1)
        releases = fetch_releases(owner, name, token)

        for r in releases:
            r['repo'] = repo
            vl = version_level(r.get('tag_name', ''))
            r['version_level'] = vl
            r['relevance_score'] = relevance_score(r, keywords)

            # Deduplication
            rid = generate_release_id(r)
            repo_seen = seen.get(repo, [])
            if rid in repo_seen:
                continue
            repo_seen.append(rid)
            seen[repo] = repo_seen

            all_releases.append(r)

    # Save state
    save_seen(seen)

    # Filter by min_version
    level_order = {'patch': 0, 'minor': 1, 'major': 2}
    min_level = level_order.get(args.min_version, 1)
    filtered = [r for r in all_releases if level_order.get(r.get('version_level', 'patch'), 0) >= min_level]

    # Sort: highest relevance first, then newest
    filtered.sort(key=lambda x: (-x.get('relevance_score', 0), x.get('published_at', '')))

    date = datetime.now().strftime("%Y-%m-%d")

    if args.output_format == 'json':
        output = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "repos_checked": len(repos),
            "releases_found": len(filtered),
            "total_fetched": len(all_releases),
            "releases": [{
                "repo": r['repo'],
                "tag_name": r.get('tag_name'),
                "version_level": r.get('version_level'),
                "published_at": r.get('published_at'),
                "html_url": r.get('html_url'),
                "relevance_score": r.get('relevance_score'),
                "summary": (r.get('name') or r.get('tag_name', ''))[:100]
            } for r in filtered]
        }
        print(json.dumps(output, indent=2))
        return

    # Briefing format
    print(f"🔧 GitHub Updates — {date}\n")
    if not filtered:
        print("No new releases matching your criteria.\n")
        return

    print(f"Found {len(filtered)} new release(s) from {len(all_releases)} total fetched\n")
    for r in filtered:
        vl = r.get('version_level', '?')
        stars = {"major": "★★★", "minor": "★★", "patch": "★"}.get(vl, "·")
        repo = r['repo']
        tag = r.get('tag_name', '?')
        title = r.get('name') or tag
        score = r.get('relevance_score', 0)
        url = r.get('html_url', '')

        print(f"[{vl.upper()}] {repo} / {tag} {stars}")
        print(f"  {title}")
        if score > 0:
            print(f"  Score: {score:.1f}/1.0")
        if url:
            print(f"  {url}")
        print()

    # Save releases file
    out_path = os.path.join(OUTPUT_DIR, f"releases-{date}.md")
    with open(out_path, "w") as f:
        f.write(f"# GitHub Releases — {date}\n\n")
        for r in filtered:
            f.write(f"## [{r['repo']}] {r.get('tag_name')} ({r.get('version_level')})\n")
            f.write(f"- Title: {r.get('name') or 'N/A'}\n")
            f.write(f"- Published: {r.get('published_at', 'N/A')}\n")
            f.write(f"- Relevance: {r.get('relevance_score', 0):.2f}\n")
            f.write(f"- URL: {r.get('html_url', 'N/A')}\n\n")
    print(f"Saved: {out_path}")


if __name__ == '__main__':
    main()