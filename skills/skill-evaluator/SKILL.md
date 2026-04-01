---
name: skill-evaluator
description: "# skill-evaluator — deterministic PASS/FAIL evaluator for OpenClaw skills"
---

# skill-evaluator

A ruthless evaluator: runs the acceptance tests declared in a target skill’s `SKILL.md`, classifies each test as **DETERMINISTIC** (execute + gate) or **MANUAL REQUIRED** (explicit reason + what evidence would satisfy it), and produces a **signed** PASS/FAIL report with evidence (commands run, stdout/stderr paths, exit codes, artefact hashes).

Thesis: **make claims costly and truth cheap**.

## Trigger

Preferred (as a skill):

`/skill-evaluator --skill-dir ~/clawd/skills/<target-skill> --out-dir ~/clawd/tmp/skill-evaluator/<target-skill> --allow-run`

Direct invocation:

```bash
/opt/anaconda3/bin/python3 ~/clawd/skills/skill-evaluator/skill_evaluator.py \
  --skill-dir ~/clawd/skills/<target-skill> \
  --out-dir ~/clawd/tmp/skill-evaluator/<target-skill> \
  --allow-run
```

## Use
Use this when you want a skill to prove itself with evidence, instead of prose.

## Inputs
- `--skill-dir` (required): target skill directory containing `SKILL.md`
- `--out-dir` (required): output directory for report + evidence
- `--allow-run` (optional): execute deterministic tests (otherwise classify-only)
- `--signing-key` (optional): path to 32-byte key (raw bytes or base64). Produces `report.sig`.
- `--hash` (repeatable): additional file/dir paths to include in hash manifest

## Outputs
- `<out-dir>/report.json` — machine-readable verdict with evidence (schema below)
- `<out-dir>/report.md` — human-readable report
- `<out-dir>/report.sig` — signature (if signing enabled)
- `<out-dir>/evidence/cmd_*.stdout.txt|stderr.txt` — captured execution evidence

### report.json schema (strict)

```json
{
  "skill": "<name>",
  "verdict": "PASS|FAIL",
  "verdict_reason": "...",
  "tests": [
    {
      "id": "T1",
      "classification": "DETERMINISTIC|MANUAL_REQUIRED",
      "command": "...",
      "exit_code": 0,
      "stdout_path": "...",
      "stderr_path": "...",
      "evidence_hashes": {"sha256": {"<path>": "<hex>"}},
      "manual_reason": null
    }
  ],
  "manual_required": ["T2", "T5"],
  "signed_at": "<ISO-8601 UTC>",
  "ledger_run_id": "<run_id>"
}
```

## Procedure

1. Load `SKILL.md` from `--skill-dir`.
2. Extract acceptance tests from the `## Acceptance tests` section.
3. Parse each test using the **strict acceptance test format** (below). Any test not in this format is **refused** (classified `MANUAL_REQUIRED` with reason `invalid_test_format`).
4. For each parsed test:
   - classify as `DETERMINISTIC` or `MANUAL_REQUIRED` (sandbox + credential/network rules)
   - if deterministic and `--allow-run`, execute it with **max 30s timeout**, capture stdout/stderr + exit code
   - if manual, record explicit reason and what evidence would satisfy it
5. Compute sha256 hashes for `SKILL.md` and requested `--hash` targets.
6. Emit `report.json` and `report.md` conforming to the schema above.

## Safe execution sandbox (mandatory)

Execution-grade evaluation must be *safe* and *repeatable*. The evaluator enforces a sandbox:

- **Allowed write dirs:** `~/clawd/tmp/` only
- **No network calls:** deterministic tests must not invoke network access
- **Max runtime:** 30 seconds per command

If a command violates the sandbox, it is automatically classified as `MANUAL_REQUIRED` (with an explicit reason).

### Sandbox violation heuristics (minimum set)
Classify as `MANUAL_REQUIRED` if the command contains any of:
- Writes outside `~/clawd/tmp/` (any absolute path not under `/Users/igorsilva/clawd/tmp/`)
- Network tools/URLs: `curl`, `wget`, `http://`, `https://`
- Privileged/destructive ops: `sudo`, `rm -rf`, service control

## Classification rules
A test is `MANUAL_REQUIRED` if any of these are true:
- it violates the sandbox rules above
- it requires external credentials (e.g. `OPENAI_API_KEY`, `BRAVE_API_KEY`)
- it performs privileged/destructive operations (`sudo`, `rm -rf`, service control)
- it depends on external network services (non-local `curl/wget/http`)

Everything else is `DETERMINISTIC`.

## Failure modes
- `SKILL.md not found` → exit `2`
- A deterministic test fails (non-zero exit) → overall `FAIL`, exit `1`.
- Manual-required tests exist → overall `FAIL` (by design; no silent skips).

## Toolset
- `read` (SKILL.md)
- `exec` (run deterministic tests)
- `write` (report files)

## Strict acceptance test format (required)

Each acceptance test **must** be a fenced code block whose contents follow:

```
# TEST <id>
<command>
# EXPECT exit=<n>
# EXPECT_FILE <path> min_bytes=<n>   (optional)
# MANUAL reason=<...> evidence=<...>  (if manual)
```

If a test does not match this format, the evaluator refuses to run it and marks it `MANUAL_REQUIRED` with reason `invalid_test_format`.

## Acceptance tests

Behavioural invocation (as a skill): `/skill-evaluator --skill-dir ~/clawd/tmp/skill-evaluator/fixture-skill --out-dir ~/clawd/tmp/skill-evaluator/fixture-skill-report --allow-run`

1. **Behavioural: happy path (evaluate a deterministic fixture skill)**

Expected: report.json file saved, parses as JSON, and verdict is `PASS`.

```bash
# TEST T1
FIXTURE_DIR="/Users/igorsilva/clawd/tmp/skill-evaluator/fixture-skill" && \
mkdir -p "$FIXTURE_DIR" && \
printf '%s' "LS0tCm5hbWU6IGZpeHR1cmUtc2tpbGwKZGVzY3JpcHRpb246ICJmaXh0dXJlIgotLS0KCiMgZml4dHVyZS1za2lsbAoKIyMgVHJpZ2dlcgoKYC9maXh0dXJlLXNraWxsYAoKIyMgVXNlCmZpeHR1cmUKCiMjIElucHV0cwpub25lCgojIyBPdXRwdXRzCm5vbmUKCiMjIEZhaWx1cmUgbW9kZXMKbm9uZQoKIyMgVG9vbHNldAotIGV4ZWMKCiMjIEFjY2VwdGFuY2UgdGVzdHMKCjEuIGJlaGF2aW91cmFsCgpgYGBiYXNoCmVjaG8gb2sKYGBgCgpFeHBlY3RlZDogc3Rkb3V0IGNvbnRhaW5zIGBva2AuCg==" | base64 -D > "$FIXTURE_DIR/SKILL.md" && \
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skill-evaluator/skill_evaluator.py \
  --skill-dir "$FIXTURE_DIR" \
  --out-dir /Users/igorsilva/clawd/tmp/skill-evaluator/fixture-skill-report \
  --allow-run
# EXPECT exit=0
# EXPECT_FILE /Users/igorsilva/clawd/tmp/skill-evaluator/fixture-skill-report/report.json min_bytes=200
```

2. **Negative: missing SKILL.md**

```bash
# TEST T2
mkdir -p /Users/igorsilva/clawd/tmp/skill-evaluator/empty-skill && \
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skill-evaluator/skill_evaluator.py \
  --skill-dir /Users/igorsilva/clawd/tmp/skill-evaluator/empty-skill \
  --out-dir /Users/igorsilva/clawd/tmp/skill-evaluator/empty-skill-out \
  --allow-run
# EXPECT exit=2
# EXPECT_FILE /Users/igorsilva/clawd/tmp/skill-evaluator/empty-skill-out/report.md min_bytes=50
# MANUAL reason=stderr_match evidence=Capture stderr contains 'SKILL.md not found'
```

3. **Structural validator**

```bash
# TEST T3
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/skill-evaluator/SKILL.md
# EXPECT exit=0
```

4. **No invented tools**

```bash
# TEST T4
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/skill-evaluator/SKILL.md
# EXPECT exit=0
```
