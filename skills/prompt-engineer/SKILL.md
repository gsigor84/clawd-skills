---
name: prompt-engineer
description: "# prompt-engineer — Design, critique, and iterate prompts that reliably produce the desired output by enforcing structure (Persona/Task/Context/Format), adding grounding + permission-to-fail, and using multi-branch exploration + adversarial critique for complex tasks."
---

# prompt-engineer

Design, critique, and iterate prompts that reliably produce the desired output by enforcing structure (Persona/Task/Context/Format), adding grounding + "permission to fail", and using multi-branch exploration and adversarial critique when the task is complex.

## Trigger
`/prompt-engineer <goal + constraints + context>`
`/prompt-engineer --nietzsche <text or idea>`

Use this skill when:
- A prompt is producing vague/generic/unpredictable output.
- You need a reusable prompt template for a recurring task (writing, coding, research, planning).
- You need to reduce hallucinations by adding grounding constraints and explicit failure behaviour.
- A task is complex enough to benefit from multi-branch ideation (Trees of Thought) or adversarial critique (playoff method).
- You want a Nietzschean analysis frame that translates conflict vs conformity into an actionable, everyday language.

## Use

### Default mode (prompt engineering)
1) **Clarify intent (offline first):** write a 1–3 sentence goal and what “good” looks like.
2) **Draft a structured prompt** using the Four Pillars:
   - Persona
   - Task
   - Context (ABC: Always Be Contexting)
   - Format (explicit output requirements)
3) **Add reliability constraints**:
   - “If you don’t know / it’s not in the provided context, say ‘I don’t know’.”
   - Ask the model what questions it needs answered to do the task well.
4) **If complex:** choose one:
   - **CoT:** request step-by-step reasoning *internally*, then a clean final answer.
   - **ToT:** generate 2–4 distinct branches, evaluate, then synthesise a “golden path”.
   - **Adversarial validation:** competing drafts + harsh critic + final synthesis.
5) **Iterate:** treat poor output as a signal that the prompt is missing constraints/context; refine and re-run.
6) **Save winners:** capture the final prompt as a template for reuse.

### --nietzsche mode (analysis frame)
When invoked as `/prompt-engineer --nietzsche <text or idea>`, produce an accessible analysis for everyday working people (not scholars) using this fixed framework:

**Persona:** Engaging Educator — accessible, conversational, no heavy jargon, use simple analogies.

**Three mandatory pillars:**
1) **HERD PRESSURE** — map conflict against conformity, Last Man comfort-seeking, Bad Conscience used as guilt tool.
2) **WILDERNESS** — Ontological Interval from breaking away, Active Nihilism destroying hollow values, Self-Overcoming in isolation.
3) **NEW COVENANT** — Übermensch path, Will to Power for self-perfection, Sublimation into new community, Amor Fati embracing the journey.

**Structure:** Introduction → The Problem → The Transition → The Solution.

**Output:** a single, readable analysis in plain language.

## Inputs
Provide at least:
- **Goal:** what you want and why.
- **Audience:** who it’s for.
- **Constraints:** length, tone, do/don’t, required inclusions.
- **Context:** facts, links, documents, examples to emulate (few-shot).
- **Output format:** bullets/table/JSON/sections, etc.

Optional:
- **Examples (few-shot):** 1–3 short exemplars of ideal output.
- **Failure tolerance:** what to do when info is missing (ask questions vs say “I don’t know”).
- **Exploration mode:** none | CoT | ToT | adversarial.

## Outputs
- A **power prompt** (ready to paste) with Persona/Task/Context/Format.
- If requested, **variants** (branches) + evaluation + a synthesised best version.
- A short **prompt checklist** to prevent regressions.

## Failure modes
- **Messy thinking → messy prompts:** goal and success criteria are unclear.
  - Fix: rewrite goal + success criteria; simplify the task.
- **Vague prompts → generic “garbage” output:** missing persona, missing constraints, or missing context.
  - Fix: enforce Four Pillars; add explicit constraints and context.
- **Hallucinations:** model fills gaps due to missing info or ambiguous requirements.
  - Fix: add “permission to fail”; require citations/grounding to provided context.
- **Wrong tone/format:** output is correct but unusable.
  - Fix: specify format, length, and tone; use few-shot exemplars.
- **Complex tasks solved “averagely”:** first answer is statistically bland.
  - Fix: ToT branches + evaluation; adversarial critique/playoff.

## Toolset
- exec (shell): run greps, run the skill validators
- read: inspect existing prompt templates/examples
- write: save finalised prompt templates (optional)

## Acceptance tests

1. Run `/skill-forge --topic "prompt engineering" --skill-name prompt-engineer --web-research` — expected output: `~/clawd/skills/prompt-engineer/SKILL.md` exists and the validators return PASS/PASS.

2. Run `grep -nE '^## (Trigger|Use|Inputs|Outputs|Failure modes|Toolset|Acceptance tests)$' ~/clawd/skills/prompt-engineer/SKILL.md` — expected output: each required heading appears exactly once.

3. Negative case: delete the `## Toolset` heading and re-run `validate_skillmd.py` — expected error message: validator FAIL mentioning missing required section(s).

4. When given a concrete task + constraints, the skill produces a prompt that contains **Persona**, **Task**, **Context**, and **Format**, and includes a “permission to fail” clause (behavioural expectation).

### Optional local checks
```bash
set -euo pipefail
FILE="/Users/igorsilva/clawd/skills/prompt-engineer/SKILL.md"
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py "$FILE"
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py "$FILE"
```
