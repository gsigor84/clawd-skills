---
name: skill-forge
description: "# skill-forge — Orchestrate research-to-skill pipeline with agent-team-orchestration. Runs research → spec → build → validate → critic flow with task states, handoffs, quality gates."
---

# skill-forge

Orchestrate research-to-skill pipeline using agent-team-orchestration patterns. Produces skills from NotebookLM with explicit handoffs, task states, and quality gates.

## Trigger

`/skill-forge --topic <topic> --goal <goal> --notebook-url <url> --skill-name <name>`
`/skill-forge --topic <topic> --goal <goal> --notebook-url <url> --skill-name <name> --creative`
`/skill-forge --topic <topic> --goal <goal> --skill-name <name> --web-research`
`/skill-forge --topic <topic> --notebook-url <url> --skill-name <name>` (legacy without goal)

### --goal flag (required for goal-driven prompts)

When `--goal` is passed, Phase 0.5 runs first to generate goal-tailored prompts before Phase 1.

### --web-research mode

When `--web-research` is specified, the pipeline uses web research instead of NotebookLM:

**Differences from NotebookLM mode:**
- **Phase 1:** Uses `~/clawd/tools/web_research.py` to fetch arXiv papers, then `~/clawd/tools/corpus_prompter.py` to run 17 prompts against the corpus
- **Phase 3:** Uses `corpus_prompter.py` again on gap analysis results
- **No notebook URL required**

**Phase 1 (Baseline via web research):**
```bash
# Step 1: Search arXiv and generate corpus
/opt/anaconda3/bin/python3 ~/clawd/tools/web_research.py \
  --topic "<topic>" \
  --limit 10 \
  --output-dir "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass1"

# Step 2: Run 17 prompts against the corpus
/opt/anaconda3/bin/python3 ~/clawd/tools/corpus_prompter.py \
  --corpus-file "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass1/research-corpus.md" \
  --prompts-dir "/Users/igorsilva/clawd/tmp/notebooklm-prompts" \
  --output-dir "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass1" \
  --model gpt-4o-mini
```

**Phase 3 (Deep extraction via web research):**
```bash
# Run corpus_prompter.py on gap prompts
/opt/anaconda3/bin/python3 ~/clawd/tools/corpus_prompter.py \
  --corpus-file "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/synthesis/enriched-summary.md" \
  --prompts-dir "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/gaps" \
  --output-dir "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass2" \
  --model gpt-4o-mini
```

## Team Structure

| Role | Purpose | Pipeline Phase |
|------|---------|----------------|
| **Orchestrator** | Route phases, track state, handle failures | All (oversees) |
| **Builder** | Execute phases 1-3: baseline, gap analysis, deep extraction | 1-3 |
| **Reviewer** | Execute phases 4-5: synthesis, skill build | 4-5 |
| **Critic** | Run self-improving-skill-builder on final SKILL.md | Post-build |

## When to Use

- Build a skill from NotebookLM research sources
- Need explicit quality gates and review steps
- Want task state tracking across all 6 phases
- Want critic review on final SKILL.md

## Task State File

`~/clawd/tmp/skill-forge/<skill-name>/task-state.json`

```json
{
  "taskId": "<skill-name>",
  "topic": "<topic>",
  "notebookUrl": "<url>",
  "status": "IN_PROGRESS",
  "phase": 1,
  "team": {
    "orchestrator": {"role": "track state, route phases"},
    "builder": {"role": "phases 1-3", "status": "active"},
    "reviewer": {"role": "phases 4-5", "status": "pending"},
    "critic": {"role": "post-build review", "status": "pending"}
  },
  "phases": {
    "1-baseline": {"status": "PENDING", "handoff": null},
    "2-gap-analysis": {"status": "PENDING", "handoff": null},
    "3-deep-extraction": {"status": "PENDING", "handoff": null},
    "4-synthesis": {"status": "PENDING", "handoff": null},
    "5-skill-build": {"status": "PENDING", "handoff": null},
    "6-critic": {"status": "PENDING", "handoff": null}
  },
  "failures": []
}
```

## Pipeline Phases

### Phase 0.5: PROMPT GENERATION (when --goal flag is passed)

**When:** Only with `--goal` flag

**Prerequisite:** Task state created, topic and goal defined

**Action:**
```bash
# Generate 17 goal-tailored prompts
/opt/anaconda3/bin/python3 ~/clawd/tools/generate_prompts.py \
  --topic "<topic>" \
  --goal "<goal>" \
  --output-dir "/Users/igorsilva/clawd/tmp/skill-forge/<skill-name>/prompts"
```

**Handoff:**
```
What was done: 17 prompts generated and saved to prompts/p01.txt...p17.txt
Where artifacts: prompts/p01.txt...p17.txt
How to verify: Check all 17 files exist with non-empty content
Known issues: Depends on OPENAI_API_KEY
What's next: Phase 1 uses these prompts instead of default notebooklm-prompts
```

---

### Phase 1: BASELINE EXTRACTION (Builder)

**Action:**
```bash
# If --goal was passed, use generated prompts; otherwise use default prompts
if [ -d "/Users/igorsilva/clawd/tmp/skill-forge/<skill-name>/prompts" ]; then
  PROMPTS_DIR="/Users/igorsilva/clawd/tmp/skill-forge/<skill-name>/prompts"
else
  PROMPTS_DIR="/Users/igorsilva/clawd/tmp/notebooklm-prompts"
fi

/opt/anaconda3/bin/python3 ~/clawd/skills/notebooklm-runner/scripts/run_notebooklm_runner.py \
  --notebook-url "<url>" \
  --prompts-dir "${PROMPTS_DIR}" \
  --runs-dir "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass1" \
  --progress-file "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass1/progress.md" \
  --final-summary "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass1/summary.md"
```

**Handoff:**
```
What was done: 17 baseline prompts extracted to pass1/
Where artifacts: pass1/*.response.txt
How to verify: progress.md shows OK status on all prompts
Known issues: None
What's next: Run gap analysis
```

---

### Phase 2: GAP ANALYSIS (Builder)

**Action:**
```bash
/opt/anaconda3/bin/python3 ~/clawd/tools/gap_analysis.py \
  --input-dir "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass1" \
  --output-file "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/gaps/gap-prompts.md" \
  --working-dir "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/gaps"
```

**Handoff:**
```
What was done: LightRAG extracted N entities, N gap prompts generated
Where artifacts: gaps/gap-prompts.md, gaps/p01.txt...p08.txt
How to verify: Check for bridging + transcend questions
Known issues: May need retry if no gaps found
What's next: Run deep extraction on gaps
```

---

### Phase 3: DEEP EXTRACTION (Builder)

**Action:**
```bash
/opt/anaconda3/bin/python3 ~/clawd/skills/notebooklm-runner/scripts/run_notebooklm_runner.py \
  --notebook-url "<url>" \
  --prompts-dir "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/gaps" \
  --runs-dir "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass2" \
  --progress-file "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass2/progress.md" \
  --final-summary "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass2/summary.md"
```

**Handoff:**
```
What was done: N gap prompts answered
Where artifacts: pass2/*.response.txt
How to verify: Check response files exist
Known issues: None
What's next: Merge passes and validate
```

---

### Phase 4: SYNTHESIS (Reviewer)

**Action:**
```bash
mkdir -p /Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/synthesis && \
/opt/anaconda3/bin/python3 -c "
import os
out = []
for p in ['pass1', 'pass2']:
    d = '/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/{}'.format(p)
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith('.response.txt'):
                out.append('\n### {}: {}\n'.format(p, f))
                try:
                    out.append(open(os.path.join(d, f)).read())
                except: pass
open('/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/synthesis/enriched-summary.md', 'w').write('\n'.join(out))
" && \
cp /Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/gaps/gap-rules.md \
   /Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/synthesis/
```

**Handoff:**
```
What was done: Both passes merged into single enriched summary
Where artifacts: synthesis/enriched-summary.md, synthesis/gap-rules.md
How to verify: File size > 100KB indicates substantial content
Known issues: Quality depends on pass1+pass2 outputs
What's next: Build SKILL.md (or Phase 4.5 with --creative)
```

---

### Phase 4.5: CREATIVE EXPANSION (Reviewer, optional)

**When:** Only with `--creative` flag

**Prerequisite:** Phase 4 (Synthesis) must be complete

**Action:**
```bash
# Read enriched-summary.md and run idea-generator-v2 to find non-obvious angles
# First, copy enriched-summary to a temp location accessible by idea-generator
cp /Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/synthesis/enriched-summary.md \
   /Users/igorsilva/clawd/tmp/idea-generator-context.md

# Run idea-generator-v2 skill via sessions_spawn
sessions_spawn:
  runtime: "acp"
  agentId: "idea-generator-v2"
  task: "Based on the research corpus at /Users/igorsilva/clawd/tmp/idea-generator-context.md, identify non-obvious angles, unexpected connections, and approaches that would make a skill built from this research genuinely different from the obvious version. Find the spine - the one-sentence statement of what this work is really about. Save output to /Users/igorsilva/clawd/tmp/skill-forge/<skill-name>/creative-expansion.md"
```

**Handoff:**
```
What was done: Creative expansion via idea-generator-v2, finding non-obvious angles
Where artifacts: creative-expansion.md
How to verify: Check for spine + unexpected angles identified
Known issues: Depends on idea-generator-v2 being available
What's next: Build SKILL.md with both enriched-summary.md AND creative-expansion.md
```

---

### Phase 5: SKILL BUILD (Reviewer)

**Action:**
```bash
# Build SKILL.md using skillmd-builder-agent
sessions_spawn:
  runtime: "acp"
  agentId: "skillmd-builder-agent"
  task: "Build a SKILL.md from /Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/synthesis/enriched-summary.md. Save to ~/clawd/skills/<skill-name>/SKILL.md. Use the research content to define: name, description, use cases, inputs, outputs, step-by-step procedure, failure_modes, toolset, and acceptance tests."
```

**Handoff:**
```
What was done: SKILL.md generated from enriched research
Where artifacts: ~/clawd/skills/<skill-name>/SKILL.md
How to verify: Check SKILL.md has valid frontmatter + body
Known issues: May need manual cleanup
What's next: Run critic review
```

---

### Phase 6: CRITIC (Critic)

**Action:**
```bash
# Run self-improving-skill-builder to validate and improve the SKILL.md
sessions_spawn:
  runtime: "acp"
  agentId: "self-improving-skill-builder"
  task: "Run /improve-skills --targets <skill-name> --skills-dir ~/clawd/skills"
```

**Handoff:**
```
What was done: Critic review complete
Where artifacts: task-state.json (updated with improvements)
How to verify: Check improvements list in state file
Known issues: None
What's next: Pipeline complete
```

---

### Phase 7: REPORT GENERATION (mandatory)

**Action:**
```bash
/opt/anaconda3/bin/python3 ~/clawd/tools/pipeline_report.py \
  --skill-name "<skill-name>" \
  --mode "notebooklm" \
  --notebook-url "<url>"
```

For `--web-research` mode, use `--mode "web-research"` instead.

**Output:** `~/clawd/tmp/skill-forge/<skill-name>/pipeline-report.md`

**Handoff:**
```
What was done: Full pipeline report generated with all artifacts
Where artifacts: pipeline-report.md
How to verify: File size > 10KB indicates substantial content
Known issues: None
What's next: Pipeline complete
```

---

## Handoff Protocol (per agent-team-orchestration)

Every phase outputs structured handoff:
1. **What was done** — summary of phase output
2. **Where artifacts are** — exact file paths
3. **How to verify** — check commands or criteria
4. **Known issues** — any gaps or risks
5. **What's next** — next phase to run

---

## Failure Handling

| Phase | Failure | Retry | Then |
|-------|---------|-------|------|
| 1-3 | notebooklm-runner fails | 3x | Log to failures[], continue |
| 2 | gap_analysis fails | 2x | Skip to next, note in state |
| 4 | Synthesis fails | 1x | Use pass1 only, note gap |
| 5 | skillmd-builder fails | 2x | Output partial, note error |
| 6 | Critic fails | 1x | Skip, note in state |
| 7 | Report generation fails | 1x | Skip, log error |

---

## Toolset

- **exec**: Run notebooklm-runner, gap_analysis.py
- **sessions_spawn**: Invoke skillmd-builder-agent, self-improving-skill-builder
- **write**: Create task-state.json, synthesis files
- **read**: Check outputs, verify phase completion

---

## Acceptance Criteria

1. ✅ Task state file created at `~/clawd/tmp/skill-forge/<skill-name>/task-state.json`
2. ✅ Task state updated after each phase
3. ✅ Structured handoffs between all 6 phases
4. ✅ Failure handling logs to task-state.json
5. ✅ Final SKILL.md at `~/clawd/skills/<skill-name>/SKILL.md`
6. ✅ Critic phase runs self-improving-skill-builder

---

## References

- [agent-team-orchestration/SKILL.md](../agent-team-orchestration/SKILL.md)
- [agent-team-orchestration/references/task-lifecycle.md](../agent-team-orchestration/references/task-lifecycle.md)
- [agent-team-orchestration/references/patterns.md](../agent-team-orchestration/references/patterns.md)