# Research-to-Skill Pipeline — Complete Guide

## Overview

This pipeline turns a body of research (NotebookLM notebooks + prompt runs) into a **production-grade OpenClaw skill**.

It is designed for cases where you want to:
- extract a *baseline* library of techniques/concepts (Pass 1)
- detect missing links/gaps via a lightweight knowledge graph (Gap Analysis)
- run a *second* deep pass to fill the gaps (Pass 2)
- synthesise everything into a clean artefact suitable for SkillMD generation
- validate the SkillMD deterministically
- (optionally) rewrite the skill from “technique explainer” into a **creative production tool**

The `creativity-toolkit-v3` build is the reference implementation for the pipeline.

---

## Prerequisites

### Required tools
- OpenClaw repo workspace at `~/clawd`
- Python (Anaconda) at: `/opt/anaconda3/bin/python3`
- NotebookLM runner script:
  - `~/clawd/skills/notebooklm-runner/scripts/run_notebooklm_runner.py`
- Skill validator:
  - `~/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py`

### Environment assumptions
- You can access the target NotebookLM notebook URL in an automated browser session.
- Your OpenClaw gateway is running (for normal ops). WhatsApp flapping (status 499) does not block the pipeline.

### Files/directories used (conventions)
- Working root per skill: `~/clawd/tmp/research-to-skill/<skill-name>/`
- Pass 1 outputs: `pass1/` (or `pass1_*` variants)
- Pass 2 outputs: `pass2/`
- Gap prompts: `gaps/`
- Synthesis: `synthesis/`

---

## Phase 0.5 — Goal-Driven Prompt Generation

**Goal:** generate a set of prompts to run in NotebookLM that reflect the project’s goal and constraints.

In the `creativity-toolkit-v3` run, prompt generation was already available as pass prompt sets in the workspace.

**Outputs (typical):**
- `tmp/research-to-skill/<skill>/pass1/<timestamp>_prompt-XX_*.txt`
- optional meta json files describing intent

---

## Phase 1 — Baseline Extraction (NotebookLM)

**Goal:** run baseline prompts against a NotebookLM notebook to extract the initial set of techniques.

**Command (example):**

```bash
/opt/anaconda3/bin/python3 \
  ~/clawd/skills/notebooklm-runner/scripts/run_notebooklm_runner.py \
  --notebook-url "<NOTEBOOKLM_URL>" \
  --prompts-dir "~/clawd/tmp/research-to-skill/<skill>/pass1" \
  --runs-dir   "~/clawd/tmp/research-to-skill/<skill>/pass1" \
  --progress-file "~/clawd/tmp/research-to-skill/<skill>/pass1/progress.md" \
  --final-summary "~/clawd/tmp/research-to-skill/<skill>/pass1/summary.md" \
  --max-checks 3600 \
  --sleep-seconds 2.0
```

**What it produces:**
- `progress.md`: per-prompt execution log
- `*.response.txt`: raw extracted text per prompt
- `summary.md`: consolidated per-prompt preview/summary

### Important fix: runner prompt discovery
Historically the runner assumed `p01..p17` and would crash if any were missing.

**Fix applied:** `run_notebooklm_runner.py` now runs **whatever `pNN.txt` files exist** in the prompts dir.

Impact:
- Gap runs can have `p01..p08` and still succeed.
- No need to create dummy `p09.txt` placeholders.

---

## Phase 1.5 — Clean Pass 1

**Goal:** normalise + deduplicate techniques into a consistent format.

Tool: `~/clawd/tools/clean_summary.py`

**Command:**

```bash
python3 ~/clawd/tools/clean_summary.py \
  --input  "~/clawd/tmp/research-to-skill/<skill>/pass1/summary.md" \
  --output "~/clawd/tmp/research-to-skill/<skill>/pass1/clean-summary.md"
```

**What it produces:**
- `clean-summary.md`: unique techniques, consistent fields.

### Cleaner capabilities (as implemented)
- Handles multiple formats:
  1. `## Technique Name` headings + `**Trigger:** ...` blocks
  2. `Name | Trigger | Timer | ...` (pipe separated)
  3. `**Name** | ...` (bold pipe)
  4. `- Name: X` / `- Trigger: Y` (dash-label)
  5. `**Trigger** | ...` (bold label newline)
- Dedupes by name (case-insensitive), strips leading articles (the/a/an)
- Stoplist removes broken entries where “technique name” is just a field label:
  - `Name`, `Trigger`, `Timer`, `Steps`, `Template`, `Failure-mode fix`, `Source`, `Source snippet`

---

## Phase 2 — Gap Analysis

**Goal:** build a lightweight knowledge graph from the clean summary and generate “bridging” + “transcend” prompts.

Tool: `~/clawd/tools/gap_analysis.py`

### Key behaviour
- Prefers `clean-summary.md` over `summary.md` if both exist in the input dir.
- Filters NotebookLM UI noise entities before graph construction.

**Command (example):**

```bash
rm -rf ~/clawd/rag_storage
/opt/anaconda3/bin/python3 ~/clawd/tools/gap_analysis.py \
  --input-dir   "~/clawd/tmp/research-to-skill/<skill>/pass1" \
  --output-file "~/clawd/tmp/research-to-skill/<skill>/gaps/gap-prompts.md"
```

**What it produces:**
- `gaps/p01.txt..pNN.txt`: prompts for Phase 3
- `gap-prompts.md`: consolidated prompt list
- `gap-rules.md`: prompt framework notes

### UI noise stoplist (applied)
Filtered entities (case-insensitive):
- Reports, Infographic, Flashcards, Quiz, Mind Map, Data table
- Audio Overview, Slide deck, Video Overview, Studio, Add note, NotebookLM

Also filtered generic hubs / junk that pollute graphs:
- Name/Trigger/Timer/Steps/Template/Failure-mode fix/Source/Source snippet
- BETA, Current Task/Project/Video Project
- Author/Authors/Sources

---

## Phase 3 — Deep Extraction (NotebookLM)

**Goal:** run NotebookLM on the generated gap prompts to pull in missing links and deeper synthesis.

**Command:**

```bash
/opt/anaconda3/bin/python3 \
  ~/clawd/skills/notebooklm-runner/scripts/run_notebooklm_runner.py \
  --notebook-url "<NOTEBOOKLM_URL>" \
  --prompts-dir "~/clawd/tmp/research-to-skill/<skill>/gaps" \
  --runs-dir   "~/clawd/tmp/research-to-skill/<skill>/pass2" \
  --progress-file "~/clawd/tmp/research-to-skill/<skill>/pass2/progress.md" \
  --final-summary "~/clawd/tmp/research-to-skill/<skill>/pass2/summary.md" \
  --max-checks 3600 \
  --sleep-seconds 2.0
```

**What it produces:**
- `pass2/*.response.txt`
- `pass2/summary.md`
- `pass2/progress.md`

---

## Phase 4 — Synthesis

**Goal:** merge Pass 1 baseline techniques and Pass 2 gap responses into a single enriched artefact.

**Command (used in v3):**

```bash
mkdir -p ~/clawd/tmp/research-to-skill/<skill>/synthesis

/opt/anaconda3/bin/python3 - <<'PY'
import os
out = []
clean = '/Users/igorsilva/clawd/tmp/research-to-skill/<skill>/pass1/clean-summary.md'
if os.path.isfile(clean):
    out.append('# PASS 1 — BASELINE TECHNIQUES\n')
    out.append(open(clean, encoding='utf-8', errors='replace').read())
pass2 = '/Users/igorsilva/clawd/tmp/research-to-skill/<skill>/pass2'
out.append('\n# PASS 2 — GAP ANALYSIS RESPONSES\n')
for f in sorted(os.listdir(pass2)):
    if f.endswith('.response.txt'):
        out.append(f'\n### {f}\n')
        out.append(open(os.path.join(pass2, f), encoding='utf-8', errors='replace').read())
open('/Users/igorsilva/clawd/tmp/research-to-skill/<skill>/synthesis/enriched-summary.md', 'w', encoding='utf-8').write('\n'.join(out))
print('Done')
PY
```

**What it produces:**
- `synthesis/enriched-summary.md`

---

## Phase 4.5 — Clean Synthesis

**Goal:** remove broken technique entries and produce the final “skill-ready” technique library.

In `creativity-toolkit-v3`, the enriched summary still contained broken entries like:

```md
## Name
**Trigger:** The Fear Welcome Speech
**Timer:** (missing)
```

**Command:**

```bash
python3 ~/clawd/tools/clean_summary.py \
  --input  "~/clawd/tmp/research-to-skill/<skill>/synthesis/enriched-summary.md" \
  --output "~/clawd/tmp/research-to-skill/<skill>/synthesis/enriched-summary.clean.md"
```

**What it produces:**
- `enriched-summary.clean.md` (in v3: 33 valid techniques)

---

## Phase 5 — Skill Build

**Goal:** generate a valid OpenClaw `SKILL.md`.

### Required sections (validator-enforced)
The validator requires headings with exact names:
- `## Use`
- `## Inputs`
- `## Outputs`
- `## Failure modes` (or `## Hard blockers`)
- `## Acceptance tests`

Frontmatter must contain ONLY:
- `name`
- `description`

### Validator command

```bash
/opt/anaconda3/bin/python3 \
  ~/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/<skill>/SKILL.md
```

---

## Phase 6 — Rewrite for Production

**Goal:** convert the skill from a “technique explainer” into a **creative production tool**.

Behavior:
- user invokes with `/creativity-toolkit-v3 --task "..."`
- skill internally applies 3–5 techniques
- outputs finished creative work (prompt/copy/strategy)
- does NOT expose technique names unless user asks

Implementation approach:
- Keep the technique library as an internal section in the SKILL.md (“Internal method / hidden by default”).
- Public outputs contain only the finished draft + minimal assumptions (if needed).

---

## Common Failures and Fixes

### 1) Cron job ran but didn’t message WhatsApp
Symptom:
- cron `status: ok` but `deliveryStatus: not-requested`

Fix:
- change cron payload to `agentTurn` + `delivery.mode=announce` targeting WhatsApp.

### 2) NotebookLM runner crashed on missing prompt file (p09.txt)
Symptom:
- `ERROR: missing prompt file: .../p09.txt`

Fix:
- patch runner to build plan from existing `pNN.txt` files (glob + numeric sort).

### 3) Gap analysis polluted by NotebookLM UI entities
Symptom:
- entities like Reports/Infographic/Flashcards/Quiz/Mind Map/Data table

Fix:
- add UI noise stoplist in `gap_analysis.py` and filter entities/relations before KG build.

### 4) Cleaner extracted fake techniques (Name/Trigger/Timer/...)
Symptom:
- `## Name` etc with missing fields

Fix:
- add `NAME_STOPLIST` and ensure the parser supports heading blocks + `**Field:**` style.

### 5) Skill validator failing on required sections
Symptom:
- missing_required_section:* errors

Fix:
- ensure headings are capitalised exactly as validator expects.
- acceptance tests must include **numbered items** (`1.`) not just code-fence comments.

---

## Full Example Run (creativity-toolkit-v3)

> Replace `<NOTEBOOKLM_URL>` and `<skill>` as needed.

```bash
# Setup
cd ~/clawd
mkdir -p tmp/research-to-skill/creativity-toolkit-v3/{pass1,gaps,pass2,synthesis}

# Phase 1: baseline extraction
/opt/anaconda3/bin/python3 skills/notebooklm-runner/scripts/run_notebooklm_runner.py \
  --notebook-url "<NOTEBOOKLM_URL>" \
  --prompts-dir "$HOME/clawd/tmp/research-to-skill/creativity-toolkit-v3/pass1" \
  --runs-dir   "$HOME/clawd/tmp/research-to-skill/creativity-toolkit-v3/pass1" \
  --progress-file "$HOME/clawd/tmp/research-to-skill/creativity-toolkit-v3/pass1/progress.md" \
  --final-summary "$HOME/clawd/tmp/research-to-skill/creativity-toolkit-v3/pass1/summary.md" \
  --max-checks 3600 --sleep-seconds 2.0

# Phase 1.5: clean pass1
python3 tools/clean_summary.py \
  --input  tmp/research-to-skill/creativity-toolkit-v3/pass1/summary.md \
  --output tmp/research-to-skill/creativity-toolkit-v3/pass1/clean-summary.md

# Phase 2: gap analysis
rm -rf rag_storage
/opt/anaconda3/bin/python3 tools/gap_analysis.py \
  --input-dir tmp/research-to-skill/creativity-toolkit-v3/pass1 \
  --output-file tmp/research-to-skill/creativity-toolkit-v3/gaps/gap-prompts.md

# Phase 3: deep extraction
/opt/anaconda3/bin/python3 skills/notebooklm-runner/scripts/run_notebooklm_runner.py \
  --notebook-url "<NOTEBOOKLM_URL>" \
  --prompts-dir "$HOME/clawd/tmp/research-to-skill/creativity-toolkit-v3/gaps" \
  --runs-dir   "$HOME/clawd/tmp/research-to-skill/creativity-toolkit-v3/pass2" \
  --progress-file "$HOME/clawd/tmp/research-to-skill/creativity-toolkit-v3/pass2/progress.md" \
  --final-summary "$HOME/clawd/tmp/research-to-skill/creativity-toolkit-v3/pass2/summary.md" \
  --max-checks 3600 --sleep-seconds 2.0

# Phase 4: synthesis
mkdir -p tmp/research-to-skill/creativity-toolkit-v3/synthesis
/opt/anaconda3/bin/python3 - <<'PY'
import os
out=[]
clean='tmp/research-to-skill/creativity-toolkit-v3/pass1/clean-summary.md'
out.append('# PASS 1 — BASELINE TECHNIQUES\n')
out.append(open(clean,encoding='utf-8',errors='replace').read())
pass2='tmp/research-to-skill/creativity-toolkit-v3/pass2'
out.append('\n# PASS 2 — GAP ANALYSIS RESPONSES\n')
for f in sorted(os.listdir(pass2)):
    if f.endswith('.response.txt'):
        out.append(f'\n### {f}\n')
        out.append(open(os.path.join(pass2,f),encoding='utf-8',errors='replace').read())
open('tmp/research-to-skill/creativity-toolkit-v3/synthesis/enriched-summary.md','w',encoding='utf-8').write('\n'.join(out))
print('Done')
PY

# Phase 4.5: clean synthesis
python3 tools/clean_summary.py \
  --input  tmp/research-to-skill/creativity-toolkit-v3/synthesis/enriched-summary.md \
  --output tmp/research-to-skill/creativity-toolkit-v3/synthesis/enriched-summary.clean.md

# Phase 5: build SKILL.md (manual or agent), then validate
/opt/anaconda3/bin/python3 skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  skills/creativity-toolkit-v3/SKILL.md
```
