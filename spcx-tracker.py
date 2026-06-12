"""SPCX live tracker with NeuralVault alert logging.

Run: python spcx-tracker.py
Then open: http://localhost:8765
"""

import json
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import yfinance as yf

TICKER = "SPCX"
IPO_PRICE = 135.0
POLL_INTERVAL = 15          # seconds between price checks
ALERT_THRESHOLD = 0.5       # % change per interval to log to NV
PORT = 8765
VAULT_LOG = Path(r"C:\Users\Futur\Documents\AiWorkspace\NeuralVault\sample-vault\wiki\logs\trading.md")

state = {
    "price": None,
    "prev_price": None,
    "change_pct": 0.0,
    "volume": None,
    "high": None,
    "low": None,
    "updated": "waiting...",
    "error": None,
    "alerts": [],
}
lock = threading.Lock()


def fetch():
    t = yf.Ticker(TICKER)
    fi = t.fast_info
    return {
        "price": fi.last_price,
        "volume": getattr(fi, "regular_market_volume", None),
        "high": getattr(fi, "fifty_two_week_high", None),
        "low": getattr(fi, "fifty_two_week_low", None),
    }


def vault_append(line: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n- **{ts}** — {line}"
    try:
        with open(VAULT_LOG, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"Vault write error: {e}")


def poll_loop():
    vault_append(f"SPCX tracker session started (IPO day, $135 base)")
    while True:
        try:
            data = fetch()
            now = datetime.now().strftime("%H:%M:%S")
            price = data["price"]
            with lock:
                prev = state["price"]
                state["price"] = price
                state["prev_price"] = prev
                state["volume"] = data["volume"]
                state["high"] = data["high"]
                state["low"] = data["low"]
                state["updated"] = now
                state["error"] = None
                if price and prev:
                    pct = (price - prev) / prev * 100
                    state["change_pct"] = pct
                    if abs(pct) >= ALERT_THRESHOLD:
                        direction = "UP" if pct > 0 else "DOWN"
                        msg = f"SPCX {direction} {pct:+.2f}% → ${price:.2f}"
                        state["alerts"].insert(0, f"{now}  {msg}")
                        state["alerts"] = state["alerts"][:30]
                        vault_append(msg)
        except Exception as e:
            with lock:
                state["error"] = str(e)
            print(f"Poll error: {e}")
        time.sleep(POLL_INTERVAL)


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SPCX Tracker</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0d18;color:#f1f5f9;font-family:system-ui,-apple-system,sans-serif;padding:2rem}
.meta{font-size:12px;color:rgba(255,255,255,.4);margin-bottom:.5rem}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#10b981;margin-right:6px;animation:p 2s infinite}
@keyframes p{0%,100%{opacity:1}50%{opacity:.2}}
.price{font-size:3.5rem;font-weight:500;margin:.25rem 0}
.sub{font-size:1rem;margin-bottom:1.5rem}
.up{color:#10b981}.dn{color:#ef4444}.mu{color:rgba(255,255,255,.45)}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:1.5rem}
.card{background:#111827;border-radius:10px;padding:.9rem;border:1px solid rgba(255,255,255,.07)}
.lbl{font-size:11px;color:rgba(255,255,255,.4);margin-bottom:4px;text-transform:uppercase;letter-spacing:.05em}
.val{font-size:1.2rem;font-weight:500}
.al-head{font-size:11px;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.06em;margin-bottom:.5rem}
.al{background:#111827;border-left:3px solid #22d3ee;padding:.45rem .75rem;margin:5px 0;font-size:12px;border-radius:0 6px 6px 0;font-family:monospace}
.err{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);border-radius:8px;padding:.75rem 1rem;font-size:13px;color:#fca5a5;margin-bottom:1rem}
.nv{font-size:12px;color:rgba(255,255,255,.3);margin-top:1.5rem}
</style>
</head>
<body>
<div class="meta"><span class="dot"></span>SPCX &nbsp;·&nbsp; Nasdaq &nbsp;·&nbsp; Refreshes every 10s</div>
<div class="price" id="price">—</div>
<div class="sub" id="sub"></div>
<div id="err"></div>
<div class="grid">
  <div class="card"><div class="lbl">Volume today</div><div class="val" id="vol">—</div></div>
  <div class="card"><div class="lbl">52w high</div><div class="val" id="hi">—</div></div>
  <div class="card"><div class="lbl">52w low</div><div class="val" id="lo">—</div></div>
  <div class="card"><div class="lbl">Last fetch</div><div class="val" id="ts">—</div></div>
</div>
<div class="al-head">NeuralVault alerts (±0.5% moves)</div>
<div id="alerts"><span style="color:rgba(255,255,255,.25);font-size:12px">Watching for moves...</span></div>
<div class="nv">Alerts logged to NeuralVault › wiki/logs/trading.md</div>
<script>
const fmt = n => n != null ? '$' + Number(n).toFixed(2) : '—';
const fmtVol = n => n ? Number(n).toLocaleString() : '—';
async function refresh() {
  try {
    const d = await fetch('/data').then(r => r.json());
    document.getElementById('price').textContent = fmt(d.price);
    const pct = d.change_pct || 0;
    const fromIpo = d.price ? ((d.price - 135) / 135 * 100) : 0;
    const cls = pct > 0 ? 'up' : pct < 0 ? 'dn' : 'mu';
    const sign = pct > 0 ? '+' : '';
    document.getElementById('sub').innerHTML =
      `<span class="${cls}">${sign}${pct.toFixed(2)}% this interval</span>` +
      `&nbsp; · &nbsp;IPO $135&nbsp; · &nbsp;` +
      `<span class="up">+${fromIpo.toFixed(1)}% from IPO</span>`;
    document.getElementById('vol').textContent = fmtVol(d.volume);
    document.getElementById('hi').textContent = fmt(d.high);
    document.getElementById('lo').textContent = fmt(d.low);
    document.getElementById('ts').textContent = d.updated;
    const errEl = document.getElementById('err');
    errEl.innerHTML = d.error ? `<div class="err">yfinance error: ${d.error}<br>SPCX may not be indexed yet — retry in a few minutes.</div>` : '';
    const alEl = document.getElementById('alerts');
    alEl.innerHTML = d.alerts.length
      ? d.alerts.map(a => `<div class="al">${a}</div>`).join('')
      : '<span style="color:rgba(255,255,255,.25);font-size:12px">Watching for moves...</span>';
  } catch(e) { console.error(e); }
}
refresh();
setInterval(refresh, 10000);
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/data":
            with lock:
                payload = json.dumps({
                    "price": state["price"],
                    "change_pct": state["change_pct"],
                    "volume": state["volume"],
                    "high": state["high"],
                    "low": state["low"],
                    "updated": state["updated"],
                    "error": state["error"],
                    "alerts": state["alerts"],
                })
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload.encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode())


if __name__ == "__main__":
    print(f"SPCX Tracker starting on http://localhost:{PORT}")
    print(f"Vault log: {VAULT_LOG}")
    print("Note: SPCX is a new ticker — yfinance may take a few hours to index it.")
    threading.Thread(target=poll_loop, daemon=True).start()
    HTTPServer(("localhost", PORT), Handler).serve_forever()
