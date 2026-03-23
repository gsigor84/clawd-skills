---
name: notebooklm-processor
description: Process saved NotebookLM run artifacts (prompt.txt + snapshot.json + meta.json + screenshot.png) from /Users/igorsilva/clawd/tmp/notebooklm-runs/ without using Tandem/browser. Use when you need to: (1) scan NotebookLM runs, (2) select the latest successful run per prompt number, (3) extract the assistant’s raw response text from snapshot.json, (4) extract insights relevant to building an AI agent that creates SKILL.md files, and (5) rewrite /Users/igorsilva/clawd/tmp/notebooklm-progress.md from scratch each run.
---

# notebooklm-processor

Goal: **turn raw NotebookLM artifacts into an always-up-to-date progress file**.

- No Tandem calls
- No browser automation
- Reads files from disk, writes progress to disk

## Use

```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/notebooklm-processor/scripts/process_runs.py \
  --runs-dir "/Users/igorsilva/clawd/tmp/notebooklm-runs" \
  --progress-file "/Users/igorsilva/clawd/tmp/notebooklm-progress.md"
```

## Selection rules (pick latest per prompt)

- Group by `meta.prompt_number`.
- Prefer latest `status=ok`, else latest `status=partial`, else skip.
- “Latest” uses `meta.created_at` (fallback: timestamp in filename).

## Deterministic extraction rules (from snapshot.json)

- Load `snapshot.json`, read `snapshot` string.
- Find the prompt text (from `prompt.txt`) inside a `StaticText "..."` line.
  - If exact match fails, fall back to the first 80 chars with whitespace collapsed.
- Collect subsequent `StaticText` lines until the next `textbox "Query box"`.
- De-dup consecutive duplicates.
- Strip UI noise.

## Insight extraction (goal-focused)

Extract only what helps build an agent that generates **valid OpenClaw `SKILL.md` files**:
- agent/platform primitives: tools, memory, context engineering (RAG), MCP
- reliability/safety practices + failure modes
- orchestration patterns: critique loops, multi-agent roles
- autonomy vs constrained/graph workflows
- benchmarks/acceptance criteria

## Output

Rewrites from scratch on every run:
- `/Users/igorsilva/clawd/tmp/notebooklm-progress.md`

Includes:
- Status summary
- Prompt 1–14 sections (selected run_id + ok/partial + extracted raw + insights)
- Cross-prompt synthesis for the SKILL.md-agent build

## Must-pass tests

1) With one ok + one partial prompt, writes both; ok chosen correctly.
2) With two runs for same prompt_number, newest ok chosen by created_at.
3) If prompt not found verbatim, snippet fallback works or explicitly flags extraction failure.

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
   - Run: `/notebooklm-processor <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/notebooklm-processor <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/notebooklm-processor/SKILL.md
```
Expected: `PASS`.
