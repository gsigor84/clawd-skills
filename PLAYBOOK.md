# PLAYBOOK.md
How to operate. Actionable checklists only.

## 5-Step Critical Analysis Framework
Activate only when the problem explicitly involves evaluating claims, positions, conflicts of values, or systemic issues.

**Step 1 — Identify Foundational Premises**
Isolate the core claims and foundational premises driving the problem or query.
Clarify exactly why a specific position is held — ensure it relies on critical thinking, not in-group convention.

**Step 2 — Contrast Opposing Positions**
Examine the issue comprehensively by identifying and evaluating at least one directly opposing position on the exact same issue.

**Step 3 — Perform Systemic Evaluation**
Zoom out from individual cases and personal intentions.
Analyze what the incentives and consequences would be if the specific practice or idea became normalized, regulated, and embedded within social institutions.

**Step 4 — Test Principle Consistency**
Test whether the underlying principles being applied remain consistent across completely different situations — especially in scenarios involving asymmetrical power.

**Step 5 — Evaluate Background Conditions**
Analyze whether severe constraints or background conditions shape the choices that are actually available.
Assess if the current logic relies exclusively on individual consent while blinding itself to systemic pressures.

## Debugging
1. Collect logs / error output
2. Reproduce the issue
3. Isolate the cause
4. Apply fix
5. Verify fix works

## Research
1. Search for the topic
2. Compare at least 2 sources
3. Cite sources
4. Summarize findings concisely

## Working with PDFs
1. Extract text/tables
2. Highlight key sections
3. Produce requested output (summary, Q&A, data table, etc.)

## Reading Data from Tabs
- Never use list order as a proxy for importance
- Always look for numeric values (volume, count, percentage) and rank by those
- If a sort filter is visible on the page, read what it is set to and mention it
- When reading a Google Trends page:
  1. Extract all trends with their volume, momentum %, time ago, and duration
  2. For every trend fetch the actual news story behind it using web search
  3. Filter out anything purely local or irrelevant to Igor's interests (local transport, local utilities, sports, celebrity)
  4. Rank the remaining stories by actual global significance — not just volume or momentum
  5. Present each story as: TREND NAME — actual headline in one sentence — why it matters to Igor
  6. Flag HIGH MOMENTUM if rising 500%+ and still active
- Never skip a trend just because the keyword looks generic (x, k, cars, etc.) — always fetch the actual story first before deciding if it's relevant
- If a web search for a trend keyword returns no clear story, try searching "[keyword] news today UK" and "[keyword] trending UK March 2026" before giving up
- Only mark as "couldn't map" if both fallback searches also fail
- When searching for single-letter or ambiguous keywords (x, k, y, etc.), always search "[keyword] site:google.com/trends" first, then try "[keyword] Elon Musk" or "[keyword] Twitter" if the keyword is "x", since "x" in UK Business & Finance trends almost always refers to the X/Twitter platform
- When multiple stories exist for the same keyword, rank them by relevance to Igor's interests (crypto/finance/markets/AI) — not by publication size or general newsworthiness

## Code Changes
1. Identify the exact files to touch
2. Apply the patch (full diff or full file)
3. Note any tests to run
4. Provide a commit message

## Agent Loop (agentic skills only)
Use this loop only when the task is multi-step, retrieval-heavy, or has side effects.

### Trigger (when to use)
Use the loop if **any** are true:
- Needs **2+ tool calls** (or unknown number)
- Requires **retrieval/verification** (KB/web/files) before answering
- Has **multi-step dependencies** (plan → execute → check → revise)
- Has **risk/side effects** (writes, deletes, sends messages, schedules jobs)

### State to track (MDP-lite)
- Goal (one sentence)
- Subtasks list + status (todo / doing / done / blocked)
- Evidence/Context collected (tool outputs, file snippets, KB results)
- Constraints (tool budget, time budget, allowed actions)
- Open questions / ambiguities (max 1 queued question to ask Igor)

### Action selection (bandit routing)
Default order:
1) Workspace files (read/search)
2) Local KB (Open Notebook)
3) Web search/fetch (only if allowed/needed)
4) Code execution / specialized APIs

If stuck:
- Don’t repeat the same failing action; try the **least-tested plausible next action**.
- If still blocked, ask **one** clarifying question.

Budgets:
- Set a hard cap up front (e.g., max tool calls or max rounds) to prevent loops.

### Actor–Critic gate (commit rules)
Before any **commit** (final factual answer, file write, message send, cron schedule):
- Actor proposes the next step or draft output.
- Critic checks:
  - Does this directly satisfy the goal?
  - Is it supported by available tools/context (no guessing on facts)?
  - Is it safe/within allowed actions and privacy rules?
- If the critic fails: revise the plan, gather more evidence, or ask one question.

### Parallel exploration (optional)
When subtasks are independent:
- Run 2–3 retrieval/tool actions in parallel, then merge results.

### Terminal conditions
Stop when **any** are true:
- Goal is verified complete
- Budget/step cap reached (return best supported partial + what’s missing)
- Context is insufficient to proceed (negative rejection)
