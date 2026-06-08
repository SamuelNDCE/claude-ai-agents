# NeuralVault — Agentic OS Design

**Date:** 2026-06-07
**Status:** Approved
**Scope:** Product-level design for NeuralVault as a local-first agentic knowledge OS. Per-sub-project implementation plans are written separately.

## 1. Vision + Principles

NeuralVault is a local-first agentic knowledge OS built on top of Obsidian-compatible vaults.

Core principles:

- **Search is free, generation is paid.** Reading, searching, and navigating the vault costs nothing. LLM generation (chat, agents, synthesis) is the paid surface.
- **The vault is the source of truth.** Markdown notes are canonical. Every derived artifact (vector index, graph, caches) is rebuildable from the vault.
- **Local-first.** Everything works offline on the user's machine. No hosted dependency for core read/search.
- **Federated vaults.** Multiple vaults can be linked and queried together; each vault remains independently owned and portable.

## 2. Architecture

**Approach A — Tauri app + Rust server.** A Tauri desktop shell with a Rust backend process that owns indexing, search, and orchestration. The frontend is a thin client over the Rust server's local API.

Five sub-projects, in dependency order:

1. **Core data + vault layer** — vault discovery, `.nv/` sidecar, frontmatter, templates.
2. **Search** — LanceDB hybrid index, embeddings, RRF ranking.
3. **Neural map** — clustering, graph rendering, interaction.
4. **NV chat + agents** — persistent memory, briefings, Vault Keeper / Analyzer / custom agents.
5. **Sync / collab / licensing / website** — CRDT sync, roles, integrations, licensing, marketing site.

Each sub-project builds on the ones before it. Later sub-projects defer their open questions to their own plans.

## 3. Data Model

- **NV vaults ARE Obsidian vaults.** No proprietary format. A NeuralVault vault opens cleanly in Obsidian and vice versa.
- **`.nv/` sidecar.** Per-vault hidden directory holding NV-specific derived state: the LanceDB index, graph/cluster cache, chat memory, audit log, and config. Everything in `.nv/` is rebuildable from the notes.
- **Note frontmatter.** Notes carry YAML frontmatter for type, tags, and NV metadata. Frontmatter drives typing and map coloring.
- **Default templates.** NV ships default note templates so new notes land with consistent frontmatter.

## 4. Search

- **LanceDB hybrid search.** Combines dense vector search with lexical/keyword search.
- **Embeddings: `nomic-embed` via Ollama.** Local embedding model, no cloud calls for indexing.
- **RRF (Reciprocal Rank Fusion)** merges vector and lexical result lists into one ranking.
- **Performance target: <10ms at 1M+ notes.**
- **First-run indexing UX.** On first open of a vault, NV indexes it with clear progress feedback; the app is usable (search degrades gracefully) while indexing completes.

## 5. Neural Map

- **Cluster-first.** The map opens on clusters/communities rather than dumping every node, so large vaults stay legible.
- **Click / right-click behavior.** Click focuses/expands a node or cluster; right-click opens a context menu of actions on that node.
- **Map highlighting on answers.** When chat or an agent answers, the nodes that sourced the answer light up on the map, tying generation back to the vault.

## 6. NV Chat

- **Persistent memory.** Chat remembers across sessions, stored per-vault in `.nv/`.
- **Proactive login briefings.** On login/open, NV can surface a short briefing (what changed, what's relevant) rather than waiting for a prompt.

## 7. Sync / Roles / Collaboration

- **Yjs CRDT** for conflict-free real-time sync across collaborators.
- **Roles: admin / editor / viewer.**
- **Audit log** of changes (stored in `.nv/`).
- **Encryption** for synced data.

## 8. Agents

- **Vault Keeper** — maintains vault health (organization, frontmatter hygiene, dead links, dedup).
- **Vault Analyzer** — surfaces insights, patterns, and summaries across the vault.
- **Custom agents** — user-defined agents scoped to a vault.

## 9. Integrations

- **Inbound import:** Slack, email, CSV, CRM.
- **Outbound:** a third-party REST API so external tools can query/write the vault.

## 10. Licensing / Website

- **Per-seat licensing.**
- **Phone-home only** — the app validates licensing by phoning home; no per-user license file shipped (annual license file is explicitly out of scope for v1).
- **Dynamic pricing configurator** on the website.
- **GitHub Pages blog** for the marketing/content site.

## 11. Out of Scope for v1

- Mobile apps
- Voice
- A full built-in markdown editor (editing happens in Obsidian or external editors)
- Non-English support
- Annual license file (superseded by phone-home licensing)

## 12. Open Questions (deferred to per-sub-project plans)

- CRDT topology (peer-to-peer vs server-relayed)
- Community-detection cadence (when/how often clusters recompute)
- Multi-server LLM routing
- Mini-vault merge semantics
- Importer schemas (per-source field mapping)
