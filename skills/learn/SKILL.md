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
- **Context-only generation:** treat the source text as the only allowed knowledge. Do not import facts, examples, or definitions that are not supported by the source.
- **Negative rejection (no guessing):** if the source does not contain enough information to complete a step without inventing details, stop and refuse (see “Anti-hallucination gates”).
- Never summarise concepts instead of extracting them individually.
- Never write definition questions (no “what is/define X”).
- Never write one-paragraph answers: every concept must have exactly two answer paragraphs.
- Never omit backbone identification.
- Never write any challenge question until the full relationship map is completed.

### Anti-hallucination gates (internal, for /learn)

**Failure mode targeted:** contextual hallucinations — the model has the correct source text available but answers from pre-trained knowledge anyway.

**Strict prompting mode (internal):**
- Use the source text as the exclusive ground truth.
- If the source diverges from what you “know”, the source wins.
- Do not fill gaps with plausible-sounding content.

**Refusal rule (negative rejection):**
- **Hard-fail only when the source is unusable** (missing/empty/unreadable/clearly irrelevant to the task).
- **Otherwise, prefer partial completion over guessing:** if *specific concepts* cannot be supported by the source well enough to complete STEP 4 without importing outside knowledge, you MUST **skip those concepts** (do not invent), proceed with the rest, and report the skipped items at the end (see below).

If you must refuse (hard-fail), output exactly one of the following (and nothing else):
1. `I do not know the answer based on the provided context.`
2. `The retrieved documents do not contain the information necessary to answer your question.`
3. `I must decline to answer, as the provided context is insufficient.`

**Coverage checks (internal):**
- STEP 1 sanity: every extracted item must be explicitly present in the source text (exact string match OR an obvious unambiguous variant, e.g., singular/plural). If not, remove it from the extract list.
- STEP 2/3 grounding: every backbone decision and every non-backbone → backbone link must be justified by a concrete mechanism described in the text (not vibes). If you can’t point to such support, revise the backbone/mapping.
- STEP 4 “answerability” gate: before writing any concept’s two paragraphs, verify the source contains enough details to write both paragraphs without importing outside facts. If not, **skip that concept** and add it to an internal `UNSUPPORTED_CONCEPTS` list (do not invent).

**End-of-run reporting (required if any skips):**
- If `UNSUPPORTED_CONCEPTS` is non-empty, in **STEP 6 — CONFIRM** add one extra line after the saved path:
  - `Skipped concepts due to insufficient support in source: <comma-separated list>`
  - Then still print: `Run /ingest [path] to load this into your knowledge base.`

### Disciplined Inquiry (internal, for /learn)

Apply a disciplined-inquiry loop to the /learn workflow WITHOUT changing the required /learn output sections or formats.

Internal structure to maintain (do not print unless explicitly asked):
- TOPIC: "I am working on producing a study guide from [source]"
- GUIDING QUESTION (choose one):
  - "How do the concepts in this source relate structurally?"
  - "Why are the backbone concepts the bridges that connect the rest?"
- PROBLEM: why this matters for the user (better learning + retrieval quality)
- CLAIM: your current best structural interpretation (updated as you read)
- REASONS: why you think the mapping/backbone is correct
- EVIDENCE: specific observations from the source text (phrases, repeated links, explicit mechanisms)
- OBJECTIONS: plausible alternative backbones/mappings
- WARRANTS: only when a reason→claim link isn’t obvious

Active reading rule (required after every read/tool call):
- Write a short internal SOURCE NOTE (not user-visible):
  - MAIN CLAIM of the passage
  - 1–2 KEY REASONS
  - how it supports a REASON or tests an OBJECTION in your mapping

Evidence quality check (internal):
- For any important mapping/backbone decision, ensure evidence is:
  - Accurate (actually present in the text)
  - Precise (points to a specific mechanism/phrase/repetition, not vibes)
  - Sufficient (more than one weak hint; prefer multiple supports)

Skeptical-colleague objection check (internal):
- For backbone selection and each non-backbone→backbone link, write at least 1 plausible objection and your response:
  - Intrinsic objection: "the evidence is thin / ambiguous" → response: qualify internally or gather more text
  - Extrinsic objection: "wrong framing / wrong backbone" → response: compare alternatives and pick the better-supported bridge
- If objections remain strong, revise Step 2/3 before proceeding.

Do NOT import these rules into /learn output:
- No 200-word cap (conflicts with /learn required length)
- No mandatory hedging (conflicts with Step 4 ‘zero hedging’ requirement)
- No mandatory user-output template (conflicts with /learn’s fixed STEP 1–4 output structure)

Quality gate before STEP 4:
- Do not start writing challenge questions/answers until:
  - backbone selection is defensible (reasons + evidence)
  - STEP 3 mapping is complete and consistent
  - **answerability is confirmed:** you can write every concept’s two paragraphs using only information present in the source text (no outside knowledge). If any concept fails this, refuse per “Anti-hallucination gates”.
- Avoid data dumps: include in the final study guide only what the /learn format requires, plus minimal wording needed for accuracy.

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
