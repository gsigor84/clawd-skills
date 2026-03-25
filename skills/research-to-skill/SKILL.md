---
name: research-to-skill
description: "# research-to-skill — Run a 5-phase research pipeline that extracts baseline knowledge from a NotebookLM notebook, performs gap analysis via LightRAG, runs a second-pass deep extraction on structural gaps, synthesizes both passes, and builds an OpenClaw skill."
---

# research-to-skill

Two-pass research pipeline with gap-driven exploration → skill output.

## Trigger

`/research-to-skill --notebook-url <url> --skill-name <name>`

## Inputs

- `--notebook-url` (required): NotebookLM notebook URL
- `--skill-name` (required): Name for the output skill (will create ~/clawd/skills/<skill-name>/)

## Pipeline

### Phase 1 — BASELINE EXTRACTION

```
TOOL: exec
COMMAND:
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/notebooklm-runner/scripts/run_notebooklm_runner.py \
  --notebook-url "<notebook-url>" \
  --prompts-dir "/Users/igorsilva/clawd/tmp/notebooklm-prompts" \
  --runs-dir "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass1" \
  --progress-file "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass1/progress.md" \
  --final-summary "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass1/summary.md"
OUTPUT USED FOR: Response files in pass1/ directory → input to Phase 2
```

**Phase 1 Complete:** Move to Phase 2.

### Phase 2 — GAP ANALYSIS

```
TOOL: exec
COMMAND:
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/tools/gap_analysis.py \
  --input-dir "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass1" \
  --output-file "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/gaps/gap-prompts.md" \
  --working-dir "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/gaps"
OUTPUT USED FOR: gaps/gap-prompts.md + gaps/p01.txt... → input to Phase 3
```

**Phase 2 Complete:** Move to Phase 3.

### Phase 3 — DEEP EXTRACTION

```
TOOL: exec
COMMAND:
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/notebooklm-runner/scripts/run_notebooklm_runner.py \
  --notebook-url "<notebook-url>" \
  --prompts-dir "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/gaps" \
  --runs-dir "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass2" \
  --progress-file "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass2/progress.md" \
  --final-summary "/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/pass2/summary.md"
OUTPUT USED FOR: Response files in pass2/ directory → input to Phase 4
```

**Phase 3 Complete:** Move to Phase 4.

### Phase 4 — SYNTHESIS

```
TOOL: exec
COMMAND:
mkdir -p /Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/synthesis && \
/opt/anaconda3/bin/python3 -c "
import os
out = []
for p in ['pass1', 'pass2']:
    d = f'/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/{p}'
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith('.response.txt'):
                out.append('\\n### {}: {}\\n'.format(p, f))
                out.append(open(os.path.join(d, f)).read())
open('/Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/synthesis/enriched-summary.md', 'w').write('\\n'.join(out))
" && \
cp /Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/gaps/gap-rules.md \
   /Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/synthesis/
OUTPUT USED FOR: synthesis/enriched-summary.md → input to Phase 5
```

**Phase 4 Complete:** Move to Phase 5.

### Phase 5 — SKILL BUILD

```
TOOL: sessions_spawn
RUNTIME: acp
AGENT: skillmd-builder-agent
TASK:
Build a SKILL.md from /Users/igorsilva/clawd/tmp/research-to-skill/<skill-name>/synthesis/enriched-summary.md

Trigger: /<skill-name>

Save to: /Users/igorsilva/clawd/skills/<skill-name>/SKILL.md
OUTPUT USED FOR: Final SKILL.md location
```

## Failure Handling

- If any phase fails: log ERR entry to ~/clawd/.learnings/ERRORS.md with stage=research-to-skill, output "❌ Phase N failed: <reason>", stop pipeline
- Do not continue to next phase on failure
- Show "✅ Phase N complete" after each successful phase

## Output Structure

```
~/clawd/tmp/research-to-skill/<skill-name>/
├── pass1/           # Baseline extraction (14 prompts)
│   └── *.response.txt
├── gaps/            # Gap analysis output
│   ├── gap-prompts.md
│   ├── gap-rules.md
│   └── p01.txt...pXX.txt
├── pass2/           # Deep extraction on gaps
│   └── *.response.txt
├── synthesis/       # Merged output
│   ├── enriched-summary.md
│   └── gap-rules.md
~/clawd/skills/<skill-name>/
└── SKILL.md
```

## Failure modes

- **Phase 1 failure:** notebooklm-runner fails → stop, log ERR
- **Phase 2 failure:** gap_analysis.py fails → stop, log ERR
- **Phase 3 failure:** notebooklm-runner fails on gap prompts → stop, log ERR
- **Phase 4 failure:** synthesis merge fails → stop, log ERR
- **Phase 5 failure:** skillmd-builder-agent fails → stop, log ERR

## Toolset

- exec
- write
- sessions_spawn