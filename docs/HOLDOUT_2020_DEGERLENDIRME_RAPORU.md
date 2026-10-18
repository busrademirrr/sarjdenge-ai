# ŞarjDenge AI — 2020 ACN Holdout Nihai Değerlendirme ve Hipotez Testi Raporu

**Tarih:** 18 Ekim 2026  
**Protokol:** Ön Kayıt 2 ([`ONKAYIT_2.md`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/ONKAYIT_2.md)) • Seçenek A (2019 Tam Yeniden Eğitim)  
**Holdout Verisi:** [`data/holdout_2020_01_02/acn_holdout_20200101_20200301_ham.csv`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/data/holdout_2020_01_02/acn_holdout_20200101_20200301_ham.csv) (1 Ocak – 1 Mart 2020)  
**Değerlendirme Kapsamı:**  
- **Birincil Değerlendirme (Ön Kayıtlı):** Tüm uygun günler (`min_arac_gunluk=1`, simülatör alt sınırı $\ge 4$ araç sağlayan **108 gün-saha, 4.043 oturum, %99.3 kapsam**)  
- **Duyarlılık Analizi (Ek Filtre):** $N \ge 8$ araç/gün filtresi uygulanan **89 gün-saha, 3.940 oturum, %96.8 kapsam**  
**Tohum ve İterasyon:** `tohum=42`, `n_boot=2000`, `kapasiteler=(0.5, 0.7, 0.9)`  

---

## 1. Yönetici Özeti ve Ön Kayıt Hipotez Kararı

```mermaid
flowchart TD
    A["2020 ACN Holdout (4.072 Temiz Beyanlı Oturum)"] --> B["BİRİNCİL DEĞERLENDİRME (108 Gün-Saha / 4.043 Oturum / %99.3)"]
    A --> C["DUYARLILIK ANALİZİ (89 Gün-Saha / 3.940 Oturum / N >= 8)"]
    
    B --> B1["f=0.5: Δ = -0.65 yp (95% GA: -1.48, +0.12)"]
    B --> B2["f=0.7: Δ = -0.82 yp (95% GA: -1.55, -0.09)"]
    B --> B3["f=0.9: Δ = +0.09 yp (95% GA: -0.33, +0.51)"]
    
    C --> C1["f=0.5: Δ = -0.79 yp (95% GA: -1.62, +0.05)"]
    C --> C2["f=0.7: Δ = -0.48 yp (95% GA: -1.13, +0.20)"]
    C --> C3["f=0.9: Δ = +0.11 yp (95% GA: -0.41, +0.59)"]
    
    B1 --> D["Ön Kayıt Ana Hipotezi (Δ >= +2.00 yp & GA Alt > 0): DESTEKLENMEDİ"]
    C1 --> D
```

| Kriter / Ön Kayıt Şartı | Hedef Eşik | Birincil Değerlendirme (Tüm Uygun Günler - 4.043 Oturum) | Duyarlılık Analizi ($N \ge 8$ Günler - 3.940 Oturum) | Nihai Karar |
| :--- | :---: | :---: | :---: | :---: |
| **Ana Hipotez Farkı ($f=0.5$)** | $\ge +2.00$ yp | **-0.65 yp** (GA: $[-1.48, +0.12]$) | **-0.79 yp** (GA: $[-1.62, +0.05]$) | ❌ **DESTEKLENMEDİ** |
| **Ana Hipotez Farkı ($f=0.7$)** | $\ge +2.00$ yp | **-0.82 yp** (GA: $[-1.55, -0.09]$) | **-0.48 yp** (GA: $[-1.13, +0.20]$) | ❌ **DESTEKLENMEDİ** |
| **Ana Hipotez Farkı ($f=0.9$)** | $\ge +2.00$ yp | **+0.09 yp** (GA: $[-0.33, +0.51]$) | **+0.11 yp** (GA: $[-0.41, +0.59]$) | ❌ **DESTEKLENMEDİ** |
| **Bootstrap %95 GA Alt Sınırı** | $> 0.0$ | $f=0.5$: -1.48 • $f=0.7$: -1.55 • $f=0.9$: -0.33 | $f=0.5$: -1.62 • $f=0.7$: -1.13 • $f=0.9$: -0.41 | ❌ **DESTEKLENMEDİ** |
| **Enerji $q_{80}$ Kapsam Toleransı** | $\%80 \pm 3$ | **%82.39** ($[77\%, 83\%]$ içinde) | **%82.39** ($[77\%, 83\%]$ içinde) |  **Tolerans İçi** |
| **Süre $q_{20}$ Kapsam Kalibrasyonu** | $\%20$ hedef | **%19.99** | **%19.99** |  **Hedefe Uyumlu** |
| **Kapasite İhlali** | $0$ | **0 İhlal** (2.916 simülasyon koşusu) | **0 İhlal** (2.403 simülasyon koşusu) |  **Kısıt Korundu** |

> [!IMPORTANT]
> **DÜRÜST BİLİMSEL SONUÇ BİLDİRİMİ:**  
> Önceden kaydedilen **ana hipotez (`mpc_tahmin_guvenli - mpc_beyan >= +0.02` ve GA alt ucu > 0), hem birincil değerlendirmede (tüm uygun günler) hem de duyarlılık analizinde ($N \ge 8$) KESİN OLARAK DESTEKLENMEMİŞTİR.**  
> Makine öğrenmesi modelleri kullanıcı beyanına kıyasla süre mutlak hatasını **%45.7**, enerji mutlak hatasını **%69.7** oranında düşürmüş ve quantile kalibrasyonu sağlamış olsa da; bu doğruluk artışı saf enerji-LP tabanlı MPC mimarisinde zamanında hedef tamamlama oranına pozitif katkı yapmamış, dar kapasitede ($f=0.5$) beyanın **0.65 yüzde puanı gerisinde** kalmıştır ($f=0.7$'de ise beyan, tahmine karşı istatistiksel olarak anlamlı biçimde **0.82 yüzde puanı daha başarılıdır**; %95 GA $[-1.55, -0.09]$).

---

## 2. Örneklem Kapsamı ve Simülasyon Uygunluk Analizi

2020 taze test veri setinde (1 Ocak – 1 Mart 2020) temiz beyanlı toplam **4.072 oturum**, 61 takvim gününde ve 122 `(siteID, gun)` çiftinde yer almaktadır:

| Küme / Kısıt | Gün-Saha Çifti | Takvim Günü | Oturum Sayısı | Kapsam Oranı | Açıklama |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Toplam Temiz Beyanlı Test Oturumu** | 122 | 61 | **4,072** | %100.0 | Tüm geçerli test evreni |
| **BİRİNCİL DEĞERLENDİRME (Tüm Uygun Günler)** | **108** | **59** | **4,043** | **%99.3** | Simülatör alt sınırını ($\ge 4$ araç) sağlayan tüm günler |
| *— Simülasyon Dışı Kalan Günler* | 14 | 14 | 29 | %0.7 | Hafta sonu / tatil günlerinde sahada 1, 2 veya 3 araç bulunan günler |
| **DUYARLILIK ANALİZİ ($N \ge 8$ Günler)** | **89** | **48** | **3,940** | **%96.8** | Günlük yoğun otopark filtresi |

### Simülasyon Dışı Kalan 29 Oturumun Nedeni (Teknik Sınır Şeffaflığı):
Deney koşucusunda ([`sarjdenge/deney_v2.py`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/sarjdenge/deney_v2.py#L104)), aynı anda sahada bağlı araç sayısı 4'ten az olduğunda (`gec.sum() < 4`) fonksiyon `return []` dönmektedir (1-3 aracın bulunduğu hafta sonu nöbetçi şarjlarında trafo kapasitesi hiçbir zaman darboğaza girmez). Bu koşul `sim.py` içinde değil, deney koşucusu `deney_v2.py` içindedir. Bu nedenle 14 gün-saha çiftindeki 29 oturum simülasyon dışı kalmış; teknik olarak çalıştırılabilen geriye kalan **4.043 oturumun tamamı (%99.3)** birincil değerlendirmeye dahil edilmiştir.

---

## 3. Birincil Değerlendirme Sonuçları (Tüm Uygun Günler - 4.043 Oturum, 108 Gün-Saha)

### A. Yöntem Performans Tablosu

| Kapasite ($f$) | Yöntem | Tür / Kaynak | Başarı Oranı (`ok`) | Teslim Oranı | Erken Ayrılan Başarı | En Kötü %10 (`p10`) | Kapasite İhlali |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **0.5** | **`edf_beyan`** | Kural / Beyan | **%86.44** | %93.64 | %71.48 | 0.881 | 0 |
| 0.5 | **`edf_tahmin_guvenli`** | Kural / Tahmin | **%86.00** | %93.63 | **%73.90** | 0.867 | 0 |
| 0.5 | `llf_beyan` | Kural / Beyan | %85.78 | %93.50 | %70.48 | 0.860 | 0 |
| 0.5 | `llf_tahmin_guvenli` | Kural / Tahmin | %85.32 | %93.66 | %72.07 | **0.873** | 0 |
| 0.5 | **`mpc_beyan` (REF)** | Optimizasyon / Beyan | **%85.28** | %93.29 | %71.06 | 0.858 | 0 |
| 0.5 | `mpc_hibrit_asimetrik` | Keşifsel / Hibrit | %84.72 | %93.16 | %72.26 | 0.851 | 0 |
| 0.5 | **`mpc_tahmin_guvenli` (ANA)**| Optimizasyon / Tahmin | **%84.63** | %93.19 | %71.77 | 0.846 | 0 |
| 0.5 | `mpc_tahmin_ortanca` | Optimizasyon / Tahmin | %84.03 | %92.96 | %70.53 | 0.845 | 0 |
| 0.5 | `fcfs_beyan` | Sıralı / Beyan | %83.42 | %92.78 | %70.49 | 0.795 | 0 |
| | | | | | | | |
| **0.7** | **`edf_beyan`** | Kural / Beyan | **%90.62** | %97.08 | %79.30 | 0.953 | 0 |
| 0.7 | `llf_tahmin_guvenli` | Kural / Tahmin | %90.58 | %97.04 | %79.08 | 0.944 | 0 |
| 0.7 | `llf_beyan` | Kural / Beyan | %90.55 | %96.95 | %78.89 | 0.944 | 0 |
| 0.7 | **`mpc_beyan` (REF)** | Optimizasyon / Beyan | **%90.26** | %96.69 | %79.03 | 0.936 | 0 |
| 0.7 | `edf_tahmin_guvenli` | Kural / Tahmin | %90.15 | %96.95 | **%79.80** | 0.941 | 0 |
| 0.7 | `mpc_hibrit_asimetrik` | Keşifsel / Hibrit | %89.70 | %96.78 | %78.82 | 0.933 | 0 |
| 0.7 | **`mpc_tahmin_guvenli` (ANA)**| Optimizasyon / Tahmin | **%89.44** | **%96.85** | %78.39 | 0.932 | 0 |
| 0.7 | `fcfs_beyan` | Sıralı / Beyan | %88.47 | %96.64 | %77.90 | 0.918 | 0 |
| | | | | | | | |
| **0.9** | **`edf_tahmin_guvenli`** | Kural / Tahmin | **%93.34** | %98.71 | **%84.49** | **0.979** | 0 |
| 0.9 | `llf_tahmin_guvenli` | Kural / Tahmin | %93.30 | **%98.74** | %84.31 | 0.978 | 0 |
| 0.9 | **`mpc_tahmin_guvenli` (ANA)**| Optimizasyon / Tahmin | **%93.19** | %98.68 | %84.10 | 0.977 | 0 |
| 0.9 | `fcfs_beyan` | Sıralı / Beyan | %93.14 | %98.73 | %84.37 | 0.978 | 0 |
| 0.9 | `llf_beyan` | Kural / Beyan | %93.14 | %98.61 | %83.94 | 0.975 | 0 |
| 0.9 | **`mpc_beyan` (REF)** | Optimizasyon / Beyan | **%93.10** | %98.59 | %83.70 | 0.975 | 0 |
| 0.9 | `edf_beyan` | Kural / Beyan | %93.09 | %98.68 | %83.74 | 0.977 | 0 |
| 0.9 | `mpc_hibrit_asimetrik` | Keşifsel / Hibrit | %92.81 | %98.56 | %83.49 | 0.975 | 0 |

### B. Eşleştirilmiş Bootstrap Hipotez Testi Sonuçları ($B=2000$)

| Kapasite ($f$) | Karşılaştırma | Tür | Ortalama Fark ($\Delta$) | %95 Güven Aralığı Alt | %95 Güven Aralığı Üst | Eşik Karşılandı mı? | Karar |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **0.5** | **`mpc_tahmin_guvenli - mpc_beyan`** | **Ana Hipotez** | **-0.65 yp** | **-1.48 yp** | **+0.12 yp** | ❌ Hayır | **DESTEKLENMEDİ** |
| 0.5 | `mpc_tahmin_ortanca - mpc_beyan` | İkincil Tahmin | -1.25 yp | -2.55 yp | -0.18 yp | ❌ Hayır | Anlamlı Negatif |
| 0.5 | `edf_tahmin_guvenli - edf_beyan` | EDF Karşılaştırması | -0.43 yp | -1.56 yp | +0.67 yp | ❌ Hayır | Anlamsız |
| 0.5 | `llf_tahmin_guvenli - llf_beyan` | LLF Karşılaştırması | -0.45 yp | -1.01 yp | +0.10 yp | ❌ Hayır | Anlamsız |
| 0.5 | `mpc_hibrit_asimetrik - mpc_beyan` | Keşifsel A1 vs Beyan | -0.56 yp | -1.71 yp | +0.43 yp | ❌ Hayır | Anlamsız |
| 0.5 | `mpc_hibrit_asimetrik - mpc_tahmin_guvenli` | Keşifsel A1 vs Güvenli | +0.09 yp | -0.92 yp | +1.06 yp | ❌ Hayır | Anlamsız |
| | | | | | | | |
| **0.7** | **`mpc_tahmin_guvenli - mpc_beyan`** | **Ana Hipotez** | **-0.82 yp** | **-1.55 yp** | **-0.09 yp** | ❌ Hayır | **DESTEKLENMEDİ (Beyan Üstün)** |
| 0.7 | `mpc_tahmin_ortanca - mpc_beyan` | İkincil Tahmin | -1.69 yp | -2.96 yp | -0.63 yp | ❌ Hayır | Beyan Üstün |
| 0.7 | `edf_tahmin_guvenli - edf_beyan` | EDF Karşılaştırması | -0.47 yp | -1.51 yp | +0.55 yp | ❌ Hayır | Anlamsız |
| 0.7 | `llf_tahmin_guvenli - llf_beyan` | LLF Karşılaştırması | +0.04 yp | -0.46 yp | +0.60 yp | ❌ Hayır | Anlamsız |
| 0.7 | `mpc_hibrit_asimetrik - mpc_beyan` | Keşifsel A1 vs Beyan | -0.55 yp | -1.26 yp | +0.07 yp | ❌ Hayır | Anlamsız |
| | | | | | | | |
| **0.9** | **`mpc_tahmin_guvenli - mpc_beyan`** | **Ana Hipotez** | **+0.09 yp** | **-0.33 yp** | **+0.51 yp** | ❌ Hayır | **DESTEKLENMEDİ** |
| 0.9 | `mpc_tahmin_ortanca - mpc_beyan` | İkincil Tahmin | -0.16 yp | -0.80 yp | +0.48 yp | ❌ Hayır | Anlamsız |
| 0.9 | `edf_tahmin_guvenli - edf_beyan` | EDF Karşılaştırması | +0.26 yp | -0.29 yp | +0.98 yp | ❌ Hayır | Anlamsız |
| 0.9 | `llf_tahmin_guvenli - llf_beyan` | LLF Karşılaştırması | +0.16 yp | -0.18 yp | +0.53 yp | ❌ Hayır | Anlamsız |

---

## 4. Ek Bulguların İstatistiksel Değerlendirmesi

### A. Erken Ayrılan Oturumlarda Gözlenen Fark Analizi (Keşifsel Alt Grup Bulgusu)
Kullanıcıların beyan ettikleri süreden en az 15 dakika önce ayrıldığı oturumlar alt kümesinde (`erken_ok`), `edf_tahmin_guvenli` ile `edf_beyan` yöntemlerinin başarı farkı eşleştirilmiş bootstrap ($B=2000$, tohum=42) ile incelenmiştir:

| Kapasite ($f$) | Karşılaştırma | Gözlenen Fark ($\Delta$) | %95 Güven Aralığı Alt | %95 Güven Aralığı Üst | Gün Sayısı | İstatistiksel Değerlendirme |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **0.5** | `edf_tahmin_guvenli - edf_beyan (erken_ok)` | **+2.42 yp** | **+0.40 yp** | **+4.44 yp** | 107 gün | Keşifsel Üstünlük ($p<0.05$) |
| **0.7** | `edf_tahmin_guvenli - edf_beyan (erken_ok)` | **+0.50 yp** | -1.00 yp | +2.13 yp | 107 gün | **Gözlenen Fark** (Anlamsız, sıfırı içerir) |
| **0.9** | `edf_tahmin_guvenli - edf_beyan (erken_ok)` | **+0.76 yp** | -0.17 yp | +1.89 yp | 107 gün | **Gözlenen Fark** (Anlamsız, sıfırı içerir) |

> [!NOTE]
> **Bilimsel ve Metodolojik Sınırlar:**  
> $f=0.5$ dar kapasite koşulunda erken ayrılan araçlarda tahmin modeli lehine gözlenen fark (+2.42 yp, %95 GA: $[+0.40, +4.44]$ yp), **sonuç gerçekleştikten sonra (post-hoc) seçilmiş bir alt grupta ve yalnızca tek bir sıkı kapasite koşulunda tespit edilmiş keşifsel bir bulgudur**. $f=0.7$ ve $f=0.9$ kapasitelerinde farklar sırasıyla $+0.50$ yp ve $+0.76$ yp düzeyinde kalmış ve güven aralıkları sıfırı içerdiği için istatistiksel üstünlük iddia edilemez. Ayrıca bu alt grup gözlemi, tüm kullanıcıları kapsayan ön kayıtlı ana hipotezin desteklenmediği gerçeğini değiştirmemektedir.

### B. Keşifsel Hibrit A1 Değerlendirmesi
- `mpc_hibrit_asimetrik` yöntemi birincil değerlendirmede $f=0.5$'te `mpc_tahmin_guvenli`ye göre $+0.09$ yp (GA: $[-0.92, +1.06]$), duyarlılık analizinde ise $+0.84$ yp (GA: $[+0.03, +1.66]$) fark göstermiştir.
- Ancak `mpc_hibrit_asimetrik`, tüm kapasite seviyelerinde beyana dayalı `mpc_beyan` yönteminin gerisinde kalmıştır ($f=0.5$'te %84.72 vs %85.28; $f=0.7$'de %89.70 vs %90.26; $f=0.9$'da %92.81 vs %93.10).
- Ön kayıt kuralı gereğince bu analiz **kesinlikle keşifsel bir ikincil bulgu** olarak değerlendirilmiş; ana hipotez yerine ikame edilmemiştir.

---

## 5. Duyarlılık Analizi Karşılaştırması ($N \ge 8$ Günler)

Önceden koşturulan 3.940 oturumluk analiz [`data/holdout_2020_01_02/deney_tablo_holdout_2020_duyarlilik_n8.csv`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/data/holdout_2020_01_02/deney_tablo_holdout_2020_duyarlilik_n8.csv) dosyasında tam şeffaflıkla saklanmaktadır. İki analiz arasındaki karşılaştırma:

| Kapasite | Metrik | Birincil Değerlendirme (Tüm Uygun Günler: 4.043 Oturum, 108 Gün-Saha) | Duyarlılık Analizi ($N \ge 8$: 3.940 Oturum, 89 Gün-Saha) | Karşılaştırma Kararı |
| :---: | :--- | :---: | :---: | :--- |
| **0.5** | `mpc_tahmin_guvenli` Başarı | %84.63 | %87.56 | Benzer Eğilim |
| 0.5 | `mpc_beyan` Başarı | %85.28 | %88.35 | Benzer Eğilim |
| 0.5 | **Ana Hipotez Farkı ($\Delta$)** | **-0.65 yp** ($[-1.48, +0.12]$) | **-0.79 yp** ($[-1.62, +0.05]$) | **İkisinde de Desteklenmedi** |
| **0.7** | **Ana Hipotez Farkı ($\Delta$)** | **-0.82 yp** ($[-1.55, -0.09]$) | **-0.48 yp** ($[-1.13, +0.20]$) | **İkisinde de Desteklenmedi** |
| **0.9** | **Ana Hipotez Farkı ($\Delta$)** | **+0.09 yp** ($[-0.33, +0.51]$) | **+0.11 yp** ($[-0.41, +0.59]$) | **İkisinde de Desteklenmedi** |

**Sonuç:** `min_arac_gunluk=8` kısıtının kaldırılması hipotez sonucunu değiştirmemiştir; ana hipotez her iki veri kesitinde de reddedilmiştir.

---

## 6. Dosya ve Veri Günlüğü

Aşağıdaki dosyalar `data/holdout_2020_01_02/` altında arşivlenmiştir:
- `deney_gunluk_holdout_2020_birincil.csv`: Birincil değerlendirme günlük sonuçları (2.916 satır).
- `deney_tablo_holdout_2020_birincil.csv`: Birincil yöntem özet tablosu.
- `deney_boot_holdout_2020_birincil.csv`: Birincil bootstrap güven aralıkları ($B=2000$).
- `deney_boot_erken_holdout_2020.csv`: Erken ayrılan oturumlar için bootstrap analiz tablosu.
- `deney_gunluk_holdout_2020_duyarlilik_n8.csv`: $N \ge 8$ duyarlılık günlük sonuçları (arşiv).
- `deney_tablo_holdout_2020_duyarlilik_n8.csv`: $N \ge 8$ duyarlılık yöntem özet tablosu (arşiv).
- `deney_boot_holdout_2020_duyarlilik_n8.csv`: $N \ge 8$ duyarlılık bootstrap tablosu (arşiv).
- `tahmin_metrikleri_holdout_2020.json`: 2020 holdout süre ve enerji tahmin metrikleri.

---

## 7. Hipotez Sonucunun Mekanizma Analizi ve Sınırları

Ön kayıtlı ana hipotezin desteklenmemesi üzerine yapılan incelemeler şu olası mekanizma ve kanıt sınırlarını ortaya koymaktadır:

1. **Olası Mekanizma: Hayalet Kapasite Rezervasyonu Hipotezi:**  
   Muhafazakar tahmin stratejisi ($q_{20}$ ayrılış süresi ve $q_{80}$ enerji talebi), her araca gerçekte gerekenden daha kısa bir süre ve daha yüksek bir enerji ihtiyacı atar. Kapasite sınırının dar olduğu koşullarda ($f=0.5, 0.7$), zamanla azalan ağırlıklı ($w_s = 1 - 0.5 s/H$) doğrusal programlama (LP) bu yapay aciliyeti karşılamak için gücü erken adımlarda agresif biçimde rezerve eder; bu sırada otoparktaki diğer ılımlı araçların gücü kısılır ve trafo tavanına takılarak toplam başarı düşer. Bu açıklama kanıtlanmış bir mutlak olgu değil, **test edilmesi gereken bir çalışma hipotezi** olarak ele alınmalıdır.
2. **2019 Teşhis Deneyi Kanıtları (`sarjdenge/tani.py` ve `tani_sonuclari.csv`):**  
   - 2019 verisi üzerinde yapılan ayrıştırma deneyinde $f=0.5$'te süre tahmini tek başına kullanıldığında (`sure_tahmin_kwh_beyan`) MPC başarısı %91.58'den %90.72'ye (-0.86 yp) düşerken; yalnızca enerji tahmini kullanıldığında (`sure_beyan_kwh_tahmin`) başarı %89.36'ya (-2.22 yp) sert biçimde gerilemiştir. Bu ampirik bulgu, enerji tahmininin (özellikle $q_{80}$ talebinin) ana olumsuz bileşen olduğunu desteklemektedir.
   - Kusursuz bilgi (`oracle`: gerçek ayrılış ve gerçek teslim enerjisi) verildiğinde dahi $f=0.5$'te EDF tavanı +2.16 yp (+2.2 yp), MPC tavanı +2.67 yp (+2.7 yp) ile sınırlı kalmaktadır. Bu durum, hiçbir modelin beyana kıyasla +2.2 ila +2.7 yüzde puanından daha yüksek bir teorik iyileşme sağlayamayacağını göstermektedir.
3. **Kural Tabanlı Algoritmaların Dinamik Üstünlüğü:**  
   EDF ve LLF gibi sezgisel algoritmalar, acil araçları hızla doyurup şebekeden çekerek trafo kapasitesini anında bir sonraki araca devreder. LP tabanlı MPC ise enerjiyi zaman ufkuna yaymaya çalıştığı için dar kapasite altında kural tabanlı yaklaşımların gerisinde kalmıştır. Nitekim tahmin destekli EDF (`edf_tahmin_guvenli`) de $f=0.5$ (%86.00 vs %86.44) ve $f=0.7$'de (%90.15 vs %90.62) beyana dayalı EDF'yi genel başarıda geçememiştir.
4. **İşyeri Otoparkı Esneklik Tamponu (Workplace Parking Slack Buffer):**  
   Caltech ve JPL yerleşkelerinde araçlar ortalama 7–8 saat park halinde kalırken, bataryaların dolması yalnızca 2.5–3 saat sürmektedir. Aradaki 4–5 saatlik bekleme süresi, sürücülerin süre beyanlarındaki yüksek hataları (MAE 156 dk) doğal bir tampon gibi absorbe eder. Bu nedenle yüksek doğruluklu süre kestirimi, esnekliğin bol olduğu kurumsal otoparklarda fazladan bir kapasite artışına dönüşememektedir.

