---
name: notebooklm-runner
description: "# notebooklm-runner"
---

# notebooklm-runner

Goal: run the full NotebookLM prompt suite (1–17) reliably and produce a clean final summary file.

This skill is an **orchestrator** that depends on two other skills’ scripts:
- `skills/notebooklm-fetcher/scripts/fetch_clipboard.py`
- `skills/notebooklm-processor/scripts/process_runs.py`

## Toolset

- `read`
- `write`
- `edit`
- `exec`

## Use

Run the orchestration script:

```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/notebooklm-runner/scripts/run_notebooklm_runner.py \
  --notebook-url "https://notebooklm.google.com/notebook/<NOTEBOOK_ID>" \
  --prompts-dir "/Users/igorsilva/clawd/tmp/notebooklm-prompts" \
  --runs-dir "/Users/igorsilva/clawd/tmp/notebooklm-runs" \
  --progress-file "/Users/igorsilva/clawd/tmp/notebooklm-progress.md" \
  --final-summary "/Users/igorsilva/clawd/tmp/notebooklm-final-summary.md"
```

Notes:
- The runner expects `p01.txt … p17.txt` in `--prompts-dir` (aligned to `/Users/igorsilva/clawd/tmp/notebooklm-prompts.md`, which should match the v2 prompt library).

Notes:
- The fetcher clears chat **best-effort**; the copy-button selection is **anchored to the current prompt**.
- The processor is run after each prompt to keep progress current.

## Inputs

- `--notebook-url` (required): NotebookLM notebook URL.
- `--prompts-dir` (required): directory containing `p01.txt` … `p17.txt`.
- `--runs-dir` (required): output directory for NotebookLM run artifacts.
- `--progress-file` (required): path to `notebooklm-progress.md`.
- `--final-summary` (required): path to `notebooklm-final-summary.md`.

## Outputs

- Artifacts per prompt run under `--runs-dir`:
  - `*.prompt.txt`
  - `*.response.txt` (clipboard-captured)
  - `*.meta.json`, `*.snapshot.json`, `*.screenshot.png` (debug)
- Rewritten progress markdown:
  - `--progress-file` (default: `/Users/igorsilva/clawd/tmp/notebooklm-progress.md`)
- Final summary markdown:
  - `--final-summary` (default: `/Users/igorsilva/clawd/tmp/notebooklm-final-summary.md`)

## Failure modes / Hard blockers

Hard-stop failures (priority HIGH):
- Tandem not running / unreachable (`127.0.0.1:8765`) → fetcher returns `blocked`; runner stops.
- Processor fails to parse runs directory → runner stops and prints the exact error.

Partial/blocked states (priority MEDIUM):
- NotebookLM UI changes (selectors not found / copy button not found) → fetcher returns `partial`; runner stops.
- Clipboard capture returns sentinel/empty repeatedly → fetcher returns `partial`; runner stops.

### Structured failure logging (ERR entries)

On any hard-stop failure or partial/blocked stop, append one structured entry to:
- `/Users/igorsilva/clawd/.learnings/ERRORS.md`

ID format:
- `ERR-YYYYMMDD-XXX` (XXX is a zero-padded counter starting at 001 per day)

Priority mapping:
- Hard-stop failure → `priority: high`
- Partial/blocked stop → `priority: medium`

Entry fields (consistent schema):
- `stage:` `notebooklm-runner`
- `priority:` `high|medium`
- `status:` `hard_stop|partial|blocked`
- `reason:` one-line reason (use the concrete failure condition)
- `suggested_fix:` one line
- `context:`
  - `notebook_url:` value passed to the runner (or `unknown`)
  - `prompts_dir:`
  - `runs_dir:`
  - `progress_file:`
  - `final_summary:`
  - `failed_prompt_number:` if known; else `unknown`

Do not include any clipboard contents or large NotebookLM outputs in the ERR entry.

## Acceptance tests

1. **Behavioral: happy path**
   - Run: `/notebooklm-runner <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/notebooklm-runner <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/notebooklm-runner/SKILL.md
```
Expected: `PASS`.

4. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/notebooklm-runner/SKILL.md
```
Expected: `PASS`.
