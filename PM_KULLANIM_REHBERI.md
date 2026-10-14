# Jira Worklog Raporu – Kullanım Rehberi

Bu uygulama, seçtiğin projede **kim, hangi gün ve saatte, hangi task'a ne kadar süre girmiş** bilgisini
Excel dosyası olarak verir. Jira'dan sadece okur; hiçbir kaydı değiştirmez veya silmez.

## 1) İlk kurulum (bir kez, yaklaşık 5 dakika)

1. **Terminal**'i aç: `Cmd + Boşluk` tuşlarına bas, «Terminal» yaz, Enter'a bas.
2. Aşağıdaki satırı **tamamen kopyalayıp** Terminal'e yapıştır ve Enter'a bas:

   ```
   git clone https://github.com/aliyetim/jira-worklog.git ~/jira-worklog && bash ~/jira-worklog/install.sh
   ```

3. Ekranda «komut satırı geliştirici araçlarını yüklemek ister misin?» gibi bir pencere çıkarsa **Install** (Yükle)'ye bas,
   bitmesini bekle (birkaç dakika). Sonra 2. adımdaki satırı **bir kez daha** yapıştırıp Enter'a bas.
   Pencere hiç çıkmazsa bu adımı atla.
4. «Setup complete» yazısını görünce bir Finder penceresi açılır; içinde **Jira Worklog** uygulaması vardır.
   Terminal'i kapatabilirsin.

Bundan sonra uygulamayı **Launchpad**'den ya da `Cmd + Boşluk` ile «Jira Worklog» yazarak açarsın.
İstersen Finder'da açılan uygulamayı Dock'a sürükleyerek sabitleyebilirsin.

Bu uygulama Mac'inde kurulum sırasında üretildiği için «Apple doğrulayamadı» uyarısı çıkmaz.
Uygulamayı açınca birkaç saniye içinde tarayıcıda **Worklog report** sayfası açılır. Uygulamanın dili İngilizcedir.

## 2) Token üretme (bir kez; süresi dolunca yenile)

Token, Jira'ya senin adına giriş yapan geçici bir şifredir. **Kendi token'ını üret, kimseyle paylaşma.**

1. Jira'ya giriş yap, sağ üstte profil resmine tıkla, **Profile**'ı aç.
2. Soldaki menüden **Personal Access Tokens**'ı seç.
3. **Create token** de, ad olarak «worklog rapor» yaz ve oluştur.
4. Çıkan uzun metni kopyala. (Bir daha gösterilmez; kaybedersen yenisini üretirsin.)

Menü adları Jira sürümüne göre biraz değişebilir. Sayfadaki **How do I create one?** bağlantısı da aynı adımları gösterir.

## 3) Rapor alma

1. Uygulamayı aç. Sayfa tarayıcıda açılır.
2. **Jira address:** İlk seferde Jira'nın ana adresini yaz (sana verilen adres, örn. `https://jira.sirketiniz.com`). Bir sonraki sefere hatırlanır.
3. **Project key:** Task numaralarının başındaki kısa kod. `PROJ-123` için `PROJ`.
4. **Period:** Last month (geçen ay), This month (bu ay) ya da Custom range (iki tarihi takvimden seçersin).
5. **Jira token:** Kopyaladığın token'ı yapıştır. Uygulama token'ı kaydetmez, her açılışta yeniden yapıştırırsın.
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
| You do not have permission for this | O projeye Jira'da erişimin olmayabilir; proje anahtarını kontrol et |
| Could not reach Jira | Şirket ağında ya da VPN'de olduğundan emin ol |
| No worklogs found for the selected project in this period | Proje anahtarını ve tarihleri kontrol et |
| Lost connection to the app | Uygulamayı yeniden aç; eski sekmeyi kapatabilirsin |
| «The Jira Worklog folder was not found» | `jira-worklog` klasörünü taşıdıysan Terminal'de `bash ~/jira-worklog/install.sh` çalıştır |
| Uygulama hiç açılmıyor | Terminal'de `bash ~/jira-worklog/start.sh` yaz; çıkan mesajı bana gönder |

Başka bir hata olursa ekranın fotoğrafını gönder.
