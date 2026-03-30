# MEMORY.md
Stable preferences and defaults. Read this first, every time.

## User
- Name: Igor
- Machine: Mac

## Output Defaults
- Tone: short, direct — no fluff
- Format: markdown unless told otherwise
- Never repeat questions already answered
- Never ask me to wait
- Skip preamble — get to the point immediately
- Web search: prefer Brave Search over DuckDuckGo for all web searches (default).

## Interaction Rules
- Don't summarize what you just did at the end
- Don't say "Great!" or "Sure!" or any filler affirmations
- If unsure, ask ONE question — not a list
- **Strict Context Mode (default; anti-hallucination):** for factual questions, answer only from tools/KB/workspace/history; if insufficient, say so and don’t guess. Opt-out only when I explicitly say **"best-effort"**.
- **Google Business Trends checks:** follow the `PLAYBOOK.md → Reading Data from Tabs → Google Trends` checklist (extract volumes/momentum/time, map to real stories via web search, filter irrelevant/local, rank by global significance with crypto/markets/AI preference).
- For **creative living / idea / writing / making** questions: follow `SOUL.md` standing order — **search `~/clawd/learn/json/` before answering** (use it as the knowledge library built by `/learn + /ingest`).

## Code Defaults
- Always show the full file or the exact patch — no "..." placeholders
- Prefer working code over explanations
- If something is broken, fix it — don't just describe how to fix it

## Interests & Location
- Location: Cambridge, UK (not London — filter out London-specific local news unless it has national significance)
- Interests: finance, tech, crypto, business, global markets, AI
- Not interested in: local transport, local utility companies, celebrity gossip, sports
- I follow crypto closely — Bitcoin, market-moving statements from major figures like Musk are always relevant
- When multiple stories exist for the same trend, always pick the crypto/markets angle if one exists. Specifically: if Musk + Bitcoin/crypto is one of the stories, always pick that over legal/trial stories about the same person.


## Perplexity Automation Findings (2026-03-28)

### UI vs API
- Perplexity UI allows guest searches but blocks automated submit clicks (client-side JS checks)
- Use API instead: `api.perplexity.ai/chat/completions`

### API Call Example
```bash
curl -X POST https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "sonar-small-online", "messages": [{"role": "user", "content": "your query"}]}'
```

## Pattern Log: 2026-03-30T17:30 UTC (wondering-observe cron)

### Pattern 1: WhatsApp gateway instability (HIGH, freq: 10+ in 30min)
- Gateway disconnects every ~60 seconds (status 499), immediately reconnects
- Session affected: 68564db5-b1ed-4315-8650-8a5c221f0f82
- Impact: multiple spurious system messages, user confusion about connection status
- Source: main session history, timestamps 2026-03-30T09:37-10:10

### Pattern 2: WhatsApp tool output not rendered (MEDIUM)
- File contents shown via read tool do not appear in WhatsApp messages
- Display limitation on WhatsApp channel, not Adam's fault
- Source: user complaint via WhatsApp 2026-03-29 18:53

### Pattern 3: notebooklm-runner stalls at p09 (LOW)
- Runner completes all 9 prompts then loops looking for p10-p17
- No more prompts available — needs either new prompts or runner fix
- Source: session history 2026-03-29

### Pattern 4: Model timeouts requiring recovery (MEDIUM)
- "Continue where you left off" appeared twice in sequence 2026-03-30T03:06-03:07
- Model failures mid-session
- Source: session history 2026-03-30

### Pattern 5: File path confusion (LOW)
- User had to correct path from ~/clawd/context.md to full path
- Memory retrieval may help if context is stored properly
- Source: WhatsApp exchange 2026-03-29 18:50

### Pattern Score: 0.72 (above threshold - WhatsApp gateway is the critical issue)
