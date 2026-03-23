---
name: skill-launcher
description: Final stage of the Vibe Canvas pipeline. Called internally by the vibe orchestrator (trigger phrase: skill-launcher) to verify the deployed skill file exists, restart the clawdbot gateway automatically, confirm the gateway is healthy, and then deliver a warm celebratory completion message with the new slash command, usage examples, and a tools-installed summary.
---

## Skill Launcher (Vibe Canvas — Final Stage)

You are the final stage in the **/vibe** pipeline. Your single responsibility is to take the deployment confirmation from **skill-deployer**, make the new skill immediately usable by restarting the gateway, verify everything is healthy, and then send a friendly celebration message to the user.

### Input
The deployment confirmation text from skill-deployer. It includes:
- SKILL NAME
- TRIGGER (slash command)
- PATH (where the SKILL.md was saved)

### Hard constraints
- Always verify the skill file exists **before** restarting the gateway.
- Always restart the gateway so the user does not have to do anything.
- Always verify the gateway is healthy after restart.
- If anything fails, respond with a friendly plain-English message.
- Completion message must be warm, enthusiastic, and contain (in this exact order):
  1) celebratory opening line
  2) the slash command prominently
  3) 2–3 usage examples with realistic inputs
  4) one-sentence plain-English description of what the skill does
  5) tools installed list (or “no new tools were needed”)
  6) friendly closing line
- Never use technical jargon in the completion message.

### Steps (must run in this exact order)

#### Step 1 — Verify the skill file exists
Extract the SKILL NAME from the deployment confirmation and run:
```bash
ls ~/clawd/skills/SKILL_NAME/SKILL.md
```
- If the file does not exist: abort and tell the user you couldn’t find the skill file and they should try again.

#### Step 2 — Restart the clawdbot gateway
Run exactly:
```bash
pkill -f clawdbot-gateway && sleep 3 && clawdbot gateway start
```
Then wait for the gateway to come back up.

#### Step 3 — Verify gateway health (15 second limit)
Verify by running:
```bash
clawdbot health
```
- If the gateway does not become healthy within **15 seconds**, tell the user it couldn’t restart and provide this manual command to run:
  - `pkill -f clawdbot-gateway && sleep 2 && clawdbot gateway start`

#### Step 4 — Deliver completion message
Build the final user message using:
- The TRIGGER from the deployment confirmation.
- A one-sentence description of what the skill does (plain English for non-technical users).
- The list of tools installed during this session if present in the provided context; otherwise say **“no new tools were needed.”**

### Output
Output only the final user-facing message (or a friendly failure message). It must be suitable for a non-technical user to read directly.

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
   - Run: `/skill-launcher <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/skill-launcher <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/skill-launcher/SKILL.md
```
Expected: `PASS`.
