#!/usr/bin/env python3
"""
Jira worklog raporu - komut satırı sürümü (sadece okuma).

Örnekler:
  python3 worklog_cli.py --project PROJ
  python3 worklog_cli.py -p PROJ -s 01.09.2026 -e 30.09.2026
  python3 worklog_cli.py -p PROJ,ABC -f csv -o ~/Desktop

Token argüman olarak verilmez (terminal geçmişinde kalır). JIRA_TOKEN ortam değişkeninden
okunur; yoksa görünmeden sorulur.
"""
import argparse
import getpass
import os
import sys
from pathlib import Path

import worklog_core as core


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Jira worklog raporu (sadece okuma)")
    ap.add_argument("-p", "--project", required=True, help="Proje anahtarı; birden fazlası için virgülle: PROJ,ABC")
    ap.add_argument("-s", "--start", help="Başlangıç (GG.AA.YYYY veya YYYY-AA-GG). Varsayılan: geçen ayın ilk günü")
    ap.add_argument("-e", "--end", help="Bitiş (GG.AA.YYYY veya YYYY-AA-GG). Varsayılan: geçen ayın son günü")
    ap.add_argument("-u", "--url", default=os.environ.get("JIRA_URL", ""), help="Jira adresi (ya da JIRA_URL ortam değişkeni)")
    ap.add_argument("-o", "--out", default=".", help="Çıktı klasörü (varsayılan: bulunduğun klasör)")
    ap.add_argument("-f", "--format", choices=("xlsx", "csv"), default="xlsx", help="Çıktı biçimi (varsayılan: xlsx)")
    ap.add_argument("--delimiter", default=";", help="CSV ayracı (varsayılan: ;)")
    ap.add_argument("--decimal-point", action="store_true", help="CSV'de saatleri 1.5 şeklinde yaz (varsayılan: 1,5)")
    args = ap.parse_args(argv)

    try:
        if not args.url.strip():
            raise core.JiraError("Jira adresi gerekli: -u https://jira.sirketiniz.com (ya da JIRA_URL ortam değişkeni).")
        projects = core.parse_projects(args.project)
        default_start, default_end = core.previous_month_range()
        start = core.parse_date(args.start) if args.start else default_start
        end = core.parse_date(args.end) if args.end else default_end
        core.check_range(start, end)

        token = os.environ.get("JIRA_TOKEN") or getpass.getpass("Jira token (yazarken görünmez): ")
        core.clean_token(token)

        def progress(stage, done, total):
            if stage == "search":
                print("Issue'lar aranıyor...")
            elif stage == "issues" and total and (done == 0 or done % 20 == 0 or done == total):
                print(f"  {done}/{total} issue işlendi" if done else f"{total} issue bulundu.")

        rows = core.fetch_report(args.url, token, projects, start, end, progress)
        if not rows:
            print("Bu dönemde seçilen proje için worklog bulunamadı. Dosya oluşturulmadı.")
            return 0

        out_dir = Path(args.out).expanduser()
        path = core.unique_path(out_dir, core.default_filename(projects, start, end, args.format))
        if args.format == "xlsx":
            core.write_xlsx(rows, path, {"projects": projects, "start": start, "end": end, "url": core.normalize_url(args.url)})
        else:
            core.write_csv(rows, path, args.delimiter, decimal_comma=not args.decimal_point)
        total_hours = sum(r["hours"] for r in rows)
        print(f"{len(rows)} kayıt, toplam {total_hours:.2f} saat -> {path.resolve()}")
        return 0
    except core.JiraError as e:
        print(f"Hata: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nİptal edildi.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
