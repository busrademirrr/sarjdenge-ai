# ŞarjDenge AI — Model Karşılaştırma ve Doğrulama Raporu (İş Paketi C)

Bu rapor, ŞarjDenge AI projesi kapsamında elektrikli araç şarj oturumlarının süre (`sure_dk`) ve teslim edilen enerji (`kWhDelivered`) ihtiyaçlarını tahmin etmek amacıyla geliştirilen quantile modellerinin (`sarjdenge/modeller.py`) kesin kronolojik doğrulama sonuçlarını, objektif model seçim skorlarını ve Temmuz–Aralık 2019 dönemler arası doğrulama bulgularını belgeler.

---

## 1. Metodolojik Çerçeve ve Ön Kayıt Kısıtları

1. **Bağımsız Hedefler:** Süre ve Enerji modelleri farklı fiziksel birimlere (dakika vs. kWh) sahip olduğundan iki hedef asla tek bir skorda toplanmamış; her hedef için ayrı bir şampiyon model seçilmiştir.
2. **Sızıntısız Özellik Matrisi ($X$):** Özellikler yalnızca `veri_hijyeni.ozellikler(strict_shift=True)` ile üretilmiştir. Sürücünün geçmiş özellikleri ($gecmis\_sure$, $gecmis\_kwh$) hesaplanırken yalnızca $disconnectTime \le connectionTime_{\text{mevcut}}$ olan tamamlanmış oturumlar dahil edilmiş, henüz bitmemiş oturumlardan hedef sızıntısı kesinlikle engellenmiştir.
3. **Bağlantı Anı Beyan Güvencesi:** Kullanıcı beyan özelliklerinde sonradan güncellenmiş değerler asla kullanılmamış; yalnızca bağlantı anında bilinen ilk değerler (`requestedDeparture_ilk`, `kWhRequested_ilk`, `minutesAvailable_ilk`) kullanılmıştır.
4. **Kesin Kronolojik Gün Sınırı:** Ocak–Haziran 2019 verisi yerel gün dönümünde (Los Angeles 00:00:00) kronolojik olarak ikiye bölünmüştür:
   - **Eğitim Kümesi (Train - %60 gün):** 7.808 oturum.
   - **Doğrulama Kümesi (Validation - %40 gün):** 5.315 oturum.
   - $\max(connectionTime_{\text{egit}}) < \min(connectionTime_{\text{val}})$; zaman çakışması 0'dır.
5. **Dönem Sınıflandırması:** Temmuz–Aralık 2019 dönemi daha önce incelendiği için **"dokunulmamış holdout test seti" olarak adlandırılmamıştır**; modelin ardışık farklı bir zaman dilimindeki mevsimsel tutarlılığını test eden bir **"dönemler arası doğrulama (out-of-period re-validation)"** olarak işletilmiştir. Gerçek dokunulmamış test verisi olan 2020 dönemi indirilmemiş ve kullanılmamıştır.

---

## 2. Sabitlenmiş Model Seçim Skoru ($MSS$) Formülasyonu

Model Seçim Skoru (MSS), keyfî değerlendirmeleri engellemek amacıyla deneyler çalıştırılmadan önce yazılı olarak kilitlenmiştir:

1. **Eğitim Ölçek Parametresi ($s_{\text{egit}}$):** Yalnızca eğitim kümesi hedef dağılımından ($y_{\text{egit}}$) hesaplanır:
   $$s_{\text{egit}} = \max\left(\text{IQR}(y_{\text{egit}}), \sigma(y_{\text{egit}}), 1.0\right)$$
   - Süre hedefi için: $s_{\text{egit}}^{\text{sure}} = 336.71 \text{ dk}$
   - Enerji hedefi için: $s_{\text{egit}}^{\text{kwh}} = 11.13 \text{ kWh}$
2. **Normalize Pinball Loss:** $\tilde{\mathcal{L}}_q = \frac{\mathcal{L}_q}{s_{\text{egit}}}$ (Boyutsuz kayıp).
3. **Kapsam Hatası Cezası:** $\mathcal{E}_{\text{kapsam}} = |Coverage(q_{20}) - 0.20| + |Coverage(q_{80}) - 0.80|$.
4. **Birleşik Seçim Skoru:**
   $$MSS = \frac{1}{3}\left(\tilde{\mathcal{L}}_{q20} + \tilde{\mathcal{L}}_{q50} + \tilde{\mathcal{L}}_{q80}\right) + 1.0 \cdot \mathcal{E}_{\text{kapsam}}$$
   *Kural:* MSS skoru, optimizasyonun ve MPC'nin fiilen kullanacağı **düzeltilmiş (monotonlaştırılmış) tahminler** üzerinden hesaplanır.

---

## 3. Ocak–Haziran 2019 Doğrulama Kümesi Karşılaştırma Tabloları

### A. Süre Modelleri Karşılaştırması ($N_{\text{val}} = 5.315$ Oturum)

| Model Adı | Ham Pinball (dk) | Düzeltilmiş Pinball (dk) | Kapsam $q_{20}$ (Hedef: %20) | Kapsam $q_{80}$ (Hedef: %80) | Kapsam Hatası | MAE $q_{50}$ (dk) | Quantile Crossing | Normalize Pinball | Model Seçim Skoru ($MSS$) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **GlobalEmpirikBaseline** | 67.16 | 67.16 | %21.11 | %81.13 | 0.0224 | 176.96 | %0.00 (0) | 0.1995 | **0.2219** |
| *BeyanGecmisHibrit (Nokta Ref)* | - | - | - | - | - | 120.62 | - | - | *Yarış Dışı* |
| **QuantileRegressor** | 44.15 | 44.15 | %19.68 | %80.75 | 0.0107 | 104.82 | %0.43 (23) | 0.1311 | **0.1418** |
| **HistGradientBoosting** | 36.15 | 36.10 | %21.52 | %78.10 | 0.0342 | 86.96 | %3.46 (184) | 0.1072 | **0.1415** |
| **GradientBoosting** | 36.94 | 36.93 | **%20.21** | **%79.72** | **0.0049** | 88.67 | %0.87 (46) | 0.1097 | **0.1146** 🏆 |

> **Süre Şampiyonu Seçimi:** **`GradientBoosting`**
> HistGradientBoosting Pinball kaybında 36.10 dk ile çok hafif daha düşük olsa da, `GradientBoosting` modeli neredeyse kusursuz bir ampirik kapsam kalibrasyonu sergilemiştir (q20: %20.21, q80: %79.72, toplam kapsam hatası yalnızca 0.0049). Ayrıca quantile crossing oranı %0.87 ile oldukça düşüktür. Formülle kilitlenen objektif seçim kuralı uyarınca **GradientBoosting** Şampiyon Süre Modeli seçilmiştir.

---

### B. Enerji Modelleri Karşılaştırması ($N_{\text{val}} = 5.315$ Oturum)

| Model Adı | Ham Pinball (kWh) | Düzeltilmiş Pinball (kWh) | Kapsam $q_{20}$ (Hedef: %20) | Kapsam $q_{80}$ (Hedef: %80) | Kapsam Hatası | MAE $q_{50}$ (kWh) | Quantile Crossing | Normalize Pinball | Model Seçim Skoru ($MSS$) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **GlobalEmpirikBaseline** | 3.07 | 3.07 | %21.30 | %82.82 | 0.0412 | 7.33 | %0.00 (0) | 0.2754 | **0.3166** |
| *BeyanGecmisHibrit (Nokta Ref)* | - | - | - | - | - | 4.46 | - | - | *Yarış Dışı* |
| **QuantileRegressor** | 1.67 | 1.67 | %20.34 | %80.81 | 0.0115 | 4.13 | %1.71 (91) | 0.1501 | **0.1616** |
| **HistGradientBoosting** | 1.34 | 1.34 | %24.16 | %79.21 | 0.0495 | 3.35 | %4.82 (256) | 0.1206 | **0.1700** |
| **GradientBoosting** | 1.40 | 1.40 | **%21.62** | **%81.34** | **0.0295** | 3.49 | %2.46 (131) | 0.1254 | **0.1549** 🏆 |

> **Enerji Şampiyonu Seçimi:** **`GradientBoosting`**
> Benzer şekilde, HGB ham Pinball kaybında 1.34 kWh verse de $q_{20}$ kapsamı %24.16'ya saparak ceza puanı almıştır. `GradientBoosting` hem güçlü bir Pinball kaybı (1.40 kWh vs. Global Baseline 3.07 kWh) hem de dengeli kapsam (%21.62 ve %81.34) sağlayarak en düşük MSS puanını (**0.1549**) almış ve Şampiyon Enerji Modeli seçilmiştir.

---

## 4. Temmuz–Aralık 2019 Dönemler Arası Doğrulama (Out-of-Period Re-validation)

Önceden sabitlenen protokole göre:
- Şampiyon modellerin mimari ve hiperparametreleri dondurulmuştur.
- Modeller tüm Ocak–Haziran 2019 verisi (%100 - 13.123 oturum) üzerinde yeniden eğitilmiş ve Temmuz–Aralık 2019 (12.298 geçerli beyanlı oturum) dönemine sıfır müdahale ile uygulanmıştır.

| Hedef | Şampiyon Model | Ortalama Pinball | Normalize Pinball | Kapsam $q_{20}$ | Kapsam $q_{80}$ | Kapsam Hatası | MAE $q_{50}$ | Quantile Crossing | Dönemler Arası $MSS$ |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Süre** | `GradientBoosting` | **36.20 dk** | 0.1072 | %22.74 | %80.09 | 0.0283 | 87.27 dk | %0.51 (63) | **0.1355** |
| **Enerji** | `GradientBoosting` | **1.47 kWh** | 0.1340 | %20.80 | %77.98 | 0.0282 | 3.68 kWh | %2.97 (365) | **0.1622** |

> **Dönemler Arası Genelleşme Yorumu:**
> Ocak–Haziran doğrulamasında elde edilen MSS skorları (Süre: 0.1146, Enerji: 0.1549) ile Temmuz–Aralık skorları (Süre: 0.1355, Enerji: 0.1622) birbirine son derece yakındır. Modeller mevsim geçişine ve farklı zaman dilimine rağmen aşırı öğrenme (overfitting) sergilememiş, tahmin kalitesini ve kapsam kalibrasyonunu korumuştur.

---

## 5. Çekirdek Simülatör (`sim.py`) ile Entegrasyon

[`sarjdenge/modeller.py`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/sarjdenge/modeller.py) modülü `tahminleri_ekle(df_test, sure_modeli, enerji_modeli)` fonksiyonunu sunmaktadır:
- Test kümesindeki her oturum için sızıntısız özellik matrisini çıkarır.
- Şampiyon modellerden $q_{20}, q_{50}, q_{80}$ tahminlerini alır ve monotonlaştırır.
- Dönen DataFrame'e `tahmin_sure_q20`, `tahmin_sure_q50`, `tahmin_sure_q80`, `tahmin_kwh_q20`, `tahmin_kwh_q50`, `tahmin_kwh_q80` sütunlarını ekler.
- Bu çıktı doğrudan dondurulmuş çekirdek simülatöre (`sim.simule(df, yontem=...)`) verilebilir durumdadır; hiçbir çekirdek dosyada değişiklik gerektirmez.

---

## 6. Bilinen Sınırlamalar

1. **LightGBM / CatBoost Durumu:** Ortamda `lightgbm` ve `catboost` yüklü olmadığından, modülün esnek adaptörü bu modelleri zarifçe atlamış ve Scikit-learn modelleri tam kapasiteyle çalıştırılmıştır.
2. **Kesişim Oranları:** Ham gradient boosting modellerinde %1–%3 oranında görülen quantile crossing durumları monotonlaştırma fonksiyonu ile çözülmüştür; MPC'ye aktarılan nihai diziler kesinlikle monoton artandır.
3. **Holdout Kısıtı:** 2020 verisi `ONKAYIT_2.md` ilkeleri uyarınca bu aşamada hiçbir şekilde kullanılmamış olup, İş Paketi D'deki simülasyon deneyleri tamamlanana kadar dokunulmamış kalacaktır.
