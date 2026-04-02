# Cron Jobs — gsigor84/clawd-skills

Recreate these after any OpenClaw reinstall using `openclaw cron add` or the gateway API.

---

## github-monitor-morning
- **Schedule:** `0 8 * * *` (8am daily, Europe/London)
- **Session:** isolated
- **Purpose:** Check 5 repos for minor/major releases, send briefing to WhatsApp
- **Repos watched:**
  - `anthropics/claude-code`
  - `modelcontextprotocol/servers`
  - `mem0ai/mem0`
  - `langchain-ai/langgraph`
  - `browser-use/browser-use`

**Payload:**
```
Run github-monitor and send results to WhatsApp.

Run via shell:
export GITHUB_TOKEN=$(/usr/bin/python3 -c "import json; print(json.load(open('/Users/igorsilva/.config/openclaw/github.json'))['token'])")
/usr/bin/python3 ~/clawd/skills/github-monitor/scripts/github-monitor.py \
  --repos "anthropics/claude-code,modelcontextprotocol/servers,mem0ai/mem0,langchain-ai/langgraph,browser-use/browser-use" \
  --github-token "$GITHUB_TOKEN" \
  --min-version minor \
  --output-format briefing 2>&1

If releases found → send output to WhatsApp +447533464436
If no releases → send: "☀️ GitHub — no new releases today."
```

---

## Morning briefing (blogwatcher + github)
- **Schedule:** `0 9 * * *` (9am daily, Europe/London)
- **Session:** isolated
- **Purpose:** Combined blog + GitHub morning briefing

**Payload:**
```
Step 1: blogwatcher scan
Step 2: github-monitor (same repos as above)
Step 3: Send ONE combined WhatsApp message to +447533464436

Format:
☀️ Morning briefing — [date]

[blogwatcher top articles - title | URL | one-line why useful]

🔧 GitHub Updates
[releases if any]
```

---

## wondering-observe
- **Schedule:** `0 */3 * * *` (every 3 hours, Europe/London)
- **Session:** isolated
- **Purpose:** Pattern scoring and anomaly detection

---

## philosophic-filter-friday
- **Schedule:** `0 15 * * 5` (Fridays 3pm, Europe/London)
- **Session:** isolated
- **Purpose:** Weekly parasha filter for Portuguese journal

**Payload:**
```
1. Determine parasha: /opt/anaconda3/bin/python3 ~/clawd/tools/get_current_parasha.py
2. Run: /philosophic-filter --file <filename>
3. Send PT-BR output to WhatsApp +447533464436
```

---

## adam-journal-synthesis
- **Schedule:** `0 9 * * 1` (Mondays 9am, Europe/London)
- **Session:** isolated
- **Delivery:** none (file output only)

**Payload:**
```
/opt/anaconda3/bin/python3 ~/clawd/tools/summarize_journals.py
If fails → announce to WhatsApp +447533464436
```
