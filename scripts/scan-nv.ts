import { VaultStorage, buildGraph } from '../src/storage';

const VAULT = 'C:\\Users\\Futur\\Documents\\AiWorkspace\\NeuralVault\\NV-Obsidian-Vault\\Neural-Vault\\Nv';

async function main(): Promise<void> {
  const vault = new VaultStorage(VAULT);
  await vault.scan();

  const notes = vault.getAllNotes();
  const graph = buildGraph(vault);

  console.log(`Notes scanned:  ${notes.length}`);
  console.log(`Graph nodes:    ${graph.nodes.length}`);
  console.log(`Graph edges:    ${graph.edges.length}`);
  console.log(`  wikilinks:    ${graph.edges.filter(e => e.type === 'wikilink').length}`);
  console.log(`  shared-tag:   ${graph.edges.filter(e => e.type === 'shared-tag').length}`);

  // Top 5 most-connected nodes
  const top = graph.nodes.sort((a, b) => b.degree - a.degree).slice(0, 5);
  console.log('\nTop 5 most-connected notes:');
  top.forEach(n => console.log(`  ${n.degree} edges — ${n.title}`));

  // Sample a concept note to confirm wikilinks were parsed
  const concept = notes.find(n => n.frontmatter['type'] === 'concept');
  if (concept) {
    console.log(`\nSample concept: "${concept.title}"`);
    console.log(`  tags:   ${concept.tags.join(', ')}`);
    console.log(`  links:  ${concept.links.map(l => l.target).join(', ')}`);
  }
}

main().catch(err => { console.error('ERROR:', err.message); process.exit(1); });
