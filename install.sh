#!/bin/bash
# Jira Worklog kurulumu. Mac'te Apple'ın komut satırı araçlarına (Xcode CLT, ~1 GB) gerek yoktur:
# uygulama dosyaları (~100 KB) ve taşınabilir bir Python (~25 MB) yalnızca curl ile indirilir.
#   curl -fsSL https://raw.githubusercontent.com/aliyetim/jira-worklog/main/install.sh | bash
# Var olan bir kurulumda yeniden çalıştırmak zararsızdır:  bash ~/jira-worklog/install.sh
# Ortam değişkenleri: JIRA_WORKLOG_DIR (kurulum klasörü, varsayılan ~/jira-worklog),
#                     JIRA_WORKLOG_APP_DIR (uygulamanın konacağı klasör, varsayılan /Applications),
#                     JIRA_WORKLOG_NO_APP=1 (Mac'te «Jira Worklog.app» oluşturma).
# «bash install.sh --app-only»: yalnızca Mac uygulama paketini yeniden oluşturur.
set -euo pipefail

REPO="aliyetim/jira-worklog"

# Taşınabilir Python (python-build-standalone, resmi CPython derlemesi). Sürüm sabittir; indirilen dosya
# aşağıdaki SHA-256 özetleriyle doğrulanır (kaynak: sürümün SHA256SUMS dosyası).
PY_RELEASE="20261003"
PY_VERSION="3.12.15"
PY_SHA256_AARCH64="316a463172740e71d8dca1f2730784e325f3f720941137b5d674d5801a632213"
PY_SHA256_X86_64="a8fd7a91852f19b6d959793ef41fad048631ccb2a334a9ecdf573255298f7978"

say() { printf '\n%s\n' "$1"; }
fail() { printf '\n%s\n' "$1" >&2; exit 1; }

# Uygulama dosyalarını GitHub'dan indirir; ETag sonraki güncellemelerde (start.sh) sürüm işareti olarak kullanılır.
fetch_app() {
  local dir="$1" tmp
  if [ -d "$dir/.git" ]; then
    return  # git ile kurulmuş: dosyalar yerinde, güncellemeyi start.sh «git pull» ile yapar
  fi
  say "Downloading the app..."
  tmp="$(mktemp -d)"
  curl -fsSL --retry 2 -D "$tmp/headers" -o "$tmp/app.tar.gz" "https://codeload.github.com/$REPO/tar.gz/refs/heads/main" \
    || fail "Could not download the app. Check your internet/VPN connection and try again."
  mkdir -p "$tmp/app" "$dir"
  tar -xzf "$tmp/app.tar.gz" -C "$tmp/app" --strip-components=1 || fail "The downloaded app archive is damaged. Try again."
  cp -R "$tmp/app/." "$dir/"
  sed -n 's/^etag: *//Ip' "$tmp/headers" | tr -d '\r' > "$dir/.version"
  rm -rf "$tmp"
}

# Mac: sabit sürümlü taşınabilir Python'ı .python/ klasörüne kurar (gerekirse). Sistem Python'ına dokunmaz.
fetch_python() {
  local arch sha name tmp pin
  if [ "$(sysctl -n hw.optional.arm64 2>/dev/null || echo 0)" = "1" ]; then
    arch="aarch64"; sha="$PY_SHA256_AARCH64"
  else
    arch="x86_64"; sha="$PY_SHA256_X86_64"
  fi
  pin="$PY_VERSION+$PY_RELEASE-$arch"
  if [ -x .python/bin/python3 ] && [ "$(cat .python/.pin 2>/dev/null)" = "$pin" ]; then
    return
  fi
  name="cpython-$PY_VERSION%2B$PY_RELEASE-$arch-apple-darwin-install_only.tar.gz"
  say "Downloading Python $PY_VERSION (about 25 MB)..."
  tmp="$(mktemp -d)"
  curl -fsSL --retry 2 -o "$tmp/python.tar.gz" \
    "https://github.com/astral-sh/python-build-standalone/releases/download/$PY_RELEASE/$name" \
    || fail "Could not download Python. Check your internet/VPN connection and try again."
  echo "$sha  $tmp/python.tar.gz" | shasum -a 256 -c - >/dev/null 2>&1 \
    || fail "The downloaded Python failed its integrity check, so setup was stopped. Try again later."
  rm -rf .python .venv  # sanal ortam eski Python'a bağlıdır; yeniden kurulur
  mkdir .python
  tar -xzf "$tmp/python.tar.gz" -C .python --strip-components=1
  echo "$pin" > .python/.pin
  rm -rf "$tmp"
}

# Mac: Launchpad'den açılan «Jira Worklog.app». Başlatıcı, macOS'un osacompile ile ürettiği AppleScript programıdır
# (Apple'ın evrensel arm64/x86_64 «applet»i). Betik başlatıcılı paketler Apple Silicon'da Rosetta ister; bu istemez.
make_mac_app() {
  local here="$1" quiet="${2:-}" dest app tmp esc
  dest="${JIRA_WORKLOG_APP_DIR:-}"
  if [ -z "$dest" ]; then
    if [ -w /Applications ]; then dest="/Applications"; else dest="$HOME/Applications"; fi
  fi
  mkdir -p "$dest"
  app="$dest/Jira Worklog.app"
  esc="${here//\\/\\\\}"; esc="${esc//\"/\\\"}"  # AppleScript dizgesi için kaçış
  tmp="$(mktemp -d)"
  cat > "$tmp/launcher.applescript" <<SCRIPT
set appDir to "$esc"
try
	do shell script "test -f " & quoted form of (appDir & "/start.sh")
on error
	activate
	display dialog "The Jira Worklog folder was not found. If you moved it, open Terminal in the folder and run «bash install.sh» again." buttons {"OK"} default button 1 with icon caution
	return
end try
do shell script "/bin/bash " & quoted form of (appDir & "/start.sh") & " >/dev/null 2>&1 &"
SCRIPT
  rm -rf "$app"
  osacompile -o "$app" "$tmp/launcher.applescript" >/dev/null 2>&1 || fail "Could not create the app in $dest."
  rm -rf "$tmp"
  [ -f assets/icon.icns ] && cp assets/icon.icns "$app/Contents/Resources/applet.icns"
  plutil -replace CFBundleIdentifier -string "local.jira-worklog" "$app/Contents/Info.plist"
  plutil -replace CFBundleName -string "Jira Worklog" "$app/Contents/Info.plist"
  plutil -replace LSUIElement -bool true "$app/Contents/Info.plist"  # Dock'ta simge göstermez
  codesign --force --sign - "$app" >/dev/null 2>&1 || true  # simge ve Info.plist değişti: yerel imzayı yenile
  touch "$app"
  [ -n "$quiet" ] && return
  say "Setup complete."
  echo "App: $app"
  echo "To open it, type «Jira Worklog» in Launchpad or Spotlight (Cmd+Space)."
  echo "To keep it in the Dock, drag the app from the Finder window that opens into the Dock."
  open -R "$app" >/dev/null 2>&1 || true
}

main() {
  local os self_dir here py
  os="$(uname -s)"

  # 1) Uygulama klasörü: betik bir kurulumun içinden çalıştırıldıysa orası, «curl | bash» ile geldiyse indirilir.
  self_dir=""
  if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  fi
  if [ -n "$self_dir" ] && [ -f "$self_dir/worklog_web.py" ]; then
    here="$self_dir"
  else
    here="${JIRA_WORKLOG_DIR:-$HOME/jira-worklog}"
    fetch_app "$here"
  fi
  cd "$here"
  here="$(pwd)"

  # Yalnızca Mac uygulama paketini yeniden oluştur (start.sh eski tip başlatıcıyı bununla değiştirir).
  if [ "${1:-}" = "--app-only" ]; then
    [ "$os" = "Darwin" ] && make_mac_app "$here" quiet
    return
  fi

  # 2) Python: Mac'te taşınabilir sürüm; diğer sistemlerde kurulu python3 (3.9+).
  if [ "$os" = "Darwin" ]; then
    fetch_python
    py="$here/.python/bin/python3"
  else
    python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1 \
      || fail "Python 3.9 or newer was not found. Install Python, then run this command again:  bash \"$here/install.sh\""
    py="python3"
  fi

  # 3) Sanal ortam ve bağımlılıklar
  say "Installing dependencies (this may take a minute)..."
  [ -x .venv/bin/python ] || "$py" -m venv .venv
  .venv/bin/python -m pip install -q --disable-pip-version-check -r requirements.txt </dev/null
  cksum < requirements.txt > .venv/.req-sum
  chmod +x start.sh start.command 2>/dev/null || true

  # 4) Mac: çift tıklanan uygulama (bu Mac'te üretildiği için «doğrulanamadı» uyarısı çıkmaz)
  if [ "$os" = "Darwin" ] && [ "${JIRA_WORKLOG_NO_APP:-}" != "1" ]; then
    make_mac_app "$here"
  else
    say "Setup complete. To start:  bash \"$here/start.sh\""
  fi
}

# Tüm betik önce okunur, sonra çalışır («curl | bash» ile gelirken yarım kalmasın).
main "$@"
