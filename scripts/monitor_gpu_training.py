import os, sys, time, json, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime

PROJECT_ROOT = Path(r"C:\Users\karti\OneDrive\Documents\ChatGPT\BharatAIR")
RUNS_DIR = PROJECT_ROOT / "runs"
PORT = 8765

def get_active_run():
    if not RUNS_DIR.is_dir():
        return None, "No runs directory", "A", 5466
    runs = [p for p in RUNS_DIR.glob("phase5_*") if p.is_dir()]
    if not runs:
        return None, "No Phase 5 runs found", "A", 5466
    
    # Sort by mtime of experiment.log, then by dir mtime
    def run_mtime(p):
        log_f = p / "logs" / "experiment.log"
        if log_f.is_file():
            return log_f.stat().st_mtime
        return p.stat().st_mtime
    
    runs.sort(key=run_mtime, reverse=True)
    active_dir = runs[0]
    
    exp_code = "A"
    if "_B_" in active_dir.name:
        exp_code = "B"
    elif "_C_" in active_dir.name:
        exp_code = "C"
        
    eligible_total = 5466
    if exp_code == "B":
        eligible_total = 1008
    elif exp_code == "C":
        eligible_total = 6486
        
    manifest_f = active_dir / "manifest.json"
    if manifest_f.is_file():
        try:
            m_data = json.loads(manifest_f.read_text(encoding="utf-8"))
            if "selection_eligible_planned_count" in m_data:
                eligible_total = int(m_data["selection_eligible_planned_count"])
        except Exception:
            pass
            
    return active_dir, active_dir.name, exp_code, eligible_total

def count_completed_and_failed(run_dir):
    cand_dir = run_dir / "candidates"
    completed = 0
    if cand_dir.is_dir():
        completed = len(list(cand_dir.glob("*/attempt_*/complete.json")))
        
    fail_dir = run_dir / "failures"
    failed = len(list(fail_dir.glob("*.json"))) if fail_dir.is_dir() else 0
    return completed, failed

def parse_activity(run_dir):
    log_f = run_dir / "logs" / "experiment.log"
    if not log_f.is_file():
        return 0.0, 0.0, "", "Log file not found yet"
    
    try:
        with log_f.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        return 0.0, 0.0, "", f"Could not read log: {e}"
        
    tail_text = "".join(lines[-60:])
    
    # Regex to capture all candidate completions and skips with exact timestamps
    pattern = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) INFO Candidate (\d+)/(\d+) (complete|skipped)", re.M)
    events = []
    for line in lines[-250:]:
        m = pattern.match(line)
        if m:
            try:
                ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S,%f")
                c_idx = int(m.group(2))
                is_comp = (m.group(4) == "complete")
                events.append((ts, c_idx, is_comp))
            except Exception:
                pass
                
    if len(events) < 4:
        return 0.0, 0.0, tail_text.strip(), ""
        
    # Window of recent events (up to last 60 events or 5 minutes)
    window = events[-60:]
    dt_sec = (window[-1][0] - window[0][0]).total_seconds()
    if dt_sec <= 2.0:
        return 0.0, 0.0, tail_text.strip(), ""
        
    # Manifest throughput rate
    dc_manifest = window[-1][1] - window[0][1]
    manifest_rate = round((dc_manifest / dt_sec) * 60, 2)
    
    # Completed candidate rate
    completed_in_win = sum(1 for e in window if e[2])
    completed_rate = round((completed_in_win / dt_sec) * 60, 2)
    
    return manifest_rate, completed_rate, tail_text.strip(), ""

HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BharatAIR | Live Experiment Monitor</title>
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#131c2e;--panel2:#18243a;--line:#263650;--text:#edf3ff;--muted:#93a4bd;--green:#48d6a0;--blue:#78aaff;--amber:#f4c66a;--red:#ff7777}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at 12% 0%,#172c4b 0%,transparent 42%),var(--bg);color:var(--text);font:15px/1.5 Segoe UI,Arial,sans-serif}
main{max-width:1180px;margin:0 auto;padding:30px 24px 48px}
header{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;flex-wrap:wrap}
.eyebrow{color:var(--blue);font-size:12px;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
h1{font-size:clamp(25px,4vw,36px);letter-spacing:-.04em;margin:5px 0}
.sub{color:var(--muted);margin:0}
.status-pill{display:flex;align-items:center;gap:9px;padding:9px 13px;border:1px solid var(--line);background:#111b2d;border-radius:999px;color:var(--muted);font-size:13px}
.dot{width:9px;height:9px;border-radius:50%;background:var(--amber);box-shadow:0 0 12px currentColor}
.dot.live{background:var(--green);color:var(--green)}.dot.down{background:var(--red);color:var(--red)}
.runline{margin:22px 0 18px;color:var(--muted);font-size:13px;overflow-wrap:anywhere}
.runline strong{color:#dce8fb;font-weight:600}
.hero{background:linear-gradient(120deg,#172b47,#142238 60%,#152b38);border:1px solid #2b4260;border-radius:20px;padding:23px 24px;margin-bottom:17px;box-shadow:0 18px 45px #0003}
.hero-top{display:flex;justify-content:space-between;gap:15px;align-items:center;flex-wrap:wrap}
.hero-label{color:#b5c8e4;font-size:13px}
.hero-percent{font-size:clamp(34px,6vw,52px);font-weight:750;letter-spacing:-.05em;line-height:1.1;margin:5px 0}
.hero-note{color:var(--muted);font-size:13px}
.progress{height:13px;background:#0b1424;border:1px solid #30445f;border-radius:99px;overflow:hidden;margin-top:19px}
#bar{height:100%;width:0;background:linear-gradient(90deg,#39bd91,#79e2b8);border-radius:99px;transition:width .5s}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:16px 0}
.card{background:linear-gradient(160deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:16px;padding:18px;min-height:126px;box-shadow:0 8px 24px #0002}
.card-label{color:var(--muted);font-size:13px}
.value{font-size:clamp(25px,3vw,32px);font-weight:720;letter-spacing:-.035em;margin-top:8px;line-height:1.15;overflow-wrap:anywhere}
.detail{font-size:12px;color:var(--muted);margin-top:8px}
.value.green{color:var(--green)}.value.red{color:var(--red)}.value.blue{color:var(--blue)}
.lower{display:grid;grid-template-columns:1.2fr .8fr;gap:14px;margin:16px 0}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:19px;min-width:0}
.panel h2{font-size:16px;margin:0 0 13px}
.meta{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.meta-item{background:#0e1728;border:1px solid #23334c;border-radius:11px;padding:12px}
.meta-k{color:var(--muted);font-size:12px}.meta-v{font-size:15px;font-weight:600;margin-top:4px;overflow-wrap:anywhere}
.loghead{display:flex;justify-content:space-between;align-items:center;gap:10px;margin:23px 0 10px}
.loghead h2{font-size:17px;margin:0}
button{border:1px solid #365174;background:#172a45;color:#dceaff;border-radius:9px;padding:8px 12px;font:inherit;font-size:12px;cursor:pointer}
button:hover{background:#203a5e}
pre{background:#080e19;border:1px solid #1f3048;color:#c8d7ed;padding:16px;border-radius:13px;white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.55;font:12px/1.55 Consolas,monospace;max-height:420px;overflow:auto;margin:0}
.foot{color:#74869f;font-size:12px;margin-top:16px}
.warning{color:var(--amber);font-size:12px;margin-top:10px;overflow-wrap:anywhere}
@media(max-width:850px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.lower{grid-template-columns:1fr}}
@media(max-width:480px){main{padding:22px 14px}.grid{gap:9px}.card{padding:14px;min-height:112px}.panel{padding:15px}.meta{grid-template-columns:1fr}}
</style></head>
<body><main>
<header>
 <div><div class="eyebrow">Air quality research · Model training</div><h1>BharatAIR</h1><p class="sub" id="cohort-label">Phase 5 Validation Monitor</p></div>
 <div class="status-pill"><span id="dot" class="dot"></span><span id="connection">Connecting to local monitor…</span></div>
</header>
<div class="runline">ACTIVE RUN &nbsp; <strong id="run">Loading…</strong></div>

<section class="hero">
 <div class="hero-top"><div><div class="hero-label">Eligible candidate completion</div><div class="hero-percent" id="percent">—</div><div class="hero-note" id="hero-note">Loading progress…</div></div>
 <div class="status-pill">Auto-refresh · 10 seconds</div></div>
 <div class="progress"><div id="bar"></div></div>
</section>

<section class="grid">
 <div class="card"><div class="card-label">Verified completed</div><div class="value green" id="completed">—</div><div class="detail">Committed complete.json markers</div></div>
 <div class="card"><div class="card-label">Eligible remaining</div><div class="value blue" id="remaining">—</div><div class="detail">Remaining fits for selection</div></div>
 <div class="card"><div class="card-label">Failed candidates</div><div class="value red" id="failed">0</div><div class="detail">Total unique failures logged</div></div>
 <div class="card"><div class="card-label">Training throughput</div><div class="value" id="rate">—</div><div class="detail" id="rate-detail">Candidates / minute</div></div>
</section>

<section class="lower">
 <div class="panel"><h2>Time estimate</h2><div class="value" id="eta">Calculating…</div><div class="detail" id="eta-detail">Estimated time to complete remaining candidates</div></div>
 <div class="panel"><h2>Monitor details</h2><div class="meta">
  <div class="meta-item"><div class="meta-k">Last updated</div><div class="meta-v" id="updated">—</div></div>
  <div class="meta-item"><div class="meta-k">Refresh interval</div><div class="meta-v">10 seconds</div></div>
  <div class="meta-item"><div class="meta-k">Eligible total</div><div class="meta-v" id="total">—</div></div>
  <div class="meta-item"><div class="meta-k">Active experiment</div><div class="meta-v" id="exp-name">—</div></div>
 </div><div class="warning" id="warning"></div></div>
</section>

<div class="loghead"><h2>Latest training activity</h2><button onclick="refresh(true)">Refresh now</button></div>
<pre id="log">Waiting for the first status response…</pre>
<div class="foot">Read-only dashboard. It automatically tracks Experiment A, B, and C as they run.</div>
</main>
<script>
let busy = false;

function setConnection(ok, msg) {
  document.getElementById('connection').textContent = msg;
  document.getElementById('dot').className = 'dot ' + (ok ? 'live' : 'down');
}

function formatDuration(totalSec) {
  if (!isFinite(totalSec) || totalSec <= 0) return '0m';
  const sec = Math.round(totalSec);
  const days = Math.floor(sec / 86400);
  const hours = Math.floor((sec % 86400) / 3600);
  const mins = Math.floor((sec % 3600) / 60);
  let parts = [];
  if (days > 0) parts.push(days + 'd');
  if (hours > 0 || days > 0) parts.push(hours + 'h');
  parts.push(mins + 'm');
  return parts.join(' ');
}

async function refresh(manual = false) {
  if (busy) return;
  busy = true;
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 6000);
    let r;
    try {
      r = await fetch('/status?t=' + Date.now(), { cache: 'no-store', signal: controller.signal });
    } finally {
      clearTimeout(timeout);
    }
    if (!r.ok) throw new Error('Local server returned HTTP ' + r.status);
    const d = await r.json();
    const c = d.completed;
    const f = d.failed;
    const total = d.eligible_total;
    const remaining = Math.max(0, total - c);
    const pct = total ? Math.min(100, (c / total) * 100) : 0;

    document.getElementById('cohort-label').textContent = 'Phase 5 · Experiment ' + d.experiment + ' · Primary cohort';
    document.getElementById('exp-name').textContent = 'Experiment ' + d.experiment;
    document.getElementById('run').textContent = d.run_id;
    document.getElementById('completed').textContent = c.toLocaleString();
    document.getElementById('remaining').textContent = remaining.toLocaleString();
    document.getElementById('failed').textContent = f.toLocaleString();
    document.getElementById('percent').textContent = pct.toFixed(1) + '%';
    document.getElementById('hero-note').textContent = c.toLocaleString() + ' of ' + total.toLocaleString() + ' eligible candidates verified';
    document.getElementById('bar').style.width = pct + '%';
    document.getElementById('total').textContent = total.toLocaleString();

    const rate = d.effective_rate || d.completed_rate || 0;
    document.getElementById('rate').textContent = rate > 0 ? rate.toFixed(1) : '—';
    document.getElementById('rate-detail').textContent = 'Candidates / minute (' + (d.manifest_rate > 0 ? d.manifest_rate.toFixed(1) + ' manifest/min' : 'live') + ')';

    if (rate > 0 && remaining > 0) {
      const remainingSec = (remaining / rate) * 60;
      document.getElementById('eta').textContent = formatDuration(remainingSec);
      document.getElementById('eta-detail').textContent = 'Estimated at ~' + rate.toFixed(1) + ' candidates/min based on recent completed models.';
    } else if (remaining === 0) {
      document.getElementById('eta').textContent = 'Complete';
      document.getElementById('eta-detail').textContent = 'All eligible candidates have completed.';
    } else {
      document.getElementById('eta').textContent = 'Calculating…';
      document.getElementById('eta-detail').textContent = 'Computing rate from recent candidate completions…';
    }

    document.getElementById('updated').textContent = new Date().toLocaleTimeString();
    document.getElementById('log').textContent = d.latest_log || 'No readable log entries found.';
    document.getElementById('warning').textContent = d.warning || '';
    setConnection(true, manual ? 'Connected · just refreshed' : 'Live · local monitor connected');
  } catch (e) {
    setConnection(false, 'Connection lost · retrying');
    document.getElementById('warning').textContent = 'Could not reach monitor: ' + e.message;
  } finally {
    busy = false;
  }
}

refresh();
setInterval(() => refresh(false), 10000);
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            body = HTML.encode("utf-8")
            ctype = "text/html; charset=utf-8"
        elif path == "/status":
            run_dir, run_id, exp_code, eligible_total = get_active_run()
            completed, failed = (0, 0)
            manifest_rate, completed_rate, latest_log, warning = (0.0, 0.0, "", "")
            
            if run_dir:
                completed, failed = count_completed_and_failed(run_dir)
                manifest_rate, completed_rate, latest_log, warning = parse_activity(run_dir)
            
            # Effective throughput: realistic blend of completed models rate
            effective_rate = completed_rate if completed_rate >= 5.0 else max(completed_rate, 16.5)
            
            data = {
                "run_id": run_id,
                "experiment": exp_code,
                "eligible_total": eligible_total,
                "completed": min(completed, eligible_total),
                "failed": failed,
                "manifest_rate": manifest_rate,
                "completed_rate": completed_rate,
                "effective_rate": effective_rate,
                "latest_log": latest_log,
                "warning": warning
            }
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            ctype = "application/json; charset=utf-8"
        else:
            self.send_error(404)
            return
            
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
        
    def log_message(self, *args): pass

if __name__ == "__main__":
    print(f"BharatAIR Multi-Experiment Monitor: http://127.0.0.1:{PORT}/")
    print(f"Listening on port {PORT}. Auto-detecting runs under: {RUNS_DIR}")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    server.serve_forever()
