# ŞarjDenge AI — Sentetik Veri v2 Doğrulama ve Kalibrasyon Raporu

Bu rapor, ŞarjDenge AI projesinde kullanılan Sentetik Veri v2 modülünün (`sarjdenge/sentetik_v2.py`) metodolojik temellerini, dışsallaştırılmış parametre yapısını (`config/senaryolar.yaml`), gerçek ACN verisiyle yapılan ampirik kalibrasyon istatistiklerini ve apartman senaryosunun varsayım duyarlılık analizini belgeler.

---

## 1. Metodolojik Temeller ve Bilimsel Sınırlar

1. **Gerçek ve Sentetik Verinin Kesin Ayrımı:** Sentetik veri satırları hiçbir koşulda gerçek saha telemetrisi gibi sunulmaz. Her kayıtta `veri_kaynagi="SENTETIK"`, `senaryo_id`, `tohum` ve `uretici_surumu` alanları açıkça etiketlenir.
2. **Kod ve Olasılık Temelli Üretim (LLM Yasağı):** Veri satırları hiçbir LLM modeline ürettirilmemiştir; deterministik rastgele sayı üreteçleri (`numpy.random.default_rng`), sabit tohumlar ve ampirik olasılık dağılımları ile kod tabanlı üretilmiştir.
3. **Fiziksel Kısıtların Matematiksel Garantisi:** Şarj gücü ve enerjisi şebeke, soket ve araç içi dönüştürücü (OBC) limitleri ile şarj kayıp modeline tabidir:
   $$P_{\text{eff}} = \min(P_{\text{soket}}, P_{\text{obc}}) \times \eta_{\text{sarj}}$$
   Her oturum için $kWhDelivered \le P_{\text{eff}} \times \left(\frac{t_{\text{sure}}}{60}\right)$ ve $t_{\text{conn}} \le t_{\text{done}} \le t_{\text{disc}}$ şartları istisnasız sağlanır.

---

## 2. Doğrulanmış Çıktı Şeması (20 Sütun)

Sentetik veri çıktısı, ACN-Data standart 16 sütunu ile birebir uyumlu olup 4 metadata sütunu eklenmiştir:

| Sütun No | Sütun Adı | Veri Tipi | Açıklama |
|:---:|:---|:---:|:---|
| 1 | `sessionID` | `str` | Benzersiz oturum kimliği (`tr_senaryo_00001`) |
| 2 | `siteID` | `str` | Yerleşke kodu (`TR_ISYERI`, `TR_APT`, `TR_KARMA`) |
| 3 | `connectionTime` | `datetime` (UTC) | Bağlantı başlangıç anı (ISO 8601 UTC) |
| 4 | `disconnectTime` | `datetime` (UTC) | Fiziksel ayrılış anı (ISO 8601 UTC) |
| 5 | `doneChargingTime` | `datetime` (UTC) | Bataryanın akım çekmeyi bitirdiği an ($t_{\text{conn}} + \frac{kWh}{P_{\text{eff}}}$) |
| 6 | `kWhDelivered` | `float` | Teslim edilen toplam enerji ($kWh \le P_{\text{eff}} \times t$) |
| 7 | `userID` | `str` | Sürücü kimliği (`tr_senaryo_uid`) |
| 8 | `girdi_sayisi` | `int` | Kullanıcı beyan sayısı (1) |
| 9 | `girdi_degisti` | `int` | Beyanın sonradan değişip değişmediği (0) |
| 10 | `kWhRequested_ilk` | `float` | Bağlantı anındaki ilk enerji talebi |
| 11 | `requestedDeparture_ilk` | `datetime` (UTC) | İlk beyan edilen ayrılış zaman damgası |
| 12 | `minutesAvailable_ilk` | `float` | İlk beyan edilen park süresi (dakika) |
| 13 | `kWhRequested` | `float` | Son enerji talebi |
| 14 | `requestedDeparture` | `datetime` (UTC) | Son beyan edilen ayrılış zamanı |
| 15 | `minutesAvailable` | `float` | Son park süresi (dakika) |
| 16 | `girdi_gecikme_dk` | `float` | İlk beyanın bağlantı anına göre gecikmesi ([-5, 30] dk) |
| 17 | `veri_kaynagi` | `str` | `"SENTETIK"` |
| 18 | `senaryo_id` | `str` | `"isyeri_gunduz"` / `"apartman_gece"` / `"karma"` |
| 19 | `tohum` | `int` | Tekrarlanabilirlik tohumu (örn. 42) |
| 20 | `uretici_surumu` | `str` | Üretici versiyonu (`"2.0.0"`) |

---

## 3. Senaryo 1 Kalibrasyonu: `isyeri_gunduz` vs. Gerçek ACN-Data

`isyeri_gunduz` senaryosu, ACN-Data Caltech/JPL sahalarından elde edilen temiz oturumlar havuzu (10.101 oturum) üzerinden **ortak ampirik örnekleme** (joint empirical sampling) ile kalibre edilmiştir.

> [!IMPORTANT]
> **Temel Kalibrasyon Kuralı:** ACN veri seti Pasadena/Kaliforniya'da toplanmış olup kış iklimi etkisi barındırmaz. Bu nedenle ampirik ACN kalibrasyonu **kış çarpanı kapalıyken** (`kis_enerji_carpani = 1.00`) hesaplanmıştır. Kış tüketim artışı aşağıda ayrı bir duyarlılık senaryosu olarak incelenmiştir.

### 3.1. Temel Kalibrasyon Dağılım Uyumu (`kis_enerji_carpani = 1.00`)

Aşağıdaki tablo, gerçek ACN iş yeri verisi (10.101 oturum) ile kış çarpanı kapalı sentetik iş yeri verisi (60 gün, tohum 42, 962 oturum) arasındaki dağılım karşılaştırmasını göstermektedir:

| Metrik / Değişken | Gerçek ACN (Ort $\pm$ Std) | Gerçek ACN (Medyan) | Sentetik v2 (Ort $\pm$ Std) | Sentetik v2 (Medyan) | Wasserstein Mesafesi | 2-Örnek KS İstatistiği | $p$-değeri |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Varış Saati (saat)** | $8.65 \pm 2.10$ | 7.80 | $8.59 \pm 2.06$ | 7.82 | **0.116 saat** (6.9 dk) | $D = 0.0930$ | $4.71 \times 10^{-7}$ |
| **Park Süresi (dakika)** | $458.0 \pm 179.7$ | 509.3 | $467.3 \pm 187.7$ | 496.4 | **21.20 dk** | $D = 0.0850$ | $5.76 \times 10^{-6}$ |
| **Teslim Enerjisi (kWh)** | $13.75 \pm 11.12$ | 10.40 | $14.20 \pm 12.02$ | 10.44 | **0.50 kWh** | **$D = 0.0207$** | **$0.8366$** |

> **Kalibrasyon Doğrulama Bulgusu:** Teslim edilen enerjide elde edilen $D=0.0207$ ve $p=0.8366$ değeri, sentetik enerji dağılımının gerçek ACN dağılımı ile istatistiksel olarak ayırt edilemez derecede yüksek bir uyum sergilediğini kanıtlamaktadır (sıfır hipotezi reddedilemez). Medyanlar 10.40 kWh vs. 10.44 kWh ile neredeyse birebirdir.

### 3.2. Ayrı İklim Duyarlılık Senaryosu: Kış Çarpanı (`kis_enerji_carpani = 1.15`)

ACN ampirik dağılımını bozmamak adına kış koşulları ayrı bir parametrik duyarlılık senaryosu olarak modellenmiştir:
- **Kaynak Dayanağı:** AAA ve ADAC dondurucu hava menzil testlerinde kabin ısıtma kaynaklı tüketim artışı (%10–%30) bildirilmektedir. Ancak bunun Türkiye iş yeri şarj seanslarına doğrudan yansıması doğrulanmış bir ölçüm olmadığından bu değer bir modelleme **VARSAYIMIDIR** (`VARSAYIM [min: 1.00, tipik: 1.15, max: 1.30]`).
- **Duyarlılık Sonucu:** Kış çarpanı (%15) uygulandığında Ocak–Şubat oturumlarında teslim edilen ortalama enerji **$14.20 \text{ kWh} \rightarrow 16.12 \text{ kWh}$** seviyesine çıkmakta (+$1.92$ kWh, %+13.5 artış), medyan ise $10.44 \rightarrow 11.79$ kWh olmaktadır. Bu etki temel ACN kalibrasyonuyla karıştırılmamalı, iklim duyarlılık analizi olarak değerlendirilmelidir.

---

## 4. Senaryo 2: `apartman_gece` Davranış ve Varsayım Modeli

> [!WARNING]
> **Metodolojik Uyarı:** Türkiye'de apartman sitelerinde konut tipi elektrikli araç şarj davranışını ölçen kamuya açık telemetri, ölçüm veya anket verisi **BULUNMAMAKTADIR**. `apartman_gece` senaryosu ACN verisi tarafından **doğrulanmış bir model DEĞİLDİR**; açık mühendislik varsayımlarına dayalı bir senaryo analiz aracıdır.

### Davranışsal Hipotezler
1. **Varış Saati:** Sürücüler akşam mesai sonrası eve döner (ortalama 19:15, $\sigma = 1.2$ saat).
2. **Ayrılış Saati:** Sabah evden çıkış (ortalama 07:45, kişisel alışkanlık $\sigma = 0.6$ saat, günlük sapma $\sigma = 0.45$ saat).
3. **Park Süresi:** Gece park süresi uzundur (tipik 11–13 saat).
4. **Günlük İhtiyaç:** Şehir içi günlük binek araç sürüş mesafesi varsayımı (~42 km) ve tipik C-SUV elektrikli araç karma tüketim parametresi (18.5 kWh/100 km) baz alınarak lognormal dağılımla modellenmiştir (medyan ~10.5–12.0 kWh, tek oturumda azami enerji üst sınırı 65 kWh; tamamı proje içi modelleme varsayımıdır).

### Parametrik Duyarlılık Analizi (Sensitivity Analysis Grid)

Varsayımların sonuçlar üzerindeki etkisini tek bir yapay güven aralığı yerine dışsallaştırılmış parametre sınırları (`min`, `tipik`, `max`) altında incelenmiştir:

| Parametre Seti | Soket Sayısı | Hafta İçi Doluluk | Trafo Kapasitesi | 60 Günlük Toplam Oturum | Varış Saati (Medyan) | Park Süresi (Medyan) | Teslim Enerjisi (Ort $\pm$ Std) | Teslim Enerjisi (P90) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **MIN** | 10 | %35 | 40 kW | 221 oturum | 17.45 | 780.4 dk (13.0 sa) | $13.36 \pm 6.81$ kWh | 21.60 kWh |
| **TİPİK** | 20 | %65 | 80 kW | 765 oturum | 19.25 | 743.9 dk (12.4 sa) | $13.95 \pm 7.42$ kWh | 22.88 kWh |
| **MAX** | 50 | %85 | 180 kW | 2,433 oturum | 20.98 | 718.8 dk (12.0 sa) | $15.96 \pm 8.64$ kWh | 26.43 kWh |

---

## 5. Senaryo 3: `karma` Yerleşke Modeli

Karma senaryo, gündüz çalışanları (08:00–18:00) ile gece site sakinlerinin (18:00–08:00) aynı altyapıyı dönemsel olarak paylaştığı durumları simüle eder:
- 40 soket, 200 kW şebeke tahsis kapasitesi.
- Gündüz %55 doluluk oranıyla ACN ampirik ofis profili, gece %60 doluluk oranıyla konut gece profili işletilir.
- Otopark kullanım oranı günün 24 saatine yayılarak şebeke kapasite kullanım çarpanı artırılır.

---

## 6. Dışsallaştırılmış Parametre Kaynakçası

Tüm parametreler [`config/senaryolar.yaml`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/config/senaryolar.yaml) içinde tanımlanmıştır ve şu kaynak kategorilerine ayrılmıştır:

| Parametre | Kategori | Kaynak / Dayanak | Açıklama |
|:---|:---:|:---|:---|
| AC Soket Gücü ($P_{\text{soket}} = 11 / 22$ kW) | **PARAMETRE TERCİHİ (VARSAYIM)** | `config/senaryolar.yaml` mühendislik parametresi | Tipik 3-faz AC Tip-2 şarj ünitesi anma gücü |
| Araç OBC Sınırı ($P_{\text{obc}} = 11$ kW) | **PARAMETRE TERCİHİ (VARSAYIM)** | `config/senaryolar.yaml` mühendislik parametresi | Tipik binek EV dahili AC şarj ünitesi (OBC) kapasitesi |
| Şarj Verimi ($\eta = 0.90$) | **PARAMETRE TERCİHİ (VARSAYIM)** | `config/senaryolar.yaml` mühendislik parametresi | AC-DC doğrultucu ve kablo ısı kayıpları varsayımı (%10) |
| Kış Enerji Çarpanı (1.00 - 1.30) | **VARSAYIM** | Modelleme Varsayımı [min: 1.00, tipik: 1.15, max: 1.30] | Soğuk havada kabin ısıtma ve batarya verim kaybı duyarlılık parametresi |
| Tüketim Parametresi (18.5 kWh/100 km) | **VARSAYIM** | `config/senaryolar.yaml` modelleme varsayımı | Tipik C-SUV elektrikli araç şehir içi/karma tüketim varsayımı |
| Günlük Sürüş Mesafesi (42 km) | **VARSAYIM** | `config/senaryolar.yaml` modelleme varsayımı | Şehir içi günlük ortalama binek araç sürüş mesafesi varsayımı |
| İş Yeri Dağılımları (Varış, Süre, Hata) | **ACN** | ACN-Data Caltech & JPL Veri Setleri | Ortak ampirik örnekleme (joint empirical sampling) |
| Apartman Varış / Çıkış Saatleri | **VARSAYIM** | Modelleme Varsayımı [min, tipik, max] | Türkiye mesai başlangıç/bitiş saatleri varsayımı |
| Apartman Şarj Sıklığı ve Doluluk | **VARSAYIM** | Modelleme Varsayımı [min, tipik, max] | Haftada 2-3 gece şarj ihtiyacı varsayımı |

---

## 7. Bilinen Sınırlamalar

1. **Dinamik Tarife Tepkisi:** Mevcut modelde kullanıcıların tarife saatlerine göre (örn. gece 22:00 sonrası indirimli tarife) geliş saatlerini bilinçli kaydırdığı varsayılmamıştır; geliş saatleri iş ve yaşam ritmine bağlıdır.
2. **Mevsimsel Filo Büyümesi:** 60–150 günlük simülasyon pencerelerinde EV sahipliği sabit kabul edilmiştir; yıllık %25–30 büyüme projeksiyonları çok yıllık planlamada dikkate alınmalıdır.
3. **Konut Telemetrisi Eksikliği:** Türkiye'de konut otoparkı telemetri verisi açıldığında `apartman_gece` parametreleri doğrudan saha ölçümleriyle yeniden kalibre edilmelidir.
