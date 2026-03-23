---
name: notebooklm-fetcher
description: Fetch-and-save only skill for NotebookLM via Tandem. Use when you need to send ONE prompt to a specific NotebookLM notebook, wait for the response to finish generating, and save raw artifacts to disk for later processing. **Preferred (v2) path uses the UI Copy button + clipboard capture** (prompt.txt + response.txt). Legacy (v1) path saves snapshot.json + screenshot.png. Triggers: “fetch NotebookLM prompt”, “run Prompt N”, “save raw NotebookLM response”, “NotebookLM fetcher”, “Tandem NotebookLM”.
---

# notebooklm-fetcher

Goal: **send exactly one prompt to NotebookLM** (through Tandem at `127.0.0.1:8765`) and **save raw artifacts**.

- No synthesis
- No summarization
- No progress updates

## Use

Run the preferred clipboard-based script (v2):

```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/notebooklm-fetcher/scripts/fetch_clipboard.py \
  --prompt-number 3 \
  --prompt-name "concept-connection-mapper" \
  --prompt-text "...full prompt..." \
  --notebook-url "https://notebooklm.google.com/notebook/..." \
  --outdir "/Users/igorsilva/clawd/tmp/notebooklm-runs"
```

Notes:
- `--notebook-url` is optional. If omitted, the script will use the current Tandem tab.
- Artifacts per run (v2): `prompt.txt`, `response.txt`, plus debug `snapshot.json`, `screenshot.png`, `meta.json`.

## Output directory + idempotent naming

Default output directory:
- `/Users/igorsilva/clawd/tmp/notebooklm-runs/`

Run id format:
- `YYYYMMDD-HHMM_prompt-NN_<slug>`

Idempotency rule:
- If any artifact path already exists, the run id gets a suffix: `-r02`, `-r03`, ...

## Completion heuristic (v2)

The script loops:
- wait → snapshot → locate the **prompt anchor** (first line of the prompt in `StaticText`)
- then locate the first **"Copy model response to clipboard"** button **after that anchor**

Completion signal:
- a **Copy response** button associated with the current prompt is present **and stable** across 2 checks
- clipboard capture is validated by writing a **sentinel** to the clipboard first and requiring the copied text to differ (prevents re-saving stale clipboard)

If max checks reached without seeing the anchored Copy button → mark `partial=true` in meta.
If clipboard stays at sentinel/empty after retries → mark `partial=true` in meta.

## Hard blockers

The script stops and writes `meta.json` with `status=blocked` if:
- Tandem is unreachable
- Query box or Submit button selector cannot be found in the snapshot
- click/type consistently fails (>=3 tries)

## Legacy script

The older script is still present for debugging/back-compat:
- `scripts/fetch_one.py`

## Non-goals
- Do not interpret NotebookLM content
- Do not update `notebooklm-progress.md`
- Do not run multiple prompts per invocation

## Inputs

- Describe required inputs.

## Outputs

- Describe outputs and formats.

## Failure modes

- List hard blockers and expected exact error strings when applicable.

## Toolset

- `read`
- `write`
- `edit`
- `exec`

## Acceptance tests

1. **Behavioral: happy path**
   - Run: `/notebooklm-fetcher <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/notebooklm-fetcher <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/notebooklm-fetcher/SKILL.md
```
Expected: `PASS`.
