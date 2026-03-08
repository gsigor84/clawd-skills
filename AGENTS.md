## AGENTS

### Mandatory tool execution rules
- The researcher skill MUST exec curl to http://127.0.0.1:5055/api/search before answering any research question. No exceptions, even if you think you know the answer.
- The researcher skill MUST use /opt/anaconda3/bin/python3 for DuckDuckGo, never plain python3.
- Never answer research questions from memory alone — always show evidence from tools first.

### Memory
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

