# NotebookLM as a Document — how to use it like a reliable “source of truth”

This is the operational workflow for using **NotebookLM** as a *document*, not a chat toy.

Goal: create a repeatable process where NotebookLM outputs are **captured, versioned, and re-usable** (prompts → responses → synthesis), with minimal UI drift risk.

## Principles

1) **Treat NotebookLM as a read-only reasoning layer over fixed sources**
- NotebookLM answers from your uploaded sources. Your job is to: (a) keep sources stable, (b) ask structured questions, (c) capture outputs deterministically.

2) **Everything important becomes a file**
- Prompts live in `p01.txt…p17.txt`
- Responses are saved as `*.response.txt`
- The run writes a progress ledger (`progress.md`) and a top-level summary (`summary.md`).

3) **Use micro-protocol prompts**
- Avoid prompts that drift into theory.
- Prefer prompts that force an output structure: **steps, timers, templates, failure modes**.

4) **Run IDs are your audit trail**
- Each prompt run produces `run_id` + snapshot + screenshot.
- Debugging is always: open the latest `.snapshot.json` and `.meta.json`.

---

## Folder layout (recommended)

For a skill/pipeline run named `<skill-name>`:

- Prompts:
  - `~/clawd/tmp/skill-forge/<skill-name>/prompts/`
    - `p01.txt … p17.txt`

- Baseline extraction (pass 1):
  - `~/clawd/tmp/research-to-skill/<skill-name>/pass1/`
    - `*.prompt.txt` / `*.response.txt` / `*.snapshot.json` / `*.screenshot.png` / `*.meta.json`
    - `progress.md`
    - `summary.md`

- Gap prompts:
  - `~/clawd/tmp/research-to-skill/<skill-name>/gaps/`

- Deep extraction (pass 2):
  - `~/clawd/tmp/research-to-skill/<skill-name>/pass2/`

- Synthesis:
  - `~/clawd/tmp/research-to-skill/<skill-name>/synthesis/enriched-summary.md`

---

## Prompting workflow (how to write prompts that behave)

### A) Use a goal that doesn’t force repetition
Bad goal pattern:
- includes a long list of example tasks (the model will echo them in every prompt)

Good goal pattern:
- a single constraint that forces reusable output.

Example goal:
> Give me reusable creativity micro-protocols I can apply to any task right now. Output steps, timers, templates, and failure-mode fixes. Avoid task-specific examples unless asked.

### B) Enforce an output schema in the prompt
Use language like:
- “Return as: **Protocol name / Timer / Steps / Template / Failure-mode fix**”
- “If you can’t cite sources, say so.”

### C) Keep the first line anchor stable
Automation and extraction often anchor on the first line of the prompt.
- Keep it short and unique.
- Avoid leading whitespace.

---

## Running extraction (baseline pass)

### One-prompt sanity test (recommended)
Before running a full suite, run prompt 01 only and ensure:
- it produces a non-empty `*.response.txt`
- `meta.json` shows `status: ok, partial: false`

### Full pass (1..17)
Use the runner:

```bash
/opt/anaconda3/bin/python3 ~/clawd/skills/notebooklm-runner/scripts/run_notebooklm_runner.py \
  --notebook-url "<notebook-url>" \
  --prompts-dir "<prompts-dir>" \
  --runs-dir "~/clawd/tmp/research-to-skill/<skill-name>/pass1" \
  --progress-file "~/clawd/tmp/research-to-skill/<skill-name>/pass1/progress.md" \
  --final-summary "~/clawd/tmp/research-to-skill/<skill-name>/pass1/summary.md" \
  --max-checks 1800 \
  --sleep-seconds 2.0
```

### What “done” looks like
- `progress.md` shows:
  - `OK: [1..17]`
  - `Partial: []`
  - `Missing: []`
- `summary.md` exists and lists all prompts and run IDs.

---

## Debugging playbook (when NotebookLM “does nothing”)

### 1) Check Tandem health
- If Tandem is unreachable, automation cannot proceed.
- Symptom: curl snapshot fails / connection refused.

### 2) Check UI state via snapshot
Look for:
- **Home state:** `Studio output will be saved here`
- No transcript messages

If home state persists:
- refresh (navigate to same notebook URL)
- retry submission once

### 3) When copy button doesn’t appear
- Don’t assume generation failed.
- Check snapshot for:
  - `Save message to a note`
  - `Copy model response to clipboard`
  - response StaticText lines

### 4) Capture artifacts
Always keep:
- `.snapshot.json`
- `.screenshot.png`
- `.meta.json`

These let you diff working vs failing runs.

---

## Turning NotebookLM output into a “document”

### A) Progress ledger (`progress.md`)
- This is the canonical run ledger.
- It contains per-prompt status and raw extraction.

### B) Final summary (`summary.md`)
- Quick index: prompt statuses, run ids, previews.
- Use this for “what happened” and audit.

### C) Enriched summary (`enriched-summary.md`)
Merge pass1 + pass2 responses into a single working document.
This becomes the input to skill building / writing.

---

## Operational recommendation

Use NotebookLM as a *document system* by committing to:
- Stable prompt sets
- File-based outputs
- A progress ledger + summary
- Deterministic reruns

When it works, you can treat the outputs as a versioned research corpus, not chat history.
