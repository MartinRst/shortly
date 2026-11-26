import secrets
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, HttpUrl

DB = Path(__file__).resolve().parent.parent / "shortly.db"

app = FastAPI(title="Shortly")


def db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS links (code TEXT PRIMARY KEY, url TEXT NOT NULL, hits INTEGER DEFAULT 0)")
    return conn


class LinkIn(BaseModel):
    url: HttpUrl


@app.get("/health")
def health():
    with db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
    return {"status": "ok", "links": count}


@app.post("/api/links", status_code=201)
def create_link(link: LinkIn):
    code = secrets.token_urlsafe(4)
    with db() as conn:
        conn.execute("INSERT INTO links (code, url) VALUES (?, ?)", (code, str(link.url)))
    return {"code": code, "url": str(link.url), "short": f"/{code}"}


@app.get("/api/links/{code}")
def get_link(code: str):
    with db() as conn:
        row = conn.execute("SELECT url, hits FROM links WHERE code = ?", (code,)).fetchone()
    if not row:
        raise HTTPException(404, "Unknown code")
    return {"code": code, "url": row[0], "hits": row[1]}


@app.get("/{code}")
def follow(code: str):
    with db() as conn:
        row = conn.execute("SELECT url FROM links WHERE code = ?", (code,)).fetchone()
        if not row:
            raise HTTPException(404, "Unknown code")
        conn.execute("UPDATE links SET hits = hits + 1 WHERE code = ?", (code,))
    return RedirectResponse(row[0], status_code=307)


@app.get("/", response_class=HTMLResponse)
def home():
    with db() as conn:
        rows = conn.execute("SELECT code, url, hits FROM links ORDER BY rowid DESC LIMIT 20").fetchall()
    items = "".join(f"<tr><td><a href='/{c}'>/{c}</a></td><td>{u}</td><td>{h}</td></tr>" for c, u, h in rows)
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Shortly</title>
<style>body{{font-family:system-ui;max-width:720px;margin:3rem auto;padding:0 1rem}}input{{width:70%;padding:.5rem}}button{{padding:.5rem 1rem}}table{{width:100%;margin-top:2rem;border-collapse:collapse}}td{{padding:.4rem;border-bottom:1px solid #ddd}}</style></head>
<body><h1>Shortly</h1><p>Paste a long URL, get a short one.</p>
<form onsubmit="event.preventDefault();fetch('/api/links',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{url:this.url.value}})}}).then(()=>location.reload())">
<input name="url" placeholder="https://kestra.io/docs" required> <button>Shorten</button></form>
<table><tr><th align=left>Short</th><th align=left>URL</th><th align=left>Hits</th></tr>{items}</table></body></html>"""
