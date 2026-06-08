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
  docs/superpowers/specs/2026-06-07-nv-agentic-os-design.md

It defines: vision/principles (search free, generation paid; vault is truth;
local-first; federated), Approach A architecture (Tauri app + Rust server),
the 5 sub-projects in dependency order, the data model (.nv/ sidecar,
Obsidian-compatible vaults), search (LanceDB hybrid + nomic-embed via Ollama
+ RRF, <10ms @ 1M), neural map (cluster-first), NV chat, sync/roles/collab
(Yjs CRDT), agents (Vault Keeper / Analyzer / custom), integrations,
licensing/website, v1 out-of-scope, and deferred open questions.

If anything in this prompt conflicts with the spec, the spec wins.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DESIGN DIRECTION (FRONTEND)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- The old frontend is dead. Delete it and rewrite clean.
- Take INSPIRATION from the old NeuralVault, do not copy it. Make it better:
  more modern, more refined, calmer, more intentional. A polished product,
  not a prototype.
- Keep the recognizable DNA: dark space-black canvas, the living
  force-directed neural map, the node palette below, the glowing "live"
  heartbeat dot, glassy floating panels.
- Improve on it: cleaner type + spacing rhythm, tighter cohesive control
  panel, smoother motion, stronger visual hierarchy, less clutter.

RENDERING ARCHITECTURE (important — not a JS canvas):
- The neural map's force simulation AND rendering run in RUST on the GPU via
  `wgpu` (WebGPU), drawing to a surface in the Tauri window. Per-frame physics
  and node/edge drawing never touch JavaScript.
- The HTML/CSS webview is UI CHROME ONLY — panels, search box, stats bar,
  detail panel, chat — overlaid on the GPU surface. Vanilla HTML/CSS + minimal
  JS for chrome and for calling Rust commands (Tauri invoke). No UI frameworks.
- Scaling strategy is CLUSTER-FIRST + LOD: draw community clusters as single
  nodes by default (a few hundred draws even at 1M notes); materialize
  individual nodes via level-of-detail as the user zooms into / clicks a
  cluster. Keep the per-frame draw count bounded regardless of vault size.
  Node colors: entity #ff9e3d  concept #46b1ff  source #56d364
               hub #b98cff  person #ffd23d  default #7d8aa0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOCATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
App root:     C:\Users\Futur\Documents\AiWorkspace\NeuralVault\desktop\neuralvault
Frontend:     <app root>\src\            (index.html, app.js, styles.css)
Rust backend: <app root>\src-tauri\src\lib.rs
Brain server: C:\Users\Futur\Documents\Obsidian Vault\Claude\brain-server.py
Repo root:    C:\Users\Futur\Documents\AiWorkspace\NeuralVault
Dev command:  cd <app root> && npx tauri dev

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERMISSIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You MAY:  rewrite all of src/; edit src-tauri/ Rust; edit brain-server.py;
          add new Rust modules, Python endpoints, and .nv/ logic per the spec;
          add dependencies the spec requires (LanceDB, Ollama client, Yjs, etc.).
You MUST NOT change:
  - vault path: C:\Users\Futur\Documents\Obsidian Vault\Claude
  - port 8900
  - the vault's .md note files (the actual notes)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REMOVE OLD CODE — AGGRESSIVELY BUT SAFELY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Delete every old frontend file in src/ except assets/.
  (kill if present: neuralvault.html, nv-renderer.js, physics-worker.js,
   nv-quadtree.js, main.js, stale styles.)
- Do NOT carry over old physics-worker.js or nv-quadtree.js — the old JS
  canvas/quadtree approach is replaced entirely by the Rust + wgpu renderer
  with cluster/LOD. Write the new force sim and renderer in Rust.
- Strip dead HTML elements, unused CSS, unused JS the new design doesn't need.
- Before deleting a file, confirm nothing in lib.rs or tauri.conf.json
  references it. The Tauri build must still find its entry point.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BUILD ORDER — 5 SUB-PROJECTS (per the spec, in dependency order)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Build in this order. Do NOT start a sub-project until the previous one's
done-condition passes. Within a sub-project, fan out parallel agents.

  SP1  Core data + vault layer   — vault discovery, .nv/ sidecar, frontmatter,
                                    default templates. (Foundation.)
  SP2  Search                    — LanceDB hybrid index, nomic-embed via Ollama,
                                    RRF ranking, first-run indexing UX.
  SP3  Neural map + frontend     — Rust + wgpu GPU renderer with cluster/LOD
                                    force sim; HTML/CSS chrome overlay:
                                    click/right-click, pan/zoom, detail panel,
                                    live search, stats. (The visible app.)
  SP4  NV chat + agents          — persistent memory, login briefings,
                                    Vault Keeper / Analyzer / custom agents,
                                    map highlighting on answers.
  SP5  Sync / collab / licensing — Yjs CRDT, admin/editor/viewer roles, audit
       / integrations / website    log, encryption, importers (Slack/email/
                                    CSV/CRM), REST API, per-seat licensing
                                    (phone-home), pricing configurator, blog.

For each sub-project, consult the spec's matching section AND its deferred
open questions; resolve open questions minimally for v1 and note the choice.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE LOOP — repeat per sub-project until its done-condition passes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

── PHASE 1: PLAN (1 architect agent) ──────────────
Spawn an architect agent. Input: the spec section for this sub-project +
current state (screenshot description, console/build errors, failing items).
Output JSON: { round, diagnosis, tasks:[{id, file, what, how, independent,
depends_on}] }. One task per file per round (parallel coders must not collide).
Round 1 of a sub-project: spec the full initial build. Later rounds: spec only
what's broken. Spec only — no code.

── PHASE 2: PARALLEL CODERS (N agents concurrently) ─
One agent per independent task, run concurrently. Dependent tasks run after
their dependency completes. Each coder:
  - implements exactly one task, writes the file, returns a 3-bullet summary
  - RENDERER work (the map) is RUST + wgpu: force sim, cluster/LOD, GPU draw,
    input handling, exposed to the webview via Tauri commands/events. Organize
    into clear Rust modules (e.g. render/, sim/, cluster/).
  - CHROME work (app.js) is minimal vanilla JS: build the panels/search/stats,
    call Rust via Tauri invoke, render results. No force sim or canvas draw here.
  - keeps spawn_server()/lifecycle intact in lib.rs
  - edits brain-server.py surgically (only the failing/needed route)

── PHASE 3: REVIEW (1 agent; fixes fan out) ────────
Read the changed files. Verify wiring & correctness:
  - index.html loads chrome JS as <script type="module">; chrome selectors
    map to real elements and styled selectors exist
  - Rust renderer: cargo check compiles; the wgpu render loop runs each frame;
    node positions seeded before the first draw; pan/zoom transform the
    camera/view matrix, not the underlying node data
  - cluster/LOD: default view draws clusters not all nodes; expanding a cluster
    materializes its members; per-frame draw count stays bounded
  - Tauri bridge: every JS invoke() targets a real #[tauri::command]; events
    the chrome listens for are actually emitted
  - chrome JS: fetch()/invoke() wrapped in try/catch; search survives empty
    input; no undefined-deref risks
  - if brain-server.py changed: new route reachable
Return PASS/FAIL per check + one-line fix per FAIL. Spawn fix agents (parallel)
for FAILs before building.

── PHASE 4: BUILD + SCREENSHOT + EVALUATE ──────────
1. Kill any running tauri/cargo/NeuralVault process.
2. Run `npx tauri dev` in <app root> (background; ~45s first build, ~10s reload).
3. Take a screenshot of the window (mcp__computer-use__screenshot, requesting
   computer access first).
4. Open devtools, list console errors.
5. LOOK AT THE SCREENSHOT. Judge it against the design direction AND the spec:
   does it draw, are colors right, is the layout clean and refined, does it
   actually resemble-but-improve-on the old NV? Note what looks wrong visually,
   not just what errors out.
6. Mark each done-condition item PASS/FAIL; note what improved vs last round.

── PHASE 5: COMMIT + LOOP ──────────────────────────
If anything improved:
  git -C "C:\Users\Futur\Documents\AiWorkspace\NeuralVault" add desktop/neuralvault/
  git -C "C:\Users\Futur\Documents\AiWorkspace\NeuralVault" commit -m "feat(nv): <sub-project> round <N> — <what improved>"
If all done-conditions for this sub-project PASS: advance to the next sub-project.
Otherwise: increment round, go back to Phase 1, carrying forward the screenshot
description, console errors, and checklist status.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DONE CONDITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Per sub-project (derive specifics from its spec section). The VISIBLE app
(SP3) must additionally pass — and you keep looping on it until ALL pass:
  [ ] App builds and opens (cargo + tauri), no build errors
  [ ] Old JS canvas/quadtree frontend gone; renderer is Rust + wgpu
  [ ] Neural map renders on the GPU — colored cluster nodes + edges, colors by type
  [ ] Cluster-first/LOD view; expanding a cluster reveals members
  [ ] Pan (drag) + zoom (scroll) move the camera smoothly
  [ ] Click a node → detail panel (HTML chrome) with title + preview text
  [ ] Live search filters / highlights the map
  [ ] Stats bar shows node + link counts
  [ ] Map stays smooth at large node counts (LOD keeps draw count bounded)
  [ ] Design looks modern/refined — recognizably NV but clearly better,
      not a copy (judged from the screenshot)
  [ ] No red console errors on startup
Whole build: every sub-project's done-condition passes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STUCK RECOVERY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Same item fails 3 rounds: scrap that section and rewrite simpler.
- Tauri build keeps failing: read the full cargo error, fix lib.rs.
- /graph.json (or any API) errors: fix the route in brain-server.py.
- Never raise a timeout to mask a bug — find the real cause.
- A sub-project blocks on an unmade decision: pick the minimal v1 choice,
  record it, and keep moving (note it for that sub-project's plan).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
START NOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Read the spec. Do Phase 0 cleanup (delete old frontend, keep assets/, confirm
the Tauri entry point). Take a baseline screenshot. Begin SP1, Round 1.
Keep looping — build, screenshot, evaluate, iterate — until every done-condition
passes and the page actually looks right.
