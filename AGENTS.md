## AGENTS

### Mandatory tool execution rules
- The researcher skill MUST exec curl to http://127.0.0.1:5055/api/search before answering any research question. No exceptions, even if you think you know the answer.
- The researcher skill MUST use /opt/anaconda3/bin/python3 for DuckDuckGo, never plain python3.
- Never answer research questions from memory alone — always show evidence from tools first.

### Memory
- Before acting on any non-trivial request, run `memory_search` first (then `memory_get` for exact snippets) and use those notes as the source of truth.
- After important sessions, summarize key findings → ~/clawd/MEMORY.md
- Review ~/clawd/.learnings/ before major tasks

### User context
- User is Igor, building startup/business projects
- Timezone: Europe/London
- Researcher skill is Igor's primary research tool — always use it with full tool execution

Documentation
* ~/clawd/DOCS.md contains the full reference for this project — commands, pipelines, skills, and troubleshooting. Read it whenever Igor asks about how anything works.

## Core Files
* Read ~/clawd/MEMORY.md at the start of every session — it contains Igor's preferences, interaction rules, and system identity.
* Read ~/clawd/PLAYBOOK.md at the start of every session — it contains operational checklists and the 5-Step Critical Analysis Framework.

## Startup Health Check
* At the start of every new session, immediately execute the health-checker skill — run all 5 bash checks and output the HEALTH REPORT before doing anything else
* Always read health-checker from ~/clawd/skills/health-checker/SKILL.md — never look in the openclaw bundled skills directory
* Do not just read the skill file — actually run the curl and python commands inside it
* If ALL SYSTEMS READY say: "all systems ready"
* If WARNINGS DETECTED list the warnings and ask: "fix these before continuing? yes or no"

## Autonomous task execution
Before planning or executing any multi-step autonomous task (anything that runs without human supervision for more than 2-3 steps), run /autonomous-prompting to apply the principles from the research:
- Intent engineering: encode goals, values, and boundaries before starting
- Eval framework: define what "done correctly" looks like before executing
- Harness design: ensure tools, memory, and proactivity are properly configured

This applies to: notebooklm-runner, research-to-skill, skill-forge, any cron job, any multi-phase pipeline.

