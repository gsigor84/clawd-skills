---
name: auto-extract-v4
description: "Trigger: /auto-extract-v4 <absolute-file-path> [--save]. Read a local .txt file, extract up to 15 concepts, and output exactly one fenced JSON array (clawd.learn.concept.v1). Optional --save writes the same JSON array to ~/clawd/tmp/<topic-slug>.json."
---

# auto-extract-v4

## Use

Turn a local **.txt** file into **≤ 15** reusable, source-grounded concepts for ingestion via `/save-concepts`.

Hard output contract:
- Exactly **one** fenced ```json block
- Top-level value is a **JSON array**
- Each item is a `clawd.learn.concept.v1` object

### Triggers
- `/auto-extract-v4 <absolute-file-path>`
- `/auto-extract-v4 <absolute-file-path> --save`

### Execution recipe (single-turn)

#### STEP 1 — Validate input (hard-stops)
1) Path must be absolute.
2) File must exist and be readable.
   - If not, output exactly (two lines) and **Then stop.**
     ❌ File not found: <path>
     💡 Check the path is correct and the file exists. Use tab-completion or Finder to verify.
3) Extension must be `.txt`.
   - If not, output exactly (two lines) and **Then stop.**
     ❌ This skill only supports .txt files. Got: <extension>
     💡 Convert your file to .txt first, then re-run.

#### STEP 2 — Read source
Use `read` to load the full file contents.

#### STEP 3 — Conservative fluff filtering (keep-by-default)
Remove only sentences that match these boilerplate starts (case-insensitive):
- In this chapter
- In this section
- We will
- We begin
- We now
- Having established
- Having laid
- As mentioned
- This chapter
- This section
- In the next
- In previous chapters
- In prior chapters

Also remove “heading echo” sentences where a section heading is repeated verbatim as a full sentence.

Hard rule:
- If you’re unsure, **keep** the sentence.

#### STEP 4 — Detect content shape (decide extraction unit)
Decide content shape automatically — **never ask the user** which shape it is.

For each coherent chunk (paragraph cluster), decide the best extraction unit.

A) **Distinction / contrast**
- Signals: “X vs Y”, “X means… while Y means…”, “whereas”.
- Unit: 1 concept named `X vs Y (distinction)`.
- Edge case: if X and Y appear far apart, only pair if the source explicitly compares them.

B) **Definition list / glossary**
- Signals: repeated “X is …”, “X refers to …”, bullet definitions.
- Unit: 1 concept per definition.
- Edge case: if a definition depends on an immediately-adjacent prerequisite, you may mention it in `answer_p1`, but keep concepts separate unless inseparable.

C) **Procedure / steps**
- Signals: numbered steps, “first/then/finally”, checklists.
- Unit: 1 concept per step (merge only if the source treats multiple steps as one atomic move).
- Edge case: skip “repeat the previous step” filler steps.

D) **Named framework with components**
- Signals: “the X model has 4 parts…”.
- Unit: 1 concept per component **if explained**.
- Edge case: if components are listed but not explained, prefer 1 concept for the overall framework (avoid shallow stubs).

E) **Reframe / paradigm shift**
- Signals: “instead of X, think Y”, “move from X to Y”.
- Unit: 1 concept named `From X to Y (reframe)`.

Skip:
- pure previews/recaps (“this section will cover…”, “as discussed previously…”) unless it contains an actual definition/rule.

#### STEP 5 — Extract candidates (grounded)
A candidate is worth extracting if it answers at least one:
- What is X?
- How does X work?
- What is the difference between X and Y?
- What rule governs X?
- What are the steps of X?

Grounding rules:
- Never invent content not present in the source.
- `challenge_question` must be answerable from the file.
- `answer_p1` must be direct and derived from the file.
- `answer_p2` must be `null` unless the file **explicitly** connects it to another named concept that you also extracted.
- `backbone` must be `null`.

#### STEP 6 — Cap + select
- Hard cap: **15** concepts.
- If more than 15 candidates: pick the 15 most distinct and generally reusable; avoid near-duplicates.

#### STEP 7 — Derive topic slug (filename only)
From the input filename:
1) strip extension
2) strip leading `chapter_\d+_`, `ch_\d+_`, `part_\d+_`
3) lowercase
4) spaces/underscores → hyphens
5) strip chars not in `[a-z0-9-]`
6) collapse multiple hyphens
7) trim hyphens

#### STEP 8 — Format strict output
If 0 concepts extracted, output exactly (two lines) and **Then stop.**
❌ No extractable concepts found in <path>
💡 The file may be too short, too generic, or mostly boilerplate. Try a different chapter or section.

Otherwise output **exactly**:

Suggested slug: <topic-slug>
```json
[
  {
    "schema": "clawd.learn.concept.v1",
    "concept": "<name>",
    "index": 1,
    "challenge_question": "<tests understanding>",
    "answer_p1": "<core answer, direct>",
    "answer_p2": null,
    "backbone": null,
    "source": {
      "type": "auto-ingest-txt",
      "md_path": "<absolute path exactly as provided>",
      "source_title": "<topic-slug>",
      "generated_at_utc": "<UTC timestamp>"
    },
    "retrieval": {
      "keywords": [],
      "tags": ["auto-ingest", "concept"]
    }
  }
]
```
Extracted <N> concepts. Review above then run /save-concepts <slug> and paste this block.

If `--save` was present, append exactly these two lines after the summary line:
💾 Saved to ~/clawd/tmp/<topic-slug>.json
👉 Next step: /save-concepts <slug> --file ~/clawd/tmp/<slug>.json

#### STEP 9 — Optional save (--save)
If `--save` is present:
1) Attempt to `write` the JSON array to: `~/clawd/tmp/<topic-slug>.json`.
2) If the write fails due to missing/unwritable folder, output exactly (two lines) and **Then stop.**
   ❌ Could not save to ~/clawd/tmp/<slug>.json — folder may not exist.
   💡 Run: mkdir -p ~/clawd/tmp and try again.
3) If save succeeds: the file must contain only the JSON array (pretty-printed ok).

## Inputs

- `absolute-file-path` (required): absolute path to a readable `.txt` file.
- `--save` (optional): also write `~/clawd/tmp/<topic-slug>.json`.

## Outputs

### Success
- Wrapper lines + exactly one fenced ```json block containing a JSON array.
- `N <= 15`.

### Errors (exact strings)
- File missing/unreadable:
  - `❌ File not found: <path>`
  - `💡 Check the path is correct and the file exists. Use tab-completion or Finder to verify.`
- Wrong extension:
  - `❌ This skill only supports .txt files. Got: <extension>`
  - `💡 Convert your file to .txt first, then re-run.`
- Zero concepts:
  - `❌ No extractable concepts found in <path>`
  - `💡 The file may be too short, too generic, or mostly boilerplate. Try a different chapter or section.`
- Save failure (when `--save` present):
  - `❌ Could not save to ~/clawd/tmp/<slug>.json — folder may not exist.`
  - `💡 Run: mkdir -p ~/clawd/tmp and try again.`

## Failure modes

Hard blockers (stop immediately):
- File missing/unreadable
- Not a `.txt`
- Save requested but cannot write `~/clawd/tmp/<topic-slug>.json`

Soft blocker (deterministic error):
- Readable file but 0 concepts

## Toolset

No external execution tools — read only. (I.e., do not run bash/python/external commands.)

- `read` — read the `.txt` file.
- `write` — only when `--save` is present, save `~/clawd/tmp/<topic-slug>.json`.

## Acceptance tests

1. **Behavioral: wrong extension hard-stop**
   - Run: `/auto-extract-v4 /abs/path/to/file.pdf`
   - Expected: outputs exactly the two-line wrong-extension error.

2. **Behavioral: missing file hard-stop**
   - Run: `/auto-extract-v4 /path/does/not/exist.txt`
   - Expected: outputs exactly the two-line file-not-found error.

3. **Behavioral: output contract (one JSON array, ≤15)**
   - Run: `/auto-extract-v4 /abs/path/to/source.txt`
   - Expected: exactly one fenced ```json block; its content parses as a JSON array with `N <= 15` and each item contains `schema: clawd.learn.concept.v1`.

4. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/auto-extract-v4/SKILL.md
```
Expected: `PASS`.

5. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/auto-extract-v4/SKILL.md
```
Expected: `PASS`.
