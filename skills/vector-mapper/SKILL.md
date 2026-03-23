---
name: vector-mapper
description: "Create a deterministic research vector map (queries + priorities) from a plain-English intelligence target. Internal sub-skill for /intel."
---

## Vector Mapper (internal sub-skill)

Turn a plain-English **INTELLIGENCE TARGET** (e.g., a company/product/industry string) into a compact **VECTOR MAP** that downstream stages can execute as web/KM searches.

This skill is intended to be called by an orchestrator (e.g., `/intel`). It is not designed for end-users to discover or run directly, but it **must** remain deterministic and parseable.

## Use

Use this when you need a consistent, machine-parseable set of research “vectors” (angles) and **time-bounded** search queries for a target.

Use cases:
- An orchestrator needs to generate a search plan before running web searches.
- You want a fixed set of core business intel angles plus (optionally) up to two target-specific angles.

Do **not** use this skill to answer questions or to fetch sources; it only outputs a plan.

## Inputs

A single string: the **target** exactly as received upstream.

Examples:
- `Notion`
- `Linear`
- `B2B project management tools`
- `no-code automation for SMBs`

## Outputs

A **plain-text** document with the following sections, in this exact order, with no additional headings:

1) **INTELLIGENCE TARGET**
- The target string, exactly as provided.

2) **VECTOR MAP**
- 5–7 vector entries.
- Each entry must include:
  - Vector number (`1`–`7`)
  - Vector name (2–4 words)
  - Priority (`HIGH` | `MEDIUM` | `LOW`)
  - Description (exactly **one** sentence)
  - Search Queries (a numbered list)

3) **PIPELINE NOTES**
- 2–3 sentences on which vectors are likely highest-signal **without** claiming facts about the target.

### Required vectors
Always output **exactly five** core vectors, in this exact order:
1) Pricing
2) Product
3) Positioning
4) Vulnerabilities
5) Competitive Moves

You may add **0–2** additional domain-specific vectors as #6 and #7 only when the target string itself implies a uniquely relevant angle.

## Steps

Follow this deterministic procedure:

1) **Echo the target**
   - Output the `INTELLIGENCE TARGET` section containing the target exactly as given (no trimming beyond preserving exact characters).

2) **Emit core vectors (1–5) in order**
   - Use these default priorities unless the Positioning escalation rule applies:
     - Pricing: HIGH
     - Product: MEDIUM
     - Positioning: LOW (may escalate; see rules)
     - Vulnerabilities: HIGH
     - Competitive Moves: MEDIUM

3) **Write queries**
   - For each vector except where fixed below, generate **2–3** queries.
   - Each query MUST include:
     - the target string verbatim
     - at least one year token: `2025` or `2026`
     - at least one action term (e.g., pricing change, outage, backlash, acquisition)

4) **Apply fixed query rules**
   - Vulnerabilities must include **exactly these 3 queries** (substitute `[target]`):
     1) `[target] reviews complaints site:g2.com 2025 2026`
     2) `[target] negative reviews site:trustpilot.com 2025 2026`
     3) `[target] problems frustrations site:news.ycombinator.com 2025 2026`

   - Competitive Moves must include **exactly these 3 queries**:
     1) `[target] acquisition partnership integration 2025 2026`
     2) `[target] competitor response market expansion site:techcrunch.com OR site:venturebeat.com 2025 2026`
     3) `[target] vs competitors announcement site:news.ycombinator.com 2025 2026`

5) **Optionally add domain-specific vectors (#6–#7)**
   - Add only if the target string itself contains clear specificity cues (e.g., “API”, “SOC2”, “banking”, “marketplace”, “HIPAA”).
   - If no strong cue exists, add none.

6) **Write PIPELINE NOTES**
   - 2–3 sentences.
   - Do not assert facts about the target.
   - Focus on expected yield (e.g., vulnerabilities + pricing often high-signal).

## Rules & constraints

- Output must be plain text and parseable (no Markdown tables).
- Never output fewer than 5 vectors or more than 7.
- Every query must include the target verbatim.
- Always time-bound queries with `2025` and/or `2026`.
- Positioning escalation rule: set Positioning to MEDIUM/HIGH only if the target string explicitly signals a positioning change (e.g., contains “rebrand”, “pivot”, “formerly”, “renamed”).
- Domain-specific vectors must not be generic (avoid “Growth”, “Marketing”, “Team”).

## Failure modes

- **Empty target**: If the input target is empty or only whitespace, output exactly:
  - `ERROR: missing_target`

- **Non-string / structured input** (e.g., JSON object provided by upstream by mistake): output exactly:
  - `ERROR: invalid_target_type`

## Toolset

This skill uses no tools. It only formats text.

## Acceptance tests

1. **Behavioral: invocation contract (internal slash)**
   - Run: `/vector-mapper Notion`
   - Expected: the first non-empty line after the header `INTELLIGENCE TARGET` is exactly `Notion`.

2. **Behavioral: structure + ordering invariants**
   - Run: `/vector-mapper Notion`
   - Expected: VECTOR MAP contains vectors numbered **1–5** only, in this order and with these names:
     - `1) Pricing`
     - `2) Product`
     - `3) Positioning`
     - `4) Vulnerabilities`
     - `5) Competitive Moves`
   - Expected: output contains no Markdown table pipes (`|`) and no extra top-level headings beyond the required three sections.

3. **Behavioral: fixed Vulnerabilities queries are exact**
   - Run: `/vector-mapper Linear`
   - Expected: under vector 4, Search Queries are exactly (line-for-line, substituting `Linear` for `[target]`):
     1) `Linear reviews complaints site:g2.com 2025 2026`
     2) `Linear negative reviews site:trustpilot.com 2025 2026`
     3) `Linear problems frustrations site:news.ycombinator.com 2025 2026`

4. **Behavioral: fixed Competitive Moves queries are exact**
   - Run: `/vector-mapper Linear`
   - Expected: under vector 5, Search Queries are exactly:
     1) `Linear acquisition partnership integration 2025 2026`
     2) `Linear competitor response market expansion site:techcrunch.com OR site:venturebeat.com 2025 2026`
     3) `Linear vs competitors announcement site:news.ycombinator.com 2025 2026`

5. **Behavioral: every non-fixed query is time-bounded**
   - Run: `/vector-mapper Notion`
   - Expected: every query line includes either `2025` or `2026`.

6. **Negative: empty input hard-stop**
   - Run: `/vector-mapper "   "`
   - Expected: output is exactly `ERROR: missing_target` (no extra whitespace, no additional lines).

7. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/vector-mapper/SKILL.md
```
   - Expected: `PASS`

8. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/vector-mapper/SKILL.md
```
   - Expected: `PASS`
