---
name: openai-news-brief
description: Get a quick 5-bullet summary of the latest news about OpenAI (trigger phrase: /openai-news-brief).
---

## OpenAI News Brief

### Trigger
`/openai-news-brief`

### Input
Optional: a time window like "today", "this week", or "last 30 days".

### Steps
1. Search the web for very recent news about OpenAI (using the time window if the user provided one).
2. Pick the most relevant results that look like real news updates.
3. Open those pages and read them.
4. Pull out the key new information.
5. Write a 5-bullet summary in plain English, and include links.

### Tools
- Brave web search
- Web page fetching (curl)

### Implementation (use Adam's stack)
1) Web search:
```bash
curl -s "https://api.search.brave.com/res/v1/web/search?q=OpenAI+latest+news&count=5" \
  -H "Accept: application/json" \
  -H "X-Subscription-Token: BSATauqhG5V6hBQaS2y0_SSNf8i1fVe" | /opt/anaconda3/bin/python3 -c "import sys, json; d=json.load(sys.stdin); 
for r in d.get('web',{}).get('results',[])[:5]:
    print(r.get('title',''))
    print(r.get('url',''))
    print(r.get('description','')[:200])
    print('---')"
```

2) Read top pages (repeat for each URL you choose):
```bash
curl -sL URL | /opt/anaconda3/bin/python3 -c "import sys, re; html=sys.stdin.read();
text=re.sub(r'<[^>]+>', ' ', html);
text=re.sub(r'\s+', ' ', text).strip();
print(text[:5000])"
```

### Output
Return exactly 5 bullet points summarising the newest, most important OpenAI news, followed by a short list of the links you used.

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
   - Run: `/openai-news-brief <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/openai-news-brief <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/openai-news-brief/SKILL.md
```
Expected: `PASS`.
