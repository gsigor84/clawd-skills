---
name: skill-launcher
description: "Pipeline stage 8: validate deployed skill path, restart the OpenClaw gateway safely, verify health, and output a single final user-facing message (or exact error)."
---

# skill-launcher (internal)

## Trigger contract

This is the final stage of the `/vibe` pipeline.

Trigger only when the input is the complete output from `skill-deployer` and contains:
- `DEPLOY_STATUS: COMPLETE`
- `PATH:` pointing to `/Users/igorsilva/clawd/skills/<skill-name>/SKILL.md`
- `TRIGGER:` (slash command)

If `DEPLOY_STATUS` is missing or not `COMPLETE`, fail with the exact error in **Failure modes**.

## Use

Use this stage to make a newly deployed skill available immediately by restarting the gateway and verifying it is healthy, then emitting a single final user-facing message.

This stage must be deterministic and safe-by-default: it only touches the gateway process and reads the deployed skill file path.

## Inputs

A single plain-text deployment confirmation block from `skill-deployer`.

Example (minimum):

DEPLOY_STATUS: COMPLETE
PATH: /Users/igorsilva/clawd/skills/example-skill/SKILL.md
TRIGGER: /example-skill
MESSAGE: deployed

## Outputs

Exactly one of the following:

### Output A — Success
A plain-text completion message (multi-line allowed) that includes, in this exact order:
1) `SKILL READY`
2) `TRIGGER: <trigger>`
3) `USAGE:` then exactly 2 example invocations
4) `WHAT IT DOES:` one sentence

### Output B — Failure (exact one-line error)
Return exactly one of the `ERROR:` strings in **Failure modes**.

## Deterministic workflow (must follow)

### Tooling
- `read` (confirm file exists and sanity-check frontmatter)
- `exec` (restart gateway + health check)

### Global caps (hard limits)
- Max gateway restart wait: **15 seconds**
- Max health retries: **3** (5 seconds apart)
- No other process management commands allowed besides those listed below.

### Boundary rules (privacy + safety)

- Never run `pkill -f` or broad process-kill patterns.
- Never modify the deployed SKILL.md.
- Never print file contents.
- Never run commands unrelated to gateway health.
- If the deployed path does not match `/Users/igorsilva/clawd/skills/<name>/SKILL.md`, refuse.

### Step 1 — Parse and validate deploy confirmation
1) Require `DEPLOY_STATUS: COMPLETE`.
2) Extract `PATH:` and `TRIGGER:`.
3) Validate `PATH:` starts with `/Users/igorsilva/clawd/skills/` and ends with `/SKILL.md`.
4) Read `PATH:` using `read`.
   - If read fails → fail.
5) Sanity-check the file begins with YAML frontmatter `---` and includes a `name:` line.
   - If not → fail.

### Step 2 — Restart gateway (safe command set)
Run exactly one of the following command sequences via `exec`:

Primary:
```bash
openclaw gateway restart
```

If restart is not available in this environment, fallback:
```bash
openclaw gateway stop && openclaw gateway start
```

Notes:
- Do not use `pkill`.
- Do not restart anything else.

### Step 3 — Verify gateway health
Check health using:
```bash
openclaw status
```

Deterministic retry policy:
- Run `openclaw status` up to 3 times.
- Sleep 5 seconds between attempts.
- If all attempts fail to show a healthy gateway state, fail.

### Step 4 — Emit final message
Emit Output A with:
- `TRIGGER:` exactly as provided.
- USAGE examples:
  1) `<TRIGGER> <example-input-1>`
  2) `<TRIGGER> <example-input-2>`

Example inputs must be generic placeholders that do not contain secrets.

## Failure modes

Return exactly one of these lines and nothing else:

### Deterministic ERR logging via /self-improving-agent (mandatory on failures)

On any emitted `ERROR: ...` failure mode below, do this deterministically:

1) Emit the `ERROR: ...` line (as required by the Failure mode contract).
2) Immediately call `/self-improving-agent` to log one ERR entry.

Priority mapping:
- All failures here are hard-stop failures → `priority: high`

Never log secrets or large payloads:
- Never print or log the full SKILL.md contents.

#### Exact /self-improving-agent call format (ERR)

Call (single line):
- `/self-improving-agent error | <one-line summary> | details: <details> | files: skills/skill-launcher/SKILL.md`

The logged ERR entry must include these fields (keep short; no payloads):
- `Pattern-Key:` use the exact key from the mapping table below
- `Recurrence-Count:` start at `1`
- `First-Seen:` and `Last-Seen:` set to today

Context fields to include inside the entry:
- `stage: skill-launcher`
- `priority: high`
- `status: hard_stop`
- `reason:` the exact `ERROR: ...` string
- `deployed_path:` extracted PATH
- `trigger:` extracted TRIGGER
- `gateway_restart_cmd:` `openclaw gateway restart` (or fallback)
- `suggested_fix:` one line

#### Pattern-Key mapping (use exact key)

| Failure | Pattern-Key |
|---|---|
| `ERROR: invalid_deploy_confirmation...` | `skill-launcher:invalid_deploy_confirmation` |
| `ERROR: skill_file_missing...` | `skill-launcher:skill_file_missing` |
| `ERROR: skill_file_malformed...` | `skill-launcher:skill_file_malformed` |
| `ERROR: unsafe_path...` | `skill-launcher:unsafe_path` |
| `ERROR: gateway_restart_failed...` | `skill-launcher:gateway_restart_failed` |
| `ERROR: gateway_unhealthy...` | `skill-launcher:gateway_unhealthy` |

- Invalid input:
  - `ERROR: invalid_deploy_confirmation. Expected DEPLOY_STATUS: COMPLETE with PATH and TRIGGER.`

- Skill file missing/unreadable:
  - `ERROR: skill_file_missing. Deployed SKILL.md not found or unreadable.`

- Skill file malformed:
  - `ERROR: skill_file_malformed. Deployed SKILL.md failed frontmatter sanity check.`

- Unsafe path:
  - `ERROR: unsafe_path. Refusing to operate outside /Users/igorsilva/clawd/skills/.`

- Gateway restart failed:
  - `ERROR: gateway_restart_failed. Could not restart gateway.`

- Gateway not healthy:
  - `ERROR: gateway_unhealthy. Gateway did not become healthy after restart.`

## Toolset

- `read`
- `write`
- `exec`

## Acceptance tests

1. **Behavioral (negative): rejects non-complete deploy input**
   - Run: `/skill-launcher DEPLOY_STATUS: FAILED`
   - Expected output (exact): `ERROR: invalid_deploy_confirmation. Expected DEPLOY_STATUS: COMPLETE with PATH and TRIGGER.`

2. **Behavioral (negative): unsafe path is refused**
   - Run: `/skill-launcher DEPLOY_STATUS: COMPLETE\nPATH: /tmp/x\nTRIGGER: /x`
   - Expected output (exact): `ERROR: unsafe_path. Refusing to operate outside /Users/igorsilva/clawd/skills/.`

3. **Behavioral (negative): missing skill file fails**
   - Run: `/skill-launcher DEPLOY_STATUS: COMPLETE\nPATH: /Users/igorsilva/clawd/skills/does-not-exist/SKILL.md\nTRIGGER: /does-not-exist\nMESSAGE: deployed`
   - Expected output (exact): `ERROR: skill_file_missing. Deployed SKILL.md not found or unreadable.`

4. **Behavioral: success message ordering**
   - Run: `/skill-launcher <valid deploy confirmation for an existing skill>`
   - Expected: output begins with `SKILL READY` and contains lines in this order:
     - `SKILL READY`
     - `TRIGGER: ...`
     - `USAGE:`
     - `WHAT IT DOES:`

5. **Behavioral: no broad process kill**
   - Run: `/skill-launcher <valid deploy confirmation>`
   - Expected: the restart step uses `openclaw gateway restart` (or `openclaw gateway stop && openclaw gateway start`) and never uses `pkill`.

6. **Behavioral: gateway unhealthy fails with exact error**
   - If `openclaw status` does not reach healthy state within retries, expected output (exact):
     - `ERROR: gateway_unhealthy. Gateway did not become healthy after restart.`

7. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/skill-launcher/SKILL.md
```
Expected: `PASS`.

8. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/skill-launcher/SKILL.md
```
Expected: `PASS`.
