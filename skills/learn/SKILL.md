---
name: learn
description: "Trigger: /learn followed by a file path or attached file (PDF, TXT, DOCX, MD). Produces a structured Markdown study guide using a strict 6-step extract→backbone→map→study-guide→save→confirm pipeline."
---

## /learn — Study Guide Generator

### Trigger
- `/learn <file-path>`
- or `/learn` with a single attached file (PDF, TXT, DOCX, MD)

### Output
- A structured Markdown study guide saved to: `~/clawd/learn/[source-title-lowercase-hyphenated]-study-guide.md`
- Then a confirmation message with the exact saved path and: `Run /ingest [path] to load this into your knowledge base.`

### Hard rules (do not violate)
- Never skip any step.
- **Context-only generation:** treat the source text as the only allowed knowledge. Do not import facts, examples, or definitions that are not supported by the source.
- Prefer **partial completion over guessing**:
  - Hard-fail only when the source is unusable (missing/empty/unreadable/clearly irrelevant).
  - Otherwise, skip unsupported concepts (do not invent) and report them in STEP 6.
- Never summarise concepts instead of extracting them individually.
- Never invent definitions or examples not supported by the source.
- Never omit backbone identification.
- Never write STEP 4 content until the full relationship map is completed.

### Anti-hallucination gates (internal, for /learn)

**Coverage checks (internal):**
- STEP 1 sanity: every extracted item must be explicitly present in the source text (exact string match OR an obvious unambiguous variant, e.g., singular/plural). If not, remove it from the extract list.
- STEP 2/3 grounding: every backbone decision and every non-backbone → backbone link must be justified by a concrete mechanism described in the text (not vibes). If you can’t support it from the text, revise the backbone/mapping.
- STEP 4 “answerability” gate: before writing any concept note, verify the source contains enough details to write the note **and** provide at least 1 verbatim quote. If not, **skip** that concept (do not invent).

**End-of-run reporting (required if any skips):**
- If any concepts were skipped due to insufficient support, in **STEP 6 — CONFIRM** add one extra line after the saved path:
  - `Skipped concepts due to insufficient support in source: <comma-separated list>`
  - Then still print: `Run /ingest [path] to load this into your knowledge base.`

### Procedure (follow exactly, in order)

1. **Resolve input file**
   - If the user provided a file path after `/learn`, use that.
   - Otherwise, if the user attached a file, use the local attachment path for the first attachment.
   - Determine `EXT` from the filename extension: `pdf | docx | md | txt`.

2. **STEP 1 — EXTRACT (must list EVERYTHING first)**
   - Read the entire source.
   - Extract **every named**:
     - concept
     - framework
     - principle
     - mental model
   - Output a single section titled exactly:
     - `STEP 1 — EXTRACT`
   - Under it, list **all extracted items** (one per bullet). Do not group, do not compress.

   **Reading rules by type**
   - PDF: use pdfminer.six
     - Run (replace FILE_PATH with the resolved file path):
       ```bash
       /opt/anaconda3/bin/python3 -c "from pdfminer.high_level import extract_text; import sys; print(extract_text(sys.argv[1]))" "FILE_PATH"
       ```
   - DOCX: use python-docx
     - Run:
       ```bash
       /opt/anaconda3/bin/python3 -c "import docx, sys; d=docx.Document(sys.argv[1]); print('\\n'.join(p.text for p in d.paragraphs))" "FILE_PATH"
       ```
   - MD/TXT: read directly
     - Run:
       ```bash
       cat "FILE_PATH"
       ```

3. **STEP 2 — IDENTIFY BACKBONE (4–6 items)**
   - From the full Step 1 list, identify the **4–6 concepts** that appear most frequently as *bridges* in explanations.
   - Output a section titled exactly:
     - `STEP 2 — IDENTIFY BACKBONE`
   - Explicitly label them as **Backbone Concepts** and list them.

4. **STEP 3 — MAP RELATIONSHIPS (complete before STEP 4)**
   - For **every non-backbone** concept:
     - assign it to **one** backbone concept it connects to structurally
     - explain **WHY** (mechanism-level, grounded in the source)
   - Output a section titled exactly:
     - `STEP 3 — MAP RELATIONSHIPS`

5. **STEP 4 — WRITE STUDY GUIDE (repeat for every concept)**
   - Output a section titled exactly:
     - `STEP 4 — WRITE STUDY GUIDE`
   - For **each** concept (backbone and non-backbone), produce **exactly** this structure:

     ```md
     ### [Number]. [Concept Name]
     **Concept Note**
     3–6 bullets, each bullet must be directly supported by the source text. No outside facts.

     **Evidence (verbatim)**
     1–3 short quotes (verbatim) from the source that support the Concept Note.

     **Backbone Link**
     One sentence: explain how this concept connects to its assigned backbone concept from STEP 3 (mechanism-level).
     ```

   - If the source is too thin to provide at least 1 evidence quote for a concept, **skip** that concept and report it in STEP 6.

6. **STEP 5 — SAVE**
   - Create directory if needed:
     ```bash
     mkdir -p /Users/igorsilva/clawd/learn
     ```
   - Choose `source-title` from the file name (no extension), lowercase it, and hyphenate.
   - Save the complete study guide to:
     - `/Users/igorsilva/clawd/learn/[source-title-lowercase-hyphenated]-study-guide.md`

7. **STEP 6 — CONFIRM**
   - Tell the user the exact saved file path.
   - Then say exactly:
     - `Run /ingest [path] to load this into your knowledge base.`

8. **STEP 7 — AUTO-INGEST (DISABLED)**
   - Do **not** attempt to auto-run `/ingest` via `exec`.
   - Instead, always finish with STEP 6 instructions so the user can run `/ingest <saved_path>` in-chat.

## Use

Describe what the skill does and when to use it.

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
   - Run: `/learn <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/learn <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/learn/SKILL.md
```
Expected: `PASS`.
