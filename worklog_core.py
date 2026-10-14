"""
Jira Server / Data Center worklog çekirdeği (arayüzden bağımsız).

- Jira'ya yalnızca GET (okuma) isteği atar. Yazma/silme yapmaz.
- Token yalnızca bellekte tutulur; hiçbir dosyaya yazılmaz.
- Sadece Python standart kütüphanesini kullanır (xlsx çıktısı için openpyxl hariç).
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import re
import socket
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

DEFAULT_URL = ""  # kasıtlı olarak boş: adres ilk kullanımda sorulur ve yerel ayar dosyasına kaydedilir

COLUMNS = ["User", "Date", "Start Time", "Issue", "Summary", "Project", "Type", "Hours", "Comment", "Logged At"]

# Türkiye 2016'dan beri yıl boyunca UTC+3 (yaz/kış saati uygulaması yok); ek bileşen gerekmez.
TURKEY_TZ = timezone(timedelta(hours=3))
_JIRA_DT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.\d+)?(Z|[+-]\d{2}:?\d{2})?$")

_PROJECT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_URL_CUT_MARKERS = ("/browse", "/secure", "/projects", "/issues", "/rest", "/plugins", "/login", "/dashboard")

ProgressFn = Callable[[str, int, int], None]  # (aşama, tamamlanan, toplam)

# Jira'ya giden istek sayısını azaltmak için worklog'lar arama yanıtına gömülü istenir (issue başına en fazla 20).
# Sunucunun üst sınırı daha düşükse dönen kayıt sayısına göre sayfalanır.
SEARCH_PAGE_SIZE = 500
DETAIL_WORKERS = 4      # yalnızca 20'den fazla worklog'u olan task'lar için; istek sayısını değil süreyi etkiler
LEGACY_PAGE_SIZE = 100  # önceki yöntem: 100'lük arama sayfaları + her task için ayrı worklog isteği


class JiraError(Exception):
    """Kullanıcıya olduğu gibi gösterilebilecek, anlaşılır hata. Jira'dan geldiyse HTTP kodu `status`'tadır."""

    def __init__(self, message: str, status: Optional[int] = None):
        super().__init__(message)
        self.status = status


class Cancelled(Exception):
    """Kullanıcı işlemi iptal etti."""


# --------------------------------------------------------------------------
# Girdi doğrulama / düzeltme
# --------------------------------------------------------------------------
def parse_date(text: str) -> date:
    text = (text or "").strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise JiraError(f"Could not read the date '{text}'. Example: 01.09.2026")


def parse_projects(text: str) -> list[str]:
    keys = [k.strip().upper() for k in re.split(r"[,\s;]+", text or "") if k.strip()]
    if not keys:
        raise JiraError("Project key cannot be empty. Example: PROJ (separate several with commas).")
    for k in keys:
        if not _PROJECT_RE.match(k):
            raise JiraError(
                f"Invalid project key '{k}'. Use only letters, digits and underscores (example: PROJ)."
            )
    return keys


def check_range(start: date, end: date) -> None:
    if end < start:
        raise JiraError("The end date cannot be before the start date.")


def normalize_url(text: str) -> str:
    """'https://jira.sirket.com/browse/ABC-1?filter=-4' gibi yapıştırılan adresi ana adrese indirir."""
    text = (text or "").strip()
    if not text:
        raise JiraError("Jira address cannot be empty.")
    if not re.match(r"^https?://", text, re.I):
        text = "https://" + text
    parsed = urllib.parse.urlparse(text)
    if not parsed.netloc:
        raise JiraError(f"Could not read the Jira address '{text}'.")
    path = parsed.path
    for marker in _URL_CUT_MARKERS:
        idx = path.find(marker)
        if idx != -1:
            path = path[:idx]
    return f"{parsed.scheme}://{parsed.netloc}{path}".rstrip("/")


def clean_token(token: str) -> str:
    token = (token or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token:
        raise JiraError("Token cannot be empty.")
    return token


def previous_month_range(today: Optional[date] = None) -> tuple[date, date]:
    today = today or date.today()
    last_prev = today.replace(day=1) - timedelta(days=1)
    return last_prev.replace(day=1), last_prev


def current_month_range(today: Optional[date] = None) -> tuple[date, date]:
    today = today or date.today()
    return today.replace(day=1), today


def parse_jira_datetime(text: str) -> datetime:
    """'2026-09-03T10:15:00.000+0300' -> saat dilimi bilgili datetime. Ofset yoksa Türkiye saati varsayılır."""
    m = _JIRA_DT_RE.match((text or "").strip())
    if not m:
        raise JiraError(f"Jira returned an unexpected date/time: '{text}'.")
    naive = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S")
    off = m.group(2)
    if off is None:
        tz = TURKEY_TZ
    elif off == "Z":
        tz = timezone.utc
    else:
        digits = off[1:].replace(":", "")
        delta = timedelta(hours=int(digits[:2]), minutes=int(digits[2:]))
        tz = timezone(-delta if off[0] == "-" else delta)
    return naive.replace(tzinfo=tz)


def to_turkey_time(text: str) -> datetime:
    """Jira'nın verdiği zamanı Türkiye saatine çevirir (saat dilimsiz, duvar saati olarak döner)."""
    return parse_jira_datetime(text).astimezone(TURKEY_TZ).replace(tzinfo=None)


# --------------------------------------------------------------------------
# Jira istemcisi (yalnızca GET)
# --------------------------------------------------------------------------
class RequestStats:
    """Jira'ya giden istek sayısı ve indirilen veri (sunucu yükünün göstergesi). Birden çok iş parçacığından yazılır."""

    def __init__(self):
        self._lock = threading.Lock()
        self._t0 = time.monotonic()
        self.requests = 0
        self.bytes = 0
        self.baseline = 0  # önceki yöntemle aynı rapor için gereken istek sayısı
        self.seconds = 0.0

    def add(self, nbytes: int) -> None:
        with self._lock:
            self.requests += 1
            self.bytes += nbytes

    def finish(self, issues: int) -> None:
        self.baseline = math.ceil(issues / LEGACY_PAGE_SIZE) + issues if issues else self.requests
        self.seconds = time.monotonic() - self._t0

    def as_dict(self) -> dict:
        with self._lock:
            return {"requests": self.requests, "bytes": self.bytes, "baseline": self.baseline,
                    "seconds": round(self.seconds or time.monotonic() - self._t0, 1)}


def _read_body(resp) -> bytes:
    raw = resp.read()
    if (resp.headers.get("Content-Encoding") or "").lower() == "gzip":
        raw = gzip.decompress(raw)
    return raw


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    """Token'ın başka bir sunucuya (ya da şifresiz http'ye) yönlendirilmesini engeller."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old = urllib.parse.urlparse(req.full_url)
        new = urllib.parse.urlparse(newurl)
        if new.netloc != old.netloc or (old.scheme == "https" and new.scheme != "https"):
            raise JiraError(
                "Jira redirected to a different address, so the request was stopped for security. "
                "Make sure the Jira address matches the one in your browser."
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class JiraClient:
    def __init__(self, base_url: str, token: str, timeout: int = 60, stats: Optional[RequestStats] = None):
        self.base_url = normalize_url(base_url)
        self._token = clean_token(token)
        self.timeout = timeout
        self.stats = stats or RequestStats()
        self._openers = self._build_openers()
        self._opener_idx = 0

    @staticmethod
    def _build_openers() -> list:
        contexts = []
        try:
            import truststore  # işletim sisteminin sertifika deposu (şirket kök sertifikaları dahil); Python 3.10+

            contexts.append(truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT))
        except Exception:
            pass
        contexts.append(ssl.create_default_context())  # Python'ın kendi sertifika ayarları
        try:
            import certifi  # paketlenmiş uygulamada sistem deposu olmayabilir

            contexts.append(ssl.create_default_context(cafile=certifi.where()))
        except Exception:
            pass
        return [
            urllib.request.build_opener(urllib.request.HTTPSHandler(context=c), _SafeRedirect())
            for c in contexts
        ]

    # -- düşük seviye -------------------------------------------------------
    def get_json(self, path: str, params: Optional[dict] = None):
        url = self.base_url + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        attempt = 0
        while True:
            req = urllib.request.Request(
                url,
                method="GET",  # bu uygulamada başka bir HTTP metodu kullanılmaz
                headers={"Authorization": "Bearer " + self._token, "Accept": "application/json",
                         "Accept-Encoding": "gzip"},  # sunucuda sıkıştırma açıksa veri ~10 kat küçülür
            )
            try:
                with self._openers[self._opener_idx].open(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                    self.stats.add(len(raw))
                    if (resp.headers.get("Content-Encoding") or "").lower() == "gzip":
                        raw = gzip.decompress(raw)
                    return json.loads(raw)
            except urllib.error.HTTPError as e:
                self.stats.add(0)
                if e.code in (429, 502, 503, 504) and attempt < 3:
                    try:
                        delay = float(e.headers.get("Retry-After", ""))
                    except ValueError:
                        delay = 2**attempt
                    time.sleep(min(delay, 30))
                    attempt += 1
                    continue
                raise self._http_error(e) from None
            except urllib.error.URLError as e:
                if isinstance(e.reason, ssl.SSLCertVerificationError):
                    if self._opener_idx + 1 < len(self._openers):
                        self._opener_idx += 1
                        continue
                    raise JiraError(
                        "The security certificate could not be verified. Make sure you are on the company "
                        "network/VPN; if the problem persists, contact IT."
                    ) from None
                raise JiraError(
                    "Could not reach Jira. Check your internet/VPN connection and the Jira address."
                ) from None
            except (TimeoutError, socket.timeout):
                raise JiraError("Jira did not respond in time. Please try again shortly.") from None
            except (ValueError, EOFError, gzip.BadGzipFile):  # JSON/UTF-8/gzip çözülemedi
                raise JiraError(
                    "Jira returned an unexpected response (possibly a login page). "
                    "Check the Jira address and the token."
                ) from None

    @staticmethod
    def _http_error(e: urllib.error.HTTPError) -> JiraError:
        detail = ""
        try:
            body = json.loads(_read_body(e).decode("utf-8", "replace"))
            msgs = body.get("errorMessages") or []
            detail = " ".join(msgs) if msgs else ""
        except Exception:
            pass
        if e.code == 401:
            msg = "The token is invalid, expired or was pasted incorrectly (401)."
        elif e.code == 403:
            msg = "You do not have permission for this (403). Make sure you have access to the project."
        elif e.code == 404:
            msg = "Address not found (404). Check the Jira address."
        elif e.code == 400:
            msg = "Jira rejected the query" + (f": {detail}" if detail else " (400).")
        else:
            msg = f"Jira returned an error (HTTP {e.code})." + (f" {detail}" if detail else "")
        return JiraError(msg, e.code)

    # -- yüksek seviye ------------------------------------------------------
    def iter_issues(self, projects: list[str], start: date, end: date, cancel=None):
        """Dönemde worklog'u olan issue'ları, worklog'ları gömülü olarak sayfa sayfa verir: (sayfa, toplam).

        Jira gömülü alanda issue başına en fazla 20 worklog döndürür; eksik kalanlar issue_worklogs ile tamamlanır.
        """
        proj = ", ".join(f'"{p}"' for p in projects)
        jql = (f'project in ({proj}) AND worklogDate >= "{start:%Y-%m-%d}" AND worklogDate <= "{end:%Y-%m-%d}" '
               "ORDER BY key ASC")  # sabit sıra: sayfalar arasında kayıt eklense de issue kaçmaz/tekrarlanmaz
        start_at = 0
        while True:
            _check_cancel(cancel)
            data = self.get_json(
                "/rest/api/2/search",
                {"jql": jql, "fields": "summary,project,issuetype,worklog", "startAt": start_at,
                 "maxResults": SEARCH_PAGE_SIZE},
            )
            batch = data.get("issues", [])
            total = data.get("total", 0)
            yield batch, total
            start_at += len(batch)
            if not batch or start_at >= total:
                break

    def issue_worklogs(self, key: str) -> list[dict]:
        path = f"/rest/api/2/issue/{urllib.parse.quote(key)}/worklog"
        data = self.get_json(path)
        out = list(data.get("worklogs", []))
        # Çok nadir: kayıtlar tek yanıta sığmadıysa kalanını sayfalayarak al
        while out and len(out) < data.get("total", len(out)):
            more = self.get_json(path, {"startAt": len(out), "maxResults": 1000}).get("worklogs", [])
            if not more:
                break
            out.extend(more)
        return out


def _check_cancel(cancel) -> None:
    if cancel is not None and cancel.is_set():
        raise Cancelled()


def _embedded_worklogs(issue: dict) -> Optional[list]:
    """Arama yanıtındaki worklog'lar eksiksizse onları, değilse (ya da alan gizliyse) None döndürür."""
    field = (issue.get("fields") or {}).get("worklog")
    if not isinstance(field, dict) or not isinstance(field.get("worklogs"), list):
        return None
    logs = field["worklogs"]
    return logs if len(logs) >= (field.get("total") or 0) else None


def _issue_rows(issue: dict, worklogs: list, start: date, end: date, base_url: str) -> list[dict]:
    key = issue["key"]
    fields = issue.get("fields", {})
    rows = []
    for w in worklogs:
        started = to_turkey_time(w["started"])  # Jira'nın verdiği ofset okunur, Türkiye saatine çevrilir
        if not (start <= started.date() <= end):
            continue
        created = to_turkey_time(w["created"]) if w.get("created") else None
        rows.append(
            {
                "user": (w.get("author") or {}).get("displayName", "?"),
                "date": started.date(),
                "time": started.time().replace(second=0),
                "key": key,
                "summary": fields.get("summary", ""),
                "project": (fields.get("project") or {}).get("key", ""),
                "type": (fields.get("issuetype") or {}).get("name", ""),
                "hours": round(w.get("timeSpentSeconds", 0) / 3600, 2),
                "comment": str(w.get("comment") or "").replace("\r", " ").replace("\n", " ").strip(),
                "created": created,
                "url": f"{base_url}/browse/{key}",
            }
        )
    return rows


def fetch_report(
    base_url: str,
    token: str,
    projects: list[str],
    start: date,
    end: date,
    progress: Optional[ProgressFn] = None,
    cancel=None,
    stats: Optional[RequestStats] = None,
) -> list[dict]:
    """Seçilen proje(ler) ve tarih aralığı için worklog satırlarını döndürür.

    İstek sayısı: arama sayfaları (500'lük) + yalnızca 20'den fazla worklog'u olan task'lar için birer istek.
    """
    check_range(start, end)
    client = JiraClient(base_url, token, stats=stats)
    say = progress or (lambda stage, done, total: None)

    say("search", 0, 0)
    rows: list[dict] = []
    seen: set[str] = set()
    pending: dict = {}  # future -> issue (worklog'ları ayrıca çekilen task'lar)
    done = total = 0

    def collect(futures) -> None:
        nonlocal done
        for fut in futures:
            issue = pending.pop(fut)
            rows.extend(_issue_rows(issue, fut.result(), start, end, client.base_url))
            done += 1

    pool = ThreadPoolExecutor(max_workers=DETAIL_WORKERS)
    try:
        # Jira "worklogDate"i kendi saat diliminde değerlendirir; Türkiye saatiyle gün sınırında kalan kayıtlar
        # kaçmasın diye aralığı bir gün genişletip kesin filtreyi Türkiye saatine göre uygularız.
        for batch, total in client.iter_issues(projects, start - timedelta(days=1), end + timedelta(days=1), cancel):
            for issue in batch:
                if issue["key"] in seen:
                    continue
                seen.add(issue["key"])
                logs = _embedded_worklogs(issue)
                if logs is None:
                    pending[pool.submit(client.issue_worklogs, issue["key"])] = issue
                else:
                    rows.extend(_issue_rows(issue, logs, start, end, client.base_url))
                    done += 1
            collect([f for f in pending if f.done()])
            say("issues", done, max(total, done))
        while pending:
            _check_cancel(cancel)
            finished, _ = wait(list(pending), timeout=0.5, return_when=FIRST_COMPLETED)
            if finished:
                collect(finished)
                say("issues", done, max(total, done))
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
        client.stats.finish(len(seen))

    rows.sort(key=lambda r: (r["user"].lower(), r["date"], r["time"], r["key"]))
    return rows


# --------------------------------------------------------------------------
# Çıktı dosyaları
# --------------------------------------------------------------------------
def default_filename(projects: list[str], start: date, end: date, ext: str) -> str:
    proj = "-".join(projects) if len(projects) <= 3 else f"{len(projects)}-projects"
    return f"Jira_Worklog_{proj}_{start:%Y-%m-%d}_{end:%Y-%m-%d}.{ext}"


def unique_path(directory: Path, filename: str) -> Path:
    """Aynı isimli dosya varsa (ya da Excel'de açıksa) üstüne yazmamak için ' (2)' ekler."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    stem, suffix, n = path.stem, path.suffix, 2
    while path.exists():
        path = directory / f"{stem} ({n}){suffix}"
        n += 1
    return path


def write_csv(rows: list[dict], path: Path, delimiter: str = ";", decimal_comma: bool = True) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig: Excel Türkçe karakterleri doğru açar
        w = csv.writer(f, delimiter=delimiter)
        w.writerow(COLUMNS)
        for r in rows:
            hours = str(r["hours"]).replace(".", ",") if decimal_comma else str(r["hours"])
            w.writerow(
                [r["user"], f"{r['date']:%Y-%m-%d}", f"{r['time']:%H:%M}", r["key"], r["summary"],
                 r["project"], r["type"], hours, r["comment"],
                 f"{r['created']:%Y-%m-%d %H:%M}" if r.get("created") else ""]
            )


def write_xlsx(rows: list[dict], path: Path, meta: dict) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.worksheet.table import Table, TableStyleInfo

    wb = Workbook()
    ws = wb.active
    ws.title = "Worklog"
    ws.append(COLUMNS)
    for r in rows:
        ws.append([r["user"], datetime.combine(r["date"], datetime.min.time()), r["time"], r["key"], r["summary"], r["project"], r["type"], r["hours"],
                   r["comment"], r.get("created")])

    last = len(rows) + 1
    for row in ws.iter_rows(min_row=2, max_row=last):
        # Küçük harfli biçim kodları Excel dışı programlarda (Numbers, Önizleme vb.) da tarih olarak tanınır.
        row[1].number_format = "dd.mm.yyyy"
        row[2].number_format = "hh:mm"
        row[7].number_format = "0.00"
        row[9].number_format = "dd.mm.yyyy hh:mm"
        for c in (row[1], row[2], row[9]):
            c.alignment = Alignment(horizontal="left")
        url = rows[row[0].row - 2]["url"]
        row[3].hyperlink = url
        row[3].style = "Hyperlink"

    table = Table(displayName="Worklog", ref=f"A1:{chr(64 + len(COLUMNS))}{last}")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(table)
    ws.freeze_panes = "A2"
    for col, width in zip("ABCDEFGHIJ", (24, 12, 14, 14, 52, 10, 14, 8, 60, 18)):
        ws.column_dimensions[col].width = width

    # Özet sayfası: kişi bazında toplam
    summ = wb.create_sheet("Overview")
    summ.append(["User", "Worklogs", "Total hours"])
    per_user: dict[str, list] = {}
    for r in rows:
        agg = per_user.setdefault(r["user"], [0, 0.0])
        agg[0] += 1
        agg[1] += r["hours"]
    for user, (count, hours) in sorted(per_user.items(), key=lambda kv: -kv[1][1]):
        summ.append([user, count, round(hours, 2)])
    summ.append(["Total", len(rows), round(sum(r["hours"] for r in rows), 2)])
    for cell in summ[1] + summ[summ.max_row]:
        cell.font = Font(bold=True)
    for row in summ.iter_rows(min_row=2):
        row[2].number_format = "0.00"
    summ.column_dimensions["A"].width = 28
    summ.column_dimensions["B"].width = 16
    summ.column_dimensions["C"].width = 14
    info_row = summ.max_row + 2
    for label, value in (
        ("Projects", ", ".join(meta.get("projects", []))),
        ("Period", f"{meta['start']:%d.%m.%Y} – {meta['end']:%d.%m.%Y}"),
        ("Created", f"{datetime.now():%d.%m.%Y %H:%M}"),
        ("Jira", meta.get("url", "")),
        ("Times", "Turkey time (UTC+3)"),
        ("Start time", "Jira's «Date Started» field: the start time chosen when the worklog was entered"),
        ("Logged at", "The moment the worklog was saved in Jira"),
    ):
        summ.cell(row=info_row, column=1, value=label).font = Font(bold=True)
        summ.cell(row=info_row, column=2, value=value).alignment = Alignment(horizontal="left")
        info_row += 1

    wb.save(path)
    _mark_number_formats(path)


def _mark_number_formats(path: Path) -> None:
    """Biçimli hücre stillerine applyNumberFormat="1" ekler (openpyxl yazmaz).

    Excel bu bayrağı gözetmeden biçimi uygular; bazı başka programlar (Numbers, Önizleme vb.) ise bayrak yoksa
    biçimi yok sayıp tarihi 46289 gibi ham sayı olarak gösterebilir.
    """
    import re
    import zipfile

    tmp = Path(str(path) + ".tmp")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "xl/styles.xml":
                text = data.decode("utf-8")
                head, sep, tail = text.partition("<cellXfs")
                if sep:
                    body, sep2, rest = tail.partition("</cellXfs>")
                    body = re.sub(r'<xf numFmtId="(?!0")(\d+)"(?![^>]*applyNumberFormat)', r'<xf numFmtId="\1" applyNumberFormat="1"', body)
                    text = head + sep + body + sep2 + rest
                data = text.encode("utf-8")
            zout.writestr(item, data)
    tmp.replace(path)
