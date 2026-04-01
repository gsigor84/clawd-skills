---
name: openclaw-self-healing
description: "4-tier autonomous self-healing system for OpenClaw Gateway (watchdog → healthcheck → Claude recovery → human escalation) plus recovery playbooks."
---

# OpenClaw Self-Healing System

> **"The system that heals itself — or calls for help when it can't."**

A 4-tier autonomous self-healing system for OpenClaw Gateway.

## Use
Run this skill to diagnose and recover from OpenClaw operational failures (gateway health, channel connectivity, and dependent local services like Tandem).

## Architecture

```
Level 1: Watchdog (180s)     → Process monitoring (OpenClaw built-in)
Level 2: Health Check (300s) → HTTP 200 + 3 retries
Level 3: Claude Recovery     → 30min AI-powered diagnosis 🧠
Level 4: Discord Alert       → Human escalation
```

## What's Special (v2.0)

- **World's first** Claude Code as Level 3 emergency doctor
- **Persistent Learning** - Automatic recovery documentation (symptom → cause → solution → prevention)
- **Reasoning Logs** - Explainable AI decision-making process
- **Multi-Channel Alerts** - Discord + Telegram support
- **Metrics Dashboard** - Success rate, recovery time, trending analysis
- Production-tested (verified recovery Feb 5-6, 2026)
- macOS LaunchAgent integration

## Quick Setup

### 1. Install Dependencies

```bash
brew install tmux
npm install -g @anthropic-ai/claude-code
```

### 2. Configure Environment

```bash
# Copy template to OpenClaw config directory
cp .env.example ~/.openclaw/.env

# Edit and add your Discord webhook (optional)
nano ~/.openclaw/.env
```

### 3. Install Scripts

```bash
# Copy scripts
cp scripts/*.sh ~/openclaw/scripts/
chmod +x ~/openclaw/scripts/*.sh

# Install LaunchAgent
cp launchagent/com.openclaw.healthcheck.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.openclaw.healthcheck.plist
```

### 4. Verify

```bash
# Check Health Check is running
launchctl list | grep openclaw.healthcheck

# View logs
tail -f ~/openclaw/memory/healthcheck-$(date +%Y-%m-%d).log
```

## Inputs
- OpenClaw gateway health endpoint (`OPENCLAW_GATEWAY_URL`, default `http://localhost:18789/`)
- Optional Discord webhook (`DISCORD_WEBHOOK_URL`)
- Tandem status endpoint: `http://127.0.0.1:8765/status`

## Outputs
- Healthcheck logs under `~/openclaw/memory/` (healthcheck + emergency recovery)
- Optional human escalation messages (Discord/Telegram/WhatsApp)

## Failure modes
- Gateway unhealthy / non-200: restart gateway; escalate to Claude recovery.
- Dependencies missing: install and re-run checks.
- Tandem status endpoint unhealthy: run Tandem auto-restart sequence.
- Still failing after restart: log error and escalate to WhatsApp.

## Acceptance tests

1. Run `/openclaw-self-healing` with Tandem healthy — expected output: the system reports Tandem status OK (HTTP 200 / valid payload) and takes no restart action.

1b. Run `curl -sSf http://127.0.0.1:8765/status` — expected output: non-empty status payload and exit 0.

2. Negative case (Tandem recovery):
```bash
set -euo pipefail
pkill -f tandem-browser || true
sleep 3
cd ~/clawd/tools/tandem/tandem-browser && npm start &
sleep 10
# Expect this to SUCCEED after restart
curl -sSf http://127.0.0.1:8765/status
```
Expected output: status endpoint returns successfully.

2b. Negative case (verify failure is detected):
```bash
set -euo pipefail
pkill -f tandem-browser || true
sleep 1
# Expect this to FAIL (non-zero) while Tandem is down
curl -sSf http://127.0.0.1:8765/status && exit 1 || echo "expected error"
```
Expected error message: curl fails while Tandem is not running.

3. Structural validators:
```bash
/opt/anaconda3/bin/python3 ~/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py ~/clawd/skills/openclaw-self-healing/SKILL.md
/opt/anaconda3/bin/python3 ~/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py ~/clawd/skills/openclaw-self-healing/SKILL.md
```
Expected output: PASS / PASS.

## Scripts

| Script | Level | Description |
|--------|-------|-------------|
| `gateway-healthcheck.sh` | 2 | HTTP 200 check + 3 retries + escalation |
| `emergency-recovery.sh` | 3 | Claude Code PTY session for AI diagnosis (v1) |
| `emergency-recovery-v2.sh` | 3 | Enhanced with learning + reasoning logs (v2) ⭐ |
| `emergency-recovery-monitor.sh` | 4 | Discord/Telegram notification on failure |
| `metrics-dashboard.sh` | - | Visualize recovery statistics (NEW) |

## Configuration

All settings via environment variables in `~/.openclaw/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_WEBHOOK_URL` | (none) | Discord webhook for alerts |
| `OPENCLAW_GATEWAY_URL` | `http://localhost:18789/` | Gateway health check URL |
| `HEALTH_CHECK_MAX_RETRIES` | `3` | Restart attempts before escalation |
| `EMERGENCY_RECOVERY_TIMEOUT` | `1800` | Claude recovery timeout (30 min) |

## Toolset
- exec
- read
- write

## Gateway duplicate listener check (port 18789)

Every 5 minutes, check if more than one process is listening on port 18789:

```bash
lsof -iTCP:18789 | grep LISTEN | wc -l
```

If count > 1:
1. Kill all listeners: `kill -9` on all PIDs except the most recent
2. Wait 3 seconds
3. Run:
```bash
openclaw gateway restart
```
4. Send WhatsApp:
`⚠️ Gateway duplicate listener detected and fixed — port 18789 restarted`

## Tandem Health Check + Auto-Restart (recovery step)

When Tandem health check fails (`curl http://127.0.0.1:8765/status` errors or returns unexpected data), run this recovery sequence:

1. Kill existing Tandem process:
```bash
pkill -f tandem-browser || true
```

2. Wait 3 seconds:
```bash
sleep 3
```

3. Restart Tandem:
```bash
cd ~/clawd/tools/tandem/tandem-browser && npm start &
```

4. Wait 10 seconds:
```bash
sleep 10
```

5. Check status again:
```bash
curl -s http://127.0.0.1:8765/status
```

6. If still failing:
- Log error details
- Send WhatsApp to `+447533464436`

## Testing

### Test Level 2 (Health Check)

```bash
# Run manually
bash ~/openclaw/scripts/gateway-healthcheck.sh

# Expected output:
# ✅ Gateway healthy
```

### Test Level 3 (Claude Recovery)

```bash
# Inject a config error (backup first!)
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak

# Wait for Health Check to detect and escalate (~8 min)
tail -f ~/openclaw/memory/emergency-recovery-*.log
```

## Links

- **GitHub:** https://github.com/Ramsbaby/openclaw-self-healing
- **Docs:** https://github.com/Ramsbaby/openclaw-self-healing/tree/main/docs

## License

MIT License - do whatever you want with it.

Built by @ramsbaby + Jarvis 🦞
