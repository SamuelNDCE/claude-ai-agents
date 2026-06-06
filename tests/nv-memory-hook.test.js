// tests/nv-memory-hook.test.js
"use strict";
const assert = require("assert");
const http = require("http");

let server;
let lastRequest = null;

async function startMockServer(statusCode = 200) {
  return new Promise((resolve) => {
    server = http.createServer((req, res) => {
      let body = "";
      req.on("data", (c) => (body += c));
      req.on("end", () => {
        lastRequest = { method: req.method, url: req.url, body };
        res.writeHead(statusCode, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ ok: statusCode === 200 }));
      });
    });
    server.listen(0, () => resolve(server.address().port));
  });
}

async function stopMockServer() {
  return new Promise((resolve) => server.close(resolve));
}

async function run() {
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

  // Test 1: nvObserve POSTs correct body
  {
    const port = await startMockServer();
    process.env.NV_HOST = "localhost";
    process.env.NV_PORT = String(port);
    delete require.cache[require.resolve("../.claude/helpers/nv-memory-hook.cjs")];
    const { nvObserve } = require("../.claude/helpers/nv-memory-hook.cjs");

    await test("nvObserve POSTs to /api/observe with title and content", async () => {
      const result = await nvObserve("test-key", "test-value");
      assert.strictEqual(lastRequest.method, "POST");
      assert.strictEqual(lastRequest.url, "/api/observe");
      const body = JSON.parse(lastRequest.body);
      assert.strictEqual(body.title, "test-key");
      assert.strictEqual(body.content, "test-value");
      assert.strictEqual(body.type, "observation");
      assert.deepStrictEqual(body.tags, ["ruflo-agent", "memory-store"]);
      assert.strictEqual(result.ok, true);
    });

    await stopMockServer();
  }

  // Test 2: nvObserve returns {ok:false} when NV unreachable
  {
    process.env.NV_PORT = "1";
    delete require.cache[require.resolve("../.claude/helpers/nv-memory-hook.cjs")];
    const { nvObserve: nvObs2 } = require("../.claude/helpers/nv-memory-hook.cjs");

    await test("nvObserve returns {ok:false} when NV is unreachable", async () => {
      const result = await nvObs2("key", "value");
      assert.strictEqual(result.ok, false);
    });
  }

  console.log(`\n${passed} passed, ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
}

run().catch((err) => { console.error(err); process.exit(1); });
