// .claude/helpers/nv-memory-hook.cjs
"use strict";
/**
 * PostToolUse hook for mcp__claude-flow__memory_store.
 * Reads the hook payload from stdin, extracts key+value, and writes a note to
 * the NeuralVault vault filesystem (NeuralVault is a serverless Rust app now —
 * there is no HTTP API). Silent failure: never throws, the hook always exits 0.
 *
 * Stdin shape (Claude Code PostToolUse):
 * {
 *   "tool_name": "mcp__claude-flow__memory_store",
 *   "tool_input": { "key": "...", "value": "...", "namespace": "..." },
 *   "tool_response": { ... }
 * }
 */

const { nvObserveFs } = require("../../nv-fs.js");

async function nvObserve(title, content) {
  const body = JSON.stringify({ title, content });
  if (Buffer.byteLength(body) > 1_000_000) return { ok: false };
  return nvObserveFs({ title, content, type: "observation", tags: ["ruflo-agent", "memory-store"] });
}

async function main(inputJson) {
  let payload;
  try { payload = JSON.parse(inputJson); } catch { process.exit(0); }

  // Only process memory_store calls
  if (payload?.tool_name && payload.tool_name !== "mcp__claude-flow__memory_store") {
    process.exit(0);
  }

  const input = payload?.tool_input || {};
  const key = String(input.key || input.title || "memory-" + Date.now());
  const value = input.value !== undefined
    ? (typeof input.value === "string" ? input.value : JSON.stringify(input.value))
    : "(no value)";

  await nvObserve(key, value);
  process.exit(0);
}

// Only run stdin listener when executed as a script (not when required by tests)
if (require.main === module) {
  // Add timeout safety: exit before Claude Code's 5000ms timeout if stdin never closes
  const timeoutHandle = setTimeout(() => process.exit(0), 4000);
  timeoutHandle.unref(); // Don't keep process alive just for this timeout

  // Read stdin
  let raw = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => (raw += chunk));
  process.stdin.on("end", () => main(raw));
}

// Export for testing
module.exports = { nvObserve, main };
