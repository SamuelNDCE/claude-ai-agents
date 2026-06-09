#!/usr/bin/env node
/**
 * codegraph-nv-bridge
 * MCP proxy: wraps `codegraph serve --mcp` and caches every tool result
 * to NeuralVault so future sessions get architecture knowledge for free.
 *
 * Architecture:
 *   Claude Code  →  bridge (this, stdio)  →  codegraph child (stdio)
 *                            ↓
 *                    NeuralVault vault filesystem (via nv-fs.js)
 */

"use strict";

const { spawn } = require("child_process");
const readline = require("readline");
const crypto = require("crypto");
const { nvObserveFs, nvSearchFs } = require("./nv-fs.js");

// ── Config ──────────────────────────────────────────────────────────────────
// Only save results from these tools (others are noisy or transient)
const SAVE_TOOLS = new Set([
  "codegraph_explore",
  "codegraph_search",
  "codegraph_impact",
  "codegraph_callers",
  "codegraph_callees",
  "codegraph_node",
]);

// ── helpers ──────────────────────────────────────────────────────────────────
function toolKey(toolName, args) {
  const sig = toolName + JSON.stringify(args || {});
  return crypto.createHash("sha1").update(sig).digest("hex").slice(0, 8);
}

function extractText(result) {
  if (!result) return "";
  if (typeof result === "string") return result.slice(0, 2000);
  if (result.content) {
    const parts = Array.isArray(result.content) ? result.content : [result.content];
    return parts
      .filter((p) => p.type === "text")
      .map((p) => p.text)
      .join("\n")
      .slice(0, 2000);
  }
  return JSON.stringify(result).slice(0, 2000);
}

async function saveToNV(toolName, args, result) {
  if (!SAVE_TOOLS.has(toolName)) return;

  const key = toolKey(toolName, args);
  const query = args?.query || args?.name || args?.symbol || args?.search || JSON.stringify(args).slice(0, 60);
  const title = `codegraph-${toolName.replace("codegraph_", "")}-${key}`;

  // Avoid re-saving identical queries
  const existing = nvSearchFs(title);
  if (existing?.results?.some((r) => r.title === title)) return;

  const text = extractText(result);
  const content = [
    `# CodeGraph: ${toolName} — ${query}`,
    "",
    `**Tool:** \`${toolName}\`  `,
    `**Args:** \`${JSON.stringify(args)}\``,
    "",
    "## Result",
    "",
    text,
    "",
    "---",
    `*Cached by codegraph-nv-bridge · [[codegraph-knowledge-graph]]*`,
  ].join("\n");

  nvObserveFs({
    title,
    content,
    type: "pattern",
    folder: "wiki/codegraph",
    tags: ["codegraph-cache", toolName],
  });
}

// ── Bridge extra tool: kg_search_nv ─────────────────────────────────────────
// Exposes a lightweight NV search so Claude can check cached findings
// BEFORE calling codegraph, saving tokens on repeated queries.

const EXTRA_TOOL = {
  name: "codegraph_kg_nv",
  description:
    "Search NeuralVault for previously cached CodeGraph findings (architecture, symbol impacts, call graphs). " +
    "Call this BEFORE codegraph_explore or codegraph_impact to retrieve cached results and avoid redundant token-heavy queries.",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string", description: "Symbol name, concept, or architecture question" },
    },
    required: ["query"],
  },
};

async function handleExtraTool(args) {
  const q = args?.query || "";
  const results = nvSearchFs("codegraph " + q);
  if (!results?.results?.length) {
    return { content: [{ type: "text", text: "No cached findings for this query. Use codegraph_explore or codegraph_search." }] };
  }
  const hits = results.results.slice(0, 5);
  const lines = hits.map((r) => `### ${r.title}\n${r.excerpt || ""}`);
  return {
    content: [{ type: "text", text: `Found ${hits.length} cached finding(s):\n\n${lines.join("\n\n")}` }],
  };
}

// ── JSON-RPC proxy ───────────────────────────────────────────────────────────

function writeMsg(msg) {
  process.stdout.write(JSON.stringify(msg) + "\n");
}

const pending = new Map(); // id → { method, params }

// Spawn codegraph directly via its npm-shim, bypassing .cmd on Windows.
// Falls back to system PATH 'codegraph' on non-Windows.
const CG_SHIM = (() => {
  try {
    const { execSync } = require("child_process");
    // Find the npm global prefix
    const prefix = execSync("npm root -g", { encoding: "utf8", timeout: 5000 }).trim();
    const shim = require("path").join(prefix, "@colbymchenry", "codegraph", "npm-shim.js");
    if (require("fs").existsSync(shim)) return shim;
  } catch {}
  return null;
})();

const cg = CG_SHIM
  ? spawn(process.execPath, [CG_SHIM, "serve", "--mcp"], {
      stdio: ["pipe", "pipe", "inherit"],
      windowsHide: true,
    })
  : spawn("codegraph", ["serve", "--mcp"], {
      stdio: ["pipe", "pipe", "inherit"],
      shell: process.platform === "win32",
    });

cg.on("error", (err) => {
  process.stderr.write(`[bridge] codegraph spawn error: ${err.message}\n`);
  process.exit(1);
});

cg.on("exit", (code) => {
  process.exit(code ?? 0);
});

// codegraph stdout → Claude (with interception)
const cgOut = readline.createInterface({ input: cg.stdout, terminal: false });
let toolsList = null; // cache tools list so we can inject our extra tool

cgOut.on("line", async (line) => {
  let msg;
  try { msg = JSON.parse(line); } catch { process.stdout.write(line + "\n"); return; }

  // Intercept tools/list response to inject kg_search_nv
  if (msg.result?.tools) {
    toolsList = msg.result.tools;
    msg.result.tools = [...toolsList, EXTRA_TOOL];
    writeMsg(msg);
    return;
  }

  // Intercept tool call responses
  if (msg.id !== undefined && pending.has(msg.id)) {
    const req = pending.get(msg.id);
    pending.delete(msg.id);

    if (req.method === "tools/call" && msg.result) {
      // Fire-and-forget save to NV
      saveToNV(req.params.name, req.params.arguments, msg.result).catch(() => {});
    }
  }

  writeMsg(msg);
});

// Claude stdin → codegraph (with extra tool interception)
const stdinRL = readline.createInterface({ input: process.stdin, terminal: false });

stdinRL.on("line", async (line) => {
  let msg;
  try { msg = JSON.parse(line); } catch { cg.stdin.write(line + "\n"); return; }

  // Track outgoing calls for response correlation
  if (msg.id !== undefined && msg.method) {
    pending.set(msg.id, { method: msg.method, params: msg.params });
  }

  // Handle our injected extra tool locally
  if (msg.method === "tools/call" && msg.params?.name === "codegraph_kg_nv") {
    pending.delete(msg.id);
    const result = await handleExtraTool(msg.params.arguments);
    writeMsg({ jsonrpc: "2.0", id: msg.id, result });
    return;
  }

  // Forward everything else to codegraph
  cg.stdin.write(line + "\n");
});

stdinRL.on("close", () => {
  cg.stdin.end();
});
