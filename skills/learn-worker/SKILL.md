---
name: learn-worker
description: "Run /learn-style study guide generation in an isolated worker session to avoid main-session .jsonl.lock wedges. Trigger: /skill learn-worker: <file-path> (or /learn-worker <file-path> if supported). Enforces single-flight (no concurrent runs) and provides safe recovery guidance (no lock-file deletion)."
---

## Agent Loop Contract (agentic skills only)

You are a tool-first agent running inside OpenClaw.

**Goal:** generate a study guide for the provided file path using the same conceptual pipeline as `learn` (STEP 1–6), but execute the work in an isolated worker session so the main session stays responsive.

**Non-goals:**
- Do not delete `~/.openclaw/agents/**/sessions/*.jsonl.lock` files.
- Do not run two learn-worker jobs concurrently.

## Anti-hallucination / context discipline

- Context-only: use only the provided source file contents.
- If the source is thin, skip unsupported concepts (do not invent) and report them in STEP 6.

## Procedure

### Inputs
- User provides a single local file path (PDF/TXT/MD/DOCX) as the argument to `/skill learn-worker:`.

### Output
- Save: `/Users/igorsilva/clawd/learn/<source-title-lowercase-hyphenated>-study-guide.md`
- Reply with the saved path and: `Run /ingest <path> to load this into your knowledge base.`

### Steps (follow in order)

1) **Validate input path**
   - If missing: ask for exactly one file path.
   - Verify the file exists (`exec: ls -la "<path>"`). If not found: stop with a short error.

2) **Single-flight guard (no concurrent runs)**
   - Use a local single-flight lock directory:
     - `LOCKDIR=/Users/igorsilva/clawd/.learn-worker.lockdir`
   - Attempt to acquire it atomically:
     - `exec: mkdir "$LOCKDIR"`
   - If mkdir fails because it exists:
     - Reply: `learn-worker busy; wait for completion` and stop.
   - Ensure cleanup at the end (best-effort):
     - `exec: rmdir "$LOCKDIR" || true`

3) **Preflight: avoid obvious main-session wedge symptoms (informational only)**
   - Check if the *main session* currently has a lock file:
     - `exec: ls /Users/igorsilva/.openclaw/agents/main/sessions/*.jsonl.lock 2>/dev/null || echo NO_LOCKS`
   - If lock files exist: do **not** attempt to clear them. Continue anyway because we are running in an isolated worker session.

4) **Run the actual learn pipeline in an isolated worker session**
   - Spawn a subagent (isolated run) whose sole job is to execute the `learn` skill on the provided input path.
   - The subagent must:
     1. Invoke: `/skill learn: <input-path>`
     2. Wait for completion
     3. Return the final saved study guide path and any errors

5) **Confirm output file exists**
   - After the worker returns a saved path, verify it exists:
     - `exec: ls -la "<saved_path>"`
   - If missing: report failure and include the returned path.

6) **Reply**
   - Print the saved path.
   - Print: `Run /ingest <saved_path> to load this into your knowledge base.`

7) **Cleanup**
   - Remove the single-flight lockdir (best-effort): `rmdir /Users/igorsilva/clawd/.learn-worker.lockdir || true`

## Acceptance criteria
- No concurrent runs: second invocation while one is running replies `learn-worker busy; wait for completion`.
- No destructive behavior: never delete `.jsonl.lock` files.
- Main session remains responsive because work runs in an isolated worker.
- Output file path is deterministic and verified to exist.

## Must-pass tests
1) Run:
   - `/skill learn-worker: /Users/igorsilva/Downloads/extracts/agentic-architectural-patterns-ch10.txt`
   - Expect a saved `.md` file in `/Users/igorsilva/clawd/learn/`.
2) Trigger twice quickly:
   - Second call must return `learn-worker busy; wait for completion`.
3) While worker is running, main session should still respond to a normal message (`ping`).

## Use

Describe what the skill does and when to use it.

## Inputs

- Describe required inputs.

## Outputs

- Describe outputs and formats.

## Failure modes

Hard-stop failures (priority HIGH):
- Input path missing or file not found/unreadable.
- Worker run fails to produce a saved study guide path.
- Returned saved path does not exist on disk.

Partial/blocked states (priority MEDIUM):
- `learn-worker busy; wait for completion` (single-flight lock already held).
- Main-session lock files detected in Step 3 (informational), if they correlate with repeated wedges.

### Deterministic ERR logging via /self-improving-agent (mandatory on failures/partials)

Write ERR entries via `/self-improving-agent` for:

Hard-stop failures (priority HIGH):
- input path missing or file not found/unreadable
- worker run fails to produce a saved study guide path
- returned saved path does not exist on disk

Partial/blocked states (priority MEDIUM):
- `learn-worker busy; wait for completion` (single-flight lock already held)

Never log secrets or large payloads:
- Do not include source file contents.

#### Exact /self-improving-agent call format (ERR)

Call (single line):
- `/self-improving-agent error | <one-line summary> | details: <details> | files: skills/learn-worker/SKILL.md`

The logged ERR entry must include these fields (keep short; no payloads):
- `Pattern-Key:` use the exact key from the mapping table below
- `Recurrence-Count:` start at `1`
- `First-Seen:` and `Last-Seen:` set to today

Context fields to include inside the entry:
- `stage: learn-worker`
- `priority: high|medium`
- `status: hard_stop|blocked`
- `reason:` one-line reason (include any exact emitted message if applicable)
- `input_path:` user-provided path (or empty)
- `lockdir:` `/Users/igorsilva/clawd/.learn-worker.lockdir`
- `main_session_locks_present:` `yes|no|unknown`
- `returned_saved_path:` if any
- `suggested_fix:` one line

#### Pattern-Key mapping (use exact key)

| Condition | Pattern-Key | priority | status |
|---|---|---|---|
| missing input path | `learn-worker:missing_input_path` | high | hard_stop |
| file not found/unreadable | `learn-worker:input_file_missing` | high | hard_stop |
| worker failed | `learn-worker:worker_failed` | high | hard_stop |
| saved path missing | `learn-worker:saved_path_missing` | high | hard_stop |
| busy lock held | `learn-worker:busy` | medium | blocked |

## Toolset

- `read`
- `write`
- `edit`
- `exec`

## Acceptance tests

1. **Behavioral: happy path**
   - Run: `/learn-worker <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/learn-worker <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/learn-worker/SKILL.md
```
Expected: `PASS`.
