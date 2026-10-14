#!/bin/bash
# Jira Worklog'u başlatır: (varsa) güncellemeyi çeker, bağımlılıkları eşitler, uygulamayı açar.
# Güncellemeyi kapatmak için: JIRA_WORKLOG_NO_UPDATE=1 bash start.sh

REPO="aliyetim/jira-worklog"

# curl ile kurulmuş klasörü günceller. Değişiklik yoksa sunucu 304 döner, hiçbir şey indirilmez.
update_from_archive() {
  local tmp code
  tmp="$(mktemp -d)" || return
  code="$(curl -sS --max-time 20 -H "If-None-Match: $(cat .version)" -D "$tmp/headers" -o "$tmp/app.tar.gz" \
    -w '%{http_code}' "https://codeload.github.com/$REPO/tar.gz/refs/heads/main" 2>/dev/null)"
  if [ "$code" = "200" ] && mkdir "$tmp/app" && tar -xzf "$tmp/app.tar.gz" -C "$tmp/app" --strip-components=1 2>/dev/null \
     && [ -f "$tmp/app/worklog_web.py" ]; then
    cp -R "$tmp/app/." ./ && sed -n 's/^etag: *//Ip' "$tmp/headers" | tr -d '\r' > .version
  fi
  rm -rf "$tmp"
}

main() {
  cd "$(dirname "$0")" || exit 1

  if [ ! -x .venv/bin/python ]; then
    echo "Setup is required first:  bash install.sh"
    exit 1
  fi

  # Sessiz güncelleme: ağ yoksa ya da yerel değişiklik varsa hata vermeden mevcut sürümle devam eder.
  if [ "${JIRA_WORKLOG_NO_UPDATE:-}" != "1" ]; then
    if [ -d .git ]; then
      command -v git >/dev/null 2>&1 && GIT_TERMINAL_PROMPT=0 GIT_HTTP_LOW_SPEED_LIMIT=1000 GIT_HTTP_LOW_SPEED_TIME=8 \
        git pull --ff-only --quiet >/dev/null 2>&1
    elif [ -f .version ]; then
      update_from_archive
    fi
  fi

  # Eski kurulumların uygulama paketi bir bash betiğiyle açılıyordu; Apple Silicon'da bu Rosetta ister.
  # Bu klasörü açan böyle bir paket varsa bir kez AppleScript başlatıcılı yenisiyle değiştirilir.
  if [ "$(uname -s)" = "Darwin" ]; then
    local app
    for app in "${JIRA_WORKLOG_APP_DIR:-/Applications}/Jira Worklog.app" "$HOME/Applications/Jira Worklog.app"; do
      if grep -qsF "APP_DIR=\"$(pwd)\"" "$app/Contents/MacOS/launcher"; then
        bash install.sh --app-only >/dev/null 2>&1
        break
      fi
    done
  fi

  # requirements.txt değiştiyse bağımlılıkları yeniden kur.
  local sum
  sum="$(cksum < requirements.txt)"
  if [ "$(cat .venv/.req-sum 2>/dev/null)" != "$sum" ]; then
    .venv/bin/python -m pip install -q --disable-pip-version-check -r requirements.txt >/dev/null 2>&1 \
      && echo "$sum" > .venv/.req-sum
  fi

  exec .venv/bin/python worklog_web.py "$@"
}

# Güncelleme bu dosyanın üzerine yazabilir; bash fonksiyonu önceden okuduğu için çalışan kopya etkilenmez.
main "$@"
