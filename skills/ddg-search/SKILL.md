---
name: ddg-search
description: Search the web using DuckDuckGo. Includes strong retry, delay, and never crashes on rate limits.
---

## DuckDuckGo Web Search (Robust)

```
/opt/anaconda3/bin/python3 -c "
import time, random
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException

def safe_search(query, max_results=8):
    for attempt in range(3):
        try:
            # Strong delay to reduce detection
            time.sleep(random.uniform(5, 10))

            with DDGS(timeout=20, proxies=None) as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return results or []

        except RatelimitException:
            # Backoff (10s, 20s, 30s)
            wait = 10 * (attempt + 1)
            time.sleep(wait)

    # Never crash → return empty
    return []

results = safe_search('YOUR QUERY HERE')

for r in results:
    print(r.get('title'))
    print(r.get('href'))
    print(r.get('body'))
    print('---')
"
```

## DuckDuckGo News (Robust)

```
/opt/anaconda3/bin/python3 -c "
import time, random
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException

def safe_news(query, max_results=8):
    for attempt in range(3):
        try:
            time.sleep(random.uniform(5, 10))

            with DDGS(timeout=20, proxies=None) as ddgs:
                results = list(ddgs.news(query, max_results=max_results))
                return results or []

        except RatelimitException:
            wait = 10 * (attempt + 1)
            time.sleep(wait)

    return []

results = safe_news('YOUR QUERY HERE')

for r in results:
    print(r.get('title'))
    print(r.get('date'))
    print(r.get('url'))
    print(r.get('body'))
    print('---')
"
```

## Usage Rules

- May return empty if rate-limited  
- Do not spam requests  
- Built for stability, not guaranteed results  

Always run via exec tool using python3 with duckduckgo_search.

## Use

Describe what the skill does and when to use it.

## Inputs

- Describe required inputs.

## Outputs

- Describe outputs and formats.

## Failure modes

- List hard blockers and expected exact error strings when applicable.

## Toolset

- `read`
- `write`
- `edit`
- `exec`

## Acceptance tests

1. **Behavioral: happy path**
   - Run: `/ddg-search <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/ddg-search <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/ddg-search/SKILL.md
```
Expected: `PASS`.
