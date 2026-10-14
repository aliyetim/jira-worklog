#!/bin/bash
# Jira Worklog'u başlatır: (varsa) güncellemeyi çeker, bağımlılıkları eşitler, uygulamayı açar.
# Güncellemeyi kapatmak için: JIRA_WORKLOG_NO_UPDATE=1 bash start.sh
cd "$(dirname "$0")" || exit 1

if [ ! -x .venv/bin/python ]; then
  echo "Önce kurulum gerekli:  bash install.sh"
  exit 1
fi

# Sessiz güncelleme: ağ yoksa ya da yerel değişiklik varsa hata vermeden mevcut sürümle devam eder.
if [ -d .git ] && [ "${JIRA_WORKLOG_NO_UPDATE:-}" != "1" ] && command -v git >/dev/null 2>&1; then
  GIT_TERMINAL_PROMPT=0 GIT_HTTP_LOW_SPEED_LIMIT=1000 GIT_HTTP_LOW_SPEED_TIME=8 \
    git pull --ff-only --quiet >/dev/null 2>&1 || true
fi

# requirements.txt değiştiyse bağımlılıkları yeniden kur.
sum="$(cksum < requirements.txt)"
if [ "$(cat .venv/.req-sum 2>/dev/null)" != "$sum" ]; then
  .venv/bin/python -m pip install -q --disable-pip-version-check -r requirements.txt >/dev/null 2>&1 \
    && echo "$sum" > .venv/.req-sum
fi

exec .venv/bin/python worklog_web.py "$@"
