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
  throw new Error(`unknown tool: ${name}`);
}

function text(s) {
  return { content: [{ type: "text", text: s }] };
}

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + "\n");
}

const rl = readline.createInterface({ input: process.stdin, terminal: false });

rl.on("line", async (line) => {
  // Strip BOM if present (from PowerShell output redirection)
  line = line.replace(/^﻿/, "");
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
    if (!params?.name) {
      send({ jsonrpc: "2.0", id, error: { code: -32602, message: "Invalid params: missing tool name" } });
      return;
    }
    try {
      const result = await callTool(params.name, params.arguments || {});
      send({ jsonrpc: "2.0", id, result });
    } catch (err) {
      send({ jsonrpc: "2.0", id, error: { code: -32603, message: err.message } });
    }
    return;
  }

  send({ jsonrpc: "2.0", id, error: { code: -32601, message: "Method not found" } });
});
