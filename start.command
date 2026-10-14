#!/bin/bash
# Finder'da çift tıklanınca Terminal'de açar (Jira Worklog.app çalışmazsa yedek yöntem).
exec /bin/bash "$(dirname "$0")/start.sh" "$@"
