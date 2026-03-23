---
name: auto-extract-v2
description: "Trigger: /auto-extract-v2 <absolute-file-path> [--save]. Read a local .txt file and extract up to 15 concepts into one fenced JSON array (clawd.learn.concept.v1). Optional --save writes the same array to ~/clawd/tmp/<topic-slug>.json."
---

# auto-extract-v2

## Use

Convert a local **.txt** file into **≤ 15** reusable concepts, returned as **one** `clawd.learn.concept.v1` JSON array inside **exactly one** fenced ```json block.

### Triggers
- `/auto-extract-v2 <absolute-file-path>`
- `/auto-extract-v2 <absolute-file-path> --save`

### Execution recipe (single-turn)

#### STEP 1 — Validate input path
1) Confirm the provided path is an **absolute path**.
2) Confirm the file exists and is readable.
   - If not, output exactly (two lines) and **Then stop.**
     ❌ File not found: <path>
     💡 Check the path is correct and the file exists. Use tab-completion or Finder to verify.
3) Confirm the extension is `.txt`.
   - If not, output exactly (two lines) and **Then stop.**
     ❌ This skill only supports .txt files. Got: <extension>
     💡 Convert your file to .txt first, then re-run.

#### STEP 2 — Read source
Use `read` to load the full file contents.

#### STEP 3 — Conservative boilerplate trimming
Optionally remove obvious “table-of-contents” style sentences, but only when the sentence begins with one of these prefixes (case-insensitive):
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

Hard rule: if you’re unsure whether it’s boilerplate, **keep it**.

#### STEP 4 — Segment and detect “shape” (decide extraction units)
For each section/paragraph cluster, determine the dominant pattern and choose the extraction unit.

**A) Distinction / contrast (pair concept)**
- Signals: “X vs Y”, “X means… while Y means…”, “X is…, whereas Y is…”.
- Output unit: **one** concept named like: `X vs Y (distinction)`.
- Example: If the text says “Precision is about consistency; accuracy is about closeness to truth”, extract one concept covering both, and make the challenge question test the difference.
- Edge case: if X and Y are introduced far apart, only pair them if the source explicitly compares them.

**B) Definition list (many small concepts)**
- Signals: repeated “X is …”, “X refers to …”, glossary-like bullets.
- Output unit: **one concept per definition**.
- Example: “Activation energy is …; Catalysis is …” → two concepts.
- Edge case: if a definition depends on a named prerequisite defined immediately above, you may include that prerequisite in `answer_p1`, but don’t merge the concepts unless the text treats them as inseparable.

**C) Procedure / steps (sequence concepts)**
- Signals: numbered steps, “first/then/finally”, recipes, protocols.
- Output unit: usually **one concept per step**.
- Example: a 5-step negotiation method → 5 concepts, each step as a concept.
- Edge case: if a step is just “do the previous step again”, don’t waste a slot; skip or fold it into the meaningful step.

**D) Framework with components (component concepts)**
- Signals: a named model with parts (e.g., “the 4 levers are …”).
- Output unit: **one concept per component** when each component is explained.
- Example: If a framework lists 4 components but only explains 2, extract the 2 explained components (and optionally one concept for the framework overview if it’s explained).
- Edge case: if components are named but not explained, prefer a single concept for the overall framework rather than shallow component stubs.

**E) Reframe / paradigm shift (shift concept)**
- Signals: “instead of X, think Y”, “move from X to Y”, “the key is not A but B”.
- Output unit: **one concept per shift**, named like `From X to Y (reframe)`.
- Example: “Don’t optimize for speed; optimize for throughput” → one shift concept.

What not to extract:
- Pure preview/recap (“this section will cover…”, “in the last chapter…”), unless it also contains a real rule/definition.

#### STEP 5 — Extract candidate concepts (grounded)
A candidate is worth extracting if it answers at least one:
- What is X?
- How does X work?
- What’s the difference between X and Y?
- What rule governs X?
- What are the steps of X?

Grounding rules:
- Never add facts not present in the file.
- Keep `answer_p1` direct and testable.
- `answer_p2` must be `null` unless the file explicitly connects it to another concept that you also extracted.
- `backbone` must be `null`.

#### STEP 6 — Apply cap and de-duplicate
Hard cap: **15**.
- If you have more than 15, keep the most broadly useful and least redundant.
- Prefer concepts that encode mechanisms/rules over anecdotes.

#### STEP 7 — Derive topic slug (filename only)
From the **filename only** (not file contents):
1) remove extension
2) remove leading `chapter_\d+_`, `ch_\d+_`, `part_\d+_`
3) lowercase
4) spaces/underscores → hyphens
5) remove characters outside `[a-z0-9-]`
6) collapse repeated hyphens
7) trim hyphens

#### STEP 8 — Format output (strict wrapper + schema)
If you extracted **0** concepts, output exactly (two lines) and **Then stop.**
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
    "challenge_question": "<question>",
    "answer_p1": "<direct, grounded answer>",
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
1) Attempt `write` to: `~/clawd/tmp/<topic-slug>.json`.
2) If that write cannot happen because the folder is missing/unwritable, output exactly (two lines) and **Then stop.**
   ❌ Could not save to ~/clawd/tmp/<slug>.json — folder may not exist.
   💡 Run: mkdir -p ~/clawd/tmp and try again.
3) If the write succeeds, the file must contain only the JSON array (pretty-printed is fine).

Guardrails:
- If `--save` is absent: do not write any files.
- If `--save` is present: write **only** `~/clawd/tmp/<topic-slug>.json`.
- Do not run bash/python/external tools.

## Inputs

- `absolute-file-path` (required)
  - Must be an absolute path to a readable `.txt` file.
- `--save` (optional)
  - When present, also save the JSON array to `~/clawd/tmp/<topic-slug>.json`.

## Outputs

### Success output
- Exactly one fenced ```json block containing a single JSON array of **≤ 15** objects.
- Wrapper text exactly as specified in STEP 8.

### Error outputs (exact strings)
- Missing/unreadable file:
  ❌ File not found: <path>
  💡 Check the path is correct and the file exists. Use tab-completion or Finder to verify.
- Wrong extension:
  ❌ This skill only supports .txt files. Got: <extension>
  💡 Convert your file to .txt first, then re-run.
- Zero concepts:
  ❌ No extractable concepts found in <path>
  💡 The file may be too short, too generic, or mostly boilerplate. Try a different chapter or section.
- Save failure on `--save`:
  ❌ Could not save to ~/clawd/tmp/<slug>.json — folder may not exist.
  💡 Run: mkdir -p ~/clawd/tmp and try again.

## Failure modes

Hard blockers (must stop immediately):
- File not found / unreadable.
- Not a `.txt`.
- `--save` requested but `~/clawd/tmp/` is missing/unwritable.

Soft blocker (deterministic output):
- Readable file but no concepts → emit the exact “No extractable concepts” output.

## Toolset

- `read` — read the local `.txt` source file.
- `write` — only with `--save`, write the JSON array to `~/clawd/tmp/<topic-slug>.json`.

## Acceptance tests

1. **Behavioral: wrong extension hard-stop**
   - Run: `/auto-extract-v2 /abs/path/to/file.pdf`
   - Expected output exactly:
     - `❌ This skill only supports .txt files. Got: .pdf`
     - `💡 Convert your file to .txt first, then re-run.`

2. **Behavioral: missing file hard-stop**
   - Run: `/auto-extract-v2 /path/does/not/exist.txt`
   - Expected output exactly:
     - `❌ File not found: /path/does/not/exist.txt`
     - `💡 Check the path is correct and the file exists. Use tab-completion or Finder to verify.`

3. **Behavioral: happy path output shape**
   - Run: `/auto-extract-v2 /abs/path/to/source.txt`
   - Expected:
     - Starts with `Suggested slug:`
     - Contains exactly one fenced ```json block
     - The fenced content parses as a JSON array with `N <= 15`
     - Every element includes `schema: clawd.learn.concept.v1` and sequential `index` values

4. **Structural validator**
   - Command: `/opt/anaconda3/bin/python3 skills/skillmd-builder-agent/scripts/validate_skillmd.py skills/auto-extract-v2/SKILL.md`
   - Expected: `PASS`.

5. **No invented tools**
   - Command: `/opt/anaconda3/bin/python3 skills/skillmd-builder-agent/scripts/check_no_invented_tools.py skills/auto-extract-v2/SKILL.md`
   - Expected: `PASS`.
