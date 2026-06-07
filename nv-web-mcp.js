// nv-web-mcp.js — NeuralVault Web Intelligence MCP server
// 5 tools: web_search, web_read, web_extract, web_live, web_research
// Zero npm deps. All results auto-save to NeuralVault.
"use strict";
const readline = require("readline");
const https = require("https");
const http = require("http");
const { URL } = require("url");
const { nvPost } = require("./nv-client.js");

const MAX_REDIRECTS = 5;
const DEFAULT_MAX_CHARS = 4000;
const FETCH_TIMEOUT_MS = 15000;
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

// ─── Fetch ────────────────────────────────────────────────────────────────────

function fetchUrl(urlStr, hopsLeft = MAX_REDIRECTS) {
  return new Promise((resolve, reject) => {
    let parsed;
    try { parsed = new URL(urlStr); } catch { return reject(new Error(`Invalid URL: ${urlStr}`)); }
    const lib = parsed.protocol === "https:" ? https : http;
    const req = lib.request({
      hostname: parsed.hostname,
      port: parsed.port || (parsed.protocol === "https:" ? 443 : 80),
      path: parsed.pathname + parsed.search,
      method: "GET",
      headers: {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "identity",
        "Connection": "close",
      },
    }, (res) => {
      clearTimeout(timer);
      if ([301, 302, 303, 307, 308].includes(res.statusCode)) {
        const loc = res.headers.location;
        if (!loc || hopsLeft <= 0) return reject(new Error("Too many redirects"));
        const next = loc.startsWith("http") ? loc : new URL(loc, urlStr).toString();
        return resolve(fetchUrl(next, hopsLeft - 1));
      }
      res.setEncoding("utf8");
      let buf = "";
      res.on("data", (c) => { buf += c; });
      res.on("end", () => resolve({
        statusCode: res.statusCode,
        body: buf,
        finalUrl: urlStr,
        contentType: res.headers["content-type"] || "",
      }));
      res.on("error", (e) => reject(e));
    });
    const timer = setTimeout(() => { req.destroy(); reject(new Error("Request timed out")); }, FETCH_TIMEOUT_MS);
    req.on("error", (e) => { clearTimeout(timer); reject(e); });
    req.end();
  });
}

// ─── HTML helpers ─────────────────────────────────────────────────────────────

function decodeEntities(s) {
  return s
    .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&apos;/g, "'")
    .replace(/&nbsp;/g, " ").replace(/&#(\d+);/g, (_, n) => String.fromCharCode(+n))
    .replace(/&[a-z]{2,8};/g, " ");
}

function extractTitle(html) {
  const m = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  return m ? decodeEntities(m[1].replace(/<[^>]+>/g, "")).trim() : "";
}

function stripHtml(html) {
  html = html
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<nav[\s\S]*?<\/nav>/gi, " ")
    .replace(/<header[\s\S]*?<\/header>/gi, " ")
    .replace(/<footer[\s\S]*?<\/footer>/gi, " ")
    .replace(/<aside[\s\S]*?<\/aside>/gi, " ")
    .replace(/<form[\s\S]*?<\/form>/gi, " ")
    .replace(/<[^>]+>/g, " ");
  return decodeEntities(html).replace(/[ \t]+/g, " ").replace(/\n[ \t]+/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
}

function truncate(text, maxChars) {
  if (text.length <= maxChars) return { text, truncated: false };
  const cut = text.lastIndexOf(" ", maxChars);
  return { text: text.slice(0, cut > 0 ? cut : maxChars), truncated: true };
}

// ─── Tools ────────────────────────────────────────────────────────────────────

async function toolSearch({ query, num_results = 10 }) {
  if (!query) throw new Error("query is required");
  const url = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}&kl=us-en`;
  let body;
  try {
    const r = await fetchUrl(url);
    body = r.body;
  } catch (e) {
    return { query, results: [], error: e.message };
  }

  // Extract title+link pairs
  const tlRe = /<a[^>]+class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi;
  const titleLinks = [];
  let tlm;
  while ((tlm = tlRe.exec(body)) !== null) {
    let href = tlm[1];
    const title = decodeEntities(tlm[2].replace(/<[^>]+>/g, "")).trim();
    const uddg = href.match(/uddg=([^&"]+)/);
    if (uddg) href = decodeURIComponent(uddg[1]);
    else if (href.startsWith("//")) href = "https:" + href;
    if (title && href.startsWith("http")) titleLinks.push({ title, url: href });
  }

  // Extract snippets
  const snipRe = /<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>([\s\S]*?)<\/a>/gi;
  const snippets = [];
  let sm;
  while ((sm = snipRe.exec(body)) !== null) {
    snippets.push(decodeEntities(sm[1].replace(/<[^>]+>/g, "")).trim());
  }

  const results = titleLinks.slice(0, num_results).map((tl, i) => ({
    ...tl,
    snippet: snippets[i] || "",
  }));

  const top5 = results.slice(0, 5).map(r => `- [${r.title}](${r.url})`).join("\n");
  nvPost("/api/observe", {
    title: `Web search: ${query}`,
    content: `Query: **${query}**\n\nTop results:\n${top5}`,
  }).catch(() => {});

  return { query, results };
}

async function toolRead({ url, max_chars = DEFAULT_MAX_CHARS }) {
  if (!url) throw new Error("url is required");
  let resp;
  try { resp = await fetchUrl(url); } catch (e) { return { error: e.message, url }; }

  const title = extractTitle(resp.body);
  const raw = stripHtml(resp.body);
  const { text: content, truncated } = truncate(raw, max_chars);
  const word_count = content.split(/\s+/).filter(Boolean).length;

  const saved = await nvPost("/api/note", {
    title: title || resp.finalUrl,
    content: `Source: ${resp.finalUrl}\n\n${content}`,
    type: "source",
    tags: ["web", "web-read"],
  }).catch(() => null);

  return {
    title,
    url: resp.finalUrl,
    content,
    word_count,
    truncated,
    nv_id: saved?.id || null,
  };
}

async function toolExtract({ url, modes = ["meta"] }) {
  if (!url) throw new Error("url is required");
  let resp;
  try { resp = await fetchUrl(url); } catch (e) { return { error: e.message, url }; }

  const html = resp.body;
  const extracted = {};

  if (modes.includes("meta")) {
    const meta = {};
    const t = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
    if (t) meta.title = decodeEntities(t[1].replace(/<[^>]+>/g, "")).trim();
    // Match <meta name="..." content="..."> and <meta property="..." content="..."> in either attribute order
    const metaRe = /<meta\s+(?=[^>]*(name|property)="([^"]+)")(?=[^>]*content="([^"]+)")[^>]*>/gi;
    let mm;
    while ((mm = metaRe.exec(html)) !== null) {
      const key = mm[2].toLowerCase().replace(/[:.]/g, "_");
      meta[key] = decodeEntities(mm[3]);
    }
    extracted.meta = meta;
  }

  if (modes.includes("links")) {
    const linkRe = /<a\s+[^>]*href="([^"#][^"]*)"[^>]*>([\s\S]*?)<\/a>/gi;
    const seen = new Set();
    const links = [];
    let lm;
    const base = new URL(url);
    while ((lm = linkRe.exec(html)) !== null && links.length < 100) {
      let href = lm[1].trim();
      const linkText = decodeEntities(lm[2].replace(/<[^>]+>/g, "")).trim();
      try { href = new URL(href, base).toString(); } catch { continue; }
      if (!seen.has(href) && href.startsWith("http")) {
        seen.add(href);
        links.push({ text: linkText, url: href });
      }
    }
    extracted.links = links;
  }

  if (modes.includes("headings")) {
    const headRe = /<(h[1-6])[^>]*>([\s\S]*?)<\/\1>/gi;
    const headings = [];
    let hm;
    while ((hm = headRe.exec(html)) !== null) {
      headings.push({ level: +hm[1][1], text: decodeEntities(hm[2].replace(/<[^>]+>/g, "")).trim() });
    }
    extracted.headings = headings;
  }

  if (modes.includes("tables")) {
    const tableRe = /<table[\s\S]*?<\/table>/gi;
    const tables = [];
    let tm;
    while ((tm = tableRe.exec(html)) !== null && tables.length < 3) {
      const rows = [];
      const rowRe = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
      let rm;
      while ((rm = rowRe.exec(tm[0])) !== null) {
        const cells = [];
        const cellRe = /<t[dh][^>]*>([\s\S]*?)<\/t[dh]>/gi;
        let cm;
        while ((cm = cellRe.exec(rm[1])) !== null) {
          cells.push(decodeEntities(cm[1].replace(/<[^>]+>/g, "")).trim());
        }
        if (cells.length) rows.push(cells);
      }
      if (rows.length) tables.push(rows);
    }
    extracted.tables = tables;
  }

  if (modes.includes("jsonld")) {
    const jldRe = /<script[^>]+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi;
    const schemas = [];
    let jm;
    while ((jm = jldRe.exec(html)) !== null) {
      try { schemas.push(JSON.parse(jm[1])); } catch { }
    }
    extracted.jsonld = schemas;
  }

  return { url: resp.finalUrl, extracted };
}

async function toolLive({ url }) {
  if (!url) throw new Error("url is required");
  let resp;
  try { resp = await fetchUrl(url); } catch (e) { return { error: e.message, url }; }

  const isXml = resp.contentType.includes("xml")
    || resp.body.trimStart().startsWith("<?xml")
    || resp.body.trimStart().startsWith("<rss")
    || resp.body.trimStart().startsWith("<feed");

  if (isXml) {
    const ftm = resp.body.match(/<(?:channel|feed)[^>]*>[\s\S]*?<title[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/i);
    const feed_title = ftm ? decodeEntities(ftm[1].replace(/<[^>]+>/g, "")).trim() : url;

    const itemRe = /<(?:item|entry)[^>]*>([\s\S]*?)<\/(?:item|entry)>/gi;
    const items = [];
    let im;
    while ((im = itemRe.exec(resp.body)) !== null && items.length < 20) {
      const blk = im[1];
      const getTag = (tag) => {
        const m = blk.match(new RegExp(`<${tag}[^>]*>(?:<!\\[CDATA\\[)?([\\s\\S]*?)(?:\\]\\]>)?<\\/${tag}>`, "i"));
        return m ? decodeEntities(m[1].replace(/<[^>]+>/g, "")).trim() : "";
      };
      const linkAttr = blk.match(/<link[^>]+href="([^"]+)"/i)?.[1] || "";
      const linkText = getTag("link");
      items.push({
        title: getTag("title"),
        link: linkAttr || linkText,
        pubDate: getTag("pubDate") || getTag("published") || getTag("updated"),
        summary: (getTag("description") || getTag("summary")).slice(0, 300),
      });
    }

    const top5 = items.slice(0, 5).map(i => `- ${i.title}`).join("\n");
    nvPost("/api/observe", {
      title: `Feed: ${feed_title}`,
      content: `Feed: ${url}\nItems fetched: ${items.length}\n\n${top5}`,
    }).catch(() => {});

    return { type: "rss", feed_title, items };
  }

  // JSON
  let data;
  try { data = JSON.parse(resp.body); } catch {
    return { type: "unknown", raw: resp.body.slice(0, 500) };
  }
  nvPost("/api/observe", {
    title: `JSON feed: ${url}`,
    content: `URL: ${url}\n\n\`\`\`json\n${JSON.stringify(data).slice(0, 600)}\n\`\`\``,
  }).catch(() => {});
  return { type: "json", data };
}

async function toolResearch({ query, max_pages = 3 }) {
  if (!query) throw new Error("query is required");

  const searchResult = await toolSearch({ query, num_results: 10 });
  const urls = (searchResult.results || []).slice(0, max_pages).map(r => r.url);
  if (!urls.length) return { query, pages_read: 0, sources: [], summary_nv_id: null };

  const pages = await Promise.all(
    urls.map(u => toolRead({ url: u }).catch(e => ({ error: e.message, url: u })))
  );

  const sources = pages.map((p, i) => ({
    title: p.title || urls[i],
    url: p.url || urls[i],
    nv_id: p.nv_id || null,
    word_count: p.word_count || 0,
    error: p.error || null,
  }));

  const sourceList = sources.map(s =>
    `- [${s.title}](${s.url})${s.nv_id ? ` → NV \`${s.nv_id}\`` : s.error ? ` (error: ${s.error})` : ""}`
  ).join("\n");

  const saved = await nvPost("/api/observe", {
    title: `Research: ${query}`,
    content: `Research query: **${query}**\nPages read: ${pages.length}\n\nSources:\n${sourceList}`,
  }).catch(() => null);

  return {
    query,
    pages_read: pages.length,
    sources,
    summary_nv_id: saved?.id || null,
  };
}

// ─── MCP protocol ─────────────────────────────────────────────────────────────

const TOOLS = [
  {
    name: "web_search",
    description: "Search the web via DuckDuckGo. Returns titles, URLs, and snippets. Auto-saves top results as a NeuralVault observation. Low token cost.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Search query" },
        num_results: { type: "number", description: "Max results to return (default 10, max 20)", default: 10 },
      },
      required: ["query"],
    },
  },
  {
    name: "web_read",
    description: "Fetch a URL and extract its main text content (scripts/nav/ads stripped). Token-efficient: capped at max_chars. Auto-saves to NeuralVault as a source note and returns nv_id.",
    inputSchema: {
      type: "object",
      properties: {
        url: { type: "string", description: "URL to fetch" },
        max_chars: { type: "number", description: "Max characters of content to return (default 4000)", default: 4000 },
      },
      required: ["url"],
    },
  },
  {
    name: "web_extract",
    description: "Extract specific structured data from a URL without returning full page text. Very low token cost. Use instead of web_read when you only need metadata, links, headings, tables, or JSON-LD schemas.",
    inputSchema: {
      type: "object",
      properties: {
        url: { type: "string", description: "URL to fetch" },
        modes: {
          type: "array",
          items: { type: "string", enum: ["meta", "links", "headings", "tables", "jsonld"] },
          description: "What to extract: meta (title/og/description), links (all hrefs), headings (h1-h6), tables (up to 3), jsonld (structured schemas)",
          default: ["meta"],
        },
      },
      required: ["url"],
    },
  },
  {
    name: "web_live",
    description: "Fetch live data from an RSS/Atom feed or JSON API endpoint. Returns up to 20 feed items or raw JSON. Auto-saves a headline summary to NeuralVault.",
    inputSchema: {
      type: "object",
      properties: {
        url: { type: "string", description: "RSS/Atom feed URL or JSON API endpoint" },
      },
      required: ["url"],
    },
  },
  {
    name: "web_research",
    description: "One-shot research: searches the web, reads the top N pages, and saves everything to NeuralVault as source notes plus a summary observation. Returns all nv_ids. Use for deep research tasks.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Research query" },
        max_pages: { type: "number", description: "Number of pages to read (default 3, max 5)", default: 3 },
      },
      required: ["query"],
    },
  },
];

const HANDLERS = {
  web_search: toolSearch,
  web_read: toolRead,
  web_extract: toolExtract,
  web_live: toolLive,
  web_research: toolResearch,
};

function send(msg) { process.stdout.write(JSON.stringify(msg) + "\n"); }
function text(s) { return { content: [{ type: "text", text: s }] }; }

const rl = readline.createInterface({ input: process.stdin, terminal: false });

rl.on("line", async (line) => {
  line = line.replace(/^﻿/, "");
  if (!line.trim()) return;
  let msg;
  try { msg = JSON.parse(line); } catch { return; }

  const { id, method, params } = msg;

  if (method === "initialize") {
    send({ jsonrpc: "2.0", id, result: {
      protocolVersion: "2024-11-05",
      capabilities: { tools: {} },
      serverInfo: { name: "nv-web", version: "1.0.0" },
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
      send({ jsonrpc: "2.0", id, error: { code: -32602, message: "Missing tool name" } });
      return;
    }
    const handler = HANDLERS[params.name];
    if (!handler) {
      send({ jsonrpc: "2.0", id, error: { code: -32601, message: `Unknown tool: ${params.name}` } });
      return;
    }
    try {
      const result = await handler(params.arguments || {});
      send({ jsonrpc: "2.0", id, result: text(JSON.stringify(result)) });
    } catch (err) {
      send({ jsonrpc: "2.0", id, error: { code: -32603, message: err.message } });
    }
    return;
  }

  send({ jsonrpc: "2.0", id, error: { code: -32601, message: "Method not found" } });
});
