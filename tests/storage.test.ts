import * as assert from 'assert';
import * as path from 'path';
import { VaultStorage, buildGraph, parseNote } from '../src/storage';

const FIXTURES = path.join(__dirname, 'fixtures');

async function run(): Promise<void> {
  let passed = 0;
  let failed = 0;

  async function test(name: string, fn: () => void | Promise<void>): Promise<void> {
    try {
      await fn();
      console.log(`  PASS: ${name}`);
      passed++;
    } catch (err) {
      console.log(`  FAIL: ${name} — ${(err as Error).message}`);
      failed++;
    }
  }

  // --- parseNote ---
  await test('parseNote: reads title from frontmatter', () => {
    const note = parseNote(path.join(FIXTURES, 'concepts', 'second-brain.md'), FIXTURES);
    assert.strictEqual(note.title, 'Second Brain Architecture');
  });

  await test('parseNote: reads tags from frontmatter', () => {
    const note = parseNote(path.join(FIXTURES, 'concepts', 'second-brain.md'), FIXTURES);
    assert.ok(note.tags.includes('second-brain'), 'missing frontmatter tag');
    assert.ok(note.tags.includes('ai'), 'missing inline #tag');
  });

  await test('parseNote: extracts wikilinks from body', () => {
    const note = parseNote(path.join(FIXTURES, 'concepts', 'second-brain.md'), FIXTURES);
    const targets = note.links.map((l) => l.target);
    assert.ok(targets.includes('Knowledge Graph Viz'), 'missing [[Knowledge Graph Viz]] link');
    assert.ok(targets.includes('RAG Lesson'), 'missing [[RAG Lesson]] link');
  });

  await test('parseNote: id is vault-relative path with forward slashes', () => {
    const note = parseNote(path.join(FIXTURES, 'lessons', 'rag-lesson.md'), FIXTURES);
    assert.strictEqual(note.id, 'lessons/rag-lesson.md');
  });

  await test('parseNote: parses created date', () => {
    const note = parseNote(path.join(FIXTURES, 'concepts', 'second-brain.md'), FIXTURES);
    assert.ok(note.created instanceof Date);
    assert.strictEqual(note.created!.getFullYear(), 2026);
  });

  // --- VaultStorage ---
  await test('VaultStorage: scan finds all fixture notes', async () => {
    const vault = new VaultStorage(FIXTURES);
    await vault.scan();
    const notes = vault.getAllNotes();
    assert.strictEqual(notes.length, 3);
  });

  await test('VaultStorage: getNoteByTitle is case-insensitive', async () => {
    const vault = new VaultStorage(FIXTURES);
    await vault.scan();
    const note = vault.getNoteByTitle('second brain architecture');
    assert.ok(note, 'note not found by lowercase title');
    assert.strictEqual(note!.title, 'Second Brain Architecture');
  });

  await test('VaultStorage: getNote returns note by id', async () => {
    const vault = new VaultStorage(FIXTURES);
    await vault.scan();
    const note = vault.getNote('concepts/second-brain.md');
    assert.ok(note);
  });

  // --- buildGraph ---
  await test('buildGraph: node count matches note count', async () => {
    const vault = new VaultStorage(FIXTURES);
    await vault.scan();
    const graph = buildGraph(vault);
    assert.strictEqual(graph.nodes.length, 3);
  });

  await test('buildGraph: wikilink between second-brain and knowledge-graph-viz', async () => {
    const vault = new VaultStorage(FIXTURES);
    await vault.scan();
    const graph = buildGraph(vault);
    const wikilinkEdges = graph.edges.filter((e) => e.type === 'wikilink');
    const hasEdge = wikilinkEdges.some(
      (e) =>
        (e.source.includes('second-brain') && e.target.includes('knowledge-graph')) ||
        (e.target.includes('second-brain') && e.source.includes('knowledge-graph'))
    );
    assert.ok(hasEdge, `expected wikilink edge between second-brain and knowledge-graph-viz. Edges: ${JSON.stringify(wikilinkEdges)}`);
  });

  await test('buildGraph: shared-tag edge between notes sharing "rag" tag', async () => {
    const vault = new VaultStorage(FIXTURES);
    await vault.scan();
    const graph = buildGraph(vault);
    const tagEdges = graph.edges.filter((e) => e.type === 'shared-tag');
    // second-brain has tag "rag", rag-lesson has tag "rag" — should share an edge
    const hasEdge = tagEdges.some(
      (e) =>
        (e.source.includes('second-brain') && e.target.includes('rag-lesson')) ||
        (e.target.includes('second-brain') && e.source.includes('rag-lesson'))
    );
    assert.ok(hasEdge, `expected shared-tag edge for "rag". Tag edges: ${JSON.stringify(tagEdges)}`);
  });

  await test('buildGraph: degree is computed correctly', async () => {
    const vault = new VaultStorage(FIXTURES);
    await vault.scan();
    const graph = buildGraph(vault);
    const sbNode = graph.nodes.find((n) => n.id.includes('second-brain'));
    assert.ok(sbNode);
    assert.ok(sbNode!.degree > 0, 'second-brain should have at least one edge');
  });

  await test('buildGraph: wikilink edges are deduplicated (bidirectional links = 1 edge)', async () => {
    const vault = new VaultStorage(FIXTURES);
    await vault.scan();
    const graph = buildGraph(vault);
    // Both notes link to each other — wikilink dedup should yield exactly 1 wikilink edge
    const wikilinksBetween = graph.edges.filter(
      (e) =>
        e.type === 'wikilink' &&
        ((e.source.includes('second-brain') && e.target.includes('knowledge-graph')) ||
          (e.target.includes('second-brain') && e.source.includes('knowledge-graph')))
    );
    assert.strictEqual(wikilinksBetween.length, 1, `expected 1 wikilink edge, got ${wikilinksBetween.length}`);
  });

  console.log(`\n${passed} passed, ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
