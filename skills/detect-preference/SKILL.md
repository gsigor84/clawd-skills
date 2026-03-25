---
name: detect-preference
description: "Manual trigger: /detect-preference <message>. Detect Igor preference signals in a message and log a structured LRN proposal to /Users/igorsilva/clawd/.learnings/LEARNINGS.md via /self-improving-agent. Proposals only; never edits USER.md/MEMORY.md/SOUL.md/AGENTS.md."
---

# detect-preference (preference proposal logger)

## Trigger contract

Manual trigger (supported):
- `/detect-preference <message>`

Automatic trigger (design intent; requires external wiring):
- Fire when Igor sends a message containing any trigger phrase in the taxonomy below.
- This skill itself does not install hooks or modify gateway config. Another hook/orchestrator must call `/detect-preference <igor-message>`.

## Goal

Given a single user message, detect high-signal preference indicators and log a proposal (LRN entry) so recurring patterns can later be promoted by `tools/promote_learnings.py`.

## Non-goals

- Do not modify: `/Users/igorsilva/clawd/USER.md`, `MEMORY.md`, `SOUL.md`, or `AGENTS.md`.
- Do not log secrets/tokens or large payloads.
- Silent by default.

## Use

Use this skill to capture preference signals from a single Igor message as structured proposals (LRN entries) in `.learnings/LEARNINGS.md`, so repeated signals can later be promoted by `tools/promote_learnings.py`.

## Inputs

- One string: the message to analyse.

## Outputs

- Silent by default.
- If one or more new preference proposals are logged, output exactly one line per new preference:
  - `📝 Preference captured: pref:<pattern-key>`

"New" means: no existing learnings entry contains a line exactly matching:
- `- Pattern-Key: pref:<pattern-key>`

## Deterministic workflow (must follow)

### Tooling
- `read` (check existing learnings for de-dup)

### Step 0 — Validate input
- If the input message is missing/empty: output `ERROR: missing_input. Usage: /detect-preference <message>`

### Step 1 — Normalise message
- Let `msg_raw = input` (trimmed)
- Let `msg_lower = msg_raw.lower()`

### Step 2 — Detect matches (taxonomy below)
- For each taxonomy item:
  - If any trigger phrase matches by case-insensitive substring on `msg_lower`, mark it as matched.
- If multiple keys match:
  - Prefer the most specific match (longest trigger phrase wins).
  - Allow multiple matches only if clearly non-overlapping.

### Step 3 — Determine scope
Default:
- `scope: session`

Set `scope: global` only if `msg_lower` contains any of:
- `always`
- `never`
- `globally`
- `from now on`
- `every time`
- `as a rule`

### Step 4 — De-dup
- Read `/Users/igorsilva/clawd/.learnings/LEARNINGS.md` if it exists.
- If it contains `- Pattern-Key: pref:<pattern-key>` for a matched key, do not log that key.

### Step 5 — Log proposal via /self-improving-agent (mandatory for new matches)

For each new matched key, call `/self-improving-agent` exactly once:

`/self-improving-agent learning | preference proposal: pref:<pattern-key> | details: <details> | files: USER.md,MEMORY.md,SOUL.md,AGENTS.md`

Where `<details>` is a compact, structured plain-text block containing exactly these lines:
- `Pattern-Key: pref:<pattern-key>`
- `Recurrence-Count: 1`
- `First-Seen: <YYYY-MM-DD>`
- `Last-Seen: <YYYY-MM-DD>`
- `target_file: <USER.md|MEMORY.md|SOUL.md|AGENTS.md>`
- `scope: <session|global>`
- `Proposed rule: <exact 1-line rule template>`
- `Trigger excerpt: <first 160 chars of msg_raw>`

Rules:
- Do not include tokens/secrets.
- Do not include full transcripts.

### Step 6 — Chat output
- If no new preferences logged: output nothing.
- If any logged: output `📝 Preference captured: pref:<pattern-key>` once per logged key.

## Taxonomy (16 keys)

Each item lists:
- pattern_key (used as `pref:<pattern_key>`)
- triggers (case-insensitive substring)
- proposed rule (exact 1 line)
- target file

### USER.md targets

1) pattern_key: `user.no_checkins`
- triggers:
  - `don't check in`
  - `no status updates`
  - `stop asking for confirmation mid-task`
  - `just do it`
- proposed rule:
  - `Rule: Don’t send mid-task check-ins/status updates; execute and report results when complete.`
- target_file: `USER.md`

2) pattern_key: `user.fix_then_report`
- triggers:
  - `don't ask me what to do`
  - `fix it and tell me what happened`
  - `if it breaks, fix it`
- proposed rule:
  - `Rule: When something breaks, attempt a fix immediately and report what happened; don’t ask Igor what to do unless blocked.`
- target_file: `USER.md`

3) pattern_key: `user.cli_first`
- triggers:
  - `terminal first`
  - `cli-heavy`
  - `no gui`
  - `don't use the ui`
- proposed rule:
  - `Rule: Prefer CLI/tooling workflows over GUI steps unless GUI is strictly necessary.`
- target_file: `USER.md`

4) pattern_key: `user.bursty_go_mode`
- triggers:
  - `go do it`
  - `run it and come back`
  - `i'll be back`
- proposed rule:
  - `Rule: When Igor says “go”, run to completion without incremental updates; return only final outputs/errors.`
- target_file: `USER.md`

5) pattern_key: `user.proper_systems_not_patches`
- triggers:
  - `build it properly`
  - `not patched`
  - `quick fix`
  - `one-off script`
  - `make it a skill`
- proposed rule:
  - `Rule: Prefer repeatable, encapsulated solutions (skills/scripts) over one-off patches when the pattern will recur.`
- target_file: `USER.md`

### MEMORY.md targets

6) pattern_key: `output.show_exact_changes`
- triggers:
  - `show me the patch`
  - `show full file`
  - `no ellipses`
  - `don't use ... placeholders`
- proposed rule:
  - `Rule: When editing code/files, show the exact patch or full file—never use “…” placeholders.`
- target_file: `MEMORY.md`

7) pattern_key: `output.diff_before_apply`
- triggers:
  - `show me changes before applying`
  - `dry-run first`
  - `don't modify anything yet`
  - `propose the patch first`
- proposed rule:
  - `Rule: For non-trivial edits, show a diff first and wait for “apply/approve” before modifying files.`
- target_file: `MEMORY.md`

8) pattern_key: `output.no_narration_for_routine_tools`
- triggers:
  - `don't narrate`
  - `skip the obvious`
  - `just do the tool call`
- proposed rule:
  - `Rule: Don’t narrate routine, low-risk tool calls; only narrate when multi-step/sensitive.`
- target_file: `MEMORY.md`

9) pattern_key: `output.include_validator_result`
- triggers:
  - `run the validator`
  - `prove it runs`
  - `show me pass`
  - `show me fail`
- proposed rule:
  - `Rule: When a deterministic validator/check exists, run it and include its PASS/FAIL output.`
- target_file: `MEMORY.md`

10) pattern_key: `output.keep_one_question_gate`
- triggers:
  - `one question only`
  - `don't ask me a list`
  - `ask one question`
- proposed rule:
  - `Rule: If blocked/uncertain, ask exactly one consolidated clarification question.`
- target_file: `MEMORY.md`

### SOUL.md targets

11) pattern_key: `soul.escalate_after_3_failures`
- triggers:
  - `stop looping`
  - `don't keep retrying`
  - `figure out why it failed`
  - `quality dropping`
- proposed rule:
  - `Rule: Limit repair loops to 3 attempts; then escalate with the smallest actionable diagnosis.`
- target_file: `SOUL.md`

12) pattern_key: `soul.minimal_blast_radius_default`
- triggers:
  - `smallest blast radius`
  - `don't touch python yet`
  - `skill.md only for now`
  - `read-only first`
- proposed rule:
  - `Rule: Default to read-only reconnaissance; take the smallest reversible action that advances the goal.`
- target_file: `SOUL.md`

13) pattern_key: `soul.no_guessing_when_facts_matter`
- triggers:
  - `don't guess`
  - `strict context`
  - `show evidence`
  - `tool-first`
- proposed rule:
  - `Rule: For factual/ops claims, rely on tools/files/logs; if evidence is missing, say so and stop.`
- target_file: `SOUL.md`

### AGENTS.md targets

14) pattern_key: `agents.memory_search_before_nontrivial`
- triggers:
  - `check memory first`
  - `you should have remembered`
  - `use the notes`
- proposed rule:
  - `Rule: Before non-trivial work, run memory_search and treat it as source of truth for prior decisions/preferences.`
- target_file: `AGENTS.md`

15) pattern_key: `agents.cite_sources_for_tool_outputs`
- triggers:
  - `show me the output`
  - `cite source`
  - `prove it`
- proposed rule:
  - `Rule: When using workspace files or web_fetch, include Source: <path#line or URL> for verifiability.`
- target_file: `AGENTS.md`

16) pattern_key: `agents.no_midrun_updates_in_go_mode`
- triggers:
  - `don't update me`
  - `only come back when done`
  - `come back when done`
  - `only come back when`
- proposed rule:
  - `Rule: In go-mode tasks, avoid intermediate messaging; report only on completion or hard block.`
- target_file: `AGENTS.md`

## Failure modes

- Missing input:
  - `ERROR: missing_input. Usage: /detect-preference <message>`

- Logger failed:
  - `ERROR: logging_failed. Could not write preference proposal.`

## Toolset

- `read`

## Acceptance tests

1. Behavioral: captures once
   - Run: `/detect-preference don't modify anything yet`
   - Expected:
     - A new LRN entry logged with `Pattern-Key: pref:output.diff_before_apply`
     - Chat output: `📝 Preference captured: pref:output.diff_before_apply`

2. Negative: missing input
   - Run: `/detect-preference`
   - Expected output (exact): `ERROR: missing_input. Usage: /detect-preference <message>`

3. Behavioral: de-dups
   - Run the same command twice.
   - Expected: second run outputs nothing.

4. Structural validator
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/detect-preference/SKILL.md
```
Expected: `PASS`.
