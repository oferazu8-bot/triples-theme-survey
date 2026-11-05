#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Theme survey: dark homepage A vs mixed B + anonymous Hebrew survey."""
from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

from flask import (
    Flask,
    Response,
    abort,
    g,
    jsonify,
    redirect,
    render_template_string,
    request,
    send_from_directory,
)

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", str(APP_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(os.environ.get("DB_PATH", str(DATA_DIR / "survey.db")))
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "triples-theme-admin-2026")
COMPANY = "טריפל אס אנרגיה מתחדשת"
IL = timezone(timedelta(hours=2))

app = Flask(__name__, static_folder="static", static_url_path="/static")


def now_il() -> str:
    return datetime.now(IL).strftime("%Y-%m-%d %H:%M:%S Asia/Jerusalem")


def db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS votes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          created_at TEXT NOT NULL,
          choice TEXT NOT NULL CHECK(choice IN ('A','B')),
          role TEXT,
          name TEXT,
          comment TEXT,
          ua TEXT
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


@app.get("/health")
def health():
    return jsonify(ok=True, service="theme-survey", company=COMPANY)


@app.get("/a/")
@app.get("/a")
def variant_a():
    return send_from_directory(APP_DIR / "static", "variant-a.html")


@app.get("/b/")
@app.get("/b")
def variant_b():
    return send_from_directory(APP_DIR / "static", "variant-b.html")


SURVEY_HTML = r"""
<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>סקר עיצוב דף הבית | {{ company }}</title>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;600;800&display=swap" rel="stylesheet">
<style>
:root{--r:#E2381B;--o:#FD8943;--s:#F6BA65;--bg:#f7f5f1;--ink:#232428;--ln:#e5e0d8}
*{box-sizing:border-box}body{margin:0;font-family:Heebo,Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.55}
.wrap{max-width:1100px;margin:auto;padding:16px 14px 48px}
.top{background:linear-gradient(100deg,var(--r),var(--o) 60%,var(--s));color:#fff;padding:18px 14px;text-align:center}
.top h1{margin:0;font-size:clamp(22px,5vw,32px);font-weight:800}
.top p{margin:8px 0 0;opacity:.95;font-size:15px}
.tabs{display:flex;gap:8px;margin:16px 0;flex-wrap:wrap}
.tabs button{flex:1;min-width:120px;padding:12px;border-radius:999px;border:1.5px solid var(--ln);background:#fff;font:700 15px Heebo;cursor:pointer}
.tabs button.on{background:#121316;color:#fff;border-color:#121316}
.frame-wrap{border:1px solid var(--ln);border-radius:18px;overflow:hidden;background:#121316;box-shadow:0 18px 40px -28px #0008}
.frame-wrap iframe{width:100%;height:min(72vh,720px);border:0;background:#121316;display:block}
.side{display:none;grid-template-columns:1fr 1fr;gap:10px}
@media(min-width:900px){.side.mode{display:grid}.single.mode{display:none}}
@media(max-width:899px){.side{display:none!important}.single{display:block}}
.card{background:#fff;border:1px solid var(--ln);border-radius:18px;padding:18px;margin-top:18px}
label{display:block;font-weight:700;margin:14px 0 6px}
.opts{display:grid;gap:10px}
.opt{display:flex;gap:12px;align-items:flex-start;padding:14px;border:1.5px solid var(--ln);border-radius:14px;cursor:pointer;background:#fff}
.opt:has(input:checked){border-color:var(--o);background:#fff8f2;box-shadow:0 0 0 3px #FD894333}
.opt input{margin-top:4px;accent-color:var(--r)}
input[type=text],select,textarea{width:100%;padding:12px 14px;border-radius:12px;border:1.5px solid var(--ln);font:inherit;background:#fff}
textarea{min-height:90px;resize:vertical}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;width:100%;margin-top:16px;padding:14px;border:0;border-radius:999px;font:800 16px Heebo;color:#fff;background:linear-gradient(100deg,var(--r),var(--o));cursor:pointer;box-shadow:0 10px 28px -12px #E2381B99}
.btn:disabled{opacity:.5;cursor:not-allowed}
.note{font-size:13px;color:#707176;margin-top:10px}
.ok{display:none;padding:18px;border-radius:14px;background:#eaf8ef;border:1px solid #b7e2c4;color:#165c2e;font-weight:700;margin-top:14px}
.links{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.links a{font-size:13px;color:var(--r);font-weight:700}
</style>
</head>
<body>
<div class="top">
  <h1>סקר קצר · עיצוב דף הבית</h1>
  <p>{{ company }} · שאלה אחת · אנונימי</p>
</div>
<div class="wrap">
  <div class="tabs" role="tablist">
    <button type="button" class="on" data-view="switch" id="t-switch">החלפה בין גרסאות</button>
    <button type="button" data-view="side" id="t-side">זו לצד זו (מחשב)</button>
  </div>
  <div class="tabs" id="ab-tabs">
    <button type="button" class="on" data-ab="a">גרסה A · כהה מלא</button>
    <button type="button" data-ab="b">גרסה B · גיבור כהה + שאר בהיר</button>
  </div>

  <div class="single mode" id="single">
    <div class="frame-wrap"><iframe id="frame" title="תצוגת גרסה" src="/a/" loading="lazy"></iframe></div>
  </div>
  <div class="side" id="side">
    <div>
      <div style="text-align:center;font-weight:800;margin-bottom:6px">A · כהה</div>
      <div class="frame-wrap"><iframe title="A" src="/a/" loading="lazy"></iframe></div>
    </div>
    <div>
      <div style="text-align:center;font-weight:800;margin-bottom:6px">B · משולב</div>
      <div class="frame-wrap"><iframe title="B" src="/b/" loading="lazy"></iframe></div>
    </div>
  </div>
  <div class="links">
    <a href="/a/" target="_blank" rel="noopener">פתיחת גרסה A בחלון חדש</a>
    <a href="/b/" target="_blank" rel="noopener">פתיחת גרסה B בחלון חדש</a>
  </div>

  <form class="card" id="form">
    <h2 style="margin:0 0 6px;font-size:22px">שאלה אחת</h2>
    <p style="margin:0;color:#5c5d62">איזו גרסה משדרת יותר אמון וגורמת לך לרצות לפנות?</p>
    <div class="opts" style="margin-top:14px">
      <label class="opt"><input type="radio" name="choice" value="A" required> <span><b>גרסה A</b> — רקע כהה מלא (העיצוב שנבחר)</span></label>
      <label class="opt"><input type="radio" name="choice" value="B" required> <span><b>גרסה B</b> — גיבור כהה, ושאר הדף בהיר</span></label>
    </div>
    <label for="role">תפקיד (אופציונלי)</label>
    <select id="role" name="role">
      <option value="">— בחירה —</option>
      <option value="צוות">צוות</option>
      <option value="לקוח">לקוח</option>
    </select>
    <label for="name">שם (אופציונלי)</label>
    <input id="name" name="name" type="text" maxlength="80" placeholder="לא חובה" autocomplete="name">
    <label for="comment">הערה (אופציונלי)</label>
    <textarea id="comment" name="comment" maxlength="500" placeholder="מה הרגיש יותר מזמין / פחות קודר?"></textarea>
    <button class="btn" type="submit" id="submit">שליחת תשובה</button>
    <p class="note">נשמרים רק בחירת הגרסה, ואם מילאתם — שם/תפקיד/הערה. בלי טלפון, מייל או מזהים אחרים.</p>
    <div class="ok" id="ok">תודה! התשובה נקלטה.</div>
  </form>
</div>
<script>
const frame=document.getElementById('frame');
const abTabs=document.querySelectorAll('#ab-tabs button');
const viewTabs=document.querySelectorAll('[data-view]');
const single=document.getElementById('single');
const side=document.getElementById('side');
abTabs.forEach(b=>b.onclick=()=>{
  abTabs.forEach(x=>x.classList.toggle('on',x===b));
  frame.src=b.dataset.ab==='a'?'/a/':'/b/';
});
viewTabs.forEach(b=>b.onclick=()=>{
  viewTabs.forEach(x=>x.classList.toggle('on',x===b));
  const sideMode=b.dataset.view==='side';
  single.classList.toggle('mode',!sideMode);
  side.classList.toggle('mode',sideMode);
  document.getElementById('ab-tabs').style.display=sideMode?'none':'flex';
});
document.getElementById('form').onsubmit=async(e)=>{
  e.preventDefault();
  const fd=new FormData(e.target);
  const btn=document.getElementById('submit');
  btn.disabled=true;
  try{
    const r=await fetch('/api/vote',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
      choice:fd.get('choice'), role:fd.get('role')||'', name:(fd.get('name')||'').toString().trim().slice(0,80),
      comment:(fd.get('comment')||'').toString().trim().slice(0,500)
    })});
    if(!r.ok) throw new Error('fail');
    document.getElementById('ok').style.display='block';
    e.target.querySelectorAll('input,select,textarea,button').forEach(el=>{if(el.id!=='submit') el.disabled=true;});
  }catch(err){
    alert('שליחה נכשלה, נסו שוב');
    btn.disabled=false;
  }
};
</script>
</body>
</html>
"""


@app.get("/")
def survey():
    return render_template_string(SURVEY_HTML, company=COMPANY)


@app.post("/api/vote")
def vote():
    data = request.get_json(silent=True) or {}
    choice = (data.get("choice") or "").strip().upper()
    if choice not in ("A", "B"):
        return jsonify(error="choice"), 400
    role = (data.get("role") or "").strip()
    if role and role not in ("צוות", "לקוח"):
        role = ""
    name = (data.get("name") or "").strip()[:80]
    comment = (data.get("comment") or "").strip()[:500]
    ua = (request.headers.get("User-Agent") or "")[:200]
    db().execute(
        "INSERT INTO votes(created_at,choice,role,name,comment,ua) VALUES(?,?,?,?,?,?)",
        (now_il(), choice, role or None, name or None, comment or None, ua),
    )
    db().commit()
    return jsonify(ok=True)


ADMIN_HTML = r"""
<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>תוצאות סקר עיצוב | {{ company }}</title>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;700;800&display=swap" rel="stylesheet">
<style>
body{margin:0;font-family:Heebo,Arial,sans-serif;background:#f7f5f1;color:#232428}
.wrap{max-width:960px;margin:auto;padding:20px 14px 40px}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:16px 0}
.card{background:#fff;border-radius:14px;padding:16px;border:1px solid #e5e0d8;text-align:center}
.card b{display:block;font-size:36px;font-weight:900}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:14px;overflow:hidden}
th,td{padding:10px;border-bottom:1px solid #eee;text-align:right;font-size:14px;vertical-align:top}
th{background:#121316;color:#fff}
.muted{color:#707176;font-size:13px}
</style>
</head>
<body>
<div class="wrap">
  <h1>תוצאות סקר עיצוב דף הבית</h1>
  <p class="muted">{{ company }} · גישה למנהלים בלבד · עודכן {{ now }}</p>
  <div class="cards">
    <div class="card"><span>סה״כ</span><b>{{ total }}</b></div>
    <div class="card"><span>גרסה A (כהה)</span><b>{{ a }}</b><div class="muted">{{ ap }}%</div></div>
    <div class="card"><span>גרסה B (משולב)</span><b>{{ b }}</b><div class="muted">{{ bp }}%</div></div>
  </div>
  <table>
    <thead><tr><th>#</th><th>זמן</th><th>בחירה</th><th>תפקיד</th><th>שם</th><th>הערה</th></tr></thead>
    <tbody>
    {% for r in rows %}
      <tr>
        <td>{{ r['id'] }}</td>
        <td>{{ r['created_at'] }}</td>
        <td><b>{{ r['choice'] }}</b></td>
        <td>{{ r['role'] or '—' }}</td>
        <td>{{ r['name'] or '—' }}</td>
        <td>{{ r['comment'] or '—' }}</td>
      </tr>
    {% else %}
      <tr><td colspan="6">עדיין אין תשובות</td></tr>
    {% endfor %}
    </tbody>
  </table>
</div>
</body>
</html>
"""


def _admin_ok() -> bool:
    token = request.args.get("token") or request.headers.get("X-Admin-Token") or ""
    cookie = request.cookies.get("theme_admin") or ""
    return secrets.compare_digest(token, ADMIN_TOKEN) or secrets.compare_digest(cookie, ADMIN_TOKEN)


@app.get("/admin/results")
@app.get("/results")
def results():
    if not _admin_ok():
        abort(401)
    rows = db().execute(
        "SELECT id,created_at,choice,role,name,comment FROM votes ORDER BY id DESC"
    ).fetchall()
    total = len(rows)
    a = sum(1 for r in rows if r["choice"] == "A")
    b = total - a
    ap = round(100 * a / total) if total else 0
    bp = round(100 * b / total) if total else 0
    resp = Response(
        render_template_string(
            ADMIN_HTML,
            company=COMPANY,
            now=now_il(),
            rows=rows,
            total=total,
            a=a,
            b=b,
            ap=ap,
            bp=bp,
        )
    )
    if request.args.get("token") == ADMIN_TOKEN:
        resp.set_cookie("theme_admin", ADMIN_TOKEN, httponly=True, samesite="Lax", max_age=60 * 60 * 24 * 30)
    return resp


@app.get("/favicon.ico")
def favicon():
    return send_from_directory(APP_DIR / "static", "logo.png")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8765)), debug=True)
