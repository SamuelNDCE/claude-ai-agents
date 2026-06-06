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
