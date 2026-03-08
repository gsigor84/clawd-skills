---
name: ddg-search
description: Search the web using DuckDuckGo. Use when you need current information, news, market data, competitor research, or any real-time web search. No API key required.
---

## DuckDuckGo Web Search

Search the web using the locally installed duckduckgo-search Python package.

### How to search:
```
python3 -c "
from duckduckgo_search import DDGS
results = DDGS().text('YOUR QUERY HERE', max_results=8)
for r in results:
    print(r['title'])
    print(r['href'])
    print(r['body'])
    print('---')
"
```

### For news specifically:
```
python3 -c "
from duckduckgo_search import DDGS
results = DDGS().news('YOUR QUERY HERE', max_results=8)
for r in results:
    print(r['title'])
    print(r['date'])
    print(r['url'])
    print(r['body'])
    print('---')
"
```

Always run searches via exec tool using python3 with the duckduckgo_search package.
