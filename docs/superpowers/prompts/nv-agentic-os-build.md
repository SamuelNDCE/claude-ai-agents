# NeuralVault — Full Agentic OS Build (Autonomous, Screenshot-Looped)

You are building NeuralVault as a local-first agentic knowledge OS, end to end.
You run autonomously, possibly for hours, with full permission over the repo.
Use parallel sub-agents wherever work is independent; run sequentially only
where there's a real dependency. Keep looping until the app builds, runs, and
the UI actually looks and works right — verified by screenshots, not assumptions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE SPEC — READ FIRST, IT IS THE SOURCE OF TRUTH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Read before writing any code:
  C:\Users\Futur\Documents\AiWorkspace\Claude\docs\superpowers\specs\2026-06-07-nv-agentic-os-design.md

If anything in this prompt conflicts with the spec, the spec wins. The spec
defines vision/principles, Approach A architecture, the 5 sub-projects, the
data model, search, neural map, chat, sync/roles, security, agents,
integrations, licensing, v1 out-of-scope, and deferred open questions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REPO STATE — READ THIS, IT IS NOT A CLEAN SLATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Repo: C:\Users\Futur\Documents\AiWorkspace\NeuralVault (separate from the Claude repo)

There are TWO app directories — do not confuse them:
  - desktop\neuralvault\         ← CANONICAL build target. Build here.
                                    (currently untracked on main; old frontend
                                     was cleaned out; SP1 Rust vault layer started)
  - .worktrees\feat-nv-core\nv-app\  ← PROTOTYPE (branch feat/nv-core, v0.1.0,
                                    32 commits). It WORKS but uses WebGL2 + React +
                                    Barnes-Hut, NOT the specced stack.

PROTOTYPE IS REFERENCE ONLY. The decision is: keep the spec, REBUILD fresh in
the Rust + wgpu / cluster-LOD / vanilla-chrome stack. Learn from the prototype's
code (its Rust vault layer is excellent and spec-aligned), but do NOT adopt its
WebGL2/React/Barnes-Hut rendering. Read prototype files for reference; build clean
in desktop\neuralvault.

GIT HYGIENE:
  - Work on a feature branch (one already exists: feat/nv-rebuild-sp1; create new
    ones per sub-project as needed). Never commit straight to main.
  - desktop\neuralvault\src-tauri\.gitignore already ignores /target/. Keep build
    artifacts out of commits.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESOLVED ARCHITECTURE PARAMETERS (all decided — do not re-litigate)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- BACKEND: Rust REPLACES the Python brain-server.py. Port its responsibilities
  into the Rust backend; retire Python at parity. Keep the local API on :8900
  available during migration so nothing breaks mid-way.
- RENDERING: the neural map's force sim AND drawing run in RUST on the GPU via
  `wgpu` (WebGPU), to a surface in the Tauri window. Per-frame physics/draw never
  touch JavaScript. HTML/CSS webview is CHROME ONLY (panels, search, stats,
  detail, chat), overlaid on the GPU surface, talking to Rust via Tauri invoke.
  Vanilla HTML/CSS + minimal JS for chrome. No UI frameworks (no React).
- SCALING: CLUSTER-FIRST + LOD. Draw community clusters as single nodes by
  default (a few hundred draws even at 1M notes); materialize individual nodes
  via level-of-detail as the user zooms into / clicks a cluster. Per-frame draw
  count stays bounded regardless of vault size.
- LLMs: route between LOCAL models (Ollama, possibly several of the customer's
  servers) AND CLOUD providers (e.g. Claude) per task. Cloud API keys stored
  ENCRYPTED.
- MEMORY: NV chat persistent memory (in `.nv/`) is canonical and ABSORBS the
  prior Ruflo + NeuralVault memory bridge (the 2026-06-06 spec is retired into it).
- SYNC: Yjs CRDT, live real-time co-editing. LAN-first; clients reach a sync
  server the CUSTOMER hosts (provisioned by NV). Topology is server-relayed.
- SECURITY: encryption at rest on the vault; encrypted cloud-LLM API key storage;
  encryption in transit for sync; mandatory audit log (who changed what, when).
- ROLES: admin / editor / viewer.
- LICENSING: per-seat + per-company. Customer hosts the server; NV provisions +
  licenses it. NV ALSO builds/supplies servers (turnkey hardware option).
  Phone-home licensing only — NO license file, NO emailed key. Very limited free
  tier for individuals.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATA MODEL + NODE-TYPE MAPPING (vault is source of truth)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- NV vaults ARE Obsidian vaults. `.nv/` sidecar holds derived state (index,
  graph/cluster cache, chat memory, audit log, config) — all rebuildable.
- Notes have YAML frontmatter (type, tags, title, created/date). Edges come from
  `[[wikilinks]]`. Note id = slug of the relative path (lowercase, separators ->
  "-", non-alphanumerics dropped).
- Frontmatter `type` maps to a visual NODE KIND. Reproduce brain-server.py's
  TYPE_MAP EXACTLY (8 kinds — richer than the spec's 6; follow the live mapping):
      moc, meta                          -> hub      (#b98cff)
      person                             -> person   (#ffd23d)
      org                                -> org
      system                             -> system
      catalog, inbox, note, task         -> entity   (#ff9e3d)
      concept, lesson, pattern, question -> concept  (#46b1ff)
      source, observation                -> source   (#56d364)
      (anything else)                    -> ext      (#5b6678)
  Pick colors for org/system in the renderer; the spec lists only 6 colors, so
  flag that gap and choose sensible distinct hues.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOCATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
App root:     C:\Users\Futur\Documents\AiWorkspace\NeuralVault\desktop\neuralvault
Rust backend: <app root>\src-tauri\src\        (lib.rs, main.rs, vault/, etc.)
Chrome:       <app root>\src\                   (index.html, app.js, styles.css)
Reference:    C:\Users\Futur\Documents\AiWorkspace\NeuralVault\.worktrees\feat-nv-core\nv-app  (prototype — read only)
Live vault:   C:\Users\Futur\Documents\Obsidian Vault\Claude   (real notes — test data)
Old Python:   C:\Users\Futur\Documents\Obsidian Vault\Claude\brain-server.py  (being replaced)
Dev command:  cd <app root> && npx tauri dev

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERMISSIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You MAY:  write all of <app root>\src and \src-tauri; add Rust crates and Tauri
          commands the spec needs (wgpu, LanceDB, Ollama/HTTP client, Yjs bridge,
          aes-gcm, etc.).
You MUST NOT change:
  - vault path: C:\Users\Futur\Documents\Obsidian Vault\Claude
  - port 8900
  - the vault's .md note files (the actual notes)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BUILD ORDER — 5 SUB-PROJECTS (per the spec, in dependency order)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Build in order. Do NOT start a sub-project until the previous one's done-condition
passes. Within a sub-project, fan out parallel agents on independent files.

  SP1  Core data + vault layer (RUST)  — vault discovery, .nv/ sidecar,
       frontmatter parsing, node-type mapping, wikilink graph, default templates,
       Tauri commands (open_vault, get_note_content, vault_status).
       STATUS: started on feat/nv-rebuild-sp1 (error.rs, config.rs,
       vault/{model,typemap,scanner}.rs done; graph.rs, sidecar.rs, commands.rs,
       lib.rs + tests remaining). Continue from there.
  SP2  Search                          — LanceDB hybrid index, nomic-embed via
       Ollama, RRF ranking, first-run indexing UX.
  SP3  Neural map + frontend           — Rust + wgpu GPU renderer with cluster/LOD
       force sim; HTML/CSS chrome overlay: click (detail + open note),
       right-click ("Ask NV about this"), pan/zoom, live search, stats.
  SP4  NV chat + agents                — persistent memory (absorbs Ruflo),
       local+cloud LLM routing, login briefings, Vault Keeper / Analyzer / custom
       agents, map highlighting on answers, adaptive answers (text/highlight/note).
  SP5  Sync / collab / security /       — Yjs CRDT live co-edit (LAN, server-
       licensing / website               relayed), roles, audit log, encryption
                                          at rest + in transit, encrypted API keys,
                                          importers (Slack/email/CSV/CRM), REST API,
                                          per-seat+per-company licensing (phone-home,
                                          customer-hosted + NV-built servers),
                                          pricing configurator, GitHub Pages blog.

For each sub-project, consult the spec's matching section AND its deferred open
questions (§13); resolve open questions minimally for v1 and record the choice.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE LOOP — repeat per sub-project until its done-condition passes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

── PHASE 1: PLAN (1 architect agent) ──────────────
Spawn an architect agent. Input: the spec section for this sub-project + current
state (screenshot description, console/build errors, failing items) + the
prototype's matching code as reference. Output JSON:
  { round, diagnosis, tasks:[{id, file, what, how, independent, depends_on}] }.
One task per file per round (parallel coders must not collide). Round 1 of a
sub-project: spec the full initial build. Later rounds: spec only what's broken.
Spec only — no code.

── PHASE 2: PARALLEL CODERS (N agents concurrently) ─
One agent per independent task, run concurrently; dependent tasks after their
deps. Each coder implements exactly one task, writes the file, returns a 3-bullet
summary.
  - RENDERER work (the map) is RUST + wgpu: force sim, cluster/LOD, GPU draw,
    input, exposed to the webview via Tauri commands/events. Organize into Rust
    modules (render/, sim/, cluster/).
  - CHROME work is minimal vanilla JS in src/: panels, search, stats, detail,
    chat. Calls Rust via Tauri invoke. No force sim or canvas physics here.
  - BACKEND work is Rust modules under src-tauri/src/ (vault/, search/, chat/,
    sync/, etc.). Match the proven patterns in the prototype where sensible.
  - Reuse the prototype's vault-layer approach (gray_matter frontmatter, walkdir
    scan, regex wikilinks, slug ids) — it's the reference design for SP1.

── PHASE 3: REVIEW (1 agent; fixes fan out) ────────
Read the changed files. Verify wiring & correctness:
  - index.html loads chrome JS as <script type="module">; chrome selectors map to
    real elements; styled selectors exist
  - Rust renderer: cargo check compiles; wgpu render loop runs each frame; node
    positions seeded before first draw; pan/zoom transform the camera/view matrix,
    not node data
  - cluster/LOD: default view draws clusters not all nodes; expanding a cluster
    materializes members; per-frame draw count bounded
  - Tauri bridge: every JS invoke() targets a real #[tauri::command]; events the
    chrome listens for are actually emitted
  - chrome JS: fetch()/invoke() wrapped in try/catch; search survives empty input
  - Rust backend: `cargo test` passes; `cargo check` clean; no unwrap() on
    fallible IO in command paths
Return PASS/FAIL per check + one-line fix per FAIL. Spawn fix agents (parallel)
for FAILs before building.

── PHASE 4: BUILD + SCREENSHOT + EVALUATE ──────────
1. Kill any running tauri/cargo/NeuralVault process.
2. `cargo test` in <app root>\src-tauri (backend correctness gate).
3. `npx tauri dev` in <app root> (background; ~45s first build, ~10s reload).
4. Screenshot the window (mcp__computer-use__screenshot; request access first).
5. Open devtools, list console errors.
6. LOOK AT THE SCREENSHOT. Judge it against the design direction AND the spec:
   does it draw, are colors right by node kind, is layout clean/refined, does it
   resemble-but-improve-on the old NV? Note visual problems, not just errors.
7. Mark each done-condition item PASS/FAIL; note what improved vs last round.

── PHASE 5: COMMIT + LOOP ──────────────────────────
If anything improved:
  git -C "C:\Users\Futur\Documents\AiWorkspace\NeuralVault" add desktop/neuralvault/
  git -C "C:\Users\Futur\Documents\AiWorkspace\NeuralVault" commit -m "feat(nv): <sub-project> round <N> — <what improved>"
If all done-conditions for this sub-project PASS: advance to the next.
Otherwise: increment round, return to Phase 1, carrying forward the screenshot
description, console errors, and checklist status.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL HARDENING LOOP — runs AFTER all 5 sub-projects pass
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Do NOT stop when SP5's done-condition passes. The per-sub-project loops only
catch what their checklists name. Now hunt for everything else. Loop this whole
phase until the app survives THREE consecutive clean rounds with zero new bugs
(loop-until-dry — a single clean round is not enough).

Each hardening round:

H1. BUILD CLEAN. Kill stray processes. `cargo test` (all crates) and
    `cargo clippy` in src-tauri; `npx tauri dev`. A test failure, a clippy
    warning, or a build warning is a bug — log it.

H2. EXERCISE EVERY FEATURE end-to-end (real vault data). For each, screenshot
    and watch the console + Rust logs:
      - open a vault; first-run indexing completes
      - map renders; clusters draw; expand a cluster; pan; zoom; resize the window
      - click a node -> detail + open note; right-click -> "Ask NV about this"
      - live search filters/highlights; empty query; query with no results
      - chat: ask a question, get an answer (text / map highlight / summary note);
        reopen app -> memory persisted
      - agents: run Vault Keeper / Analyzer; create a custom agent
      - sync: two clients edit live; a role with viewer perms cannot edit;
        audit log records the change
      - settings: add a cloud API key (stored encrypted); switch LLM routing
      - import a small Slack/CSV sample
      - close and relaunch the app cleanly (no orphaned processes, no data loss)

H3. SPAWN PARALLEL BUG-HUNTER AGENTS, each on a different lens, concurrently:
      - console/runtime errors and unhandled promise rejections
      - Rust panics, unwrap()/expect() on fallible paths, error handling gaps
      - memory/perf: leaks, unbounded growth, frame drops at scale, slow queries
      - UI/UX: layout breaks on resize, dark-mode glitches, focus traps, jank
      - data integrity: vault never corrupted, .nv/ rebuildable, edges correct
      - security: keys never logged/plaintext, audit log can't be bypassed
    Each returns a list of findings with file:line and a severity.

H4. TRIAGE + DEDUPE all findings into one list. For each real bug, spawn a
    fix agent (parallel where fixes touch different files). Apply fixes.

H5. RE-VERIFY: re-run H1+H2 and confirm each fix; make sure no fix introduced a
    regression. Count this round CLEAN only if H1 passes and H2 + H3 surface
    ZERO new real bugs.

H6. COMMIT each batch:
      git -C "C:\Users\Futur\Documents\AiWorkspace\NeuralVault" add desktop/neuralvault/
      git -C "C:\Users\Futur\Documents\AiWorkspace\NeuralVault" commit -m "fix(nv): hardening round <H> — <bugs fixed>"
    If 3 consecutive rounds are clean: STOP. Print a final report — features
    verified, bugs fixed, anything deferred. Otherwise: next hardening round.

If a bug resists 3 fix attempts: stop and write it up (repro, what you tried,
your best hypothesis) rather than thrashing.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DESIGN DIRECTION (frontend chrome)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Inspired by the old NeuralVault, NOT a copy. Modern, refined, calm, intentional —
a polished product. Keep the DNA: dark space-black backdrop, the living force
graph, the node palette above, the glowing "live" heartbeat dot, glassy floating
panels. Improve it: cleaner type + spacing rhythm, tighter control panel, smoother
motion, stronger hierarchy, less clutter.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DONE CONDITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Per sub-project (derive specifics from its spec section). SP1 specifically:
  [ ] cargo test passes (frontmatter parse, slug, type->node_kind, graph edges,
      .nv sidecar create/read)
  [ ] cargo check / build clean
  [ ] open_vault scans the live vault and returns a graph with notes + edges
  [ ] .nv/ sidecar created with config + default templates
  [ ] Python brain-server.py no longer required for the vault layer
The VISIBLE app (SP3) must additionally pass — keep looping until ALL pass:
  [ ] App builds and opens (cargo + tauri), no build errors
  [ ] Old JS canvas/quadtree frontend gone; renderer is Rust + wgpu
  [ ] Neural map renders on the GPU — colored cluster nodes + edges, colors by kind
  [ ] Cluster-first/LOD view; expanding a cluster reveals members
  [ ] Pan (drag) + zoom (scroll) move the camera smoothly
  [ ] Click a node -> detail panel with title + preview + open-note; right-click ->
      "Ask NV about this"
  [ ] Live search filters / highlights the map
  [ ] Stats bar shows node + link counts
  [ ] Map stays smooth at large node counts (LOD keeps draw count bounded)
  [ ] Design looks modern/refined — recognizably NV but clearly better, not a copy
  [ ] No red console errors on startup
Whole build: every sub-project's done-condition passes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STUCK RECOVERY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Same item fails 3 rounds: scrap that section and rewrite simpler.
- Tauri/cargo build keeps failing: read the FULL cargo error, fix the Rust.
- wgpu + Tauri compositing is the known hard part (surface a wgpu layer with the
  HTML webview over it). If it flails: render wgpu to a child window/surface via
  raw-window-handle, or a transparent webview overlay — pick one and commit.
- Any API/command errors: fix the Rust command, not the caller.
- Never raise a timeout to mask a bug — find the real cause.
- A sub-project blocks on an unmade decision: pick the minimal v1 choice, record
  it, keep moving (note it for that sub-project's plan).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
START NOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Read the spec. Read the repo state above. Continue SP1 on feat/nv-rebuild-sp1
(finish graph.rs, sidecar.rs, commands.rs, lib.rs + tests, then cargo test).
When SP1's done-condition passes, advance through SP2 -> SP5. Keep looping —
build, test, screenshot, evaluate, iterate — until every done-condition passes
and the page actually looks right. THEN run the FINAL HARDENING LOOP and do not
stop until the app survives three consecutive clean, bug-free rounds.
