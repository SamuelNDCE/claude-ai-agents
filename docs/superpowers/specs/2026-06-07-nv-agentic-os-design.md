# NeuralVault — Agentic OS Design

**Date:** 2026-06-08 (updated from 2026-06-07)
**Status:** Approved
**Scope:** Product-level design for NeuralVault as a local-first agentic knowledge OS for businesses. Per-sub-project implementation plans are written separately.

## 1. Vision + Principles

NeuralVault is a local-first agentic knowledge OS built on top of Obsidian-compatible vaults. It gives companies a shared, living brain — a neural map of their knowledge — with AI agents that maintain, analyze, and act on it.

Core principles:

- **Search is free, generation is paid.** Reading, searching, and navigating the vault costs nothing. LLM generation (chat, agents, synthesis) is the paid surface.
- **The vault is the source of truth.** Markdown notes are canonical. Every derived artifact (vector index, graph, caches) is rebuildable from the vault.
- **Local-first.** Everything works on the company's LAN. No hosted dependency for core read/search.
- **Federated vaults.** Multiple vaults can be linked and queried together; each vault remains independently owned and portable.

## 2. Architecture

**Pure Rust native desktop app — no WebView.**

The app is a native binary built with `eframe` (the egui application framework). Every visual element — panels, chat UI, admin screens, the neural map — is rendered in a unified `wgpu` GPU context. There is no browser engine, no HTML, no JavaScript, and no surface composition problem. The egui UI panels and the neural map share one render pass. This is the architecture that makes smooth <10ms rendering at 1M+ notes achievable without workarounds.

The sync-server is a separate Rust binary that customers deploy on their own server.

**Deployment and LLMs.** NV ships as a desktop app for employee devices and as a server binary for company infrastructure. Generation routes between local models (Ollama, served from the customer's LLM servers) and cloud providers (e.g. Claude) per task. Cloud API keys are stored encrypted (§9). NV load-balances across the customer's local LLM servers with health-check-based failover to cloud if all local servers are unreachable (user-configurable).

**Five sub-projects, in dependency order:**

1. **Core data + vault layer** — vault discovery, `.nv/` sidecar, frontmatter, templates.
2. **Search** — LanceDB hybrid index, embeddings, RRF ranking.
3. **Neural map** — Rust + wgpu GPU rendering, cluster/LOD optimization, interaction.
4. **NV chat + agents** — persistent memory, briefings, File Keeper / AI Manager / custom agents.
5. **Sync / collab / security / licensing / integrations** — CRDT sync, roles, ACL, SSO, encryption, live data import, licensing, marketing site.

## 3. App Structure

```
NeuralVault/                     ← C:\Users\Futur\Documents\AiWorkspace\NeuralVault
├── Cargo.toml                   ← workspace root
├── apps/
│   ├── desktop/src/
│   │   ├── main.rs              ← eframe entry point
│   │   ├── app.rs               ← top-level App state
│   │   ├── ui/
│   │   │   ├── map_panel.rs     ← overlay controls on GPU surface
│   │   │   ├── chat_panel.rs
│   │   │   ├── admin_panel.rs
│   │   │   └── settings_panel.rs
│   │   └── map/                 ← wgpu custom render pass (neural map)
│   └── sync-server/src/
│       ├── relay.rs             ← Yjs WebSocket relay
│       ├── auth.rs              ← SSO validation, sessions
│       └── license.rs          ← phone-home seat validation
└── packages/
    ├── vault/                   ← vault I/O, .nv/ sidecar, frontmatter
    ├── search/                  ← LanceDB hybrid search, embeddings
    ├── sync/                    ← yrs (Yjs Rust) CRDT client
    ├── agents/                  ← agent runner, manifests, sandbox
    ├── memory/                  ← persistent chat memory
    ├── llm/                     ← router: local Ollama ↔ cloud providers
    ├── auth/                    ← SSO (SAML/OIDC) + phone-home licensing
    ├── permissions/             ← folder-level ACL enforcement
    ├── audit/                   ← audit log + 30-day snapshots
    └── import/                  ← live sync: Slack, email, CRM, CSV
```

## 4. Data Model

- **NV vaults are Obsidian-compatible.** No proprietary format. A NeuralVault vault opens cleanly in Obsidian and vice versa.
- **`.nv/` sidecar.** Per-vault hidden directory holding NV-specific derived state: LanceDB index, graph/cluster cache, chat memory, audit log, snapshots, encrypted OAuth tokens for integrations, and config. Everything in `.nv/` is rebuildable from the notes.
- **Note frontmatter.** Notes carry YAML frontmatter for type, tags, and NV metadata. Frontmatter drives typing and map coloring.
- **Default templates.** NV ships default note templates so new notes land with consistent frontmatter.

**Company vault default structure (configurable by admin):**

```
Company Vault/
├── financials/
├── issues/
├── complaints/
├── decisions/
└── shared-knowledge/
```

**Employee mini-vault structure:**

```
Employee Mini-Vault/
├── my-notes/        ← private, E2E encrypted, never readable by company
├── my-tasks/        ← private, E2E encrypted, never readable by company
└── work/            ← syncs to members/{username}/ in company vault
```

Employees can promote notes from `members/{username}/` into shared company folders by moving them. Role permissions govern which shared folders each employee can write to. The File Keeper agent can suggest promotions.

## 5. Search

- **LanceDB hybrid search.** Combines dense vector search with lexical/keyword search.
- **Embeddings: `nomic-embed` via Ollama.** Local embedding model, no cloud calls for indexing.
- **RRF (Reciprocal Rank Fusion)** merges vector and lexical result lists into one ranking.
- **Performance target: <10ms at 1M+ notes.**
- **First-run indexing UX.** On first open of a vault, NV indexes it with clear progress feedback; the app is usable while indexing completes.
- **Search scope.** An employee's search spans both the company vault (folders they have access to) and their own mini-vault simultaneously.

## 6. Neural Map

- **Rendered in Rust on the GPU (wgpu).** Force simulation and drawing run in a custom wgpu render pass, sharing the same GPU context as the egui UI. No JavaScript involvement.
- **Cluster-first + LOD is the scaling strategy.** The map opens on community clusters. Individual nodes materialize via level-of-detail as the user zooms in. Per-frame draw count stays bounded regardless of vault size.
- **Permission-aware.** The map only shows nodes in folders the current user can access.
- **Click behavior.** Click a node to open a detail panel (title, preview, metadata) with a button to jump to the underlying note.
- **Right-click behavior.** Context menu with primary action **Ask NV about this** (hands the node to chat), plus standard node actions.
- **Map highlighting on answers.** When chat or an agent answers, source nodes light up on the map.

## 7. NV Chat

- **Persistent memory (canonical).** Chat remembers past conversations across sessions, stored per-vault in `.nv/`.
- **LLM routing.** Chat and agents route between local models and cloud providers per task. Local model unavailable → falls back to cloud (user-configurable).
- **Proactive briefings.** On login/vault open, NV surfaces a short briefing (what changed, what's relevant).
- **Adaptive answer presentation.** NV answers in whatever form fits best: inline text, highlighting source nodes on the map, or creating a summary note in the vault.

## 8. Agents

NV agents can do effectively anything within the vault and its connected tools. Every agent (including the built-in Vault Keepers) declares a manifest at setup: allowed tools, allowed folder paths, token budget per run, and a schedule or trigger.

**Two always-on Vault Keepers:**

- **File Keeper** — manages vault files: organization, frontmatter hygiene, dead link repair, deduplication, cluster connections, and general vault health. Suggests note promotions from employee workspaces to shared company folders.
- **AI Manager** — oversees and supervises all other agents (custom and built-in). Monitors running agents, enforces their manifests, pauses or terminates agents that exceed their budget or try to access out-of-scope folders, and surfaces an agent health report to the admin panel.

**Custom agents** — users can set up additional agents that do almost anything, each scoped by their manifest. Examples: a daily digest agent, a CRM-to-vault sync agent, a research summarizer.

**Agent sandbox.** An agent that attempts to access a folder or tool outside its manifest is blocked and the violation is logged in the audit log. The AI Manager is notified.

## 9. Sync / Roles / Collaboration

- **Live real-time co-editing.** `yrs` (Yjs in Rust) CRDT: when two people edit the same content, each sees the other's changes live.
- **LAN-first, customer-hosted sync server.** Clients reach a sync server the customer hosts on their LAN. CRDT topology is server-relayed through that server. Vault stays reachable without internet.
- **Roles: admin / editor / viewer.** Roles operate at the folder level. An admin assigns each employee (or group) access to specific folders with a specific role. Example: support team gets editor on `complaints/` and `issues/`, viewer on `shared-knowledge/`, no access to `financials/`.
- **`members/{username}/` namespace.** Each employee's `work/` syncs to this path in the company vault. It's visible to admins and anyone with appropriate access, but only that employee can write to it.
- **SSO (SAML 2.0 / OIDC) in v1.** NV integrates with the company's identity provider (Azure AD, Google Workspace, Okta). Accounts provision and deprovision automatically. Employees sign in with their existing company credentials.
- **Audit log.** Every change is recorded — who changed what, when — stored in `.nv/`. Non-negotiable.

## 10. Employee Management

**Onboarding:**
Admin panel (in the desktop app or the company's NV server web UI). Admin adds an employee by entering their name/email and assigning a role. For SSO deployments, users are provisioned automatically from the directory. For non-SSO: NV generates a time-limited invite link. Employee clicks it, installs the NV app, signs in, and their mini-vault is auto-provisioned and linked to the company vault. Phone-home licensing enforces the seat cap; exceeding it prompts the admin to upgrade before the invite can be sent.

**Devices:** Mini-vault syncs across the employee's work devices through the company's NV sync server. Private folders (`my-notes/`, `my-tasks/`) are E2E encrypted before hitting the server — the server relays them but cannot read them. `work/` syncs normally.

**Multiple vaults:** An employee can connect their mini-vault to more than one company vault (e.g. a contractor with two clients). Each connection is managed independently.

**Offboarding:** Admin deactivates the account. Their `members/{username}/` content stays in the company vault as a read-only archive (searchable, linkable). Their private mini-vault is theirs — NV has no access and nothing is deleted from their device.

## 11. Security

- **Encryption at rest** on the vault.
- **E2E encrypted private folders.** `my-notes/` and `my-tasks/` are encrypted with a key only the employee holds. The company sync server relays them but cannot read them.
- **Key recovery:** Primary — the private folder key is wrapped with the employee's SSO identity, so only their authenticated SSO session can unwrap it. Backup — a 24-word recovery phrase generated at first setup, stored by the employee. NV never holds the plaintext key.
- **Encrypted API key management** for cloud LLM providers.
- **Encryption in transit** for all synced data.
- **Audit log** of all changes (see §9).
- **Phone-home licensing:** Requires outbound access to NV's licensing endpoint. Grace period: 7-day offline buffer before the app locks. Configurable proxy setting for restrictive corporate firewalls. IT whitelist endpoint is documented at setup.

## 12. Integrations

**Live sync (OAuth-connected, persistent):**

- **Slack:** OAuth app + Events API webhooks. Messages, files, and threads flow in as they happen.
- **Email:** IMAP IDLE (real-time push from mail server).
- **CRM (Salesforce, HubSpot):** Webhook subscriptions for record changes.
- **CSV:** File-watcher on a drop folder; re-imports on file change.

Each integration's OAuth token is stored encrypted in `.nv/`. The admin panel shows connection status and can pause/reconnect any source.

**Outbound:** A third-party REST API so external tools can query and write the vault.

## 13. Licensing / Website

- **Per-seat and per-company licensing.**
- **Customer-hosted, NV-licensed server.** The customer hosts the sync/LLM server on their own infrastructure; NV provisions/sets it up and licenses the software. NV also offers a turnkey hardware/server option for customers who want NV to supply the box.
- **Phone-home licensing — no emailed license key.** The app validates entitlement by phoning home. No license file, no key delivered by email.
- **Admin cost controls.** Admins can set a monthly cloud LLM spending cap per employee or per team. NV tracks usage and blocks generation calls once the cap is hit, with a warning before the limit is reached.
- **Free / trial tier.** A very limited free tier for individual (single-person) use.
- **Dynamic pricing configurator** on the website.
- **GitHub Pages blog** for the marketing/content site.

## 14. Out of Scope for v1

- Mobile apps
- Voice
- A full built-in markdown editor (editing happens in Obsidian or external editors)
- Non-English support
- Tauri / WebView-based rendering (superseded by egui + eframe)
- Annual / emailed license files (superseded by phone-home licensing)

## 15. Open Questions (deferred to per-sub-project plans)

- Community-detection cadence (when/how often clusters recompute)
- Importer field mapping schemas (per-source: Slack channel → vault folder, CRM record type → note type, etc.)
- Agent manifest schema (exact tool-permission vocabulary)
- SSO per-customer configuration UX (self-service metadata exchange flow)
- Version snapshot storage sizing / compression strategy
