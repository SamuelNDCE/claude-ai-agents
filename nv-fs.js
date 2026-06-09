// nv-fs.js — write/search NeuralVault notes directly on the vault filesystem.
// Replaces the old HTTP API (localhost:8900) that no longer exists: NeuralVault
// is now a serverless Rust desktop app that reads these files directly.
"use strict";
const fs = require("fs");
const path = require("path");

const VAULT = process.env.NV_VAULT ||
  "C:\\Users\\Futur\\Documents\\AiWorkspace\\NeuralVault\\sample-vault";

// type → folder under the vault, matching the old /api/observe routing.
const TYPE_FOLDER = {
  observation: "wiki/agent-inbox",
  lesson: "wiki/lessons",
  concept: "wiki/concepts",
  pattern: "wiki/patterns",
  source: "wiki/sources",
  meta: "wiki/meta",
  synthesis: "wiki/synthesis",
  entity: "wiki/entities",
  question: "wiki/questions",
  note: "wiki/agent-inbox",
};

function slugify(s) {
  return String(s).toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "note";
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

// Write a note to the vault. Never throws — returns { ok, id } or { ok:false }.
// id is the vault-relative path without the .md extension.
function nvObserveFs({ title, content, type = "observation", tags = [], status = "seed", folder } = {}) {
  try {
    let rel = folder || TYPE_FOLDER[type] || TYPE_FOLDER.observation;
    // Path-traversal guard: `folder` is caller-supplied, so a value like
    // "../../x" or an absolute path would escape the vault. Only accept a
    // simple relative sub-path (safe charset, no "..", not absolute) when a
    // caller passes one; the TYPE_FOLDER fallbacks are already trusted.
    if (folder) {
      const f = String(folder).replace(/\\/g, "/");
      const bad = path.isAbsolute(f) || /(^|\/)\.\.(\/|$)/.test(f) ||
        !/^[A-Za-z0-9._/-]+$/.test(f);
      if (bad) return { ok: false };
      rel = f;
    }
    const dir = path.resolve(VAULT, rel);
    // Belt-and-suspenders: confirm the resolved dir is inside the vault root
    // (Windows path comparison is case-insensitive).
    const root = path.resolve(VAULT);
    const a = process.platform === "win32" ? dir.toLowerCase() : dir;
    const b = process.platform === "win32" ? root.toLowerCase() : root;
    if (a !== b && !a.startsWith(b + path.sep)) return { ok: false };
    fs.mkdirSync(dir, { recursive: true });

    const slug = slugify(title);
    const file = path.join(dir, slug + ".md");
    const tagList = (Array.isArray(tags) ? tags : []).concat("wiki/agent");
    const safeTitle = String(title || "untitled").replace(/\n/g, " ");

    const doc = [
      "---",
      `title: ${safeTitle}`,
      `type: ${type}`,
      `status: ${status}`,
      "source: agent-api",
      `created: ${today()}`,
      `updated: ${today()}`,
      `tags: [${tagList.join(", ")}]`,
      "---",
      "",
      `# ${safeTitle}`,
      "",
      content || "",
      "",
    ].join("\n");

    fs.writeFileSync(file, doc, "utf8");
    return { ok: true, id: `${rel}/${slug}` };
  } catch {
    return { ok: false };
  }
}

// Lightweight AND-of-terms search across vault markdown, returning the old API
// shape { results: [{ title, excerpt, id }] } for dedup and cache lookups.
function nvSearchFs(q, limit = 40) {
  const results = [];
  const terms = String(q || "").toLowerCase().split(/\s+/).filter(Boolean);
  if (!terms.length) return { results };

  const stack = [path.join(VAULT, "wiki")];
  while (stack.length && results.length < limit) {
    let entries;
    const cur = stack.pop();
    try { entries = fs.readdirSync(cur, { withFileTypes: true }); } catch { continue; }
    for (const e of entries) {
      if (results.length >= limit) break;
      const full = path.join(cur, e.name);
      if (e.isDirectory()) { stack.push(full); continue; }
      if (!e.name.endsWith(".md")) continue;
      let text;
      try { text = fs.readFileSync(full, "utf8"); } catch { continue; }
      const low = text.toLowerCase();
      if (!terms.every((t) => low.includes(t))) continue;
      const titleM = text.match(/^title:\s*(.+)$/m);
      const title = titleM ? titleM[1].trim() : e.name.replace(/\.md$/, "");
      const idx = low.indexOf(terms[0]);
      const excerpt = text.slice(Math.max(0, idx - 40), idx + 120).replace(/\s+/g, " ").trim();
      results.push({ title, excerpt, id: path.relative(VAULT, full).replace(/\\/g, "/").replace(/\.md$/, "") });
    }
  }
  return { results };
}

module.exports = { nvObserveFs, nvSearchFs, VAULT };
