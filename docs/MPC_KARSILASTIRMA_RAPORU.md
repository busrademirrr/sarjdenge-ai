# ŞarjDenge AI — MPC Simülasyonu ve Karar Mekanizması Raporu (İş Paketi D)

Bu rapor, ŞarjDenge AI projesi kapsamında İş Paketi C'de seçilen GradientBoosting şampiyon modellerinin tahminleri ile beslenen MPC ve kural tabanlı planlayıcıların simülasyon sonuçlarını, ön kayıtlı ana hipotez testlerini, adillik metriklerini ve Temmuz–Aralık 2019 dönemler arası doğrulama bulgularını belgeler.

---

## 1. Simülasyon Protokolü ve Adil Karşılaştırma Şartları

Tüm algoritmalar tamamen özdeş koşullarda karşılaştırılmıştır:
- **Zaman Çözünürlüğü:** $\Delta t = 15$ dakika ($DK = 900$ saniye).
- **Ayrık Güç Kademeleri:** $P \in \{0, 1.66, 3.33, 4.99, 6.66\}$ kW ($208\text{ V}$ ACN standart seviyeleri).
- **Kapasite Kısıtları:** Kontrolsüz tepe gücünün ($P_{\text{tepe}}$) $f \in \{0.5, 0.7, 0.9\}$ oranları.
- **Sıfır Gelecek Bilgisi Sızıntısı:** Planlayıcılar online kararlarında yalnızca inanılan değerleri (`inan_dep`, `inan_kwh`) görür. Gerçek ayrılış (`disconnectTime`) ve gerçek ihtiyaç (`kWhDelivered`) yalnızca simülasyon sonrası post-hoc değerlendirmede kullanılır.
- **Kapasite İhlali Güvencesi:** Tüm yöntemlerde $\sum P_i \le P_{\text{kapasite}}$ kısıtı kesin olarak sağlanmış, kapasite ihlali sayısı **0** olarak doğrulanmıştır.

### 1.1. MPC Matematiksel Modeli (Gerçek Kod Eşleştirmesi)
`sarjdenge/sim.py` modülünde (satır 68–104) fiilen çalışan MPC optimizasyonu, `scipy.optimize.linprog` (HiGHS metodu) ile çözülen bir **Doğrusal Programlama (LP)** problemidir:
- **Karar Değişkenleri:** $P_{i, s}$ — $i$ aracına ufuk boyunca $s \in \{0, \dots, L_i - 1\}$ adımında tahsis edilecek şarj gücü (kW) ($L_i = \max(\text{dep}_i - t, 1)$, $H = \max_i L_i$).
- **Amaç Fonksiyonu (Zamanla Azalan Ağırlıkla Toplam Enerji Maksimizasyonu):**
  $$\max_{0 \le P_{i, s} \le P_{\max}} \sum_{i=1}^{m} \sum_{s=0}^{L_i - 1} \left(1.0 - 0.5 \frac{s}{\max(H, 1)}\right) \Delta t \cdot P_{i, s}$$
  (Kodda $c_{i, s} = -w_s \cdot \Delta t$ ile minimize edilir; erken adımlara $w_0=1.0$, son adıma $w_H=0.5$ ağırlık verilerek erken şarj teşvik edilir. Kodda ceza veya araç bazlı aciliyet terimi yoktur).
- **Kısıtlar:**
  1. $0 \le P_{i, s} \le P_{\max}$ ($6.656$ kW).
  2. $\sum_{i: s < L_i} P_{i, s} \le P_{\text{kapasite}}$ (adım başına kapasite tavanı).
  3. $\sum_{s=0}^{L_i - 1} P_{i, s} \cdot \Delta t \le \max(\text{kalan}_i, 0.0)$ (araç başına kalan enerji sınırı).
- **Ayrıklaştırma ve Artık Dağıtımı:** $P_{i, 0}$ alt EVSE kademesine yuvarlanır, artık kapasite en büyük yuvarlama farkına sahip araçlara aktarılır, kalan güç `_firsatci` ile bağlı araçlara paylaştırılır. Çözüm bulunamazsa `kural("edf")` devreye girer.

---

## 2. Ön Kayıtlı Ana Hipotez Değerlendirmesi

[`ONKAYIT_2.md`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/ONKAYIT_2.md) belgesinde kilitlenen ana karar kuralı:
$$\Delta = \text{mpc\_tahmin\_guvenli} - \text{mpc\_beyan} \ge +0.02 \text{ (+2.0 yüzde puanı)} \quad \text{ve} \quad \text{CI}_{95\%} \text{ alt sınırı} > 0$$

### Eşleştirilmiş Gün Bazlı Bootstrap ($B = 2.000$) Hipotez Testi Sonuçları

#### A. Ocak–Haziran 2019 Doğrulama Dönemi ($N = 5.207$ oturum, 68 gün)

| Kapasite Oranı ($f$) | Karşılaştırma | Ortalama Fark ($\Delta$) | %95 Bootstrap Güven Aralığı | Ön Kayıt Eşiği | Hipotez Desteklendi mi? |
| :---: | :---|:---:|:---:|:---:|:---:|
| **$f = 0.5$** (Sıkı) | `mpc_tahmin_guvenli - mpc_beyan` | **$-0.17$ p.p.** ($-0.0017$) | $[-0.66, +0.28]$ p.p. | $\ge +2.0$ p.p. | ❌ **DESTEKLENMEDİ** |
| **$f = 0.7$** (Orta) | `mpc_tahmin_guvenli - mpc_beyan` | **$-0.58$ p.p.** ($-0.0058$) | $[-1.06, -0.10]$ p.p. | $\ge +2.0$ p.p. | ❌ **DESTEKLENMEDİ** |
| **$f = 0.9$** (Gevşek) | `mpc_tahmin_guvenli - mpc_beyan` | **$-0.02$ p.p.** ($-0.0002$) | $[-0.22, +0.17]$ p.p. | $\ge +2.0$ p.p. | ❌ **DESTEKLENMEDİ** |

#### B. Temmuz–Aralık 2019 Dönemler Arası Doğrulama ($N = 11.911$ oturum, 148 gün)
*(Daha önce incelendiği için bağımsız holdout test olarak adlandırılmaz; ardışık dönem kararlılık testidir).*

| Kapasite Oranı ($f$) | Karşılaştırma | Ortalama Fark ($\Delta$) | %95 Bootstrap Güven Aralığı | Ön Kayıt Eşiği | Hipotez Desteklendi mi? |
| :---: | :---|:---:|:---:|:---:|:---:|
| **$f = 0.5$** (Sıkı) | `mpc_tahmin_guvenli - mpc_beyan` | **$-0.22$ p.p.** ($-0.0022$) | $[-0.53, +0.11]$ p.p. | $\ge +2.0$ p.p. | ❌ **DESTEKLENMEDİ** |
| **$f = 0.7$** (Orta) | `mpc_tahmin_guvenli - mpc_beyan` | **$-0.13$ p.p.** ($-0.0013$) | $[-0.39, +0.15]$ p.p. | $\ge +2.0$ p.p. | ❌ **DESTEKLENMEDİ** |
| **$f = 0.9$** (Gevşek) | `mpc_tahmin_guvenli - mpc_beyan` | **$-0.01$ p.p.** ($-0.0001$) | $[-0.23, +0.23]$ p.p. | $\ge +2.0$ p.p. | ❌ **DESTEKLENMEDİ** |

> **Bilimsel Sonuç:** Önceden tanımlanmış ana hipotez her iki dönemde ve tüm kapasite seviyelerinde **desteklenmemiştir**. Metodolojik kurallar gereği hipotez reddedilmiş olup hedef veya başarı eşiği sonradan değiştirilmemiştir.

---

## 3. Mekanizma Analizi ve Sınırları

Tahmin destekli güvenli MPC'nin beyanlı MPC karşısında beklenen üstünlüğü sağlayamamasının olası mekanizmaları ve kanıt sınırları:

1. **Olası Mekanizma: Hayalet Kapasite Rezervasyonu Hipotezi:**
   - Güvenli MPC, aracı erken ayrılma riskinden korumak için kısa süre ($q_{20}$) ve yüksek enerji ($q_{80}$) varsayar.
   - Doğrusal programlama (LP) planlayıcısı, amaç fonksiyonundaki erken yükleme ağırlığı nedeniyle bu yüksek enerjiyi ($q_{80}$) dar zaman penceresinde ($q_{20}$) yetiştirebilmek için gücü agresif biçimde rezerve eder.
   - Ancak araç gerçekte daha geç ayrılır ve gerçek ihtiyacı $q_{80}$'den düşüktür. Planlayıcının bu araca ayırdığı "hayalet kapasite", o sırada istasyonda şarj bekleyen diğer araçların şarjını kısıtlar.
   - Bu durum kanıtlanmış bir mutlak olgu değil, **test edilmesi gereken bir çalışma hipotezi** olarak ele alınmalıdır.
2. **2019 Teşhis Deneyi Kanıtları (`sarjdenge/tani.py` ve `tani_sonuclari.csv`):**
   - 2019 verisi üzerinde yapılan ayrıştırma analizinde $f=0.5$'te süre tahmini tek başına kullanıldığında (`sure_tahmin_kwh_beyan`) MPC başarısı %91.58'den %90.72'ye (-0.86 yp) düşerken; yalnızca enerji tahmini kullanıldığında (`sure_beyan_kwh_tahmin`) başarı %89.36'ya (-2.22 yp) sert düşüş göstermiştir. Bu durum, enerji tahmininin (özellikle $q_{80}$ talebinin) ana olumsuz bileşen olduğunu ampirik olarak kanıtlamaktadır.
   - Kusursuz bilgi (`oracle`: gerçek ayrılış ve gerçek teslim enerjisi) verildiğinde dahi $f=0.5$'te EDF tavanı +2.16 yp (+2.2 yp), MPC tavanı +2.67 yp (+2.7 yp) ile sınırlı kalmaktadır.
3. **Kullanıcı Beyanının Tamponlama Gücü:**
   - ACN kullanıcılarının ayrılış beyanları ortalama 7–8 saatlik park sürelerini kapsar; gerçek şarj ise 2.5–3 saatte biter. Bu aradaki 4–5 saatlik boş bekleme süresi (*slack*), sürücülerin beyan hatalarını absorbe eder.
4. **Erken Ayrılanlarda Durum (Keşifsel Alt Grup Bulgusu):**
   - Erken ayrılan araçlar alt kümesinde (`erken_ayrilan_basari`):
     - $f = 0.5$'te güvenli MPC erken ayrılanlarda %78.56 başarı sağlarken, beyanlı MPC %78.04 sağlamıştır.
     - Ancak bu etki yalnızca dar kapasitede ve post-hoc tanımlı bir alt kümede gözlenmiş olup genel ana hipotezin desteklenmediği gerçeğini değiştirmemektedir.

---

## 4. Tüm Yöntemlerin Ayrıntılı Karşılaştırma Tabloları

### A. Ocak–Haziran 2019 Doğrulama Dönemi ($N = 5.207$ Oturum, 68 Gün)

| Kapasite ($f$) | Algoritma / Yöntem | Zamanında Başarı (`ok`) | Toplam Teslim Oranı | Erken Ayrılan Başarısı | En Alt %10 Adillik ($p_{10}$) | Kapasite İhlali |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| **0.5** | `fcfs_beyan` | %89.00 | %96.02 | %77.68 | 0.8915 | 0 |
| **0.5** | `llf_beyan` | %90.46 | %96.34 | %78.11 | 0.9314 | 0 |
| **0.5** | `mpc_beyan` *(Ref)* | %90.11 | %96.24 | %78.04 | 0.9303 | 0 |
| **0.5** | `mpc_tahmin_ortanca` | %89.01 | %95.93 | %78.47 | 0.9270 | 0 |
| **0.5** | `mpc_tahmin_guvenli` *(Ana)* | %89.94 | %96.10 | %78.56 | 0.9308 | 0 |
| **0.5** | **`edf_beyan`** | **%91.21** | %96.44 | %79.08 | **0.9480** | 0 |
| **0.5** | **`edf_tahmin_guvenli`** | **%91.23** | **%96.68** | **%79.46** | 0.9449 | 0 |
| | | | | | | |
| **0.7** | `fcfs_beyan` | %93.38 | %98.53 | %85.40 | 0.9719 | 0 |
| **0.7** | `llf_beyan` | %94.16 | %98.64 | %86.98 | 0.9783 | 0 |
| **0.7** | `mpc_beyan` *(Ref)* | %94.16 | %98.62 | %87.20 | 0.9800 | 0 |
| **0.7** | `mpc_tahmin_guvenli` *(Ana)* | %93.58 | %98.51 | %85.63 | 0.9795 | 0 |
| **0.7** | **`edf_beyan`** | %94.23 | %98.57 | %86.51 | 0.9795 | 0 |
| **0.7** | **`edf_tahmin_guvenli`** | **%94.45** | **%98.76** | **%87.05** | **0.9829** | 0 |
| | | | | | | |
| **0.9** | `fcfs_beyan` | %94.79 | %99.06 | %88.05 | 0.9841 | 0 |
| **0.9** | `mpc_beyan` *(Ref)* | %94.99 | %99.07 | %88.98 | 0.9861 | 0 |
| **0.9** | `mpc_tahmin_guvenli` *(Ana)* | %94.97 | %99.12 | %88.99 | 0.9855 | 0 |
| **0.9** | **`edf_tahmin_guvenli`** | **%95.25** | **%99.17** | **%89.24** | **0.9863** | 0 |

---

## 5. Keşifsel Aday 1 Karşılaştırması (`mpc_hibrit_asimetrik`)

> [!NOTE]
> Bu analiz ön kayıtlı ana hipotez testinden tamamen bağımsız, keşifsel bir karşılaştırmadır.

- **Mantığı:** Ayrılış için $\min(\text{beyan}, q_{20})$, enerji için $\max(\text{beyan}, q_{50})$ kullanır.
- **Bulgular:**
  - $f = 0.7$'de Güvenli MPC'ye göre **+$0.39$ yüzde puan** daha yüksek başarı sağlamıştır (%95 CI: $[-0.11, +0.85]$).
  - Güvenli MPC'deki $q_{80}$ aşırı enerji hedefi yerine $q_{50}$ kullanarak hayalet rezervasyon kaybını hafifletmiş; ancak beyanlı MPC'nin gerisinde kalmıştır ($-0.19$ p.p.).
  - Bütün kapasite oranlarında beyana dayalı MPC'den daha düşük başarı verdiği için genel bir çözüm veya doğrudan uygulanabilir yol haritası olarak konumlandırılamaz.

---

## 6. Önemli Bulgular: Kural Tabanlı Dağıtımın Rolü

1. **EDF (Earliest Deadline First) Performansı:** İncelenen senaryolarda en yüksek zamanında başarıyı ve en adil teslimatı (`p10`) kural tabanlı **EDF** sağlamıştır.
2. **Tahmin Destekli EDF ve Sınırları:** 
   - $f = 0.9$'da `edf_tahmin_guvenli`, beyanlı EDF'e kıyasla **+$0.38$ yüzde puanlık** hafif bir artış sağlamıştır (%95 CI: $[+0.06, +0.75]$ p.p.).
   - Ancak dar ve orta kapasitelerde ($f=0.5$ ve $f=0.7$) tahmin destekli EDF, beyana dayalı EDF karşısında belirgin bir üstünlük sağlayamamış (2020 taze test döneminde $f=0.5$'te %86.00 vs %86.44; $f=0.7$'de %90.15 vs %90.62 ile beyanın hafif gerisinde kalmıştır).
3. **Ölçek Farkı Notu:** Ocak–Haziran doğrulamasında kullanılan $s_{\text{egit}}^{\text{sure}} = 336.71 \text{ dk}$ ile Temmuz–Aralık'ta kullanılan $s_{\text{egit}} = 337.72 \text{ dk}$ birbirine çok yakın olduğundan MSS puanları doğrudan karşılaştırılabilir niteliktedir.

---

## 7. Metodolojik Sınırlar ve Sonuç

- **Taze Test Dönemi İzolasyonu:** ACN 2020 verisi bu aşamada kesinlikle modele veya deneylere dahil edilmemiştir.
- **Sonuç:** Güvenli tahminli MPC hipotezi desteklenmemiştir; optimizasyon kurgusunda aşırı koruyucu quantile hedeflerinin ($q_{20}, q_{80}$) hayalet kapasite rezervasyonu olası mekanizmasıyla tutarlı biçimde kapasiteyi kısıtladığı gözlenmiştir.

İş Paketi D tamamlanmıştır. Raporlar ampirik bulgular sınırında tutulmuştur.

