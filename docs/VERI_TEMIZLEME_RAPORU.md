# ŞarjDenge AI — Veri Temizleme ve Hijyen Raporu

Bu rapor, ACN-Data şarj oturumlarının dışsallaştırılmış yapılandırma (`data/hijyen.yaml`) doğrultusunda temizleme adımlarını, saha bazlı şelale tablolarını, veri sözlüğünü ve zaman bazlı sızıntı denetimlerini belgeler.

> [!IMPORTANT]
> **Metodolojik Hedef Bildirimi:** `kWhDelivered` alanı kullanıcının bataryasının gerçek/tam > enerji ihtiyacı değil; ACN planlayıcısının mevcut kısıtlar altında araca teslim ettiği enerjidir. > Raporlarda ve modellerde 'tarihsel teslim enerjisi / ihtiyaç göstergesi' olarak adlandırılır.

## 1. Dışsallaştırılmış Filtreleme Eşikleri (`data/hijyen.yaml`)

| Parametre | Eşik Değeri | Açıklama |
|:---|:---:|:---|
| `min_sure_dk` | 30.0 dk | 30 dakikadan kısa oturumlar popülasyon dışı bırakılır |
| `max_sure_saat` | 48.0 sa | 48 saatten uzun oturumlar anormal kabul edilir |
| `min_kwh` | 0.5 kWh | 0.5 kWh altındaki test/başarısız bağlantılar elenir |
| `beyan_min_gecikme_dk` | -5.0 dk | Bağlantıdan en fazla 5 dk önceki beyanlar geçerlidir |
| `beyan_max_gecikme_dk` | 30.0 dk | Bağlantıdan en geç 30 dk sonraki beyanlar bağlantı anında bilinen sayılır |

## 2. Eleme Şelalesi: `acn_oturumlar_v2.csv`

| Eleme Adımı / Kural | Caltech (Site 2) | JPL (Site 1) | Toplam | Kalan Kayıt |
|:---|:---:|:---:|:---:|:---:|
| 1. Başlangıç Ham Satır | 5,762 | 8,610 | 14,372 | 14,372 |
| 2. Tekrar Eden sessionID | -0 | -0 | -0 | 14,372 |
| 3. Eksik Zaman veya kWh | -0 | -0 | -0 | 14,372 |
| 4. Negatif / Sıfır Süre | -0 | -0 | -0 | 14,372 |
| 5. Kısa Oturum (<30 dk) | -97 | -42 | -139 | 14,233 |
| 6. Aşırı Uzun Oturum (>48 sa) | -13 | -1 | -14 | 14,219 |
| 7. Yetersiz Enerji (<0.5 kWh) | -0 | -0 | -0 | **14,219** |
| **=> Fiziksel Temiz Küme (`data.yukle` ile aynı)** | **5,652** | **8,567** | **14,219** | **14,219** |
| 8. Eksik Beyan (Dep/kWh yok) | -721 | -283 | -1004 | 13,215 |
| 9. Gecikmiş Beyan (Gecikme >30 dk) | -36 | -56 | -92 | **13,123** |
| **=> Geçerli Beyanlı Küme (`beyan_var==True`)** | **4,895** | **8,228** | **13,123** | **13,123** |

> **Doğrulama Sonucu:**
> `veri_hijyeni.temizle('acn_oturumlar_v2.csv', sadece_beyanli=False)` çıktısı tam **14,219** satırdır ve `data.yukle()` ile **birebir aynı satır kümesidir**.
> Sadece beyanlı oturumlar filtrelendiğinde satır sayısı **13,123** olmaktadır.

## 2. Eleme Şelalesi: `acn_oturumlar_temmuz_aralik.csv`

| Eleme Adımı / Kural | Caltech (Site 2) | JPL (Site 1) | Toplam | Kalan Kayıt |
|:---|:---:|:---:|:---:|:---:|
| 1. Başlangıç Ham Satır | 4,850 | 8,734 | 13,584 | 13,584 |
| 2. Tekrar Eden sessionID | -0 | -0 | -0 | 13,584 |
| 3. Eksik Zaman veya kWh | -0 | -0 | -0 | 13,584 |
| 4. Negatif / Sıfır Süre | -0 | -0 | -0 | 13,584 |
| 5. Kısa Oturum (<30 dk) | -90 | -41 | -131 | 13,453 |
| 6. Aşırı Uzun Oturum (>48 sa) | -8 | -0 | -8 | 13,445 |
| 7. Yetersiz Enerji (<0.5 kWh) | -0 | -0 | -0 | **13,445** |
| **=> Fiziksel Temiz Küme (`data.yukle` ile aynı)** | **4,752** | **8,693** | **13,445** | **13,445** |
| 8. Eksik Beyan (Dep/kWh yok) | -745 | -267 | -1012 | 12,433 |
| 9. Gecikmiş Beyan (Gecikme >30 dk) | -40 | -95 | -135 | **12,298** |
| **=> Geçerli Beyanlı Küme (`beyan_var==True`)** | **3,967** | **8,331** | **12,298** | **12,298** |

> **Doğrulama Sonucu:**
> `veri_hijyeni.temizle('acn_oturumlar_temmuz_aralik.csv', sadece_beyanli=False)` çıktısı tam **13,445** satırdır ve `data.yukle()` ile **birebir aynı satır kümesidir**.
> Sadece beyanlı oturumlar filtrelendiğinde satır sayısı **12,298** olmaktadır.

## 3. ACN Veri Sözlüğü (16 Orijinal Sütun)

| Sütun Adı | Veri Tipi | Birim | Anlamı ve Rolü | Karar Anında Biliniyor mu? |
|:---|:---:|:---:|:---|:---:|
| `sessionID` | `str` | - | Oturuma ait benzersiz kimlik | ✅ Evet |
| `siteID` | `str` / `int` | - | Şarj istasyonu sahası (1: JPL, 2: Caltech) | ✅ Evet |
| `connectionTime` | `datetime` (UTC) | - | Aracın şarj istasyonuna bağlandığı an | ✅ Evet |
| `disconnectTime` | `datetime` (UTC) | - | Aracın istasyondan ayrıldığı an (süre hedefi) | ❌ Hayır (Hedef) |
| `doneChargingTime` | `datetime` (UTC) | - | Bataryanın akım çekmeyi bitirdiği an | ❌ Hayır (Gelecek) |
| `kWhDelivered` | `float` | kWh | İstasyondan aktarılan toplam enerji (ihtiyaç göstergesi) | ❌ Hayır (Hedef) |
| `userID` | `str` | - | Sürücü kimliği (geçmiş oturumları eşleştirmek için) | ✅ Evet |
| `girdi_sayisi` | `int` | adet | Kullanıcının girdiği ayrılış/enerji beyan sayısı | ❌ Hayır (Sonradan artabilir) |
| `girdi_degisti` | `int` | 0/1 | Kullanıcının ilk beyanını sonradan değiştirip değiştirmediği | ❌ Hayır (Sonradan belirlenir) |
| `kWhRequested_ilk` | `float` | kWh | Kullanıcının bağlantı anında (ilk) talep ettiği enerji | ✅ Evet |
| `requestedDeparture_ilk` | `datetime` (UTC) | - | Kullanıcının bağlantı anında (ilk) beyan ettiği ayrılış | ✅ Evet |
| `minutesAvailable_ilk` | `float` | dk | Kullanıcının ilk park süresi beyanı | ✅ Evet |
| `kWhRequested` | `float` | kWh | Kullanıcının son enerji talebi (güncellenmiş olabilir) | ❌ Sızıntı Riski |
| `requestedDeparture` | `datetime` (UTC) | - | Kullanıcının son ayrılış beyanı (güncellenmiş olabilir) | ❌ Sızıntı Riski |
| `minutesAvailable` | `float` | dk | Kullanıcının son park süresi | ❌ Sızıntı Riski |
| `girdi_gecikme_dk` | `float` | dk | İlk beyanın bağlantı zamanına göre gecikmesi | ✅ Evet ([-5, 30] dk) |

## 4. Zaman Sızıntısı ve Shift Testi Doğrulama Bulguları

1. **Hedef Ayrımı:** `sure_dk` ve `kWhDelivered` özellik matrisi $X$ içerisinden kesinlikle çıkarılmıştır.
2. **Kronolojik Eğitim/Test Ayrımı:** Veriler zaman damgasına göre sıralı bölünür. Eğitim kümesinin en son `connectionTime` değeri, test kümesinin en erken `connectionTime` değerinden küçüktür (çakışma sıfırdır).
3. **Kullanıcı Geçmişi Shift Denetimi:** Standart `cumsum - self` işlemi, kullanıcının mevcut oturumunu dışarıda bırakır. Ancak veri setinde nadir rastlanan (Ocak–Haziran'da 1, Temmuz–Aralık'ta 3 adet) çakışan/eşzamanlı oturum durumunda önceki oturumun `disconnectTime` değeri mevcut oturumun başlangıcından sonraya sarkabilmektedir. `strict_shift=True` parametresi bu oturumları kesinlikle dışarıda tutarak tam sızıntısız geçmiş özellik üretir.

