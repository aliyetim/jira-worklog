#!/usr/bin/env python3
"""
Jira worklog report - command-line version (read-only).

Examples:
  python3 worklog_cli.py --project PROJ
  python3 worklog_cli.py -p PROJ -s 01.09.2026 -e 30.09.2026
  python3 worklog_cli.py -p PROJ,ABC -f csv -o ~/Desktop

The token is not passed as an argument (it would stay in the shell history). It is read from the
JIRA_TOKEN environment variable; otherwise it is asked for without echoing.
"""
import argparse
import getpass
import os
import sys
from pathlib import Path

import worklog_core as core


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Jira worklog report (read-only)")
    ap.add_argument("-p", "--project", required=True, help="Project key; separate several with commas: PROJ,ABC")
    ap.add_argument("-s", "--start", help="Start (DD.MM.YYYY or YYYY-MM-DD). Default: first day of last month")
    ap.add_argument("-e", "--end", help="End (DD.MM.YYYY or YYYY-MM-DD). Default: last day of last month")
    ap.add_argument("-u", "--url", default=os.environ.get("JIRA_URL", ""), help="Jira address (or the JIRA_URL environment variable)")
    ap.add_argument("-o", "--out", default=".", help="Output folder (default: current folder)")
    ap.add_argument("-f", "--format", choices=("xlsx", "csv"), default="xlsx", help="Output format (default: xlsx)")
    ap.add_argument("--delimiter", default=";", help="CSV delimiter (default: ;)")
    ap.add_argument("--decimal-point", action="store_true", help="Write hours as 1.5 in CSV (default: 1,5)")
    args = ap.parse_args(argv)

    try:
        if not args.url.strip():
            raise core.JiraError("Jira address required: -u https://jira.yourcompany.com (or the JIRA_URL environment variable).")
        projects = core.parse_projects(args.project)
        default_start, default_end = core.previous_month_range()
        start = core.parse_date(args.start) if args.start else default_start
        end = core.parse_date(args.end) if args.end else default_end
        core.check_range(start, end)

        token = os.environ.get("JIRA_TOKEN") or getpass.getpass("Jira token (hidden while typing): ")
        core.clean_token(token)

        reported = 0

        def progress(stage, done, total):
            nonlocal reported
            if stage == "search":
                print("Searching issues...")
            elif stage == "issues" and done != reported and (done == total or done - reported >= 50):
                reported = done
                print(f"  {done}/{total} issues processed")

        stats = core.RequestStats()
        rows = core.fetch_report(args.url, token, projects, start, end, progress, stats=stats)
        cost = stats.as_dict()
        print(f"Jira: {cost['requests']} requests, {cost['bytes'] / 1024:.0f} KB, {cost['seconds']} s "
              f"(~{cost['baseline']} with one request per issue)")
        if not rows:
            print("No worklogs found for the selected project in this period. No file was created.")
            return 0

        out_dir = Path(args.out).expanduser()
        path = core.unique_path(out_dir, core.default_filename(projects, start, end, args.format))
        if args.format == "xlsx":
            core.write_xlsx(rows, path, {"projects": projects, "start": start, "end": end, "url": core.normalize_url(args.url)})
        else:
            core.write_csv(rows, path, args.delimiter, decimal_comma=not args.decimal_point)
        total_hours = sum(r["hours"] for r in rows)
        print(f"{len(rows)} worklogs, {total_hours:.2f} hours in total -> {path.resolve()}")
        return 0
    except core.JiraError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
