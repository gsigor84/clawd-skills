---
name: tool-installer
description: "Stage 3 of /vibe. Parse a TOOL AUDIT REPORT, request explicit approval, install missing tools using only the report’s INSTALL PLAN commands, verify, and emit a parseable result."
---

# tool-installer (internal)

## Trigger contract

This is an internal stage in the `/vibe` pipeline.

Trigger only when the input includes a plain-text `TOOL AUDIT REPORT` produced by `tool-auditor` and contains:
- `SKILL NAME:`
- `TRIGGER:`
- `VERDICT:` with one of: `ALL TOOLS READY` | `TOOLS MISSING` | `AUDIT INCOMPLETE`
- If `VERDICT: TOOLS MISSING`, an `INSTALL PLAN:` section with one or more numbered install commands.

This skill supports a two-turn flow:
- Turn 1 (TOOLS MISSING): ask for confirmation and stop.
- Turn 2: input contains the original report plus the user reply; if reply is YES → install; else cancel.

## Use

Use this stage to safely install missing helper tools required to build a skill. It never invents install commands; it only runs commands explicitly listed in the upstream `INSTALL PLAN`, and only after explicit user approval.

## Inputs

A single plain-text message containing:

1) The full `TOOL AUDIT REPORT` from `tool-auditor`, and optionally
2) A user reply appended anywhere in the message (for the second turn).

The user reply is interpreted as YES only if it contains (case-insensitive, whole-word match):
- `yes` or `y`

Any other reply (including empty/unclear) is treated as NO.

## Outputs

Output must be a structured plain-text block in exactly one of these formats.

### A) VERDICT: ALL TOOLS READY
Exactly one line:
- `ALL TOOLS READY: Everything needed is already installed. Continuing.`

### B) VERDICT: AUDIT INCOMPLETE
Exactly 3 lines:
- `AUDIT INCOMPLETE`
- `MESSAGE: I couldn’t confirm tool status. I didn’t install anything.`
- `NEXT: RETRY`

### C) VERDICT: TOOLS MISSING (turn 1 → confirmation)
Exactly this structure:

INSTALL CONFIRMATION
SKILL NAME: <from report>
TRIGGER: <from report>
TOOLS TO INSTALL:
1. <item 1 name> — <explanation from report if present, else: "required helper tool">
2. ...
QUESTION: Approve installing these tools? Reply YES to proceed or NO to cancel.
WAITING_FOR_CONFIRMATION: YES

### D) User says NO (or unclear)
Exactly 3 lines:
- `INSTALLATION CANCELLED`
- `MESSAGE: No changes were made.`
- `CHANGES_MADE: NO`

### E) User says YES and all installs succeed
Exactly this structure:

INSTALLATION COMPLETE
INSTALLED:
- <item 1>
- <item 2>
MESSAGE: Tools installed and verified.
CHANGES_MADE: YES

### F) Install fails
Exactly this structure:

INSTALLATION FAILED
FAILED STEP: <item>
REASON: <one-line reason>
CHANGES_MADE: PARTIAL

## Deterministic workflow (must follow)

### Tooling
- `exec`

### Global caps (hard limits)
- Max install steps: **10**
- Max command length per step: **400** characters
- Per-command timeout: **300** seconds

### Boundary rules (privacy + consent + disallowed)

Consent:
- Never run installs unless the user explicitly replied YES.

Disallowed commands (hard reject; do not execute):
- Any command containing `sudo`
- Any command containing `rm -rf` or `mkfs`
- Any command that pipes remote content into a shell, including patterns like `curl ... | sh`, `wget ... | bash`
- Any command that edits shell profiles (`.bashrc`, `.zshrc`) or writes outside `/Users/igorsilva/clawd/` (this stage must not modify user dotfiles)

Secrets:
- Do not print, request, or embed API tokens.
- If a verification command in the report contains an obvious token header (e.g., `X-Subscription-Token:`), do not execute it; treat verification as failed and stop with `INSTALLATION FAILED`.

Network:
- Allowed only as part of the exact install commands provided by the report.
- Do not add extra network calls.

### Step 1 — Parse the audit report
1) Extract `SKILL NAME`, `TRIGGER`, and `VERDICT`.
2) If `VERDICT` is missing or not one of the allowed values → output `AUDIT INCOMPLETE` block.

### Step 2 — Branch by verdict

#### 2A) ALL TOOLS READY
- Emit output A.

#### 2B) AUDIT INCOMPLETE
- Emit output B.

#### 2C) TOOLS MISSING
1) Parse the `INSTALL PLAN` into ordered steps.
   - Each step must have a tool/package name label and an exact command.
2) If there are 0 steps → output:
   - `AUDIT INCOMPLETE`
   - `MESSAGE: I couldn’t find an INSTALL PLAN. I didn’t install anything.`
   - `NEXT: RETRY`
3) If steps > 10 → output:
   - `INSTALLATION FAILED`
   - `FAILED STEP: (plan)`
   - `REASON: plan_too_large. Max 10 install steps.`
   - `CHANGES_MADE: NO`

### Step 3 — Determine whether to ask or install
- If the input does not contain a YES reply → emit output C (confirmation) and stop.
- If the input contains a YES reply → proceed to Step 4.
- Otherwise (explicit NO/unclear) → emit output D.

### Step 4 — Safety check commands
For each install step command:
- If command length > 400 → fail.
- If command matches any disallowed pattern → fail.

On failure, emit output F with:
- `REASON: disallowed_command. Refusing to run install command.`

### Step 5 — Execute installs sequentially
For each step in order:
1) Run the install command exactly as given using `exec`.
2) If the command exits non-zero → emit output F and stop.

### Step 6 — Verify installations
Verification must be deterministic and must not invent checks.

Rules:
- If the report includes an explicit `VERIFY:` command for a tool, execute it (subject to the same disallowed-command rules).
- If the report does not include `VERIFY:` for a tool, treat verification as `UNKNOWN` and fail with:
  - `REASON: verification_missing. Report did not provide verify command.`

If any verify command contains a token header like `X-Subscription-Token:` → fail with:
- `REASON: verification_requires_secret. Refusing to run token-bearing verification command.`

### Step 7 — Emit completion
If all installs and verifies succeed, emit output E.

## Failure modes

If the input is missing a parseable audit report, output exactly:
- `AUDIT INCOMPLETE`
- `MESSAGE: I couldn’t confirm tool status. I didn’t install anything.`
- `NEXT: RETRY`

## Toolset

- `exec`

## Acceptance tests

1. **Behavioral: ALL TOOLS READY is one-line**
   - Run: `/tool-installer <TOOL AUDIT REPORT with VERDICT: ALL TOOLS READY>`
   - Expected output is exactly one line:
     - `ALL TOOLS READY: Everything needed is already installed. Continuing.`

2. **Behavioral: AUDIT INCOMPLETE emits the 3-line block**
   - Run: `/tool-installer <TOOL AUDIT REPORT with VERDICT: AUDIT INCOMPLETE>`
   - Expected output is exactly:
     - `AUDIT INCOMPLETE`
     - `MESSAGE: I couldn’t confirm tool status. I didn’t install anything.`
     - `NEXT: RETRY`

3. **Behavioral: TOOLS MISSING (turn 1) asks for confirmation**
   - Run: `/tool-installer <TOOL AUDIT REPORT with VERDICT: TOOLS MISSING and INSTALL PLAN>`
   - Expected output contains:
     - `INSTALL CONFIRMATION`
     - `WAITING_FOR_CONFIRMATION: YES`

4. **Behavioral: unclear reply cancels safely (turn 2)**
   - Run: `/tool-installer <same report>\nUSER_REPLY: maybe`
   - Expected output is exactly:
     - `INSTALLATION CANCELLED`
     - `MESSAGE: No changes were made.`
     - `CHANGES_MADE: NO`

5. **Behavioral: disallowed command is rejected without executing**
   - Run: `/tool-installer <TOOLS MISSING report + USER_REPLY: yes + INSTALL PLAN command contains sudo>`
   - Expected output contains:
     - `INSTALLATION FAILED`
     - `REASON: disallowed_command. Refusing to run install command.`

6. **Behavioral: token-bearing verification is refused**
   - Run: `/tool-installer <TOOLS MISSING report + USER_REPLY: yes + VERIFY command contains X-Subscription-Token:>`
   - Expected output contains:
     - `INSTALLATION FAILED`
     - `REASON: verification_requires_secret. Refusing to run token-bearing verification command.`

7. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/tool-installer/SKILL.md
```
Expected: `PASS`.

8. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/tool-installer/SKILL.md
```
Expected: `PASS`.
