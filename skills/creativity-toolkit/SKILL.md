---
name: creativity-toolkit
description: "Trigger: /creativity-toolkit <task>. Artefact-driven Inklings-style creativity pipeline with ledgered phases, schema-validated outputs, and a mandatory Nietzschean gate."
---

# creativity-toolkit

## Trigger
`/creativity-toolkit <task>`

## Use
Run an artefact-driven creativity pipeline that produces a single paste-ready generation prompt (Phase 8) while leaving durable evidence for every phase under `~/clawd/tmp/creativity-toolkit/<run_id>/`.

This skill is designed to make creative claims **costly** and truth **cheap**: every phase writes a schema-constrained artefact, ledgered via `ledger_event.py run`.

## Inputs
- `<task>` (required): plain-English creative request.

## Outputs
Primary:
- `~/clawd/tmp/creativity-toolkit/<run_id>/phase-8-final.md` — the final paste-ready prompt (exactly one paragraph)

Supporting artefacts (schema-constrained):
- `phase-1-research.md`
- `phase-2-selection.md`
- `phase-5-scamper.md`
- `phase-6-generated.md`
- `phase-7-critic.md`
- `phase-65-gate.md`
- `WARNINGS.md` (only when gate fails beyond rewrite budget)

## Safe execution + determinism
- No network calls.
- All writes must be under `~/clawd/tmp/creativity-toolkit/<run_id>/`.
- Stop conditions are enforced (see below).

## Run ledger (mandatory)

All phases are executed via the `ledger_event.py run` wrapper:

- Create run:
```bash
run_id=$(/opt/anaconda3/bin/python3 ~/clawd/tools/ledger_event.py create creativity-toolkit '{"task":"<task>"}')
```

- Run a phase (ledgered, with start/done/fail):
```bash
/opt/anaconda3/bin/python3 ~/clawd/tools/ledger_event.py run "$run_id" phase-1 creativity-toolkit -- <command>
```

Phase names used:
- `phase-1` research
- `phase-2` selection
- `phase-5` scamper
- `phase-6` generator
- `phase-7` critic
- `phase-65` gate
- `phase-8` final

## Stop conditions (mandatory)
- Max **2** stagnation retries (oblique strategy loops).
- Max **2** Nietzsche Gate rewrites.
- After budgets are exhausted: stop with `FAIL` or continue only as `DONE_WITH_WARNINGS` (see gate handling).

## Phase artefacts: paths + schema (mandatory)

All artefacts are written under:
- `ROOT=~/clawd/tmp/creativity-toolkit/<run_id>/`

### Phase 1 — Research
- Path: `$ROOT/phase-1-research.md`
- Schema:
  - must contain heading `## Sparks`
  - must contain **>= 5** bullet lines under Sparks

### Phase 2 — Selection
- Path: `$ROOT/phase-2-selection.md`
- Schema:
  - must contain `## Selected`
  - must contain `## Rejected`

### Phase 5 — SCAMPER synthesis
- Path: `$ROOT/phase-5-scamper.md`
- Schema:
  - must contain `## Synthesized_prompt`

### Phase 6 — Generated variations
- Path: `$ROOT/phase-6-generated.md`
- Schema:
  - must contain `## Variations`
  - must contain **>= 3** clearly separated variations

### Phase 7 — Critic revision
- Path: `$ROOT/phase-7-critic.md`
- Schema:
  - must contain `## Praise`
  - must contain `## Critique`
  - must contain `## Revision`

### Phase 6.5 — Nietzsche Gate
- Path: `$ROOT/phase-65-gate.md`
- Schema:
  - must contain `## Gate_result`
  - Gate_result must be either:
    - `PASS`
    - `FAIL_with_reason: <one line>`

### Phase 8 — Final prompt
- Path: `$ROOT/phase-8-final.md`
- Schema:
  - must contain **exactly one paragraph**

## Nietzsche Gate — failure handling (mandatory)

- If gate fails: rewrite up to **2** times.
- After 2 rewrites still FAIL:
  - mark the run as `DONE_WITH_WARNINGS` in the ledger (operationally: record gate as FAIL and proceed)
  - write `$ROOT/WARNINGS.md`
  - stamp the final prompt output as:
    - `UNPROVEN/LOW_VOLTAGE` (prefix in Phase 8 artefact)

## Procedure (runtime: exec the Python runner)

When `/creativity-toolkit <task>` is invoked, do **not** simulate the phases in chat. Execute the deterministic runner and return the final artefact.

1) **exec** the runner:
```bash
/opt/anaconda3/bin/python3 ~/clawd/skills/creativity-toolkit/creativity_toolkit.py \
  --task "<task>"
```
The runner prints the absolute path to `phase-8-final.md`.

2) Read the printed path from stdout (last line).

3) **exec**:
```bash
cat "<printed_phase_8_path>"
```

4) Return the contents of `phase-8-final.md` as the reply.

Stop conditions, phase artefacts, and ledger semantics are enforced by `creativity_toolkit.py`.

## Failure modes
- Missing task → `ERROR: no_task_provided`
- Any phase command fails (non-zero) → phase FAILED in ledger; stop.
- Artefact schema missing required headings/bullets → FAIL.
- Nietzsche Gate fails beyond rewrite budget → `DONE_WITH_WARNINGS` + WARNINGS.md + final stamped `UNPROVEN/LOW_VOLTAGE`.

## Toolset
- `exec` (phase commands via `ledger_event.py run`)
- `write` (artefacts)
- `read` (verify artefacts)
- `sessions_spawn` (optional: if you implement multi-agent writing of artefacts; still must write artefacts deterministically)

## Acceptance tests

1. **Behavioural (positive): artefact-driven final prompt exists**

Run: `/creativity-toolkit "write a video prompt for a futuristic city"`

```bash
# TEST T1
/creativity-toolkit "write a video prompt for a futuristic city"
# EXPECT exit=0
# EXPECT_FILE /Users/igorsilva/clawd/tmp/creativity-toolkit/<run_id>/phase-8-final.md min_bytes=250
# MANUAL reason=run_id_unknown evidence=Capture the run_id printed by the skill and substitute it into EXPECT_FILE path.
```

Expected: `phase-8-final.md` exists and contains a single paragraph of at least 50 words.

2. **Behavioural (negative): missing task**

Run: `/creativity-toolkit`

```bash
# TEST T2
/creativity-toolkit
# EXPECT exit=2
# MANUAL reason=stderr_match evidence=Output contains error string "no_task_provided".
```

Expected: error `no_task_provided`.

3. **Structural: critic artefact contains required headings**

```bash
# TEST T3
# MANUAL reason=run_id_unknown evidence=After running T1, open phase-7-critic.md and confirm it contains headings ## Praise, ## Critique, ## Revision.
```

4. **Structural validator**

```bash
# TEST T4
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py /Users/igorsilva/clawd/skills/creativity-toolkit/SKILL.md
# EXPECT exit=0
```

5. **No invented tools**

```bash
# TEST T5
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py /Users/igorsilva/clawd/skills/creativity-toolkit/SKILL.md
# EXPECT exit=0
```
