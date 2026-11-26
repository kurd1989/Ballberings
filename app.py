# -*- coding: utf-8 -*-
"""
سامانه خط نورد — نسخه پایدار دسکتاپ 1.0.1-stable
بدون وابستگی به pywebview/pythonnet (سازگار با PyInstaller EXE)
داده‌ها در SQLite: data/app.db
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        # PyInstaller onedir: exe next to _internal; data beside exe
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

APP_DIR = app_dir()
WWW = APP_DIR / "www"
if not WWW.exists() and getattr(sys, "frozen", False):
    # sometimes bundled under _MEIPASS
    meipass = Path(getattr(sys, "_MEIPASS", ""))
    if (meipass / "www").exists():
        WWW = meipass / "www"

DATA = APP_DIR / "data"
DB_PATH = DATA / "app.db"
PORT = int(os.environ.get("ROLLING_MILL_PORT", "8765"))


def ensure_db() -> sqlite3.Connection:
    DATA.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS kv (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )
        """
    )
    conn.commit()
    return conn


class AppState:
    def __init__(self):
        self.conn = ensure_db()
        self.lock = threading.Lock()

    def all(self):
        with self.lock:
            rows = self.conn.execute("SELECT key, value FROM kv").fetchall()
        return {k: v for k, v in rows}

    def get(self, key: str):
        with self.lock:
            row = self.conn.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def set(self, key: str, value: str):
        with self.lock:
            self.conn.execute(
                """
                INSERT INTO kv(key, value, updated_at)
                VALUES(?,?,datetime('now','localtime'))
                ON CONFLICT(key) DO UPDATE SET
                  value=excluded.value,
                  updated_at=datetime('now','localtime')
                """,
                (key, value if value is not None else ""),
            )
            self.conn.commit()


STATE = AppState()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WWW), **kwargs)

    def _json(self, code: int, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/kv":
            return self._json(200, STATE.all())
        if path.startswith("/api/kv/"):
            key = path[len("/api/kv/") :]
            val = STATE.get(key)
            return self._json(200, {"key": key, "value": val})
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/kv":
            data = self._read_json()
            key = data.get("key")
            value = data.get("value")
            if key is None:
                return self._json(400, {"ok": False, "error": "missing key"})
            if value is not None and not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)
            STATE.set(str(key), value if value is not None else "")
            return self._json(200, {"ok": True, "persistent": True})
        return self._json(404, {"ok": False, "error": "not found"})

    def log_message(self, fmt, *args):
        try:
            sys.stdout.write("[http] " + (fmt % args) + "\n")
        except Exception:
            pass


def main():
    if not (WWW / "rolling-mill-system.html").exists():
        # message box style for frozen
        msg = f"فایل رابط یافت نشد:\n{WWW / 'rolling-mill-system.html'}"
        print(msg, file=sys.stderr)
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, msg, "RollingMill", 0x10)
        except Exception:
            pass
        sys.exit(1)

    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{PORT}/rolling-mill-system.html"
    print("=" * 60)
    print("سامانه خط نورد 1.0.1-stable")
    print(url)
    print("DB:", DB_PATH)
    print("=" * 60)
    webbrowser.open(url)

    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    main()
