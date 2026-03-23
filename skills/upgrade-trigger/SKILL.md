---
name: upgrade-trigger
description: "Trigger: /upgrade-trigger: <context>. Decide whether an MVP should be upgraded and output exactly one concrete Signal/Meaning/Action triple (or an exact ask for context)."
---

# upgrade-trigger

## Trigger contract

Trigger when the user sends exactly:
- `/upgrade-trigger: <context>`

Rules:
- `<context>` must be non-empty and describe the current system/product/process and what is happening (symptoms, workload, users, incidents).
- This skill is single-shot and side-effect free.

## Use

Use this skill to detect when a system has outgrown MVP constraints and needs a specific next upgrade. It returns one observable trigger, what it implies, and one concrete implementation action.

## Inputs

One required input:
- `context` (string): a short description of the current situation.

Examples:
- `/upgrade-trigger: We have 20 customers, on-call is getting paged weekly, and deployments are risky because we lack rollback.`
- `/upgrade-trigger: We’re spending more time debugging integrations than shipping; different agents use different tool versions.`

## Outputs

Return **EXACTLY one** of the following:

### Output A — needs context
If the context is missing/too vague, output exactly:
- `provide context`

### Output B — upgrade decision
Otherwise output **EXACTLY 3 lines** (no extra whitespace lines), each line one sentence max:
- `Signal: <observable trigger>`
- `Meaning: <what it implies about system maturity>`
- `Action: <one specific next implementation>`

Hard constraints:
- No bullet points.
- No multiple options.
- No paragraphs.
- Base only on the provided context.

## Deterministic workflow (must follow)

Tools used: none.

### Step 1 — Validate context
If any of the following are true, output `provide context`:
- context is missing
- context is only whitespace
- context is shorter than 20 characters
- context contains no observable symptom keywords (case-insensitive match) from this set:
  - `incident`, `outage`, `paged`, `on-call`, `rollback`, `debug`, `flaky`, `drift`, `security`, `auth`, `permission`, `compliance`, `audit`, `latency`, `timeouts`, `scale`, `customers`, `users`, `integration`, `manual`, `repeatable`, `reproducible`, `handoff`, `multi-agent`

### Step 2 — Choose the dominant upgrade theme
Pick exactly one theme using the first matching rule below (top-to-bottom priority):

1) **Security / access control** if context mentions any of:
   - `security`, `breach`, `auth`, `authorization`, `permission`, `token`, `secret`

2) **Reliability / incident response** if context mentions any of:
   - `incident`, `outage`, `paged`, `on-call`, `rollback`, `postmortem`

3) **Scale / performance** if context mentions any of:
   - `scale`, `spike`, `latency`, `timeouts`, `queue`, `backlog`, `throughput`, `SLA`

4) **Governance / compliance** if context mentions any of:
   - `compliance`, `audit`, `PII`, `GDPR`, `SOC2`, `retention`

5) **Integration/tooling drift** if context mentions any of:
   - `integration`, `drift`, `version`, `inconsistent`, `debugging`, `manual steps`

6) **Coordination** if context mentions any of:
   - `multi-agent`, `handoff`, `ownership`, `conflicts`, `duplicate work`

If none match, default to **Reliability / repeatability**.

### Step 3 — Emit the 3 lines
Construct the output as:
- `Signal:` must quote an observable symptom from the context (paraphrase allowed, but it must be directly grounded).
- `Meaning:` must explain why that symptom indicates MVP constraints are failing.
- `Action:` must be one concrete implementation (a single next step), selected by theme:

Theme → Action templates (choose exactly one):
- Security / access control → implement role-based access control and secret handling policy.
- Reliability / incident response → implement deploy rollback + incident runbook + error budget tracking.
- Scale / performance → implement queueing/backpressure and latency SLO dashboards.
- Governance / compliance → implement audit logging and PII redaction with retention policy.
- Integration/tooling drift → implement a tool/agent registry with pinned versions and validation.
- Coordination → implement a single source of truth for tasks and a handoff protocol.

## Failure modes

The only allowed failure output is exactly:
- `provide context`

## Boundary rules (privacy + safety)

- Do not request or output secrets.
- Do not include personally identifying information beyond what the user already included.
- Do not propose destructive actions.
- No tool use, no network access, no file writes.

## Toolset

- (none)

## Acceptance tests

1. **Behavioral (negative): missing context**
   - Input: `/upgrade-trigger:`
   - Expected output (exact): `provide context`

2. **Behavioral (negative): too short/vague context**
   - Input: `/upgrade-trigger: it is broken`
   - Expected output (exact): `provide context`

3. **Behavioral: output is exactly three lines**
   - Input: `/upgrade-trigger: We have weekly on-call pages and no rollback; releases cause incidents.`
   - Expected:
     - Output has exactly 3 lines.
     - Line 1 starts with `Signal: `, line 2 with `Meaning: `, line 3 with `Action: `.

4. **Behavioral: security theme wins by priority**
   - Input: `/upgrade-trigger: We had an outage and also found permissions are unmanaged; secrets are in logs.`
   - Expected:
     - Line 3 (Action) mentions implementing access control/secret handling (security), not rollback/runbook.

5. **Behavioral: integration/tooling drift maps to registry action**
   - Input: `/upgrade-trigger: Debugging integrations takes longer than building because different agents use different tool versions and workflows drift.`
   - Expected:
     - Line 3 is exactly: `Action: implement a tool/agent registry with pinned versions and validation.`

6. **Behavioral: no extra text**
   - Input: any valid context.
   - Expected: output contains no bullets, no blank lines, and no extra headings.

7. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/upgrade-trigger/SKILL.md
```
Expected: `PASS`.

8. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/upgrade-trigger/SKILL.md
```
Expected: `PASS`.
