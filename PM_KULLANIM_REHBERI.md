# Jira Worklog Raporu – Kullanım Rehberi

Bu uygulama, seçtiğin projede **kim, hangi gün ve saatte, hangi task'a ne kadar süre girmiş** bilgisini
Excel dosyası olarak verir. Jira'dan sadece okur; hiçbir kaydı değiştirmez veya silmez.

## 1) İlk kurulum (bir kez, yaklaşık 1 dakika)

### Mac

1. **Terminal**'i aç: `Cmd + Boşluk` tuşlarına bas, «Terminal» yaz, Enter'a bas.
2. Aşağıdaki satırı **tamamen kopyalayıp** Terminal'e yapıştır ve Enter'a bas:

   ```
   curl -fsSL https://raw.githubusercontent.com/aliyetim/jira-worklog/main/install.sh | bash
   ```

   Komut uygulamayı ve çalışması için gereken Python'ı (toplam ~25 MB) indirir; ek bir program kurmana ya da şifre
   girmene gerek yoktur.
3. «Setup complete» yazısını görünce bir Finder penceresi açılır; içinde **Jira Worklog** uygulaması vardır.
   Terminal'i kapatabilirsin.

Bundan sonra uygulamayı **Launchpad**'den ya da `Cmd + Boşluk` ile «Jira Worklog» yazarak açarsın.
İstersen Finder'da açılan uygulamayı Dock'a sürükleyerek sabitleyebilirsin.

Bu uygulama Mac'inde kurulum sırasında üretildiği için «Apple doğrulayamadı» uyarısı çıkmaz.
Uygulamayı açınca birkaç saniye içinde tarayıcıda **Worklog report** sayfası açılır. Uygulamanın dili İngilizcedir.

### Windows

0. **Şirket bilgisayarındaysan:** Güvenlik politikası internetten indirilen programları engelleyebilir. Önce şirketin yazılım
   portalından **Python**'ı (3.9 veya üstü) kur; kurulum komutu onu kendiliğinden bulup kullanır.
1. **PowerShell**'i aç: Başlat menüsüne «PowerShell» yaz, **Windows PowerShell**'e tıkla.
2. Aşağıdaki satırı **tamamen kopyalayıp** PowerShell'e yapıştır (sağ tık yapıştırır) ve Enter'a bas:

   ```
   irm https://raw.githubusercontent.com/aliyetim/jira-worklog/main/install.ps1 | iex
   ```

   Bilgisayarda Python kuruluysa onu kullanır; yoksa gereken Python'ı da indirir (~47 MB). Yönetici şifresi girmene
   gerek yoktur.
3. Yeşil «Setup complete» yazısını görünce uygulama kendiliğinden açılır. PowerShell'i kapatabilirsin.

Bundan sonra uygulamayı **Başlat menüsünden** ya da masaüstündeki **Jira Worklog** kısayolundan açarsın.
Kırmızı «Setup failed» yazısı çıkarsa yazının tamamını bana gönder. Altında sarı bir «security policy» uyarısı varsa
önce portaldan Python kurup komutu yeniden çalıştır.

## 2) Token üretme (bir kez; süresi dolunca yenile)

Token, Jira'ya senin adına giriş yapan geçici bir şifredir. **Kendi token'ını üret, kimseyle paylaşma.**

1. Jira'ya giriş yap, sağ üstte profil resmine tıkla, **Profile**'ı aç.
2. Soldaki menüden **Personal Access Tokens**'ı seç.
3. **Create token** de, ad olarak «worklog rapor» yaz ve oluştur.
4. Çıkan uzun metni kopyala. (Bir daha gösterilmez; kaybedersen yenisini üretirsin.)

Token oluştururken bir bitiş tarihi (ör. 90 gün) seçmen önerilir. Süresi dolunca uygulama yenisini ister.

Menü adları Jira sürümüne göre biraz değişebilir. Sayfadaki **How do I create one?** bağlantısı da aynı adımları gösterir.

## 3) Rapor alma

1. Uygulamayı aç. Sayfa tarayıcıda açılır.
2. **Jira address:** İlk seferde Jira'nın ana adresini yaz (sana verilen adres, örn. `https://jira.sirketiniz.com`). Bir sonraki sefere hatırlanır.
3. **Project key:** Task numaralarının başındaki kısa kod. `PROJ-123` için `PROJ`.
4. **Period:** Last month (geçen ay), This month (bu ay) ya da Custom range (iki tarihi takvimden seçersin).
5. **Jira token:** Kopyaladığın token'ı yapıştır. **Remember on this computer** seçili kalırsa rapor başarıyla
   alındıktan sonra token Mac'inin Anahtar Zinciri'nde şifreli saklanır; sonraki açılışlarda yeniden yapıştırman gerekmez.
   **Change** ile yeni token girebilir, **Forget** ile kayıtlı token'ı silebilirsin.
6. **Create report**'a bas. Task sayısına göre bir dakika kadar sürebilir. Dönem şeridi ilerledikçe dolar.
7. Bitince sayfanın altında **Preview** tablosu açılır. İndirmeden önce kayıtlara buradan bakabilirsin:
   - Arama kutusuna kişi, task, özet, yorum ya da tarih (`03.09`) yaz; tablo ve toplam saat buna göre süzülür.
   - Sütun başlığına tıklayınca o sütuna göre sıralanır; ikinci tıklama sırayı ters çevirir.
   - **By person** kişi başına kayıt, gün, task ve toplam saati gösterir. Bir kişiye tıklayınca onun kayıtları açılır.
8. **Download Excel**'e bas. Dosya tarayıcının indirilenler klasörüne kaydedilir.
   - Şeritteki çubuklar her günün toplam saatini gösterir; üzerine gelince değeri görürsün.
   - Excel'de her sütunun başlığında filtre düğmesi vardır (kullanıcıya, tarihe, task'a göre filtreleyebilirsin).
     **Overview** sayfasında kişi bazında toplam saatler bulunur.
   - Tüm saatler **Türkiye saatine (UTC+3)** göre yazılır.
   - **Start Time**, Jira'da worklog girilirken seçilen başlangıç zamanıdır (Jira'daki «Date Started» alanı).
     Kişi bunu sonradan değiştirmiş olabilir. **Logged At** ise kaydın Jira'ya gerçekten girildiği andır.

## 4) Kapatma

Tarayıcı sekmesini kapatman yeterli, uygulama birkaç saniye içinde kendini kapatır.

## 5) Güncelleme

Hiçbir şey yapman gerekmez. Uygulama her açıldığında yeni sürüm varsa kendini günceller.

## Sık karşılaşılan mesajlar

| Mesaj | Ne yapmalı |
|---|---|
| Jira address cannot be empty | «Jira address» alanını (change bağlantısı) doldur |
| The token is invalid, expired or was pasted incorrectly | Token'ı baştan ve eksiksiz yapıştır; olmazsa yenisini üret |
| The saved token no longer works | Kayıtlı token'ın süresi dolmuş ya da iptal edilmiş; Jira'da yenisini üretip yapıştır |
| You do not have permission for this | O projeye Jira'da erişimin olmayabilir; proje anahtarını kontrol et |
| Could not reach Jira | Şirket ağında ya da VPN'de olduğundan emin ol |
| No worklogs found for the selected project in this period | Proje anahtarını ve tarihleri kontrol et |
| Lost connection to the app | Uygulamayı yeniden aç; eski sekmeyi kapatabilirsin |
| «The Jira Worklog folder was not found» | `jira-worklog` klasörünü taşıdıysan Terminal'de `bash ~/jira-worklog/install.sh` çalıştır |
| Uygulamayı açarken «Rosetta» kurmak istiyor | Gerek yok, iptal edebilirsin. Terminal'de `bash ~/jira-worklog/install.sh --app-only` çalıştır, sonra uygulamayı yeniden aç |
| Windows: «Jira Worklog could not start» | `%LOCALAPPDATA%\jira-worklog\launcher.log` dosyasını bana gönder |
| Uygulama hiç açılmıyor | Terminal'de `bash ~/jira-worklog/start.sh` yaz; çıkan mesajı bana gönder |

Başka bir hata olursa ekranın fotoğrafını gönder.
