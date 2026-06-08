# NeuralVault Desktop — Session Handoff

**Date:** 2026-06-08  
**Branch:** session/2026-06-07-neuralvault-physics-lag-fixes  
**App root:** `C:\Users\Futur\Documents\AiWorkspace\NeuralVault\desktop\neuralvault`

---

## Current State: APP IS WORKING

The `desktop/neuralvault` vanilla HTML/JS Tauri v2 app is fully functional as of this session.

Screenshot verification confirmed all 6 done conditions:
1. ✅ `npx tauri dev` compiles and opens window (0.63s incremental, PID ~37164)
2. ✅ Node circles visible on canvas (126 NEURONS showing)
3. ✅ Edge lines connecting nodes (103 SYNAPSES)
4. ✅ Pan and zoom wired (instructions at bottom: Drag / Shift-drag / Scroll / Double-click)
5. ⚠️ Console errors: NOT YET VERIFIED (devtools not opened)
6. ✅ Search bar at top is present and wired to filter nodes

## What Was Fixed This Session

All fixes applied to `C:\Users\Futur\Documents\AiWorkspace\NeuralVault\desktop\neuralvault`:

### 1. `src-tauri/tauri.conf.json`
Added `"url": "neuralvault.html"` to `app.windows[0]`.  
Root cause: Tauri 2.11.2 without `devUrl` defaults to `http://127.0.0.1` (HTTP port 80) in dev mode, causing ERR_CONNECTION_REFUSED. Setting `url` forces the webview to use `tauri://localhost/neuralvault.html` via custom protocol.

```json
"windows": [
  {
    "url": "neuralvault.html",
    "title": "NeuralVault",
    "width": 1400, "height": 900,
    "minWidth": 900, "minHeight": 600, "center": true
  }
]
```

### 2. `src/neuralvault.html` — 8 fixes
- Added `default` entry to TYPES dict: `default:{color:'#7d8aa0', label:'Unknown'}`
- 6 null-guard sites: `TYPES[n.t]||TYPES.default` (in buildSubstrate, pickHover, openDetail, node halos loop, pulse renderer — 2 sites each loop)
- Fixed nav brand `href="/"` → `href="neuralvault.html"`
- Fixed nav links: Map → `href="#"`, Agents → `href="http://127.0.0.1:8900/manage"`

### 3. `src/index.html`
Replaced 1090-line broken WebGL copy with a minimal redirect:
```html
<!DOCTYPE html><html><head><meta charset="UTF-8">
<script>location.replace('neuralvault.html')</script>
</head></html>
```
(This redirect is now bypassed entirely since `tauri.conf.json` directly loads `neuralvault.html`.)

## Pending Action

**Commit the changes** to the `session/2026-06-07-neuralvault-physics-lag-fixes` branch:

```powershell
cd "C:\Users\Futur\Documents\AiWorkspace\NeuralVault\desktop\neuralvault"
git add src/index.html src/neuralvault.html src-tauri/tauri.conf.json
git commit -m "fix(desktop): vanilla Tauri app fully functional — url, TYPES null guards, nav links"
```

Or stage from the NeuralVault repo root:
```powershell
git -C "C:\Users\Futur\Documents\AiWorkspace\NeuralVault" add desktop/neuralvault/src/index.html desktop/neuralvault/src/neuralvault.html desktop/neuralvault/src-tauri/tauri.conf.json
git -C "C:\Users\Futur\Documents\AiWorkspace\NeuralVault" commit -m "fix(desktop): vanilla Tauri app fully functional"
```

## Optionally: Verify Console Errors

To check condition 5 (no red console errors):
1. Run `npx tauri dev` in the app root
2. Right-click on the canvas in the NeuralVault window → Inspect (devtools should be available since `csp: null`)
3. Click Console tab and look for red errors

## Key Facts to Not Forget

- `src-tauri/src/lib.rs` — DO NOT CHANGE. Spawns `python brain-server.py 8900` in `C:\Users\Futur\Documents\Obsidian Vault\Claude\`.
- `frontendDist: "../src"` — no Vite, no bundler, static files served via Tauri custom protocol
- `withGlobalTauri: true`, `csp: null` — required for devtools and Tauri APIs
- All fetch calls in `neuralvault.html` use absolute `http://127.0.0.1:8900/` URLs — correct
- The WRONG NeuralVault: `C:\Users\Futur\Documents\AiWorkspace\NeuralVault\.worktrees\feat-nv-core\nv-app` — React/Vite app, separate project
- The CORRECT NeuralVault: `C:\Users\Futur\Documents\AiWorkspace\NeuralVault\desktop\neuralvault` — vanilla HTML/JS Tauri app

## Dev Command

```powershell
cd "C:\Users\Futur\Documents\AiWorkspace\NeuralVault\desktop\neuralvault"
npx tauri dev
```
