# Skill Forge — Run Book

Complete step-by-step guide to build a skill from concept to shipped.

---

## Phase 0 — Setup Task

**What:** Create a ledger entry for the skill build.

**Command:**
```bash
/opt/anaconda3/bin/python3 ~/clawd/tools/ledger_event.py create skill-forge '{
  "skill_name": "<skill-name>",
  "topic": "<topic>",
  "goal": "<what the skill does>",
  "notebook_url": "<notebooklm url or empty>"
}'
```

**Output:** Task ID (e.g. `20260403T224425.155785Z`)

**Next:** Use task ID to resume if interrupted.

---

## Phase 0.5 — Generate Research Prompts

**What:** Generate 17 research prompts from the goal.

**Requires:** `OPENAI_API_KEY` environment variable.

**Commands:**
```bash
# Set key (if not already permanent)
export OPENAI_API_KEY='sk-proj-...'

# Generate prompts
/opt/anaconda3/bin/python3 ~/clawd/tools/generate_prompts.py \
  --topic "<topic>" \
  --goal "<goal description>" \
  --output-dir "/Users/igorsilva/clawd/tmp/skill-forge/<skill-name>/prompts"
```

**Output:** 17 `.txt` files in `prompts/` directory.

**Verify:**
```bash
ls ~/clawd/tmp/skill-forge/<skill-name>/prompts/
# Expect: p01.txt through p17.txt
```

---

## Phase 1 — Research

> ⚠️ **IMPORTANT: NotebookLM Chat automation via Tandem is broken.**
> NotebookLM uses React, which redraws the query box on every keystroke.
> Snapshot refs become stale immediately — fill/click commands fail with "Ref not found".
> This is a fundamental React limitation, not a config issue.
> See: `memory/notebooklm-automation-lesson.md` for full explanation.

**Option A: Perplexity (recommended)**

1. Igor pastes prompts into Perplexity
2. Copies responses back
3. Agent saves to `pass1/*.response.txt`

**Option B: Manual NotebookLM**

1. Open NotebookLM → Chat tab
2. Paste prompts manually, copy responses
3. Agent saves to `pass1/`

**Option C: NotebookLM Suggested Questions**

1. NotebookLM auto-generates suggested questions from sources
2. Click suggested questions to get auto-summaries
3. Agent extracts from snapshot

**Option D: Web Research (experimental)**

```bash
/opt/anaconda3/bin/python3 ~/clawd/tools/web_research.py \
  --prompts-dir ~/clawd/tmp/skill-forge/<skill-name>/prompts \
  --output-dir ~/clawd/tmp/skill-forge/<skill-name>/pass1
```

**Output:** `pass1/` directory with `.response.txt` files for each prompt.

**Verify:**
```bash
ls ~/clawd/tmp/skill-forge/<skill-name>/pass1/*.response.txt | wc -l
# Expect: 17
```

---

## Phase 2 — Gap Analysis (NetworkX)

**What:** Find structural gaps in the research corpus.

**Command:**
```bash
/opt/anaconda3/bin/python3 ~/clawd/tools/skill_gap_analysis.py \
  --input-dir "/Users/igorsilva/clawd/tmp/skill-forge/<skill-name>/pass1" \
  --output-dir "/Users/igorsilva/clawd/tmp/skill-forge/<skill-name>/gaps" \
  --top-gaps 8 \
  --min-degree 3
```

**Output:**
- `gap-prompts.md` — top gap keywords with gap scores
- `gap-rules.md` — synthesis rules for Phase 4
- `gap-meta.json` — structured gap data

**Verify:**
```bash
cat ~/clawd/tmp/skill-forge/<skill-name>/gaps/gap-meta.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Top gaps: {len(d[\"top_gaps\"])}')"
```

---

## Phase 3 — Deep Extraction (NotebookLM)

**What:** Use gap questions to dig deeper into the sources.

1. Open NotebookLM → Chat
2. Paste gap questions from `gaps/gap-prompts.md`
3. Capture responses to `pass2/` directory

**Alternative — Web research:**
```bash
/opt/anaconda3/bin/python3 ~/clawd/tools/web_research.py \
  --prompts-dir ~/clawd/tmp/skill-forge/<skill-name>/gaps \
  --output-dir ~/clawd/tmp/skill-forge/<skill-name>/pass2
```

---

## Phase 4 — Synthesis

**What:** Build the SKILL.md spec from research.

**Requires:** `pass1/`, `pass2/`, `gaps/` directories populated.

**Command:**
```bash
/opt/anaconda3/bin/python3 ~/clawd/tools/build_skill.py \
  --skill-name <skill-name> \
  --goal "<goal>" \
  --research-dir ~/clawd/tmp/skill-forge/<skill-name>/pass1 \
  --gap-dir ~/clawd/tmp/skill-forge/<skill-name>/gaps \
  --output ~/clawd/skills/<skill-name>/SKILL.md
```

**Verify:**
```bash
cat ~/clawd/skills/<skill-name>/SKILL.md | head -30
# Should show frontmatter + triggers + tools
```

---

## Phase 5 — Validate

**What:** Check SKILL.md structure and tools.

```bash
/opt/anaconda3/bin/python3 ~/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/<skill-name>/SKILL.md

/opt/anaconda3/bin/python3 ~/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  ~/clawd/skills/<skill-name>/SKILL.md
```

**Both must output: `PASS`**

---

## Phase 6 — Test

**What:** Run the skill with a real task.

**Command:**
```
/<skill-name> <test-task>
```

Example:
```
/writing-tutor I want to write about the problem with event tickets
```

**Verify:** Output is clear, structured, useful.

---

## Phase 7 — Ship

**What:** Push to GitHub.

```bash
cd ~/clawd
git add -A
git commit -m "<skill-name>: built from research"
git push
```

---

## Resume After Interruption

```bash
# Find your task ID
ls ~/clawd/tmp/runs/skill-forge/

# Resume from where you left off
# Check state
cat ~/clawd/tmp/runs/skill-forge/<task-id>/state.json

# Re-run specific phase
python3 ~/clawd/tools/skill_forge_resume.py --run-id <task-id> --from <phase-name>
```

---

## Quick Reference

| Phase | Time | Key Tool |
|-------|------|----------|
| 0 Setup | 1 min | ledger_event.py |
| 0.5 Prompts | 2 min | generate_prompts.py |
| 1 Research | 20-60 min | NotebookLM / Perplexity / web_research |
| 2 Gap Analysis | 5 min | skill_gap_analysis.py |
| 3 Deep Extract | 15 min | NotebookLM / web_research |
| 4 Synthesis | 10 min | build_skill.py |
| 5 Validate | 2 min | validate_skillmd.py |
| 6 Test | 5 min | Manual |
| 7 Ship | 2 min | git |

**Total: ~45 min to 1.5 hours** (depending on research phase)

---

## Troubleshooting

**generate_prompts.py fails with "OPENAI_API_KEY required":**
```bash
export OPENAI_API_KEY='sk-proj-...'
# Or add to ~/.zshrc for permanence
```

**NotebookLM auth fails:**
- Use Perplexity instead (Phase 1 Option B)
- Or use web_research.py (Phase 1 Option C)

**NotebookLM fill/fill fails on query box:**
- This is a React stale-element issue — NOT a config problem
- React-controlled inputs redraw on every keystroke, invalidating refs
- Solution: Use Perplexity Sonar API for research (reliable, no UI automation)
- See: `memory/notebooklm-automation-lesson.md`

**Perplexity Sonar API (recommended for Phase 1):**
- No UI automation needed
- Send prompts via API, get text responses
- Encode 17 prompts as JSON calls, add retries, save to pass1/
- Much more stable than NotebookLM Chat automation

**Local Playwright alternative:**
- Playwright handles React inputs with locator.waitFor() + event dispatching
- Could run as local HTTP service on same machine as Tandem
- For NotebookLM Chat automation if needed

**Tandem retry-loop (fragile, last resort):**
- Re-find element by semantic pattern (role, aria-label) before every action
- Retry N times with 50-100ms delay on stale-ref errors
- Still unreliable under load

**Skill-forge resume fails:**
```bash
# Manually check what's done
ls ~/clawd/tmp/skill-forge/<skill-name>/
# Re-run specific phase manually from this runbook
```