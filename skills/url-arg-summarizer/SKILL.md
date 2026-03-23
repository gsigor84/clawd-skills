---
name: url-arg-summarizer
description: Summarise a webpage URL into key points, extract the main argument, include supporting quotes, and list caveats/unknowns (optionally focusing on user instructions).
---

# URL Argument Summarizer

## Trigger
User types:

- `/sumurl <url> [optional instructions]`

Examples:
- `/sumurl https://example.com/article`
- `/sumurl https://example.com/report focus on assumptions and evidence`

## Goal
Given a webpage URL (plus optional focus instructions), return:
1) 5–10 key-point bullets
2) 2–3 sentence statement of the main argument
3) 3 supporting verbatim quotes (with section/heading context if available)
4) Caveats/unknowns bullet list

Target length: ~300 words (quotes should be short excerpts).

## Tools
- Prefer `web_fetch` (markdown extraction) first.
- If `web_fetch` fails, returns empty/very short content, or page is JS-rendered/paywalled, fall back to `browser` to capture the readable content.
- **No KB / DDG cross-checking by default.** Only do that if the user explicitly asks.

## Workflow

### 1) Parse input
- Extract the first http/https URL.
- Everything after the URL is `focus_instructions` (may be empty).
- If URL is missing/invalid, ask the user for a valid http/https URL.

### 2) Fetch content (primary)
Use `web_fetch`:
- `extractMode=markdown`
- `maxChars` high enough to capture the article (e.g., 120000)

If the extracted content is:
- empty,
- obviously navigation-only,
- extremely short relative to the page,
- or indicates blocking/paywall,
then do the fallback.

### 3) Fallback (browser snapshot)
Use `browser`:
- `open` the URL
- `snapshot` the page (prefer `refs="aria"` if interacting)

Then:
- Prefer to capture the main article text (not header/footer/comments).
- If needed, scroll and snapshot again to capture missing sections.

### 4) Produce the response (structured)
Write the output in this exact order and headings:

**KEY POINTS**
- 5–10 bullets. Prefer concrete claims, numbers, named entities, and causal statements.
- If `focus_instructions` exist, prioritize points relevant to them.

**MAIN ARGUMENT**
- 2–3 sentences answering: what is the author trying to convince you of, and why?
- If the page does not present an argument (directory/listing/reference/product page), say so and state the page’s central purpose instead.

**SUPPORTING QUOTES**
- 3 short verbatim excerpts.
- For each quote include:
  - `Quote:` “...”
  - `Where:` section heading / subheading / identifiable page location if available

**CAVEATS / UNKNOWNS**
- Bullets for: missing access (paywall), incomplete extraction, ambiguous claims, lack of evidence, potential bias, unknown data sources, or parts not captured.

### 5) Quality rules
- **Context-only:** treat the fetched page content as the only allowed source. Do not add outside facts or “common knowledge”.
- Clearly separate **claims** vs **evidence** when possible.
- Do not invent facts not in the page.
- **Negative rejection (no guessing):** if the page content is too incomplete to support KEY POINTS / MAIN ARGUMENT / 3 QUOTES, do partial completion and put the missing parts explicitly under **CAVEATS / UNKNOWNS** rather than guessing.
- Keep within ~300 words excluding the quotes if necessary; if you exceed, shorten KEY POINTS first.

## Failure modes
- If content is inaccessible: explain what you could access and put the rest under **CAVEATS / UNKNOWNS**.
- If multiple URLs provided: ask which single URL to summarise unless the user explicitly asks for comparison.

## Use

Describe what the skill does and when to use it.

## Inputs

- Describe required inputs.

## Outputs

- Describe outputs and formats.

## Toolset

- `read`
- `write`
- `edit`
- `exec`

## Acceptance tests

1. **Behavioral: happy path**
   - Run: `/url-arg-summarizer <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/url-arg-summarizer <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/url-arg-summarizer/SKILL.md
```
Expected: `PASS`.
