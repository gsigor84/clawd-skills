---
name: health-checker
description: Triggered by "check health", "health check", or "system check". Internal preflight used by the vibe, validate, and intel orchestrators (before stage 1) and also runnable directly by the user. Runs 5 lightweight checks covering browser relay, Brave Search, Open Notebook knowledge base, Playwright, and gateway health, then outputs a HEALTH REPORT with ALL SYSTEMS READY or WARNINGS DETECTED plus plain-English fix commands for anything unavailable.
tools: bash
---

## health-checker

### Trigger
- check health
- health check
- system check

### Hard constraints
- Never require external dependencies.
- Use only **bash**, **curl**, and **/opt/anaconda3/bin/python3**.
- Never modify any files.
- Always run all 5 checks even if one fails (no short-circuiting).
- Output must be plain text and directly usable by orchestrators to decide whether to proceed.
- Warnings must be plain English; fix commands must be exact.

### Steps (must run in this exact order)

1) **Browser check (Chrome relay)**
- Run: `curl -s http://127.0.0.1:9222/json`
- Mark **Browser relay: READY** if the command returns any response at all (including `Unauthorized`). Any response means the relay endpoint is running.
- Only mark **Browser relay: UNAVAILABLE** if the connection is refused or times out, and set warning:
  - `Chrome relay not reachable — click the extension icon to attach a tab.`

2) **Brave Search check**
- Run:
  - `curl -s "https://api.search.brave.com/res/v1/web/search?q=test&count=1" -H "Accept: application/json" -H "X-Subscription-Token: BSATauqhG5V6hBQaS2y0_SSNf8i1fVe"`
- If the response contains a top-level `web` key, mark **Brave Search: READY**.
- Otherwise mark **Brave Search: UNAVAILABLE** and set warning:
  - `Brave Search not responding — check your internet connection or API key.`

3) **Knowledge base check (Open Notebook KB)**
- Run:
  - `curl -s -X POST http://127.0.0.1:5055/api/search -H "Content-Type: application/json" -d "{\"query\":\"test\",\"type\":\"text\",\"limit\":1}"`
- If the response contains `results` or `data`, mark **KB: READY**.
- Otherwise mark **KB: UNAVAILABLE** and set warning:
  - `Open Notebook KB not responding — check if it is running.`

4) **Playwright check**
- Run:
  - `/opt/anaconda3/bin/python3 -c "from playwright.sync_api import sync_playwright; print('ok')"`
- If output is exactly `ok`, mark **Playwright: READY**.
- Otherwise mark **Playwright: UNAVAILABLE** and set warning:
  - `Playwright not available — run playwright install chromium.`

5) **Gateway check**
- Run:
  - `curl -s http://127.0.0.1:18789/health`
- Mark **Gateway: READY** if the command returns any response at all. Any response means the gateway endpoint is reachable.
- Only mark **Gateway: UNAVAILABLE** if the connection is refused or times out, and set warning:
  - `Gateway not healthy — run pkill -f clawdbot-gateway and sleep 2 and clawdbot gateway start.`

6) **Output (HEALTH REPORT)**
Produce a plain text HEALTH REPORT with exactly two sections:

- **Section 1: SYSTEM STATUS**
  - If every check passed: `ALL SYSTEMS READY`
  - Else: `WARNINGS DETECTED`

- **Section 2: CHECK RESULTS**
  - List each check with status `READY` or `UNAVAILABLE`.
  - If UNAVAILABLE, include its warning message.

If SYSTEM STATUS is ALL SYSTEMS READY, output a single line:
- `all systems ready, proceeding.`

If SYSTEM STATUS is WARNINGS DETECTED:
- List every warning clearly in plain English.
- Ask the user exactly:
  - `fix these issues before continuing? yes or no.`
