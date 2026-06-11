import { watch } from 'chokidar'
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import matter from 'gray-matter'

const __dirname = dirname(fileURLToPath(import.meta.url))
const TOKENS_FILE = join(__dirname, '.tokens.json')
const VAULT = process.env.VAULT_PATH || String.raw`C:\Users\Futur\Documents\AiWorkspace\NeuralVault\sample-vault`
const OUTBOX = join(VAULT, 'wiki', 'agent-inbox', 'social', 'outbox')
const LOG_FILE = join(VAULT, 'wiki', 'logs', 'perpetual-technologies.md')

mkdirSync(OUTBOX, { recursive: true })

function loadTokens() {
  if (!existsSync(TOKENS_FILE)) {
    console.error('No .tokens.json — run: npm run auth')
    process.exit(1)
  }
  return JSON.parse(readFileSync(TOKENS_FILE, 'utf8'))
}

async function refreshIfNeeded(tokens) {
  if (Date.now() < tokens.expires_at - 7 * 86_400_000) return tokens
  if (!tokens.refresh_token) {
    console.error('Token expired. Run: npm run auth')
    process.exit(1)
  }
  console.log('Refreshing access token...')
  const res = await fetch('https://www.linkedin.com/oauth/v2/accessToken', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'refresh_token',
      refresh_token: tokens.refresh_token,
      client_id: process.env.LINKEDIN_CLIENT_ID,
      client_secret: process.env.LINKEDIN_CLIENT_SECRET,
    }),
  })
  const data = await res.json()
  if (!data.access_token) { console.error('Refresh failed:', data); process.exit(1) }
  tokens.access_token = data.access_token
  tokens.expires_at = Date.now() + (data.expires_in ?? 5_184_000) * 1000
  if (data.refresh_token) tokens.refresh_token = data.refresh_token
  writeFileSync(TOKENS_FILE, JSON.stringify(tokens, null, 2))
  return tokens
}

async function postToLinkedIn(text, tokens) {
  const res = await fetch('https://api.linkedin.com/v2/ugcPosts', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${tokens.access_token}`,
      'Content-Type': 'application/json',
      'X-Restli-Protocol-Version': '2.0.0',
    },
    body: JSON.stringify({
      author: tokens.person_urn,
      lifecycleState: 'PUBLISHED',
      specificContent: {
        'com.linkedin.ugc.ShareContent': {
          shareCommentary: { text },
          shareMediaCategory: 'NONE',
        },
      },
      visibility: { 'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC' },
    }),
  })

  if (!res.ok) throw new Error(`LinkedIn API ${res.status}: ${await res.text()}`)

  const postId = res.headers.get('x-restli-id') || (await res.json().catch(() => ({}))).id || 'unknown'
  return `https://www.linkedin.com/feed/update/${encodeURIComponent(postId)}/`
}

function appendToLog(message) {
  if (!existsSync(LOG_FILE)) return
  const log = readFileSync(LOG_FILE, 'utf8')
  const entry = `\n## ${new Date().toISOString().slice(0, 10)} — LinkedIn post published\n\n${message}\n`
  writeFileSync(LOG_FILE, log.replace(/^(# .+\n)/, `$1${entry}`))
}

const processing = new Set()

async function handleFile(filePath) {
  if (processing.has(filePath)) return
  processing.add(filePath)
  try {
    const raw = readFileSync(filePath, 'utf8')
    const parsed = matter(raw)
    if (parsed.data.status !== 'ready') return

    console.log(`\nPublishing: ${filePath}`)
    const text = parsed.content.trim()
    if (!text) { console.error('  Post body is empty — skipping'); return }

    let tokens = loadTokens()
    tokens = await refreshIfNeeded(tokens)

    const url = await postToLinkedIn(text, tokens)

    parsed.data.status = 'published'
    parsed.data.linkedin_url = url
    parsed.data.published_at = new Date().toISOString()
    writeFileSync(filePath, matter.stringify(parsed.content, parsed.data))

    const title = parsed.data.title || filePath.split(/[\\/]/).pop()
    appendToLog(`"${title}" published. URL: ${url}`)
    console.log(`✓ Published: ${url}`)
  } catch (err) {
    console.error(`  Error: ${err.message}`)
  } finally {
    processing.delete(filePath)
  }
}

const watcher = watch(join(OUTBOX, '*.md'), {
  persistent: true,
  ignoreInitial: false,
  awaitWriteFinish: { stabilityThreshold: 500, pollInterval: 100 },
})
watcher.on('add', handleFile)
watcher.on('change', handleFile)
console.log(`NV LinkedIn Publisher watching:\n  ${OUTBOX}\n\nDrop a .md file with status: ready to publish.\n`)
