---
name: ai-agent-platforms
description: "# ai-agent-platforms — Build and understand AI agent platforms: agent vs workflow distinction, tools/actions (MCP), memory systems (RAG), multi-agent systems, platform governance, and enterprise deployment."
---

# ai-agent-platforms

Understand and build AI agent platforms — the infrastructure for autonomous AI workers.

## Trigger

`/ai-agent-platforms` — get a comprehensive understanding of AI agent platforms

## What Is an AI Agent Platform?

An AI agent platform is the underlying infrastructure that allows developers to securely build, manage, and scale artificial intelligence agents across an organization. While a standard AI chatbot simply generates text, an AI agent acts as a digital worker that can autonomously make decisions and use software tools to achieve specific goals.

**Analogy:** Building a platform for agents is like constructing a commercial kitchen — instead of every chef building their own oven and plumbing from scratch, the platform provides standardized tools, memory storage, and safety guardrails so developers can focus on creating smart agents efficiently.

## Core Concepts

### 1. Agents vs. Workflows

| Aspect | Agent | Workflow |
|--------|-------|----------|
| Autonomy | Dynamically directs its own processes | Rigid, developer-defined path |
| Decision-making | AI decides which tools to use | Developer fills in the blanks |
| Task handling | Unpredictable tasks via reasoning-acting-observing loop | Predictable, repetitive tasks |
| Example | Research agent searches web, reads article, decides to search again, compiles report | Data-extraction pipeline that processes every contract the same way |

**Core definition:** `Agent = LLM + Tool + Loop`

### 2. Tools and Actions

LLMs are isolated text generators that cannot access real-time information or affect the outside world. **Tools** give agents "hands" to interact with their environment.

- **Information-augmenting tools:** Web search, database queries, API calls
- **Action-executing tools:** Booking flights, updating databases, sending emails
- **Tool Calling:** The mechanism the AI uses to generate a structured request to activate tools

**Model Context Protocol (MCP):** A standardized interface (like "USB-C for AI") that allows developers to plug external tools (Google Drive, Slack, databases) into any agent without writing custom integration code for every model.

### 3. Memory and Knowledge (RAG)

- **Working memory (short-term):** Tracks the current ongoing conversation using rolling context windows
- **Long-term memory:** Stores facts and preferences from past interactions using vector databases
- **RAG (Retrieval-Augmented Generation):** Agent searches an external knowledge base and injects relevant facts into its context before generating a response

### 4. Multi-Agent Systems

Instead of building one "God Agent" to do everything, divide work among specialized agents:

- **Product Launch Crew:** Market Researcher → Content Creator → PR Specialist
- **Hierarchical Support:** Call Handling Agent triages, routes to Tech Support or Billing
- **Software Development:** Manager Agent → Coder Agent → Review Agent

### 5. Platform Governance

Enterprise deployment requires:
- **Guardrails:** Define what the agent is allowed to do
- **Human-in-the-loop:** Agent prepares decision but requires human approval
- **Observability:** Trace every agent action
- **Invisible integration:** Embed agents into existing workflows, not separate dashboards

## Key Takeaways

1. **Agents act, they don't just talk** — True agents use tools to fetch real-time data and take actions
2. **Specialization beats generalization** — Build multi-agent systems with specialized roles
3. **Structure over total freedom** — Graph-based workflows prevent agents from going off track
4. **Context is everything** — Without RAG, an agent is an amnesiac
5. **Trust drives adoption** — Agents must be governed, integrated seamlessly, and make humans look good

## Gap Rules (from research)

These rules detect structural blind spots in agent platform research:

- **Autonomy vs. Structure Gap:** If building autonomous agents without considering graph-based workflows → ask about structured pathways
- **Tool Integration Gap:** If using custom tool integrations without MCP → ask about standardized protocols
- **Memory Gap:** If discussing agent behavior without RAG → ask about context retrieval
- **Governance Gap:** If deploying agents without human-in-the-loop → ask about approval workflows

## Toolset

- read
- write
- web_search (for current agent framework updates)
- sessions_spawn (for multi-agent orchestration)

## Use

Use this skill when:
- Building AI agents that use tools and memory
- Designing multi-agent systems
- Evaluating agent platforms (LangGraph, CrewAI, AutoGen)
- Planning enterprise agent deployments
- Understanding the agent vs. workflow distinction

## Failure modes

- Confusing workflows (rigid) with agents (autonomous)
- Building single agents instead of multi-agent systems
- Ignoring governance and human-in-the-loop requirements
- Overlooking RAG for long-term memory

## Acceptance criteria

1. Can explain the difference between agents and workflows
2. Can describe how MCP standardizes tool integration
3. Can design a multi-agent system with specialized roles
4. Understands when to use graph-based workflows vs autonomous agents
5. Knows the key governance requirements for enterprise deployment