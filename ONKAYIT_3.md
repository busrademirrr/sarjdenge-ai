# ŞarjDenge AI — Ön Kayıt 3 (TASLAK — HENÜZ KİLİTLENMEDİ)

> [!WARNING]
> **DURUM: TASLAK — ÖN ÇALIŞMA AŞAMASINDA (HENÜZ KİLİTLENMEDİ)**
> Bu belge, Faz 0 ve Faz 1A denetimleri sonrasında ileri tarihli bağımsız bir değerlendirme için hazırlanmış bir ön kayıt protokol taslağıdır.
> Bu aşamada **yeni veri indirilmemiş, API çağrısı yapılmamış, model eğitilmemiş ve deney çalıştırılmamıştır.** Veri erişimi ve örneklem yeterliliği doğrulanmadan bu taslak kilitlenemez ve yürürlüğe giremez.

---

## 1. Araştırma Bağlamı ve Yeni Hipotezin Konumu

### 1.1. Tarihsel Hipotezden (`ONKAYIT_2`) Ayrım
* `ONKAYIT_2.md` protokolü, doğrusal programlama tabanlı MPC optimizasyonunun tahminle beslendiğinde beyana kıyasla zamanında hedef tamamlama oranını artıracağı hipotezini (`mpc_tahmin_guvenli - mpc_beyan >= +0.02`) sınamıştır. Bu hipotez hem 2019 doğrulamasında hem de 2020 taze testinde **desteklenmemiştir** (LP-MPC enerjiyi zamana yaydığı ve $q_{80}$ enerji şişirmesi hayalet rezervasyona yol açtığı için beyanlı yöntemlerin gerisinde kalmıştır).
* **Ön Kayıt 3 Hipotezi:** Faz 0 ve Faz 1A denetimlerinde, kural tabanlı En Erken Bitiş Öncelikli (Earliest Deadline First — EDF) planlayıcısının en sıkı kapasite kısıtında ($f=0.5$) ve orta kapasitede ($f=0.7$) tüm yöntemler arasında en yüksek başarıyı elde ettiği saptanmıştır. Bu nedenle Ön Kayıt 3, önceki MPC hipotezinden **tamamen bağımsız ve yeni bir araştırma sorusuna** odaklanır:
  > *"Kural tabanlı EDF algoritması, sürücü beyanı yerine makine öğrenmesi tabanlı güvenli tahminle (`sure_q20`, `kwh_q80`) çalıştırıldığında, en sıkı kapasite kısıtı ($f=0.5$) altında zamanında hedef tamamlama oranında kullanıcı beyanına kıyasla gerçek bir üstünlük sağlar mı?"*

---

## 2. Hipotez Tanımı, Birincil Metrik ve Karar Kuralı

### 2.1. Tek Birincil Karşılaştırma
* **Algoritmalar:** `edf_tahmin_guvenli` karşısında `edf_beyan`.
* **Kapasite Düzeyi:** $f = 0.5$ (Günün kontrolsüz tepe gücünün %50'si; en sıkı kapasite kısıtı).
* **Hipotez Formülasyonu:**
  Günlük zamanında hedef tamamlama oranları farkı:
  $$\Delta_d = \text{ok}_{d, \text{edf\_tahmin\_guvenli}} - \text{ok}_{d, \text{edf\_beyan}}$$
  Popülasyon düzeyindeki gerçek beklenen fark $\Delta = \mathbb{E}[\Delta_d]$ olmak üzere:
  $$\mathcal{H}_0: \Delta < 0.02 \quad \text{vs.} \quad \mathcal{H}_1: \Delta \ge 0.02$$

### 2.2. Birincil Metrik ve Bilimsel Sınırlandırması (`ok`)
* Simülatörde her $i$ oturumu için başarı:
  $$\text{ok}_i = \left( \frac{\text{teslim}_i}{\max(e_{\text{gercek}, i}, 10^{-6})} \ge 0.95 \right)$$
* **Zorunlu Bilimsel Sınır:** Buradaki $e_{\text{gercek}, i}$, ACN veri tabanındaki `kWhDelivered` değeridir. Bu değer **aracın gerçek toplam batarya kapasitesini veya gerçek toplam ihtiyacını ölçmez**; yalnızca o şarj oturumunda EVSE tarafından araca fiilen teslim edilmiş enerjidir. Dolayısıyla metrik, *"tarihsel teslim edilen enerjiyi kısıt altında tamamlama oranı"* olarak tanımlanır.

### 2.3. Matematiksel Olarak Tutarlı Başarı Karar Kuralı
Yeni deneyde **"tahminin sağladığı gerçek iyileşmenin en az +2.0 yüzde puan (+0.02) olduğu"** güçlü iddiası sınanacaktır. Bu iddia ile tam tutarlı karar kuralı:
$$\text{Karar:} \quad \text{CI}_{95\%, \text{alt}} \ge +0.0200 \quad \text{(+2.00 yüzde puanı)}$$
* Burada $\text{CI}_{95\%, \text{alt}}$, günler üzerinden eşleştirilmiş bootstrap ($B=2.000$, sabit tohum `tohum=42`) dağılımının %2.5 persentil alt sınırıdır.
* Nokta tahmininin ($\hat{\Delta}$) $+0.02$'yi geçmesi tek başına yeterli değildir; örneklem belirsizliği hesaba katıldığında dahi alt sınırın $+0.02$'nin altına inmemesi şarttır.
* *(Not: Bu katı kural yalnızca Ön Kayıt 3 için geçerlidir; `ONKAYIT_2.md` kapsamındaki tarihsel analizlerin karar kuralı geriye dönük değiştirilemez).*
* **Başarı Eşiğinin Korunması:** Başarı eşiği (+0.02 / +2.0 yüzde puanı), ileride elde edilecek veri veya örneklem miktarına göre asla düşürülmeyecek veya gevşetilmeyecektir. Eğer elde edilen örneklem büyüklüğü istatistiksel güç için yetersiz kalırsa, başarı kriteri esnetilmeyecek; deney sonucu "yetersiz güç / sonuçsuz (inconclusive)" olarak raporlanacaktır.

---

## 3. Planlama Güç Analizi ve Örneklem Boyutu

Tarihsel verilerde (2019 doğrulama ve 2020 test) günlük farkların standart sapması $\sigma_{\Delta} \approx 0.035 - 0.045$ aralığında gözlenmiştir. İki taraflı $\alpha=0.05$ ($z_{1-\alpha/2} = 1.96$) ve $\%80$ istatistiksel güç ($1-\beta=0.80$, $z_{1-\beta} = 0.8416$) varsayımı altında, alt sınırın $+0.02$'yi aşması için gereken yaklaşık bağımsız simülasyon gün sayısı ($N_{\text{gün}}$):

$$N_{\text{gün}} \approx \left( \frac{(1.96 + 0.8416) \cdot \sigma}{\Delta - 0.02} \right)^2 = \left( \frac{2.8016 \cdot \sigma}{\Delta - 0.02} \right)^2$$

| Gerçek Popülasyon Farkı ($\Delta$) | Planlama Standart Sapması ($\sigma$) | Net Marj ($\Delta - 0.02$) | Gereken Bağımsız Gün Sayısı ($N_{\text{gün}}$) |
| :---: | :---: | :---: | :---: |
| **+0.030 (+3.0 yp)** | 0.035 | +0.010 | **97 gün** |
| **+0.030 (+3.0 yp)** | 0.040 | +0.010 | **126 gün** |
| **+0.030 (+3.0 yp)** | 0.045 | +0.010 | **159 gün** |
| **+0.040 (+4.0 yp)** | 0.035 | +0.020 | **25 gün** |
| **+0.040 (+4.0 yp)** | 0.040 | +0.020 | **32 gün** |
| **+0.040 (+4.0 yp)** | 0.045 | +0.020 | **40 gün** |
| **+0.050 (+5.0 yp)** | 0.035 | +0.030 | **11 gün** |
| **+0.050 (+5.0 yp)** | 0.045 | +0.030 | **18 gün** |

### 3.1. Yaklaşık Güç Hesabı ve Sınırları
* **Kestirim Niteliği:** Yukarıdaki hesaplama, asimptotik normallik ve gözlemler arası bağımsızlık varsayımlarına dayanan **yaklaşık bir planlama kestirimidir**; kesin bir güç veya başarı garantisi teşkil etmez.
* **Fiili Koşullar:** Gerçek veri dağılımındaki basıklık/çarpıklık, uç değerler, günler arası otokorelasyon ve bootstrap persentil aralıklarının asimetrisi ampirik test gücünü değiştirebilir.

### 3.2. Üç Farklı Gün ve Örneklem Kavramının Ayrımı
Protokolde örneklem büyüklüğü değerlendirilirken şu üç kavram kesin çizgilerle birbirinden ayrılmalıdır:
1. **Takvim Günü Sayısı ($N_{\text{takvim}}$):** Seçilen başlangıç ve bitiş tarihleri arasındaki toplam gün sayısıdır.
2. **Geçerli Simülasyon Günü Sayısı ($N_{\text{sim}}$):** Takvim günleri içerisinden; şebeke/sensör kesintisi olmayan, hafta sonu/tatil kaynaklı aşırı düşük hacim içermeyen ve protokolün `min_arac_gunluk >= 8` (ve simülatörde $\ge 4$ araç) filtresini geçen günlerin sayısıdır. Tarihsel olarak iş yeri şarj istasyonlarında hafta sonları ve tatiller nedeniyle takvim günlerinin ancak yaklaşık %60–%70'i bu filtreyi geçebilmektedir ($N_{\text{sim}} < N_{\text{takvim}}$).
3. **Etkin Bağımsız Örneklem Sayısı ($N_{\text{etkin}}$):** Günler arasındaki zamansal otokorelasyon, haftalık periyodik döngüsellik ve aynı kullanıcıların tekrar eden oturumları nedeniyle istatistiksel testin varsaydığı bağımsız gözlem eşdeğeridir. Pozitif otokorelasyon varlığında etkin örneklem geçerli simülasyon gününden de azdır ($N_{\text{etkin}} \le N_{\text{sim}}$).

### 3.3. 1 Ocak – 1 Haziran 2021 Penceresinin Yetersizliği ve Tam 2021 Adaylığı
* **İlk Aday Pencere Hacmi:** 1 Ocak 2021 – 1 Haziran 2021 aralığı toplam **151 takvim günü** ($N_{\text{takvim}} = 151$) içerir.
* **Tutarsızlığın Tespiti:** En ihtiyatlı planlama senaryosunda ($\Delta = +0.030, \sigma = 0.045$), yaklaşık 159 bağımsız gün ($N_{\text{etkin}} \approx 159$) gerekmektedir. Takvimdeki günlerin tamamı geçerli simülasyon günü kabul edilse dahi bu süre **matematiksel olarak 159 güne ulaşamamaktadır** ($151 < 159$). Hafta sonları ve `min_arac_gunluk >= 8` filtresi sonrası en fazla ~90–105 geçerli simülasyon günü ($N_{\text{sim}}$) kalacaktır.
* **Tam 2021 Yılı Adaylığı (Doğrulanmamış Aday):** Bu yetersizlik nedeniyle aday inceleme penceresi tam 2021 yılı (1 Ocak 2021 – 31 Aralık 2021, 365 takvim günü) olarak ele alınmalıdır; ancak bu dönem henüz API ile test edilmemiş **doğrulanmamış bir aday** niteliğindedir.

### 3.4. Örneklem Karar Kuralı ve İhtiyatlı Güç Yönetimi
* **$N_{\text{sim}} \ge 159$ Durumu (Otomatik Devam Koşulu Değildir):** Geçerli simülasyon günü sayısının 159'a ulaşması ($N_{\text{sim}} \ge 159$), otomatik olarak ön kaydı dondurma veya deneyi başlatma yetkisi vermez. Günler arasındaki zamansal otokorelasyon, haftalık periyodik dalgalanmalar ve sahadaki aynı kullanıcıların tekrar eden şarj davranışları bağımsız gün eşdeğerini düşürür ($N_{\text{etkin}} \le N_{\text{sim}}$). Otokorelasyon yapısı ve sahadaki bağımlılık riski ampirik olarak değerlendirilmeden protokol kilitlenemez.
* **$N_{\text{sim}} < 25$ Eşiği (Evrensel Bilimsel Baraj Değildir):** Güç tablosunda yer alan ~25 gün değeri, $\Delta = +0.040, \sigma = 0.035$ gibi yüksek etki büyüklüğü ve düşük varyans varsayımı altında türetilmiş asimptotik teorik bir alt sınırdır; mutlak ve evrensel bir bilimsel doğa kanunu veya kesin durma barajı olarak sunulamaz. Karar verilirken oturum yoğunluğu, pandemi koşulları ve hedeflenen etki marjı bir arada değerlendirilmelidir.
* **İhtiyatlı Planlama Kararlılığı:** Proje, $\sigma = 0.045$, gerçek etki $\Delta = +0.030$ ve yaklaşık 159 bağımsız gün varsayımını en ihtiyatlı planlama senaryosu olarak korur.
* **Başarı Eşiğinin Dokunulmazlığı:** Örneklem azlığı veya veri yetersizliği gerekçe gösterilerek birincil başarı eşiği ($\text{CI}_{95\%, \text{alt}} \ge +0.02$) **asla aşağı çekilmeyecektir**.

---

## 4. İkincil Karşılaştırmalar ve Çoklu Test Yönetimi

Birincil test tektir: en sıkı kapasite kısıtı altında (`edf_tahmin_guvenli - edf_beyan`, $f=0.5$). Diğer tüm analizler hiyerarşik olarak ikincil veya keşifsel kabul edilir:

1. **Ön Kayıtlı İkincil Karşılaştırmalar:**
   - EDF Kapasite Duyarlılığı: $f=0.7$ ve $f=0.9$ için `edf_tahmin_guvenli - edf_beyan`.
   - MPC Karşılaştırmaları: en sıkı kapasite kısıtı ($f=0.5$) ile $f \in \{0.7, 0.9\}$ için `mpc_tahmin_guvenli - mpc_beyan`.
   - LLF Karşılaştırmaları: en sıkı kapasite kısıtı ($f=0.5$) ile $f \in \{0.7, 0.9\}$ için `llf_tahmin_guvenli - llf_beyan`.
   - *Çoklu Karşılaştırma Düzeltmesi:* İkincil hipotezler raporlanırken Tip I hata şişmesini kontrol etmek amacıyla **Holm-Bonferroni** sıralı düzeltmesi uygulanacaktır.
   - *Korelasyon Uyarısı:* Aynı günlerde koşan algoritmalar birbirine yüksek düzeyde pozitif bağımlıdır. Bağımsızlık varsayımı altındaki teorik hata birikimi hesapları evrensel bir üst sınır olarak algılanmamalıdır.
2. **Keşifsel Analizler (Hipotez Doğrulama Dışı):**
   - Erken ayrılan araçlar (`erken_ok`) alt kümesi analizi.
   - Keşifsel hibrit yöntemler (`mpc_hibrit_asimetrik`).

---

## 5. Aday Veri Dönemi, Resmî API Sorgu Protokolü ve Kaçak Önleme Kuralları

### 5.1. Aday Değerlendirme Penceresi (Tam 2021 Yılı — Doğrulanmamış Aday)
* **Aday Dönem:** 1 Ocak 2021 00:00:00 GMT – 31 Aralık 2021 23:59:59 GMT (Tam 2021 Yılı).
* **Statü (Doğrulanmamış Aday):** Bu dönem yerel depoda mevcut değildir ve kesinleşmiş test seti olarak kabul edilmemiştir. ACN API üzerinden veri bulunabilirliği, Caltech ve JPL sahalarındaki aktif soket sayıları ve 2021 yılı pandemi kısıtlamalarının oturum yoğunluğuna etkisi doğrulanmadan aday dönem kilitlenemez ve yeterli güce sahip olduğu iddia edilemez.
* **Örneklem Yetersizliği Karar Kuralı:** Eğer API sorguları sonucunda filtreden geçen geçerli simülasyon gün sayısı ($N_{\text{sim}}$) hedeflenen güç gereksinimini karşılayamazsa; ya çalışma bağımsız değerlendirme için yetersiz veri nedeniyle resmi olarak durdurulacak ya da yeni bir aday dönem araştırılacaktır. Başarı eşiği (+0.02) veri azlığı gerekçesiyle asla düşürülmeyecektir.

### 5.2. Resmî ACN-Data REST API Sözdizimi ve Sorgu Protokolü
ACN-Data resmî dokümantasyonuna (`ev.caltech.edu/dataset`) dayanan teknik sorgu kuralları:
* **Resmî Oturum Uç Noktası:**
  `https://ev.caltech.edu/api/v1/sessions/{site_id}` (Zaman serisi içermeyen standart oturumlar için; geçerli siteler: `caltech`, `jpl`).
* **Resmî `where` Sözdizimi:**
  Belgelenmemiş MongoDB filtreleri (`$gte`, `$lt`) yerine, resmî dokümantasyonda tanımlanan Python/SQL benzeri mantıksal ifadeler ve RFC 1123 tarih biçimi (`%a, %d %b %Y %H:%M:%S GMT`) kullanılır:
  - `caltech` için sorgu URI:
    ```http
    GET https://ev.caltech.edu/api/v1/sessions/caltech?where=connectionTime>="Fri, 1 Jan 2021 00:00:00 GMT" and connectionTime<="Fri, 31 Dec 2021 23:59:59 GMT"
    ```
  - `jpl` için sorgu URI:
    ```http
    GET https://ev.caltech.edu/api/v1/sessions/jpl?where=connectionTime>="Fri, 1 Jan 2021 00:00:00 GMT" and connectionTime<="Fri, 31 Dec 2021 23:59:59 GMT"
    ```
* **Belgelenmiş ve Belgelenmemiş Özelliklerin Ayrımı:**
  - Standart uç noktada (`/sessions/{site_id}`) varsayılan sayfa boyutu 25 oturumdur (`max_results: 25`).
  - Belgelenmeyen `$gte`, `$lt` veya `max_results=1` gibi parametreler doğrulanmış API özelliği olarak kabul edilmeyecektir.
* **`_meta.total` Alanı ve Sayfa Verisi Ayrımı:**
  - JSON yanıtında dönen `_meta` bloğu (`page`, `max_results`, `total`) ile o anki sayfada yer alan kayıtlar (`_items`, en fazla 25 adet) tamamen farklıdır.
  - Tek bir hafif GET isteği yapıldığında dönen ilk sayfanın `response.json()["_meta"]["total"]` alanı okunarak, tüm veri indirilmeden sorguya eşleşen toplam oturum sayısı ($N_{\text{oturum}}$) kesin olarak tespit edilir.
* **Tarih Formatı, UTC ve Yerel Saat Davranışı:**
  - API, sorgu filtrelerini ve zaman damgalarını UTC (GMT) olarak işler.
  - Pasadena sahaları yerel saat dilimindedir (`America/Los_Angeles`, PST: UTC-8 / PDT: UTC-7). API'nin zaman filtresi davranışı belgelenmiş bir UTC filtrelemesidir; oturumların takvim günlerine bölünmesi ve günlük simülasyon filtresi aşamasında yerel saat dönüşümü uygulanmalıdır. Dokümantasyonda yazan UTC davranışı ile yerel dönüşüm varsayımları birbirinden ayrı tutulmalıdır.
* **Oturum Sayısı vs Geçerli Simülasyon Günü:**
  - Yalnızca toplam oturum sayısının ($N_{\text{oturum}}$) yüksek çıkması yeterli değildir. Pandemi nedeniyle oturumların günlere homojen dağılmamış olması durumunda, `min_arac_gunluk >= 8` filtresini geçen gün sayısı ($N_{\text{sim}}$) beklenenden çok düşük kalabilir.
  - Bu nedenle doğrulamada yalnızca toplam oturum sayısına bakılmayacak; hafif zaman damgaları üzerinden geçerli simülasyon günü sayısı ($N_{\text{sim}}$) fiilen ölçülecektir.

### 5.3. Güvenli Veri Edinim Süreci (Çalıştırmadan Hazırlık Adımları)
Bu aşamada hiçbir API çağrısı yapılmamakta ve veri indirilmemektedir; süreç protokol olarak tanımlanmıştır:
1. **Yerel Anahtar Güvenliği:** API anahtarı kullanıcının yerel ortam değişkeninde (`$env:ACN_API_TOKEN`) tutulur. Anahtar asla koda, depoya, git commit'lerine veya sohbete yazılmaz/istenmez.
2. **Küçük Salt-Okunur Metadata Sorgusu:** Yetkilendirme ve uç nokta yanıt şeması (`_meta.total`), tek bir hafif istek ile test edilir.
3. **Hafif Oturum Başlıklarının Çekilmesi:** Tüm şarj profili yerine yalnızca oturum başlıkları (`sessionID`, `siteID`, `connectionTime`, `disconnectTime`) çekilerek yerel gün bazlı $N_{\text{sim}}$ hesaplanır.
4. **Yetersizlik Durumunda Durma Kuralı:** Elde edilen geçerli gün sayısı istatistiksel güç gereksinimini karşılamıyorsa ön kayıt kilitlenmez ve tam veri indirme yapılmaz.

### 5.4. Zamansal Sızıntıyı Kesin Engelleyen Kesim Kuralı (Buffer Cut-off)
Faz 1A.1 denetiminde saptanan H1–H2 sınırındaki 3 taşan oturum vakasının tekrarlanmaması için:
$$\max(disconnectTime_{\text{eğitim}}) \le \min(connectionTime_{\text{test}})$$
Test döneminin ilk oturumu başladığı anda eğitim kümesindeki tüm araçların fiziksel olarak ayrılmış ve sayaçlarının kapanmış olması zorunludur. Henüz ayrılmamış araçlar eğitim kümesine dahil edilemez.

### 5.5. Kullanıcı Geçmişinin Sürekliliği (`strict_shift=True`)
* Model eğitim verisi ile yeni test dönemi tek bir kronolojik zaman dizisi olarak birleştirilecek; öznitelik matrisi `veri_hijyeni.ozellikler(df_tum, strict_shift=True)` ile tek seferde üretilecektir.
* Yalnızca $disconnectTime_{\text{önceki}} \le connectionTime_{\text{mevcut}}$ şartını sağlayan tamamlanmış oturumlar geçmişe dahil edilecek; ardından test satırları dilimlenecektir.

### 5.6. Günlük Simülasyon Filtreleri
* **Simülasyon Ön Filtresi:** `deney_calistir` içindeki `min_arac_gunluk = 8` (veya birincil protokolde kilitlenecek eşik) uygulanır.
* **Simülatör Güvenlik Tabanı:** `simule_gun` seviyesinde sahada geçerli araç sayısı $\ge 4$ olmayan günler simülasyon dışı bırakılır.

---

## 6. Dondurulmuş Model ve Kod Bütünlüğü

* **Model Mimarisi:** İş Paketi C'de seçilen ve dondurulan Şampiyon Süre ve Enerji modelleri (`sarjdenge/modeller.py` içindeki `GradientBoostingQuantileModel`, n_estimators=60, max_depth=4) sıfır müdahale ile kullanılacaktır. Hiperparametre optimizasyonu veya model seçimi yapılmayacaktır.
* **Simülatör:** Dondurulmuş `sarjdenge/sim.py` çekirdeği aynen korunacaktır.

---

**Ön Kayıt 3 Taslağı tamamlanmıştır. Veri erişimi doğrulanmadan ve protokol onaylanmadan kilitleme yapılmayacaktır.**
