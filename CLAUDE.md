<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **claude-ai-agents** (395 symbols, 431 relationships, 3 execution flows). Use GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` first.

## Rules
- **MUST** run `gitnexus_impact({target: "symbolName", direction: "upstream"})` before editing any symbol — report blast radius, warn if HIGH or CRITICAL.
- **MUST** run `gitnexus_detect_changes()` before committing.
- **NEVER** rename with find-and-replace — use `gitnexus_rename`.
- Exploring: use `gitnexus_query({query: "concept"})` over grepping.
- Full symbol context (callers, callees, flows): `gitnexus_context({name: "symbolName"})`.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/claude-ai-agents/context` | Codebase overview, index freshness |
| `gitnexus://repo/claude-ai-agents/clusters` | All functional areas |
| `gitnexus://repo/claude-ai-agents/processes` | All execution flows |
| `gitnexus://repo/claude-ai-agents/process/{name}` | Step-by-step trace |

## CLI Skills

| Task | Skill |
|------|-------|
| Architecture / "How does X work?" | `gitnexus-exploring` |
| Blast radius / "What breaks?" | `gitnexus-impact-analysis` |
| Trace bugs | `gitnexus-debugging` |
| Rename / refactor | `gitnexus-refactoring` |
| Tools reference | `gitnexus-guide` |
| Index / status / CLI | `gitnexus-cli` |

<!-- gitnexus:end -->

# CodeGraph — Semantic Code Intelligence

CodeGraph v0.9.9 indexed: this project (23 nodes, 27 edges), NeuralVault (62 nodes, 119 edges).
MCP server: `codegraph-nv-bridge.js` (proxies codegraph + saves to NeuralVault).

**Always call `codegraph_kg_nv` first** — use cached result if found, only hit live tool on cache miss.
After full codebase exploration: `node codegraph-kg-snapshot.js [project-path]`

## Tools

| Tool | Purpose |
|------|---------|
| `codegraph_kg_nv` | NV cache check — call FIRST |
| `codegraph_explore` | Architecture, data flows, surveys |
| `codegraph_search` | Find symbol by name |
| `codegraph_callers` | What calls this |
| `codegraph_callees` | What this calls |
| `codegraph_impact` | Blast radius |
| `codegraph_node` | Full symbol details |
| `codegraph_files` | Indexed file structure |
| `codegraph_status` | Index health |

Re-index after significant changes: `codegraph index` then `node codegraph-kg-snapshot.js`

# NeuralVault — Rust desktop app

App: `neuralvault-desktop.exe` (`NeuralVault-Desktop.bat`). No HTTP API, no localhost:8900. Old `nv_*` MCP tools deleted.

**In-app hybrid search** (`app.rs`): `vault_context_for` uses `HybridIndex` (TF-IDF + cosine, RRF k=60). Embedder runs once at launch via `scheduler_tick` step 0 — new notes not re-embedded until next launch.

`nv-client.js` kept — imported by `nv-web-mcp.js`.
