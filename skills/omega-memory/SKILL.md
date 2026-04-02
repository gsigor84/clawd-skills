---
name: omega-memory
description: "# omega-memory — Persistent memory for OpenClaw using Omega Memory. Store, retrieve, and manage memories that persist across sessions. Omega runs locally with no cloud dependency."
---

# omega-memory

Use Omega Memory to give OpenClaw persistent memory across sessions. Omega is installed locally and stores memories on your machine.

## Trigger
`/omega-memory <command> <query or memory text>`
`/remember <thing to remember>`
`/recall <query>`

## Tool
Omega CLI installed at system level — accessed via exec.

## Use

### Store a memory
```
/remember Igor's preferred model is MiniMax-M2.7 for most tasks
```
```
omega store <text>
```

### Recall a memory
```
/recall what model does Igor prefer
```
```
omega query <text>
```

### Show memory timeline
```
omega timeline
```

### Show memory stats
```
omega status
```

### Get session briefing (recent memories)
```
omega welcome
```

### Store typed memories
```
omega store <text> --type decision|lesson|error|summary|preference
```

### Record feedback on a memory (helps omega learn)
```
omega feedback <memory-id> <positive|negative>
```

### Consolidate memory (remove stale, prune duplicates)
```
omega consolidate
```

### List all stored preferences
```
omega list_preferences
```

## Examples

**Store a decision:**
```
omega store "The marketing pipeline always runs: strategy → concept → video prompt. Never skip the strategy stage."
```

**Query by meaning:**
```
omega query "what decisions were made about the marketing workflow"
```

**Store a lesson learned:**
```
omega store "skill-forge runs need the canonical state tool, not session state. Always use skill_forge_state.py for status." --type lesson
```

**Store an error pattern:**
```
omega store "NotebookLM fetcher fails with 'copy button not found' — this is recoverable. Retry with re-snapshot." --type error
```

**Surface memories at session start:**
When OpenClaw starts, it should recall relevant memories before beginning work:
```
omega query <current task context>
omega welcome
```

## Architecture
- Omega runs as MCP server + CLI on your machine
- Storage: `~/.omega/omega.db` (SQLite)
- Embedding model: `bge-small-en-v1.5` (~127MB, downloaded)
- No cloud, no API keys, no vendor lock-in
- Memories persist across Claude Code and OpenClaw sessions

## Limitations
- Omega MCP server is registered with Claude Code — OpenClaw accesses via CLI exec
- Requires `omega` command in PATH (installed system-wide)
- First run downloads embedding model if not present
