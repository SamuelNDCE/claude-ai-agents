# Ruflo + NeuralVault Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bridge claude-flow (Ruflo) agent memory writes to NeuralVault and expose NeuralVault's HTTP API as MCP tools, giving Claude a unified brain accessible from both systems.

**Architecture:** `nv-mcp-server.js` is a standalone stdio MCP server (no dependencies beyond Node.js stdlib) that wraps NeuralVault's REST API at `localhost:8900`. A `PostToolUse` hook fires after every `mcp__claude-flow__memory_store` call and posts the stored key/value to NV `/api/observe`. Claude gains 5 new NV MCP tools and automatic NV persistence of all Ruflo memory writes.

**Tech Stack:** Node.js stdlib only (`http`, `readline`, `assert`). No npm packages. claude-flow MCP already running. NeuralVault already running on port 8900.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `nv-client.js` | Create | NeuralVault HTTP client — `nvGet`, `nvPost`. Imported by both the MCP server and tests. |
| `nv-mcp-server.js` | Create | MCP stdio server — reads JSON-RPC 2.0 from stdin, routes to `nv-client.js`, writes responses to stdout. |
| `.claude/helpers/nv-memory-hook.cjs` | Create | PostToolUse hook — reads tool input from stdin, calls `nvPost("/api/observe")` when `memory_store` fires. |
| `tests/nv-client.test.js` | Create | Unit tests for `nv-client.js` using a real local HTTP server as mock. |
| `tests/nv-memory-hook.test.js` | Create | Unit tests for `nv-memory-hook.cjs` using a local HTTP mock. |
| `.claude/settings.json` | Modify | Add `PostToolUse` hook entry matching `mcp__claude-flow__memory_store`. |
| `CLAUDE.md` | Modify | Add NeuralVault MCP section — document the 5 NV tools and memory bridge behaviour. |

---

## Task 1: Create `nv-client.js`

**Files:**
- Create: `nv-client.js`

- [ ] **Step 1: Write the file**

```javascript
// nv-client.js
"use strict";
const http = require("http");

const NV_HOST = process.env.NV_HOST || "localhost";
const NV_PORT = parseInt(process.env.NV_PORT || "8900", 10);

function nvGet(path, host = NV_HOST, port = NV_PORT) {
  return new Promise((resolve) => {
    const req = http.request(
      { host, port, path, method: "GET" },
      (res) => {
        let buf = "";
        res.on("data", (c) => (buf += c));
        res.on("end", () => {
          try { resolve(JSON.parse(buf)); } catch { resolve(null); }
        });
      }
    );
    req.on("error", () => resolve(null));
    req.end();
  });
}

function nvPost(path, body, host = NV_HOST, port = NV_PORT) {
  return new Promise((resolve) => {
    const data = JSON.stringify(body);
    const req = http.request(
      {
        host, port, path, method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(data),
        },
      },
      (res) => {
        let buf = "";
        res.on("data", (c) => (buf += c));
        res.on("end", () => {
          try { resolve(JSON.parse(buf)); } catch { resolve({ ok: false }); }
        });
      }
    );
    req.on("error", () => resolve({ ok: false }));
    req.write(data);
    req.end();
  });
}

module.exports = { nvGet, nvPost, NV_HOST, NV_PORT };
```

- [ ] **Step 2: Verify it loads**

```powershell
node -e "const c = require('./nv-client.js'); console.log(typeof c.nvGet, typeof c.nvPost)"
```

Expected output: `function function`

- [ ] **Step 3: Commit**

```powershell
git add nv-client.js
git commit -m "feat: add NeuralVault HTTP client module"
```

---

## Task 2: Write and pass tests for `nv-client.js`

**Files:**
- Create: `tests/nv-client.test.js`

- [ ] **Step 1: Create tests directory and write failing tests**

```powershell
mkdir -p tests
```

```javascript
// tests/nv-client.test.js
"use strict";
const assert = require("assert");
const http = require("http");
const { nvGet, nvPost } = require("../nv-client.js");

let server;
let lastRequest = null;
let mockResponseBody = {};

async function startMockServer() {
  return new Promise((resolve) => {
    server = http.createServer((req, res) => {
      let body = "";
      req.on("data", (chunk) => (body += chunk));
      req.on("end", () => {
        lastRequest = { method: req.method, url: req.url, body };
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify(mockResponseBody));
      });
    });
    server.listen(0, () => resolve(server.address().port));
  });
}

async function stopMockServer() {
  return new Promise((resolve) => server.close(resolve));
}

async function run() {
  const port = await startMockServer();
  let passed = 0;
  let failed = 0;

  async function test(name, fn) {
    try {
      await fn();
      console.log(`  PASS: ${name}`);
      passed++;
    } catch (err) {
      console.log(`  FAIL: ${name} — ${err.message}`);
      failed++;
    }
  }

  // Test nvGet
  await test("nvGet sends GET request to correct path", async () => {
    mockResponseBody = { results: [{ id: "wiki/test" }] };
    const result = await nvGet("/api/search?q=hello", "localhost", port);
    assert.strictEqual(lastRequest.method, "GET");
    assert.strictEqual(lastRequest.url, "/api/search?q=hello");
    assert.deepStrictEqual(result, { results: [{ id: "wiki/test" }] });
  });

  await test("nvGet returns null on connection error", async () => {
    const result = await nvGet("/api/search?q=x", "localhost", 1);
    assert.strictEqual(result, null);
  });

  // Test nvPost
  await test("nvPost sends POST with JSON body", async () => {
    mockResponseBody = { ok: true, file: "wiki/agent-inbox/test.md" };
    const result = await nvPost("/api/observe", { title: "t", content: "c" }, "localhost", port);
    assert.strictEqual(lastRequest.method, "POST");
    assert.strictEqual(lastRequest.url, "/api/observe");
    assert.deepStrictEqual(JSON.parse(lastRequest.body), { title: "t", content: "c" });
    assert.strictEqual(result.ok, true);
  });

  await test("nvPost returns {ok:false} on connection error", async () => {
    const result = await nvPost("/api/observe", { title: "t", content: "c" }, "localhost", 1);
    assert.strictEqual(result.ok, false);
  });

  await stopMockServer();

  console.log(`\n${passed} passed, ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
}

run().catch((err) => { console.error(err); process.exit(1); });
```

- [ ] **Step 2: Run tests — expect them to pass**

```powershell
node tests/nv-client.test.js
```

Expected output:
```
  PASS: nvGet sends GET request to correct path
  PASS: nvGet returns null on connection error
  PASS: nvPost sends POST with JSON body
  PASS: nvPost returns {ok:false} on connection error

4 passed, 0 failed
```

- [ ] **Step 3: Commit**

```powershell
git add tests/nv-client.test.js
git commit -m "test: add nv-client unit tests"
```

---

## Task 3: Create `nv-mcp-server.js`

**Files:**
- Create: `nv-mcp-server.js`

- [ ] **Step 1: Write the MCP server**

```javascript
// nv-mcp-server.js
"use strict";
const readline = require("readline");
const { nvGet, nvPost } = require("./nv-client.js");

const TOOLS = [
  {
    name: "nv_observe",
    description: "Save a quick observation or memory to NeuralVault. Lands in wiki/agent-inbox/. Use whenever Claude learns something worth persisting.",
    inputSchema: {
      type: "object",
      properties: {
        title: { type: "string", description: "Short title for the note" },
        content: { type: "string", description: "The observation or memory content (markdown)" },
      },
      required: ["title", "content"],
    },
  },
  {
    name: "nv_search",
    description: "Search NeuralVault notes by keyword. Returns up to 40 matching notes with titles, types, and snippets.",
    inputSchema: {
      type: "object",
      properties: { q: { type: "string", description: "Search keywords" } },
      required: ["q"],
    },
  },
  {
    name: "nv_ask",
    description: "Ask a natural-language question against the NeuralVault knowledge graph. Returns an extractive answer from the best-matching notes plus source IDs.",
    inputSchema: {
      type: "object",
      properties: { q: { type: "string", description: "The question to ask" } },
      required: ["q"],
    },
  },
  {
    name: "nv_note",
    description: "Read the full markdown content of a NeuralVault note by its ID (path without .md extension, e.g. 'wiki/lessons/my-note').",
    inputSchema: {
      type: "object",
      properties: { id: { type: "string", description: "Note ID — the file path relative to the vault, without .md" } },
      required: ["id"],
    },
  },
  {
    name: "nv_create_note",
    description: "Create a structured note in NeuralVault with frontmatter. More control than nv_observe: set type, tags, and folder.",
    inputSchema: {
      type: "object",
      properties: {
        title: { type: "string", description: "Note title" },
        content: { type: "string", description: "Note body (markdown)" },
        type: {
          type: "string",
          description: "Note type — one of: observation, lesson, pattern, task, concept, entity, source, question",
          default: "note",
        },
        tags: {
          type: "array",
          items: { type: "string" },
          description: "Tags to apply",
          default: [],
        },
      },
      required: ["title", "content"],
    },
  },
];

async function callTool(name, args) {
  if (name === "nv_observe") {
    const r = await nvPost("/api/observe", { title: args.title, content: args.content });
    return text(JSON.stringify(r));
  }
  if (name === "nv_search") {
    const r = await nvGet(`/api/search?q=${encodeURIComponent(args.q)}`);
    return text(JSON.stringify(r ?? { results: [] }));
  }
  if (name === "nv_ask") {
    const r = await nvGet(`/api/ask?q=${encodeURIComponent(args.q)}`);
    return text(JSON.stringify(r ?? { answer: "NeuralVault offline", sources: [] }));
  }
  if (name === "nv_note") {
    const r = await nvGet(`/api/note?id=${encodeURIComponent(args.id)}`);
    return text(JSON.stringify(r ?? { error: "not found" }));
  }
  if (name === "nv_create_note") {
    const r = await nvPost("/api/note", {
      title: args.title,
      content: args.content,
      type: args.type || "note",
      tags: args.tags || [],
    });
    return text(JSON.stringify(r));
  }
  return { content: [{ type: "text", text: `{"error":"unknown tool: ${name}"}` }], isError: true };
}

function text(s) {
  return { content: [{ type: "text", text: s }] };
}

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + "\n");
}

const rl = readline.createInterface({ input: process.stdin, terminal: false });

rl.on("line", async (line) => {
  if (!line.trim()) return;
  let msg;
  try { msg = JSON.parse(line); } catch { return; }

  const { id, method, params } = msg;

  if (method === "initialize") {
    send({ jsonrpc: "2.0", id, result: {
      protocolVersion: "2024-11-05",
      capabilities: { tools: {} },
      serverInfo: { name: "neuralvault", version: "1.0.0" },
    }});
    return;
  }

  if (method === "notifications/initialized") return;

  if (method === "tools/list") {
    send({ jsonrpc: "2.0", id, result: { tools: TOOLS } });
    return;
  }

  if (method === "tools/call") {
    const result = await callTool(params.name, params.arguments || {});
    send({ jsonrpc: "2.0", id, result });
    return;
  }

  send({ jsonrpc: "2.0", id, error: { code: -32601, message: "Method not found" } });
});
```

- [ ] **Step 2: Smoke-test the MCP server responds to `tools/list`**

```powershell
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}' | node nv-mcp-server.js
```

Expected: a JSON line with `"serverInfo":{"name":"neuralvault","version":"1.0.0"}`

- [ ] **Step 3: Commit**

```powershell
git add nv-mcp-server.js
git commit -m "feat: add NeuralVault MCP stdio server"
```

---

## Task 4: Register `nv-mcp-server.js` as a Claude MCP server

**Files:**
- No file changes — runs `claude mcp add`

- [ ] **Step 1: Register the server**

```powershell
claude mcp add neuralvault -- node "C:\Users\Futur\Documents\AiWorkspace\Claude\nv-mcp-server.js"
```

- [ ] **Step 2: Verify it appears in the MCP list**

```powershell
claude mcp list
```

Expected: `neuralvault` appears in the list alongside `claude-flow` (and codegraph).

- [ ] **Step 3: Commit nothing** (MCP registration is in user-level Claude config, not this repo)

---

## Task 5: Create `nv-memory-hook.cjs` and tests

**Files:**
- Create: `.claude/helpers/nv-memory-hook.cjs`
- Create: `tests/nv-memory-hook.test.js`

- [ ] **Step 1: Write the hook**

```javascript
// .claude/helpers/nv-memory-hook.cjs
"use strict";
/**
 * PostToolUse hook for mcp__claude-flow__memory_store.
 * Reads the hook payload from stdin, extracts key+value, POSTs to NeuralVault /api/observe.
 * Silent failure: if NV is offline, the hook exits 0 so Claude Code is not blocked.
 *
 * Stdin shape (Claude Code PostToolUse):
 * {
 *   "tool_name": "mcp__claude-flow__memory_store",
 *   "tool_input": { "key": "...", "value": "...", "namespace": "..." },
 *   "tool_response": { ... }
 * }
 */

const http = require("http");

const NV_HOST = process.env.NV_HOST || "localhost";
const NV_PORT = parseInt(process.env.NV_PORT || "8900", 10);

function nvObserve(title, content) {
  return new Promise((resolve) => {
    const body = JSON.stringify({ title, content, type: "observation", tags: ["ruflo-agent", "memory-store"] });
    const req = http.request(
      {
        host: NV_HOST, port: NV_PORT, path: "/api/observe", method: "POST",
        headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) },
      },
      (res) => {
        res.resume();
        resolve({ ok: res.statusCode === 200 });
      }
    );
    req.on("error", () => resolve({ ok: false }));
    req.write(body);
    req.end();
  });
}

async function main(inputJson) {
  let payload;
  try { payload = JSON.parse(inputJson); } catch { process.exit(0); }

  const input = payload?.tool_input || {};
  const key = String(input.key || input.title || "memory-" + Date.now());
  const value = input.value !== undefined
    ? (typeof input.value === "string" ? input.value : JSON.stringify(input.value))
    : "(no value)";

  await nvObserve(key, value);
  process.exit(0);
}

// Read stdin
let raw = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => (raw += chunk));
process.stdin.on("end", () => main(raw));

// Export for testing
module.exports = { nvObserve, main };
```

- [ ] **Step 2: Write the tests**

```javascript
// tests/nv-memory-hook.test.js
"use strict";
const assert = require("assert");
const http = require("http");

// Load the module but suppress stdin listening (it's already exported)
const { nvObserve } = require("../.claude/helpers/nv-memory-hook.cjs");

let server;
let lastRequest = null;

async function startMockServer(responseBody = { ok: true }) {
  return new Promise((resolve) => {
    server = http.createServer((req, res) => {
      let body = "";
      req.on("data", (c) => (body += c));
      req.on("end", () => {
        lastRequest = { method: req.method, url: req.url, body };
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify(responseBody));
      });
    });
    server.listen(0, () => resolve(server.address().port));
  });
}

async function stopMockServer() {
  return new Promise((resolve) => server.close(resolve));
}

async function run() {
  let passed = 0;
  let failed = 0;

  async function test(name, fn) {
    try {
      await fn();
      console.log(`  PASS: ${name}`);
      passed++;
    } catch (err) {
      console.log(`  FAIL: ${name} — ${err.message}`);
      failed++;
    }
  }

  // nvObserve needs to hit the mock server — we override env vars
  const port = await startMockServer();
  process.env.NV_HOST = "localhost";
  process.env.NV_PORT = String(port);

  // Reload module with new env (need to clear cache since env is read at module load time)
  delete require.cache[require.resolve("../.claude/helpers/nv-memory-hook.cjs")];
  const { nvObserve: nvObs } = require("../.claude/helpers/nv-memory-hook.cjs");

  await test("nvObserve POSTs to /api/observe with title and content", async () => {
    const result = await nvObs("test-key", "test-value");
    assert.strictEqual(lastRequest.method, "POST");
    assert.strictEqual(lastRequest.url, "/api/observe");
    const body = JSON.parse(lastRequest.body);
    assert.strictEqual(body.title, "test-key");
    assert.strictEqual(body.content, "test-value");
    assert.strictEqual(body.type, "observation");
    assert.deepStrictEqual(body.tags, ["ruflo-agent", "memory-store"]);
    assert.strictEqual(result.ok, true);
  });

  await test("nvObserve returns {ok:false} when NV is unreachable", async () => {
    process.env.NV_PORT = "1";
    delete require.cache[require.resolve("../.claude/helpers/nv-memory-hook.cjs")];
    const { nvObserve: nvObs2 } = require("../.claude/helpers/nv-memory-hook.cjs");
    const result = await nvObs2("key", "value");
    assert.strictEqual(result.ok, false);
  });

  await stopMockServer();
  console.log(`\n${passed} passed, ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
}

run().catch((err) => { console.error(err); process.exit(1); });
```

- [ ] **Step 3: Run the tests**

```powershell
node tests/nv-memory-hook.test.js
```

Expected output:
```
  PASS: nvObserve POSTs to /api/observe with title and content
  PASS: nvObserve returns {ok:false} when NV is unreachable

2 passed, 0 failed
```

- [ ] **Step 4: Commit**

```powershell
git add .claude/helpers/nv-memory-hook.cjs tests/nv-memory-hook.test.js
git commit -m "feat: add NV memory-store PostToolUse hook"
```

---

## Task 6: Wire the hook into `.claude/settings.json`

**Files:**
- Modify: `.claude/settings.json`

- [ ] **Step 1: Add the PostToolUse entry for `memory_store`**

In `.claude/settings.json`, find the `"PostToolUse"` array and add this entry **before** the existing `"Write|Edit|MultiEdit"` entry:

```json
{
  "matcher": "mcp__claude-flow__memory_store",
  "hooks": [
    {
      "type": "command",
      "command": "cmd /c \"node \"%CLAUDE_PROJECT_DIR%\\.claude\\helpers\\nv-memory-hook.cjs\"\"",
      "timeout": 5000
    }
  ]
}
```

The `PostToolUse` section should look like:

```json
"PostToolUse": [
  {
    "matcher": "mcp__claude-flow__memory_store",
    "hooks": [
      {
        "type": "command",
        "command": "cmd /c \"node \"%CLAUDE_PROJECT_DIR%\\.claude\\helpers\\nv-memory-hook.cjs\"\"",
        "timeout": 5000
      }
    ]
  },
  {
    "matcher": "Write|Edit|MultiEdit",
    ...existing entry...
  },
  ...
]
```

- [ ] **Step 2: Verify the JSON is valid**

```powershell
node -e "JSON.parse(require('fs').readFileSync('.claude/settings.json','utf8')); console.log('valid JSON')"
```

Expected: `valid JSON`

- [ ] **Step 3: Commit**

```powershell
git add .claude/settings.json
git commit -m "feat: wire memory_store PostToolUse hook to NeuralVault"
```

---

## Task 7: Update `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add the NeuralVault MCP section**

In the project-level `CLAUDE.md` (at `C:\Users\Futur\Documents\AiWorkspace\Claude\CLAUDE.md`), add after the existing CodeGraph section:

```markdown
# NeuralVault MCP Integration

`nv-mcp-server.js` runs as a Claude MCP server named `neuralvault`. It exposes NeuralVault's REST API (localhost:8900) as 5 tools directly callable in Claude sessions.

## NV Tools

| Tool | When to use |
|------|-------------|
| `nv_observe(title, content)` | Quick save — a fact, decision, or lesson learned |
| `nv_search(q)` | Find notes by keyword before deep work |
| `nv_ask(q)` | Natural-language question against the vault |
| `nv_note(id)` | Read full content of a specific note |
| `nv_create_note(title, content, type, tags)` | Structured note with frontmatter |

## Memory Bridge

Any call to `mcp__claude-flow__memory_store` automatically triggers a `PostToolUse` hook that also writes the key/value to NV `/api/observe`. This means Ruflo agent memory and NeuralVault stay in sync without manual intervention.

## Session Pattern

```
Session start:   curl -s http://localhost:8900/api/context  ← existing NV check
Mid-session:     nv_search(topic)                           ← find existing knowledge  
Learning saved:  mcp__claude-flow__memory_store → auto-synced to NV
Specific recall: nv_ask("what did we learn about X?")
```

## Failure Modes

- NV offline: all nv_* tools return `{"error":"..."}` gracefully; the memory hook exits silently (no Claude Code error)
- Ruflo MCP offline: nv_* tools still work independently from NeuralVault directly
```

- [ ] **Step 2: Commit**

```powershell
git add CLAUDE.md
git commit -m "docs: document NeuralVault MCP tools and memory bridge in CLAUDE.md"
```

---

## Task 8: End-to-End Verification

- [ ] **Step 1: Confirm NeuralVault is running**

```powershell
curl -s http://localhost:8900/api/search?q=test | node -e "const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')); console.log('NV online, notes:', d.results?.length ?? 0)"
```

On Windows use:
```powershell
(Invoke-WebRequest -Uri "http://localhost:8900/api/search?q=test" -UseBasicParsing).Content
```

Expected: JSON with a `results` array.

- [ ] **Step 2: Test `nv_observe` via the MCP server directly**

```powershell
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}' | node nv-mcp-server.js
```

Then in a new shell, pipe a `tools/call` for `nv_observe`:

```powershell
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"nv_observe","arguments":{"title":"integration-test","content":"Ruflo+NV bridge is working"}}}' | node nv-mcp-server.js
```

Expected: JSON with `"ok":true` and a `file` path like `wiki/agent-inbox/integration-test.md`

- [ ] **Step 3: Verify the note appeared in NeuralVault**

```powershell
(Invoke-WebRequest -Uri "http://localhost:8900/api/search?q=integration-test" -UseBasicParsing).Content
```

Expected: results array containing a note with title `integration-test`.

- [ ] **Step 4: Confirm hook fires on `memory_store`**

In a Claude Code session, call:
```
mcp__claude-flow__memory_store with key="hook-test" value="hook verification"
```

Then check NV:
```powershell
(Invoke-WebRequest -Uri "http://localhost:8900/api/search?q=hook-test" -UseBasicParsing).Content
```

Expected: a note titled `hook-test` in the results.

- [ ] **Step 5: Run all tests one final time**

```powershell
node tests/nv-client.test.js && node tests/nv-memory-hook.test.js
```

Expected: `4 passed, 0 failed` and `2 passed, 0 failed`

---

## Self-Review

**Spec coverage check:**
- [x] Ruflo MCP registered → Task 4 (claude-flow already running; registration step adds `neuralvault` MCP)
- [x] NV HTTP API as MCP tools → Task 3 + 4 (5 tools: nv_observe, nv_search, nv_ask, nv_note, nv_create_note)
- [x] memory_store auto-sync to NV → Tasks 5 + 6 (hook + settings.json wiring)
- [x] Silent NV failure → nvObserve catches errors, hook exits 0, MCP tools return error JSON not crash
- [x] CLAUDE.md updated → Task 7
- [x] Tests for NV client → Task 2
- [x] Tests for hook → Task 5

**Placeholder scan:** None found. All steps contain complete code.

**Type consistency:** `nvObserve` used in hook matches exported name. `nvGet`/`nvPost` signature `(path, host, port)` used consistently in test and client.
