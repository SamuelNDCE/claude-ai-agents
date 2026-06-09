// tests/nv-memory-hook.test.js
"use strict";
const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");

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

  // Isolate writes to a throwaway vault so the real vault is untouched.
  const tmpVault = fs.mkdtempSync(path.join(os.tmpdir(), "nvfs-test-"));
  process.env.NV_VAULT = tmpVault;
  delete require.cache[require.resolve("../nv-fs.js")];
  delete require.cache[require.resolve("../.claude/helpers/nv-memory-hook.cjs")];
  const { nvObserve } = require("../.claude/helpers/nv-memory-hook.cjs");

  // Test 1: nvObserve writes a note to the vault filesystem
  await test("nvObserve writes a note file with title, content, type, and tags", async () => {
    const result = await nvObserve("test-key", "test-value");
    assert.strictEqual(result.ok, true);
    assert.strictEqual(result.id, "wiki/agent-inbox/test-key");

    const file = path.join(tmpVault, "wiki", "agent-inbox", "test-key.md");
    const text = fs.readFileSync(file, "utf8");
    assert.ok(text.includes("title: test-key"), "title in frontmatter");
    assert.ok(text.includes("type: observation"), "type observation");
    assert.ok(text.includes("ruflo-agent, memory-store"), "tags present");
    assert.ok(text.includes("test-value"), "content body");
  });

  // Test 2: nvObserve returns {ok:false} for oversized payloads
  await test("nvObserve returns {ok:false} when content exceeds 1MB", async () => {
    const huge = "x".repeat(1_000_001);
    const result = await nvObserve("big", huge);
    assert.strictEqual(result.ok, false);
  });

  fs.rmSync(tmpVault, { recursive: true, force: true });
  console.log(`\n${passed} passed, ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
}

run().catch((err) => { console.error(err); process.exit(1); });
