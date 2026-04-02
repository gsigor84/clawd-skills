# gsigor84/clawd-skills — Bootstrap Guide

This repo contains Igor Silvas personal AI agent skill stack for OpenClaw + Claude Code.

## Quick Restore After Reinstall

### 1. Reinstall OpenClaw
```bash
npm install -g openclaw
openclaw configure  # or restore ~/.openclaw/openclaw.json from backup
```

### 2. Restore GitHub token
```bash
mkdir -p ~/.config/openclaw
# Restore from backup (the token is NOT in this repo)
echo '{"token": "ghp_YOUR_TOKEN", "user": "gsigor84"}' > ~/.config/openclaw/github.json
chmod 600 ~/.config/openclaw/github.json
gh auth login --with-token <your_token
```

### 3. Clone skills
```bash
git clone https://github.com/gsigor84/clawd-skills ~/clawd
```

### 4. Restore Omega Memory
```bash
pip install omega-memory
omega setup --download-model
```

### 5. Recreate cron jobs
See `docs/cron-jobs.md` for the full list of cron jobs with their schedules and payloads.

---

## Skills Installed

| Skill | Purpose |
|-------|---------|
| `marketing-knowledge/` | Marketing strategy from NotebookLM research |
| `video-pipeline/` | Strategy → concept → video prompt chain |
| `omega-memory/` | Persistent session memory |
| `prompt-engineer/` | Text + video prompt design |
| `creativity-toolkit/` | Marketing asset generation |
| `notebooklm-runner/` | NotebookLM fetcher + runner |
| `notebooklm-fetcher/` | Self-healing NotebookLM clipboard fetcher |
| `skill-forge/` | Build new skills from research |
| `skillmd-builder-agent/` | Skill validation + building |
| `self-improving-skill-builder/` | Skill improvement pipeline |
| `blogwatcher/` | Daily blog monitoring |
| `github-monitor/` | GitHub release monitoring |

---

## Tools

| Tool | Purpose |
|------|---------|
| `skill_forge_state.py` | Canonical run-state layer for skill-forge |
| `run_skill_judge.py` | Isolated judge path with infra-fail classification |
| `get_current_parasha.py` | Weekly parasha lookup |
| `summarize_journals.py` | Adam journal synthesis |
| `github_scout.py` | GitHub repo scout |

---

## Cron Jobs (see cron-jobs.md for full details)

| Job | Schedule | Purpose |
|-----|----------|---------|
| `github-monitor-morning` | 8am daily | GitHub releases → WhatsApp |
| `Morning briefing` | 9am daily | Blogwatcher + GitHub → WhatsApp |
| `wondering-observe` | every 3hrs | Pattern scoring + alerts |
| `philosophic-filter-friday` | Fri 3pm | Weekly parasha filter |
| `adam-journal-synthesis` | Mon 9am | Journal summary |

---

## Config Files NOT in This Repo

These must be backed up separately and restored after reinstall:

- `~/.openclaw/openclaw.json` — OpenClaw main config (gateway token, auth, tools, channels)
- `~/.config/openclaw/github.json` — GitHub personal access token
- `OPENCLAW_GATEWAY_TOKEN` env var — gateway authentication

---

## Omega Memory

Installed via: `pip install omega-memory && omega setup --download-model`

MCP server registered with Claude Code. Stores memories in `~/.omega/omega.db`.

Commands:
- `omega store <text>` — store a memory
- `omega query <text>` — recall by meaning
- `omega timeline` — show all memories
- `omega consolidate` — prune stale memories
- `omega welcome` — session briefing with recent memories

---

## Workspace Files

These live in `~/clawd/` and are tracked in git:
- `MEMORY.md` — agent memory and context
- `SOUL.md` — agent persona and behavior
- `AGENTS.md` — agent instructions
- `HEARTBEAT.md` — periodic task definitions
- `USER.md` — user profile and preferences
- `IDENTITY.md` — agent identity
- `PHILOSOPHY.md` — philosophical framework
