# NeuralVault — Architecture (layered C4)

> Source-of-truth Mermaid diagrams for the interactive HTML beside this file.
> Generated 2026-06-14 from the code at `C:\Users\Futur\Documents\AiWorkspace\NeuralVault`
> (workspace v0.9.0-beta, GitNexus index 9b61a15). **This is an M1 skeleton:** contracts/types
> are frozen and the desktop search/embedding path is fully wired, but several crate bodies are
> deliberate stubs (`nv-sync`, `sync-server`, `AgentRunner::tick_all`, most importers, cloud LLM).
> Stubbed elements are marked `(stub)` and drawn with dashed borders.

Legend: **solid** = wired & running · **dashed** = planned / M1 stub · `→` = depends-on / calls.

---

## L1 — System Context

```mermaid
flowchart TB
    user([User])

    subgraph PT["Perpetual Technologies (org)"]
        direction TB
        desktop["NeuralVault Desktop<br/>(egui/eframe, wgpu)<br/>local-first knowledge app"]
        site["perpetual-site<br/>(sibling: company website,<br/>Next.js + TS) — 'Nice'"]
    end

    syncsrv["NeuralVault Sync Server<br/>(M1 stub relay)"]
    ollama["Ollama<br/>(local LLM: chat +<br/>nomic-embed-text embeddings)"]
    whisper["whisper.cpp STT<br/>(bundled, in-process, local)"]
    vault[("Markdown Vault on disk<br/>+ .nv sidecar:<br/>vectors.json · audit · memory · acl")]
    hooks["nv-claude-hooks<br/>(sibling: Claude Code ↔ NV bridge) — 'Hardup'"]

    user -->|uses| desktop
    user -->|browses| site
    desktop -->|read / write .md notes| vault
    desktop -->|HTTP: chat stream + embeddings| ollama
    desktop -->|push-to-talk audio → text| whisper
    desktop -. "planned CRDT sync (stub)" .-> syncsrv
    hooks -->|inject notes / save outputs| vault
    site -. "same org, no runtime link" .- desktop
```

---

## L2 — Containers (crate dependency graph)

Every edge below is taken directly from each crate's `Cargo.toml`. `nv-core` is the dependency-light
foundation; `nv-agents` is the apex (6 internal deps); the **desktop** binary pulls all 11 crates,
**sync-server** only 4.

```mermaid
flowchart TB
    subgraph apps["Applications"]
        desktop["neuralvault-desktop<br/>(all 11 crates + egui/eframe,<br/>whisper-rs, cpal/hound, screenshots)"]
        syncserver["neuralvault-sync-server<br/>(stub) — core, sync, auth, audit"]
    end

    subgraph ui_app["UI / App layer"]
        agents["nv-agents<br/>agent runtime"]
    end

    subgraph knowledge["Knowledge / AI"]
        memory["nv-memory<br/>conversations"]
        search["nv-search<br/>hybrid index"]
        llm["nv-llm<br/>LLM boundary"]
    end

    subgraph data["Data / IO"]
        vault["nv-vault<br/>on-disk vault"]
        importc["nv-import<br/>(stub) source importers"]
        syncc["nv-sync<br/>(stub) sync client"]
    end

    subgraph security["Security / Governance"]
        auth["nv-auth<br/>identity + licensing"]
        perms["nv-permissions<br/>folder ACLs"]
        audit["nv-audit<br/>append-only log"]
    end

    core["nv-core — shared types, errors, palette (zero internal deps)"]

    %% foundation
    vault --> core
    perms --> core
    llm --> core
    %% level 2
    search --> core
    search --> vault
    syncc --> core
    syncc --> vault
    audit --> core
    audit --> vault
    importc --> core
    importc --> vault
    auth --> core
    auth --> perms
    memory --> core
    memory --> vault
    memory --> llm
    %% apex crate
    agents --> core
    agents --> vault
    agents --> llm
    agents --> perms
    agents --> audit
    agents --> memory
    %% apps
    desktop --> agents
    desktop --> search
    desktop --> memory
    desktop --> llm
    desktop --> vault
    desktop --> auth
    desktop --> perms
    desktop --> audit
    desktop --> syncc
    desktop --> importc
    desktop --> core
    syncserver --> core
    syncserver --> syncc
    syncserver --> auth
    syncserver --> audit

    syncc:::stub
    importc:::stub
    syncserver:::stub
    classDef stub stroke-dasharray: 5 4,opacity:0.85;
```

---

## L3 — Components (key types per crate)

```mermaid
flowchart LR
    subgraph core["nv-core"]
        c1["NvError / Result"]
        c2["ids: AgentId, FolderId,<br/>NoteId, UserId"]
        c3["palette (approved colors)"]
    end
    subgraph vault["nv-vault"]
        v1["Vault: open · folders ·<br/>list_notes · read/write_note · sidecar"]
        v2["Note · FolderInfo"]
        v3["Frontmatter: parse · to_markdown"]
        v4["NvSidecar (.nv dir)"]
        v5["markdown::render_markdown_to_text"]
    end
    subgraph search["nv-search"]
        s1["SearchIndex (trait): rebuild · query"]
        s2["HybridIndex: query_hybrid ·<br/>query_semantic · RRF k=60"]
        s3["LexicalIndex (TF-IDF)"]
        s4["VectorIndex (cosine,<br/>.nv/vectors.json)"]
        s5["Query · SearchHit · SearchMode"]
    end
    subgraph llm["nv-llm"]
        l1["LlmRouter: pick_backend ·<br/>complete · complete_streaming · embed"]
        l2["OllamaClient: chat_blocking ·<br/>chat_streaming · embeddings"]
        l3["Backend · ChatMessage ·<br/>CompletionRequest · Role · StreamEvent"]
    end
    subgraph memory["nv-memory"]
        m1["MemoryStore"]
        m2["Conversation (JSON in sidecar)"]
    end
    subgraph agents["nv-agents"]
        a1["AgentRunner: with_builtins ·<br/>states · tick_all (no-op, stub)"]
        a2["Agent (trait) · AgentContext<br/>{vault, llm, perms, audit}"]
        a3["AgentManifest · AgentState ·<br/>AgentStatus · Trigger"]
        a4["builtins: FileKeeper · AiManager ·<br/>AGENT_TEMPLATES"]
        a5["tools: ToolCall · ToolSpec ·<br/>parse_tool_calls · TOOLS · sandbox"]
    end
    subgraph sync["nv-sync (stub)"]
        sy1["SyncClient (no-op shell;<br/>CRDT/yrs later)"]
    end
    subgraph security["Security"]
        au1["nv-auth: LicenseClient ·<br/>AuthSession · IdentityProvider · StubProvider"]
        pe1["nv-permissions: PermissionSet ·<br/>FolderAcl · Access · Role"]
        ad1["nv-audit: AuditLog (append-only) · AuditEntry"]
    end
    subgraph importc["nv-import (stub)"]
        i1["Importer (trait)"]
        i2["Source: Slack · IMAP · CRM · CSV"]
    end
    subgraph desktopui["neuralvault-desktop (UI modules)"]
        d1["app.rs — orchestrator / eframe update loop"]
        d2["graph.rs — force-directed note physics"]
        d3["map/* — note_map · nodes · particles · agents_layer"]
        d4["ui/* — sidebar · topbar · tabs<br/>(chat · board · dashboard · map · agents · admin)"]
        d5["voice.rs — cpal/hound mic → whisper STT"]
        d6["search_overlay · capture_overlay · backup · theme"]
    end
```

---

## L4 — Key runtime flows

### (a) Search / RAG — `vault_context_for` (app.rs:2026)

```mermaid
sequenceDiagram
    participant U as User
    participant App as Desktop (app.rs)
    participant O as Ollama
    participant H as HybridIndex
    U->>App: type query / chat message
    App->>O: embed("nomic-embed-text", query) [600 ms timeout]
    alt embedding returns in time
        O-->>App: query vector
        App->>H: query_hybrid(q, vec)
        H->>H: RRF fuse (k=60) LexicalIndex(TF-IDF) + VectorIndex(cosine)
        H-->>App: ranked SearchHits  ("hybrid lexical+semantic")
    else timeout / error
        App->>H: lexical-only query
        H-->>App: ranked SearchHits  ("lexical fallback")
    end
    App-->>U: hits injected as chat context
```

### (b) Embed-at-launch — `scheduler_tick` (app.rs:2474) + `pump_embeddings` (app.rs:2724)

```mermaid
sequenceDiagram
    participant App as Desktop
    participant RT as tokio runtime
    participant O as Ollama
    participant V as VectorIndex / .nv/vectors.json
    Note over App: first scheduler_tick after launch (embed_rx == None)
    App->>App: collect notes not yet embedded (total vs already)
    App->>RT: spawn async embed job per note (channel tx/rx)
    loop each note
        RT->>O: embed("nomic-embed-text", body)
        O-->>RT: vector (or empty on failure)
        RT-->>App: send (note_id, vector)
    end
    Note over App: each frame, pump_embeddings drains a few
    App->>V: vector_mut().insert(note_id, vec)
    App->>V: save_to_sidecar every 25 new vectors
```

### (c) Re-index on change — 10 s poll (app.rs:3053)

```mermaid
sequenceDiagram
    participant App as Desktop (update loop)
    participant FS as Vault on disk
    loop every 10 s
        App->>FS: read folders + note counts
        App->>App: compute folder_signature
        alt signature changed (notes added/removed)
            App->>App: index.rebuild(vault) = lexical rebuild + load vectors from sidecar
            Note over App: rebuild also re-seeds the map physics layout
        else unchanged
            App->>App: no-op (live physics map left undisturbed)
        end
    end
```

### (d) Multi-device sync — planned (M1 stub)

```mermaid
sequenceDiagram
    participant D as Desktop (nv-sync SyncClient)
    participant S as sync-server (relay)
    Note over D,S: M1 — both are no-op stubs
    D-.->S: CRDT delta push (yrs) — not yet implemented
    S-.->D: merged updates — not yet implemented
```
