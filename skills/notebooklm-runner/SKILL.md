---
name: notebooklm-runner
description: Orchestrate the full NotebookLM research flow end-to-end (clear chat, run prompts 1–17 via notebooklm-fetcher, run notebooklm-processor after each prompt, and write a final summary). Triggers: "run notebooklm", "run notebooklm prompts", "notebooklm runner", "orchestrate notebooklm research", "generate notebooklm final summary".
---

# notebooklm-runner

Goal: run the full NotebookLM prompt suite (1–17) reliably and produce a clean final summary file.

This skill is an **orchestrator** that depends on two other skills’ scripts:
- `skills/notebooklm-fetcher/scripts/fetch_clipboard.py`
- `skills/notebooklm-processor/scripts/process_runs.py`

## Toolset

- `exec` — run the runner script and validations
- `read` — read prompt files / progress / outputs
- `write` — write the final summary markdown

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

- Tandem not running / unreachable (`127.0.0.1:8765`) → fetcher returns blocked.
- NotebookLM UI changes (selectors not found / copy button not found) → fetcher returns partial; runner stops.
- Clipboard capture returns sentinel/empty repeatedly → fetcher returns partial; runner stops.
- Processor fails to parse runs directory → runner stops and prints the exact error.

## Acceptance tests

1. **Frontmatter + section compliance**
   ```bash
   /opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
     /Users/igorsilva/clawd/skills/notebooklm-runner/SKILL.md
   ```

2. **No invented tools in Toolset**
   ```bash
   /opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
     /Users/igorsilva/clawd/skills/notebooklm-runner/SKILL.md
   ```

3. **Behavioral: dry-run prompt plan includes 17 prompts**
   - Run: `/notebooklm-runner --dry-run`
   - Expected: prints a plan covering prompts `01` through `17` and exits cleanly.

4. **Dry-run mapping sanity** (no Tandem call)
   ```bash
   /opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/notebooklm-runner/scripts/run_notebooklm_runner.py \
     --notebook-url "https://notebooklm.google.com/notebook/TEST" \
     --prompts-dir "/Users/igorsilva/clawd/tmp/notebooklm-prompts" \
     --runs-dir "/Users/igorsilva/clawd/tmp/notebooklm-runs" \
     --progress-file "/Users/igorsilva/clawd/tmp/notebooklm-progress.md" \
     --final-summary "/Users/igorsilva/clawd/tmp/notebooklm-final-summary.md" \
     --dry-run
   ```
   Expected: prints the prompt plan (1–17) and exits 0.
