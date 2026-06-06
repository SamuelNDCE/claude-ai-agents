# Ruflo + NeuralVault Integration Design

**Date:** 2026-06-06
**Status:** Approved

## Goal

Register Ruflo as a Claude Code MCP server and wire Ruflo's memory writes through NeuralVault so both systems share a single persistent brain. NeuralVault remains the canonical markdown knowledge store; Ruflo's agentdb is the fast vector index on top.

## Architecture

```
Claude Code (user)
    │
    ▼  MCP
Ruflo server  ─────────────────────────────────────────────────────────────
    │  (memory_store, swarm_init, agent_spawn, 60+ tools)                 │
    │                                                                      │
    ▼  plugin hook                                                    agentdb
ruflo-neuralvault plugin                                         (vector index,
    │  (nv_observe, nv_search, nv_ask, nv_note, nv_create_note)   fast recall)
    │
    ▼  HTTP REST
NeuralVault (localhost:8900)
    │
    ▼
Markdown vault  (wiki/agent-inbox/, wiki/lessons/, etc.)
```

## Components

### 1. Ruflo CLI install

- Run `npx ruflo@latest init` in `C:\Users\Futur\Documents\AiWorkspace\Claude`
- Lays down `.claude/`, hooks, agent definitions, MCP daemon
- Register as Claude MCP: `claude mcp add ruflo -- npx ruflo@latest mcp start`

### 2. `ruflo-neuralvault` plugin

Location: `.claude/plugins/ruflo-neuralvault/`

Files:
- `plugin.json` — Ruflo plugin manifest (name, version, tools, hooks)
- `index.js` — plugin entry point, registers tools and hook
- `hooks/post-memory-store.js` — fires after every `memory_store` call

Tools exposed to Claude via Ruflo MCP:

| Tool | Method | NV Endpoint |
|------|--------|-------------|
| `nv_observe(title, content)` | POST | `/api/observe` |
| `nv_search(q)` | GET | `/api/search?q=` |
| `nv_ask(q)` | GET | `/api/ask?q=` |
| `nv_note(id)` | GET | `/api/note?id=` |
| `nv_create_note(title, content, type, tags)` | POST | `/api/note` |

### 3. CLAUDE.md update

Add to the NeuralVault section:
- Ruflo MCP is registered; Claude has access to 98 agents and Ruflo memory tools
- Session start: check NV context AND Ruflo memory retrieve for recent session state
- On new learnings: call `memory_store` (Ruflo agentdb) — the hook auto-writes to NV

### 4. NeuralVault (unchanged)

`brain-server.py` is not modified. It is the stable HTTP target the plugin writes to.

## Data Flow

### Write path

```
Claude calls memory_store("key", "value")
    → Ruflo agentdb stores vector embedding
    → post-memory-store hook fires
    → nv_observe("key", "value") called
    → NeuralVault writes wiki/agent-inbox/<slug>.md
```

### Read path

```
Session start:   curl localhost:8900/api/context     (existing NV check)
During session:  memory_retrieve("topic")            (Ruflo fast vector search)
Specific lookup: nv_ask("question")                  (NV extractive answer)
```

## Error Handling

- If NeuralVault is offline: hook fails silently. Ruflo agentdb still gets the write. No crash, no retry.
- If Ruflo MCP is not running: Claude falls back to NV-only (current behavior). Nothing breaks.
- Plugin validates NV endpoint at startup, logs a warning if unreachable.

## Success Criteria

- `claude mcp list` shows `ruflo` as a registered server
- Claude can call `memory_store` and the note appears in NeuralVault's wiki/agent-inbox/
- Claude can call `nv_search` and get results from NeuralVault
- If NeuralVault is down, Ruflo tools still work without errors
- CLAUDE.md updated to reflect both systems
