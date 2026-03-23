---
name: summarize
description: "Summarize a URL, local text file, YouTube link, or pasted text into a consistent Markdown brief."
---

## Summarize

A deterministic summarization skill for OpenClaw.

## Trigger contract

Activate this skill when the user message matches any of these patterns:

1) Slash command
- `/summarize <input>`

2) Natural language
- "summarize <input>"
- "summarise <input>"
- "tl;dr <input>"

### Input typing rules (must be applied in this order)

Given the `<input>` string (after stripping surrounding quotes):

1) **URL** if it matches `^https?://`.
2) **YouTube link** if URL host contains any of:
   - `youtube.com`
   - `youtu.be`
3) **Local file path** if it matches either:
   - absolute mac/linux path: starts with `/`
   - home path: starts with `~/`
4) **Raw text** otherwise (treat the remainder as the content to summarize).

If the message contains **no `<input>`** after the trigger phrase/command, the skill must fail with the exact error in Failure modes.

## Deterministic agent workflow

Follow these steps exactly. Do not skip branches.

### Step 0 — Confirm privacy boundary (only when needed)

- If the input type is **Local file path**: the agent will read local disk content.
- If the input type is **URL / YouTube link**: the agent will fetch remote content.

Proceed without asking only if the user’s message already implies consent (e.g. they explicitly asked to summarize a specific path/URL).

### Step 1 — Acquire source text

#### Branch A — URL (non-YouTube)
1) Use `web_fetch` with the URL.
   - `extractMode: "markdown"`
   - If `web_fetch` fails or returns empty content → Failure modes.
2) Set `SOURCE_TITLE` = the URL.
3) Set `SOURCE_TEXT` = fetched content.

#### Branch B — YouTube link
1) Use `web_fetch` on the YouTube URL with `extractMode: "markdown"`.
2) If the fetched content does **not** include a transcript or substantial body text (heuristic: < 1500 characters of non-boilerplate text), do **not** hallucinate a transcript.
   - Output must explicitly state: "No transcript available via web_fetch; paste the transcript or a notes doc to summarize." (see Outputs).
3) Set `SOURCE_TITLE` = the YouTube URL.
4) Set `SOURCE_TEXT` = fetched content (even if partial) and continue to Step 2.

#### Branch C — Local file path
1) Safety check the path (see Boundary rules). If disallowed → Failure modes.
2) Use `read` on the path.
   - If read fails (missing file/permission) → Failure modes.
3) Set `SOURCE_TITLE` = the file path.
4) Set `SOURCE_TEXT` = file contents.

#### Branch D — Raw text
1) Set `SOURCE_TITLE` = "pasted text".
2) Set `SOURCE_TEXT` = the raw text.

### Step 2 — Summarize (single-pass)

Produce the summary directly (no extra tool calls required):

- Compress aggressively.
- Do not invent facts.
- If the source is thin/boilerplate/marketing, say so.
- If YouTube content lacks transcript, treat it as metadata/description only.

### Step 3 — Emit standardized output

Return output using the exact format in Outputs.

## Boundary rules

### Privacy / consent
- **Never** summarize local content that appears sensitive without explicit confirmation.
  - Sensitive indicators include (non-exhaustive): `~/.ssh`, `~/.aws`, `~/.gnupg`, `.env`, `id_rsa`, `key`, `token`, `password`, `wallet`, `seed`, `mnemonic`.
- If the user provides a path/URL explicitly and requests a summary, treat that as consent to fetch/read it.

### Disallowed local paths (hard block)
Refuse to read any local file path under:
- `~/.ssh/`
- `~/.aws/`
- `~/.gnupg/`
- any `.env` file
- any path containing `/Library/Keychains/`

### Allowed local file types
- Only summarize plain-text formats:
  - `.txt`, `.md`, `.json`, `.csv`, `.log`
- Refuse binary/large formats (e.g., `.pdf`, `.docx`, images, audio/video) unless the user converts to text first.

### Caps (fetch/compute)
- For `web_fetch`: at most **1 fetch** per request.
- Summaries must be **<= 2500 characters** unless the user explicitly asks for a long summary.

## Use

Use this skill to turn a URL, local text file, YouTube link, or pasted text into a consistent, decision-ready brief (what it says, what matters, and what’s missing) while staying within strict privacy and non-hallucination boundaries.

## Inputs

One of:

1) URL
- `/summarize https://example.com/article`

2) Local text file path (allowed extensions only)
- `/summarize /Users/igorsilva/clawd/notes.md`

3) YouTube link
- `/summarize https://www.youtube.com/watch?v=...`

4) Raw text
- `/summarize <paste text here>`

## Outputs

Return Markdown with this exact skeleton:

- `Source: <SOURCE_TITLE>`
- `Summary (3–6 bullets):`
  - bullets
- `Key points:`
  - bullets
- `Caveats / Unknowns:`
  - bullets

If input is YouTube and transcript is not available via `web_fetch`, also include this line at the top:
- `Note: No transcript available via web_fetch; paste the transcript (or a notes doc) for a real content summary.`

## Failure modes

- **Missing input**: If the user triggers summarize without an argument, reply exactly:
  - `ERROR: missing input. Usage: /summarize <url|file-path|youtube-link|text>`

- **Disallowed/sensitive path**: If the local path is disallowed or appears sensitive, reply exactly:
  - `ERROR: refused to read sensitive path. Paste the text you want summarized instead.`

- **Unsupported file type**: If the local file extension is not in the allowed list, reply exactly:
  - `ERROR: unsupported file type. Provide a .txt/.md/.json/.csv/.log file or paste the text.`

- **Read failed**: If `read` fails, reply exactly:
  - `ERROR: could not read file (missing or permission denied).`

- **Fetch failed**: If `web_fetch` fails or returns empty content, reply exactly:
  - `ERROR: could not fetch content from URL.`

## Toolset

- `read`
- `web_fetch`

## Acceptance tests

1. **URL: basic article summary**
   - Run: `/summarize https://example.com/`
   - Expected: exactly one `web_fetch` call; output includes `Source: https://example.com/` and the 3 required sections (Summary/Key points/Caveats).

2. **Local file: allowed extension**
   - Run: `/summarize /Users/igorsilva/clawd/MEMORY.md`
   - Expected: uses `read` (not `web_fetch`); output uses the required Markdown skeleton and does not invent facts.

3. **YouTube link: no transcript available**
   - Run: `/summarize https://youtu.be/dQw4w9WgXcQ`
   - Expected: uses `web_fetch` once; output includes the `Note: No transcript available via web_fetch...` line OR (if transcript is present) clearly cites that it summarized transcript text.

4. **Missing input**
   - Run: `/summarize`
   - Expected: replies exactly `ERROR: missing input. Usage: /summarize <url|file-path|youtube-link|text>` and stops.

5. **Sensitive path refusal**
   - Run: `/summarize ~/.ssh/id_rsa`
   - Expected: replies exactly `ERROR: refused to read sensitive path. Paste the text you want summarized instead.` and stops.

6. **Unsupported file type refusal**
   - Run: `/summarize /Users/igorsilva/clawd/some.pdf`
   - Expected: replies exactly `ERROR: unsupported file type. Provide a .txt/.md/.json/.csv/.log file or paste the text.` and stops.

7. **Fetch failure**
   - Run: `/summarize https://this-domain-should-not-exist.example.invalid/`
   - Expected: replies exactly `ERROR: could not fetch content from URL.`

8. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/summarize/SKILL.md
```
Expected: `PASS`.

9. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/summarize/SKILL.md
```
Expected: `PASS`.
