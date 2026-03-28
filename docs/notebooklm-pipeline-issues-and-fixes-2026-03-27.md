# NotebookLM pipeline — issues encountered + fixes applied (2026-03-27)

This document captures the failure modes we hit while running the NotebookLM → file-based extraction pipeline (skill-forge / research-to-skill), and the concrete fixes that made it reliable.

## 0) Context (what we were trying to do)

Goal: run NotebookLM prompt suites (p01..p17), extract responses deterministically to files, then use the outputs as inputs for later synthesis/skill building.

Key components:
- `skills/notebooklm-fetcher/scripts/fetch_clipboard.py` — drives NotebookLM via Tandem and extracts responses
- `skills/notebooklm-runner/scripts/run_notebooklm_runner.py` — runs prompts 1..17 using the fetcher, then triggers processor
- `skills/notebooklm-processor/scripts/process_runs.py` — generates `progress.md`
- `tools/generate_prompts.py` — generates the 17 prompts

---

## 1) Failure: fetcher reported partial/blocked

### Symptom
- Pipeline errors like:
  - `ERROR: fetcher returned partial/blocked prompt=1 exit=1`

### Root causes observed
- NotebookLM UI state sometimes didn’t expose expected affordances (copy button missing)
- Early on, `clear_chat_history` sometimes failed to find a delete/clear menu item (best-effort)

### Fix applied
- Kept `clear_chat_history` best-effort and **stopped marking the entire run partial** just because clear history failed.
- Ensured partial/error is driven by **actual response extraction failure**, not menu availability.

---

## 2) Failure: runner “stuck” waiting for progress.md + SIGTERM

### Symptom
- Long runner appeared stuck; watchdog logs showed repeated `progress.md not yet` then SIGTERM.

### Actual situation
- The runner was blocked on a prompt where NotebookLM never produced a copy affordance / response.
- A separate orchestration process timed out and SIGTERM’d.

### Mitigation
- Prefer a **one-prompt sanity test** before launching the full 17 prompts.
- When you do need a watchdog, watch for the correct run dir and use file mtime (freshness), not just existence.

---

## 3) Failure: “copy button visible” but extracted UI chrome (false success)

### Symptom
- Fetcher returned `EXIT_CODE:0` and wrote a response that was clearly sidebar text like:
  - `4 sources / Studio / Audio Overview ... NotebookLM can be inaccurate ...`

### Root cause
- Fetcher could end up saving non-answer UI text when the message-level copy button wasn’t actually available.

### Fix applied
- Added rejection logic so DOM/clipboard extraction does **not accept obvious UI chrome**.
- If extraction doesn’t yield a real answer, the run remains `partial` (non-zero) rather than “ok”.

---

## 4) Failure: selectors not found / NotebookLM “home state”

### Symptom
- Fetcher runs failed with `selectors_not_found`.
- Snapshots showed `Studio output will be saved here` (NotebookLM home state) and no transcript.

### Root cause
- **Tandem endpoint mismatch**: our `Tandem` wrapper in `fetch_clipboard.py` used legacy endpoints:
  - `/type` with `{selector,text}`
  - `/click` with `{selector}`
  - `/snapshot`
  but the Tandem HTTP server actually expects **snapshot endpoints**:
  - `POST /snapshot/fill` with `{ref,value}`
  - `POST /snapshot/click` with `{ref}`
  - `GET /snapshot?compact=true`

That mismatch meant “typing” could effectively no-op even though refs were found, leaving NotebookLM in home state and never generating a transcript/copy button.

### Fix applied (load-bearing)
Updated `skills/notebooklm-fetcher/scripts/fetch_clipboard.py`:
- `snapshot_raw()` → `GET /snapshot?compact=true`
- `click(@e...)` → `POST /snapshot/click {ref}`
- `fill(@e...)` → `POST /snapshot/fill {ref,value}`
- Routed `.type()` → `.fill()` for back-compat

Outcome: previously stuck prompts (notably prompt 05) completed reliably; full Phase 1 ran 1..17 OK.

---

## 5) Failure: prompt generation produced repetitive, task-specific prompts

### Symptom
- Prompts repeated "video prompts / marketing / writing" across many questions.

### Root cause
- `tools/generate_prompts.py` injected `--goal` verbatim into multiple angles. When the goal contained a list of examples, the model echoed them everywhere.

### Fix applied
- Operational: set `--goal` as a general constraint (“portable micro-protocols… avoid task-specific examples unless asked”).
- Later: patched `tools/generate_prompts.py` to replace the hard-coded “daily habits and rituals” angle with **in-session** protocol angles and an explicit constraint.

---

## 6) Failure: NotebookLM outputs over-indexed on daily routines (Morning Pages, rituals)

### Symptom
- Even with “in-session” prompts, outputs still included:
  - Morning Pages / Artist’s Date / rituals / daily routines

### Why it happens
- Source distribution bias: Artist’s Way-style routines are prominent in sources → NotebookLM defaults to them.

### Mitigations attempted
1) Prompt regen (v2b): in-session angles (5–30 minutes) — reduced but did not eliminate routine leakage.
2) Hard constraints embedded into each prompt (v2c):
   - forbid ongoing routines, forbid naming Morning Pages/Artist’s Date
   - require translating routine concepts into one-off protocols without naming originals

Practical guidance: when sources are biased, you need **hard negative constraints** + self-check rubric inside each prompt, not just “prefer in-session”.

---

## 7) Operational “done” criteria for Phase 1

A Phase 1 run is finished when:
- `progress.md` shows:
  - `OK: [1..17]`
  - `Partial: []`
  - `Missing: []`
- `summary.md` exists and lists all prompt run IDs.

---

## 8) Concrete commands used (reference)

### Generate prompts
```bash
/opt/anaconda3/bin/python3 ~/clawd/tools/generate_prompts.py \
  --topic "creative practice and artistic toolkit" \
  --goal "Give me reusable creativity micro-protocols..." \
  --output-dir "~/clawd/tmp/skill-forge/creativity-toolkit-v2/prompts_v2a"
```

### Run Phase 1
```bash
/opt/anaconda3/bin/python3 ~/clawd/skills/notebooklm-runner/scripts/run_notebooklm_runner.py \
  --notebook-url "https://notebooklm.google.com/notebook/<id>" \
  --prompts-dir "~/clawd/tmp/skill-forge/creativity-toolkit-v2/prompts_v2a" \
  --runs-dir "~/clawd/tmp/research-to-skill/creativity-toolkit-v2/pass1_v2a" \
  --progress-file "~/clawd/tmp/research-to-skill/creativity-toolkit-v2/pass1_v2a/progress.md" \
  --final-summary "~/clawd/tmp/research-to-skill/creativity-toolkit-v2/pass1_v2a/summary.md" \
  --max-checks 1800 \
  --sleep-seconds 2.0
```

---

## 9) Current state

- Fetcher is now aligned with Tandem’s snapshot API (`/snapshot/fill` + `/snapshot/click`), which was the major reliability unlock.
- Prompt generation template updated to support in-session protocol prompt sets.
- Remaining modelling issue: source bias towards routines; best handled by embedding hard negative constraints in prompts.
