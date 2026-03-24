---
name: promote-learnings
description: "Trigger: /promote-learnings. Run the local tools/promote_learnings.py script and print its output."
---

## Purpose

Run the repository script `tools/promote_learnings.py` and return its stdout/stderr so Igor can confirm it runs cleanly.

## Inputs

- None.

## Outputs

- Prints the script output verbatim.

## Steps

1. Exec:
   ```bash
   cd /Users/igorsilva/clawd && /opt/anaconda3/bin/python3 tools/promote_learnings.py
   ```
2. Return the full output (including any errors) exactly as produced.

## Failure modes

- If the script path is missing: report the filesystem error.
- If Python errors: return the traceback.

## Agent Loop Contract (agentic skills only)

- This is a single-shot utility skill. Do not loop or iterate.

## Anti-hallucination / context discipline

- Do not claim proposals exist unless they appear in the script output.
- Do not infer or summarise results beyond what the script prints.
