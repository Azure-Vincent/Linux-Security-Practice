"""Local web UI for BeaconHunt submissions.

A dependency-free (stdlib only) web server that drives the same engine as the
CLI: generate a round, submit findings, take hints, grade, and view the
scoreboard from the browser. It is bound to 127.0.0.1 only — in keeping with
BeaconHunt's localhost-only scope — so it is never reachable from the LAN.

    beaconhunt web            # serve on http://127.0.0.1:8800
    beaconhunt web --port N
"""

from __future__ import annotations

import hmac
import json
import os
import secrets
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from . import report, safety
from .catalog import load_catalog
from .grader import Submission, grade
from .hints import choose_hint
from .scenario import (
    current_seed,
    generate_scenario,
    load_scenario,
)
from .schema import KNOWN_CATEGORIES, KNOWN_SERVICES
from .scoreboard import load as load_scoreboard
from .scoreboard import record as record_score
from .session import load_round, save_round

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BeaconHunt</title>
<style>
  :root {
    --bg: #0f1115; --panel: #171a21; --edge: #262b36; --fg: #e6e9ef;
    --muted: #9aa4b2; --accent: #4ea1ff; --ok: #3fb950; --warn: #d29922;
    --bad: #f85149; --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  @media (prefers-color-scheme: light) {
    :root { --bg:#f4f6fa; --panel:#fff; --edge:#dde2ea; --fg:#1c2128;
            --muted:#5b6673; --accent:#1f6feb; }
  }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--fg);
    font:15px/1.5 system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
  header { padding:18px 24px; border-bottom:1px solid var(--edge);
    display:flex; align-items:baseline; gap:14px; flex-wrap:wrap; }
  header h1 { font-size:20px; margin:0; letter-spacing:.3px; }
  header .tag { color:var(--muted); font-size:13px; }
  .wrap { max-width:1000px; margin:0 auto; padding:24px 16px; display:grid;
    grid-template-columns:1fr 1fr; gap:18px; }
  @media (max-width:820px){ .wrap{ grid-template-columns:1fr; } }
  .card { background:var(--panel); border:1px solid var(--edge);
    border-radius:12px; padding:18px; }
  .card h2 { font-size:14px; text-transform:uppercase; letter-spacing:.6px;
    color:var(--muted); margin:0 0 14px; }
  label { display:block; font-size:13px; color:var(--muted); margin:10px 0 4px; }
  input, select, textarea, button { font:inherit; }
  input, select, textarea { width:100%; padding:9px 11px; border-radius:8px;
    border:1px solid var(--edge); background:var(--bg); color:var(--fg); }
  textarea { resize:vertical; min-height:62px; }
  .row { display:flex; gap:10px; } .row > * { flex:1; }
  button { cursor:pointer; border:1px solid var(--edge); border-radius:8px;
    padding:10px 14px; background:var(--accent); color:#fff; font-weight:600; }
  button.ghost { background:transparent; color:var(--fg); }
  button:active { transform:translateY(1px); }
  .stat { display:flex; gap:20px; flex-wrap:wrap; }
  .stat div b { display:block; font-size:22px; }
  .stat div span { color:var(--muted); font-size:12px; }
  ul { list-style:none; margin:0; padding:0; }
  li.sub { padding:9px 0; border-bottom:1px solid var(--edge); display:flex;
    gap:10px; align-items:flex-start; }
  .mark { width:20px; text-align:center; font-weight:700; }
  .mark.strong{color:var(--ok);} .mark.weak{color:var(--warn);}
  .mark.none{color:var(--bad);} .mark.pending{color:var(--muted);}
  .ev { font-family:var(--mono); font-size:13px; word-break:break-all; }
  .note { color:var(--muted); font-size:12px; }
  pre { white-space:pre-wrap; font-family:var(--mono); font-size:12.5px;
    background:var(--bg); border:1px solid var(--edge); border-radius:8px;
    padding:12px; overflow:auto; max-height:420px; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th,td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--edge); }
  .full { grid-column:1 / -1; }
  .hintbox { background:var(--bg); border:1px dashed var(--edge);
    border-radius:8px; padding:10px; margin-top:10px; font-size:13px; }
  .banner { grid-column:1/-1; background:var(--panel); border:1px solid var(--edge);
    border-radius:12px; padding:14px 18px; color:var(--muted); }
</style>
</head>
<body>
<header>
  <h1>🛰 BeaconHunt</h1>
  <span class="tag" id="seedtag">no active round</span>
  <span class="tag" style="margin-left:auto">local range · 127.0.0.1 only</span>
  <a class="tag" href="/logout" style="color:var(--accent);text-decoration:none">sign out</a>
</header>
<div class="wrap" id="root">

  <div class="banner" id="noround" style="display:none">
    No active scenario. Start one below (or run <code>beaconhunt generate</code>
    in a terminal), then deploy the range with <code>beaconhunt deploy</code>.
  </div>

  <div class="card">
    <h2>Submit a finding</h2>
    <div class="row">
      <div><label>Service</label><select id="service"></select></div>
      <div><label>Category</label><select id="type"></select></div>
    </div>
    <label>Evidence (path · PID · port · user · config line)</label>
    <textarea id="evidence" placeholder="/root/.ssh/authorized_keys line 3"></textarea>
    <div class="row" style="margin-top:12px">
      <button onclick="submitFinding()">Submit finding</button>
      <button class="ghost" onclick="takeHint()">Hint (costs points)</button>
    </div>
    <div id="hint" class="hintbox" style="display:none"></div>
  </div>

  <div class="card">
    <h2>Round</h2>
    <div class="stat" id="stats"><div><b>—</b><span>no round</span></div></div>
    <div style="margin-top:14px" class="row">
      <button onclick="doGrade()">Grade round</button>
      <button class="ghost" onclick="toggleNew()">New round</button>
    </div>
    <div id="newround" style="display:none;margin-top:12px">
      <div class="row">
        <div><label>Seed (blank = random)</label><input id="seed" type="number"></div>
        <div><label>Count</label><input id="count" type="number" value="5"></div>
      </div>
      <label>Limit to service (optional)</label>
      <select id="genservice"></select>
      <button style="margin-top:12px" onclick="newRound()">Generate scenario</button>
    </div>
  </div>

  <div class="card">
    <h2>Your submissions</h2>
    <ul id="subs"><li class="note">None yet.</li></ul>
  </div>

  <div class="card">
    <h2>Scoreboard</h2>
    <table id="board"><tbody><tr><td class="note">No rounds recorded.</td></tr></tbody></table>
  </div>

  <div class="card full" id="reportcard" style="display:none">
    <h2>Report</h2>
    <pre id="report"></pre>
  </div>

</div>
<script>
const $ = s => document.querySelector(s);
async function api(path, body){
  const opt = body ? {method:'POST', headers:{'Content-Type':'application/json'},
                      body:JSON.stringify(body)} : {};
  const r = await fetch(path, opt);
  if(r.status===401){ location.href='/login'; throw new Error('unauthorized'); }
  if(!r.ok){ alert('Error: '+(await r.text())); throw new Error(r.status); }
  return r.json();
}
function opts(sel, items, blankLabel){
  sel.innerHTML = '';
  if(blankLabel){ const o=document.createElement('option'); o.value=''; o.textContent=blankLabel; sel.appendChild(o); }
  for(const it of items){ const o=document.createElement('option'); o.value=it; o.textContent=it; sel.appendChild(o); }
}
async function boot(){
  const meta = await api('/api/meta');
  opts($('#service'), meta.services);
  opts($('#type'), meta.categories);
  opts($('#genservice'), meta.services, 'any service');
  await refresh();
}
async function refresh(){
  const s = await api('/api/state');
  const board = await api('/api/scoreboard');
  renderBoard(board);
  if(!s.active){
    $('#noround').style.display='block';
    $('#seedtag').textContent='no active round';
    $('#stats').innerHTML='<div><b>—</b><span>no round</span></div>';
    $('#subs').innerHTML='<li class="note">None yet.</li>';
    return;
  }
  $('#noround').style.display='none';
  $('#seedtag').textContent='seed '+s.seed+' · '+s.count+' findings · '+s.total_points+' pts';
  $('#stats').innerHTML =
    stat(s.submissions.length,'submitted') +
    stat(Object.values(s.hints_used).reduce((a,b)=>a+b,0),'hints') +
    stat(fmtTime(s.elapsed),'elapsed');
  renderSubs(s.submissions, s.graded);
  if(s.graded){ $('#reportcard').style.display='block'; $('#report').textContent=s.report; }
}
const stat=(v,l)=>`<div><b>${v}</b><span>${l}</span></div>`;
function fmtTime(sec){ sec=Math.floor(sec); return Math.floor(sec/60)+'m'+String(sec%60).padStart(2,'0')+'s'; }
function renderSubs(subs, graded){
  const el=$('#subs');
  if(!subs.length){ el.innerHTML='<li class="note">None yet.</li>'; return; }
  const byIdx = {};
  if(graded){ graded.scored.forEach((g,i)=> byIdx[i]=g); }
  el.innerHTML = subs.map((sub,i)=>{
    const g = byIdx[i];
    const mk = g ? (g.strength==='strong'?['✓','strong']:g.strength==='weak'?['~','weak']:['✗','none'])
                 : ['•','pending'];
    const extra = g ? `<div class="note">+${g.awarded} · ${g.note}</div>` : '';
    return `<li class="sub"><span class="mark ${mk[1]}">${mk[0]}</span>
      <div><div class="ev">${esc(sub.service)}/${esc(sub.type)} — ${esc(sub.evidence)}</div>${extra}</div></li>`;
  }).join('');
}
function renderBoard(rows){
  const b=$('#board').querySelector('tbody');
  if(!rows.length){ b.innerHTML='<tr><td class="note">No rounds recorded.</td></tr>'; return; }
  b.innerHTML='<tr><th>seed</th><th>score</th><th>detect</th><th>FP</th><th>time</th></tr>'+
    rows.slice().reverse().map(r=>`<tr><td>${r.seed}</td><td>${r.final_points}/${r.total_possible}</td>
      <td>${Math.round(r.detection_rate*100)}%</td><td>${r.false_positives}</td>
      <td>${Math.floor(r.elapsed_seconds)}s</td></tr>`).join('');
}
const esc = s => String(s).replace(/[&<>]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
async function submitFinding(){
  const evidence=$('#evidence').value.trim();
  if(!evidence){ alert('Enter some evidence.'); return; }
  await api('/api/submit', {service:$('#service').value, type:$('#type').value, evidence});
  $('#evidence').value=''; $('#reportcard').style.display='none'; refresh();
}
async function takeHint(){
  const h = await api('/api/hint', {service:$('#service').value});
  const box=$('#hint'); box.style.display='block';
  box.textContent = h.text ? `(~${h.cost} pts) ${h.text}` : 'No findings match that service.';
  refresh();
}
async function doGrade(){
  const r = await api('/api/grade', {});
  $('#reportcard').style.display='block'; $('#report').textContent=r.report;
  refresh();
}
function toggleNew(){ const n=$('#newround'); n.style.display = n.style.display==='none'?'block':'none'; }
async function newRound(){
  const seed=$('#seed').value, count=$('#count').value, service=$('#genservice').value;
  await api('/api/generate', {seed:seed?Number(seed):null, count:Number(count)||5, service:service||null});
  $('#newround').style.display='none'; $('#hint').style.display='none';
  $('#reportcard').style.display='none'; refresh();
}
boot();
</script>
</body>
</html>"""


LOGIN_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BeaconHunt · sign in</title>
<style>
  :root{ --bg:#0f1115; --panel:#171a21; --edge:#262b36; --fg:#e6e9ef;
    --muted:#9aa4b2; --accent:#4ea1ff; }
  @media (prefers-color-scheme: light){ :root{ --bg:#f4f6fa; --panel:#fff;
    --edge:#dde2ea; --fg:#1c2128; --muted:#5b6673; --accent:#1f6feb; } }
  *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--fg);
    font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
    display:grid;min-height:100vh;place-items:center}
  form{background:var(--panel);border:1px solid var(--edge);border-radius:12px;
    padding:26px;width:320px}
  h1{font-size:19px;margin:0 0 4px} p{color:var(--muted);font-size:13px;margin:0 0 18px}
  label{display:block;font-size:13px;color:var(--muted);margin:12px 0 4px}
  input{width:100%;padding:10px 11px;border-radius:8px;border:1px solid var(--edge);
    background:var(--bg);color:var(--fg);font:inherit}
  button{margin-top:18px;width:100%;cursor:pointer;border:0;border-radius:8px;
    padding:11px;background:var(--accent);color:#fff;font-weight:600;font:inherit}
  .err{color:#f85149;font-size:13px;margin-top:12px;min-height:16px}
</style></head><body>
<form method="post" action="/login">
  <h1>🛰 BeaconHunt</h1>
  <p>Local training range · sign in to continue</p>
  <label>Username</label><input name="username" autofocus autocomplete="username">
  <label>Password</label><input name="password" type="password" autocomplete="current-password">
  <button type="submit">Sign in</button>
  <div class="err">__ERROR__</div>
</form></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    # injected by the server
    catalog_dir: Path
    state_dir: Path
    auth_enabled: bool = True
    username: str = "hunter"
    password: str = ""
    _sessions: set[str] = set()
    _lock = threading.Lock()

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200) -> None:
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json")

    def _error(self, msg: str, code: int = 400) -> None:
        self._send(code, msg.encode("utf-8"), "text/plain")

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        return json.loads(self.rfile.read(length) or b"{}")

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def _redirect(self, location: str, cookie: str | None = None) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", "0")
        self.end_headers()

    # -- auth ----------------------------------------------------------------

    def _authed(self) -> bool:
        if not self.auth_enabled:
            return True
        raw = self.headers.get("Cookie")
        if not raw:
            return False
        try:
            token = SimpleCookie(raw).get("bh_session")
        except Exception:
            return False
        if token is None:
            return False
        with self._lock:
            return token.value in self._sessions

    def _do_login(self) -> None:
        body = self._read_body().decode("utf-8", "replace")
        form = parse_qs(body)
        user = (form.get("username", [""])[0]).strip()
        pw = form.get("password", [""])[0]
        ok = (hmac.compare_digest(user, self.username)
              and hmac.compare_digest(pw, self.password))
        if not ok:
            time.sleep(0.5)  # mild brute-force friction
            page = LOGIN_PAGE.replace("__ERROR__", "Invalid username or password.")
            self._send(401, page.encode("utf-8"), "text/html; charset=utf-8")
            return
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions.add(token)
        self._redirect("/", cookie=(
            f"bh_session={token}; HttpOnly; SameSite=Strict; Path=/"))

    def _do_logout(self) -> None:
        raw = self.headers.get("Cookie")
        if raw:
            tok = SimpleCookie(raw).get("bh_session")
            if tok:
                with self._lock:
                    self._sessions.discard(tok.value)
        self._redirect("/login", cookie="bh_session=; Max-Age=0; Path=/")

    # -- routing -------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        try:
            if self.path == "/login":
                page = LOGIN_PAGE.replace("__ERROR__", "")
                self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
                return
            if self.path == "/logout":
                self._do_logout()
                return
            if not self._authed():
                if self.path.startswith("/api/"):
                    self._error("unauthorized", 401)
                else:
                    self._redirect("/login")
                return
            if self.path == "/" or self.path.startswith("/index"):
                self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
            elif self.path == "/api/meta":
                self._json({
                    "services": sorted(KNOWN_SERVICES - {"host"}) + ["host"],
                    "categories": sorted(KNOWN_CATEGORIES),
                    "current_seed": current_seed(self.state_dir),
                })
            elif self.path == "/api/state":
                self._json(self._state())
            elif self.path == "/api/scoreboard":
                self._json([e.__dict__ | {"detection_rate": e.detection_rate}
                            for e in load_scoreboard(self.state_dir)])
            else:
                self._error("not found", 404)
        except Exception as exc:  # keep the server alive, report to the UI
            self._error(f"{type(exc).__name__}: {exc}", 500)

    def do_POST(self) -> None:  # noqa: N802
        try:
            if self.path == "/login":
                self._do_login()
                return
            if not self._authed():
                self._error("unauthorized", 401)
                return
            body = self._read_json()
            if self.path == "/api/submit":
                self._post_submit(body)
            elif self.path == "/api/hint":
                self._post_hint(body)
            elif self.path == "/api/grade":
                self._post_grade()
            elif self.path == "/api/generate":
                self._post_generate(body)
            else:
                self._error("not found", 404)
        except Exception as exc:
            self._error(f"{type(exc).__name__}: {exc}", 500)

    # -- handlers ------------------------------------------------------------

    def _state(self) -> dict:
        seed = current_seed(self.state_dir)
        if seed is None:
            return {"active": False}
        scenario = load_scenario(seed, self.state_dir)
        state = load_round(seed, self.state_dir)
        out = {
            "active": True,
            "seed": seed,
            "count": len(scenario.findings),
            "total_points": scenario.total_points,
            "elapsed": state.elapsed,
            "hints_used": state.hints_used,
            "submissions": [
                {"type": s.type, "service": s.service, "evidence": s.evidence}
                for s in state.submissions
            ],
            "graded": None,
        }
        if state.finished_at is not None:
            cat = load_catalog(self.catalog_dir)
            result = grade(scenario, cat, state.submissions, state.hints_used)
            out["graded"] = result.to_dict()
            out["report"] = report.render_text(result, cat, scenario, state.elapsed)
        return out

    def _post_submit(self, body: dict) -> None:
        seed = current_seed(self.state_dir)
        if seed is None:
            return self._error("no active scenario", 409)
        evidence = (body.get("evidence") or "").strip()
        if not evidence:
            return self._error("evidence required", 400)
        state = load_round(seed, self.state_dir)
        # A new submission after grading reopens the round.
        state.finished_at = None
        state.submissions.append(Submission(
            type=body.get("type", ""), service=body.get("service", ""),
            evidence=evidence, at=time.time(),
        ))
        save_round(state, self.state_dir)
        self._json(self._state())

    def _post_hint(self, body: dict) -> None:
        seed = current_seed(self.state_dir)
        if seed is None:
            return self._error("no active scenario", 409)
        cat = load_catalog(self.catalog_dir)
        scenario = load_scenario(seed, self.state_dir)
        state = load_round(seed, self.state_dir)
        hint = choose_hint(cat, scenario, state, service=body.get("service") or None)
        if hint is None:
            return self._json({"text": None})
        state.hints_used[hint["artifact_id"]] = hint["n"] + 1
        save_round(state, self.state_dir)
        self._json({"text": hint["text"], "cost": hint["cost"]})

    def _post_grade(self) -> None:
        seed = current_seed(self.state_dir)
        if seed is None:
            return self._error("no active scenario", 409)
        cat = load_catalog(self.catalog_dir)
        scenario = load_scenario(seed, self.state_dir)
        state = load_round(seed, self.state_dir)
        if state.finished_at is None:
            state.finished_at = time.time()
            save_round(state, self.state_dir)
        result = grade(scenario, cat, state.submissions, state.hints_used)
        record_score(result, state.elapsed, self.state_dir)
        self._json({
            "report": report.render_text(result, cat, scenario, state.elapsed),
            "result": result.to_dict(),
        })

    def _post_generate(self, body: dict) -> None:
        cat = load_catalog(self.catalog_dir)
        service = body.get("service") or None
        scenario = generate_scenario(
            cat,
            seed=body.get("seed"),
            count=int(body.get("count") or 5),
            services=[service] if service else None,
        )
        scenario.save(self.state_dir)
        save_round(load_round(scenario.seed, self.state_dir), self.state_dir)
        self._json(self._state())

    def log_message(self, *_a) -> None:
        return  # quiet


def serve(
    catalog_dir: Path,
    state_dir: Path,
    port: int = 8800,
    user: str = "hunter",
    password: str | None = None,
    auth: bool = True,
) -> int:
    # Hard scope: bind to loopback only.
    safety.require_in_scope("127.0.0.1")

    generated = False
    if auth:
        password = password or os.environ.get("BEACONHUNT_WEB_PASSWORD")
        if not password:
            password = secrets.token_urlsafe(9)
            generated = True

    handler = type("Handler", (_Handler,), {
        "catalog_dir": Path(catalog_dir),
        "state_dir": Path(state_dir),
        "auth_enabled": auth,
        "username": user,
        "password": password or "",
        "_sessions": set(),
        "_lock": threading.Lock(),
    })
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}"

    print("=" * 56)
    print(f"  BeaconHunt web UI   {url}")
    print(f"  Address : 127.0.0.1  (localhost only — not on the LAN)")
    if auth:
        print(f"  Username: {user}")
        if generated:
            print(f"  Password: {password}   (generated for this run)")
        else:
            print(f"  Password: (as supplied)")
        print("  Open the URL, sign in with the above, then start hunting.")
    else:
        print("  Auth    : DISABLED (--no-auth) — anyone on this host can use it")
    print("  Ctrl-C to stop.")
    print("=" * 56)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping web UI")
    finally:
        httpd.server_close()
    return 0
