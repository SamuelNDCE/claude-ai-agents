export interface WikiLink {
  target: string;
  alias?: string;
}

export interface Note {
  id: string;
  path: string;
  title: string;
  body: string;
  frontmatter: Record<string, unknown>;
  tags: string[];
  links: WikiLink[];
  created?: Date;
  updated?: Date;
}

export interface GraphNode {
  id: string;
  title: string;
  tags: string[];
  degree: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: 'wikilink' | 'shared-tag';
}

export interface NoteGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
