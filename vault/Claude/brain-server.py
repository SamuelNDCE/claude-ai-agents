#!/usr/bin/env python3
"""
NeuralVault — live server.

Scans this folder (the `Claude/` vault) for Markdown notes, parses frontmatter +
[[wikilinks]], and serves a live knowledge graph the neural map polls every few
seconds. Edit a note, add a link, and the map updates itself.

Run:  python brain-server.py        (defaults to port 8900)
Then open:  http://localhost:8900/

No dependencies — Python standard library only.
"""
import os, re, json, sys, html, gzip, time, urllib.parse, threading, platform, ctypes, subprocess
from collections import deque, Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE, "NeuralVault.html")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8900


def find_vault_root(start):
    d = start
    while True:
        if os.path.isdir(os.path.join(d, ".obsidian")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


VAULT_ROOT = find_vault_root(BASE)
VAULT_NAME = os.path.basename(VAULT_ROOT) if VAULT_ROOT else ""


def load_env():
    """Load KEY=VALUE from .env files into os.environ (don't overwrite existing). Secrets stay server-side."""
    candidates = [
        os.path.join(BASE, ".env"),
        r"C:\Users\Futur\Documents\AiWorkspace\Claude\.env",
        r"C:\Users\Futur\Documents\AiWorkspace\NeuralVault\.env",
    ]
    for path in candidates:
        try:
            for line in open(path, encoding="utf-8", errors="ignore"):
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                if line.lower().startswith("export "):
                    line = line[7:]
                k, v = line.split("=", 1)
                k = k.strip(); v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
        except FileNotFoundError:
            continue


load_env()
ANTHROPIC_KEY      = os.environ.get("ANTHROPIC_API_KEY", "")
NV_TOKEN           = os.environ.get("NEURALVAULT_TOKEN", "")
OLLAMA_URL         = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_DEFAULT_MOD = os.environ.get("OLLAMA_MODEL", "llama3.2")

ENV_FILE = r"C:\Users\Futur\Documents\AiWorkspace\Claude\.env"

def update_env_var(key, value):
    """Update or append KEY=VALUE in the primary .env file without touching other lines."""
    try:
        lines = open(ENV_FILE, encoding="utf-8").readlines()
    except FileNotFoundError:
        lines = []
    found = False; out = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("#") or "=" not in s:
            out.append(ln); continue
        k = s.split("=", 1)[0].strip()
        if k == key:
            out.append(f"{key}={value}\n"); found = True
        else:
            out.append(ln)
    if not found:
        out.append(f"{key}={value}\n")
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(out)

# wiki note type -> visualization type key (must match TYPES in the HTML)
TYPE_MAP = {
    "moc": "hub", "meta": "hub",
    "person": "person", "org": "org", "system": "system",
    "catalog": "entity", "inbox": "entity", "note": "entity", "task": "entity",
    "concept": "concept", "lesson": "concept", "pattern": "concept", "question": "concept",
    "source": "source", "observation": "source",
    "section": "section",
}

LINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
SECTION_RE = re.compile(r"^#{1,3}\s+(.+)$", re.MULTILINE)
SECTION_MIN = 80    # min chars in a section body to create a sub-neuron

# Generic template headings that appear in many notes — skip to avoid noise neurons
SECTION_SKIP = frozenset({
    "architecture", "files", "functions", "sources", "key claims", "what was built",
    "what happened", "write", "related", "notes", "overview", "summary", "details",
    "background", "context", "references", "links", "tags", "metadata",
    "high", "medium", "low", "open threads", "lessons banked", "what it contributes",
    "duplicate titles", "unconnected notes",
})


def _split_sections(nid, body):
    """Return list of (sec_id, heading, sec_body) for each H1-H3 section >= SECTION_MIN chars.
    Skips generic template headings that produce noise duplicate neurons."""
    matches = list(SECTION_RE.finditer(body))
    out = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sec_body = body[start:end].strip()
        if len(sec_body) < SECTION_MIN:
            continue
        heading = m.group(1).strip()
        # strip leading emoji/symbols to get the plain text for skip-check
        plain = re.sub(r"^[^\w]+", "", heading).strip().lower()
        if plain in SECTION_SKIP:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")[:40]
        out.append((f"{nid}#{slug}", heading, sec_body))
    return out


def field(fm, name):
    m = re.search(rf"^{name}\s*:\s*(.+)$", fm, re.MULTILINE)
    return m.group(1).strip() if m else ""


def first_alias(fm):
    raw = field(fm, "aliases")
    if not raw:
        return ""
    raw = raw.strip().strip("[]")
    parts = [p.strip().strip('"').strip("'") for p in raw.split(",") if p.strip()]
    return parts[0] if parts else ""


def prettify(slug):
    return re.sub(r"[-_]+", " ", os.path.basename(slug)).strip().title()


def _age_str(mtime):
    if not mtime: return "?"
    d = int(time.time() - mtime)
    if d < 3600: return f"{d//60}m"
    if d < 86400: return f"{d//3600}h"
    return f"{d//86400}d"


def clean_summary(body):
    # skip the H1 and blank/callout lines, grab first real paragraph
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(">") or s.startswith("---"):
            continue
        s = re.sub(r"\[\[([^\[\]|]+)\|([^\[\]]+)\]\]", r"\2", s)   # [[a|b]] -> b
        s = re.sub(r"\[\[([^\[\]]+)\]\]", r"\1", s)                # [[a]]   -> a
        s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)                   # bold
        s = re.sub(r"`([^`]+)`", r"\1", s)                         # code
        s = re.sub(r"\s*Parent:.*$", "", s)                        # drop Parent: tail
        s = s.strip()
        if len(s) > 170:
            s = s[:167].rstrip() + "…"
        if s:
            return s
    return ""


def _do_scan():
    nodes = {}          # id -> node dict
    relpaths = {}       # lower relpath-without-ext -> id
    basenames = {}      # lower basename -> [ids]
    alias_map = {}      # lower alias/title -> id
    raw_links = []      # (src_id, target_string)

    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            if not fn.endswith(".md"):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, BASE).replace("\\", "/")
            nid = rel[:-3]  # drop .md, keep path -> unique id
            try:
                text = open(full, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            fm, body = "", text
            m = FM_RE.match(text)
            if m:
                fm, body = m.group(1), text[m.end():]
            ntype = field(fm, "type").strip().strip('"').strip("'").lower()
            vtype = TYPE_MAP.get(ntype, "ext")
            label = (first_alias(fm) or field(fm, "title").strip('"').strip("'")
                     or prettify(nid))
            file_rel = (os.path.relpath(full, VAULT_ROOT).replace("\\", "/")
                        if VAULT_ROOT else rel)
            node = {"id": nid, "t": vtype, "label": label,
                    "s": clean_summary(body) or "(no summary yet)",
                    "file": file_rel, "size": len(text)}   # size = how much data is in the note
            nodes[nid] = node
            relpaths[nid.lower()] = nid
            basenames.setdefault(os.path.basename(nid).lower(), []).append(nid)
            for a in [label] + ([field(fm, "title")] if field(fm, "title") else []):
                if a:
                    alias_map[a.strip().lower()] = nid
            for mlink in LINK_RE.finditer(body):
                raw = mlink.group(1).replace("\\|", "|").replace("\\", "")
                tgt = raw.split("|")[0].split("#")[0].strip()
                if tgt:
                    raw_links.append((nid, tgt))

    # ── section sub-neurons: split large notes by H1-H3 headings ──
    section_edges = []   # (parent_nid, sec_id) — added to edges after wikilink resolution
    base_node_ids = set(nodes.keys())   # track real notes vs sections
    for nid in list(base_node_ids):
        nd = nodes[nid]
        if nd.get("t") == "ext":
            continue
        fp = nd.get("file", "")
        try:
            fp_full = os.path.join(VAULT_ROOT, fp) if VAULT_ROOT else os.path.join(BASE, fp)
            raw = open(fp_full, encoding="utf-8", errors="ignore").read()
            m2 = FM_RE.match(raw); body_s = raw[m2.end():] if m2 else raw
        except Exception:
            continue
        for sec_id, heading, sec_body in _split_sections(nid, body_s):
            nodes[sec_id] = {
                "id": sec_id, "t": "section", "label": heading,
                "s": sec_body[:100].replace("\n", " ").strip(),
                "file": fp, "size": len(sec_body), "parent": nid,
            }
            section_edges.append((nid, sec_id))

    def resolve(tgt):
        t = tgt.replace("\\", "/").strip().lower()
        if "/" in t:
            t = t[:-3] if t.endswith(".md") else t
            for nid_low, nid in relpaths.items():
                if nid_low.endswith(t):
                    return nid
            base = t.rsplit("/", 1)[-1]
        else:
            base = t
        if base in basenames and len(basenames[base]) == 1:
            return basenames[base][0]
        if t in alias_map:
            return alias_map[t]
        if base in alias_map:
            return alias_map[base]
        return None

    # ── body-text title-mention edges (implicit links even without [[wikilinks]]) ──
    # Build title -> node id map for titles long enough to be meaningful
    mention_map = {}  # lower_title -> id
    for nid, nd in nodes.items():
        lbl = (nd.get("label") or "").strip()
        if len(lbl) >= 5:   # skip very short titles — too many false positives
            mention_map[lbl.lower()] = nid

    body_cache = {}   # nid -> lower body text (read once, reuse)
    for nid, nd in nodes.items():
        if nd.get("t") == "ext":
            continue
        fp = nd.get("file")
        if not fp:
            continue
        try:
            fp_full = os.path.join(VAULT_ROOT, fp) if VAULT_ROOT else os.path.join(BASE, nd.get("file", ""))
            raw = open(fp_full, encoding="utf-8", errors="ignore").read()
            m2 = FM_RE.match(raw); body_cache[nid] = (raw[m2.end():] if m2 else raw).lower()
        except Exception:
            body_cache[nid] = ""

    mention_edges = set()
    for nid, body_lower in body_cache.items():
        for title_lower, other_id in mention_map.items():
            if other_id == nid:
                continue
            if title_lower in body_lower:
                key2 = tuple(sorted((nid, other_id)))
                mention_edges.add(key2)

    edges, seen = [], set()
    for src, tgt in raw_links:
        dst = resolve(tgt)
        if dst is None:
            # external note (lives outside the Claude brain folder) — show it lightly
            disp = tgt.split("/")[-1].rstrip("\\ ").strip()
            # keep only real-looking titles (multi-word); skip single-token junk like [[wikilinks]]
            if "/" in tgt or disp == "_index" or " " not in disp:
                continue
            ext_id = "ext::" + disp
            nodes.setdefault(ext_id, {"id": ext_id, "t": "ext", "label": disp,
                                      "s": "External note (outside the Claude brain folder)."})
            dst = ext_id
        if dst == src:
            continue
        key = tuple(sorted((src, dst)))
        if key in seen:
            continue
        seen.add(key)
        edges.append([src, dst])

    # Add implicit mention-based edges that weren't already captured by wikilinks
    for key2 in mention_edges:
        if key2 not in seen:
            seen.add(key2); edges.append(list(key2))

    # Add parent → section edges (sections orbit their parent note)
    for src, dst in section_edges:
        key = tuple(sorted((src, dst)))
        if key not in seen:
            seen.add(key); edges.append([src, dst])

    # ── guaranteed connectivity: every real node gets at least one edge ──
    # Isolated nodes (degree 0) are connected to the best-matching connected node.
    # Fallback edges are tracked separately so the linker can count real edges only.
    degree = Counter()
    for e in edges:
        degree[e[0]] += 1; degree[e[1]] += 1

    virtual_edge_keys = set()   # keys of fallback edges (not backed by real wikilinks)
    conn_pool = sorted(
        [nid for nid in nodes if degree[nid] > 0 and nodes[nid].get("t") != "ext"],
        key=lambda n: -degree[n])
    if conn_pool:
        isolated = [nid for nid in nodes if degree[nid] == 0 and nodes[nid].get("t") != "ext"]
        for nid in isolated:
            same = [h for h in conn_pool if nodes[h].get("t") == nodes[nid].get("t")]
            target = same[0] if same else conn_pool[0]
            key3 = tuple(sorted((nid, target)))
            if key3 not in seen:
                seen.add(key3); edges.append([nid, target])
                virtual_edge_keys.add(key3)

    return {"nodes": list(nodes.values()), "edges": edges, "vault": VAULT_NAME,
            "generated": True, "count": {"nodes": len(nodes), "edges": len(edges)},
            "virtual_edges": [list(k) for k in virtual_edge_keys]}


# ── Scan cache: background thread keeps graph fresh; HTTP handler always returns instantly ──
_scan_cache = None
_scan_cache_lock = threading.Lock()
_scan_ready = threading.Event()

def _scan_loop():
    global _scan_cache
    while True:
        try:
            result = _do_scan()
            with _scan_cache_lock:
                _scan_cache = result
            _scan_ready.set()
        except Exception:
            pass
        time.sleep(8)

threading.Thread(target=_scan_loop, daemon=True).start()

def scan():
    """Returns the latest cached graph instantly; blocks only on very first call (≤30s)."""
    _scan_ready.wait(timeout=30)
    with _scan_cache_lock:
        return _scan_cache or {"nodes": [], "edges": [], "count": {"nodes": 0, "edges": 0}}


# Learned-weight memory (STDP output). This file + the notes are the artifact a local
# LLM would later consume: a knowledge graph annotated with learned connection strengths.
STATE_FILE = os.path.join(BASE, "brain-state.json")       # full fidelity, NO compression
GZ_STATE = os.path.join(BASE, "brain-state.json.gz")      # legacy compressed file (migrated on load)


def load_state():
    try:
        return open(STATE_FILE, encoding="utf-8").read()
    except FileNotFoundError:
        try:                                              # migrate legacy gz once
            with gzip.open(GZ_STATE, "rb") as f:
                return f.read().decode("utf-8")
        except FileNotFoundError:
            return '{"weights":{},"updated":null}'


def save_state(body):
    """Full-fidelity save — every learned weight kept, no pruning, no compression."""
    try:
        data = json.loads(body)
    except Exception:
        return None
    w = data.get("weights", {}) or {}
    data["updated"] = int(time.time() * 1000)
    raw = json.dumps(data).encode("utf-8")
    with open(STATE_FILE, "wb") as f:
        f.write(raw)
    try:                                                  # drop legacy gz so it can't shadow
        if os.path.exists(GZ_STATE):
            os.remove(GZ_STATE)
    except OSError:
        pass
    return {"ok": True, "weights": len(w), "bytes": len(raw)}


def storage_report():
    """How much space the brain occupies, by category."""
    cats = {"notes": [0, 0], "memory": [0, 0], "engine": [0, 0], "other": [0, 0]}
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            p = os.path.join(root, fn)
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            if fn.endswith(".md"):
                k = "notes"
            elif fn.startswith("brain-state"):
                k = "memory"
            elif fn.endswith((".html", ".py")):
                k = "engine"
            else:
                k = "other"
            cats[k][0] += sz
            cats[k][1] += 1
    total = sum(v[0] for v in cats.values())
    # memory compression ratio (raw weights vs gz on disk)
    ratio = None
    try:
        raw = len(json.loads(load_state()).get("weights", {}))
    except Exception:
        raw = 0
    return {"total_bytes": total,
            "categories": {k: {"bytes": v[0], "files": v[1]} for k, v in cats.items()},
            "weights_stored": raw,
            "state_gz_bytes": os.path.getsize(STATE_FILE) if os.path.exists(STATE_FILE) else 0}


def api_system_metrics():
    """Return a real-time snapshot of system resource usage using only stdlib.
    CPU% is a 0.1s blocking sample. Not cached — always fresh."""
    # ── CPU% via two successive /proc/stat reads (Windows: wmic fallback) ──
    def _cpu_pct():
        if platform.system() == "Windows":
            try:
                out = subprocess.check_output(
                    ["wmic", "cpu", "get", "LoadPercentage", "/value"],
                    timeout=5, stderr=subprocess.DEVNULL).decode("utf-8", "replace")
                m = re.search(r"LoadPercentage=(\d+)", out)
                return float(m.group(1)) if m else 0.0
            except Exception:
                return 0.0
        # Linux/macOS — read /proc/stat twice with 0.1 s gap
        def _read_stat():
            try:
                line = open("/proc/stat").readline()
                vals = list(map(int, line.split()[1:]))
                idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
                total = sum(vals)
                return idle, total
            except Exception:
                return 0, 1
        i1, t1 = _read_stat()
        time.sleep(0.1)
        i2, t2 = _read_stat()
        dt = t2 - t1
        return round((1.0 - (i2 - i1) / dt) * 100, 1) if dt > 0 else 0.0

    # ── Memory ──
    mem_used_mb = mem_total_mb = 0
    if platform.system() == "Windows":
        class _MEMSTATEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
        ms = _MEMSTATEX()
        ms.dwLength = ctypes.sizeof(ms)
        try:
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
            mem_total_mb = ms.ullTotalPhys // (1024 * 1024)
            mem_used_mb  = mem_total_mb - ms.ullAvailPhys // (1024 * 1024)
        except Exception:
            pass
    else:
        try:
            info = {}
            for line in open("/proc/meminfo"):
                k, v = line.split(":", 1)
                info[k.strip()] = int(v.strip().split()[0])
            mem_total_mb = info.get("MemTotal", 0) // 1024
            mem_used_mb  = mem_total_mb - info.get("MemAvailable", info.get("MemFree", 0)) // 1024
        except Exception:
            pass

    # ── Disk free (vault drive) ──
    disk_free_gb = 0.0
    try:
        st = os.statvfs(BASE) if hasattr(os, "statvfs") else None
        if st:
            disk_free_gb = round(st.f_bavail * st.f_frsize / (1024 ** 3), 1)
        elif platform.system() == "Windows":
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(os.path.splitdrive(BASE)[0] + "\\"),
                None, None, ctypes.byref(free_bytes))
            disk_free_gb = round(free_bytes.value / (1024 ** 3), 1)
    except Exception:
        pass

    # ── System uptime ──
    uptime_s = 0
    if platform.system() == "Windows":
        try:
            uptime_s = int(ctypes.windll.kernel32.GetTickCount64() / 1000)
        except Exception:
            pass
    else:
        try:
            uptime_s = int(float(open("/proc/uptime").read().split()[0]))
        except Exception:
            pass

    cpu_pct = _cpu_pct()
    return {
        "cpu_pct": cpu_pct,
        "mem_used_mb": mem_used_mb,
        "mem_total_mb": mem_total_mb,
        "disk_free_gb": disk_free_gb,
        "uptime_s": uptime_s,
    }


# ---------- Agent API: let other AI agents read & write the brain ----------
def _safe_under(path):
    rp = os.path.realpath(path)
    return rp if rp.startswith(os.path.realpath(BASE)) else None


def slugify(s):
    s = re.sub(r"[^a-zA-Z0-9 -]", "", s).strip().lower()
    return re.sub(r"\s+", "-", s)[:60] or "note"


# ───────────── In-memory note index + inverted (posting-list) index ─────────────
NOTE_INDEX  = {}  # id  -> {id, title, type, tokens, content, cl, size, mtime}
TOKEN_INDEX = {}  # tok -> set of note IDs  (posting list — makes search O(k) not O(N))
INDEX_LOCK  = threading.Lock()

# Lightweight response cache — avoids recomputing identical queries within the TTL
_RESP_CACHE: dict = {}   # key -> (timestamp, payload)
_RESP_TTL   = 45.0       # seconds; set low enough that new notes show up quickly

# Activity counter — tracks agent API calls so the visualization fire rate can fluctuate
_ACTIVITY: deque = deque()   # monotonic timestamps of meaningful API calls (auto-pruned)

def record_activity(weight: float = 1.0):
    """Record an agent API call. Weight > 1 for heavier operations (writes)."""
    now = time.monotonic()
    for _ in range(max(1, round(weight))):
        _ACTIVITY.append(now)
    # Keep only the last 60 seconds
    cutoff = now - 60.0
    while _ACTIVITY and _ACTIVITY[0] < cutoff:
        _ACTIVITY.popleft()

def get_activity():
    """Return call counts over recent windows (used by /api/activity)."""
    now = time.monotonic()
    return {
        "calls_10s": sum(1 for t in _ACTIVITY if t >= now - 10),
        "calls_60s": sum(1 for t in _ACTIVITY if t >= now - 60),
    }

def _cache_get(key):
    hit = _RESP_CACHE.get(key)
    return hit[1] if hit and (time.time() - hit[0]) < _RESP_TTL else None

def _cache_set(key, val):
    _RESP_CACHE[key] = (time.time(), val)
    # Evict old entries occasionally (keep max 200)
    if len(_RESP_CACHE) > 200:
        oldest = sorted(_RESP_CACHE, key=lambda k: _RESP_CACHE[k][0])
        for k in oldest[:50]:
            _RESP_CACHE.pop(k, None)

def _cache_invalidate():
    """Clear cache when notes change."""
    _RESP_CACHE.clear()


def _index_note(full_path):
    """Index or re-index a single .md file. Skips if mtime unchanged."""
    try:
        rel = os.path.relpath(full_path, BASE).replace("\\", "/")
        nid = rel[:-3] if rel.endswith(".md") else rel
        mtime = os.path.getmtime(full_path)
        with INDEX_LOCK:
            cached = NOTE_INDEX.get(nid)
        if cached and cached.get("mtime") == mtime:
            return
        text = open(full_path, encoding="utf-8", errors="ignore").read()
        m = FM_RE.match(text)
        fm = m.group(1) if m else ""
        body = text[m.end():] if m else text
        title = (first_alias(fm) or field(fm, "title").strip().strip('"').strip("'")
                 or prettify(nid))
        ntype = field(fm, "type").strip().lower()
        raw    = (title + " " + body).lower()
        tokens = frozenset(t for t in re.split(r"[^a-z0-9]+", raw) if len(t) >= 3)
        cl     = body.lower()   # pre-computed for O(1) substring search
        # Parse tags from frontmatter into a list
        raw_tags = field(fm, "tags")
        tags_list = []
        if raw_tags:
            raw_tags = raw_tags.strip().strip("[]")
            tags_list = [t.strip().strip('"').strip("'")
                         for t in raw_tags.split(",") if t.strip()]

        with INDEX_LOCK:
            old = NOTE_INDEX.get(nid)
            old_tokens = old["tokens"] if old else frozenset()
            # Update posting lists: remove from tokens that dropped, add to new tokens
            for tok in old_tokens - tokens:
                s = TOKEN_INDEX.get(tok)
                if s: s.discard(nid)
            for tok in tokens - old_tokens:
                TOKEN_INDEX.setdefault(tok, set()).add(nid)
            NOTE_INDEX[nid] = {
                "id": nid, "title": title, "type": ntype,
                "content": body, "cl": cl, "tokens": tokens,
                "size": len(text), "mtime": mtime, "tags": tags_list,
            }
            # Remove any stale section sub-entries for this note
            stale = [k for k in NOTE_INDEX if k.startswith(nid + "#")]
            for k in stale:
                for tok in NOTE_INDEX[k].get("tokens", frozenset()):
                    s = TOKEN_INDEX.get(tok)
                    if s: s.discard(k)
                del NOTE_INDEX[k]

        # Index each H1-H3 section as a separate searchable sub-neuron
        for sec_id, heading, sec_body in _split_sections(nid, body):
            raw_s = (heading + " " + sec_body).lower()
            tok_s = frozenset(t for t in re.split(r"[^a-z0-9]+", raw_s) if len(t) >= 3)
            with INDEX_LOCK:
                old_s = NOTE_INDEX.get(sec_id)
                old_tok_s = old_s["tokens"] if old_s else frozenset()
                for tok in old_tok_s - tok_s:
                    s = TOKEN_INDEX.get(tok)
                    if s: s.discard(sec_id)
                for tok in tok_s - old_tok_s:
                    TOKEN_INDEX.setdefault(tok, set()).add(sec_id)
                NOTE_INDEX[sec_id] = {
                    "id": sec_id, "title": heading, "type": "section",
                    "content": sec_body, "cl": sec_body.lower(), "tokens": tok_s,
                    "size": len(sec_body), "mtime": mtime, "parent": nid,
                    "tags": tags_list,  # inherit parent note's tags
                }
        _cache_invalidate()
    except Exception:
        pass


def _remove_from_index(full_path):
    rel = os.path.relpath(full_path, BASE).replace("\\", "/")
    nid = rel[:-3] if rel.endswith(".md") else rel
    with INDEX_LOCK:
        # Remove parent note
        entry = NOTE_INDEX.pop(nid, None)
        if entry:
            for tok in entry.get("tokens", frozenset()):
                s = TOKEN_INDEX.get(tok)
                if s: s.discard(nid)
        # Remove all section sub-entries
        sec_keys = [k for k in NOTE_INDEX if k.startswith(nid + "#")]
        for k in sec_keys:
            for tok in NOTE_INDEX[k].get("tokens", frozenset()):
                s = TOKEN_INDEX.get(tok)
                if s: s.discard(k)
            del NOTE_INDEX[k]


def _build_index():
    """Walk vault and index every .md file. Runs once in background at startup."""
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            if fn.endswith(".md"):
                _index_note(os.path.join(root, fn))


def api_search(q):
    """Indexed full-text search with token-overlap scoring. O(N) over in-memory index."""
    q = (q or "").lower().strip()
    if not q:
        return []

    cached = _cache_get("search:" + q)
    if cached is not None:
        return cached

    q_tokens = frozenset(t for t in re.split(r"[^a-z0-9]+", q) if len(t) >= 3)

    # If index not built yet, fall back to disk scan for this call
    with INDEX_LOCK:
        if not NOTE_INDEX:
            snapshot = None
        else:
            snapshot = list(NOTE_INDEX.values())

    if snapshot is None:
        # cold fallback — index is still building
        out = []
        for root, dirs, files in os.walk(BASE):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fn in files:
                if not fn.endswith(".md"):
                    continue
                full = os.path.join(root, fn)
                rel  = os.path.relpath(full, BASE).replace("\\", "/")
                try:
                    text = open(full, encoding="utf-8", errors="ignore").read()
                except Exception:
                    continue
                low = text.lower()
                if q in low or q in fn.lower():
                    m   = FM_RE.match(text)
                    fm  = m.group(1) if m else ""
                    idx = low.find(q)
                    snip = text[max(0, idx-60):idx+120].replace("\n", " ").strip()
                    out.append({"id": rel[:-3], "file": rel,
                                "title": field(fm, "title") or prettify(rel[:-3]),
                                "type": field(fm, "type"), "size": len(text), "snippet": snip,
                                "score": 1})
                if len(out) >= 40:
                    return out
        return out

    # Use posting lists to get candidates — O(k) not O(N)
    with INDEX_LOCK:
        if q_tokens:
            candidate_ids = set()
            for tok in q_tokens:
                candidate_ids |= TOKEN_INDEX.get(tok, set())
            # Add substring-match candidates for the full phrase (catches stop-word phrases)
            if not candidate_ids or len(q.split()) == 1:
                pass  # posting lists sufficient
        else:
            candidate_ids = set(NOTE_INDEX.keys())
        snapshot = {nid: NOTE_INDEX[nid] for nid in candidate_ids if nid in NOTE_INDEX}

    if not snapshot and q:
        # Substring fallback for phrases not in token set
        with INDEX_LOCK:
            snapshot = dict(NOTE_INDEX)

    results = []
    for nid, entry in snapshot.items():
        tl    = entry.get("title", "").lower()
        cl    = entry.get("cl", "")
        score = 0

        if q in tl:
            score += 10
        elif any(t in tl for t in q_tokens):
            score += 4

        score += len(q_tokens & entry["tokens"]) * 2

        if score == 0 and q in cl:
            score += 1

        if score == 0:
            continue

        # Recency boost: recently modified notes are more likely to be relevant
        age = time.time() - entry.get("mtime", 0)
        if age < 7 * 86400:
            score += 3
        elif age < 30 * 86400:
            score += 1

        idx = cl.find(q)
        if idx < 0:
            for tok in sorted(q_tokens, key=len, reverse=True):
                idx = cl.find(tok)
                if idx >= 0:
                    break
        snip = (entry["content"][max(0, idx-30):idx+70].replace("\n", " ").strip()
                if idx >= 0 else entry["content"][:100].replace("\n", " ").strip())

        # Section sub-neurons are useful but should rank below their parent note
        if entry.get("type") == "section":
            score = max(1, score - 2)

        item = {
            "id": nid, "title": entry["title"],
            "type": entry["type"], "snippet": snip, "score": score,
            "tokens_est": entry["size"] // 4,
            "modified_ago": _age_str(entry.get("mtime")),
        }
        if entry.get("tags"):
            item["tags"] = entry["tags"]
        if entry.get("parent"):
            item["parent"] = entry["parent"]
        results.append(item)

    results.sort(key=lambda r: -r["score"])
    final = results[:10]
    _cache_set("search:" + q, final)
    return final


def api_get_note(ident):
    ident = (ident or "").replace("\\", "/").strip()
    cand = ident if ident.endswith(".md") else ident + ".md"
    full = _safe_under(os.path.join(BASE, cand))
    if full and os.path.isfile(full):
        text = open(full, encoding="utf-8", errors="ignore").read()
        return {"id": ident[:-3] if ident.endswith(".md") else ident,
                "file": os.path.relpath(full, BASE).replace("\\", "/"), "content": text}
    base = os.path.basename(ident).lower()                # fall back to basename search
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            if fn.endswith(".md") and fn[:-3].lower() == base:
                full = os.path.join(root, fn)
                return {"id": os.path.relpath(full, BASE).replace("\\", "/")[:-3],
                        "file": os.path.relpath(full, BASE).replace("\\", "/"),
                        "content": open(full, encoding="utf-8", errors="ignore").read()}
    return None


def api_peek(ident, chars=400):
    """Return just the first `chars` characters of a note's body (after frontmatter).
    Faster than /api/note for quick lookups — uses the in-memory index when possible."""
    ident = (ident or "").replace("\\", "/").strip()
    cache_key = f"peek:{ident}:{chars}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    with INDEX_LOCK:
        entry = NOTE_INDEX.get(ident)
    if entry:
        preview = entry["content"][:chars].replace("\n", " ").strip()
        result = {"id": ident, "title": entry.get("title", ""), "preview": preview}
        _cache_set(cache_key, result)
        return result

    # Fallback: read from disk
    note = api_get_note(ident)
    if not note:
        return None
    text = note["content"]
    m = FM_RE.match(text)
    body = text[m.end():] if m else text
    preview = body[:chars].replace("\n", " ").strip()
    result = {"id": note["id"], "title": "", "preview": preview}
    _cache_set(cache_key, result)
    return result


def api_context():
    """Compact working-memory snapshot for injecting into Claude sessions.
    Targets ~1200 tokens: recent observations + key concept excerpts + active agent goals."""
    cached = _cache_get("ctx")
    if cached is not None:
        return cached
    # Recent notes from agent-inbox, sorted newest first (observations = ephemeral context)
    inbox_dir = os.path.join(BASE, "wiki/agent-inbox")
    recent = []
    if os.path.isdir(inbox_dir):
        mds = sorted(
            [os.path.join(inbox_dir, f) for f in os.listdir(inbox_dir) if f.endswith(".md")],
            key=lambda p: os.path.getmtime(p), reverse=True)[:5]
        for fp in mds:
            try:
                text = open(fp, encoding="utf-8", errors="ignore").read()
                m = FM_RE.match(text)
                fm   = m.group(1) if m else ""
                body = text[m.end():] if m else text
                title = field(fm, "title") or prettify(os.path.splitext(os.path.basename(fp))[0])
                age = _age_str(os.path.getmtime(fp))
                recent.append({"title": title, "summary": clean_summary(body), "age": age})
            except Exception:
                pass

    # Hub / concept notes — blend recency with size so newly promoted notes surface
    now_ts = time.time()
    with INDEX_LOCK:
        hub_pool = [e for e in NOTE_INDEX.values()
                    if e.get("type") in ("moc", "concept", "hub", "pattern", "lesson", "synthesis", "meta")
                    and "#" not in e.get("id", "")]
    for h in hub_pool:
        age_days = (now_ts - (h.get("mtime") or 0)) / 86400
        h["_score"] = h["size"] + max(0, (7 - age_days) * 200)   # recency bonus decays over 7 days
    hubs = sorted(hub_pool, key=lambda e: -e["_score"])[:5]
    key_concepts = [{"title": h["title"], "type": h["type"],
                     "excerpt": h["content"][:150].replace("\n", " ").strip()}
                    for h in hubs]

    # Active agent goals
    agent_goals = [{"name": a.get("name"), "goal": (a.get("goal") or "")[:200]}
                   for a in AGENTS if a.get("enabled") and a.get("goal")]

    with INDEX_LOCK:
        node_count = len(NOTE_INDEX)
        # Graph stats: count non-section nodes by type (sections are internal detail)
        type_counts = Counter(
            e.get("type", "?")
            for e in NOTE_INDEX.values()
            if e.get("type") != "section"
        )

    # Top-5 most recently modified notes anywhere in the vault (excluding sections + observations)
    with INDEX_LOCK:
        all_notes = [(e["id"], e.get("mtime", 0), e.get("title", ""), e.get("type", ""), e.get("content", ""))
                     for e in NOTE_INDEX.values()
                     if "#" not in e["id"] and e.get("type") != "observation"]  # skip ephemeral observations
    recent_activity = sorted(all_notes, key=lambda x: -x[1])[:3]

    # Plain-text format: ~50% fewer tokens than JSON for same information
    lines = [f"NV:{VAULT_NAME}|{node_count}n|{time.strftime('%Y-%m-%d %H:%M')}", ""]

    # Graph stats line: type breakdown for quick vault shape awareness
    if type_counts:
        stats_parts = "|".join(f"{t}:{c}" for t, c in
                               sorted(type_counts.items(), key=lambda x: -x[1]))
        lines.append(f"GRAPH STATS: {stats_parts}")
        lines.append("")

    if recent:
        lines.append("RECENT OBSERVATIONS:")
        for r in recent:
            s = (r.get("summary") or "")[:120].replace("\n", " ")
            lines.append(f"  {r['title'][:55]} ({r.get('age','?')}): {s}")
        lines.append("")

    # 3 most recently modified notes (vault-wide, non-observation)
    if recent_activity:
        lines.append("RECENT ACTIVITY:")
        for nid, mtime, title, ntype, content in recent_activity:
            ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime)) if mtime else "?"
            snip = content[:80].replace("\n", " ").strip()
            lines.append(f"  [{ntype}] {title[:45]} ({ts}): {snip}")
        lines.append("")

    if key_concepts:
        lines.append("KEY CONCEPTS:")
        for c in key_concepts:
            ex = (c.get("excerpt") or "")[:150].replace("\n", " ")
            lines.append(f"  [{c['type']}] {c['title'][:50]}: {ex}")
        lines.append("")
    if agent_goals:
        lines.append("ACTIVE AGENTS:")
        for a in agent_goals:
            lines.append(f"  {a['name']}: {a['goal'][:120]}")
        lines.append("")
    # Surface agent last results so Claude sees their work without extra API calls
    agent_insights = [
        (a.get("name", "?"), (a.get("last_result") or "").replace("\n", " ")[:150])
        for a in AGENTS if a.get("enabled") and a.get("last_result")
    ]
    if agent_insights:
        lines.append("AGENT INSIGHTS:")
        for name, res in agent_insights[:5]:
            lines.append(f"  {name}: {res}")
    result = "\n".join(lines)
    _cache_set("ctx", result)
    return result


def api_fetch_to_vault(payload):
    """Fetch a web URL, strip HTML, and save it as a source note in wiki/sources/.
    Returns {"id": slug, "chars": N} or raises ValueError for bad input."""
    import urllib.request, urllib.error
    url = (payload.get("url") or "").strip()
    if not url:
        raise ValueError("url required")
    scheme = urllib.parse.urlparse(url).scheme.lower()
    if scheme not in ("http", "https"):
        raise ValueError("only http/https URLs are supported")

    title = (payload.get("title") or "").strip()

    # Fetch with 10 s timeout
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; NeuralVault/1.0)"})
    with urllib.request.urlopen(req, timeout=10) as r:
        raw = r.read(131072).decode("utf-8", "replace")

    # Strip <script>, <style>, then all remaining tags
    raw = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', raw)
    raw = re.sub(r'<[^>]+>', ' ', raw)
    raw = re.sub(r'[ \t]+', ' ', raw)
    raw = re.sub(r'\n\s*\n\s*\n', '\n\n', raw).strip()
    text = raw[:4000]

    # Derive title from content if not supplied
    if not title:
        m_title = re.search(r'<title[^>]*>([^<]{1,120})</title>', raw, re.IGNORECASE)
        title = m_title.group(1).strip() if m_title else url[:60]

    slug = slugify(title or "web-fetch")
    sources_dir = _safe_under(os.path.join(BASE, "wiki/sources"))
    if not sources_dir:
        raise ValueError("wiki/sources not accessible")
    os.makedirs(sources_dir, exist_ok=True)
    full = os.path.join(sources_dir, slug + ".md")

    today = time.strftime("%Y-%m-%d")
    fm = (f"---\ntitle: {title}\ntype: source\nstatus: seed\n"
          f"source: web-fetch\nurl: {url}\ncreated: {today}\nupdated: {today}\n"
          f"tags: [web]\n---\n\n")
    with open(full, "w", encoding="utf-8") as f:
        f.write(fm + f"# {title}\n\n{text}\n")
    threading.Thread(target=_index_note, args=(full,), daemon=True).start()
    return {"id": slug, "chars": len(text)}


def api_graph_stats():
    """Richer graph data: total count, type breakdown, top-5 hubs by degree, 5 most recent.
    Cached with key 'graph:stats', 60 s TTL."""
    cached = _cache_get("graph:stats")
    if cached is not None:
        return cached

    # Build the full graph to get real edges and degree counts
    g = scan()
    degree = Counter()
    for e in g["edges"]:
        degree[e[0]] += 1
        degree[e[1]] += 1

    with INDEX_LOCK:
        # Type counts — exclude section sub-neurons
        by_type = Counter(
            e.get("type", "?")
            for e in NOTE_INDEX.values()
            if e.get("type") != "section" and "#" not in e["id"]
        )
        total = sum(by_type.values())

        # Top-5 hubs by degree (exclude ext:: and section nodes)
        hub_candidates = [
            (nid, entry)
            for nid, entry in NOTE_INDEX.items()
            if "#" not in nid and not nid.startswith("ext::")
        ]
        hub_candidates.sort(key=lambda x: -degree[x[0]])
        top_hubs = [
            {"id": nid, "title": entry.get("title", nid), "deg": degree[nid]}
            for nid, entry in hub_candidates[:5]
        ]

        # 5 most recently modified notes (exclude sections)
        recents = sorted(
            [(nid, entry) for nid, entry in NOTE_INDEX.items() if "#" not in nid],
            key=lambda x: -(x[1].get("mtime") or 0)
        )[:5]
        recent = [
            {"id": nid, "title": entry.get("title", nid),
             "mtime": time.strftime("%Y-%m-%d", time.localtime(entry["mtime"])) if entry.get("mtime") else ""}
            for nid, entry in recents
        ]

    result = {
        "total": total,
        "by_type": dict(sorted(by_type.items(), key=lambda x: -x[1])),
        "top_hubs": top_hubs,
        "recent": recent,
    }
    _cache_set("graph:stats", result)
    return result


# every captured thought/lesson becomes a neuron, filed in an organized folder by its type
FOLDER_BY_TYPE = {
    "observation": "wiki/agent-inbox", "thought": "wiki/agent-inbox", "note": "wiki/agent-inbox",
    "lesson": "wiki/lessons", "pattern": "wiki/patterns", "task": "wiki/tasks",
    "concept": "wiki/concepts", "entity": "wiki/entities", "source": "wiki/sources",
    "question": "wiki/questions",
    # structural / hub types
    "meta": "wiki/meta", "moc": "wiki/meta",
    # entity subtypes — all land in entities
    "person": "wiki/entities", "org": "wiki/entities", "system": "wiki/entities",
    # higher-order notes
    "synthesis": "wiki/synthesis", "catalog": "wiki/catalog",
    # inbox alias
    "inbox": "wiki/agent-inbox",
}


def api_create_note(payload):
    title = (payload.get("title") or "").strip()
    content = payload.get("content") or ""
    if not title and not content:
        return None
    ntype = payload.get("type") or "note"
    folder = payload.get("folder") or FOLDER_BY_TYPE.get(ntype, "wiki/agent-inbox")
    tags = payload.get("tags") or ["wiki/agent", "agent-ingest"]
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    fname = slugify(title or ("note-" + str(int(time.time()))))
    folder_full = _safe_under(os.path.join(BASE, folder))
    if not folder_full:
        return None
    os.makedirs(folder_full, exist_ok=True)
    full = os.path.join(folder_full, fname + ".md")
    if os.path.exists(full):                              # append mode if exists
        with open(full, "a", encoding="utf-8") as f:
            f.write("\n\n" + content)
        action = "appended"
    else:
        today = time.strftime("%Y-%m-%d")
        links = payload.get("links") or []
        rel = "\n\nRelated: " + " · ".join(f"[[{l}]]" for l in links) if links else ""
        note_status = payload.get("status") or "seed"
        fm = (f"---\ntitle: {title or fname}\ntype: {ntype}\nstatus: {note_status}\n"
              f"source: agent-api\ncreated: {today}\nupdated: {today}\n"
              f"tags: [{', '.join(tags)}]\n---\n\n")
        with open(full, "w", encoding="utf-8") as f:
            f.write(fm + f"# {title or fname}\n\n{content}{rel}\n")
        action = "created"
    threading.Thread(target=_index_note, args=(full,), daemon=True).start()
    return {"ok": True, "action": action,
            "file": os.path.relpath(full, BASE).replace("\\", "/")}


def api_save(payload):
    """Slice 2 editor: overwrite an existing note's full markdown (sandboxed, must already exist)."""
    ident = (payload.get("id") or payload.get("file") or "").replace("\\", "/").strip()
    content = payload.get("content")
    if not ident or content is None:
        return None
    cand = ident if ident.endswith(".md") else ident + ".md"
    full = _safe_under(os.path.join(BASE, cand))
    if not full:
        return None
    if not os.path.isfile(full):
        return {"ok": False, "error": "note not found (use /api/note to create)"}
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    threading.Thread(target=_index_note, args=(full,), daemon=True).start()
    return {"ok": True, "file": os.path.relpath(full, BASE).replace("\\", "/"),
            "bytes": len(content.encode("utf-8"))}


def api_ask(q):
    """Retrieval foundation for the NeuralVault voice (Jarvis). Finds the most relevant
    neurons and returns an extractive answer. Wire a local LLM to synthesize from `sources`."""
    q = (q or "").strip()
    if not q:
        return {"question": q, "answer": "Ask me something about the vault.", "sources": []}
    hits = api_search(q)
    if not hits:
        # retry on individual keywords
        for w in sorted(q.lower().split(), key=len, reverse=True):
            if len(w) > 3:
                hits = api_search(w)
                if hits:
                    break
    if not hits:
        return {"question": q, "answer": "Nothing in the vault matches that yet.", "sources": []}
    hits.sort(key=lambda h: (q.lower() in (h["title"] or "").lower(), h.get("tokens_est", h.get("size", 0))), reverse=True)
    top = hits[:3]
    note = api_get_note(top[0]["id"])
    body = note["content"] if note else ""
    m = FM_RE.match(body)
    body = body[m.end():] if m else body
    paras = [p.strip() for p in re.split(r"\n\s*\n", body)
             if p.strip() and not p.strip().startswith(("#", "|", "---"))]
    answer = re.sub(r"\[\[([^\[\]|]+)\|([^\[\]]+)\]\]", r"\2", " ".join(paras[:2]))
    answer = re.sub(r"\[\[([^\[\]]+)\]\]", r"\1", answer)[:600]
    return {"question": q, "answer": answer or top[0]["snippet"],
            "sources": [{"id": h["id"], "title": h["title"]} for h in top],
            "synthesized": False, "note": "extractive — connect a local LLM to /api/ask for true answers"}


# ───────────────────────── Agent system ─────────────────────────
AGENTS_FILE = os.path.join(BASE, "agents.json")
AGENT_LOG = deque(maxlen=120)
WRITE_LOCK = threading.Lock()
DEFAULT_AGENTS = [
    {"id": "vault-keeper-0001", "name": "Vault Keeper",
     "role": "Stats · orphan curation · frontmatter lint · neuron linking · redundant note cleanup",
     "type": "vault-keeper", "interval": 1800, "enabled": True, "last_run": 0, "last_result": ""},
]


def load_agents():
    try:
        return json.load(open(AGENTS_FILE, encoding="utf-8"))
    except Exception:
        save_agents(DEFAULT_AGENTS)
        return [dict(a) for a in DEFAULT_AGENTS]


def save_agents(a):
    with WRITE_LOCK:
        with open(AGENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(a, f, indent=2)


AGENTS = load_agents()


def _write_report(relpath, title, body):
    full = os.path.join(BASE, relpath)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    day = time.strftime("%Y-%m-%d")
    fm = (f"---\ntitle: {title}\ntype: source\nstatus: ripe\nsource: agent\n"
          f"created: {day}\nupdated: {day}\ntags: [wiki/agents, agent-report]\n---\n\n")
    with WRITE_LOCK:
        open(full, "w", encoding="utf-8").write(fm + body)
    threading.Thread(target=_index_note, args=(full,), daemon=True).start()
    return os.path.relpath(full, BASE).replace("\\", "/")


def agent_stats(a=None):
    g = scan(); s = storage_report()
    # Pick 2 real hub/concept nodes to link to (not phantom titles like [[index]])
    hubs = [n["label"] for n in g["nodes"] if n.get("t") in ("hub", "concept") and n.get("label")][:2]
    related = (" · ".join(f"[[{h}]]" for h in hubs)) if hubs else ""
    body = (f"# Brain stats\n\nSnapshot {time.strftime('%Y-%m-%d %H:%M')}.\n\n"
            f"- Neurons: **{g['count']['nodes']}**\n- Synapses: **{g['count']['edges']}**\n"
            f"- Storage: **{s['total_bytes']} bytes**\n"
            + (f"\nRelated: {related}\n" if related else ""))
    _write_report("wiki/agents/brain-stats.md", "Brain stats", body)
    return f"{g['count']['nodes']} neurons, {g['count']['edges']} synapses"


def agent_curator(a=None):
    g = scan()
    endpoints = set()
    for e in g["edges"]:
        endpoints.add(e[0]); endpoints.add(e[1])
    weak = [n for n in g["nodes"] if n["id"] not in endpoints and n["t"] != "hub"]
    titles = Counter((n["label"] or "").lower() for n in g["nodes"])
    dups = [t for t, c in titles.items() if c > 1 and t]
    hubs = [n["label"] for n in g["nodes"] if n.get("t") in ("hub","concept") and n.get("label")][:2]
    related = " · ".join(f"[[{h}]]" for h in hubs) if hubs else ""
    body = ("# Curator report\n\n" + time.strftime("%Y-%m-%d %H:%M") +
            "\n\n## Unconnected notes\n" +
            ("\n".join(f"- {o['label']}" for o in weak) or "- none") +
            "\n\n## Duplicate titles\n" + ("\n".join(f"- {d}" for d in dups) or "- none") +
            ("\n\nRelated: " + related if related else "") + "\n")
    _write_report("wiki/agents/curator-report.md", "Curator report", body)
    return f"{len(weak)} orphans, {len(dups)} dup titles"


def agent_linter(a=None):
    n = 0; gaps = []
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            if not fn.endswith(".md"):
                continue
            n += 1
            txt = open(os.path.join(root, fn), encoding="utf-8", errors="ignore").read()
            m = FM_RE.match(txt); fm = m.group(1) if m else ""
            miss = [k for k in ("type", "created", "tags") if not field(fm, k)]
            if miss:
                gaps.append((os.path.relpath(os.path.join(root, fn), BASE).replace("\\", "/"), miss))
    body = ("# Lint report\n\n" + time.strftime("%Y-%m-%d %H:%M") + f"\n\nScanned {n} notes.\n\n## Frontmatter gaps\n" +
            ("\n".join(f"- {p}: missing {', '.join(m)}" for p, m in gaps) or "- none (clean)") + "\n")
    _write_report("wiki/agents/lint-report.md", "Lint report", body)
    return f"{n} notes scanned, {len(gaps)} gaps"


MODEL_ALIASES = {  # short pickers -> exact API model ids
    "claude-haiku-4-5": "claude-haiku-4-5-20251001",
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-8",
}

def anthropic_call(system, user, model="claude-opus-4-8", max_tokens=2000, key_override=None):
    """Raw-HTTP call to the Anthropic Messages API (keeps the server dependency-free)."""
    import urllib.request, urllib.error
    key = key_override or ANTHROPIC_KEY
    if not key:
        raise RuntimeError("no ANTHROPIC_API_KEY (add it to .env or set a per-agent key)")
    model = MODEL_ALIASES.get(model, model)
    body = json.dumps({
        "model": model, "max_tokens": max_tokens,
        "system": system + "\n\nRespond with only the final answer - no preamble, no meta-commentary.",
        "messages": [{"role": "user", "content": user}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body, method="POST",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        raise RuntimeError("API %s: %s" % (e.code, detail))
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()


def api_ollama_status():
    """Quick reachability check — returns {ok, url, status} without touching do_GET's urllib scope."""
    import urllib.request as _ureq
    base = (OLLAMA_URL or "http://localhost:11434").rstrip("/")
    try:
        with _ureq.urlopen(base + "/api/tags", timeout=2):
            return {"ok": True, "url": base, "status": "online"}
    except Exception as e:
        return {"ok": False, "url": base, "status": "offline", "error": str(e)}


def ollama_call(system, user, model=None, max_tokens=2000):
    """Raw HTTP call to a local Ollama instance. model = Ollama model name e.g. llama3.2, mistral."""
    import urllib.request, urllib.error
    mdl = model or OLLAMA_DEFAULT_MOD
    base = (OLLAMA_URL or "http://localhost:11434").rstrip("/")
    body = json.dumps({"model": mdl, "stream": False,
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user",   "content": user}],
                       "options": {"num_predict": max_tokens}}).encode("utf-8")
    req = urllib.request.Request(base + "/api/chat", data=body, method="POST",
                                 headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read())
    except urllib.error.URLError as e:
        raise RuntimeError("Ollama unreachable at %s — is it running? (%s)" % (base, e))
    return ((data.get("message") or {}).get("content") or "").strip()


# ──────────────────── Provider registry ─────────────────────────
PROVIDERS_FILE = os.path.join(BASE, "providers.json")
DEFAULT_PROVIDERS = [
    {"id": "anthropic", "name": "Anthropic", "type": "anthropic",
     "key": "", "url": "", "models": ["claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"]},
    {"id": "ollama",    "name": "Ollama (Local)", "type": "ollama",
     "key": "", "url": "http://localhost:11434", "models": ["llama3.2", "mistral", "qwen2.5", "phi4"]},
]

def load_providers():
    try:
        return json.load(open(PROVIDERS_FILE, encoding="utf-8"))
    except Exception:
        save_providers([dict(p) for p in DEFAULT_PROVIDERS])
        return [dict(p) for p in DEFAULT_PROVIDERS]

def save_providers(ps):
    with WRITE_LOCK:
        with open(PROVIDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(ps, f, indent=2)

PROVIDERS = load_providers()

# Seed the Anthropic key from .env into the Anthropic provider record so the UI shows it as set.
# The key is stored in providers.json (same machine, same user, local server only).
def _sync_env_key():
    changed = False
    for p in PROVIDERS:
        if p["id"] == "anthropic" and ANTHROPIC_KEY and not p.get("key"):
            p["key"] = ANTHROPIC_KEY
            changed = True
    if changed:
        save_providers(PROVIDERS)
_sync_env_key()

def _find_provider(pid):
    return next((p for p in PROVIDERS if p["id"] == pid), None)

def openai_compat_call(system, user, model, max_tokens, base_url, key):
    """OpenAI Chat Completions format — works for OpenAI, Groq, Together, Mistral, Deepseek, etc."""
    import urllib.request, urllib.error
    if not key:
        raise RuntimeError("no API key for this provider")
    url = base_url.rstrip("/") + "/v1/chat/completions"
    body = json.dumps({"model": model, "max_tokens": max_tokens,
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user",   "content": user}]}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
          headers={"Authorization": "Bearer " + key, "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError("API %s: %s" % (e.code, e.read().decode("utf-8","replace")[:300]))
    return ((data.get("choices") or [{}])[0].get("message", {}).get("content") or "").strip()

def call_provider(model_str, system, user, max_tokens=2000, key_override=None):
    """Route 'provider_id:model_name' to the right API. Falls back to anthropic for legacy bare model names."""
    if model_str and ":" in model_str:
        pid, model = model_str.split(":", 1)
    else:
        pid, model = "anthropic", (model_str or "claude-opus-4-8")

    prov = _find_provider(pid)
    key  = key_override or (prov.get("key") if prov else "") or ANTHROPIC_KEY
    ptype = (prov.get("type") if prov else "anthropic")
    url   = (prov.get("url") if prov else "") or ""

    if ptype == "anthropic":
        return anthropic_call(system, user, model=model, max_tokens=max_tokens, key_override=key or None)
    if ptype == "ollama":
        return ollama_call(system, user, model=model or OLLAMA_DEFAULT_MOD, max_tokens=max_tokens)
    if ptype in ("openai", "groq", "together", "openai-compatible"):
        return openai_compat_call(system, user, model, max_tokens, url or "https://api.openai.com", key)
    raise RuntimeError("Unknown provider type '%s' for provider '%s'" % (ptype, pid))

def _llm_call(model, system, user, max_tokens, key_override=None):
    """Thin shim — routes through the provider registry."""
    return call_provider(model, system, user, max_tokens, key_override)


# ─────────────────────── Web search ─────────────────────────────────
# Sources (priority order):
#   1. Brave Search API  — best real-web results; add a provider with type "brave" and your key
#                          Free plan (2 000 queries/month, no CC): api.search.brave.com
#   2. Wikipedia API     — always works, no key; solid for technical / reference queries
def web_search(query, max_results=5):
    """Return [{title, snippet, url}]. Tries Brave Search first, then Wikipedia."""
    import urllib.request, urllib.parse
    q   = urllib.parse.quote_plus((query or "")[:200])
    out = []

    # ── Brave Search (provider type="brave") ──────────────────────────
    brave_prov = next((p for p in PROVIDERS if p.get("type") == "brave"), None)
    brave_key  = (brave_prov or {}).get("key", "")
    if brave_key:
        try:
            req = urllib.request.Request(
                f"https://api.search.brave.com/res/v1/web/search?q={q}&count={max_results}",
                headers={"Accept": "application/json",
                         "X-Subscription-Token": brave_key})
            with urllib.request.urlopen(req, timeout=12) as r:
                data = json.loads(r.read())
            for item in (data.get("web", {}).get("results") or [])[:max_results]:
                out.append({"title": item.get("title", ""),
                            "snippet": (item.get("description") or "")[:300],
                            "url": item.get("url", "")})
            if out:
                return out
        except Exception:
            pass

    # ── Wikipedia API fallback (no key required) ──────────────────────
    try:
        wiki = (f"https://en.wikipedia.org/w/api.php?action=query&list=search"
                f"&srsearch={q}&format=json&utf8=1&srlimit={max_results}")
        req2 = urllib.request.Request(wiki,
               headers={"User-Agent": "NeuralVault/1.0 (github.com/SamuelNDCE/NeuralVault)"})
        with urllib.request.urlopen(req2, timeout=10) as r:
            data2 = json.loads(r.read())
        for item in data2.get("query", {}).get("search", [])[:max_results]:
            title = item.get("title", "")
            out.append({"title": title,
                        "snippet": re.sub(r'<[^>]+>', '', item.get("snippet", "")).strip()[:300],
                        "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))})
    except Exception:
        pass

    return out


def web_fetch(url, max_chars=3000):
    """Fetch a URL; tries Jina Reader first (clean text, no key), then raw HTML strip."""
    import urllib.request
    for fetch_url, hdrs in [
        ("https://r.jina.ai/" + str(url)[:500],
         {"User-Agent": "NeuralVault/1.0", "Accept": "text/plain"}),
        (str(url)[:500],
         {"User-Agent": "Mozilla/5.0 (compatible; NeuralVault/1.0)"}),
    ]:
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(fetch_url, headers=hdrs), timeout=15) as r:
                raw = r.read(65536).decode("utf-8", "replace")
            if "r.jina.ai" in fetch_url:
                return raw[:max_chars]
            raw = re.sub(r'(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>', ' ', raw)
            raw = re.sub(r'<[^>]+>', ' ', raw)
            raw = re.sub(r'[ \t]+', ' ', raw)
            raw = re.sub(r'\n\s*\n\s*\n', '\n\n', raw).strip()
            return raw[:max_chars]
        except Exception:
            continue
    return "[fetch failed]"


def agent_llm(a, command=None):
    """Reasoning agent: pulls vault neurons + optional live web search, calls LLM, deposits answer."""
    goal = (command or a.get("goal") or "").strip()
    if not goal:
        return "no goal set"
    model      = a.get("model")          or "ollama:qwen3.5:9b"
    max_tok    = int(a.get("max_tokens") or 2000)
    key        = (a.get("api_key") or "").strip() or None
    ctx_q      = (a.get("context_query") or goal).strip()
    sys_prompt = (a.get("system_prompt") or "").strip()
    do_web     = bool(a.get("web_search", True))   # enabled by default

    # ── Vault context: full content of top 3 hits + titles of next 5 ──
    q1 = api_search(ctx_q)
    q2 = api_search(ctx_q.split()[0]) if not q1 and ctx_q.split() else []
    hits = (q1 or q2)[:8]
    src_links = " · ".join(f"[[{h['title']}]]" for h in hits[:5])
    vault_ctx_parts = []
    for h in hits[:3]:
        with INDEX_LOCK:
            entry = NOTE_INDEX.get(h["id"])
        if entry and entry.get("content"):
            excerpt = entry["content"][:1200].strip()
            vault_ctx_parts.append(f"### {h['title']}\n{excerpt}")
        else:
            vault_ctx_parts.append(f"- {h['title']}: {h.get('snippet', '')[:300]}")
    for h in hits[3:8]:
        vault_ctx_parts.append(f"- {h['title']}: {h.get('snippet', '')[:120]}")
    vault_ctx = "\n\n".join(vault_ctx_parts) or "(vault empty so far)"

    # ── Web context ──
    web_section = ""
    if do_web:
        try:
            results = web_search(ctx_q[:150], max_results=4)
            if results:
                web_section = "\n".join(
                    f"- {r['title']}: {r['snippet']}" for r in results if r.get("title"))
        except Exception:
            pass

    default_sys = ("You are a reasoning agent inside Samuel's NeuralVault (personal knowledge graph). "
                   "Your output will be saved as a vault note and indexed for future retrieval. "
                   "Build on the vault context provided — reference what you find, identify gaps, and extend it. "
                   "Use [[wikilinks]] to link every relevant concept to its exact existing note title. "
                   "Do not repeat the goal verbatim. Write only the insight, analysis, or synthesis. "
                   "Be concise and specific. No preamble, no meta-commentary.")
    system = sys_prompt if sys_prompt else default_sys
    user   = (f"TASK:\n{goal}\n\n"
              f"VAULT CONTEXT:\n{vault_ctx}\n\n"
              + (f"WEB SEARCH RESULTS:\n{web_section}\n\n" if web_section else "")
              + "Write a focused, well-linked note that directly advances the task.")

    answer = _llm_call(model, system, user, max_tok, key_override=key)
    title  = goal[:60] + ("…" if len(goal) > 60 else "")
    note_body = (f"# {title}\n\n"
                 f"_by [[{a.get('name','agent')}]] ({model}) · {time.strftime('%Y-%m-%d %H:%M')}_\n\n"
                 f"{answer}\n"
                 + (f"\n\nSources: {src_links}\n" if src_links else ""))
    fname = "wiki/agent-inbox/" + slugify(a.get("name", "agent") + "-" + title) + ".md"
    _write_report(fname, title or "Agent note", note_body)
    return f"wrote '{title}' ({len(answer)} chars)"


def agent_linker(a=None):
    """Hive linker: writes wikilinks to notes that have fewer than 2 actual [[links]].
    Works directly from filesystem wikilink counts — never from scan() which includes
    virtual fallback edges and would always show 0 targets."""
    WIKILINK_RE2 = re.compile(r"\[\[([^\[\]]+)\]\]")
    MIN_LINKS = 2   # target: every note should have at least this many outgoing wikilinks

    # ── Step 1: collect raw file text and wikilinks per file ─────────
    file_raw        = {}   # nid -> file text
    file_wikilinks  = {}   # nid -> set of lowercase raw link targets in the file
    note_files      = {}   # nid -> absolute path

    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            if not fn.endswith(".md"):
                continue
            full = os.path.join(root, fn)
            rel  = os.path.relpath(full, BASE).replace("\\", "/")
            nid  = rel[:-3]
            try:
                txt = open(full, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            existing = {m.split("|")[0].split("#")[0].strip().lower()
                        for m in WIKILINK_RE2.findall(txt) if m.strip()}
            file_raw[nid]       = txt
            file_wikilinks[nid] = existing
            note_files[nid]     = full

    # ── Step 2: get node metadata + real graph degree ────────────────
    g = scan()
    node_meta = {n["id"]: n for n in g["nodes"] if n.get("t") not in ("ext", None)}

    # Build real degree: count edges but exclude virtual fallback edges
    virtual_keys = {tuple(sorted(k)) for k in g.get("virtual_edges", [])}
    real_degree  = Counter()
    for e in g["edges"]:
        key = tuple(sorted([e[0], e[1]]))
        if key not in virtual_keys:
            real_degree[e[0]] += 1; real_degree[e[1]] += 1

    # ── Step 3: targets = notes whose real graph degree < MIN_LINKS ───
    targets = [(nid, node_meta[nid]) for nid in note_files
               if nid in node_meta
               and real_degree[nid] < MIN_LINKS]

    STOP = {"the","a","an","in","of","and","or","is","to","for","on","at","my","by","be","as",
            "it","its","this","that","with","from","are","was","has","have","will","not","but",
            "s","re","ve","ll","d","m"}

    def words_of(s):
        return set(re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).split()) - STOP

    def tags_of(txt):
        m2 = FM_RE.match(txt)
        if not m2: return set()
        raw = field(m2.group(1), "tags")
        return {t.strip().strip("[]").lower() for t in re.split(r"[,\s]+", raw) if t.strip()}

    linked = 0
    for nid, node in targets:
        fp = note_files[nid]
        try:
            txt = open(fp, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue

        existing_lower = file_wikilinks.get(nid, set())  # already-linked titles (lower)
        label_words    = words_of(node.get("label", ""))
        body_m         = FM_RE.match(txt)
        body_lower     = (txt[body_m.end():] if body_m else txt).lower()
        node_tags      = tags_of(txt)
        scored         = {}

        for other_nid, other in node_meta.items():
            if other_nid == nid or not other.get("label") or other.get("t") == "ext":
                continue
            other_lbl = other.get("label", "")
            if other_lbl.lower() in existing_lower:
                continue   # already linked
            score = 0
            score += len(label_words & words_of(other_lbl)) * 3   # title word overlap
            if other_lbl.lower() in body_lower:
                score += 4                                          # body-text mention
            ofp_rel = other.get("file", "")
            try:
                ofp = (os.path.join(VAULT_ROOT or BASE, ofp_rel) if (VAULT_ROOT and "/" in ofp_rel)
                       else os.path.join(BASE, ofp_rel))
                if node_tags & tags_of(open(ofp, encoding="utf-8", errors="ignore").read()):
                    score += 2                                      # shared tags
            except Exception:
                pass
            if other.get("t") == node.get("t"):
                score += 1                                          # same type
            if score > 0:
                scored[other_lbl] = score

        need = MIN_LINKS - len(existing_lower)
        if scored:
            candidates = [lbl for lbl, _ in sorted(scored.items(), key=lambda x: -x[1])][:max(need, 3)]
        else:
            # fallback: nearest hubs / concepts not already linked
            candidates = [n["label"] for n in g["nodes"]
                          if n.get("t") in ("hub", "concept")
                          and n["id"] != nid
                          and n.get("label")
                          and n["label"].lower() not in existing_lower][:3]

        candidates = [c for c in candidates if c.lower() not in existing_lower][:4]
        if not candidates:
            continue

        links = " · ".join(f"[[{c}]]" for c in candidates)
        with WRITE_LOCK:
            with open(fp, "a", encoding="utf-8") as f:
                f.write(f"\n\nRelated: {links}\n")
        linked += 1

    _write_report("wiki/agents/linker-report.md", "Linker report",
                  f"# Linker report\n\n{time.strftime('%Y-%m-%d %H:%M')}\n\n"
                  f"Weak notes (< {MIN_LINKS} wikilinks): {len(targets)} — linked this run: {linked}\n")
    return f"linked {linked}/{len(targets)} weak notes"


def agent_cleanup(a=None):
    """Prunes stale agent-inbox stubs and empty notes so they stop showing up as noise neurons."""
    deleted = []
    now_ts = time.time()
    INBOX = os.path.join(BASE, "wiki", "agent-inbox")
    SAFE_TYPES = {"hub", "concept", "lesson", "moc"}

    # 1. Prune old stubs from agent-inbox (>14 days old, body < 400 chars)
    if os.path.isdir(INBOX):
        for fn in sorted(os.listdir(INBOX)):
            if not fn.endswith(".md"):
                continue
            fp = os.path.join(INBOX, fn)
            try:
                raw = open(fp, encoding="utf-8", errors="ignore").read()
                m = FM_RE.match(raw)
                body = raw[m.end():].strip() if m else raw.strip()
                age_days = (now_ts - os.path.getmtime(fp)) / 86400
                if age_days > 14 and len(body) < 400:
                    os.remove(fp)
                    deleted.append(f"inbox/{fn} ({age_days:.0f}d, {len(body)}c)")
            except Exception:
                pass

    # 2. Remove truly empty notes outside wiki/agents (body < 80 chars, not hub/concept/lesson/moc)
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        rel_root = os.path.relpath(root, BASE).replace("\\", "/")
        if rel_root.startswith("wiki/agents"):
            continue
        for fn in files:
            if not fn.endswith(".md"):
                continue
            fp = os.path.join(root, fn)
            try:
                raw = open(fp, encoding="utf-8", errors="ignore").read()
                m = FM_RE.match(raw)
                fm_text = m.group(1) if m else ""
                body = raw[m.end():].strip() if m else raw.strip()
                if (field(fm_text, "type") or "") in SAFE_TYPES:
                    continue
                if len(body) < 80:
                    os.remove(fp)
                    deleted.append(f"empty: {os.path.relpath(fp, BASE).replace(chr(92), '/')}")
            except Exception:
                pass

    lines = "\n".join(f"- {d}" for d in deleted) or "- none"
    body = (f"# Cleanup report\n\n{time.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Pruned {len(deleted)} redundant notes.\n\n## Deleted\n{lines}\n")
    _write_report("wiki/agents/cleanup-report.md", "Cleanup report", body)
    return f"pruned {len(deleted)} notes"


def agent_vault_keeper(a=None):
    """Runs vault maintenance sub-tasks on their individual schedules.
    Each task has its own interval stored in a['tasks'][key]['interval'].
    Only runs a task if enough time has elapsed since its last_run."""
    _VK_SUBTASKS = [
        ("stats",        agent_stats,        300),
        ("curator",      agent_curator,      3600),
        ("linter",       agent_linter,       3600),
        ("linker",       agent_linker,       1800),
        ("cleanup",      agent_cleanup,      7200),
        ("note-updater", agent_note_updater, 86400),
    ]
    now = time.time()
    tasks_cfg = (a or {}).get("tasks") or {}
    results = []
    for key, fn, default_iv in _VK_SUBTASKS:
        cfg = tasks_cfg.get(key) or {}
        interval = int(cfg.get("interval") or default_iv)
        last_run = float(cfg.get("last_run") or 0)
        if now - last_run >= interval:
            try:
                res = fn(a)
                results.append(res)
            except Exception as e:
                results.append(f"{key} error: {e}")
            if a is not None:
                if not isinstance(a.get("tasks"), dict):
                    a["tasks"] = {}
                a["tasks"].setdefault(key, {})
                a["tasks"][key]["last_run"] = now
                a["tasks"][key]["interval"] = interval
    return (" · ".join(results)) if results else "all tasks up to date"


def agent_session(a=None):
    """Passive agent — stamped externally by Claude Code sessions, never auto-runs."""
    return "session agent — updated by Claude Code activity"


def agent_note_updater(a=None):
    """Scan concept/entity/lesson notes older than STALE_DAYS, find recent observations that
    mention them, call LLM to generate an updated note body, and save it back to the vault."""
    STALE_DAYS    = 7
    TARGET_TYPES  = {"concept", "entity", "lesson", "pattern", "org", "system", "person"}
    SKIP_PREFIXES = ("wiki/agent-", "wiki/agents/", "wiki/codegraph/")
    today         = time.time()
    today_str     = time.strftime("%Y-%m-%d")

    # ── 1. Collect stale candidates from the in-memory index ──────────
    stale = []
    with INDEX_LOCK:
        snapshot = list(NOTE_INDEX.items())
    for nid, entry in snapshot:
        if entry.get("type") not in TARGET_TYPES:
            continue
        if any(nid.startswith(p) for p in SKIP_PREFIXES):
            continue
        age_days = (today - entry.get("mtime", 0)) / 86400
        if age_days > STALE_DAYS:
            stale.append((age_days, nid, entry))

    stale.sort(reverse=True)  # oldest first
    candidates = stale[:12]   # process up to 12 per run

    model    = (a.get("model") if a else None) or "ollama:qwen3.5:9b"
    max_tok  = int((a.get("max_tokens") if a else None) or 1600)
    key      = (a.get("api_key") if a else None) or None

    updated_count = 0
    skipped_count = 0
    report_lines  = []

    for age_days, nid, entry in candidates:
        title = entry.get("title") or nid.split("/")[-1]

        # ── 2. Find recent observations (< 14 days) that mention this note ──
        hits = api_search(title)[:6]
        recent_parts = []
        for h in hits:
            if h["id"] == nid:
                continue
            with INDEX_LOCK:
                h_entry = NOTE_INDEX.get(h["id"])
            if h_entry and (today - h_entry.get("mtime", 0)) / 86400 < 14:
                excerpt = h_entry.get("content", "")[:700].strip()
                recent_parts.append(f"### {h['title']}\n{excerpt}")

        if not recent_parts:
            skipped_count += 1
            report_lines.append(f"- {title} ({age_days:.0f}d) — no recent context, skipped")
            continue

        # ── 3. Read the current note from disk ────────────────────────
        full_path = os.path.join(BASE, nid + ".md")
        if not os.path.exists(full_path):
            report_lines.append(f"- {title} — file missing on disk, skipped")
            continue
        try:
            old_text = open(full_path, encoding="utf-8", errors="ignore").read()
        except Exception:
            report_lines.append(f"- {title} — read error, skipped")
            continue

        current_body = entry.get("content", old_text)[:2000]
        recent_ctx   = "\n\n".join(recent_parts[:3])

        # ── 4. LLM call ───────────────────────────────────────────────
        system = ("You are a vault maintenance agent. Your task is to update a knowledge note "
                  "using newer observations. Return ONLY the updated Markdown body — no frontmatter. "
                  "Keep the existing structure. If information is contradicted, use ~~strikethrough~~. "
                  "Add a small '## Updated " + today_str + "' section at the bottom listing what changed.")
        user   = (f"EXISTING NOTE ({age_days:.0f} days old):\n{current_body}\n\n"
                  f"RECENT OBSERVATIONS:\n{recent_ctx}\n\n"
                  "Produce the updated note body. Be concise — preserve what is still accurate.")

        updated_body = _llm_call(model, system, user, max_tok, key_override=key)
        if not updated_body or len(updated_body) < 80:
            report_lines.append(f"- {title} — LLM returned too-short response, skipped")
            continue

        # ── 5. Re-write the file with updated frontmatter + body ──────
        fm_match = FM_RE.match(old_text)
        if fm_match:
            fm = fm_match.group(1)
            fm = re.sub(r"^updated\s*:.*$", f"updated: {today_str}", fm, flags=re.MULTILINE)
            if not re.search(r"^updated\s*:", fm, re.MULTILINE):
                fm += f"\nupdated: {today_str}"
            new_text = f"---\n{fm}\n---\n\n{updated_body}\n"
        else:
            new_text = updated_body + "\n"

        safe_path = _safe_under(full_path)
        if not safe_path:
            report_lines.append(f"- {title} — path outside vault, skipped")
            continue
        try:
            with WRITE_LOCK:
                open(safe_path, "w", encoding="utf-8").write(new_text)
            _index_note(safe_path)
            _cache_invalidate()
            updated_count += 1
            report_lines.append(f"- {title} ({age_days:.0f}d) — updated")
        except Exception as exc:
            report_lines.append(f"- {title} — write failed: {exc}")

    summary = (f"Scanned {len(stale)} stale notes · candidates {len(candidates)} "
               f"· updated {updated_count} · skipped {skipped_count}")
    report_body = f"# Note Freshness Report — {today_str}\n\n{summary}\n\n" + "\n".join(report_lines)
    _write_report("wiki/agents/freshness-report.md", "Note Freshness Report", report_body)
    return summary


BEHAVIORS = {"stats": agent_stats, "curator": agent_curator, "linter": agent_linter,
             "linker": agent_linker, "cleanup": agent_cleanup, "llm": agent_llm,
             "vault-keeper": agent_vault_keeper, "session": agent_session,
             "note-updater": agent_note_updater}


def _deposit_agent_log(a, result, command=None):
    """Write every agent run as a neuron in wiki/agent-logs/ so runs are searchable in the vault."""
    name    = a.get("name", a.get("id", "agent"))
    atype   = a.get("type", "unknown")
    day     = time.strftime("%Y-%m-%d")
    stamp   = time.strftime("%H:%M")
    is_err  = result.startswith("error:")
    status  = "error" if is_err else "ok"

    # Append to the daily rolling log for this agent
    log_rel = f"wiki/agent-logs/{day}-{slugify(name)}.md"
    log_full = _safe_under(os.path.join(BASE, log_rel))
    if log_full:
        os.makedirs(os.path.dirname(log_full), exist_ok=True)
        if not os.path.exists(log_full):
            fm = (f"---\ntitle: {name} log {day}\ntype: observation\nstatus: seed\n"
                  f"source: agent-log\ncreated: {day}\nupdated: {day}\n"
                  f"tags: [wiki/agents, agent-log, {atype}]\n---\n\n"
                  f"# {name} — run log {day}\n\n")
            with WRITE_LOCK:
                open(log_full, "w", encoding="utf-8").write(fm)
        entry = (f"\n## {stamp}  `{status}`\n"
                 + (f"Command: _{command}_\n\n" if command else "")
                 + f"{result}\n")
        with WRITE_LOCK:
            open(log_full, "a", encoding="utf-8").write(entry)


def run_agent(a, command=None):
    fn = BEHAVIORS.get(a.get("type"))
    try:
        if command and a.get("type") == "llm":
            res = agent_llm(a, command=command)
        else:
            res = fn(a) if fn else "unknown type '%s'" % a.get("type")
    except Exception as e:
        res = "error: " + str(e)
    a["last_run"] = int(time.time()); a["last_result"] = res
    tag = (a.get("name", a.get("id")) + (" (cmd)" if command else ""))
    AGENT_LOG.appendleft({"t": int(time.time() * 1000), "agent": tag, "result": res})
    save_agents(AGENTS)
    try:
        _deposit_agent_log(a, res, command=command)
    except Exception:
        pass
    return res


def scheduler_loop():
    while True:
        now = time.time()
        for a in list(AGENTS):
            try:
                if a.get("enabled") and now - a.get("last_run", 0) >= a.get("interval", 600):
                    run_agent(a)
            except Exception:
                pass
        time.sleep(8)


threading.Thread(target=scheduler_loop, daemon=True).start()

def _startup_vault_keeper():
    """Run a full vault-keeper pass at boot: stats, curation, linting, linking."""
    time.sleep(12)
    try:
        agent_vault_keeper()
    except Exception:
        pass
threading.Thread(target=_startup_vault_keeper, daemon=True).start()

# Build in-memory index immediately (no sleep — index must be ready before first search)
threading.Thread(target=_build_index, daemon=True).start()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"   # enables keep-alive; eliminates per-request TCP setup

    def log_message(self, *a):
        pass

    def _auth_ok(self):
        """Returns True if no token is configured (open), or if the caller supplies the right one."""
        if not NV_TOKEN:
            return True
        return self.headers.get("X-NV-Token", "") == NV_TOKEN

    def _send(self, code, body, ctype, cache=None):
        raw = body if isinstance(body, bytes) else body.encode("utf-8")
        # HTML pages use no-cache (allows prerender/prefetch); API uses no-store
        if cache is None:
            cache = "no-cache" if ctype.startswith("text/html") else "no-store"
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", len(raw))
        self.send_header("Cache-Control", cache)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, separators=(",", ":")), "application/json")

    def do_GET(self):
        parts = urllib.parse.urlparse(self.path)
        path = parts.path
        qs = urllib.parse.parse_qs(parts.query)
        if path in ("/graph.json", "/api/graph"):
            try:
                self._json(200, scan())
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        if path == "/state":                       # load persisted learned weights
            self._send(200, load_state(), "application/json")
            return
        if path == "/storage":                     # how much space the brain takes
            self._json(200, storage_report()); return
        if path == "/api/activity":                # visualization: fire-rate feed for the neural map
            self._json(200, get_activity()); return
        if path == "/api/search":                  # agents: find notes
            record_activity(1.0)
            self._json(200, {"results": api_search(qs.get("q", [""])[0])}); return
        if path == "/api/context":                 # compact working-memory for Claude sessions
            record_activity(2.0)                   # heavyweight: counts double
            self._send(200, api_context(), "text/plain; charset=utf-8"); return
        if path == "/api/ask":                      # the NeuralVault voice (retrieval)
            record_activity(1.0)
            self._json(200, api_ask(qs.get("q", [""])[0])); return
        if path == "/api/note":                    # agents: read a note
            record_activity(1.0)
            n = api_get_note(qs.get("id", [""])[0])
            self._json(200 if n else 404, n or {"error": "not found"}); return
        if path == "/api/peek":                    # quick first-400-chars preview of a note
            record_activity(0.5)                   # lightweight: half-weight
            chars = int(qs.get("chars", ["400"])[0])
            p = api_peek(qs.get("id", [""])[0], chars=max(50, min(chars, 2000)))
            self._json(200 if p else 404, p or {"error": "not found"}); return
        if path == "/api/config":                   # server config (masked)
            self._json(200, {
                "key_set": bool(ANTHROPIC_KEY), "key_last4": ANTHROPIC_KEY[-4:] if len(ANTHROPIC_KEY) >= 4 else "",
                "token_set": bool(NV_TOKEN), "token_last4": NV_TOKEN[-4:] if len(NV_TOKEN) >= 4 else "",
                "ollama_url": OLLAMA_URL, "ollama_model": OLLAMA_DEFAULT_MOD,
            }); return
        if path == "/api/providers":                # list providers (keys masked)
            masked = []
            for p in PROVIDERS:
                mp = dict(p); k = mp.get("key","")
                mp["key_set"] = bool(k); mp["key_last4"] = k[-4:] if len(k) >= 4 else ""; mp["key"] = ""
                masked.append(mp)
            self._json(200, {"providers": masked}); return
        if path == "/api/providers/test":           # test a provider's key with a tiny call
            qs2 = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            pid = qs2.get("id", ["anthropic"])[0]
            prov = _find_provider(pid)
            if not prov:
                self._json(404, {"ok": False, "error": "provider not found"}); return
            try:
                result = call_provider(
                    pid + ":claude-haiku-4-5-20251001" if prov.get("type") == "anthropic"
                    else (pid + ":" + (prov.get("models") or [""])[0]),
                    "You are a test.", "Reply with exactly: OK", 10)
                self._json(200, {"ok": True, "reply": result[:80]}); return
            except Exception as e:
                self._json(200, {"ok": False, "error": str(e)[:300]}); return
        if path == "/api/web/search":               # live web search (DuckDuckGo, no key)
            q = qs.get("q", [""])[0]
            try:
                results = web_search(q, max_results=int(qs.get("n", ["6"])[0]))
            except Exception as e:
                results = [{"title": "error", "snippet": str(e), "url": ""}]
            self._json(200, {"query": q, "results": results}); return
        if path == "/api/web/fetch":               # fetch + extract text from a URL
            url = qs.get("url", [""])[0]
            self._json(200, {"url": url, "text": web_fetch(url)}); return
        if path.startswith("/api/system"):         # real-time system resource metrics (never cached)
            try:
                self._json(200, api_system_metrics())
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        if path.startswith("/api/graph/stats"):    # richer graph stats (type breakdown, hubs, recent)
            try:
                self._json(200, api_graph_stats())
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        if path == "/api/ollama-status":            # quick Ollama reachability check
            self._json(200, api_ollama_status())
            return
        if path == "/api/agents":                   # list agents
            self._json(200, {"agents": AGENTS}); return
        if path == "/api/agents/log":               # recent activity
            self._json(200, {"log": list(AGENT_LOG)}); return
        if path == "/agents":                       # old landing page removed -> control panel
            self.send_response(302); self.send_header("Location", "/manage"); self.end_headers(); return
        if path == "/manage":                       # agent control dashboard
            try:
                self._send(200, open(os.path.join(BASE, "manage.html"), "rb").read(), "text/html; charset=utf-8")
            except FileNotFoundError:
                self._send(404, "manage.html not found", "text/plain")
            return
        try:
            self._send(200, open(HTML_FILE, "rb").read(), "text/html; charset=utf-8")
        except FileNotFoundError:
            self._send(404, "neural map HTML not found next to this script", "text/plain")

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        ln = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(ln).decode("utf-8") if ln else "{}"
        if path == "/api/config":                  # update API key / auth token (writes .env)
            if not self._auth_ok():
                self._json(401, {"error": "unauthorized"}); return
            try:
                p = json.loads(body)
            except Exception:
                self._json(400, {"error": "invalid json"}); return
            global ANTHROPIC_KEY, NV_TOKEN, OLLAMA_URL, OLLAMA_DEFAULT_MOD
            if "key" in p and p["key"].strip():
                ANTHROPIC_KEY = p["key"].strip(); update_env_var("ANTHROPIC_API_KEY", ANTHROPIC_KEY)
            if "token" in p:
                NV_TOKEN = p["token"].strip(); update_env_var("NEURALVAULT_TOKEN", NV_TOKEN)
            if "ollama_url" in p:
                OLLAMA_URL = (p["ollama_url"] or "http://localhost:11434").strip()
                update_env_var("OLLAMA_URL", OLLAMA_URL)
            if "ollama_model" in p and p["ollama_model"].strip():
                OLLAMA_DEFAULT_MOD = p["ollama_model"].strip()
                update_env_var("OLLAMA_MODEL", OLLAMA_DEFAULT_MOD)
            self._json(200, {"ok": True, "key_set": bool(ANTHROPIC_KEY), "token_set": bool(NV_TOKEN),
                             "ollama_url": OLLAMA_URL, "ollama_model": OLLAMA_DEFAULT_MOD}); return
        if path.startswith("/api/providers"):       # provider management
            if not self._auth_ok():
                self._json(401, {"error": "unauthorized"}); return
            try:
                p = json.loads(body)
            except Exception:
                self._json(400, {"error": "invalid json"}); return
            if path == "/api/providers/delete":
                pid = p.get("id","")
                if pid in ("anthropic","ollama"):
                    self._json(400, {"error": "cannot delete built-in providers"}); return
                PROVIDERS[:] = [x for x in PROVIDERS if x.get("id") != pid]
                save_providers(PROVIDERS)
                self._json(200, {"ok": True}); return
            # upsert
            pid = p.get("id") or re.sub(r"[^a-z0-9]","",p.get("name","provider").lower())[:20]
            existing = next((x for x in PROVIDERS if x.get("id") == pid), None)
            if existing:
                for k in ("name","type","url","models"):
                    if k in p: existing[k] = p[k]
                if p.get("key","").strip():  # only update key if provided
                    existing["key"] = p["key"].strip()
            else:
                PROVIDERS.append({"id": pid, "name": p.get("name","Provider"),
                                  "type": p.get("type","openai-compatible"),
                                  "key": p.get("key","").strip(), "url": p.get("url",""),
                                  "models": p.get("models",[])})
            _sync_env_key(); save_providers(PROVIDERS)
            self._json(200, {"ok": True, "id": pid}); return
        # ── protect all other write endpoints ──────────────────────────────────────
        if path != "/state" and not self._auth_ok():
            self._json(401, {"error": "unauthorized"}); return
        if path == "/state":                       # save learned weights (compressed)
            stats = save_state(body)
            self._json(200 if stats else 400, stats or {"ok": False}); return
        if path.startswith("/api/agents"):         # agent management
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            aid = qs.get("id", [""])[0]
            def find(i): return next((x for x in AGENTS if x.get("id") == i), None)
            if path == "/api/agents/run":
                a = find(aid); self._json(200 if a else 404, {"ok": bool(a), "result": run_agent(a) if a else "not found"}); return
            if path == "/api/agents/toggle":
                a = find(aid)
                if a: a["enabled"] = not a.get("enabled"); save_agents(AGENTS)
                self._json(200 if a else 404, {"ok": bool(a), "enabled": a.get("enabled") if a else None}); return
            if path == "/api/agents/delete":
                before = len(AGENTS); AGENTS[:] = [x for x in AGENTS if x.get("id") != aid]; save_agents(AGENTS)
                self._json(200, {"ok": len(AGENTS) < before}); return
            if path == "/api/agents/command":      # one-off instruction dispatched to agent(s)
                try:
                    p = json.loads(body)
                except Exception:
                    self._json(400, {"error": "invalid json"}); return
                cmd = (p.get("prompt") or "").strip()
                if not cmd:
                    self._json(400, {"error": "empty prompt"}); return
                tid = p.get("id", "")
                targets = [x for x in AGENTS if x.get("type") == "llm"] if tid == "all" else [t for t in [find(tid)] if t]
                if not targets:
                    self._json(404, {"ok": False, "error": "no llm agent to run this on"}); return
                results = [{"agent": t.get("name"), "result": run_agent(t, command=cmd)} for t in targets]
                self._json(200, {"ok": True, "results": results}); return
            # upsert (create / edit)
            try:
                p = json.loads(body)
            except Exception:
                self._json(400, {"error": "invalid json"}); return
            existing = find(p.get("id", ""))
            EDITABLE = ("name","role","type","interval","enabled","goal","model",
                        "system_prompt","context_query","max_tokens","api_key","web_search")
            if existing:
                existing.update({k: p[k] for k in EDITABLE if k in p})
            else:
                nid = slugify(p.get("name", "agent")) + "-" + str(int(time.time()))[-4:]
                AGENTS.append({"id": nid, "name": p.get("name","Agent"), "role": p.get("role",""),
                               "type": p.get("type","stats"), "interval": int(p.get("interval",600)),
                               "enabled": bool(p.get("enabled",False)), "goal": p.get("goal",""),
                               "model": p.get("model","claude-opus-4-8"),
                               "system_prompt": p.get("system_prompt",""), "context_query": p.get("context_query",""),
                               "max_tokens": int(p.get("max_tokens",2000)), "api_key": p.get("api_key",""),
                               "last_run": 0, "last_result": ""})
            save_agents(AGENTS)
            self._json(200, {"ok": True, "agents": AGENTS}); return
        if path == "/api/save":                    # editor: overwrite an existing note
            try:
                payload = json.loads(body)
            except Exception:
                self._json(400, {"error": "invalid json"}); return
            res = api_save(payload)
            self._json(200 if res and res.get("ok") else 400, res or {"error": "id + content required"}); return
        if path in ("/api/note", "/api/observe"):  # agents: write into the brain
            record_activity(3.0)                   # writes are the heaviest signal
            try:
                payload = json.loads(body)
            except Exception:
                self._json(400, {"error": "invalid json"}); return
            if path == "/api/observe":             # quick episodic capture — routes by type
                _obs_type = payload.get("type") or "observation"
                _obs_folder = payload.get("folder") or FOLDER_BY_TYPE.get(_obs_type, "wiki/agent-inbox")
                _obs_tags = payload.get("tags") or ["wiki/agent", _obs_type]
                payload = {"title": payload.get("title") or (_obs_type + " " + time.strftime("%Y-%m-%d %H:%M")),
                           "content": payload.get("content") or payload.get("text") or "",
                           "type": _obs_type, "folder": _obs_folder,
                           "tags": _obs_tags,
                           "status": payload.get("status") or "seed",
                           "links": payload.get("links") or []}
            res = api_create_note(payload)
            if path == "/api/observe":   # stamp Claude session agent so it shows live in the canvas
                _snip = (payload.get("content") or "")[:120].replace("\n", " ").strip()
                for _ag in AGENTS:
                    if _ag.get("type") == "session":
                        _ag["last_run"] = int(time.time())
                        _ag["last_result"] = _snip or "observed"
                        save_agents(AGENTS)
                        break
            self._json(200 if res else 400, res or {"error": "title or content required"}); return
        if path == "/api/fetch":                   # fetch a web URL and save as a source note
            try:
                payload = json.loads(body)
            except Exception:
                self._json(400, {"error": "invalid json"}); return
            url_val = (payload.get("url") or "").strip()
            if not url_val:
                self._json(400, {"error": "url required"}); return
            scheme = urllib.parse.urlparse(url_val).scheme.lower()
            if scheme not in ("http", "https"):
                self._json(400, {"error": "only http/https URLs are supported"}); return
            try:
                res = api_fetch_to_vault(payload)
                self._json(200, res)
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        self._json(404, {"error": "not found"})


if __name__ == "__main__":
    g = scan()
    print(f"NeuralVault server  ->  http://localhost:{PORT}/")
    print(f"Scanning: {BASE}")
    print(f"Graph: {g['count']['nodes']} neurons, {g['count']['edges']} synapses (re-scanned on every poll)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
