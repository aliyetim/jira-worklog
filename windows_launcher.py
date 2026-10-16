"""
Windows başlatıcısı. Başlat menüsü/masaüstü kısayolu bunu pythonw.exe ile (konsol penceresi açmadan) çalıştırır:
1) Uygulama zip ile kurulduysa (install.ps1) GitHub'da yeni sürüm var mı bakar; değişiklik yoksa sunucu 304 döner
   ve hiçbir şey indirilmez. Ağ yoksa mevcut sürümle devam edilir.
2) requirements.txt değiştiyse bağımlılıkları .deps klasörüne kurar (pip --target; sanal ortam yok, böylece
   kurulum klasöründen hiçbir program çalıştırılmaz ve şirketin kurduğu Python ile de çalışır).
3) Uygulamayı (worklog_web) aynı süreçte başlatır; güncellenen dosyalar bu açılışta kullanılır.
Hata olursa launcher.log dosyasına yazar ve bir mesaj kutusu gösterir.
Güncellemeyi kapatmak için: JIRA_WORKLOG_NO_UPDATE=1

«--install-shortcuts»: install.ps1 çağırır; Başlat menüsü ve masaüstü kısayolunu oluşturur. Şirket politikasıyla
PowerShell kısıtlı dil modundaysa COM kullanılamadığı için kısayollar buradan (comtypes) oluşturulur.
"""
from __future__ import annotations

import hashlib
import io
import os
import subprocess
import sys
import traceback
import urllib.request
import zipfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ARCHIVE_URL = "https://codeload.github.com/aliyetim/jira-worklog/zip/refs/heads/main"
LOG_PATH = APP_DIR / "launcher.log"
DEPS_DIR = APP_DIR / ".deps"  # bağımlılıklar (install.ps1 kurar)
LOG_LIMIT = 256 * 1024


def update_app() -> None:
    marker = APP_DIR / ".version"  # GitHub arşivinin ETag'i: install.ps1 yazar
    if os.environ.get("JIRA_WORKLOG_NO_UPDATE") == "1" or (APP_DIR / ".git").exists() or not marker.exists():
        return
    req = urllib.request.Request(ARCHIVE_URL, headers={"If-None-Match": marker.read_text(encoding="ascii").strip()})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data, etag = resp.read(), resp.headers.get("ETag", "")
    except Exception:  # 304 (değişiklik yok), ağ yok, zaman aşımı: mevcut sürümle devam
        return
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        root = names[0].split("/", 1)[0] + "/"
        if root + "worklog_web.py" not in names:
            return
        for info in archive.infolist():
            rel = info.filename[len(root):]
            if not rel or info.is_dir():
                continue
            target = (APP_DIR / rel).resolve()
            if APP_DIR not in target.parents:  # arşiv klasör dışına yazamasın
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
    marker.write_text(etag, encoding="ascii")
    print("Updated to", etag)


def sync_requirements() -> None:
    req = APP_DIR / "requirements.txt"
    stamp = DEPS_DIR / ".req-sha256"  # install.ps1 aynı özeti yazar
    digest = hashlib.sha256(req.read_bytes()).hexdigest()
    if stamp.exists() and stamp.read_text(encoding="ascii").strip() == digest:
        return
    python = Path(sys.executable)
    if python.name.lower() == "pythonw.exe":
        python = python.with_name("python.exe")  # pip çıktısı için; pencere açılmaz (CREATE_NO_WINDOW)
    result = subprocess.run(
        [str(python), "-m", "pip", "install", "-q", "--disable-pip-version-check", "--upgrade", "--target", str(DEPS_DIR),
         "-r", str(req)],
        capture_output=True, text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode == 0:
        stamp.write_text(digest, encoding="ascii")
    else:
        print(result.stdout, result.stderr)


def install_shortcuts() -> int:
    import ctypes

    from comtypes.client import CreateObject
    from comtypes.persist import IPersistFile
    from comtypes.shelllink import IShellLinkW, ShellLink

    def folder(csidl: int) -> Path:
        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buf)
        return Path(buf.value)

    pythonw = Path(sys.executable).with_name("pythonw.exe")
    for place in (folder(0x0002), folder(0x0010)):  # CSIDL_PROGRAMS (Başlat menüsü), CSIDL_DESKTOPDIRECTORY
        link = CreateObject(ShellLink, interface=IShellLinkW)
        link.SetPath(str(pythonw))
        link.SetArguments(f'"{APP_DIR / "windows_launcher.py"}"')
        link.SetWorkingDirectory(str(APP_DIR))
        link.SetIconLocation(str(APP_DIR / "assets" / "icon.ico"), 0)
        link.SetDescription("Jira worklog report")
        place.mkdir(parents=True, exist_ok=True)
        link.QueryInterface(IPersistFile).Save(str(place / "Jira Worklog.lnk"), True)
        print("Shortcut:", place / "Jira Worklog.lnk")
    return 0


def show_error(text: str) -> None:
    if os.name == "nt":
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, text, "Jira Worklog", 0x10)  # MB_ICONERROR
    else:
        print(text, file=sys.stderr)


def main() -> int:
    os.chdir(APP_DIR)
    sys.path.insert(0, str(DEPS_DIR))
    if sys.argv[1:] == ["--install-shortcuts"]:
        return install_shortcuts()
    if sys.stdout is None:  # pythonw: konsol yok, çıktılar günlüğe
        if LOG_PATH.exists() and LOG_PATH.stat().st_size > LOG_LIMIT:
            LOG_PATH.unlink()
        sys.stdout = sys.stderr = open(LOG_PATH, "a", encoding="utf-8", buffering=1)
    try:
        update_app()
        sync_requirements()
        import worklog_web

        return worklog_web.main(sys.argv[1:])
    except Exception:
        traceback.print_exc()
        show_error(f"Jira Worklog could not start.\n\nDetails were written to:\n{LOG_PATH}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
