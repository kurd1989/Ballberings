# -*- coding: utf-8 -*-
"""
سامانه خط نورد — نسخه پایدار دسکتاپ 1.0.0-stable
داده‌ها در SQLite کنار برنامه (پوشه data/app.db) ذخیره می‌شوند.
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

APP_DIR = Path(__file__).resolve().parent
WWW = APP_DIR / "www"
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


class Api:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._lock = threading.Lock()

    def kv_all(self, payload=None):
        with self._lock:
            rows = self.conn.execute("SELECT key, value FROM kv").fetchall()
        return {k: v for k, v in rows}

    def kv_get(self, payload):
        key = (payload or {}).get("key")
        if not key:
            return None
        with self._lock:
            row = self.conn.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def kv_set(self, payload):
        payload = payload or {}
        key = payload.get("key")
        value = payload.get("value")
        if key is None:
            return {"ok": False, "error": "missing key"}
        if value is None:
            value = ""
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False)
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO kv(key, value, updated_at)
                VALUES(?,?,datetime('now','localtime'))
                ON CONFLICT(key) DO UPDATE SET
                  value=excluded.value,
                  updated_at=datetime('now','localtime')
                """,
                (key, value),
            )
            self.conn.commit()
        return {"ok": True, "persistent": True}

    def kv_remove(self, payload):
        key = (payload or {}).get("key")
        if not key:
            return {"ok": False}
        with self._lock:
            self.conn.execute("DELETE FROM kv WHERE key=?", (key,))
            self.conn.commit()
        return {"ok": True}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WWW), **kwargs)

    def log_message(self, fmt, *args):
        sys.stdout.write("[http] " + (fmt % args) + "\n")


def start_server():
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def main():
    if not (WWW / "rolling-mill-system.html").exists():
        print("فایل www/rolling-mill-system.html یافت نشد.", file=sys.stderr)
        sys.exit(1)

    conn = ensure_db()
    api = Api(conn)
    start_server()
    url = f"http://127.0.0.1:{PORT}/rolling-mill-system.html"
    print("=" * 60)
    print("سامانه خط نورد — نسخه پایدار دسکتاپ 1.0.0-stable")
    print(f"آدرس: {url}")
    print(f"دیتابیس: {DB_PATH}")
    print("برای خروج: Ctrl+C")
    print("=" * 60)

    # pywebview اگر نصب باشد پنجره دسکتاپ باز می‌کند
    try:
        import webview

        window = webview.create_window(
            "سامانه خط نورد",
            url,
            width=1400,
            height=900,
            js_api=api,
        )

        def on_ready():
            # بارگذاری تمام کلیدها داخل صفحه
            try:
                all_kv = api.kv_all()
                js = "window.__deskKV = " + json.dumps(all_kv, ensure_ascii=False) + ";"
                js += "window.RollingMillDesktop = window.pywebview.api;"
                js += "window.__deskReady = true;"
                window.evaluate_js(js)
            except Exception as e:
                print("inject kv:", e)

        webview.start(on_ready)
    except ImportError:
        print("pywebview نصب نیست — مرورگر پیش‌فرض باز می‌شود.")
        print("برای پنجره دسکتاپ: pip install pywebview")
        # بدون pywebview، از endpoint ساده JSON استفاده نمی‌کنیم مگر پچ fetch؛
        # حداقل مرورگر + localStorage. برای DB کامل pywebview لازم است.
        webbrowser.open(url)
        try:
            while True:
                threading.Event().wait(3600)
        except KeyboardInterrupt:
            print("\nخروج.")


if __name__ == "__main__":
    main()
