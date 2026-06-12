# NeuralVault Session Handoff — 2026-06-12

## What to tell the next session

> "Continue NeuralVault desktop work. Read this handoff first."

---

## Binary state

- **Repo**: `C:\Users\Futur\Documents\AiWorkspace\NeuralVault`
- **Build**: `cargo build --release -p neuralvault-desktop` — was clean at end of session
- **Run**: `NeuralVault-Desktop.bat` or the exe in `target\release\`
- **Kill before rebuild**: `Stop-Process -Name "neuralvault-desktop" -Force`

---

## Everything shipped this session

### Fixed: Anthropic 400 error
- Root cause: `~/.neuralvault-provider` was set to `"anthropic"` → every send hit Anthropic API → 400 credit error
- Fix: reset file to `"ollama"`. Now Ollama is the default; user picks provider from the in-chat ComboBox

### Multi-provider routing (`app.rs`)
- `nv_send()` now uses `match self.chat_provider` (was implicit bool based on key presence)
- Providers: `"ollama"` / `"anthropic"` / `"openai_compat"`
- `spawn_openai_compat_stream()` — full SSE for LM Studio, llama.cpp, Jan, etc.
- Config: `~/.neuralvault-compat.json` → `{"base": "...", "model": "...", "key": "..."}`
- New AppState fields: `openai_compat_base`, `openai_compat_model`, `openai_compat_key`

### Chat UI (`ui/chat_tab.rs`)
- Model label in left-rail footer → interactive ComboBox (3 sections: Anthropic / Ollama / OpenAI-compat)
- Conversation right-click → "Rename" → inline TextEdit, Enter commits, Escape cancels
- AppState field: `chat_renaming: Option<(String, String)>` at line 615

### Chat bubbles (`ui/chat.rs`)
- "copy" pill at bottom-right of every assistant bubble

### Context rot (`app.rs`)
- `Backend::finish_stream()`: trim at 50 msgs, keep 30, insert system marker. Both NvChat + agent threads.

### Agent reasoning (`packages/agents/src/tools.rs` + `app.rs`)
- `reasoning_preamble()` injected at top of every agent system prompt
- `agent_inbox_block()` reads and injects `agents/<id>-inbox.md`

### Search (`ui/search_overlay.rs`)
- `@people` pill filters to `wiki/entities/people` (FolderId exact match)
- `@agents` + `@decisions` visual-only (no folder mapping yet)
- Pill toggles now retrigger search via egui temp `search_prev_pills`

### Other
- Ollama: 10s connect + 120s response timeout (no more infinite hangs)
- Tool rounds cap: 3 → 8
- `FileKeeper/AiManager/CustomAgent tick()` panics → `Ok(())`
- `memory::store.delete()` + `chat_delete_conversation()`

---

## Pending: user was selecting from audit list

At end of session an interactive widget showed 20 items. User hadn't confirmed yet.
**Show them the list again (or rebuild it) and ask which to implement.**

### Broken (UI exists, doesn't work)
| # | Item | What's wrong |
|---|------|-------------|
| B1 | Voice mic button | Stub — no audio capture or Whisper |
| B2 | Cron schedule UI doesn't load saved values | Reverse parse never called |
| B3 | Board card drag-drop doesn't persist | Save only fires via agent edit |
| B4 | Search history not persisted | Memory-only, never written to disk |
| B5 | Dashboard "tasks done" always 0 | Board done-column never mapped |
| B6 | File Keeper dupe settings unused | Settings stored, never read by logic |
| B7 | Other cloud keys (OpenAI/Google/Groq) ignored | Only Anthropic wired in routing |
| B8 | OpenAI-compat config has no Settings panel | Must hand-edit JSON file |
| B9 | @agents + @decisions pills do nothing | No vault folder mapping |
| B10 | Vault context timeout silent | No banner/feedback when degrading to lexical |

### Missing (not built at all)
| # | Item | Why it matters |
|---|------|---------------|
| M1 | Markdown rendering in chat | Raw text only — no bold, code, lists |
| M2 | Message regenerate/retry | Can't redo a bad response |
| M3 | Note viewer/editor in-app | Must use external editor for vault notes |
| M4 | Export vault/note | No ZIP or PDF export |
| M5 | In-conversation search | Can't find messages in chat history |
| M6 | Notification persistence | Notifications lost on app restart |
| M7 | Scheduled run history UI | No visible log of cron agent runs |
| M8 | Agent token budget enforcement | Budget field stored but never checked |
| M9 | Vault switcher | Single vault only — no switching |
| M10 | Note linking UI | No [[wiki-link]] picker in chat |

---

## Key files

| Area | File |
|------|------|
| Main app logic | `apps/desktop/src/app.rs` |
| Chat tab (Cortex full page) | `apps/desktop/src/ui/chat_tab.rs` |
| Side chat panel | `apps/desktop/src/ui/chat.rs` |
| Agents tab | `apps/desktop/src/ui/agents_tab.rs` |
| Dashboard | `apps/desktop/src/ui/dashboard_tab.rs` |
| Neural map | `apps/desktop/src/ui/map_tab.rs` |
| Settings/Admin | `apps/desktop/src/ui/admin_tab.rs` |
| Search overlay | `apps/desktop/src/ui/search_overlay.rs` |
| LLM client | `packages/llm/src/ollama.rs` |
| Agent tools | `packages/agents/src/tools.rs` |
| Vault log | `sample-vault/wiki/logs/neuralvault-app.md` |

---

## Quick context

- egui/eframe + wgpu — immediate-mode UI, no async in render loop
- Streaming: `spawn_stream()` → tokio task → `mpsc::unbounded_channel` → `pump_stream()` each frame
- Tool rounds: `maybe_run_tool_round()` detects `[TOOL: ...]` markers, re-sends to Ollama, loops up to 8x
- Agents run via `agent_send()` / `agent_send_text()` (streaming pipeline), NOT `runner.tick_all()` (no-op)
- Vault search: `HybridIndex` (TF-IDF + cosine), RRF k=60, folder filter = exact FolderId match
- Settings persist to `~/.neuralvault-*` files in user home

---

*Handoff written 2026-06-12. Log: `sample-vault/wiki/logs/neuralvault-app.md` entry `2026-06-12 (session 2q-c)`.*
