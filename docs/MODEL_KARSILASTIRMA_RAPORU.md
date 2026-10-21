# ┼ŞarjDenge AI ÔÇö Model Kar┼ş─▒la┼şt─▒rma ve Do─şrulama Raporu (─░┼ş Paketi C)

Bu rapor, ┼ŞarjDenge AI projesi kapsam─▒nda elektrikli ara├ğ ┼şarj oturumlar─▒n─▒n s├╝re (`sure_dk`) ve teslim edilen enerji (`kWhDelivered`) ihtiya├ğlar─▒n─▒ tahmin etmek amac─▒yla geli┼ştirilen quantile modellerinin (`sarjdenge/modeller.py`) kesin kronolojik do─şrulama sonu├ğlar─▒n─▒, objektif model se├ğim skorlar─▒n─▒ ve TemmuzÔÇôAral─▒k 2019 d├Ânemler aras─▒ do─şrulama bulgular─▒n─▒ belgeler.

---

## 1. Metodolojik ├çer├ğeve ve ├ûn Kay─▒t K─▒s─▒tlar─▒

1. **Ba─ş─▒ms─▒z Hedefler ve Enerji Tan─▒m─▒:** S├╝re ve Enerji modelleri farkl─▒ fiziksel birimlere (dakika vs. kWh) sahip oldu─şundan iki hedef asla tek bir skorda toplanmam─▒┼ş; her hedef i├ğin ayr─▒ bir ┼şampiyon model se├ğilmi┼ştir. ACN verisindeki `kWhDelivered` alan─▒ arac─▒n ger├ğek batarya kapasitesini veya toplam ihtiyac─▒n─▒ de─şil, oturumda EVSE taraf─▒ndan teslim edilen enerji miktar─▒n─▒ (ihtiya├ğ g├Âstergesi) temsil eder.
2. **S─▒z─▒nt─▒s─▒z ├ûzellik Matrisi ($X$):** ├ûzellikler yaln─▒zca `veri_hijyeni.ozellikler(strict_shift=True)` ile ├╝retilmi┼ştir. S├╝r├╝c├╝n├╝n ge├ğmi┼ş ├Âzellikleri ($gecmis\_sure$, $gecmis\_kwh$) hesaplan─▒rken yaln─▒zca $disconnectTime \le connectionTime_{\text{mevcut}}$ olan tamamlanm─▒┼ş oturumlar dahil edilmi┼ş, hen├╝z bitmemi┼ş oturumlardan hedef s─▒z─▒nt─▒s─▒ kesinlikle engellenmi┼ştir.
3. **Ba─şlant─▒ An─▒ Beyan G├╝vencesi:** Kullan─▒c─▒ beyan ├Âzelliklerinde sonradan g├╝ncellenmi┼ş de─şerler asla kullan─▒lmam─▒┼ş; yaln─▒zca ba─şlant─▒ an─▒nda bilinen ilk de─şerler (`requestedDeparture_ilk`, `kWhRequested_ilk`, `minutesAvailable_ilk`) kullan─▒lm─▒┼şt─▒r.
4. **Kesin Kronolojik G├╝n S─▒n─▒r─▒:** OcakÔÇôHaziran 2019 verisi yerel g├╝n d├Ân├╝m├╝nde (Los Angeles 00:00:00) kronolojik olarak ikiye b├Âl├╝nm├╝┼şt├╝r:
   - **E─şitim K├╝mesi (Train - %60 g├╝n):** 7.808 oturum.
   - **Do─şrulama K├╝mesi (Validation - %40 g├╝n):** 5.315 oturum.
   - $\max(connectionTime_{\text{egit}}) < \min(connectionTime_{\text{val}})$; zaman ├ğak─▒┼şmas─▒ 0'd─▒r.
5. **D├Ânem S─▒n─▒fland─▒rmas─▒:** TemmuzÔÇôAral─▒k 2019 d├Ânemi daha ├Ânce incelendi─şi i├ğin **"dokunulmam─▒┼ş holdout test seti" olarak adland─▒r─▒lmam─▒┼şt─▒r**; modelin ard─▒┼ş─▒k farkl─▒ bir zaman dilimindeki mevsimsel tutarl─▒l─▒─ş─▒n─▒ test eden bir **"d├Ânemler aras─▒ do─şrulama (out-of-period re-validation)"** olarak i┼şletilmi┼ştir. *(Not: 2020 d├Ânemi verisi daha sonra ─░┼ş Paketi E/F s├╝recinde incelendi─şinden, gelecekteki model se├ğimi ve hiperparametre ayar─▒ i├ğin art─▒k dokunulmam─▒┼ş bir test seti olarak de─şerlendirilemez).*

---

## 2. Sabitlenmi┼ş Model Se├ğim Skoru ($MSS$) Form├╝lasyonu

Model Se├ğim Skoru (MSS), keyf├« de─şerlendirmeleri engellemek amac─▒yla deneyler ├ğal─▒┼şt─▒r─▒lmadan ├Ânce yaz─▒l─▒ olarak kilitlenmi┼ştir:

1. **E─şitim ├ûl├ğek Parametresi ($s_{\text{egit}}$):** Yaln─▒zca e─şitim k├╝mesi hedef da─ş─▒l─▒m─▒ndan ($y_{\text{egit}}$) hesaplan─▒r:
   $$s_{\text{egit}} = \max\left(\text{IQR}(y_{\text{egit}}), \sigma(y_{\text{egit}}), 1.0\right)$$
   - S├╝re hedefi i├ğin: $s_{\text{egit}}^{\text{sure}} = 336.71 \text{ dk}$
   - Enerji hedefi i├ğin: $s_{\text{egit}}^{\text{kwh}} = 11.13 \text{ kWh}$
2. **Normalize Pinball Loss:** $\tilde{\mathcal{L}}_q = \frac{\mathcal{L}_q}{s_{\text{egit}}}$ (Boyutsuz kay─▒p).
3. **Kapsam Hatas─▒ Cezas─▒:** $\mathcal{E}_{\text{kapsam}} = |Coverage(q_{20}) - 0.20| + |Coverage(q_{80}) - 0.80|$.
4. **Birle┼şik Se├ğim Skoru:**
   $$MSS = \frac{1}{3}\left(\tilde{\mathcal{L}}_{q20} + \tilde{\mathcal{L}}_{q50} + \tilde{\mathcal{L}}_{q80}\right) + 1.0 \cdot \mathcal{E}_{\text{kapsam}}$$
   *Kural:* MSS skoru, optimizasyonun ve MPC'nin fiilen kullanaca─ş─▒ **d├╝zeltilmi┼ş (monotonla┼şt─▒r─▒lm─▒┼ş) tahminler** ├╝zerinden hesaplan─▒r.

---

## 3. OcakÔÇôHaziran 2019 Do─şrulama K├╝mesi Kar┼ş─▒la┼şt─▒rma Tablolar─▒

### A. S├╝re Modelleri Kar┼ş─▒la┼şt─▒rmas─▒ ($N_{\text{val}} = 5.315$ Oturum)

| Model Ad─▒ | Ham Pinball (dk) | D├╝zeltilmi┼ş Pinball (dk) | Kapsam $q_{20}$ (Hedef: %20) | Kapsam $q_{80}$ (Hedef: %80) | Kapsam Hatas─▒ | MAE $q_{50}$ (dk) | Quantile Crossing | Normalize Pinball | Model Se├ğim Skoru ($MSS$) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **GlobalEmpirikBaseline** | 67.16 | 67.16 | %21.11 | %81.13 | 0.0224 | 176.96 | %0.00 (0) | 0.1995 | **0.2219** |
| *BeyanGecmisHibrit (Nokta Ref)* | - | - | - | - | - | 120.62 | - | - | *Yar─▒┼ş D─▒┼ş─▒* |
| **QuantileRegressor** | 44.15 | 44.15 | %19.68 | %80.75 | 0.0107 | 104.82 | %0.43 (23) | 0.1311 | **0.1418** |
| **HistGradientBoosting** | 36.15 | 36.10 | %21.52 | %78.10 | 0.0342 | 86.96 | %3.46 (184) | 0.1072 | **0.1415** |
| **GradientBoosting** | 36.94 | 36.93 | **%20.21** | **%79.72** | **0.0049** | 88.67 | %0.87 (46) | 0.1097 | **0.1146** ­şÅå |

> **S├╝re ┼Şampiyonu Se├ğimi:** **`GradientBoosting`**
> HistGradientBoosting Pinball kayb─▒nda 36.10 dk ile ├ğok hafif daha d├╝┼ş├╝k olsa da, `GradientBoosting` modeli neredeyse kusursuz bir ampirik kapsam kalibrasyonu sergilemi┼ştir (q20: %20.21, q80: %79.72, toplam kapsam hatas─▒ yaln─▒zca 0.0049). Ayr─▒ca quantile crossing oran─▒ %0.87 ile olduk├ğa d├╝┼ş├╝kt├╝r. Form├╝lle kilitlenen objektif se├ğim kural─▒ uyar─▒nca **GradientBoosting** ┼Şampiyon S├╝re Modeli se├ğilmi┼ştir.

---

### B. Enerji Modelleri Kar┼ş─▒la┼şt─▒rmas─▒ ($N_{\text{val}} = 5.315$ Oturum)

| Model Ad─▒ | Ham Pinball (kWh) | D├╝zeltilmi┼ş Pinball (kWh) | Kapsam $q_{20}$ (Hedef: %20) | Kapsam $q_{80}$ (Hedef: %80) | Kapsam Hatas─▒ | MAE $q_{50}$ (kWh) | Quantile Crossing | Normalize Pinball | Model Se├ğim Skoru ($MSS$) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **GlobalEmpirikBaseline** | 3.07 | 3.07 | %21.30 | %82.82 | 0.0412 | 7.33 | %0.00 (0) | 0.2754 | **0.3166** |
| *BeyanGecmisHibrit (Nokta Ref)* | - | - | - | - | - | 4.46 | - | - | *Yar─▒┼ş D─▒┼ş─▒* |
| **QuantileRegressor** | 1.67 | 1.67 | %20.34 | %80.81 | 0.0115 | 4.13 | %1.71 (91) | 0.1501 | **0.1616** |
| **HistGradientBoosting** | 1.34 | 1.34 | %24.16 | %79.21 | 0.0495 | 3.35 | %4.82 (256) | 0.1206 | **0.1700** |
| **GradientBoosting** | 1.40 | 1.40 | **%21.62** | **%81.34** | **0.0295** | 3.49 | %2.46 (131) | 0.1254 | **0.1549** ­şÅå |

> **Enerji ┼Şampiyonu Se├ğimi:** **`GradientBoosting`**
> Benzer ┼şekilde, HGB ham Pinball kayb─▒nda 1.34 kWh verse de $q_{20}$ kapsam─▒ %24.16'ya saparak ceza puan─▒ alm─▒┼şt─▒r. `GradientBoosting` hem g├╝├ğl├╝ bir Pinball kayb─▒ (1.40 kWh vs. Global Baseline 3.07 kWh) hem de dengeli kapsam (%21.62 ve %81.34) sa─şlayarak en d├╝┼ş├╝k MSS puan─▒n─▒ (**0.1549**) alm─▒┼ş ve ┼Şampiyon Enerji Modeli se├ğilmi┼ştir.

---

## 4. TemmuzÔÇôAral─▒k 2019 D├Ânemler Aras─▒ Do─şrulama (Out-of-Period Re-validation)

├ûnceden sabitlenen protokole g├Âre:
- ┼Şampiyon modellerin mimari ve hiperparametreleri dondurulmu┼ştur.
- Modeller t├╝m OcakÔÇôHaziran 2019 verisi (%100 - 13.123 oturum) ├╝zerinde yeniden e─şitilmi┼ş ve TemmuzÔÇôAral─▒k 2019 (12.298 ge├ğerli beyanl─▒ oturum) d├Ânemine s─▒f─▒r m├╝dahale ile uygulanm─▒┼şt─▒r.

| Hedef | ┼Şampiyon Model | Ortalama Pinball | Normalize Pinball | Kapsam $q_{20}$ | Kapsam $q_{80}$ | Kapsam Hatas─▒ | MAE $q_{50}$ | Quantile Crossing | D├Ânemler Aras─▒ $MSS$ |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **S├╝re** | `GradientBoosting` | **36.20 dk** | 0.1072 | %22.74 | %80.09 | 0.0283 | 87.27 dk | %0.51 (63) | **0.1355** |
| **Enerji** | `GradientBoosting` | **1.47 kWh** | 0.1340 | %20.80 | %77.98 | 0.0282 | 3.68 kWh | %2.97 (365) | **0.1622** |

> **D├Ânemler Aras─▒ Genelle┼şme Yorumu:**
> OcakÔÇôHaziran do─şrulamas─▒nda elde edilen MSS skorlar─▒ (S├╝re: 0.1146, Enerji: 0.1549) ile TemmuzÔÇôAral─▒k skorlar─▒ (S├╝re: 0.1355, Enerji: 0.1622) birbirine son derece yak─▒nd─▒r. Modeller mevsim ge├ği┼şine ve farkl─▒ zaman dilimine ra─şmen a┼ş─▒r─▒ ├Â─şrenme (overfitting) sergilememi┼ş, tahmin kalitesini ve kapsam kalibrasyonunu korumu┼ştur.

---

## 5. ├çekirdek Sim├╝lat├Âr (`sim.py`) ile Entegrasyon

[`sarjdenge/modeller.py`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/sarjdenge/modeller.py) mod├╝l├╝ `tahminleri_ekle(df_test, sure_modeli, enerji_modeli)` fonksiyonunu sunmaktad─▒r:
- Test k├╝mesindeki her oturum i├ğin s─▒z─▒nt─▒s─▒z ├Âzellik matrisini ├ğ─▒kar─▒r.
- ┼Şampiyon modellerden $q_{20}, q_{50}, q_{80}$ tahminlerini al─▒r ve monotonla┼şt─▒r─▒r.
- D├Ânen DataFrame'e `tahmin_sure_q20`, `tahmin_sure_q50`, `tahmin_sure_q80`, `tahmin_kwh_q20`, `tahmin_kwh_q50`, `tahmin_kwh_q80` s├╝tunlar─▒n─▒ ekler.
- Bu ├ğ─▒kt─▒ do─şrudan dondurulmu┼ş ├ğekirdek sim├╝lat├Âre (`sim.simule(df, yontem=...)`) verilebilir durumdad─▒r; hi├ğbir ├ğekirdek dosyada de─şi┼şiklik gerektirmez.

---

## 6. Bilinen S─▒n─▒rlamalar ve Model Mimarisi Ayr─▒m─▒

1. **`tahmin.py` ile `modeller.py` Aras─▒ndaki Model ve Parametre Farkl─▒l─▒klar─▒:**
   Proje kod taban─▒nda iki ayr─▒ modelleme hatt─▒ mevcuttur:
   - **`sarjdenge/tahmin.py` (v1 ├çekirdek Hatt─▒):** Sadece Scikit-learn `HistGradientBoostingRegressor(loss="quantile", quantile=q, max_iter=150, learning_rate=0.06, max_depth=4, min_samples_leaf=20, random_state=0)` kullan─▒r. S├╝re tahmininde hedef de─şi┼şkene `ys = np.log1p(sure_dk)` d├Ân├╝┼ş├╝m├╝ uygulan─▒r ve tahminde `np.maximum(np.expm1(...), 30.0)` taban─▒ al─▒n─▒r. Bu mod├╝l `sarjdenge/deney.py` taraf─▒ndan kullan─▒l─▒r.
   - **`sarjdenge/modeller.py` (v2 Model Se├ğim Hatt─▒):** Kar┼ş─▒la┼şt─▒rmal─▒ deneyler sonucunda se├ğilen ┼Şampiyon Model, Scikit-learn `GradientBoostingRegressor(loss="quantile", n_estimators=60, max_depth=4, random_state=42)` + `SimpleImputer` pipeline'─▒d─▒r. Hedef de─şi┼şkene log d├Ân├╝┼ş├╝m├╝ yap─▒lmaz; do─şrudan dakika ve kWh ├Âl├ğe─şinde e─şitilir. Tahminler `monotonlastir` fonksiyonu ile $q_{20} \le q_{50} \le q_{80}$ olacak ┼şekilde s─▒ralan─▒r. Bu mod├╝l `sarjdenge/deney_v2.py` taraf─▒ndan kullan─▒l─▒r.
2. **2019 Do─şrulama K├╝mesinde ($N_{\text{val}} = 5.315$) 5 Referans Y├Ântemin Kar┼ş─▒la┼şt─▒r─▒labilirlik Durumu:**
   - *Genel Medyan (Global Median):* `GlobalEmpirikBaseline` modelinin $q_{50}$ ├ğ─▒kt─▒s─▒d─▒r (S├╝re: 480 dk, Enerji: 12.0 kWh). MAE S├╝re: 176.96 dk, MAE Enerji: 7.33 kWh.
   - *Kullan─▒c─▒ Ge├ğmi┼şine Dayal─▒ Medyan:* `BeyanGecmisHibrit_NoktaRef` modelidir. Kullan─▒c─▒n─▒n ge├ğmi┼şi varsa ge├ğmi┼ş medyan─▒n─▒, yoksa ilk beyan─▒n─▒ kullan─▒r. MAE S├╝re: 120.62 dk, MAE Enerji: 4.46 kWh. Nokta tahmini oldu─şundan quantile (pinball/kapsam) metrikleri ├╝retmez, nicelik ┼şampiyonlu─şu yar─▒┼ş─▒na girmez.
   - *Global Quantile Tahmini:* `GlobalEmpirikBaseline` modelinin ampirik $q_{20}, q_{50}, q_{80}$ sabitleridir. Pinball S├╝re: 67.16 dk, Pinball Enerji: 3.07 kWh.
   - *Linear Quantile Modeli:* `QuantileRegressor(alpha=0.05, solver="highs")` modelidir. MAE S├╝re: 104.82 dk, Pinball: 44.15 dk; MAE Enerji: 4.13 kWh, Pinball: 1.67 kWh.
   - *├û─şrenilmi┼ş Model (Gradient Boosting ┼Şampiyon):* `GradientBoostingQuantileModel(n_estimators=60)`. MAE S├╝re: 88.66 dk, Pinball: 36.89 dk; MAE Enerji: 3.49 kWh, Pinball: 1.40 kWh.
   - *Metodolojik De─şerlendirme:* T├╝m bu 5 y├Ântem tamamen ayn─▒ 5.315 do─şrulama oturumu ve s─▒z─▒nt─▒s─▒z ├Âzellik matrisi (`strict_shift=True`) ├╝zerinde e┼şle┼ştirilmi┼ştir. Say─▒sal metrikler tam ve tutarl─▒d─▒r; ek uydurma metrik veya farkl─▒ ├Ârneklem kullan─▒lmam─▒┼şt─▒r.
3. **LightGBM / CatBoost Durumu:** Ortamda `lightgbm` ve `catboost` y├╝kl├╝ olmad─▒─ş─▒ndan, mod├╝l├╝n esnek adapt├Âr├╝ bu modelleri zarif├ğe atlam─▒┼ş ve Scikit-learn modelleri tam kapasiteyle ├ğal─▒┼şt─▒r─▒lm─▒┼şt─▒r.
4. **Kesi┼şim Oranlar─▒:** Ham gradient boosting modellerinde %1ÔÇô%3 oran─▒nda g├Âr├╝len quantile crossing durumlar─▒ monotonla┼şt─▒rma fonksiyonu ile ├ğ├Âz├╝lm├╝┼şt├╝r; MPC'ye aktar─▒lan nihai diziler kesinlikle monoton artand─▒r.
5. **Holdout K─▒s─▒t─▒ ve 2020 Verisi:** 2020 verisi (OcakÔÇô┼Şubat 2020) daha ├Ânce incelenmi┼ş ve de─şerlendirilmi┼ş bir holdout k├╝mesidir. Bu nedenle gelecekteki model se├ğimi veya hiperparametre optimizasyonu i├ğin **dokunulmam─▒┼ş test seti olarak adland─▒r─▒lamaz ve bu ama├ğla kullan─▒lamaz**.
6. **Canl─▒ Web Servisi ve Ampirik Beyan Oranlar─▒ Ayr─▒m─▒:** Canl─▒ web servisi (`sarjdenge/web_servis.py`), 2019 H1 e─şitim k├╝mesinden (7.808 oturum) ├Â─şrenilen ampirik beyan oran─▒ kuantillerini (`config/beyan_oranlari.json`) baseline olarak kullanmaktad─▒r. Bu raporda k─▒yaslanan GradientBoosting ve QuantileRegressor modelleri ├ğevrimd─▒┼ş─▒ model se├ğim hatt─▒nda yer almakta olup canl─▒ serviste do─şrudan model serile┼ştirmesi yap─▒lmamaktad─▒r.
7. **2019 H1 Veri Say─▒lar─▒ Mutabakat─▒:** `acn_20181231_20190630.csv` dosyas─▒ 14.372 ham veri sat─▒r─▒ (1 ba┼şl─▒k ile 14.373 sat─▒r) i├ğermektedir. Fiziksel hijyen filtreleri sonras─▒ 14.219 temiz oturum kalmakta, beyan filtresiyle 13.123 ge├ğerli oturuma (7.808 e─şitim + 5.315 do─şrulama) ula┼ş─▒lmaktad─▒r. Eski d├Âk├╝mlerdeki 14.219 say─▒s─▒ ham sat─▒r say─▒s─▒ de─şil, fiziksel temiz oturum say─▒s─▒d─▒r.
