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

**Approach A — Tauri app + Rust server.** A Tauri desktop shell with a Rust backend process that owns indexing, search, and orchestration. The frontend is a thin client over the Rust server's local API. **This Rust backend replaces the current Python `brain-server.py`**; Python is retired once the Rust server reaches parity. The local API continues to serve on port `8900` so existing clients keep working through the migration.

**Rendering is Rust + GPU.** The neural map's force simulation and rendering run in Rust on the GPU via `wgpu` (WebGPU), drawing to a surface in the Tauri window. The HTML/CSS webview is used only for UI chrome (panels, search box, stats, chat) overlaid on the GPU surface. The heavy per-frame work (physics, node/edge draw) never touches JavaScript. This is what makes the <10ms-at-1M ambition reachable on the visual side.

**Deployment & LLMs.** NV ships as a desktop app for end-user devices and can also be installed on a server. Generation routes between **local models** (Ollama, served from one or more of the customer's LLM servers) **and cloud providers** (e.g. Claude) per task; cloud keys are stored encrypted (§9). NV routes each request to the appropriate model. (This resolves the prior "multi-server LLM routing" open question at the product level; the routing mechanism is detailed in the chat/agents plan.)

Five sub-projects, in dependency order:

1. **Core data + vault layer** — vault discovery, `.nv/` sidecar, frontmatter, templates.
2. **Search** — LanceDB hybrid index, embeddings, RRF ranking.
3. **Neural map** — Rust + wgpu GPU rendering, cluster/LOD optimization, interaction.
4. **NV chat + agents** — persistent memory, briefings, Vault Keeper / Analyzer / custom agents.
5. **Sync / collab / security / licensing / website** — CRDT sync, roles, encryption, integrations, licensing, marketing site.

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

- **Rendered in Rust on the GPU (wgpu).** Force simulation and drawing run in Rust against a `wgpu` surface, not in JS canvas. Positions never round-trip through JavaScript per frame.
- **Cluster-first + LOD is the scaling strategy.** The map opens on community clusters rather than every node — this is both for legibility AND as the core rendering optimization. At full-vault scale only a few hundred cluster nodes are drawn; individual nodes materialize via level-of-detail as the user zooms into or clicks a cluster. This keeps the per-frame draw count bounded regardless of vault size (target: smooth at 1M+ notes).
- **Click behavior.** Click a node to focus/expand it and open a detail panel (title, preview, metadata); from there you can jump straight to the underlying note.
- **Right-click behavior.** Right-click opens a context menu whose primary action is **Ask NV about this** (hands the node to chat), alongside other node actions.
- **Map highlighting on answers.** When chat or an agent answers, the nodes that sourced the answer light up on the map, tying generation back to the vault.

## 6. NV Chat

- **Persistent memory (canonical).** Chat remembers past conversations across sessions, stored per-vault in `.nv/`. This is the single source of memory and **absorbs the prior Ruflo + NeuralVault memory bridge** (see `2026-06-06-ruflo-neuralvault-design.md`), which is retired into this system.
- **LLM routing.** Chat and agents route between local models and cloud providers per task (see §2 Deployment & LLMs); cloud API keys are encrypted (§9).
- **Proactive login briefings.** On login/open, NV can surface a short briefing (what changed, what's relevant) rather than waiting for a prompt.
- **Adaptive answer presentation.** NV answers in whatever form fits best — inline text, highlighting the source nodes on the map, and/or creating a summary note in the vault.

## 7. Sync / Roles / Collaboration

- **Live real-time co-editing.** Yjs CRDT: when two people edit the same content, each sees the other's changes live as they type.
- **LAN-first, customer-hosted sync server.** Deployments typically run on the company LAN; clients reach a sync server the customer hosts (provisioned by NV). Because it lives on the LAN, the vault stays reachable even without internet access. CRDT topology is therefore **server-relayed** through that hosted server. (Resolves the prior "CRDT topology" open question.)
- **Roles: admin / editor / viewer.** Roles govern who can see and edit what in the company vault.
- **Audit log.** Every change is recorded — who changed what, and when (stored in `.nv/`). Non-negotiable.

## 8. Agents

NV agents can do effectively anything within the vault and its connected tools.

- **Vault Keeper** — one of one-or-two always-on management agents; maintains vault health (organization, frontmatter hygiene, dead links, dedup, general cleaning).
- **Vault Analyzer** — surfaces insights, patterns, and summaries across the vault.
- **Custom agents** — users can set up multiple additional agents that do almost anything, each scoped to a vault.

## 9. Security

- **Encryption at rest** on the vault.
- **Encrypted API key management** for cloud LLM providers — keys are stored encrypted.
- **Encryption in transit** for synced data.
- **Audit log** of all changes (see §7).

## 10. Integrations

- **Inbound import:** Slack, email, CSV, CRM.
- **Outbound:** a third-party REST API so external tools can query/write the vault.

## 11. Licensing / Website

- **Per-seat and per-company licensing.** Priced per seat within a company plan.
- **Customer-hosted, NV-licensed server.** The customer hosts the sync/LLM server on their own infrastructure; NV provisions/sets it up and licenses the software running on it.
- **NV-built servers (turnkey option).** In addition to customer self-hosting, NV also builds and supplies servers — a turnkey hardware/server offering for customers who want NV to provide the box, not just the license.
- **Phone-home licensing — no emailed license key.** The app validates entitlement by phoning home; there is no license file and no key delivered by email. (Offline grace behavior to be defined in the licensing plan.)
- **Free / trial tier.** A very limited free tier for individual (single-person) use.
- **Dynamic pricing configurator** on the website.
- **GitHub Pages blog** for the marketing/content site.

## 12. Out of Scope for v1

- Mobile apps
- Voice
- A full built-in markdown editor (editing happens in Obsidian or external editors)
- Non-English support
- Annual / emailed license file (superseded by phone-home licensing)

## 13. Open Questions (deferred to per-sub-project plans)

- Community-detection cadence (when/how often clusters recompute)
- Mini-vault merge semantics
- Adding / removing employees and connecting mini-vaults (approach TBD — owner deferred to design)
- Importer schemas (per-source field mapping for Slack / email / CSV / CRM)

**Resolved since v1 of this spec:** CRDT topology (server-relayed via customer-hosted server, §7) and multi-server LLM routing (route across customer's LLM servers, §2).
