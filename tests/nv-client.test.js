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
