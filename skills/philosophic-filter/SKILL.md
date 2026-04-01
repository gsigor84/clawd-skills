---
name: philosophic-filter
description: "Reads a Maimonides knowledge file, applies an invisible Nietzschean analytical engine, and outputs a modern rabbi-style sermon (EN + PT-BR) under 400 words, then sends to WhatsApp."
---

# philosophic-filter

## Trigger
`/philosophic-filter --file <filename>`

## Use
Run this skill to turn a file in `~/clawd/knowledge/maimonides/` into a short modern sermon. The analysis engine is Nietzschean (societal pressure → breakaway → wilderness → renewal), but the sermon must not use philosophical jargon or name Nietzsche.

## Inputs
- `--file`: filename under `~/clawd/knowledge/maimonides/` (e.g. `Beshalach.md`)

## Outputs
- Portuguese (Brazilian) sermon
- WhatsApp message to `+447533464436` containing the PT-BR sermon only

## Failure modes
- File not found: ask for a valid filename in `~/clawd/knowledge/maimonides/`.
- Sermon too long: cut hard, keep the core human challenge + wilderness + resolution.
- Jargon leak: remove philosophical labels/terms and keep plain language.
- WhatsApp send fails: report the failure and output the sermon text anyway.

## Acceptance tests

1. Run `/philosophic-filter --file Beshalach.md` — expected output: a warm PT-BR sermon under 400 words, no philosophical jargon/labels.

2. Negative case:
```bash
/opt/anaconda3/bin/python3 - <<'PY'
from pathlib import Path
p = Path('/Users/igorsilva/clawd/knowledge/maimonides/DOES_NOT_EXIST.md')
print('exists:', p.exists())
PY
```
Then run `/philosophic-filter --file DOES_NOT_EXIST.md` — expected error message: file not found (missing).

3. Structural validators:
```bash
/opt/anaconda3/bin/python3 ~/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py ~/clawd/skills/philosophic-filter/SKILL.md
/opt/anaconda3/bin/python3 ~/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py ~/clawd/skills/philosophic-filter/SKILL.md
```
Expected output: PASS / PASS.

## Toolset
- read (required): read `~/clawd/knowledge/maimonides/<filename>`
- exec (optional): word count checks
- sessions_send (required): send WhatsApp to `+447533464436`

## Procedure
1. Read the specified file from `~/clawd/knowledge/maimonides/`.
2. Scan for the human arc: pressure → breakaway → wilderness → renewal.
3. Write the sermon directly in Portuguese (Brazilian):
   - Warm, passionate, accessible
   - Speaks to everyday modern life
   - No philosophical jargon or labels
   - Opens with the core human challenge
   - Walks through the struggle and the wilderness
   - Ends with a personal challenge to the reader
   - Under 400 words
4. Send ONE WhatsApp message to `+447533464436` containing the PT-BR sermon only.
