## [LRN-20260302-001] best_practice

**Logged**: 2026-03-02T23:00:00Z
**Priority**: high
**Status**: pending
**Area**: config

### Summary
Use /api/search (vector) instead of /api/search/ask/simple for Open Notebook KB queries

### Details
/api/search/ask/simple consistently times out (>90s) on large book collections.
/api/search with type=vector returns results in <2s and includes real passage matches.

### Suggested Action
Always use vector search endpoint in researcher skill. Only use /ask/simple for short targeted queries.

### Metadata
- Source: conversation
- Related Files: ~/clawd/skills/researcher/SKILL.md
- Tags: open-notebook, performance, timeout

---

## [LRN-20260302-002] knowledge_gap

**Logged**: 2026-03-02T23:00:00Z
**Priority**: high
**Status**: pending
**Area**: config

### Summary
DuckDuckGo search requires /opt/anaconda3/bin/python3, not system python3

### Details
The duckduckgo_search package is installed in Anaconda environment.
Calling python3 directly fails with ModuleNotFoundError.
Must use full path: /opt/anaconda3/bin/python3

### Suggested Action
Always use /opt/anaconda3/bin/python3 for DuckDuckGo searches in exec commands.

### Metadata
- Source: conversation
- Related Files: ~/clawd/skills/researcher/SKILL.md, ~/clawd/skills/ddg-search/SKILL.md
- Tags: duckduckgo, python, path

---

## [LRN-20260303-003] best_practice

**Logged**: 2026-03-03T10:03:00Z
**Priority**: high
**Status**: resolved
**Area**: researcher skill

### Summary
Text search + source fetch is the reliable KB query pattern

### Details
/api/search with type=text returns source IDs and relevance scores instantly.
Then fetch full source with GET /api/sources/source:{id} to get full_text.
This pattern works without OpenAI quota (text search is keyword-based).
Vector search requires OpenAI embeddings (currently quota exceeded).

### Suggested Action
Use type=text for all KB searches until OpenAI quota is restored.
Then optionally add type=vector for semantic matching.

---
