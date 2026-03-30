# Pipeline Report: github-monitor-v2

**Generated:** 2026-03-29
**Mode:** web-research (fallback from NotebookLM)
**Topic:** GitHub repository monitoring release tracking and relevance filtering for AI developers

---

## Goal

Build an OpenClaw skill that monitors specific GitHub repos for new releases, evaluates their relevance to my AI agent stack, and surfaces only the important ones in my morning briefing — filtering out noise and patch versions.

---

## Pipeline Summary

| Phase | Status | Notes |
|-------|--------|-------|
| 1. Research (Web) | ✅ Complete | Fetched GitHub API docs, release filtering patterns |
| 2. Spec | ✅ Complete | Created SKILL.md with full spec |
| 3. Build | ✅ Complete | SKILL.md generated |
| 4. Validate | ✅ Complete | Structure validated |
| 5. Critic Review | ⚠️ Skipped | No critic skill available in this context |
| 6. Polish | ✅ Complete | Finalized output formats |
| 7. Report | ✅ Complete | This report |

---

## Research Findings

### GitHub Releases API
- `GET /repos/{owner}/{repo}/releases` — list all releases
- `GET /repos/{owner}/{repo}/releases/latest` — latest non-draft
- Authentication: Bearer token with `Accept: application/vnd.github+json`
- Rate limits: 60/hr unauthenticated, 5000/hr authenticated

### Semantic Versioning Filtering
- Major (x.0.0): Breaking changes — always significant
- Minor (1.x.0): New features — usually worth surfacing
- Patch (1.2.x): Bug fixes — often noise, filtered by default

### Relevance Scoring
- Keyword matching in release name + body
- Configurable keywords for AI agent stack
- Ignore patterns for noise filtering

---

## Skill Specification

**Name:** `github-monitor-v2`

**Location:** `~/clawd/skills/github-monitor-v2/SKILL.md`

### Key Features

1. **Configurable Repo List** — Monitor any GitHub repos
2. **Semver Filtering** — Filter by major/minor/patch level
3. **Relevance Scoring** — Keyword-based AI relevance
4. **Morning Briefing** — Formatted output for daily digest
5. **Error Handling** — Rate limits, 404s, network failures

### Inputs
- `repos`: List of "owner/repo" strings
- `github_token`: Optional, falls back to GITHUB_TOKEN env
- `min_version`: "major" | "minor" | "patch" (default: minor)
- `keywords`: Relevance keywords (default: agent, llm, ai, openai, anthropic, tool)
- `ignore_patterns`: Noise patterns (default: chore, deps)
- `output_format`: "briefing" | "json" | "full"

### Outputs
- JSON structured data with relevance scores
- Human-readable morning briefing format

---

## Artifacts

| Artifact | Path |
|----------|------|
| SKILL.md | `~/clawd/skills/github-monitor-v2/SKILL.md` |
| Task State | `~/clawd/tmp/skill-forge/github-monitor-v2/task-state.json` |
| Research Corpus | `~/clawd/tmp/skill-forge/github-monitor-v2/research-corpus.md` |
| Pipeline Report | `~/clawd/tmp/skill-forge/github-monitor-v2/pipeline-report.md` |

---

## Notes

- Built via web-research fallback (no NotebookLM URL provided)
- Research gathered from GitHub API documentation
- Critic review skipped — can be run separately with `/skill-forge --critic github-monitor-v2`
- Skill ready for use with `/github-monitor-v2` command

---

## Next Steps

1. Test skill with real repos: `/github-monitor-v2 --repos "openai/gpt-4,anthropic/claude-code"`
2. Add to morning briefing cron job
3. Optionally configure GitHub token for higher rate limits
