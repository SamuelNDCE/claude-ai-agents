import * as fs from 'fs';
import * as path from 'path';
import { parseNote } from './parser';
import type { Note } from './types';

export class VaultStorage {
  private readonly root: string;
  private notes: Map<string, Note> = new Map();
  private byTitle: Map<string, string> = new Map(); // lowercase title → note id

  constructor(rootPath: string) {
    this.root = path.resolve(rootPath);
  }

  async scan(): Promise<void> {
    this.notes.clear();
    this.byTitle.clear();
    const files = findMarkdownFiles(this.root);
    for (const file of files) {
      try {
        const note = parseNote(file, this.root);
        this.notes.set(note.id, note);
        this.byTitle.set(note.title.toLowerCase(), note.id);
      } catch {
        // Skip notes with malformed frontmatter (e.g. unquoted colons in YAML values)
      }
    }
  }

  getNote(id: string): Note | undefined {
    return this.notes.get(id);
  }

  getNoteByTitle(title: string): Note | undefined {
    const id = this.byTitle.get(title.toLowerCase());
    return id ? this.notes.get(id) : undefined;
  }

  getAllNotes(): Note[] {
    return Array.from(this.notes.values());
  }

  async writeNote(id: string, content: string): Promise<void> {
    const filePath = path.join(this.root, id);
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, content, 'utf-8');
    // Re-parse and update index
    const note = parseNote(filePath, this.root);
    this.notes.set(note.id, note);
    this.byTitle.set(note.title.toLowerCase(), note.id);
  }

  watch(callback: (changedId: string) => void): fs.FSWatcher {
    return fs.watch(this.root, { recursive: true }, (_event: fs.WatchEventType, filename: string | Buffer | null) => {
      if (!filename || Buffer.isBuffer(filename)) return;
      if (filename && filename.endsWith('.md')) {
        const id = filename.replace(/\\/g, '/');
        const filePath = path.join(this.root, filename);
        if (fs.existsSync(filePath)) {
          const note = parseNote(filePath, this.root);
          this.notes.set(note.id, note);
          this.byTitle.set(note.title.toLowerCase(), note.id);
        }
        callback(id);
      }
    });
  }
}

function findMarkdownFiles(dir: string): string[] {
  const results: string[] = [];
  function walk(current: string): void {
    const entries = fs.readdirSync(current, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
      } else if (entry.isFile() && entry.name.endsWith('.md')) {
        results.push(fullPath);
      }
    }
  }
  walk(dir);
  return results;
}
