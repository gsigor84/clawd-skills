---
name: github-monitor
description: "Monitor GitHub repositories for new releases, filter by semantic versioning to ignore patch updates, evaluate relevance to AI agent stack, and surface important releases in a morning briefing format."
---

# github-monitor

Monitor GitHub repos for releases, filter noise, surface relevant updates for AI developers.

## Use

Run daily to get a morning briefing of significant GitHub releases for your AI agent stack.

```
/github-monitor --repos "anthropic/claude-code,openai/gpt-agents" --min-version minor
/github-monitor --config ~/github-monitor-config.yaml
```

## Inputs

| Input | Type | Required | Default |
|-------|------|----------|---------|
| `repos` | list[string] | Yes | - |
| `github_token` | string | No | env:GITHUB_TOKEN |
| `min_version` | string | No | "minor" |
| `keywords` | list[string] | No | ["agent", "llm", "ai", "openai", "anthropic", "tool"] |
| `ignore_patterns` | list[string] | No | ["chore", "deps"] |
| `output_format` | string | No | "briefing" |

### Input Details

- **repos**: List of "owner/repo" format strings (e.g., "anthropic/claude-code")
- **github_token**: GitHub personal access token. Falls back to env var GITHUB_TOKEN
- **min_version**: Semantic version level — "major", "minor", or "patch". Only releases at this level or higher are surfaced
- **keywords**: Keywords to score relevance. Release notes containing these score higher
- **ignore_patterns**: Patterns that cause automatic filtering (e.g., "chore update", "deps bump")
- **output_format**: "briefing" (readable), "json" (structured), or "full" (with all details)

## Outputs

### JSON Format
```json
{
  "timestamp": "2026-03-29T08:00:00Z",
  "repos_checked": 5,
  "releases_found": 3,
  "briefing": "...",
  "releases": [
    {
      "repo": "anthropic/claude-code",
      "tag_name": "v1.2.0",
      "version_level": "minor",
      "published_at": "2026-03-28T15:00:00Z",
      "html_url": "https://github.com/...",
      "relevance_score": 0.85,
      "summary": "New tool use API for agents"
    }
  ]
}
```

### Briefing Format
```
📦 GitHub Morning Briefing — March 29, 2026

✓ 3 significant releases found (filtered from 12)

ANTHROPIC/CLAUDE-CODE v1.2.0 [minor] ★
→ New tool use API for agents
→ https://github.com/anthropic/claude-code/releases/tag/v1.2.0

OPENAI/GPT-AGENTS v2.0.0 [major] ★★★
→ GPT Agents SDK 2.0 with improved planning
→ https://github.com/openai/gpt-agents/releases/tag/v2.0.0

---
Filtered: 9 patch releases hidden
```

## Procedure

### Step 1: Load Configuration
```python
# Load repos list from input or config file
repos = inputs.get('repos', [])
github_token = os.environ.get('GITHUB_TOKEN', inputs.get('github_token'))
```

### Step 2: Fetch Releases from GitHub API
```python
# For each repo, call GET /repos/{owner}/{repo}/releases
# Authenticate with Bearer token if provided
# Use ?per_page=30 to get recent releases

headers = {
    "Authorization": f"Bearer {github_token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}
```

### Step 3: Parse Semantic Version
```python
import re

def parse_version(tag_name):
    """Extract semver components from tag like v1.2.3"""
    match = re.match(r'v?(\d+)\.(\d+)\.(\d+)', tag_name)
    if match:
        return tuple(map(int, match.groups()))
    return None

def version_level(old, new):
    """Determine level of version change: patch, minor, major"""
    o = parse_version(old) or (0,0,0)
    n = parse_version(new) or (0,0,0)
    if n[0] > o[0]: return "major"
    if n[1] > o[1]: return "minor"
    return "patch"
```

### Step 4: Filter by Version Level
```python
# Filter releases based on min_version input
min_level = {"patch": 0, "minor": 1, "major": 2}[inputs['min_version']]
levels = {"patch": 0, "minor": 1, "major": 2}

def should_include(release):
    level = levels.get(version_level(previous_tag, release['tag_name']), 0)
    return level >= min_level
```

### Step 5: Score Relevance
```python
def relevance_score(release, keywords):
    """Score 0-1 based on keyword presence in release notes"""
    text = (release.get('name', '') + ' ' + release.get('body', '')).lower()
    score = sum(1 for kw in keywords if kw.lower() in text)
    return min(score / len(keywords), 1.0)
```

### Step 6: Filter Noise Patterns
```python
def is_noise(release, ignore_patterns):
    """Check if release matches ignore patterns"""
    text = (release.get('name', '') + ' ' + release.get('body', '')).lower()
    return any(p.lower() in text for p in ignore_patterns)
```

### Step 7: Format Output
```python
def format_briefing(releases, output_format):
    if output_format == 'json':
        return json.dumps(...)
    elif output_format == 'briefing':
        return render_template(...)
    else:
        return full_details(...)
```

## Failure modes

| Failure | Handling |
|---------|----------|
| Rate limit (403) | Return partial results with warning, include retry-after if available |
| Invalid repo format (404) | Skip repo, log error, continue with others |
| Network failure | Return cached results if available, else return empty with error |
| Empty releases list | Return "No releases found" message |
| No GitHub token | Use unauthenticated (60 req/hr limit), warn user |

### Error Messages
- `RATE_LIMITED`: "GitHub API rate limit reached. Try adding a token."
- `REPO_NOT_FOUND`: "Repository {repo} not found or not accessible."
- `NETWORK_ERROR`: "Failed to connect to GitHub API. Check network."

## Toolset

- `exec`: Run curl requests to GitHub API
- `read`: Read config files for repo lists
- `write`: Write briefing output to file
- `web_fetch`: Optionally fetch full release notes from html_url

## Acceptance tests

1. **Behavioral: happy path**
   - Run: `/github-monitor --repos "openai/gpt-agents,anthropic/claude-code" --output-format json`
   - Expected: Returns JSON with releases array, each having repo, tag_name, relevance_score

2. **Negative case: rate limit error**
   - Run with no token when rate limited
   - Expected: Returns partial results with warning message

3. **Version filtering**
   - Run: `--min-version minor` with patch releases present
   - Expected: Patch releases filtered out of output

4. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/github-monitor/SKILL.md
```
Expected: `PASS`.

## Dependencies

- `requests` library for HTTP calls
- `python-semver` or regex for version parsing
- Optional: `pyyaml` for config file support
