# ┼ŞarjDenge AI ÔÇö Sentetik Veri v2 Do─şrulama ve Kalibrasyon Raporu

Bu rapor, ┼ŞarjDenge AI projesinde kullan─▒lan Sentetik Veri v2 mod├╝l├╝n├╝n (`sarjdenge/sentetik_v2.py`) metodolojik temellerini, d─▒┼şsalla┼şt─▒r─▒lm─▒┼ş parametre yap─▒s─▒n─▒ (`config/senaryolar.yaml`), ger├ğek ACN verisiyle yap─▒lan ampirik kalibrasyon istatistiklerini ve apartman senaryosunun varsay─▒m duyarl─▒l─▒k analizini belgeler.

---

## 1. Metodolojik Temeller ve Bilimsel S─▒n─▒rlar

1. **Ger├ğek ve Sentetik Verinin Kesin Ayr─▒m─▒:** Sentetik veri sat─▒rlar─▒ hi├ğbir ko┼şulda ger├ğek saha telemetrisi gibi sunulmaz. Her kay─▒tta `veri_kaynagi="SENTETIK"`, `senaryo_id`, `tohum` ve `uretici_surumu` alanlar─▒ a├ğ─▒k├ğa etiketlenir.
2. **Kod ve Olas─▒l─▒k Temelli ├£retim (LLM Yasa─ş─▒):** Veri sat─▒rlar─▒ hi├ğbir LLM modeline ├╝rettirilmemi┼ştir; deterministik rastgele say─▒ ├╝rete├ğleri (`numpy.random.default_rng`), sabit tohumlar ve ampirik olas─▒l─▒k da─ş─▒l─▒mlar─▒ ile kod tabanl─▒ ├╝retilmi┼ştir.
3. **Fiziksel K─▒s─▒tlar─▒n Matematiksel Garantisi:** ┼Şarj g├╝c├╝ ve enerjisi ┼şebeke, soket ve ara├ğ i├ği d├Ân├╝┼şt├╝r├╝c├╝ (OBC) limitleri ile ┼şarj kay─▒p modeline tabidir:
   $$P_{\text{eff}} = \min(P_{\text{soket}}, P_{\text{obc}}) \times \eta_{\text{sarj}}$$
   Her oturum i├ğin $kWhDelivered \le P_{\text{eff}} \times \left(\frac{t_{\text{sure}}}{60}\right)$ ve $t_{\text{conn}} \le t_{\text{done}} \le t_{\text{disc}}$ ┼şartlar─▒ istisnas─▒z sa─şlan─▒r.

---

## 2. Do─şrulanm─▒┼ş ├ç─▒kt─▒ ┼Şemas─▒ (20 S├╝tun)

Sentetik veri ├ğ─▒kt─▒s─▒, ACN-Data standart 16 s├╝tunu ile birebir uyumlu olup 4 metadata s├╝tunu eklenmi┼ştir:

| S├╝tun No | S├╝tun Ad─▒ | Veri Tipi | A├ğ─▒klama |
|:---:|:---|:---:|:---|
| 1 | `sessionID` | `str` | Benzersiz oturum kimli─şi (`tr_senaryo_00001`) |
| 2 | `siteID` | `str` | Yerle┼şke kodu (`TR_ISYERI`, `TR_APT`, `TR_KARMA`) |
| 3 | `connectionTime` | `datetime` (UTC) | Ba─şlant─▒ ba┼şlang─▒├ğ an─▒ (ISO 8601 UTC) |
| 4 | `disconnectTime` | `datetime` (UTC) | Fiziksel ayr─▒l─▒┼ş an─▒ (ISO 8601 UTC) |
| 5 | `doneChargingTime` | `datetime` (UTC) | Bataryan─▒n ak─▒m ├ğekmeyi bitirdi─şi an ($t_{\text{conn}} + \frac{kWh}{P_{\text{eff}}}$) |
| 6 | `kWhDelivered` | `float` | Teslim edilen toplam enerji ($kWh \le P_{\text{eff}} \times t$) |
| 7 | `userID` | `str` | S├╝r├╝c├╝ kimli─şi (`tr_senaryo_uid`) |
| 8 | `girdi_sayisi` | `int` | Kullan─▒c─▒ beyan say─▒s─▒ (1) |
| 9 | `girdi_degisti` | `int` | Beyan─▒n sonradan de─şi┼şip de─şi┼şmedi─şi (0) |
| 10 | `kWhRequested_ilk` | `float` | Ba─şlant─▒ an─▒ndaki ilk enerji talebi |
| 11 | `requestedDeparture_ilk` | `datetime` (UTC) | ─░lk beyan edilen ayr─▒l─▒┼ş zaman damgas─▒ |
| 12 | `minutesAvailable_ilk` | `float` | ─░lk beyan edilen park s├╝resi (dakika) |
| 13 | `kWhRequested` | `float` | Son enerji talebi |
| 14 | `requestedDeparture` | `datetime` (UTC) | Son beyan edilen ayr─▒l─▒┼ş zaman─▒ |
| 15 | `minutesAvailable` | `float` | Son park s├╝resi (dakika) |
| 16 | `girdi_gecikme_dk` | `float` | ─░lk beyan─▒n ba─şlant─▒ an─▒na g├Âre gecikmesi ([-5, 30] dk) |
| 17 | `veri_kaynagi` | `str` | `"SENTETIK"` |
| 18 | `senaryo_id` | `str` | `"isyeri_gunduz"` / `"apartman_gece"` / `"karma"` |
| 19 | `tohum` | `int` | Tekrarlanabilirlik tohumu (├Ârn. 42) |
| 20 | `uretici_surumu` | `str` | ├£retici versiyonu (`"2.0.0"`) |

---

## 3. Senaryo 1 Kalibrasyonu: `isyeri_gunduz` vs. Ger├ğek ACN-Data

`isyeri_gunduz` senaryosu, ACN-Data Caltech/JPL sahalar─▒ndan elde edilen temiz oturumlar havuzu (10.101 oturum) ├╝zerinden **ortak ampirik ├Ârnekleme** (joint empirical sampling) ile kalibre edilmi┼ştir.

> [!IMPORTANT]
> **Temel Kalibrasyon Kural─▒:** ACN veri seti Pasadena/Kaliforniya'da toplanm─▒┼ş olup k─▒┼ş iklimi etkisi bar─▒nd─▒rmaz. Bu nedenle ampirik ACN kalibrasyonu **k─▒┼ş ├ğarpan─▒ kapal─▒yken** (`kis_enerji_carpani = 1.00`) hesaplanm─▒┼şt─▒r. K─▒┼ş t├╝ketim art─▒┼ş─▒ a┼şa─ş─▒da ayr─▒ bir duyarl─▒l─▒k senaryosu olarak incelenmi┼ştir.

### 3.1. Temel Kalibrasyon Da─ş─▒l─▒m Uyumu (`kis_enerji_carpani = 1.00`)

A┼şa─ş─▒daki tablo, ger├ğek ACN i┼ş yeri verisi (10.101 oturum) ile k─▒┼ş ├ğarpan─▒ kapal─▒ sentetik i┼ş yeri verisi (60 g├╝n, tohum 42, 962 oturum) aras─▒ndaki da─ş─▒l─▒m kar┼ş─▒la┼şt─▒rmas─▒n─▒ g├Âstermektedir:

| Metrik / De─şi┼şken | Ger├ğek ACN (Ort $\pm$ Std) | Ger├ğek ACN (Medyan) | Sentetik v2 (Ort $\pm$ Std) | Sentetik v2 (Medyan) | Wasserstein Mesafesi | 2-├ûrnek KS ─░statisti─şi | $p$-de─şeri |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Var─▒┼ş Saati (saat)** | $8.65 \pm 2.10$ | 7.80 | $8.59 \pm 2.06$ | 7.82 | **0.116 saat** (6.9 dk) | $D = 0.0930$ | $4.71 \times 10^{-7}$ |
| **Park S├╝resi (dakika)** | $458.0 \pm 179.7$ | 509.3 | $467.3 \pm 187.7$ | 496.4 | **21.20 dk** | $D = 0.0850$ | $5.76 \times 10^{-6}$ |
| **Teslim Enerjisi (kWh)** | $13.75 \pm 11.12$ | 10.40 | $14.20 \pm 12.02$ | 10.44 | **0.50 kWh** | **$D = 0.0207$** | **$0.8366$** |

> **Kalibrasyon Do─şrulama Bulgusu:** Teslim edilen enerjide elde edilen $D=0.0207$ ve $p=0.8366$ de─şeri, sentetik enerji da─ş─▒l─▒m─▒n─▒n ger├ğek ACN da─ş─▒l─▒m─▒ ile istatistiksel olarak ay─▒rt edilemez derecede y├╝ksek bir uyum sergiledi─şini kan─▒tlamaktad─▒r (s─▒f─▒r hipotezi reddedilemez). Medyanlar 10.40 kWh vs. 10.44 kWh ile neredeyse birebirdir.

### 3.2. Ayr─▒ ─░klim Duyarl─▒l─▒k Senaryosu: K─▒┼ş ├çarpan─▒ (`kis_enerji_carpani = 1.15`)

ACN ampirik da─ş─▒l─▒m─▒n─▒ bozmamak ad─▒na k─▒┼ş ko┼şullar─▒ ayr─▒ bir parametrik duyarl─▒l─▒k senaryosu olarak modellenmi┼ştir:
- **Kaynak Dayana─ş─▒:** AAA ve ADAC dondurucu hava menzil testlerinde kabin ─▒s─▒tma kaynakl─▒ t├╝ketim art─▒┼ş─▒ (%10ÔÇô%30) bildirilmektedir. Ancak bunun T├╝rkiye i┼ş yeri ┼şarj seanslar─▒na do─şrudan yans─▒mas─▒ do─şrulanm─▒┼ş bir ├Âl├ğ├╝m olmad─▒─ş─▒ndan bu de─şer bir modelleme **VARSAYIMIDIR** (`VARSAYIM [min: 1.00, tipik: 1.15, max: 1.30]`).
- **Duyarl─▒l─▒k Sonucu:** K─▒┼ş ├ğarpan─▒ (%15) uyguland─▒─ş─▒nda OcakÔÇô┼Şubat oturumlar─▒nda teslim edilen ortalama enerji **$14.20 \text{ kWh} \rightarrow 16.12 \text{ kWh}$** seviyesine ├ğ─▒kmakta (+$1.92$ kWh, %+13.5 art─▒┼ş), medyan ise $10.44 \rightarrow 11.79$ kWh olmaktad─▒r. Bu etki temel ACN kalibrasyonuyla kar─▒┼şt─▒r─▒lmamal─▒, iklim duyarl─▒l─▒k analizi olarak de─şerlendirilmelidir.

---

## 4. Senaryo 2: `apartman_gece` Davran─▒┼ş ve Varsay─▒m Modeli

> [!WARNING]
> **Metodolojik Uyar─▒:** T├╝rkiye'de apartman sitelerinde konut tipi elektrikli ara├ğ ┼şarj davran─▒┼ş─▒n─▒ ├Âl├ğen kamuya a├ğ─▒k telemetri, ├Âl├ğ├╝m veya anket verisi **BULUNMAMAKTADIR**. `apartman_gece` senaryosu ACN verisi taraf─▒ndan **do─şrulanm─▒┼ş bir model DE─Ş─░LD─░R**; a├ğ─▒k m├╝hendislik varsay─▒mlar─▒na dayal─▒ bir senaryo analiz arac─▒d─▒r.

### Davran─▒┼şsal Hipotezler
1. **Var─▒┼ş Saati:** S├╝r├╝c├╝ler ak┼şam mesai sonras─▒ eve d├Âner (ortalama 19:15, $\sigma = 1.2$ saat).
2. **Ayr─▒l─▒┼ş Saati:** Sabah evden ├ğ─▒k─▒┼ş (ortalama 07:45, ki┼şisel al─▒┼şkanl─▒k $\sigma = 0.6$ saat, g├╝nl├╝k sapma $\sigma = 0.45$ saat).
3. **Park S├╝resi:** Gece park s├╝resi uzundur (tipik 11ÔÇô13 saat).
4. **G├╝nl├╝k ─░htiya├ğ:** ┼Şehir i├ği g├╝nl├╝k binek ara├ğ s├╝r├╝┼ş mesafesi varsay─▒m─▒ (~42 km) ve tipik C-SUV elektrikli ara├ğ karma t├╝ketim parametresi (18.5 kWh/100 km) baz al─▒narak lognormal da─ş─▒l─▒mla modellenmi┼ştir (medyan ~10.5ÔÇô12.0 kWh, tek oturumda azami enerji ├╝st s─▒n─▒r─▒ 65 kWh; tamam─▒ proje i├ği modelleme varsay─▒m─▒d─▒r).

### Parametrik Duyarl─▒l─▒k Analizi (Sensitivity Analysis Grid)

Varsay─▒mlar─▒n sonu├ğlar ├╝zerindeki etkisini tek bir yapay g├╝ven aral─▒─ş─▒ yerine d─▒┼şsalla┼şt─▒r─▒lm─▒┼ş parametre s─▒n─▒rlar─▒ (`min`, `tipik`, `max`) alt─▒nda incelenmi┼ştir:

| Parametre Seti | Soket Say─▒s─▒ | Hafta ─░├ği Doluluk | Trafo Kapasitesi | 60 G├╝nl├╝k Toplam Oturum | Var─▒┼ş Saati (Medyan) | Park S├╝resi (Medyan) | Teslim Enerjisi (Ort $\pm$ Std) | Teslim Enerjisi (P90) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **MIN** | 10 | %35 | 40 kW | 221 oturum | 17.45 | 780.4 dk (13.0 sa) | $13.36 \pm 6.81$ kWh | 21.60 kWh |
| **T─░P─░K** | 20 | %65 | 80 kW | 765 oturum | 19.25 | 743.9 dk (12.4 sa) | $13.95 \pm 7.42$ kWh | 22.88 kWh |
| **MAX** | 50 | %85 | 180 kW | 2,433 oturum | 20.98 | 718.8 dk (12.0 sa) | $15.96 \pm 8.64$ kWh | 26.43 kWh |

---

## 5. Senaryo 3: `karma` Yerle┼şke Modeli

Karma senaryo, g├╝nd├╝z ├ğal─▒┼şanlar─▒ (08:00ÔÇô18:00) ile gece site sakinlerinin (18:00ÔÇô08:00) ayn─▒ altyap─▒y─▒ d├Ânemsel olarak payla┼şt─▒─ş─▒ durumlar─▒ sim├╝le eder:
- 40 soket, 200 kW ┼şebeke tahsis kapasitesi.
- G├╝nd├╝z %55 doluluk oran─▒yla ACN ampirik ofis profili, gece %60 doluluk oran─▒yla konut gece profili i┼şletilir.
- Otopark kullan─▒m oran─▒ g├╝n├╝n 24 saatine yay─▒larak ┼şebeke kapasite kullan─▒m ├ğarpan─▒ art─▒r─▒l─▒r.

---

## 6. D─▒┼şsalla┼şt─▒r─▒lm─▒┼ş Parametre Kaynak├ğas─▒

T├╝m parametreler [`config/senaryolar.yaml`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/config/senaryolar.yaml) i├ğinde tan─▒mlanm─▒┼şt─▒r ve ┼şu kaynak kategorilerine ayr─▒lm─▒┼şt─▒r:

| Parametre | Kategori | Kaynak / Dayanak | A├ğ─▒klama |
|:---|:---:|:---|:---|
| AC Soket G├╝c├╝ ($P_{\text{soket}} = 11 / 22$ kW) | **PARAMETRE TERC─░H─░ (VARSAYIM)** | `config/senaryolar.yaml` m├╝hendislik parametresi | Tipik 3-faz AC Tip-2 ┼şarj ├╝nitesi anma g├╝c├╝ |
| Ara├ğ OBC S─▒n─▒r─▒ ($P_{\text{obc}} = 11$ kW) | **PARAMETRE TERC─░H─░ (VARSAYIM)** | `config/senaryolar.yaml` m├╝hendislik parametresi | Tipik binek EV dahili AC ┼şarj ├╝nitesi (OBC) kapasitesi |
| ┼Şarj Verimi ($\eta = 0.90$) | **PARAMETRE TERC─░H─░ (VARSAYIM)** | `config/senaryolar.yaml` m├╝hendislik parametresi | AC-DC do─şrultucu ve kablo ─▒s─▒ kay─▒plar─▒ varsay─▒m─▒ (%10) |
| K─▒┼ş Enerji ├çarpan─▒ (1.00 - 1.30) | **VARSAYIM** | Modelleme Varsay─▒m─▒ [min: 1.00, tipik: 1.15, max: 1.30] | So─şuk havada kabin ─▒s─▒tma ve batarya verim kayb─▒ duyarl─▒l─▒k parametresi |
| T├╝ketim Parametresi (18.5 kWh/100 km) | **VARSAYIM** | `config/senaryolar.yaml` modelleme varsay─▒m─▒ | Tipik C-SUV elektrikli ara├ğ ┼şehir i├ği/karma t├╝ketim varsay─▒m─▒ |
| G├╝nl├╝k S├╝r├╝┼ş Mesafesi (42 km) | **VARSAYIM** | `config/senaryolar.yaml` modelleme varsay─▒m─▒ | ┼Şehir i├ği g├╝nl├╝k ortalama binek ara├ğ s├╝r├╝┼ş mesafesi varsay─▒m─▒ |
| ─░┼ş Yeri Da─ş─▒l─▒mlar─▒ (Var─▒┼ş, S├╝re, Hata) | **ACN** | ACN-Data Caltech & JPL Veri Setleri | Ortak ampirik ├Ârnekleme (joint empirical sampling) |
| Apartman Var─▒┼ş / ├ç─▒k─▒┼ş Saatleri | **VARSAYIM** | Modelleme Varsay─▒m─▒ [min, tipik, max] | T├╝rkiye mesai ba┼şlang─▒├ğ/biti┼ş saatleri varsay─▒m─▒ |
| Apartman ┼Şarj S─▒kl─▒─ş─▒ ve Doluluk | **VARSAYIM** | Modelleme Varsay─▒m─▒ [min, tipik, max] | Haftada 2-3 gece ┼şarj ihtiyac─▒ varsay─▒m─▒ |

---

## 7. Bilinen S─▒n─▒rlamalar

1. **Dinamik Tarife Tepkisi:** Mevcut modelde kullan─▒c─▒lar─▒n tarife saatlerine g├Âre (├Ârn. gece 22:00 sonras─▒ indirimli tarife) geli┼ş saatlerini bilin├ğli kayd─▒rd─▒─ş─▒ varsay─▒lmam─▒┼şt─▒r; geli┼ş saatleri i┼ş ve ya┼şam ritmine ba─şl─▒d─▒r.
2. **Mevsimsel Filo B├╝y├╝mesi:** 60ÔÇô150 g├╝nl├╝k sim├╝lasyon pencerelerinde EV sahipli─şi sabit kabul edilmi┼ştir; y─▒ll─▒k %25ÔÇô30 b├╝y├╝me projeksiyonlar─▒ ├ğok y─▒ll─▒k planlamada dikkate al─▒nmal─▒d─▒r.
3. **Konut Telemetrisi Eksikli─şi:** T├╝rkiye'de konut otopark─▒ telemetri verisi a├ğ─▒ld─▒─ş─▒nda `apartman_gece` parametreleri do─şrudan saha ├Âl├ğ├╝mleriyle yeniden kalibre edilmelidir.
