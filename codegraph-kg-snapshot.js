#!/usr/bin/env node
/**
 * codegraph-kg-snapshot
 * Dumps the codegraph index for a project to NeuralVault as a structured
 * knowledge graph note. Run after `codegraph init -i` or `codegraph index`.
 *
 * Usage:
 *   node codegraph-kg-snapshot.js [project-path]
 *   node codegraph-kg-snapshot.js C:\Users\Futur\Documents\AiWorkspace\NeuralVault
 */

"use strict";

const { execSync } = require("child_process");
const fs = require("fs");
const http = require("http");
const path = require("path");

const VAULT_ROOT = "C:\\Users\\Futur\\Documents\\Obsidian Vault\\Claude";

const NV_HOST = "localhost";
const NV_PORT = 8900;

const projectPath = process.argv[2] || process.cwd();
const projectName = path.basename(projectPath);

function run(cmd, cwd) {
  try {
    return execSync(cmd, { cwd, encoding: "utf8", timeout: 30000 });
  } catch {
    return "";
  }
}

function nvPost(endpoint, body) {
  return new Promise((resolve) => {
    const data = JSON.stringify(body);
    const req = http.request(
      { host: NV_HOST, port: NV_PORT, path: endpoint, method: "POST",
        headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(data) } },
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

async function snapshot() {
  console.log(`[kg-snapshot] Snapshotting ${projectName} → NeuralVault`);

  const status = run("codegraph status --json", projectPath);
  const filesRaw = run("codegraph files --json", projectPath);
  const queryFunctions = run('codegraph query "" --kind function --limit 80 --json', projectPath);
  const queryClasses = run('codegraph query "" --kind class --limit 40 --json', projectPath);
  const queryInterfaces = run('codegraph query "" --kind interface --limit 40 --json', projectPath);

  let stats = {};
  try { stats = JSON.parse(status); } catch {}

  let files = [];
  try { files = JSON.parse(filesRaw); } catch {}

  let functions = [];
  try { functions = JSON.parse(queryFunctions); } catch {}

  let classes = [];
  try { classes = JSON.parse(queryClasses); } catch {}

  let interfaces = [];
  try { interfaces = JSON.parse(queryInterfaces); } catch {}

  // Build knowledge graph note
  const fileList = Array.isArray(files)
    ? files.slice(0, 50).map((f) => `- \`${f.path || f}\``).join("\n")
    : "";

  const funcList = Array.isArray(functions)
    ? functions.slice(0, 60).map((s) => {
        const n = s.node || s;
        return `- \`${n.name}\` (${n.filePath || ""}:${n.startLine || ""})`;
      }).join("\n")
    : "";

  const classList = Array.isArray(classes)
    ? classes.slice(0, 30).map((s) => {
        const n = s.node || s;
        return `- \`${n.name}\` (${n.filePath || ""})`;
      }).join("\n")
    : "";

  const ifaceList = Array.isArray(interfaces)
    ? interfaces.slice(0, 30).map((s) => {
        const n = s.node || s;
        return `- \`${n.name}\` (${n.filePath || ""})`;
      }).join("\n")
    : "";

  const content = [
    `# CodeGraph Knowledge Graph — ${projectName}`,
    "",
    `**Project:** \`${projectPath}\`  `,
    `**Nodes:** ${stats.nodeCount || "?"}  |  **Edges:** ${stats.edgeCount || "?"}  |  **Files:** ${stats.fileCount || "?"}`,
    "",
    "## Files",
    "",
    fileList || "_No files indexed_",
    "",
    "## Functions",
    "",
    funcList || "_None_",
    "",
    "## Classes",
    "",
    classList || "_None_",
    "",
    "## Interfaces / Types",
    "",
    ifaceList || "_None_",
    "",
    "---",
    `*Snapshot by codegraph-kg-snapshot · [[codegraph-knowledge-graph]]*`,
  ].join("\n");

  const title = `codegraph-kg-${projectName.toLowerCase().replace(/[^a-z0-9]/g, "-")}`;
  const noteId = `wiki/codegraph/${title}`;
  const relPath = `${noteId}.md`;

  // Build full frontmatter + content for the file
  const today = new Date().toISOString().slice(0, 10);
  const fileContent = [
    "---",
    `title: ${title}`,
    "type: concept",
    "status: seed",
    `created: ${today}`,
    `updated: ${today}`,
    `tags: [codegraph-kg, architecture, ${projectName}]`,
    "---",
    "",
    content,
  ].join("\n");

  // Write directly to vault for true replacement (API POST appends)
  const vaultPath = path.join(VAULT_ROOT, relPath);
  try {
    fs.mkdirSync(path.dirname(vaultPath), { recursive: true });
    fs.writeFileSync(vaultPath, fileContent, "utf8");
    console.log(`[kg-snapshot] Saved → ${relPath}`);
  } catch (err) {
    console.warn(`[kg-snapshot] Direct write failed (${err.message}), falling back to API`);
    const result = await nvPost("/api/note", { id: noteId, title, content, type: "concept", folder: "wiki/codegraph", tags: ["codegraph-kg", "architecture", projectName] });
    if (result.ok) console.log(`[kg-snapshot] Saved via API → ${result.file}`);
    else console.error("[kg-snapshot] Failed to save to NeuralVault:", result);
  }
}

snapshot().catch(console.error);
