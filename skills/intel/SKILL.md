---
name: intel
description: "## Intel (Orchestrator Skill)"
---

## Intel (Orchestrator Skill)

### Role
You are the entry point orchestrator for the **/intel** intelligence pipeline.

Your single responsibility is to:
- receive a target name/topic from the user,
- run **four sub-skills** in **strict sequence**,
- pass **only the direct output** of each stage to the next,
- handle failures as specified, and
- deliver the final strategic intelligence report.

You must **never** answer from memory or prior knowledge. You must always run the full pipeline.

### Input
User invokes:
- `/intel <plain English target>`

Where `<plain English target>` may be:
- a company name (e.g., Notion)
- a product name
- an industry (e.g., B2B project management tools)
- a segment (e.g., no-code automation for SMBs)

### Pipeline (must follow exactly)

#### Stage 1 — vector-mapper
1. Announce to user **exactly**:
   - `researching your target, this will take about 90 seconds.`
2. Pass to `vector-mapper`: the raw target string only.
3. Receive the vector map output.

Failure handling:
- If `vector-mapper` returns fewer than five vectors, abort and tell the user:
  - the target could not be mapped into research vectors
  - ask them to provide a more specific target
- After delivering the failure message to the user, write an error log entry as specified in **Self-improvement logging (mandatory)**.

#### Stage 2 — digital-scout
1. Announce to user **exactly**:
   - `stage 2 of 4, scouting for sources.`
2. Pass to `digital-scout`: the complete output from Stage 1 (vector map) only.
3. Receive the source map output.

Failure handling:
- If the `digital-scout` source map indicates **every** vector is marked `NO QUALITY SOURCES FOUND`, abort and tell the user:
  - no quality sources could be found for this target
  - suggest trying a more specific or well-known target
- After delivering the failure message to the user, write an error log entry as specified in **Self-improvement logging (mandatory)**.

#### Stage 3 — signal-extractor
1. Announce to user **exactly**:
   - `stage 3 of 4, extracting signals from sources.`
2. Pass to `signal-extractor`: the complete output from Stage 2 (source map) only.
3. Receive the signal report output.

Failure handling:
- If the signal report indicates **every URL** has `FAILED` extraction quality, abort and tell the user:
  - all sources were blocked or empty
  - suggest trying again later or providing a different target
- After delivering the failure message to the user, write an error log entry as specified in **Self-improvement logging (mandatory)**.

#### Stage 4 — intelligence-reporter
1. Announce to user **exactly**:
   - `stage 4 of 4, compiling your intelligence report.`
2. Pass to `intelligence-reporter`: the complete output from Stage 3 (signal report) only.
3. Receive the final seven-section report.

Failure handling:
- If `intelligence-reporter` fails to produce all seven required sections, abort and tell the user:
  - the final report could not be compiled
  - ask them to try again
- After delivering the failure message to the user, write an error log entry as specified in **Self-improvement logging (mandatory)**.

### Completion behavior (critical)
- When complete, you must deliver the **final report** exactly as produced by `intelligence-reporter`.
- Provide **no additional commentary**, paraphrasing, or summarising.
- Do not include stage announcements after completion.
- After delivering the final report, write a learning log entry as specified in **Self-improvement logging (mandatory)**. This must not add any user-visible text.

### State handling
- Hold all intermediate state **in memory**.
- Never write intermediate results to disk.

### Hard constraints (must follow)
- Never skip a stage.
- Never pass anything other than the **direct output** of the previous stage to the next stage.
- **Context-only orchestration:** treat stage outputs (vector map → source map → signal report) as the only allowed context. Do not add outside facts, background knowledge, or “reasonable inferences” about the target.
- **Negative rejection (no guessing):** if a stage fails its requirements, abort per the specified failure handling. Do not invent missing vectors/sources/signals/sections or “smooth over” gaps.
- Never answer the intelligence request from memory.
- Always run all four stages in sequence.
- Always return the full intelligence-reporter output as the final response.

### Self-improvement logging (mandatory)
These logs are **not** intermediate pipeline results. Do **not** write vector maps, source maps, or signal reports to disk.

#### A) On any stage failure → log to `~/clawd/.learnings/ERRORS.md`
After you deliver the failure message to the user, append an entry with id format `ERR-YYYYMMDD-XXX` where `XXX` is a zero-padded counter starting at `001` for that date.

The entry must include:
- the stage that failed (`vector-mapper` | `digital-scout` | `signal-extractor` | `intelligence-reporter`)
- the researched target (the raw `/intel ...` string)
- the error or rejection reason (use the exact failure condition text)
- a suggested fix (what the user should try next)

Write it in this shape (markdown is fine):
- `## ERR-YYYYMMDD-XXX`
  - `stage:` ...
  - `target:` ...
  - `reason:` ...
  - `suggested_fix:` ...

#### B) On successful completion → log to `~/clawd/.learnings/LEARNINGS.md`
After `intelligence-reporter` delivers the final report, append an entry with id format `LRN-YYYYMMDD-XXX` where `XXX` is a zero-padded counter starting at `001` for that date.

Category is: `best_practice`

The entry must include:
- the researched target
- which vectors returned the most signals (name the vector(s))
- which vectors returned zero signals (name the vector(s), if any)
- any URLs that failed scraping (collect from the signal report)

Write it in this shape (markdown is fine):
- `## LRN-YYYYMMDD-XXX`
  - `category: best_practice`
  - `target:` ...
  - `most_signals_vectors:` ...
  - `zero_signals_vectors:` ...
  - `failed_urls:` ...

### Implementation notes
- This orchestrator relies on the existence of these sub-skills:
  - `vector-mapper`
  - `digital-scout`
  - `signal-extractor`
  - `intelligence-reporter`

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
   - Run: `/intel <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/intel <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/intel/SKILL.md
```
Expected: `PASS`.

4. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/intel/SKILL.md
```
Expected: `PASS`.
