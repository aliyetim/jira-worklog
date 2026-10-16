# Jira Worklog Raporu

Jira Server / Data Center için worklog raporu aracı (Tempo gerekmez). Seçilen proje ve tarih aralığı için
**kim, hangi gün ve saatte, hangi task'a ne kadar süre girmiş** bilgisini Excel (veya CSV) olarak verir.

Uygulama açılınca bilgisayarda küçük bir yerel sunucu başlar ve tarayıcıda bir sayfa açılır. Ek arayüz kütüphanesi gerekmez.

- Jira'dan **yalnızca okuma (GET)** yapar; hiçbir kaydı değiştirmez, silmez.
- **Token hiçbir dosyaya yazılmaz.** «Remember on this computer» seçiliyse işletim sisteminin şifreli anahtar deposunda
  (macOS Anahtar Zinciri, Windows Kimlik Bilgisi Yöneticisi) saklanır; seçili değilse yalnızca bellekte tutulur.
- Mac ve Windows'ta çalışır. Kaynak kodu okunabilir (aşağıdaki «Güvenlik notları»).

## Kurulum

### Mac

Terminal'i aç (Cmd+Boşluk, «Terminal») ve şu tek komutu yapıştır:

```bash
curl -fsSL https://raw.githubusercontent.com/aliyetim/jira-worklog/main/install.sh | bash
```

Git ya da Apple'ın komut satırı araçları (Xcode CLT, ~1 GB) **gerekmez**. Komut yalnızca macOS'ta hazır gelen `curl` ile
uygulama dosyalarını (~100 KB) ve taşınabilir bir Python 3.12'yi (~25 MB, [python-build-standalone](https://github.com/astral-sh/python-build-standalone))
`~/jira-worklog` klasörüne indirir; Python'ın sürümü `install.sh` içinde sabittir ve indirilen dosya SHA-256 ile doğrulanır.
Sisteme hiçbir şey kurulmaz, yönetici şifresi istenmez; kurulum yaklaşık bir dakika sürer.
Kurulum sonunda **Jira Worklog** uygulaması oluşur (Launchpad ya da Spotlight'tan aç). Uygulama bu Mac'te üretildiği için
«Apple doğrulayamadı» uyarısı çıkmaz. Başlatıcısı macOS'un `osacompile` aracıyla üretilen bir AppleScript programıdır (Apple'ın
evrensel arm64/x86_64 «applet»i); Apple Silicon'da **Rosetta istemez**.

Eski kurulumlarda başlatıcı bir bash betiğiydi ve Apple Silicon'da Rosetta istiyordu. Bu kurulumlar ilk güncellemeden sonraki
açılışta kendiliğinden yeni başlatıcıya geçer; hemen düzeltmek için: `bash ~/jira-worklog/install.sh --app-only`.

### Windows

PowerShell'i aç (Başlat → «PowerShell») ve şu tek komutu yapıştır:

```powershell
irm https://raw.githubusercontent.com/aliyetim/jira-worklog/main/install.ps1 | iex
```

Git ya da kurulu bir Python **gerekmez**, yönetici yetkisi istenmez. Komut uygulama dosyalarını (~100 KB) ve taşınabilir bir
Python 3.12'yi (~47 MB, SHA-256 ile doğrulanır) `%LOCALAPPDATA%\jira-worklog` klasörüne indirir, Başlat menüsüne ve masaüstüne
**Jira Worklog** kısayolu ekler ve uygulamayı açar. Kısayol `windows_launcher.py`'yi `pythonw.exe` ile çalıştırır (konsol
penceresi açılmaz); başlatıcı her açılışta güncellemeyi kontrol eder. Açılışta bir sorun olursa mesaj kutusu çıkar, ayrıntı
`%LOCALAPPDATA%\jira-worklog\launcher.log` dosyasındadır.

Kurulum betiği PowerShell'in kısıtlı dil modunda (Constrained Language Mode; AppLocker/WDAC politikaları) da çalışır:
.NET ya da COM kullanmaz, kısayolları Python (`comtypes`) oluşturur. Politika `%LOCALAPPDATA%` altındaki programları da
engelliyorsa betik bunu söyler; o durumda BT'den izin gerekir. Kaldırmak için: `%LOCALAPPDATA%\jira-worklog` klasörünü ve iki kısayolu sil.

Eski yöntem (Python 3.9+ ve Git kurulu olmalı): `git clone https://github.com/aliyetim/jira-worklog.git`, sonra klasördeki
`start.bat` dosyasına çift tıkla. Bu kurulumlar `git pull` ile güncellenmeye devam eder.

### Güncelleme

Uygulama her açılışta repo'dan güncellemeyi sessizce çeker (ağ yoksa mevcut sürümle devam eder). Kapatmak için
`JIRA_WORKLOG_NO_UPDATE=1` ortam değişkenini ver.

- `curl` (Mac) ya da `install.ps1` (Windows) ile kurulanlar: `main` dalının arşivi koşullu istekle (`If-None-Match`) sorulur; değişiklik yoksa sunucu 304 döner ve
  hiçbir şey indirilmez. Sürüm işareti `.version` dosyasındadır.
- `git clone` ile kurulmuş eski kurulumlar `git pull` ile güncellenmeye devam eder.
- Python sürümünü yükseltmek için `install.sh` içindeki `PY_RELEASE`/`PY_VERSION`/`PY_SHA256_*` değiştirilir; kullanıcıların
  kurulum komutunu bir kez yeniden çalıştırması gerekir (uygulama dosyaları ve ayarlar korunur).

## Kullanım

1. İlk açılışta **Jira adresini** gir (örn. `https://jira.sirketiniz.com`); bir sonraki sefere hatırlanır.
2. **Proje anahtarı:** Task numaralarının başındaki kod (`PROJ-123` için `PROJ`).
3. **Dönem**, **Jira token'ı** (Profil → Personal Access Tokens), **Create report**.

Arayüz, hata mesajları ve Excel/CSV çıktısı İngilizcedir.

Ayrıntılı anlatım: [`PM_KULLANIM_REHBERI.md`](PM_KULLANIM_REHBERI.md).

## Dosyalar

| Dosya | Görevi |
|---|---|
| `install.sh` | Mac/Linux kurulumu: uygulama dosyaları, (Mac'te) taşınabilir Python, sanal ortam, bağımlılıklar, `Jira Worklog.app` |
| `install.ps1` | Windows kurulumu: uygulama dosyaları, taşınabilir Python, sanal ortam, bağımlılıklar, kısayollar |
| `windows_launcher.py` | Windows kısayolunun çalıştırdığı başlatıcı: güncelleme + bağımlılıklar + uygulama |
| `start.sh`, `start.command`, `start.bat` | Güncelle + başlat (Mac uygulaması `start.sh`'i çağırır; `start.bat` git ile kurulmuş Windows içindir) |
| `worklog_web.py` | Uygulamanın kendisi: yerel sunucu + API |
| `web_page.py` | Tarayıcıda açılan sayfa (HTML/CSS/JS) |
| `worklog_core.py` | Jira istemcisi, doğrulama, Excel/CSV yazımı |
| `worklog_cli.py` | Argümanlı komut satırı sürümü |

## Jira'ya yük

Jira sunucusu bizim olduğu için öncelik **en az istek**, sonra hız:

- Worklog'lar arama yanıtına gömülü istenir (`fields=...,worklog`, 500'lük sayfalar). Jira burada issue başına en fazla 20
  worklog döndürür; çoğu task için ayrıca istek atılmaz.
- Yalnızca 20'den fazla worklog'u olan task'lar için `/issue/{key}/worklog` çağrılır; bunlar aynı anda en fazla 4 tane
  gider (istek sayısını değil, bekleme süresini etkiler).
- Yanıtlar sıkıştırılmış (`gzip`) istenir; Jira'da sıkıştırma açıksa indirilen veri birkaç kat küçülür.
- Komut satırı sürümü istek sayısını, indirilen veriyi, süreyi ve her task için ayrı istek atılsaydı kaç istek
  gerekeceğini yazar (ölçüm için).

## Saatler

Jira her zamanı saat dilimi ofsetiyle verir (`2026-09-03T10:15:00.000+0300`); hangi dilimde döneceği Jira kullanıcısının
profil ayarına bağlıdır. Uygulama ofseti okuyup tüm zamanları **Türkiye saatine (UTC+3)** çevirir; tarih filtresi ve günlük
toplamlar da buna göre hesaplanır. Jira aramasında aralık ±1 gün genişletilir, kesin filtre Türkiye saatiyle uygulanır.

- **Start Time:** Jira'daki «Date Started» alanı (worklog girilirken seçilen başlangıç; kişi değiştirebilir).
- **Logged At:** Kaydın Jira'ya girildiği an (`created`).

## Komut satırı

```bash
export JIRA_URL=https://jira.sirketiniz.com
export JIRA_TOKEN=...            # ya da boş bırak, görünmeden sorar
~/jira-worklog/.venv/bin/python ~/jira-worklog/worklog_cli.py -p PROJ                      # geçen ay, Excel
~/jira-worklog/.venv/bin/python ~/jira-worklog/worklog_cli.py -p PROJ,ABC -s 01.09.2026 -e 30.09.2026 -f csv -o ~/Desktop
```

Tarihler `GG.AA.YYYY` veya `YYYY-AA-GG` olabilir. Tarih verilmezse geçen ay alınır.

## Kaynak koddan çalıştırma (geliştirici)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt       # certifi, openpyxl
python worklog_web.py                 # seçenekler: --no-browser, --port 8080
```

Varsayılan port 47865'tir; uygulama zaten açıksa ikinci başlatma yeni sunucu açmaz, mevcut sayfayı açıp çıkar.

## Güvenlik notları

- Kod yaklaşık 2000 satır Python; Jira'ya giden her istek `worklog_core.py` içindeki tek noktadan, `GET` yöntemiyle çıkar.
- Sunucu yalnızca `127.0.0.1`'e bağlanır; ağdaki başka bilgisayarlar erişemez.
- Her çalıştırmada rastgele bir anahtar üretilir; anahtarsız ya da yanlış `Host` başlıklı istekler reddedilir
  (başka web sitelerinin yerel uygulamaya istek atmasını engeller). Sayfa katı bir içerik güvenliği politikasıyla (CSP) sunulur.
- Hazırlanan rapor geçici bir klasörde durur, uygulama kapanınca silinir.
- Sekme kapanınca uygulama birkaç saniye içinde kendini kapatır.
- Jira başka bir adrese yönlendirirse token oraya gönderilmez, işlem durur.
- Her kullanıcı **kendi** Personal Access Token'ını üretmeli; başkasının token'ı kullanılmamalı.
- Hatırlanan token Jira adresine bağlı saklanır (`jira-worklog` / adres); yalnızca o adrese gönderilir ve tarayıcıya
  hiç geri verilmez. Yalnızca Jira'nın kabul ettiği token saklanır; Jira 401 dönerse (süresi dolmuş, iptal edilmiş)
  kendiliğinden silinir. Anahtar deposu yoksa (ör. bazı Linux kurulumları) bu seçenek görünmez; düz dosyaya düşülmez.
- Token'a bir bitiş tarihi verilmesi önerilir: hatırlanan token sınırsız süre geçerli kalmaz.
- Ayarlar (token hariç) `~/.jira_worklog_app.json` dosyasına kaydedilir: adres, proje, dönem, çıktı biçimi.
- Otomatik güncelleme repo sahibinin kodunu çalıştırır; bunu istemeyen `JIRA_WORKLOG_NO_UPDATE=1` kullanmalı.
