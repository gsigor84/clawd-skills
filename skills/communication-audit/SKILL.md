---
name: communication-audit
description: Analyze Igor's communication patterns and provide insights to improve clarity, brevity, and output quality. Tracks the "brief → output" loop: when brief quality is high, output quality is high. Weekly reports sent to WhatsApp.
---

# communication-audit

Track, analyze, and improve how Igor communicates with Adam.

## Core insight

**The brief quality loop:**
- Clear, specific brief → Adam produces correct output in one shot
- Vague or bundle requests → multiple corrections needed
- This skill surfaces that loop so Igor can see it and adjust

## What it tracks

| Metric | What it measures |
|--------|-----------------|
| **Brief quality** | Context, constraints, format specifiers present? |
| **Ask clarity** | Single focused request or multiple bundled asks? |
| **Output alignment** | Did the first output match what was wanted? |
| **Pattern detected** | Which brief styles produce best outputs |

## Data source

`~/.openclaw/workspace/.active-session-log.md`

Format expected per entry:
```
## [YYYY-MM-DD HH:MM BST] — [topic]
Igor: [exact message or summary of what Igor asked]
Agent: [what Adam did]
Outcome: [what happened — success, revision needed, follow-up]
```

The more detailed the Igor field, the better the analysis.

## Trigger

`/communication-audit` — run on demand, returns full report to WhatsApp

## Output format

```
=== COMMUNICATION INSIGHTS ===

SCORES:
  Brief quality:   X/10
  Ask clarity:     X/10
  Overall:         X/10

WHAT'S WORKING:
  • "exact brief that worked well"
    → Score: X/10 (why it worked)

COULD IMPROVE:
  • "brief that caused rework or confusion"
    → Why it missed

PATTERN:
  Connecting brief style → output quality

THIS WEEK'S FOCUS:
  One specific thing to work on
```

## Weekly cron

Every Monday 9am — send report to WhatsApp automatically.

## Improving accuracy

The session log is the data source. Best practices for logging:
- After each meaningful exchange, log the EXACT thing Igor asked (not a paraphrase)
- Note if output needed revision: "had to ask twice" vs "perfect first time"
- Capture the outcome: what happened after Adam responded

## Files

- `scripts/audit.py` — parse session log, extract exchanges
- `scripts/report.py` — score dimensions, format report
