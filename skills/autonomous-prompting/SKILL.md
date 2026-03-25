---
name: autonomous-prompting
description: "# autonomous-prompting — Build AI agent platforms that transition from passive chatbots to autonomous digital workers. Covers harness architecture, intent engineering, eval frameworks, and multi-agent coordination."
---

# autonomous-prompting

Build AI systems that generate their own prompts and operate autonomously — the shift from chatbots to digital workers.

## What Is Autonomous Prompting?

Autonomous prompting is the practice of building AI systems that:
- Generate their own prompts dynamically based on context
- Operate without constant human supervision
- Execute multi-day projects autonomously
- Self-correct using eval frameworks

The key insight: **AI model = brain in a jar. Harness = body that gives it hands, memory, and schedule.**

## Core Concepts

### 1. The Agent Harness

The harness (or scaffolding) is the environment built around an AI model that allows real work:
- **Tools**: Ability to interact with databases, browsers, file systems
- **Memory**: Persistent storage to remember past actions across sessions
- **Proactivity**: Wake up and act on schedule without being prompted

**Example**: Cursor's harness organizes agents into "planners" and "workers" that solved a graduate-level math problem autonomously over 4 days.

### 2. Intent Engineering

Since agents run autonomously for hours/days, you can't course-correct in real-time. You must encode:
- **Goals**: What the agent should achieve
- **Values**: How to prioritize when goals conflict
- **Boundaries**: What the agent must NEVER do

**Critical**: Without intent engineering, agents optimize ruthlessly and may destroy production (e.g., deleting live databases instead of temp files).

### 3. Evaluations (Evals)

An **Eval** is an automated test that verifies if agent output is correct and safe.

The key human skill: **Rejection** — identify subtle flaws, articulate why, encode as permanent eval.

**Example**: ChatGPT Health correctly identified respiratory failure in internal reasoning but output "wait 24-48 hours" instead of "immediate ER" — evals catch this gap.

### 4. Multi-Agent Coordination

Break massive tasks across specialized agents that:
- Work in parallel
- Verify each other's work
- Iterate toward solution

**Extreme**: "Dark Factory" — humans write specs and evals, machines write 100% of code. StrongDM runs with 3 humans, 90% of Claude Code was written by Claude Code itself.

## Key Terminology

| Term | Definition |
|------|-------------|
| **Harness** | Environment around AI that gives tools, memory, proactivity |
| **MCP** | Model Context Protocol — standard interface for AI to read/write external tools |
| **Intent Engineering** | Encoding goals, values, boundaries before task starts |
| **Eval** | Automated test to verify agent output correctness |
| **Dark Factory** | 100% autonomous code generation with human specs only |

## The Shift: Prompting → Specification

| Old Way | New Way |
|---------|---------|
| Chat-based iteration | Single spec upfront |
| Real-time course correction | Intent engineering |
| Human does the work | Human writes evals, agents execute |
| Teams of humans | Strike teams (5 humans + AI) |

## Toolset

- read (analyze specs, outputs)
- write (create specs, evals)
- web_search (research frameworks)
- sessions_spawn (multi-agent orchestration)

## Use When

- Building autonomous AI agents
- Designing eval frameworks for AI safety
- Creating self-improving pipelines
- Moving from chatbot to digital worker workflows

## Failure Modes

- No intent boundaries → agent destroys production
- No evals → silent failures on long-horizon tasks
- Single agent → can't handle massive multi-day projects
- No memory → agent forgets context between sessions

## Acceptance Criteria

1. Can explain harness vs. model distinction
2. Can design intent engineering for autonomous agents
3. Can create eval frameworks to catch agent failures
4. Understands multi-agent coordination patterns
5. Knows when to use dark factory vs. human-in-loop