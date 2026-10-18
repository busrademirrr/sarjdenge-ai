# ŞarjDenge AI — Veri Hazırlama Kuralları

**Durum: KİLİTLENDİ (Aşama 2 — Veri Hijyeni Kapsamında)**  
**Referans Yapılandırma:** [`data/hijyen.yaml`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/data/hijyen.yaml)  
**Tarih:** 2026-10-17  

Bu belge, ACN ham verisini koruyan, tekrar üretilebilir ve zaman sızıntılarından arındırılmış bir veri hazırlama hattı için kesinleştirilmiş kuralları içerir. Bu kuralların kod tarafından uygulandığı [`tests/test_veri_hijyeni.py`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/tests/test_veri_hijyeni.py) ile doğrulanmıştır.

---

## 1. Dosya ve Veri Kaynağı Yönetimi

1. **Ham Veri Dokunulmazlığı:** Ham ACN CSV dosyaları (`acn_oturumlar_v2.csv`, `acn_oturumlar_temmuz_aralik.csv`) kesinlikle değiştirilmez ve üzerine yazılmaz.
2. **Dizin Ayrımı:**
   - Ham arşiv: `data/ham/`
   - Temizlenmiş ara türevler: `data/islenmis/` (ihtiyaç halinde)
   - Taze test dönemi: `data/holdout_2020_01_02/`
3. **Manifest Denetimi:** Her ham dosya için dosya adı, satır sayısı, benzersiz `sessionID`, başlangıç/bitiş zaman damgası ve SHA-256 özeti [`data/MANIFEST.md`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/data/MANIFEST.md) içinde belgelenir.
4. **Çift Kopya Uyarısı:** `acn_ocak_temmuz.csv`, `acn_oturumlar_ocak_haziran.csv` ve `acn_oturumlar_v2.csv` dosyaları aynı hash'e (`3e6e6aa2a199...`) sahip kopyalardır; bağımsız veri seti gibi değerlendirilemez.
5. **İndirme Güvenliği:** `acn_veri_cek.py` betiği proje kökünden varsayılan parametreyle çalıştırılmaz; aksi halde `acn_oturumlar_v2.csv` dosyasını ezebilir. Çıktı yolu açıkça güvenli bir klasöre yönlendirilmelidir.

---

## 2. Beklenen Ham Alanlar ve Veri Sözlüğü (16 Sütun)

| Sıra | Sütun Adı | Orijinal Tip | UTC Formatı / Örnek | Karar Anında Bilinirlik |
|:---:|:---|:---:|:---|:---:|
| 0 | `sessionID` | `str` | Benzersiz oturum kimliği | ✅ Biliniyor |
| 1 | `siteID` | `str` / `int` | Saha kodu (1: Caltech, 2: JPL) | ✅ Biliniyor |
| 2 | `connectionTime` | `datetime` | Bağlantı anı (UTC) | ✅ Biliniyor |
| 3 | `disconnectTime` | `datetime` | Ayrılış anı (Süre Hedefi) | ❌ Hedef (Gelecek) |
| 4 | `doneChargingTime` | `datetime` | Akımın sıfırlandığı an | ❌ Gelecek Bilgisi |
| 5 | `kWhDelivered` | `float` | Teslim edilen enerji | ❌ Hedef (İhtiyaç Göstergesi) |
| 6 | `userID` | `str` | Kullanıcı kimliği | ✅ Biliniyor |
| 7 | `girdi_sayisi` | `int` | Toplam beyan sayısı | ❌ Gelecek Bilgisi |
| 8 | `girdi_degisti` | `int` | Beyanın sonradan değişip değişmediği | ❌ Gelecek Bilgisi |
| 9 | `kWhRequested_ilk` | `float` | İlk enerji talebi beyanı | ✅ Biliniyor |
| 10 | `requestedDeparture_ilk` | `datetime` | İlk ayrılış beyanı | ✅ Biliniyor |
| 11 | `minutesAvailable_ilk` | `float` | İlk park süresi beyanı | ✅ Biliniyor |
| 12 | `kWhRequested` | `float` | Son enerji talebi | ❌ Sızıntı Riski |
| 13 | `requestedDeparture` | `datetime` | Son ayrılış beyanı | ❌ Sızıntı Riski |
| 14 | `minutesAvailable` | `float` | Son park süresi | ❌ Sızıntı Riski |
| 15 | `girdi_gecikme_dk` | `float` | Beyan gecikmesi | ✅ Biliniyor ([-5, 30] dk) |

---

## 3. Filtreleme Sırası ve Eşikler

Tüm eşikler [`data/hijyen.yaml`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/data/hijyen.yaml) içinde tanımlıdır. Kod içinde sabit değer kullanılamaz.

1. **Şema Kontrolü:** 16 zorunlu sütun eksiksiz olmalıdır.
2. **Oturum Kimliği Tekilliği:** Tekrar eden `sessionID` kayıtları elenir.
3. **Zaman Damgası Bütünlüğü:** `connectionTime` ve `disconnectTime` geçerli ISO/UTC olmalıdır; eksik kayıtlar elenir.
4. **Zaman Mantığı:** $disconnectTime > connectionTime$ olmalıdır.
5. **Süre Kısıtı:** $30 \le sure\_dk \le 2880$ (30 dk ile 48 saat arası). Bu aralık dışındaki oturumlar popülasyon dışı bırakılır.
6. **Enerji Kısıtı:** $kWhDelivered \ge 0.5$ kWh. Altındaki kayıtlar başarısız bağlantı sayılır.
7. **Fiziksel Temiz Küme:** Bu 6 filtre sonucunda kalan kayıtlar `data.yukle()` ile **birebir aynı satır kümesidir** (Ocak–Haziran: **14.219**, Temmuz–Aralık: **13.445**).
8. **Beyan Baseline Alt Kümesi (`beyan_var`):**
   - `requestedDeparture_ilk` ve `kWhRequested_ilk` eksiksiz olmalı,
   - `girdi_gecikme_dk` $[-5.0, 30.0]$ dakika aralığında olmalı,
   - $requestedDeparture\_ilk > connectionTime$ olmalıdır.
   Bu filtre uygulandığında kalan satır sayısı Ocak–Haziran için **13.123**, Temmuz–Aralık için **12.298**'dir.

---

## 4. Zaman Sızıntısı Kontrolleri (Zorunlu Güvenlik Kapısı)

1. **Hedef İzolasyonu:** `sure_dk` ve `kWhDelivered` özellik matrisi $X$ içerisine dahil edilemez.
2. **Kronolojik Bölünme:** Eğitim, doğrulama ve test pencereleri kesinlikle zamana göre sıralı ayrılır ($connectionTime_{egit\_max} < connectionTime_{test\_min}$). Rastgele satır bölünmesi (random train_test_split) kesinlikle yasaktır.
3. **Kullanıcı Geçmişi Shift ve Tamamlanma Denetimi:**
   - Standart `cumsum - self` işlemi kullanıcının kendi satırını çıkarır; ancak kullanıcının önceki oturumunun fiilen tamamlandığını garanti etmez.
   - `strict_shift=True` kuralı uyarınca, bir önceki oturumun $disconnectTime$ değeri mevcut oturumun $connectionTime$ değerinden büyükse (çakışan oturum), o oturum geçmiş ortalamalarına dahil edilmez.
4. **Dondurulmuş Ön Değerlendirme:** Normalizasyon, frekans hesapları ve model parametreleri yalnızca geliştirme verisi üzerinde fit edilir. Test verisinde fit yapılamaz.

---

## 5. Çıktılar ve Doğrulama

Her çalıştırma aşağıdaki belgelerle denetlenir:
- `data/MANIFEST.md`: Dosya özetleri ve çift kopya analizi.
- `docs/VERI_TEMIZLEME_RAPORU.md`: Saha bazlı şelale tablosu ve veri sözlüğü.
- `tests/test_veri_hijyeni.py`: Otomatik sızıntı ve eşleşme testleri.
