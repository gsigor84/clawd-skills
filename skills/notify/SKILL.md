---
name: notify
description: "Internal: send Igor a WhatsApp status update when a long-running batch completes or halts on double-fail."
---

## Trigger contract

This is an internal-only skill.

Trigger when Adam needs to proactively message Igor on WhatsApp:

1) Batch completion
- `/notify done <summary>`
- `/notify completion <summary>`

2) Batch halt (double-fail)
- `/notify halt <skill-name> <optional-notes>`
- `/notify stopped <skill-name> <optional-notes>`

Input parsing:
- If the first argument is `done` or `completion`, treat the remainder of the message as the human summary.
- If the first argument is `halt` or `stopped`, the next token is the `<skill-name>` and the remainder is optional notes.

## Deterministic agent workflow

### Step 1 - Classify notification type
- If mode is `done|completion` → type = completion.
- If mode is `halt|stopped` → type = halt.
- Otherwise → Failure modes.

### Step 2 - Construct WhatsApp message (exact templates)

Completion message template:
- `✅ Batch done. <summary>`

Halt message template:
- `⚠️ Stopped at <skill-name>. Failed judge twice. Needs review.`

Notes handling:
- Ignore optional notes for the outbound message unless Igor explicitly requested extra detail.

### Step 3 — Send WhatsApp message

Use `exec` to run OpenClaw's message CLI (do not call vendor APIs directly):

```bash
OPENCLAW_GATEWAY_TOKEN="nGAnv9-os_c7BGgi3uN1H42nZwe53CZH5J9AJfxt1uk" npx --yes openclaw message send \
  --channel whatsapp \
  --target +447533464436 \
  --message "<constructed-message>"
```

Hard rule:
- Send exactly one WhatsApp message per invocation.

### Step 4 - Return local confirmation
Return exactly one line:
- `OK: notified`

## Boundary rules

- Do not send messages to any number other than `+447533464436`.
- Do not include sensitive content (file contents, API keys, tokens) in the outbound message.
- Do not attach media.
- If the constructed message exceeds 240 characters, truncate the `<summary>` to fit and append `...`.

## Use

Use this skill at the end of long-running autonomous batches (or when halting due to a double-fail) to ensure Igor gets a short status update on WhatsApp.

## Inputs

One of:
- `/notify done <summary>`
- `/notify completion <summary>`
- `/notify halt <skill-name> [notes...]`
- `/notify stopped <skill-name> [notes...]`

## Outputs

- On success: `OK: notified`
- On failure: exact error string from Failure modes

## Failure modes

- Unknown mode:
  - `ERROR: invalid notify mode. Use: /notify done <summary> OR /notify halt <skill-name>`

- Missing summary for completion:
  - `ERROR: missing summary. Usage: /notify done <summary>`

- Missing skill-name for halt:
  - `ERROR: missing skill-name. Usage: /notify halt <skill-name>`

- Send failed:
  - `ERROR: failed to send WhatsApp message.`

## Toolset

- `exec`

## Acceptance tests

1. **Completion: sends exact template**
   - Run: `/notify done 12 pass, 2 fail`
   - Expected output: exactly one WhatsApp send via exec (`openclaw message send`), with message starting `✅ Batch done. 12 pass, 2 fail`.

2. **Halt: sends exact template**
   - Run: `/notify halt vector-mapper`
   - Expected output: exactly one WhatsApp send via exec, with message exactly `⚠️ Stopped at vector-mapper. Failed judge twice. Needs review.`

3. **Missing summary**
   - Run: `/notify done`
   - Expected error message (exact): `ERROR: missing summary. Usage: /notify done <summary>`

4. **Missing skill-name**
   - Run: `/notify halt`
   - Expected error message (exact): `ERROR: missing skill-name. Usage: /notify halt <skill-name>`

5. **Invalid mode**
   - Run: `/notify foo bar`
   - Expected error message (exact): `ERROR: invalid notify mode. Use: /notify done <summary> OR /notify halt <skill-name>`

6. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/notify/SKILL.md
```
Expected: `PASS`.

7. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/notify/SKILL.md
```
Expected: `PASS`.
