# NeuralVault Dev Session — 2026-06-07

Exported from Claude Code session `f4baa080-b1db-443b-828e-47236b70d2d1`.  
Files modified: `NeuralVault.html`, `manage.html`, `brain-server.py`, `agents.json`.

---

## 1. NeuralVault.html — Controls panel fixes

### Toggle button lag (was CPU-bound layout property)
The `#panelToggle` was using `transition: right` while the panel used `transition: transform`. They ran on different compositing paths and the button lagged. Fixed by switching both to `transform`.

```css
/* Before */
#panelToggle.open { right: 272px; transition: right .3s; }

/* After */
#panelToggle { transition: transform .15s ease; }
#panelToggle.open { transform: translateY(-50%) translateX(-272px); }
```

### Vault type breakdown grid gap
`.vb-grid { gap: 2px 0 }` — zero column gap made concept/lesson/hub run into source/entity/person.  
Fixed: `gap: 3px 28px`.

### Panel slide speed
Removed `backdrop-filter: blur(12px)` (expensive GPU composite on every frame). Cut transition from `.3s cubic-bezier` to `.15s ease`.

### Controls panel — new sections added
All visual controls (camera, appearance, synapses) removed — values locked. Panel now has:

| Section | Contents |
|---------|----------|
| View | Fit view button + Labels toggle |
| Learning | STDP toggle, Activity fires/s, Memory weight count |
| Vault | Live type-count grid (concept/source/lesson/entity/hub/person) — from NODES array |
| Observe | Textarea + Save button → `POST /api/observe` |
| Storage | Brain size, memory, notes/engine |
| Agents | Most recently active agent name + snippet, link to /manage |

Graph poll interval changed from 4s → 10s.

---

## 2. manage.html — Agent edit form (inline accordion)

### The problem
Form was always visible at the bottom. Clicking Edit scrolled to a static form with no visual connection to the agent being edited.

### Solution: true DOM-move accordion

`agentFormWrap` lives in `#formStorage` when idle. Clicking Edit:
1. `clearInterval(pollInterval)` — pauses the 4s poll so `$("agents").innerHTML` isn't rebuilt while form is live
2. `card.after(formWrap)` — physically moves the form node directly below the clicked card
3. Card gets `.editing` class (blue highlight border)

Cancel/Save moves it back: `$("formStorage").appendChild(w)` then restarts poll.

```js
function _showForm(anchor){
  const w = $("agentFormWrap");
  if (anchor) anchor.after(w); else $("agents").appendChild(w);
  w.style.display = "block";
  requestAnimationFrame(() => w.scrollIntoView({behavior:"smooth", block:"nearest"}));
}

function exitEdit(){
  _clearFields();
  const w = $("agentFormWrap"); w.style.display = "none";
  $("formStorage").appendChild(w);
  if (!pollInterval) pollInterval = setInterval(load, 4000);
}
```

`startEdit(x, card)` calls `_showForm(card)`.  
`+ New` button (in sectit header) calls `_showForm(null)` — appends to bottom of agents list.

### pollInterval pattern
```js
let editId = null, pollInterval = null;
// Init:
pollInterval = setInterval(load, 4000);
// exitEdit restarts with guard:
if (!pollInterval) pollInterval = setInterval(load, 4000);
```

### Field visibility per type (syncType)

| Type | Shown | Hidden |
|------|-------|--------|
| session | Name, Role | interval, model, goal, Advanced, Behavior row |
| vault-keeper | Name, Role, interval | model, goal, Advanced, Behavior row |
| llm | everything | nothing |

```js
function syncType(){
  const t = $("fType").value;
  const llm = t === "llm";
  const isSystem = t === "vault-keeper" || t === "session";
  const needsModel = t === "llm";
  const needsInterval = t !== "session";
  const tl = $("typeLabel"); if (tl) tl.style.display = isSystem ? "none" : "flex";
  $("goalWrap").style.display = llm ? "flex" : "none";
  $("modelWrap").style.display = needsModel ? "flex" : "none";
  if (!needsModel) $("customModelWrap").style.display = "none";
  const il = $("intLabel"); if (il) il.style.display = needsInterval ? "flex" : "none";
  $("advToggle").style.display = llm ? "" : "none";
  if (!llm){ $("advFields").style.display = "none"; $("advToggle").textContent = "▸ Advanced"; }
}
```

### Behavior dropdown — cleaned
Removed: stats, curator, linter, linker (Vault Keeper covers all of these now).  
Kept: `llm`, `vault-keeper` (system), `session` (external).  
Default for new agents: `llm`.

---

## 3. Agent roster — three sections

### Final agents (agents.json)

| Agent | ID | Type | Interval | Notes |
|---|---|---|---|---|
| Vault Keeper | linker-8337 | vault-keeper | 30m | Runs ALL 4 ops: stats + curator + linter + linker |
| News Pulse | news-pulse-2183 | llm | 4h | Web search: AI/SaaS/dev news digest |
| Vault Analyst | vault-analyst-2350 | llm | 1h | Homelab + patterns + PerpTech strategy |
| Claude | claude-2350 | session | disabled | Stamped by observe hook on every vault write |

### manage.html three sections

```
▸ Vault        (green)  — Vault Keeper only (compact, protected)
▸ AI Agents    (pink)   — Vault Analyst, News Pulse
▸ Sessions     (blue)   — Claude
```

JS categorization:
```js
const vkAgents   = a.filter(x => x.type === 'vault-keeper');
const aiAgents   = a.filter(x => x.type === 'llm');
const sessAgents = a.filter(x => x.type === 'session');
```

### Protected agents
Vault Keeper and Claude (`isProtected = isVK || isSess`):
- No delete button
- Claude also has no toggle and no Run button
- Behavior row hidden when editing them

---

## 4. brain-server.py changes

### vault-keeper type — runs all 4 ops
```python
def agent_vault_keeper(a=None):
    """Runs all four vault maintenance tasks in one pass."""
    results = []
    try: results.append(agent_stats(a))
    except Exception as e: results.append(f"stats error: {e}")
    try: results.append(agent_curator(a))
    except Exception as e: results.append(f"curator error: {e}")
    try: results.append(agent_linter(a))
    except Exception as e: results.append(f"linter error: {e}")
    try: results.append(agent_linker(a))
    except Exception as e: results.append(f"linker error: {e}")
    return " · ".join(results)
```

Combined last_result example: `626 neurons, 5567 synapses · 0 orphans, 66 dup titles · 160 notes scanned, 1 gaps · linked 0/0 weak notes`

### session type — Claude agent
```python
def agent_session(a=None):
    return "session agent — updated by Claude Code activity"
```

### observe hook — stamps Claude on every vault write
Added to the `/api/observe` handler after `api_create_note()`:
```python
if path == "/api/observe":
    _snip = (payload.get("content") or "")[:120].replace("\n", " ").strip()
    for _ag in AGENTS:
        if _ag.get("type") == "session":
            _ag["last_run"] = int(time.time())
            _ag["last_result"] = _snip or "observed"
            save_agents(AGENTS)
            break
```

Matches by `type == "session"` (not by id, since the API auto-generates ids).

### BEHAVIORS dict
```python
BEHAVIORS = {
    "stats": agent_stats, "curator": agent_curator,
    "linter": agent_linter, "linker": agent_linker,
    "llm": agent_llm,
    "vault-keeper": agent_vault_keeper,
    "session": agent_session
}
```

### ⚠️ Server restart required
All brain-server.py changes (vault-keeper type, session type, observe hook) require restarting the running server:
```
python brain-server.py
```

---

## 5. API gotcha — agents always get auto-generated IDs

`POST /api/agents` with `id: "some-name"` only LOOKS UP existing agents by that id.  
New agents always get: `slugify(name) + "-" + last4digits(unix_time)`.

To update an existing agent you MUST pass its real auto-generated id.  
Passing a custom id with no matching agent creates a duplicate with a new id.

---

## 6. CSS additions (manage.html)

```css
/* Inline accordion */
.agent.editing { border-color: rgba(79,179,255,.45)!important; box-shadow: 0 0 0 2px rgba(79,179,255,.09)!important }
.form-hdr { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px }
.form-hdr span { font-size:10px; letter-spacing:.14em; text-transform:uppercase; color:var(--dim); font-weight:750 }
#agentFormWrap .panel { border-top: 2px solid rgba(79,179,255,.18) }

/* New agent types */
.agent[data-type="vault-keeper"]::before { background: var(--green) }
.agent[data-type="session"]::before { background: var(--blue) }
.agent:has(.tog.on)[data-type="vault-keeper"] { border-color: rgba(61,202,110,.22) }
```
