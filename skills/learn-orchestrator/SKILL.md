---
name: learn-orchestrator
description: "Trigger: /learn: <pasted text>. Runs the full learn pipeline in one go (extract → map → study) from pasted text only. No file paths, no shell commands. Produces a full structured study guide and saves it under ~/clawd/learn/ using a fixed SOURCE_TITLE."
---

## learn-orchestrator — full pipeline from pasted text

### Trigger
User runs either:
- `/learn: <PASTE FULL SOURCE TEXT HERE>`
- `/learn: /absolute/path/to/file.txt`

### Hard rules
- User provides source text **once** (either pasted text or a local file path). Treat the resolved text as the full source.
- Do **not** ask for file paths (the user may supply one directly).
- Do **not** run shell commands or external Python.
- Run the pipeline **internally in sequence** (no pauses, no intermediate user steps).
- **Text size limit:** if the resolved text is too large, process only the first ~8,000–12,000 characters. Do not fail and do not ask the user to retry.
- Context-only: do not invent facts, definitions, or examples not present in the resolved text.

### Input handling (first step)
At the very start, interpret the user’s `/learn:` argument:

- **File path mode:** if the argument is a single string that starts with `/` and looks like a local path (e.g., `/Users/.../file.txt`), treat it as a file path.
  - Use the **built-in safe file read tool** (OpenClaw `read` capability) to read the file contents as text.
  - Replace the input with the file contents and continue the pipeline using that text.
  - If the file cannot be read, output exactly:
    - `ERROR: Unable to read file. Please check path.`

- **Text mode:** otherwise, treat the argument as pasted source text and continue.

### Safety check
If the resulting source text is empty / not meaningful (e.g., only a title, only a filepath, or whitespace), output exactly:
- `ERROR: Please paste source text`

---

## Output format (must follow exactly)
Return a single Markdown study guide with these sections in this order:

1. `## STEP 1 — EXTRACT`
2. `## STEP 2 — IDENTIFY BACKBONE`
3. `## STEP 3 — MAP RELATIONSHIPS`
4. `## STEP 4 — WRITE STUDY GUIDE`
5. `## STEP 5 — SAVE`
6. `## STEP 6 — CONFIRM`
7. `## STEP 7 — SYSTEM BLUEPRINT`
8. `## STEP 8 — IMPLEMENTATION PLAN`

---

## Pipeline

## STEP 0 — LEARNING GATE (ANTI-CRASH)

Before any processing:

1) Check input size and scope  
2) If content is large or multi-topic:
   → Output:
   Status: ok
   Step: /extract-concept: <input>
   Reason: split before ingest

3) If content is small and focused:
   → Output:
   Status: ok
   Step: /ingest: <input>
   Reason: safe to store

4) If unclear:
   → Output:
   Status: blocked
   Step: clarify input
   Reason: unclear content

Rules:
- NEVER process large files directly
- ALWAYS prefer atomic concepts
- DO NOT merge multiple concepts in one run

### STEP 1 — EXTRACT
**Clean extraction filter (required):**
- ONLY extract:
  - system concepts
  - architectural patterns
  - system components
  - mechanisms
- DO NOT extract:
  - variable names (e.g., `user_id`, `client_id`)
  - headers (e.g., `Authorization header`)
  - trivial fields/parameters
  - single-use example values
- If unsure, prefer the higher-level concept over low-level detail.

**Output format:**
- For each extracted item, include a short supporting phrase quoted verbatim from the text.
- Output one bullet per top-level item using this format:
  - `<item> — "<short phrase from text>"`

**Grouping low-level items (required):**
- If low-level items appear that are still useful, do NOT list them as separate bullets.
- Attach them under the closest parent concept bullet using a parenthetical note.
  - Example: `OAuth 2.0 — "..." (includes: client_id / client_secret)`

No analysis beyond extraction.

### STEP 2 — IDENTIFY BACKBONE (4–6 items)
- Choose 4–6 concepts from STEP 1 that act as structural “bridges” in the source.
- Output under:
  - `**Backbone Concepts**`

### STEP 3 — MAP RELATIONSHIPS
- For every non-backbone concept from STEP 1:
  - Assign it to exactly one backbone concept.
  - Explain why, grounded in wording/mechanism present in the pasted text.
- If the pasted text does not contain enough detail to justify a mapping, still assign it, but mark:
  - `(insufficient detail in pasted text)`

### STEP 4 — WRITE STUDY GUIDE
For each concept that is supportable from the pasted text, output:

```md
### [Number]. [Concept Name]
**Concept Note**
3–6 bullets, each bullet directly supported by the pasted text.

**Evidence (verbatim)**
1–3 short quotes (verbatim) from the pasted text that support the Concept Note.

**Backbone Link**
One sentence linking the concept to its assigned backbone from STEP 3 (mechanism-level).
```

Rules:
- If you cannot provide at least 1 verbatim quote for a concept, **skip** that concept.
- Track skipped concepts in `UNSUPPORTED_CONCEPTS` and report them in STEP 6.

### STEP 5 — SAVE
- Use a fixed title:
  - `SOURCE_TITLE: chapter-10-system-level-patterns`
- Save path must be exactly:
  - `/Users/igorsilva/clawd/learn/chapter-10-system-level-patterns-study-guide.md`
- Save the full rendered study guide Markdown to that path using the filesystem write tool (not shell).
- **Fallback:** if saving fails or is unavailable, still return the full study guide in the response and continue to STEP 6 (do not stop execution).

### STEP 6 — CONFIRM
- Print:
  - `Saved study guide: /Users/igorsilva/clawd/learn/chapter-10-system-level-patterns-study-guide.md`
- If any were skipped, print one additional line:
  - `Skipped concepts due to insufficient support in source: <comma-separated list>`
- Then print:
  - `Run /ingest /Users/igorsilva/clawd/learn/chapter-10-system-level-patterns-study-guide.md to load this into your knowledge base.`

### STEP 7 — SYSTEM BLUEPRINT
After STEP 6, generate:

#### STRICT SOURCE DISCIPLINE (CRITICAL)
- Use **ONLY** concepts from `## STEP 1 — EXTRACT`.
- Do **NOT** introduce new technologies, acronyms, or components that are not explicitly present as extracted items.
  - Example: do **not** mention `JWT`, `RBAC`, `mTLS`, `JWKS`, etc. unless those exact strings appear as items in STEP 1.
- When you reference a concept, use the **exact STEP 1 item text**.
- If a component is not in STEP 1, **do not include it** anywhere in STEP 7 (omit it rather than inventing).

#### Architecture Layers
Output architecture as layers:
- Identity Layer (Auth, IAM, tokens)
- Communication Layer (event bus, reactivity)
- Discovery Layer (registry)
- Governance Layer (compliance, policies)
- Control Layer (orchestration)

##### Control Layer (orchestration) (required content)
When you output the Control Layer, use this structure, but still obey STRICT SOURCE DISCIPLINE (only include bullets that are present in STEP 1):

```md
### Control Layer (orchestration)
- Components:
  - orchestration
  - system-level patterns
  - GenAI Maturity Model
- Responsibilities:
  - Coordinate agent interactions across identity, registry, and event systems.
  - Decide when and how agents execute tasks.
  - Apply system-level patterns progressively based on system maturity.
- Key mechanisms:
  - Orchestrated execution flow (agent → registry → event → action).
  - Pattern adoption guided by GenAI Maturity Model.
  - Central coordination of distributed agents.
- Failure risks:
  - Missing orchestration → no coordination across agents/tools
  - Missing system-level patterns → ad-hoc architecture, inconsistent production readiness
  - Missing GenAI Maturity Model → over-engineering or under-securing the system
```

If any of the listed component bullets are not present in STEP 1, omit those bullets (do not invent), and ensure failure risks only reference components that remain.

For each layer, output:

```md
### <Layer Name>
- Components: <bullet list> (ONLY STEP 1 items)
- Responsibilities: <bullet list> (ONLY using STEP 1 terms; no new nouns)
- Key mechanisms: <bullet list> (ONLY using STEP 1 terms; no new nouns)
- Failure risks: <bullet list> (concrete, system-level; format: "Missing X → consequence Y"; ONLY STEP 1 terms)
```

## SYSTEM FLOW (END-TO-END)
Write the end-to-end system flow as an 8-step numbered sequence. Use ONLY STEP 1 items. If a referenced component is missing from STEP 1, omit or replace with the closest STEP 1 item (do not invent).

1. Agent initiates task
2. Identity Layer authenticates (use only STEP 1 identity items present, e.g., `IAM`, `service accounts`, `access token`, `API gateway`, `permissions/scopes`, `token rotation`, `least privilege`)
3. Agent queries registry to discover required tool/agent (use STEP 1 registry items)
4. Communication Layer dispatches event via message bus/event stream (use STEP 1 comms items)
5. Target agent/tool executes action (orchestration applied) (use STEP 1 orchestration/system items)
6. Governance Layer intercepts and evaluates action against policy (use STEP 1 governance/compliance items)
7. Result is returned or blocked (express using STEP 1 terms only)
8. System logs, monitors, and feeds back into future decisions (include `monitoring` only if present in STEP 1)

## PRODUCTION CHECKLIST
Provide a checklist. Include an item ONLY if it exists in STEP 1 (exact match of the extracted item text).

Target checklist items (include only if present in STEP 1):
- IAM
- service accounts
- token rotation
- least privilege
- API gateway
- message bus/event stream
- backpressure
- dead-letter queues (DLQs)
- idempotency
- central registry
- governance services
- monitoring

## Output quality rules (STEP 7)
- Failure risks must be concrete and system-level (not vague), using the format: `Missing X → specific consequence Y`.
- No generic wording (avoid: “system may fail”).
- Must be implementation-aware and read like a real system design, not a summary.

Rules:
- No external knowledge.
- No fluff. Make it actionable.
- If something is not in STEP 1, omit it (do not invent).

---

### STEP 8 — IMPLEMENTATION PLAN
After STEP 7, generate:

`## STEP 8 — IMPLEMENTATION PLAN`

Purpose: turn the STEP 7 system blueprint into a buildable, minimal plan.

**Rules (CRITICAL):**
- Use ONLY concepts that appear in STEP 1 and STEP 7.
- Do not introduce new technologies unless explicitly extracted in STEP 1.
- Keep it minimal, concrete, and implementation-ready.
- No fluff.
- **Determinism:** given the same input, keep the output structure and naming consistent; prefer stable, repeated names (no random variations).

Output sections (in this order):

#### Services
- List concrete services to build, mapping each to one STEP 7 layer.
- **Limit:** maximum **5–7 services** total.
- Each service must map directly to a STEP 7 layer.
- Service names should be simple kebab-case.
- Only include a service if you can justify it using STEP 7 components.

#### API Contracts
- For each service, define minimal endpoints.
- **Limit:** max **2–4 endpoints per service**.
- Use consistent naming patterns:
  - `GET /resource`
  - `POST /action`
- No random/redundant endpoints.
- Do not introduce protocols/technologies not present in STEP 1.

#### Event Schema
- **Limit:** max **2 event types**.
- Use simple, reusable fields:
  - `event_type`
  - `agent_id`
  - `payload`
- Event types must be derived from STEP 1 concepts.
- If STEP 1 contains a specific event/topic string (e.g., `shipping_events topic`), you may use it.
- Otherwise, define events using STEP 1 terms only.

#### Data Structures
- Only include core objects:
  - agent
  - token
  - event
  - registry entry
- Avoid low-level fields unless essential.
- Use STEP 1 terms only for any labels.

#### Deployment Shape
- Describe, in plain text, how services interact, using STEP 1 terms only.
- Keep it to 5–8 bullets."}

---

## Notes
- This skill intentionally does not call other skills; it performs extract→map→study in one response to avoid multi-turn concurrency issues.

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
   - Run: `/learn-orchestrator <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/learn-orchestrator <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/learn-orchestrator/SKILL.md
```
Expected: `PASS`.
