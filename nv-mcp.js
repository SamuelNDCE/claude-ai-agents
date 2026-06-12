// Copyright (c) 2026 perpetualtechnologies. All rights reserved.
// Proprietary and confidential. Unauthorised copying, modification,
// or distribution is strictly prohibited.
// nv-mcp.js — NeuralVault write-side MCP server (stdio, zero npm deps).
// 2 tools: nv_log (append session entry to wiki/log.md), nv_save (create a note).
// Read/search side is handled by the qmd MCP server (vector + BM25 over the vault).
// Writes go straight to the vault filesystem — there is NO NeuralVault server.
// Unlike the old HTTP-backed tools, every failure here raises a loud MCP error.
"use strict";
const fs = require("fs");
const path = require("path");
const readline = require("readline");
const { nvObserveFs, VAULT } = require("./nv-fs.js");

const LOG_FILE = path.join(VAULT, "wiki", "log.md");

function today() {
  return new Date().toISOString().slice(0, 10);
}

// Insert a new entry right after the header block, newest at top:
//   # NeuralVault Log
//   _Newest entries at top._
//
//   ---
//   <new entry goes here>
function toolLog({ title, body }) {
  if (!title || !body) throw new Error("nv_log requires both title and body");
  const text = fs.readFileSync(LOG_FILE, "utf8");
  const sep = text.indexOf("\n---\n");
  if (sep === -1) throw new Error(`No '---' separator found in ${LOG_FILE}`);
  const insertAt = sep + "\n---\n".length;
  const entry = `\n## ${today()} — ${String(title).replace(/\n/g, " ")}\n\n${String(body).trim()}\n\n---\n`;
  fs.writeFileSync(LOG_FILE, text.slice(0, insertAt) + entry + text.slice(insertAt), "utf8");
  return { ok: true, file: "wiki/log.md", date: today(), title };
}

function toolSave({ title, content, type, tags, status, folder }) {
  if (!title || !content) throw new Error("nv_save requires both title and content");
  const res = nvObserveFs({ title, content, type, tags, status, folder });
  if (!res.ok) throw new Error("nv_save failed — invalid folder path or filesystem write error");
  return res;
}

const TOOLS = [
  {
    name: "nv_log",
    description: "Append a session entry to the NeuralVault log (wiki/log.md, newest at top). Use after completing any task or code change: what was done, why, where, anything learned. One call replaces the manual Read+Edit of log.md.",
    inputSchema: {
      type: "object",
      properties: {
        title: { type: "string", description: "Short entry title, e.g. 'Fixed physics lag in graph view'" },
        body: { type: "string", description: "Markdown body: what changed, why, file paths, gotchas" },
      },
      required: ["title", "body"],
    },
  },
  {
    name: "nv_save",
    description: "Save a note to the NeuralVault vault with frontmatter and type-based folder routing. Use for any discovered fact, decision, fix, pattern, or lesson the moment you have it. Returns the vault-relative note id.",
    inputSchema: {
      type: "object",
      properties: {
        title: { type: "string", description: "Note title (becomes the filename slug)" },
        content: { type: "string", description: "Markdown body of the note" },
        type: {
          type: "string",
          enum: ["observation", "lesson", "concept", "pattern", "source", "meta", "synthesis", "entity", "question", "note"],
          description: "Note type — routes to the matching wiki/ folder (default: observation → wiki/agent-inbox)",
        },
        tags: { type: "array", items: { type: "string" }, description: "Extra tags for the frontmatter" },
        status: { type: "string", description: "Note status (default: seed)" },
        folder: { type: "string", description: "Override target folder (vault-relative, e.g. 'wiki/Mistakes & Fixes')" },
      },
      required: ["title", "content"],
    },
  },
];

const HANDLERS = { nv_log: toolLog, nv_save: toolSave };

function send(msg) { process.stdout.write(JSON.stringify(msg) + "\n"); }
function text(s) { return { content: [{ type: "text", text: s }] }; }

const rl = readline.createInterface({ input: process.stdin, terminal: false });

rl.on("line", (line) => {
  line = line.replace(/^﻿/, "");
  if (!line.trim()) return;
  let msg;
  try { msg = JSON.parse(line); } catch { return; }

  const { id, method, params } = msg;

  if (method === "initialize") {
    send({ jsonrpc: "2.0", id, result: {
      protocolVersion: "2024-11-05",
      capabilities: { tools: {} },
      serverInfo: { name: "nv", version: "1.0.0" },
    }});
    return;
  }

  if (method === "notifications/initialized") return;

  if (method === "tools/list") {
    send({ jsonrpc: "2.0", id, result: { tools: TOOLS } });
    return;
  }

  if (method === "tools/call") {
    const handler = HANDLERS[params?.name];
    if (!handler) {
      send({ jsonrpc: "2.0", id, error: { code: -32601, message: `Unknown tool: ${params?.name}` } });
      return;
    }
    try {
      const result = handler(params.arguments || {});
      send({ jsonrpc: "2.0", id, result: text(JSON.stringify(result)) });
    } catch (err) {
      send({ jsonrpc: "2.0", id, error: { code: -32603, message: err.message } });
    }
    return;
  }

  send({ jsonrpc: "2.0", id, error: { code: -32601, message: "Method not found" } });
});
