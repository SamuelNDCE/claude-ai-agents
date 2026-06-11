import { createServer } from 'http'
import { watch } from 'chokidar'
import { readFileSync, writeFileSync, mkdirSync, existsSync, realpathSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join, basename, sep } from 'path'
import { randomUUID } from 'crypto'
import matter from 'gray-matter'
import open from 'open'

const SESSION_TOKEN = randomUUID().replace(/-/g, '')

const __dirname = dirname(fileURLToPath(import.meta.url))
const TOKENS_FILE = join(__dirname, '.tokens.json')
const VAULT = process.env.VAULT_PATH || String.raw`C:\Users\Futur\Documents\AiWorkspace\NeuralVault\sample-vault`
const OUTBOX = join(VAULT, 'wiki', 'agent-inbox', 'social', 'outbox')
const LOG_FILE = join(VAULT, 'wiki', 'logs', 'perpetual-technologies.md')
const PORT = 3001

mkdirSync(OUTBOX, { recursive: true })

// ── Tokens ──────────────────────────────────────────────────────────────────

function loadTokens() {
  if (!existsSync(TOKENS_FILE)) { console.error('No .tokens.json — run: npm run auth'); process.exit(1) }
  return JSON.parse(readFileSync(TOKENS_FILE, 'utf8'))
}

async function refreshIfNeeded(tokens) {
  if (Date.now() < tokens.expires_at - 7 * 86_400_000) return tokens
  if (!tokens.refresh_token) { console.error('Token expired — run: npm run auth'); process.exit(1) }
  const res = await fetch('https://www.linkedin.com/oauth/v2/accessToken', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ grant_type: 'refresh_token', refresh_token: tokens.refresh_token,
      client_id: process.env.LINKEDIN_CLIENT_ID, client_secret: process.env.LINKEDIN_CLIENT_SECRET }),
  })
  const data = await res.json()
  if (!data.access_token) { console.error('Refresh failed:', data); process.exit(1) }
  tokens.access_token = data.access_token
  tokens.expires_at = Date.now() + (data.expires_in ?? 5_184_000) * 1000
  if (data.refresh_token) tokens.refresh_token = data.refresh_token
  writeFileSync(TOKENS_FILE, JSON.stringify(tokens, null, 2))
  return tokens
}

// ── LinkedIn API ─────────────────────────────────────────────────────────────

async function postToLinkedIn(text, tokens) {
  const res = await fetch('https://api.linkedin.com/v2/ugcPosts', {
    method: 'POST',
    headers: { Authorization: `Bearer ${tokens.access_token}`, 'Content-Type': 'application/json',
      'X-Restli-Protocol-Version': '2.0.0' },
    body: JSON.stringify({
      author: tokens.person_urn, lifecycleState: 'PUBLISHED',
      specificContent: { 'com.linkedin.ugc.ShareContent': {
        shareCommentary: { text }, shareMediaCategory: 'NONE' } },
      visibility: { 'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC' },
    }),
  })
  if (!res.ok) throw new Error(`LinkedIn API ${res.status}: ${await res.text()}`)
  const postId = res.headers.get('x-restli-id') || ''
  return postId ? `https://www.linkedin.com/feed/update/${encodeURIComponent(postId)}/` : 'https://www.linkedin.com/feed/'
}

// ── NV log ───────────────────────────────────────────────────────────────────

function appendToLog(line) {
  if (!existsSync(LOG_FILE)) return
  const log = readFileSync(LOG_FILE, 'utf8')
  const date = new Date().toISOString().slice(0, 10)
  writeFileSync(LOG_FILE, log.replace(/^(# .+\n)/, `$1\n## ${date} — LinkedIn published\n\n${line}\n`))
}

// ── Preview HTML ─────────────────────────────────────────────────────────────

function previewHtml(filename, content, token) {
  const escaped = JSON.stringify(content)
  return `<!DOCTYPE html><html><head><meta charset="utf-8">
<title>LinkedIn Preview</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,system-ui,sans-serif;background:#1b1f23;color:#e0e0e0;padding:2rem;min-height:100vh}
.wrap{max-width:600px;margin:0 auto}
h1{font-size:.75rem;color:#70b5f9;letter-spacing:.08em;text-transform:uppercase;margin-bottom:1.5rem}
.card{background:#1d2226;border:1px solid #38434f;border-radius:8px;padding:1.25rem;margin-bottom:1rem}
.label{font-size:.7rem;color:#888;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.6rem}
#preview{white-space:pre-wrap;word-break:break-word;font-size:.925rem;line-height:1.55;color:#e0e0e0}
.cutoff{margin-top:.5rem;font-size:.75rem;color:#f59e0b}
textarea{width:100%;min-height:180px;background:#0f1923;border:1px solid #38434f;border-radius:4px;
  color:#e0e0e0;font-size:.9rem;line-height:1.55;padding:.75rem;resize:vertical;font-family:inherit}
textarea:focus{outline:none;border-color:#70b5f9}
.meta{display:flex;justify-content:space-between;margin-top:.35rem;font-size:.75rem;color:#888}
.over{color:#ef4444}.warn{color:#f59e0b}
.btns{display:flex;gap:.75rem;margin-top:1rem}
button{padding:.6rem 1.4rem;border:none;border-radius:20px;font-size:.875rem;font-weight:600;cursor:pointer;transition:opacity .15s}
.post{background:#0a66c2;color:#fff}.post:hover{opacity:.85}.post:disabled{background:#333;color:#666;cursor:not-allowed}
.cancel{background:transparent;color:#aaa;border:1px solid #38434f}.cancel:hover{background:#38434f}
.msg{margin-top:1rem;padding:.75rem 1rem;border-radius:6px;font-size:.875rem;display:none}
.ok{background:#14532d;color:#86efac;display:block}.err{background:#7f1d1d;color:#fca5a5;display:block}
</style></head><body><div class="wrap">
<h1>LinkedIn Post Preview &nbsp;·&nbsp; ${filename}</h1>
<div class="card"><div class="label">How it looks in the feed</div>
<div id="preview"></div><div class="cutoff" id="co"></div></div>
<div class="card"><div class="label">Edit before posting</div>
<textarea id="ed" oninput="sync()"></textarea>
<div class="meta"><span id="cc">0 / 3000</span><span>first ~210 chars show before "see more"</span></div></div>
<div class="btns">
<button class="post" id="pb" onclick="doPost()">Post to LinkedIn</button>
<button class="cancel" onclick="doCancel()">Cancel</button></div>
<div class="msg" id="msg"></div></div>
<script>
const FILE=${JSON.stringify(filename)}
const TOK=${JSON.stringify(token)}
const ed=document.getElementById('ed')
ed.value=${escaped}
sync()
function sync(){
  const t=ed.value,n=t.length
  document.getElementById('preview').textContent=t
  const cc=document.getElementById('cc')
  cc.textContent=n+' / 3000'
  cc.className=n>3000?'over':n>2700?'warn':''
  document.getElementById('pb').disabled=n>3000||n===0
  document.getElementById('co').textContent=n>210?'↑ "see more" appears around character 210':''
}
async function doPost(){
  const pb=document.getElementById('pb')
  pb.disabled=true;pb.textContent='Posting...'
  const r=await fetch('/approve/'+encodeURIComponent(FILE)+'?t='+TOK,{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify({text:ed.value})})
  const d=await r.json(),m=document.getElementById('msg')
  if(d.ok){m.className='msg ok';m.textContent='✓ Posted! ';const a=document.createElement('a');a.href=d.url;a.target='_blank';a.rel='noopener';a.style.color='#86efac';a.textContent='View on LinkedIn';m.appendChild(a)}
  else{m.className='msg err';m.textContent='Error: '+d.error;pb.disabled=false;pb.textContent='Post to LinkedIn'}
}
async function doCancel(){
  await fetch('/cancel/'+encodeURIComponent(FILE)+'?t='+TOK,{method:'POST',headers:{'Content-Type':'application/json'},body:'null'})
  window.close()
}
</script></body></html>`
}

// ── HTTP server (preview + approve + cancel) ─────────────────────────────────

// Resolve OUTBOX once so path-containment check is stable
const OUTBOX_REAL = realpathSync(OUTBOX)

function safeFilePath(raw) {
  if (!raw || raw !== basename(raw) || !raw.endsWith('.md') || raw.includes('\0')) return null
  const resolved = join(OUTBOX, raw)
  try {
    const real = realpathSync(resolved)
    if (!real.startsWith(OUTBOX_REAL + sep)) return null
    return resolved
  } catch { return null }
}

function csrfOk(req) {
  const urlObj = new URL(req.url, `http://127.0.0.1:${PORT}`)
  if (urlObj.searchParams.get('t') !== SESSION_TOKEN) return false
  const origin = req.headers['origin'] || req.headers['referer'] || ''
  return origin.startsWith(`http://localhost:${PORT}`) || origin.startsWith(`http://127.0.0.1:${PORT}`)
}

const server = createServer(async (req, res) => {
  const urlObj = new URL(req.url, `http://127.0.0.1:${PORT}`)
  const parts = urlObj.pathname.split('/').filter(Boolean)
  const [action, rawFilename] = parts

  if (req.method === 'GET' && action === 'preview') {
    const filePath = safeFilePath(decodeURIComponent(rawFilename ?? ''))
    if (!filePath || !existsSync(filePath)) { res.writeHead(404); res.end('Not found'); return }
    const urlToken = urlObj.searchParams.get('t')
    if (urlToken !== SESSION_TOKEN) { res.writeHead(403); res.end('Forbidden'); return }
    const { content } = matter(readFileSync(filePath, 'utf8'))
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' })
    res.end(previewHtml(decodeURIComponent(rawFilename), content.trim(), SESSION_TOKEN))
    return
  }

  if (req.method === 'POST' && (action === 'approve' || action === 'cancel')) {
    if (!csrfOk(req)) { res.writeHead(403); res.end('Forbidden'); return }
    if (!req.headers['content-type']?.includes('application/json')) { res.writeHead(415); res.end(); return }
    const filePath = safeFilePath(decodeURIComponent(rawFilename ?? ''))
    if (!filePath) { res.writeHead(400); res.end(); return }
    const body = await new Promise(r => { let d=''; req.on('data',c=>d+=c); req.on('end',()=>r(d)) })
    const parsed_body = JSON.parse(body)

  if (action === 'approve') {
    const { text } = parsed_body
    try {
      let tokens = loadTokens()
      tokens = await refreshIfNeeded(tokens)
      const url = await postToLinkedIn(text, tokens)
      const raw = readFileSync(filePath, 'utf8')
      const parsed = matter(raw)
      parsed.data.status = 'published'
      parsed.data.linkedin_url = url
      parsed.data.published_at = new Date().toISOString()
      writeFileSync(filePath, matter.stringify(parsed.content, parsed.data))
      appendToLog(`"${parsed.data.title || rawFilename}" published. ${url}`)
      console.log(`✓ Published: ${url}`)
      res.writeHead(200, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: true, url }))
    } catch (err) {
      console.error('Post failed:', err.message)
      res.writeHead(500, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: false, error: err.message }))
    }
    return
  }

  if (action === 'cancel') {
    if (existsSync(filePath)) {
      const raw = readFileSync(filePath, 'utf8')
      const parsed = matter(raw)
      parsed.data.status = 'draft'
      writeFileSync(filePath, matter.stringify(parsed.content, parsed.data))
    }
    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify({ ok: true }))
    return
  }
  } // end POST approve/cancel block

  res.writeHead(404); res.end()
})

server.listen(PORT, '127.0.0.1', () => console.log(`Preview server: http://127.0.0.1:${PORT}`))

// ── Vault watcher ─────────────────────────────────────────────────────────────

const opened = new Map()

async function handleFile(filePath) {
  const last = opened.get(filePath) ?? 0
  if (Date.now() - last < 3000) return
  const { data } = matter(readFileSync(filePath, 'utf8'))
  if (data.status !== 'preview') return
  opened.set(filePath, Date.now())
  const url = `http://127.0.0.1:${PORT}/preview/${encodeURIComponent(basename(filePath))}?t=${SESSION_TOKEN}`
  console.log(`\nOpening preview: ${url}`)
  await open(url)
}

const watcher = watch(join(OUTBOX, '*.md'), {
  persistent: true, ignoreInitial: false,
  awaitWriteFinish: { stabilityThreshold: 500, pollInterval: 100 },
})
watcher.on('add', p => handleFile(p).catch(e => console.error(e.message)))
watcher.on('change', p => handleFile(p).catch(e => console.error(e.message)))

console.log(`NV LinkedIn Publisher
  Outbox: ${OUTBOX}
  Preview server: http://localhost:${PORT}

Drop a .md file with status: preview in the outbox to start.
`)
