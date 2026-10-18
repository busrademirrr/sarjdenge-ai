# ŞarjDenge Bağımsız Deney Sonuçları (Temmuz–Aralık 2019)

> **Metrik ve Talep Tanımı:**
> - Bu deneyde referans hedef enerji ($e$), ACN veri tabanındaki tarihi oturumda ACN'nin kendi planlayıcısı tarafından teslim edilmiş olan enerjidir (`kWhDelivered`).
> - Bir oturum, simülasyonda teslim edilen enerji $\ge 0.95 \times e$ olduğunda zamanında hedefe ulaşmış (`ok`) kabul edilir.
> - Dolayısıyla bu oran, sınırsız pil kapasitesinin veya kullanıcı ilk istek listesinin değil; kısıtlı kapasite altında ACN'nin tarihi şarj başarım benchmark'ının yakalanma oranını ifade eder.
> - **Kapasite Kısıtları:** Simülasyonda gözlenen kapasite ihlali yoktur (tüm adımlarda ve yöntemlerde 0).

---

## 1. Tahmin Doğruluğu (Bağımsız Test Oturumları)

| Hedef   | Kaynak          |   SMAPE_% |
|:--------|:----------------|----------:|
| süre    | beyan           |     49.44 |
| süre    | tahmin (medyan) |     25.86 |
| enerji  | beyan           |     56.92 |
| enerji  | tahmin (medyan) |     25.77 |

- Süre $q20$ kapsaması (hedef 0.20): **0.212**
- Enerji $q80$ kapsaması (hedef 0.80): **0.776**
- Beyan gecikmesi (dk): medyan 0.3, p90 1.2; girdisi sonradan değişen oturum oranı: %17.4
- Aday 1 ($kwh = \max(beyan, q50)$): $kwh\_q50 > beyan\_kwh$ olan oturum oranı **%4.0** (ortalama fark: +2.06 kWh). Gerçek talep ile planlayıcının hedefi kesinlikle birbirine karıştırılmamıştır.

---

## 2. Yöntem Başarı Oranları (Kapasite = Günün Kontrolsüz Tepe Gücünün f Katı)

|   f | yontem                 |   gun |    ok |   teslim |   erken_ok |   p10 |   kapasite_ihlali |
|----:|:-----------------------|------:|------:|---------:|-----------:|------:|------------------:|
| 0.5 | edf_beyan              |    59 | 0.879 |    0.937 |      0.699 | 0.886 |                 0 |
| 0.5 | edf_tahmin_dengeli     |    59 | 0.845 |    0.947 |      0.712 | 0.869 |                 0 |
| 0.5 | edf_tahmin_guvenli     |    59 | 0.862 |    0.950 |      0.730 | 0.876 |                 0 |
| 0.5 | fcfs_beyan             |    59 | 0.845 |    0.931 |      0.680 | 0.764 |                 0 |
| 0.5 | llf_beyan              |    59 | 0.859 |    0.950 |      0.673 | 0.845 |                 0 |
| 0.5 | llf_tahmin_guvenli     |    59 | 0.842 |    0.954 |      0.724 | 0.844 |                 0 |
| 0.5 | mpc_beyan              |    59 | 0.857 |    0.948 |      0.665 | 0.848 |                 0 |
| 0.5 | mpc_hibrit_asimetrik   |    59 | 0.863 |    0.946 |      0.711 | 0.857 |                 0 |
| 0.5 | mpc_hibrit_risk_esikli |    59 | 0.858 |    0.946 |      0.701 | 0.856 |                 0 |
| 0.5 | mpc_hibrit_adaptif     |    59 | 0.827 |    0.945 |      0.668 | 0.846 |                 0 |
| 0.5 | mpc_tahmin_guvenli     |    59 | 0.840 |    0.951 |      0.701 | 0.862 |                 0 |
| 0.5 | mpc_tahmin_dengeli     |    59 | 0.818 |    0.944 |      0.669 | 0.836 |                 0 |
| 0.5 | mpc_tahmin_ortanca     |    59 | 0.808 |    0.940 |      0.656 | 0.805 |                 0 |
| 0.7 | edf_beyan              |    59 | 0.916 |    0.978 |      0.784 | 0.961 |                 0 |
| 0.7 | edf_tahmin_dengeli     |    59 | 0.903 |    0.980 |      0.795 | 0.958 |                 0 |
| 0.7 | edf_tahmin_guvenli     |    59 | 0.913 |    0.981 |      0.813 | 0.958 |                 0 |
| 0.7 | fcfs_beyan             |    59 | 0.906 |    0.976 |      0.788 | 0.938 |                 0 |
| 0.7 | llf_beyan              |    59 | 0.920 |    0.982 |      0.802 | 0.953 |                 0 |
| 0.7 | llf_tahmin_guvenli     |    59 | 0.913 |    0.983 |      0.815 | 0.949 |                 0 |
| 0.7 | mpc_beyan              |    59 | 0.922 |    0.983 |      0.798 | 0.962 |                 0 |
| 0.7 | mpc_hibrit_asimetrik   |    59 | 0.921 |    0.983 |      0.803 | 0.958 |                 0 |
| 0.7 | mpc_hibrit_risk_esikli |    59 | 0.919 |    0.983 |      0.797 | 0.960 |                 0 |
| 0.7 | mpc_hibrit_adaptif     |    59 | 0.899 |    0.979 |      0.784 | 0.947 |                 0 |
| 0.7 | mpc_tahmin_guvenli     |    59 | 0.912 |    0.982 |      0.811 | 0.954 |                 0 |
| 0.7 | mpc_tahmin_dengeli     |    59 | 0.898 |    0.979 |      0.786 | 0.942 |                 0 |
| 0.7 | mpc_tahmin_ortanca     |    59 | 0.895 |    0.979 |      0.782 | 0.935 |                 0 |
| 0.9 | edf_beyan              |    59 | 0.934 |    0.989 |      0.831 | 0.977 |                 0 |
| 0.9 | edf_tahmin_dengeli     |    59 | 0.930 |    0.988 |      0.834 | 0.977 |                 0 |
| 0.9 | edf_tahmin_guvenli     |    59 | 0.933 |    0.989 |      0.838 | 0.977 |                 0 |
| 0.9 | fcfs_beyan             |    59 | 0.933 |    0.989 |      0.834 | 0.976 |                 0 |
| 0.9 | llf_beyan              |    59 | 0.935 |    0.990 |      0.835 | 0.977 |                 0 |
| 0.9 | llf_tahmin_guvenli     |    59 | 0.934 |    0.990 |      0.838 | 0.978 |                 0 |
| 0.9 | mpc_beyan              |    59 | 0.935 |    0.990 |      0.831 | 0.978 |                 0 |
| 0.9 | mpc_hibrit_asimetrik   |    59 | 0.937 |    0.990 |      0.837 | 0.979 |                 0 |
| 0.9 | mpc_hibrit_risk_esikli |    59 | 0.936 |    0.990 |      0.835 | 0.980 |                 0 |
| 0.9 | mpc_hibrit_adaptif     |    59 | 0.929 |    0.988 |      0.831 | 0.974 |                 0 |
| 0.9 | mpc_tahmin_guvenli     |    59 | 0.935 |    0.990 |      0.838 | 0.978 |                 0 |
| 0.9 | mpc_tahmin_dengeli     |    59 | 0.931 |    0.989 |      0.834 | 0.975 |                 0 |
| 0.9 | mpc_tahmin_ortanca     |    59 | 0.930 |    0.988 |      0.831 | 0.975 |                 0 |

---

## 3. Önceden Belirlenmiş Ana Başarı Kuralı Değerlendirmesi

- **Önceden Yazılmış Kural:** Ana karşılaştırma `mpc_tahmin_guvenli - mpc_beyan`, fark $\ge +0.02$ (+2 yüzde puan) ve %95 GA alt ucu $> 0$.
- **Sonuç:**
  - $f=0.5$: Fark = **−0.017** (%95 GA: [−0.028, −0.006]) $\rightarrow$ **esik_gecti = False**
  - $f=0.7$: Fark = **−0.010** (%95 GA: [−0.018, −0.002]) $\rightarrow$ **esik_gecti = False**
  - $f=0.9$: Fark = **0.000** (%95 GA: [−0.004, +0.005]) $\rightarrow$ **esik_gecti = False**
- **Değerlendirme:** Önceden yazılmış ana başarı eşiği **karşılanmamıştır.** Ham ML tahminli MPC (`mpc_tahmin_guvenli`), beyan tabanlı MPC'yi genel başarıda geçememiş ve geride kalmıştır.

---

## 4. Eşleştirilmiş Farklar: Genel Hedef Başarısı (`ok`, Bootstrap %95 GA)

|   f | Karşılaştırma                               |   Fark |    Alt |    Üst | Eşik Geçti | Yorum |
|----:|:--------------------------------------------|-------:|-------:|-------:|:-----------|:---|
| 0.5 | `mpc_tahmin_guvenli - mpc_beyan`            | -0.017 | -0.028 | -0.006 | False      | Önceden yazılmış ana hipotez geçmedi |
| 0.5 | `mpc_hibrit_asimetrik - mpc_tahmin_guvenli` | **+0.022** | **+0.014** | **+0.032** | — | Güvenli tahmine göre anlamlı iyileşme (+2.2 puan) |
| 0.5 | `mpc_hibrit_asimetrik - mpc_beyan`          | **+0.005** | **-0.002** | **+0.013** | False      | Beyan tabanlı MPC'ye karşı anlamlı üstünlük yok (GA sıfırı kapsar) |
| 0.5 | `mpc_hibrit_risk_esikli - mpc_beyan`        | +0.001 | -0.006 | +0.008 | False      | Beyan tabanlı MPC ile istatistiksel olarak eşit |
| 0.5 | `mpc_hibrit_adaptif - mpc_beyan`            | -0.030 | -0.040 | -0.021 | False      | Anlamlı derecede geride (−3.0 puan) |
| 0.7 | `mpc_hibrit_asimetrik - mpc_beyan`          | -0.001 | -0.007 | +0.005 | False      | Eşit |
| 0.7 | `mpc_hibrit_asimetrik - mpc_tahmin_guvenli` | +0.008 | +0.002 | +0.016 | — | Güvenli tahmine göre +0.8 puan |
| 0.9 | `mpc_hibrit_asimetrik - mpc_beyan`          | +0.002 |  0.000 | +0.005 | False      | Eşit |

---

## 5. Ek / İkincil Analiz: Erken Ayrılan Araç Başarısı (`erken_ok`, Bootstrap %95 GA)

> **Metodolojik Not:** Bu analiz, önceden belirlenmiş birincil hipotez metriği değildir; post-hoc gözlemleri test döneminde doğrulamak amacıyla yürütülen **ikincil/keşifsel bir ek analizdir.**
> - **Örneklem ve Eşleştirme:** Test döneminde erken ayrılan araca sahip 107 (saha, gün) çiftinin tamamında her iki yöntem de mevcuttur (kayıp gün yoktur). Gün bazlı bootstrap her gün çiftini eşit ağırlıklandırır; araç bazında ağırlıklandırıldığında da pozitif fark (+3.37 yüzde puan) korunmaktadır.
> - Sonuçlar oranlarla karıştırılmaması için **yüzde puan (% puan)** cinsinden ifade edilmiştir.

| Kapasite | Karşılaştırma | Fark (% puan) | %95 Güven Aralığı (% puan) | Yorum |
|:---|:---|:---:|:---:|:---|
| **$f=0.5$** | **`mpc_hibrit_asimetrik - mpc_beyan`** | **+4.62 % puan** | **[+2.79, +6.61] % puan** | **Erken ayrılanlarda alt sınır > 0 (Pozitif Sinyal)** |
| $f=0.5$ | `mpc_hibrit_risk_esikli - mpc_beyan` | +3.60 % puan | [+1.59, +5.66] % puan | Erken ayrılanlarda pozitif sinyal |
| $f=0.5$ | `mpc_tahmin_guvenli - mpc_beyan` | +3.61 % puan | [+1.32, +6.12] % puan | Ham güvenli tahmin erken ayrılanlarda +3.61 % puan |
| $f=0.5$ | `mpc_hibrit_asimetrik - mpc_tahmin_guvenli` | +1.01 % puan | [−0.45, +2.47] % puan | Güvenli tahmin ile benzer koruma düzeyi |
| **$f=0.7$** | `mpc_hibrit_asimetrik - mpc_beyan` | +0.53 % puan | [−0.54, +1.66] % puan | Kapasite arttıkça fark nötrleşir (sıfırı kapsar) |
| **$f=0.9$** | `mpc_hibrit_asimetrik - mpc_beyan` | +0.52 % puan | [+0.08, +1.14] % puan | Nötr / hafif pozitif |

---

## 6. İki Dönemin Yan Yana Karşılaştırması ($f=0.5$ Kapasite Senaryosu)

Ocak–Haziran (Doğrulama, 68 gün) ve Temmuz–Aralık (Test, 59 gün) dönemleri aynı sahalardan gelen ardışık takvim dilimleridir. Bağımsız kör deneyler olmadıkları için, iki dönemdeki bulgular "genel geçer kanıt" yerine yan yana karşılaştırmalı olarak incelenmelidir:

| Metrik / Karşılaştırma ($f=0.5$) | Doğrulama Dönemi (Oca–Haz 2019) | Bağımsız Test Dönemi (Tem–Ara 2019) | İki Dönem Arasındaki Eğilim |
|:---|:---:|:---:|:---|
| `mpc_beyan` Genel Başarı (`ok`) | %90.9 | %85.7 | Veri dönemi mevsimselliğine göre taban başarı değişti |
| `mpc_tahmin_guvenli` Genel Başarı (`ok`) | %88.3 | %84.0 | Her iki dönemde de beyanın gerisinde kaldı |
| **`mpc_hibrit_asimetrik` (Aday 1) Genel Başarı (`ok`)** | **%90.8** | **%86.3** | **Her iki dönemde de `mpc_beyan` ile başa baş** |
| Fark: `Aday 1 − mpc_tahmin_guvenli` (Genel `ok`) | **+2.4 % puan** ([+1.8, +3.1]) | **+2.2 % puan** ([+1.4, +3.2]) | **Aday 1, güvenli tahminli MPC'de görülen başarı kaybını tutarlı biçimde azaltmıştır** |
| Fark: `Aday 1 − mpc_beyan` (Genel `ok`) | −0.1 % puan ([−0.7, +0.4]) | +0.5 % puan ([−0.2, +1.3]) | Her iki dönemde de GA sıfırı kapsar (belirgin üstünlük yok) |
| Fark: `Aday 1 − mpc_beyan` (Erken Ayrılış `erken_ok`) | **+3.5 % puan** | **+4.6 % puan** ([+2.8, +6.6]) | Erken ayrılan araçlarda pozitif iyileşme eğilimi |
| Toplam Teslim Oranı (`teslim`) | %97.1 vs %97.3 (Beyan) | %94.6 vs %94.8 (Beyan) | Toplam enerji teslim oranı her iki dönemde de benzer kaldı |

---

## 7. Bilimsel Değerlendirme ve Konumlandırma

1. **Aday 1 Neyi Başardı, Neyi Başaramadı?**
   - **Başardığı:** Aday 1, güvenli tahminli MPC'de görülen başarı kaybını azaltmıştır ($f=0.5$'te test döneminde +2.2 yüzde puan iyileşme).
   - **Başaramadığı:** Referans `mpc_beyan`'a karşı genel başarıda (`ok`) istatistiksel olarak anlamlı bir üstünlük sağlayamamıştır (%86.3 vs %85.7; fark +0.5 yüzde puan, güven aralığı sıfırı içermektedir).
2. **Kazanım İddiasının Sınırları:**
   - Ocak–Haziran ve Temmuz–Aralık dönemleri bağımsız iki kör deney değildir; aynı saha altyapısından gelen ardışık iki takvim dönemidir. Bu nedenle sonuçlar genel bir üstünlük kanıtı olarak değil, test dönemi bulgusuna dayalı bir iyileşme eğilimi olarak ifade edilmelidir.
3. **Nihai Proje Konumlandırması (Climathon 2026):**
   > *ŞarjDenge'nin asimetrik hibrit yaklaşımı, düşük kapasite senaryosunda erken ayrılan araçların hedef enerjiyi zamanında almasını iyileştirme potansiyeli gösteriyor. Genel başarı oranında beyan tabanlı MPC'ye karşı belirgin bir üstünlük kanıtlanmış değil; toplam enerji teslim oranı da benzer kalıyor. Bu nedenle mevcut bulgu, genel performansta kanıtlanmış üstünlükten çok, erken ayrılış riskini yönetmeye yönelik umut verici bir ödünleşim olarak değerlendirilmelidir.*
