---
name: file-summarizer
description: "Trigger: /file-summarizer <absolute-file-path>. Read a local .txt file and output a 3–5 sentence summary plus key topics."
---

# file-summarizer

## Use

Summarize a local **.txt** file into **3–5 sentences** and list the **key topics**.

### Trigger
- `/file-summarizer <absolute-file-path>`

### Steps

#### STEP 1 — Validate input
1) Confirm `<absolute-file-path>` exists and is readable.
   - If not, output exactly and **Then stop.**
     ❌ File not found: <path>
     💡 Check the path is correct and the file exists.
2) Confirm file extension is `.txt`.
   - If not, output exactly and **Then stop.**
     ❌ This skill only supports .txt files. Got: <extension>
     💡 Convert your file to .txt first, then re-run.

#### STEP 2 — Read source
Use `read` to load the full file.

#### STEP 3 — Produce summary
- Output a 3–5 sentence summary grounded in the text.
- Then output `Key topics:` followed by 3–8 bullets.
- Do not invent facts; if the text is too thin, state that explicitly in the summary.

## Inputs

- `absolute-file-path` (required)
  - Must be an absolute path to a readable `.txt` file.

## Outputs

### Success
Output exactly:
- `Summary:` then 3–5 sentences.
- `Key topics:` then 3–8 bullets.

### Errors (exact strings)
- Missing/unreadable file:
  - `❌ File not found: <path>`
  - `💡 Check the path is correct and the file exists.`
- Wrong extension:
  - `❌ This skill only supports .txt files. Got: <extension>`
  - `💡 Convert your file to .txt first, then re-run.`

## Failure modes

### Musts
- Return 3–5 sentences.
- Include a short list of key topics.
- If the file is missing/unreadable, return the exact error output.
- Single-turn: read → summarize → output.

### Must-nots
- Do not use web tools.
- Do not write any files.
- Do not run exec/process.
- Do not invent details not present in the text.

### Preferences
- Prefer plain language over jargon.
- Prefer concrete nouns/verbs over abstract phrasing.
- If the text is long, summarize the central thesis + 2–4 main supporting points.

### Escalation triggers
- If the user asks for summarization of non-text (pdf/image/audio) → ask for a .txt export.

## Toolset

- `read`

## Acceptance tests

1. **Behavioral: missing file**
   - Run: `/file-summarizer /path/does/not/exist.txt`
   - Expected: exactly the 2-line file-not-found error.

2. **Behavioral: wrong extension**
   - Run: `/file-summarizer /abs/path/to/file.pdf`
   - Expected: exactly the 2-line wrong-extension error.

3. **Behavioral: output shape**
   - Run: `/file-summarizer /abs/path/to/file.txt`
   - Expected:
     - Starts with `Summary:`
     - Contains 3–5 sentences
     - Contains `Key topics:` followed by 3–8 bullets

4. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py   /Users/igorsilva/clawd/skills/file-summarizer/SKILL.md
```
Expected: `PASS`.

5. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py   /Users/igorsilva/clawd/skills/file-summarizer/SKILL.md
```
Expected: `PASS`.

## References (retrieved patterns)

Closest skills used as pattern references:
- /Users/igorsilva/clawd/skills/url-arg-summarizer/SKILL.md
- /Users/igorsilva/clawd/skills/evidence-extractor/SKILL.md
- /Users/igorsilva/clawd/skills/learn-augment/SKILL.md
