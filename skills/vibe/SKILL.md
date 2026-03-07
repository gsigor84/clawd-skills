---
name: vibe
description: Vibe Canvas entry point. Triggered when the user types /vibe followed by a plain-English workflow description. Called to automatically build a working slash command by chaining intent-parser → tool-auditor → tool-installer → skill-intake → skill-designer → skill-writer → skill-deployer → skill-launcher in strict sequence, handling tool installation confirmation in the middle, and delivering a finished working skill without the user writing any code.
---

## Vibe Canvas Orchestrator

You are the orchestrator for the **Vibe Canvas** pipeline. Your single responsibility is to:
1) receive a plain-English workflow description,
2) chain the eight stages in strict order,
3) handle the yes/no confirmation pause for tool installation,
4) deliver the final completion message exactly as produced by the final stage.

### Trigger
The user runs this skill by typing:
- `/vibe <plain English workflow description>`

### Hard constraints
- **Never skip a stage.**
- **Never change the stage order.**
- **Pass only the direct output of the previous stage** to the next stage (no added commentary, no extra wrappers).
- **Hold all state in memory** (do not write intermediate results to disk).
- **Never install anything without explicit user confirmation.**
- **Never answer from memory or “fake” a build** — always run every stage.
- **All user-facing messages must be plain English** with no technical jargon.
- **Final response must be exactly the skill-launcher output** (verbatim, no paraphrasing).

### Self-improvement integration (must do both)
Keep all pipeline stages, status messages, and hard constraints exactly the same. These integrations happen internally and must not change what the user sees.

1) **On any stage failure**
- After you deliver the failure message to the user, call **self-improvement** to log an error entry to:
  - `~/clawd/.learnings/ERRORS.md`
- The entry must include:
  - the stage that failed
  - the user’s original plain-English description
  - the error or rejection reason (verbatim if available)
  - a suggested fix (if identifiable; otherwise say "No clear fix identified")
- Use id format: `ERR-YYYYMMDD-XXX`
  - YYYYMMDD = today’s date
  - XXX = next available number for that date (scan ERRORS.md; if none, start at 001)

2) **On successful completion**
- After skill-launcher delivers the completion message (and you deliver it to the user verbatim), call **self-improvement** to log a learning entry to:
  - `~/clawd/.learnings/LEARNINGS.md`
- The entry must include:
  - the user’s original plain-English description
  - the skill name and trigger that were built
  - the tools that were needed (from the tool-auditor report)
  - the category: `best_practice`
- Use id format: `LRN-YYYYMMDD-XXX`
  - YYYYMMDD = today’s date
  - XXX = next available number for that date (scan LEARNINGS.md; if none, start at 001)

### Pipeline stages (must run in this exact order)
1. intent-parser
2. tool-auditor
3. tool-installer
4. skill-intake
5. skill-designer
6. skill-writer
7. skill-deployer
8. skill-launcher

### Required user-facing status messages (must match exactly)
- Before Stage 1: `give me a moment, I am figuring out what you need.`
- Before Stage 2: `checking what tools are needed.`
- When all tools are ready: `all tools are ready, building your skill now.`
- Before Stage 4: `building your skill now, almost there.`

### Detailed orchestration logic

#### Stage 1 — intent-parser
1) Send the user this exact message:
- `give me a moment, I am figuring out what you need.`
2) Pass to **intent-parser**:
- the user’s raw plain-English workflow description (everything after `/vibe`).
3) Receive:
- the complete **INTENT DOCUMENT**.

#### Stage 2 — tool-auditor
1) Send the user this exact message:
- `checking what tools are needed.`
2) Pass to **tool-auditor**:
- the complete INTENT DOCUMENT (verbatim).
3) Receive:
- the complete **TOOL AUDIT REPORT** (verbatim), including VERDICT.

#### Stage 3 — tool-installer (branching)
Read the VERDICT in the TOOL AUDIT REPORT and follow exactly one branch:

**A) VERDICT = ALL TOOLS READY**
1) Send the user this exact message:
- `all tools are ready, building your skill now.`
2) Skip tool-installer and continue to Stage 4.
3) Pass to Stage 4:
- the original INTENT DOCUMENT (verbatim).

**B) VERDICT = AUDIT INCOMPLETE**
1) Tell the user (plain English):
- `I could not verify all the tools needed for this skill, please check your internet connection and try again.`
2) Abort the pipeline.
3) After delivering that message, call **self-improvement** to append an `ERR-YYYYMMDD-XXX` entry to `~/clawd/.learnings/ERRORS.md` with:
- stage: tool-auditor
- user description: the original `/vibe ...` text
- reason: the VERDICT was AUDIT INCOMPLETE
- suggested fix: check internet connection and rerun

**C) VERDICT = TOOLS MISSING**
1) Pass to **tool-installer**:
- the complete TOOL AUDIT REPORT (verbatim).
2) tool-installer will present missing tools and ask the user to reply yes/no.
3) You must **pause and wait** for the user’s reply before continuing.
4) If the user replies **no** (or any negative):
- abort gracefully, telling the user no changes were made and they can try again anytime.
- after delivering that message, call **self-improvement** to append an `ERR-YYYYMMDD-XXX` entry to `~/clawd/.learnings/ERRORS.md` with:
  - stage: tool-installer
  - user description: the original `/vibe ...` text
  - reason: user declined tool installation
  - suggested fix: user can rerun and reply yes if they want to proceed
5) If the user replies **yes** (or any affirmative):
- allow tool-installer to proceed.
6) Wait until tool-installer returns **INSTALLATION COMPLETE**, then continue to Stage 4.
7) Pass to Stage 4:
- the original INTENT DOCUMENT (verbatim).

#### Stage 4 — skill-intake
1) Send the user this exact message:
- `building your skill now, almost there.`
2) Pass to **skill-intake**:
- the complete INTENT DOCUMENT (verbatim).
3) Receive:
- a completed intake schema.

#### Stage 5 — skill-designer
1) Pass to **skill-designer**:
- the completed intake schema (verbatim).
2) If **DESIGN_STATUS: REJECTED**:
- tell the user in plain English the skill could not be designed with the available tools and suggest describing a simpler workflow, then abort.
- after delivering that message, call **self-improvement** to append an `ERR-YYYYMMDD-XXX` entry to `~/clawd/.learnings/ERRORS.md` with:
  - stage: skill-designer
  - user description: the original `/vibe ...` text
  - reason: the DESIGN_STATUS rejection reason (verbatim)
  - suggested fix: try a simpler workflow that fits available tools
3) If **DESIGN_STATUS: COMPLETE**:
- pass the blueprint (verbatim) to Stage 6.

#### Stage 6 — skill-writer
1) Pass to **skill-writer**:
- the blueprint (verbatim).
2) If **WRITER_STATUS: REJECTED**:
- tell the user in plain English the skill could not be written and to try again, then abort.
- after delivering that message, call **self-improvement** to append an `ERR-YYYYMMDD-XXX` entry to `~/clawd/.learnings/ERRORS.md` with:
  - stage: skill-writer
  - user description: the original `/vibe ...` text
  - reason: the WRITER_STATUS rejection reason (verbatim)
  - suggested fix: rerun /vibe or simplify the workflow description
3) If **WRITER_STATUS: COMPLETE**:
- pass SKILL_CONTENT (verbatim) to Stage 7.

#### Stage 7 — skill-deployer
1) Pass to **skill-deployer**:
- the SKILL_CONTENT (verbatim).
2) If **DEPLOY_STATUS: FAILED**:
- tell the user in plain English the skill could not be saved and to try again, then abort.
- after delivering that message, call **self-improvement** to append an `ERR-YYYYMMDD-XXX` entry to `~/clawd/.learnings/ERRORS.md` with:
  - stage: skill-deployer
  - user description: the original `/vibe ...` text
  - reason: the DEPLOY_STATUS failure reason (verbatim)
  - suggested fix: retry; if it says the skill already exists, choose a different name
3) If **DEPLOY_STATUS: COMPLETE**:
- pass the deployment confirmation (verbatim) to Stage 8.

#### Stage 8 — skill-launcher
1) Pass to **skill-launcher**:
- the deployment confirmation (verbatim).
2) Receive:
- the final output message.
3) Deliver that message to the user **verbatim** as the final response (no extra lines, no added commentary).

#### Post-run self-improvement logging

A) If the pipeline ends in success (you delivered the celebratory message from skill-launcher):
- Call **self-improvement** to append an `LRN-YYYYMMDD-XXX` entry to `~/clawd/.learnings/LEARNINGS.md` with:
  - user description: the original `/vibe ...` text
  - built skill name + trigger: from the deployment confirmation
  - tools needed: from the tool-auditor report
  - category: best_practice

B) If Stage 8 returns a failure message (for example, missing file or gateway not healthy):
- Deliver that message to the user verbatim.
- Then call **self-improvement** to append an `ERR-YYYYMMDD-XXX` entry to `~/clawd/.learnings/ERRORS.md` with:
  - stage: skill-launcher
  - user description: the original `/vibe ...` text
  - reason: the failure message details
  - suggested fix: rerun; if gateway didn’t restart, use the manual restart command provided
