import type { NoteGraph, GraphNode, GraphEdge } from './types';
import type { VaultStorage } from './vault';

export function buildGraph(vault: VaultStorage): NoteGraph {
  const notes = vault.getAllNotes();
  const edgeSet = new Set<string>();
  const edges: GraphEdge[] = [];

  // Every note becomes a node (degree filled in after edge pass)
  const nodeMap = new Map<string, GraphNode>();
  for (const note of notes) {
    nodeMap.set(note.id, { id: note.id, title: note.title, tags: note.tags, degree: 0 });
  }

  function addEdge(source: string, target: string, type: GraphEdge['type']): void {
    const key = `${type}:${[source, target].sort().join('|')}`;
    if (!edgeSet.has(key)) {
      edgeSet.add(key);
      edges.push({ source, target, type });
    }
  }

  // Wikilink edges
  for (const note of notes) {
    for (const link of note.links) {
      const target = vault.getNoteByTitle(link.target);
      if (target && target.id !== note.id) {
        addEdge(note.id, target.id, 'wikilink');
      }
    }
  }

  // Shared-tag edges (only between notes that share at least one tag)
  const tagIndex = new Map<string, string[]>(); // tag → [noteId]
  for (const note of notes) {
    for (const tag of note.tags) {
      const list = tagIndex.get(tag) ?? [];
      list.push(note.id);
      tagIndex.set(tag, list);
    }
  }
  for (const ids of tagIndex.values()) {
    if (ids.length < 2) continue;
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        addEdge(ids[i], ids[j], 'shared-tag');
      }
    }
  }

  // Compute degree per node
  for (const edge of edges) {
    const s = nodeMap.get(edge.source);
    const t = nodeMap.get(edge.target);
    if (s) s.degree++;
    if (t) t.degree++;
  }

  return { nodes: Array.from(nodeMap.values()), edges };
}
