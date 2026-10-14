#!/bin/bash
# Jira Worklog kurulumu (bir kez çalıştırılır; tekrar çalıştırmak zararsızdır).
#   git clone <adres> ~/jira-worklog && bash ~/jira-worklog/install.sh
set -e
cd "$(dirname "$0")"
HERE="$(pwd)"
OS="$(uname -s)"

say() { printf '\n%s\n' "$1"; }

# --- 1) Python 3.9+ var mı?
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
  if [ "$OS" = "Darwin" ] && ! xcode-select -p >/dev/null 2>&1; then
    xcode-select --install >/dev/null 2>&1 || true
    say "Mac'inde Python ve Git için Apple'ın «komut satırı araçları» gerekiyor."
    echo "Ekrandaki pencerede «Install» (Yükle) düğmesine bas, kurulum bitince bu komutu tekrar çalıştır:"
    echo "  bash \"$HERE/install.sh\""
  else
    say "Python 3.9 veya üstü bulunamadı. Python'u kurduktan sonra bu komutu tekrar çalıştır:"
    echo "  bash \"$HERE/install.sh\""
  fi
  exit 1
fi

# --- 2) Sanal ortam ve bağımlılıklar
say "Bağımlılıklar kuruluyor (1-2 dakika sürebilir)..."
python3 -m venv .venv
.venv/bin/python -m pip install -q --disable-pip-version-check -r requirements.txt
cksum < requirements.txt > .venv/.req-sum

# --- 3) Mac: çift tıklanan uygulama oluştur (bu Mac'te üretildiği için «doğrulanamadı» uyarısı çıkmaz)
if [ "$OS" = "Darwin" ]; then
  if [ -w /Applications ]; then DEST="/Applications"; else DEST="$HOME/Applications"; fi
  mkdir -p "$DEST"
  APP="$DEST/Jira Worklog.app"
  rm -rf "$APP"
  mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
  [ -f assets/icon.icns ] && cp assets/icon.icns "$APP/Contents/Resources/icon.icns"
  cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Jira Worklog</string>
  <key>CFBundleDisplayName</key><string>Jira Worklog</string>
  <key>CFBundleIdentifier</key><string>local.jira-worklog</string>
  <key>CFBundleExecutable</key><string>launcher</string>
  <key>CFBundleIconFile</key><string>icon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>LSUIElement</key><true/>
</dict>
</plist>
PLIST
  cat > "$APP/Contents/MacOS/launcher" <<LAUNCH
#!/bin/bash
APP_DIR="$HERE"
if [ ! -f "\$APP_DIR/start.sh" ]; then
  osascript -e 'display dialog "Jira Worklog klasörü bulunamadı. Klasörü taşıdıysan Terminal penceresinde klasörün içinde «bash install.sh» komutunu yeniden çalıştır." buttons {"Tamam"} with icon caution' >/dev/null 2>&1
  exit 1
fi
exec /bin/bash "\$APP_DIR/start.sh"
LAUNCH
  chmod +x "$APP/Contents/MacOS/launcher" start.sh start.command
  touch "$APP"
  say "Kurulum tamamlandı."
  echo "Uygulama: $APP"
  echo "Açmak için Launchpad'de ya da Spotlight'ta (Cmd+Boşluk) «Jira Worklog» yaz."
  echo "Dock'ta tutmak istersen açılan Finder penceresinde uygulamayı Dock'a sürükle."
  open -R "$APP" >/dev/null 2>&1 || true
else
  chmod +x start.sh start.command 2>/dev/null || true
  say "Kurulum tamamlandı. Başlatmak için:  bash \"$HERE/start.sh\""
fi
