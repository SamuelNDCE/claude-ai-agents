<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **claude-ai-agents** (395 symbols, 431 relationships, 3 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/claude-ai-agents/context` | Codebase overview, check index freshness |
| `gitnexus://repo/claude-ai-agents/clusters` | All functional areas |
| `gitnexus://repo/claude-ai-agents/processes` | All execution flows |
| `gitnexus://repo/claude-ai-agents/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

# CodeGraph — Semantic Code Intelligence

CodeGraph v0.9.9 is indexed for this project (23 nodes, 27 edges) and for NeuralVault (62 nodes, 119 edges).
MCP server: `codegraph-nv-bridge.js` (proxies codegraph + saves results to NeuralVault).

## Token-Saving Protocol (read this)

**Before calling any codegraph tool, call `codegraph_kg_nv` first:**
```
codegraph_kg_nv({ query: "your question or symbol name" })
```
If NeuralVault has a cached result, use it. Only call the live codegraph tool if the cache misses.

After a full codebase exploration, run the snapshot script to persist the architecture to NV:
```bash
node codegraph-kg-snapshot.js [project-path]
```

## Tools

| Tool | Purpose |
|------|---------|
| `codegraph_kg_nv` | Check NV cache FIRST before any other codegraph call |
| `codegraph_explore` | Answer architecture questions, data flows, code surveys |
| `codegraph_search` | Find symbols by name |
| `codegraph_callers` | Who calls a function |
| `codegraph_callees` | What a function calls |
| `codegraph_impact` | Blast radius for changing a symbol |
| `codegraph_node` | Full details for one symbol |
| `codegraph_files` | Indexed file structure (faster than FS scan) |
| `codegraph_status` | Index health |

## Maintenance

- Re-index after significant code changes: `codegraph index`
- Re-snapshot to NV: `node codegraph-kg-snapshot.js`
- Bridge source: `codegraph-nv-bridge.js`

# NeuralVault MCP Integration

`nv-mcp-server.js` runs as a Claude MCP server named `neuralvault`. It exposes NeuralVault's REST API (localhost:8900) as 5 tools directly callable in Claude sessions.

## NV Tools

| Tool | When to use |
|------|-------------|
| `nv_observe(title, content)` | Quick save — a fact, decision, or lesson learned |
| `nv_search(q)` | Find notes by keyword before deep work |
| `nv_ask(q)` | Natural-language question against the vault |
| `nv_note(id)` | Read full content of a specific note |
| `nv_create_note(title, content, type, tags)` | Structured note with frontmatter |

## Memory Bridge

Any call to `mcp__claude-flow__memory_store` automatically triggers a `PostToolUse` hook that also writes the key/value to NV `/api/observe`. Ruflo agent memory and NeuralVault stay in sync without manual intervention.

## Session Pattern

```
Session start:   curl -s http://localhost:8900/api/context  ← existing NV check
Mid-session:     nv_search(topic)                           ← find existing knowledge
Learning saved:  mcp__claude-flow__memory_store → auto-synced to NV
Specific recall: nv_ask("what did we learn about X?")
```

## Failure Modes

- NV offline: all nv_* tools return gracefully; the memory hook exits silently (no Claude Code error)
- Ruflo MCP offline: nv_* tools still work independently from NeuralVault directly
