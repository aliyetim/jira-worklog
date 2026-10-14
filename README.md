# Jira Worklog Raporu

Jira Server / Data Center için worklog raporu aracı (Tempo gerekmez). Seçilen proje ve tarih aralığı için
**kim, hangi gün ve saatte, hangi task'a ne kadar süre girmiş** bilgisini Excel (veya CSV) olarak verir.

Uygulama açılınca bilgisayarda küçük bir yerel sunucu başlar ve tarayıcıda bir sayfa açılır. Ek arayüz kütüphanesi gerekmez.

- Jira'dan **yalnızca okuma (GET)** yapar; hiçbir kaydı değiştirmez, silmez.
- **Token kaydedilmez.** Sadece bellekte tutulur; ayar dosyasına, günlüğe ya da rapora yazılmaz.
- Mac ve Windows'ta çalışır. Kaynak kodu okunabilir (aşağıdaki «Güvenlik notları»).

## Kurulum

### Mac

Terminal'i aç (Cmd+Boşluk, «Terminal») ve şu tek komutu yapıştır:

```bash
git clone https://github.com/KULLANICI/jira-worklog.git ~/jira-worklog && bash ~/jira-worklog/install.sh
```

Mac'te Git ya da Python yoksa Apple «komut satırı araçları» penceresi çıkarır: **Install**'a bas, bitince aynı komutu yeniden çalıştır.
Kurulum sonunda **Jira Worklog** uygulaması oluşur (Launchpad ya da Spotlight'tan aç). Uygulama bu Mac'te üretildiği için
«Apple doğrulayamadı» uyarısı çıkmaz.

### Windows

Python 3.9+ ve Git kurulu olmalı. Sonra:

```bat
git clone https://github.com/KULLANICI/jira-worklog.git
```

klasördeki `start.bat` dosyasına çift tıkla (ilk açılışta kurulumu kendisi yapar).

### Güncelleme

Uygulama her açılışta repo'dan güncellemeyi sessizce çeker (ağ yoksa mevcut sürümle devam eder). Kapatmak için
`JIRA_WORKLOG_NO_UPDATE=1` ortam değişkenini ver. Elle güncellemek için: `cd ~/jira-worklog && git pull`.

## Kullanım

1. İlk açılışta **Jira adresini** gir (örn. `https://jira.sirketiniz.com`); bir sonraki sefere hatırlanır.
2. **Proje anahtarı:** Task numaralarının başındaki kod (`PROJ-123` için `PROJ`).
3. **Dönem**, **Jira token'ı** (Profil → Personal Access Tokens), **Raporu oluştur**.

Ayrıntılı anlatım: [`PM_KULLANIM_REHBERI.md`](PM_KULLANIM_REHBERI.md).

## Dosyalar

| Dosya | Görevi |
|---|---|
| `install.sh` | Mac/Linux kurulumu: sanal ortam, bağımlılıklar, `Jira Worklog.app` |
| `start.sh`, `start.command`, `start.bat` | Güncelle + başlat (uygulama bunları çağırır) |
| `worklog_web.py` | Uygulamanın kendisi: yerel sunucu + API |
| `web_page.py` | Tarayıcıda açılan sayfa (HTML/CSS/JS) |
| `worklog_core.py` | Jira istemcisi, doğrulama, Excel/CSV yazımı |
| `worklog_cli.py` | Argümanlı komut satırı sürümü |

## Saatler

Jira her zamanı saat dilimi ofsetiyle verir (`2026-09-03T10:15:00.000+0300`); hangi dilimde döneceği Jira kullanıcısının
profil ayarına bağlıdır. Uygulama ofseti okuyup tüm zamanları **Türkiye saatine (UTC+3)** çevirir; tarih filtresi ve günlük
toplamlar da buna göre hesaplanır. Jira aramasında aralık ±1 gün genişletilir, kesin filtre Türkiye saatiyle uygulanır.

- **Başlama Saati:** Jira'daki «Date Started» alanı (worklog girilirken seçilen başlangıç; kişi değiştirebilir).
- **Girilme Zamanı:** Kaydın Jira'ya girildiği an (`created`).

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

- Kod yaklaşık 1400 satır Python; Jira'ya giden her istek `worklog_core.py` içindeki tek noktadan, `GET` yöntemiyle çıkar.
- Sunucu yalnızca `127.0.0.1`'e bağlanır; ağdaki başka bilgisayarlar erişemez.
- Her çalıştırmada rastgele bir anahtar üretilir; anahtarsız ya da yanlış `Host` başlıklı istekler reddedilir
  (başka web sitelerinin yerel uygulamaya istek atmasını engeller). Sayfa katı bir içerik güvenliği politikasıyla (CSP) sunulur.
- Hazırlanan rapor geçici bir klasörde durur, uygulama kapanınca silinir.
- Sekme kapanınca ya da «Uygulamayı kapat»a basılınca uygulama kendini kapatır.
- Jira başka bir adrese yönlendirirse token oraya gönderilmez, işlem durur.
- Her kullanıcı **kendi** Personal Access Token'ını üretmeli; başkasının token'ı kullanılmamalı.
- Ayarlar (token hariç) `~/.jira_worklog_app.json` dosyasına kaydedilir: adres, proje, dönem, çıktı biçimi.
- Otomatik güncelleme repo sahibinin kodunu çalıştırır; bunu istemeyen `JIRA_WORKLOG_NO_UPDATE=1` kullanmalı.
