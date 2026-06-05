// browser-agent.ts — Claude Agent SDK + Opera DevTools MCP
//
// A starter autonomous browser agent. It drives the browser through the
// `opera-devtools-mcp` server and is instructed to READ pages via the
// accessibility tree (structured text) rather than spamming screenshots.
//
// Run:
//   1. Put your key in .env:  ANTHROPIC_API_KEY=sk-ant-...
//   2. npx tsx browser-agent.ts "your task here"
//      (or with no arg it runs the default demo task below)
//
// Requires: @anthropic-ai/claude-agent-sdk (installed), npx available.

import { query } from "@anthropic-ai/claude-agent-sdk";

const task =
  process.argv.slice(2).join(" ") ||
  "List my open browser tabs. Then read the ACTIVE tab using the accessibility " +
    "tree and give me a 3-bullet summary of what's on it. Do not take screenshots " +
    "unless reading the text fails.";

const SYSTEM_PROMPT = [
  "You are a browser automation agent driving Opera via the opera-devtools-mcp tools.",
  "EFFICIENCY RULES:",
  "- ALWAYS read page content with the accessibility-tree / snapshot tool, never screenshots, for understanding text and structure.",
  "- Only use the screenshot tool when the task explicitly needs pixels (visual layout, images, canvas) AND text reading is insufficient.",
  "- Act on elements by their reference/id from the snapshot; re-snapshot only after the page changes.",
  "- Be decisive: plan, then take the fewest tool calls that accomplish the task.",
].join("\n");

async function main() {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error("ANTHROPIC_API_KEY is not set. Add it to .env (see .env.example).");
  }

  for await (const message of query({
    prompt: task,
    options: {
      model: "claude-sonnet-4-6", // verified current latest Sonnet
      systemPrompt: SYSTEM_PROMPT,
      maxTurns: 15,
      mcpServers: {
        // Standalone Opera DevTools MCP server (npm: opera-devtools-mcp).
        // npx fetches/runs it; the agent gets its browser tools as
        // mcp__opera__<tool>. If it needs a browser executable path, set the
        // server's documented env var here (see the package README).
        opera: {
          command: "npx",
          args: ["-y", "opera-devtools-mcp@latest"],
          // env: { /* e.g. an executable-path var pointing at Opera GX */ },
        },
      },
      // allowedTools omitted → all opera tools allowed. To lock it down, list
      // e.g. ["mcp__opera__snapshot", "mcp__opera__go-to-page", "mcp__opera__click"].
      //
      // Safe by default: 'default' mode gates tool use behind approval. Only opt
      // into bypass deliberately, e.g. AGENT_YOLO=1 npx tsx browser-agent.ts ...
      // (bypass lets the agent act on your live, signed-in browser with no prompt).
      permissionMode: process.env.AGENT_YOLO === "1" ? "bypassPermissions" : "default",
      ...(process.env.AGENT_YOLO === "1" ? { allowDangerouslySkipPermissions: true } : {}),
    },
  })) {
    if (message.type === "assistant") {
      for (const block of message.message.content) {
        if (block.type === "text") process.stdout.write(block.text);
      }
    } else if (message.type === "result" && message.subtype === "success") {
      console.log("\n\n--- RESULT ---\n" + message.result);
    }
  }
}

main().catch((e) => {
  console.error("Agent failed:", e.message);
  process.exit(1);
});
