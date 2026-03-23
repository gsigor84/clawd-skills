---
name: how-to-learn
description: "Trigger: /how-to-learn. Provide simple, direct instructions on how to use /learn and the /auto-extract → /save-concepts txt ingestion pipeline."
---

how-to-learn

Goal  
Provide simple, direct instructions on how to use /learn and the txt ingestion pipeline.

Trigger  
/how-to-learn

Output (strict)

Return EXACTLY this structure every time:

HOW TO USE THE SYSTEM

1. LEARN (use /learn)
Use when:
* something is worth remembering
* you found a useful insight
* you want to store knowledge

Command: /learn: <short text or /path/to/file>

RULE
If you ask: "Do I need to remember this?"
* YES → use /learn

EXAMPLES
/learn: Use direct integration for MVP; add interfaces for future scaling

---

2. INGEST A TEXT FILE (use /auto-extract → /save-concepts)
Use when:
* you have a .txt file (book chapter, article, guide) worth adding to your knowledge library
* you want Adam to learn from a document automatically

⚠️ IMPORTANT: Always run /reset before /auto-extract.
Large files will cause context saturation and the skill will fail silently.

Step 1: /reset

Step 2: /auto-extract /absolute/path/to/file.txt --save
→ Adam extracts up to 15 concepts, shows JSON in chat, saves to ~/clawd/tmp/<slug>.json
→ Note the suggested slug from the output

Step 3: /save-concepts <slug> --file ~/clawd/tmp/<slug>.json
→ Adam writes all concepts to ~/clawd/learn/json/<slug>/
→ index.json updated, knowledge is live

RULE
If you have a .txt file worth remembering → /reset → /auto-extract --save → /save-concepts --file

EXAMPLE
/reset
/auto-extract /Users/igorsilva/Documents/chapter_04_agentic_ai_architecture.txt --save
/save-concepts agentic-ai-architecture --file ~/clawd/tmp/agentic-ai-architecture.json

Rules  
- Keep it simple  
- No extra explanation  
- Always return same structure

Acceptance criteria  
1) Clear instructions  
2) Easy to follow  
3) No variation in output

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
   - Run: `/how-to-learn <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/how-to-learn <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/how-to-learn/SKILL.md
```
Expected: `PASS`.
