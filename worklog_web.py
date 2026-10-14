#!/usr/bin/env python3
"""
Jira Worklog Raporu - yerel web arayüzü.

Çift tıklanınca bilgisayarında küçük bir sunucu başlar ve tarayıcıda sayfa açılır.
- Sunucu yalnızca bu bilgisayardan erişilebilir (127.0.0.1); dışarıya açılmaz.
- Jira'ya yalnızca GET (okuma) isteği atılır. Token hiçbir dosyaya yazılmaz; istenirse işletim sisteminin
  şifreli anahtar deposunda (macOS Anahtar Zinciri, Windows Kimlik Bilgisi Yöneticisi) saklanır.
- Sekme kapatılınca uygulama kendini kapatır.
"""
from __future__ import annotations

import argparse
import atexit
import json
import os
import secrets
import shutil
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import worklog_core as core
from web_page import PAGE

APP_MARK = "jira-worklog-web"
PREFERRED_PORT = 47865            # ikinci kez çift tıklanırsa aynı pencereyi açabilmek için sabit
CONFIG_PATH = Path.home() / ".jira_worklog_app.json"   # token HARİÇ son kullanılan ayarlar
IDLE_TIMEOUT = 150                # sn: tarayıcıdan hiç sinyal gelmezse kapan (arka plan sekmeleri yavaşlar)
FIRST_TIMEOUT = 120               # sn: sayfa hiç açılmazsa kapan
BYE_GRACE = 10                    # sn: sekme kapandı sinyalinden sonra yeniden açılma (yenileme) payı
MAX_BODY = 64 * 1024


# --------------------------------------------------------------------------
# Ayarlar
# --------------------------------------------------------------------------
def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _iso_or(text, fallback):
    try:
        return core.parse_date(text).isoformat()
    except Exception:
        return fallback.isoformat()


# --------------------------------------------------------------------------
# Token deposu: işletim sisteminin şifreli anahtar deposu. Token Jira adresine bağlı saklanır, böylece
# yalnızca kaydedildiği adrese gönderilir; tarayıcıya hiç geri verilmez.
# --------------------------------------------------------------------------
KEYRING_SERVICE = "jira-worklog"
_keyring = None  # None: henüz bakılmadı, False: depo yok


def _store():
    global _keyring
    if _keyring is None:
        try:
            import keyring

            mod = type(keyring.get_keyring()).__module__
            _keyring = False if ("fail" in mod or "null" in mod) else keyring  # depo bulunamadıysa düz dosyaya düşmeyiz
        except Exception:
            _keyring = False
    return _keyring or None


def token_load(url: str) -> str | None:
    kr = _store()
    try:
        return kr.get_password(KEYRING_SERVICE, url) if kr and url else None
    except Exception:
        return None


def token_save(url: str, token: str) -> None:
    kr = _store()
    try:
        if kr:
            kr.set_password(KEYRING_SERVICE, url, token)
    except Exception:
        pass


def token_forget(url: str) -> None:
    kr = _store()
    try:
        if kr and token_load(url):
            kr.delete_password(KEYRING_SERVICE, url)
    except Exception:
        pass


def token_info(url: str) -> dict:
    try:
        url = core.normalize_url(url)
    except core.JiraError:
        url = ""
    store = {"darwin": "macOS Keychain", "win32": "Windows Credential Manager"}.get(sys.platform, "system keyring")
    return {"available": _store() is not None, "saved": bool(token_load(url)), "store": store}


def boot_payload() -> dict:
    cfg = load_config()
    prev, cur = core.previous_month_range(), core.current_month_range()
    preset = cfg.get("preset") if cfg.get("preset") in ("prev", "cur", "custom") else "prev"
    return {
        "url": cfg.get("url") or core.DEFAULT_URL,
        "project": cfg.get("project", ""),
        "preset": preset,
        "start": _iso_or(cfg.get("start", ""), prev[0]),
        "end": _iso_or(cfg.get("end", ""), prev[1]),
        "format": "csv" if "csv" in str(cfg.get("format", "")).lower() else "xlsx",
        "ranges": {"prev": [prev[0].isoformat(), prev[1].isoformat()],
                   "cur": [cur[0].isoformat(), cur[1].isoformat()]},
        "token": token_info(cfg.get("url") or ""),
    }


# --------------------------------------------------------------------------
# Uygulama durumu
# --------------------------------------------------------------------------
def _blank_job() -> dict:
    return {"state": "idle", "rev": 0, "stage": "", "done": 0, "total": 0, "message": "", "filename": None,
            "count": 0, "people": 0, "hours": 0.0, "daily": {}, "start": None, "end": None}


class AppState:
    def __init__(self):
        self.key = secrets.token_urlsafe(24)       # her çalıştırmada değişen gizli anahtar
        self.nonce = secrets.token_urlsafe(12)
        self.lock = threading.Lock()
        self.cancel = threading.Event()
        self.worker: threading.Thread | None = None
        self.tmpdir = Path(tempfile.mkdtemp(prefix="jira_worklog_"))
        self.file: Path | None = None
        self.rows: list[dict] | None = None        # önizleme tablosu için (yalnızca bellekte)
        self.started = time.time()
        self.last_ping: float | None = None
        self.bye_at: float | None = None
        self.job = _blank_job()

    def update(self, **kw):
        with self.lock:
            self.job.update(kw)
            self.job["rev"] += 1

    def snapshot(self) -> dict:
        with self.lock:
            return dict(self.job)

    def busy(self) -> bool:
        return self.worker is not None and self.worker.is_alive()

    def cleanup(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)


def start_job(state: AppState, payload: dict) -> None:
    """Girdileri doğrular ve işi başlatır. Geçersizse core.JiraError fırlatır."""
    if state.busy():
        raise core.JiraError("A report is already being prepared.")
    url = core.normalize_url(payload.get("url", ""))
    projects = core.parse_projects(payload.get("project", ""))
    preset = payload.get("preset")
    if preset == "prev":
        start, end = core.previous_month_range()
    elif preset == "cur":
        start, end = core.current_month_range()
    else:
        start, end = core.parse_date(payload.get("start", "")), core.parse_date(payload.get("end", ""))
    core.check_range(start, end)
    raw_token = str(payload.get("token", "")).strip()
    use_saved = not raw_token and bool(payload.get("useSaved"))
    if use_saved:
        token = token_load(url)
        if not token:
            raise core.JiraError("There is no saved token for this Jira address. Paste your token.")
    elif not raw_token:
        raise core.JiraError("Token cannot be empty. Click «How do I create one?» for help.")
    else:
        token = core.clean_token(raw_token)
    remember = not use_saved and bool(payload.get("remember"))
    if not use_saved and not remember:
        token_forget(url)  # "hatırlama" seçilmediyse eski kayıt da kalmasın
    fmt = "csv" if payload.get("format") == "csv" else "xlsx"

    if state.file:
        try:
            state.file.unlink()
        except OSError:
            pass
        state.file = None
    state.rows = None
    state.cancel.clear()
    with state.lock:
        state.job = _blank_job() | {"state": "running", "start": start.isoformat(), "end": end.isoformat(),
                                    "rev": state.job["rev"] + 1}
    save_config({"url": url, "project": ", ".join(projects), "preset": preset if preset in ("prev", "cur") else "custom",
                 "start": start.isoformat(), "end": end.isoformat(), "format": fmt})
    state.worker = threading.Thread(target=_run_job, args=(state, url, token, projects, start, end, fmt, use_saved, remember),
                                    daemon=True)
    state.worker.start()


def _row_json(r: dict) -> dict:
    return {"user": r["user"], "date": r["date"].isoformat(), "time": f"{r['time']:%H:%M}", "key": r["key"],
            "summary": r["summary"], "project": r["project"], "type": r["type"], "hours": r["hours"],
            "comment": r["comment"], "created": f"{r['created']:%Y-%m-%d %H:%M}" if r.get("created") else "",
            "url": r["url"]}


def _run_job(state: AppState, url, token, projects, start, end, fmt, use_saved=False, remember=False) -> None:
    def progress(stage, done, total):
        state.update(stage=stage, done=done, total=total)

    try:
        rows = core.fetch_report(url, token, projects, start, end, progress=progress, cancel=state.cancel)
        if remember:
            token_save(url, token)  # yalnızca Jira'nın kabul ettiği token saklanır
        if not rows:
            state.update(state="empty")
            return
        path = core.unique_path(state.tmpdir, core.default_filename(projects, start, end, fmt))
        if fmt == "xlsx":
            core.write_xlsx(rows, path, {"projects": projects, "start": start, "end": end, "url": url})
        else:
            core.write_csv(rows, path)
        daily: dict[str, float] = {}
        for r in rows:
            k = r["date"].isoformat()
            daily[k] = round(daily.get(k, 0) + r["hours"], 2)
        state.file = path
        state.rows = [_row_json(r) for r in rows]
        state.update(state="done", filename=path.name, count=len(rows), people=len({r["user"] for r in rows}),
                     hours=round(sum(r["hours"] for r in rows), 2), daily=daily)
    except core.Cancelled:
        state.update(state="cancelled")
    except core.JiraError as e:
        if use_saved and e.status == 401:
            token_forget(url)
            state.update(state="error", message="The saved token no longer works (it may have expired or been revoked), "
                                                "so it was removed. Paste a new token.")
        else:
            state.update(state="error", message=str(e))
    except ImportError:
        state.update(state="error", message="The component needed for Excel output is missing. Choose CSV and try again.")
    except OSError as e:
        state.update(state="error", message=f"Could not prepare the file: {e.strerror or e}")
    except Exception as e:  # beklenmeyen durum: kullanıcıya düz metin göster
        state.update(state="error", message=f"Unexpected error: {type(e).__name__}: {e}")


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------
def _safe_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def make_handler(state: AppState):
    class Handler(BaseHTTPRequestHandler):
        server_version = "JiraWorklog"

        def log_message(self, *args):  # token ve istek ayrıntıları hiçbir yere yazılmaz
            pass

        # -- yardımcılar --------------------------------------------------
        def _send(self, code: int, body: bytes = b"", ctype: str = "application/json; charset=utf-8", extra=None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if body and self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, code: int, obj) -> None:
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

        def _host_ok(self) -> bool:
            port = self.server.server_address[1]
            return self.headers.get("Host", "") in (f"127.0.0.1:{port}", f"localhost:{port}")

        def _key_ok(self, candidate: str | None) -> bool:
            return bool(candidate) and secrets.compare_digest(candidate, state.key)

        def _query(self) -> dict:
            return {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).items()}

        def _ping(self):
            state.last_ping = time.time()

        def _guard(self, via_query: bool = False) -> bool:
            if not self._host_ok():
                self._json(403, {"error": "forbidden"})
                return False
            candidate = self._query().get("k") if via_query else self.headers.get("X-App-Key")
            if not self._key_ok(candidate):
                self._json(403, {"error": "forbidden"})
                return False
            return True

        # -- GET ------------------------------------------------------------
        def do_GET(self):
            path = urllib.parse.urlparse(self.path).path
            if not self._host_ok():
                return self._json(403, {"error": "forbidden"})
            if path in ("/", "/index.html"):
                self._ping()
                html = (PAGE.replace("__NONCE__", state.nonce).replace("__APP_KEY__", state.key)
                        .replace("__BOOT__", _safe_json(boot_payload())))
                csp = (f"default-src 'none'; script-src 'nonce-{state.nonce}'; style-src 'nonce-{state.nonce}'; "
                       "connect-src 'self'; img-src data:; form-action 'none'; base-uri 'none'; frame-ancestors 'none'")
                return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8",
                                  {"Content-Security-Policy": csp, "X-Frame-Options": "DENY"})
            if path == "/api/hello":
                return self._json(200, {"app": APP_MARK})
            if path == "/api/status":
                if not self._guard():
                    return
                self._ping()
                return self._json(200, state.snapshot())
            if path == "/api/token":
                if not self._guard():
                    return
                return self._json(200, token_info(self._query().get("url", "")))
            if path == "/api/rows":
                if not self._guard():
                    return
                rows = state.rows
                if state.snapshot()["state"] != "done" or rows is None:
                    return self._json(404, {"error": "No report is ready."})
                return self._json(200, {"rows": rows})
            if path == "/download":
                if not self._guard(via_query=True):
                    return
                f = state.file
                if state.snapshot()["state"] != "done" or not f or not f.exists():
                    return self._json(404, {"error": "No report is ready."})
                ctype = ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if f.suffix == ".xlsx"
                         else "text/csv; charset=utf-8")
                return self._send(200, f.read_bytes(), ctype,
                                  {"Content-Disposition": f'attachment; filename="{f.name}"'})
            self._json(404, {"error": "not found"})

        # -- POST -----------------------------------------------------------
        def do_POST(self):
            path = urllib.parse.urlparse(self.path).path
            if path == "/api/bye":  # sendBeacon özel başlık gönderemez; anahtar adreste
                if not self._guard(via_query=True):
                    return
                state.bye_at = time.time()
                return self._send(204)
            if not self._guard():
                return
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self._json(413, {"error": "Request too large."})
            raw = self.rfile.read(length) if length else b""
            if path == "/api/start":
                try:
                    payload = json.loads(raw.decode("utf-8") or "{}")
                    if not isinstance(payload, dict):
                        raise ValueError
                except ValueError:
                    return self._json(400, {"error": "Could not read the request."})
                try:
                    start_job(state, payload)
                except core.JiraError as e:
                    return self._json(409 if state.busy() else 400, {"error": str(e)})
                return self._json(200, {"ok": True})
            if path == "/api/cancel":
                state.cancel.set()
                return self._json(200, {"ok": True})
            if path == "/api/token/forget":
                try:
                    url = core.normalize_url(json.loads(raw.decode("utf-8") or "{}").get("url", ""))
                except (ValueError, AttributeError, core.JiraError):
                    return self._json(400, {"error": "Could not read the request."})
                token_forget(url)
                return self._json(200, token_info(url))
            self._json(404, {"error": "not found"})

    return Handler


class Server(ThreadingHTTPServer):
    # Windows'ta SO_REUSEADDR aynı porta ikinci bağlanmaya izin verir; tek örnek kontrolü bozulmasın
    allow_reuse_address = os.name != "nt"


def watchdog(state: AppState, server: ThreadingHTTPServer) -> None:
    """Sekme kapanınca (ya da hiç açılmazsa) uygulamanın arka planda takılı kalmasını önler."""
    while True:
        time.sleep(2)
        if state.busy():
            continue
        now = time.time()
        if state.last_ping is None:
            if now - state.started > FIRST_TIMEOUT:
                break
        else:
            if state.bye_at and state.last_ping < state.bye_at and now - state.bye_at > BYE_GRACE:
                break
            if now - state.last_ping > IDLE_TIMEOUT:
                break
    threading.Thread(target=server.shutdown, daemon=True).start()


def already_running(port: int) -> bool:
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # şirket proxy'si localhost'a karışmasın
        with opener.open(f"http://127.0.0.1:{port}/api/hello", timeout=1.5) as r:
            return json.load(r).get("app") == APP_MARK
    except Exception:
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Jira Worklog Report (local web interface)")
    ap.add_argument("--port", type=int, default=None, help="Specific port (0 = random)")
    ap.add_argument("--no-browser", action="store_true", help="Do not open the browser automatically")
    args, _ = ap.parse_known_args(argv)  # macOS'un eklediği -psn_... gibi argümanlara takılma
    no_browser = args.no_browser or bool(os.environ.get("JIRA_WORKLOG_NO_BROWSER"))

    state = AppState()
    atexit.register(state.cleanup)
    server = None
    for port in ([args.port] if args.port is not None else [PREFERRED_PORT, 0]):
        try:
            server = Server(("127.0.0.1", port), make_handler(state))
            break
        except OSError:
            if port == PREFERRED_PORT and already_running(port):
                if not no_browser:
                    webbrowser.open(f"http://127.0.0.1:{port}/")
                return 0  # zaten açık; mevcut pencereyi öne getirdik
    if server is None:
        print("Could not start the app: the port is in use or could not be opened.", file=sys.stderr)
        return 1

    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Jira Worklog Report: {url}", flush=True)
    threading.Thread(target=watchdog, args=(state, server), daemon=True).start()
    if not no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        state.cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
