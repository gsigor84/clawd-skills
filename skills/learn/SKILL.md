---
name: learn
description: "Trigger: /learn followed by a file path or attached file (PDF, TXT, DOCX, MD). Produces a graduate-level structured Markdown study guide using a strict 6-step extract→backbone→map→study-guide→save→confirm pipeline."
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
- Never summarise concepts instead of extracting them individually.
- Never write definition questions (no “what is/define X”).
- Never write one-paragraph answers: every concept must have exactly two answer paragraphs.
- Never omit backbone identification.
- Never write any challenge question until the full relationship map is completed.

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

4. **STEP 3 — MAP RELATIONSHIPS (complete before questions)**
   - For **every non-backbone** concept:
     - assign it to **one** backbone concept it connects to structurally
     - explain **WHY** (mechanism-level, structural reason)
   - Output a section titled exactly:
     - `STEP 3 — MAP RELATIONSHIPS`
   - This mapping must be complete **for all** non-backbone concepts before writing any questions.

5. **STEP 4 — WRITE STUDY GUIDE (repeat for every concept)**
   - Output a section titled exactly:
     - `STEP 4 — WRITE STUDY GUIDE`
   - For **each** concept (backbone and non-backbone), produce **exactly** this structure:

     ```md
     ### [Number]. [Concept Name]
     **Challenge Question**
     A scenario-based question where the reader is placed in a concrete real-world situation (mentoring someone, building a product, writing copy, evaluating a policy, driving a car, running an experiment) and must apply the concept under pressure. Never ask "what is X" or "define X". Always ask "you are doing X and Y happens, explain how concept Z applies and what the specific consequences are."

     **Graduate-Level Answer**
     Paragraph 1: Direct confident answer to the scenario. Use the technical vocabulary of the concept. Zero hedging. Full conviction. Demonstrate operational understanding — show the concept working, not just named.
     Paragraph 2: Bridge to one backbone concept. Explain the structural relationship — not just "this is similar to" but WHY the same underlying mechanism produces both phenomena. Be specific about the mechanism.
     ```

   - The paragraph-2 backbone bridge must be consistent with the Step 3 relationship mapping.

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

8. **STEP 7 — AUTO-INGEST (run after confirmation)**
   - Automatically run `/ingest` on the saved study guide path so it is immediately loaded into the knowledge base.
   - Use the exact saved file path from STEP 5.
