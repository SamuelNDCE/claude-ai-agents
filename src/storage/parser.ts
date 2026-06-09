import * as fs from 'fs';
import * as path from 'path';
import matter from 'gray-matter';
import type { Note, WikiLink } from './types';

const WIKILINK_RE = /\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]/g;
const INLINE_TAG_RE = /#([\w/-]+)/g;

export function parseNote(filePath: string, vaultRoot: string): Note {
  const raw = fs.readFileSync(filePath, 'utf-8');
  const { data, content: body } = matter(raw);

  const title =
    (data['title'] as string | undefined) ||
    body.match(/^#\s+(.+)/m)?.[1] ||
    path.basename(filePath, '.md');

  const fmTags: string[] = Array.isArray(data['tags'])
    ? (data['tags'] as unknown[]).map(String)
    : typeof data['tags'] === 'string'
    ? (data['tags'] as string).split(',').map((t) => t.trim())
    : [];
  const inlineTags = extractInlineTags(body);
  const tags = [...new Set([...fmTags, ...inlineTags])];

  const links = extractWikilinks(body);

  const createdRaw = data['created'];
  const updatedRaw = data['updated'];
  const created = createdRaw ? new Date(createdRaw as string) : undefined;
  const updated = updatedRaw ? new Date(updatedRaw as string) : undefined;

  const id = path.relative(vaultRoot, filePath).replace(/\\/g, '/');

  return {
    id,
    path: filePath,
    title,
    body,
    frontmatter: data as Record<string, unknown>,
    tags,
    links,
    created,
    updated,
  };
}

function extractWikilinks(text: string): WikiLink[] {
  const links: WikiLink[] = [];
  const re = new RegExp(WIKILINK_RE.source, 'g');
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    links.push({ target: m[1].trim(), alias: m[2]?.trim() });
  }
  return links;
}

function extractInlineTags(text: string): string[] {
  const tags: string[] = [];
  const re = new RegExp(INLINE_TAG_RE.source, 'g');
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    tags.push(m[1]);
  }
  return tags;
}
