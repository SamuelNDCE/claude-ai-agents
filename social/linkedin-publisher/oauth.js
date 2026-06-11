import http from 'http'
import { writeFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import open from 'open'

const __dirname = dirname(fileURLToPath(import.meta.url))
const CLIENT_ID = process.env.LINKEDIN_CLIENT_ID
const CLIENT_SECRET = process.env.LINKEDIN_CLIENT_SECRET
const REDIRECT_URI = 'http://localhost:3000/callback'
const SCOPES = 'openid profile w_member_social'

if (!CLIENT_ID || !CLIENT_SECRET) {
  console.error('LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET required in .env')
  process.exit(1)
}

const authUrl = 'https://www.linkedin.com/oauth/v2/authorization?' + new URLSearchParams({
  response_type: 'code',
  client_id: CLIENT_ID,
  redirect_uri: REDIRECT_URI,
  scope: SCOPES,
  state: 'nv-linkedin',
})

console.log('Opening LinkedIn authorization in browser...')
await open(authUrl)

const code = await new Promise((resolve, reject) => {
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, 'http://localhost:3000')
    if (url.pathname !== '/callback') return
    const error = url.searchParams.get('error')
    if (error) { res.end(`Error: ${error}`); server.close(); reject(new Error(error)); return }
    res.writeHead(200, { 'Content-Type': 'text/html' })
    res.end('<h2 style="font-family:sans-serif;padding:2rem">Authorized. You can close this tab.</h2>')
    server.close()
    resolve(url.searchParams.get('code'))
  })
  server.listen(3000)
  server.on('error', reject)
})

const tokenRes = await fetch('https://www.linkedin.com/oauth/v2/accessToken', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({ grant_type: 'authorization_code', code, redirect_uri: REDIRECT_URI, client_id: CLIENT_ID, client_secret: CLIENT_SECRET }),
})
const tokens = await tokenRes.json()
if (!tokens.access_token) { console.error('Token exchange failed:', tokens); process.exit(1) }

const profileRes = await fetch('https://api.linkedin.com/v2/userinfo', {
  headers: { Authorization: `Bearer ${tokens.access_token}` },
})
const profile = await profileRes.json()
if (!profile.sub) { console.error('Could not get profile:', profile); process.exit(1) }

const saved = {
  access_token: tokens.access_token,
  refresh_token: tokens.refresh_token ?? null,
  expires_at: Date.now() + (tokens.expires_in ?? 5_184_000) * 1000,
  person_urn: `urn:li:person:${profile.sub}`,
  name: profile.name,
}
writeFileSync(join(__dirname, '.tokens.json'), JSON.stringify(saved, null, 2))
console.log(`\n✓ Authorized as ${profile.name}`)
console.log(`  Person URN: ${saved.person_urn}`)
console.log(`  Tokens saved to .tokens.json (valid ~60 days)\n`)
console.log('Now run: npm start')
