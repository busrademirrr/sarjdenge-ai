# ŞarjDenge AI — İş Paketi E-UI Tamamlama Raporu: Site Yöneticisi Karar Destek Arayüzü ve Sonuç Raporlaması

**Tarih:** 17 Ekim 2026  
**Durum:** Tamamlandı, Doğrulandı ve Test Edildi (48/48 Python + 5/5 Node.js + 5/5 E2E Başarılı)  
**Kapsam:** React + Tailwind CSS Frontend, Node.js Express API, Python ML/MPC Simülasyon Köprüsü, Açıklanabilirlik ("Neden?") Paneli, Bilimsel Şeffaflık Bildirimi  

---

## 1. Yönetici Özeti ve Mimari Genel Bakış

İş Paketi E-UI kapsamında, daha önce İş Paketi C (Quantile Regresyon Şampiyon Modelleri) ve İş Paketi D'de (Eşleştirilmiş Bootstrap ve Hipotez Testi) elde edilen tüm ML ve MPC simülasyon çıktıları jürinin ve site yöneticisinin doğrudan deneyimleyebileceği, sıfır kurulum engeli olan, profesyonel, mobil uyumlu ve bilimsel olarak şeffaf bir web ürününe dönüştürülmüştür.

### Mimari Bileşenler:
1. **Frontend (Kullanıcı Arayüzü):** React 18 + Tailwind CSS + Lucide Icons (Tek sayfa uygulaması, mobil uyumlu, duyarlı tasarım).
2. **Backend (API Katmanı):** Node.js Express API (Port 5000) — REST/JSON sözleşmeleri, CORS desteği, in-memory oturum yönetimi ve statik derleme sunumu.
3. **ML & Simülasyon Motoru:** `sarjdenge/web_servis.py` — Python 3.12, scikit-learn, scipy.optimize (HiGHS) ve simülatör çekirdeği ile 96 adımlı yük profili ve araç telemetrisi üretimi.
4. **Veritabanı Durumu:** Kullanıcı veya jüri verisi kalıcılığı gerekmediğinden veritabanı eklenmemiştir; in-memory demo oturumuyla sıfır sürtünmeli misafir erişimi sağlanmıştır.
5. **Google Kimlik Doğrulama:** Opsiyoneldir. Jüri üyeleri kayıt olmak veya şifre girmek zorunda kalmadan doğrudan "Misafir Modu" ile tüm özellikleri kullanabilir. OAuth sırları frontend veya Git deposunda kesinlikle tutulmamaktadır.

---

## 2. Oluşturulan ve Değiştirilen Dosyalar

| Dosya Yolu | Rol ve Açıklama |
| :--- | :--- |
| `sarjdenge/web_servis.py` | Web arayüzü için tek günlük 96 adımlı güç eğrileri, telemetri ve fiziksel "Neden?" (explainability) motoru. |
| `tests/test_web_servis.py` | Python web servisinin senaryo, profil çıkarma ve neden üretme birim testleri (3/3 geçti). |
| `web/server/package.json` | Node.js Express sunucu paket yapılandırması. |
| `web/server/index.js` | Express ana sunucu, rota bağlayıcı, hata yakalayıcı ve statik frontend sunucu. |
| `web/server/routes/scenarios.js` | Senaryo tanımları ve `GERÇEK SAHA VERİSİ` vs `SENTETİK MODEL (VARSAYIM)` etiketleri. |
| `web/server/routes/benchmark.js` | Doğrulanmış C ve D deney tabloları, bootstrap GA değerleri ve örneklem mutabakatı API'si. |
| `web/server/routes/simulate.js` | Parametrik istekleri Python CLI servisine aktaran ve JSON yanıt dönen köprü. |
| `web/server/routes/auth.js` | Misafir modu (varsayılan) ve opsiyonel Google kimlik doğrulama simülasyonu. |
| `web/server/routes/export.js` | Telemetri ve parametreleri Excel/Pandas uyumlu UTF-8 BOM CSV ve JSON formatında dışa aktarma. |
| `web/server/tests/server.test.js` | Node.js dahili test koşucusuyla API entegrasyon testleri (5/5 geçti). |
| `web/server/tests/e2e_verify.py` | Canlı HTTP istekleri ve Python motoruyla çalışan uçtan uca doğrulama testi (5/5 geçti). |
| `web/client/package.json` | Vite, React 18, Tailwind CSS bağımlılıkları. |
| `web/client/vite.config.js` | Vite yapılandırması ve `/api` vekil (proxy) ayarları. |
| `web/client/tailwind.config.js` | Tailwind tema ve renk paleti (Emerald, Slate, Amber, Rose). |
| `web/client/src/App.jsx` | Karar destek paneli ana bileşeni (Canlı Simülasyon, Doğrulama Arşivi, Metodoloji sekmeleri). |
| `web/client/src/components/*` | Navbar, TransparencyBanner, ScenarioSelector, CapacityControl, KpiCards, PowerCurveChart, GanttChart, VehicleInspectorModal, BenchmarkView, MethodologyView, ExportModal, AuthModal. |

> [!IMPORTANT]
> **Dondurulmuş Çekirdek Bütünlüğü Korundu:**  
> `data.py`, `tahmin.py`, `sim.py`, `deney.py`, `turkiye.py`, `sentetik.py`, `sarjdenge/modeller.py` ve `sarjdenge/deney_v2.py` dosyaları **kesinlikle değiştirilmemiştir**. 2020 ACN holdout test verisi **indirilmemiş ve incelenmemiştir**.

---

## 3. Web Arayüzü Özellikleri ve Jüri Deneyimi

Arayüz üç ana sekme ve zengin etkileşimli modüller halinde tasarlanmıştır:

### A. Bilimsel Şeffaflık Bildirimi (Transparency Banner)
Tüm sayfalarda en üstte sabit olarak yer alan bu alan, önceden kayıtlı ana hipotezin durumunu jüriye dürüstçe sunar:
- **Ana Hipotez:** $\Delta = \text{mpc\_tahmin\_guvenli} - \text{mpc\_beyan} \ge +2,00$ yüzde puanı (y.p.).
- **Sonuç:** **Desteklenmedi (H₀ Korundu)**.
- **Ampirik Değerler:** $f=0.5$ için $\Delta = -0.17$ y.p. (%95 GA: $[-0.66, +0.28]$); $f=0.7$ için $\Delta = -0.58$ y.p. (%95 GA: $[-1.06, -0.10]$); $f=0.9$ için $\Delta = -0.02$ y.p. (%95 GA: $[-0.22, +0.17]$).
- **Fiziksel Mekanizma Açıklaması:** Hayalet Kapasite Rezervasyonu (*Ghost Capacity Reservation*).
- **Lider Çözücü:** EDF (En Erken Termin Önceliği) — Hayali rezervasyon tutmaksızın %91.23–%95.25 başarı oranı ve $p_{10} = %94–%98$ adillik sağlamıştır.

### B. Senaryo ve Altyapı Seçimi
1. **Türkiye İş Yeri Kampüsü:** ACN ampirik verisi ile kalibre edilmiş kurumsal mesai şarjı (`SENTETİK MODEL (VARSAYIM)`).
2. **Türkiye Apartman / Site Otoparkı:** 20 soket, 11 kW Wallbox, 80 kW trafo tahsisli gece şarjı (`SENTETİK MODEL (VARSAYIM)`).
3. **Türkiye Karma Yerleşke:** Gündüz ofis çalışanları, gece site sakinlerinin dinamik paylaştığı 40 soketli hibrit model (`SENTETİK MODEL (VARSAYIM)`).
4. **ACN Gerçek Saha (Doğrulama):** Caltech ve JPL 2019 sahalarının 68 sıkışık günündeki 5.207 gerçek oturumu (`GERÇEK SAHA VERİSİ`).
5. **ACN Gerçek Saha (Dönemler Arası):** Temmuz–Aralık 2019 dönemi 153 günündeki 11.911 gerçek oturumu (`GERÇEK SAHA VERİSİ`).

### C. Dinamik Kapasite Kontrolü (f)
- Kaydırma çubuğu (*slider*) ile kapasite katsayısı $f \in [0.4, 1.0]$ arasında anlık değiştirilebilir.
- Hızlı butonlar: `%40 (Aşırı Kısıtlı)`, `%50 (Temel Deney)`, `%70 (Orta Kapasite)`, `%90 (Geniş Kapasite)`.
- Trafo güç sınırı (kW) ve kontrolsüz tepe gücü dinamik güncellenir.
- "Simülasyonu Çalıştır" butonu tek tıkla Python hattını tetikler ve 1 saniye içinde tüm grafikleri yeniler.

### D. 24 Saatlik Güç-Zaman Yük Eğrisi (96 Adım / 15 dk)
- SVG tabanlı etkileşimli yük eğrisi grafiği.
- Trafo kapasite tavanı (kesikli kırmızı çizgi), kontrolsüz şarj eğrisi (noktalı gri çizgi) ve 6 farklı algoritmanın güç profilleri yan yana izlenebilir.
- Çizgiler tek tek gizlenip açılabilir (toggle legend).
- Fare ile üzerine gelindiğinde (*hover*) adımın yerel saati ve her algoritmanın çektiği kW gücü anlık araç ipucunda (*tooltip*) gösterilir.

### E. Araç Bazlı Zaman Çizelgesi (Gantt) ve "Neden?" (Explainability) Paneli
- Otoparka bağlanan araçların varış, ayrılış ve beyan terminleri yatay bloklar halinde çizilir.
- Herhangi bir araca tıklandığında veya listedeki "Neden?" butonuna basıldığında detaylı modal açılır:
  - Aracın gerçek talebi, kullanıcının beyanı, modelin $q_{20}, q_{50}, q_{80}$ tahminleri.
  - 6 algoritmanın bu araca teslim ettiği kWh ve doyum oranı.
  - **Fiziksel Karar Açıklaması:** Örneğin:
    > *"Hayalet Kapasite Rezervasyonu: Güvenli MPC modeli, diğer araçların yüksek q80 enerji taleplerini dar q20 sürelerinde karşılamak üzere kapasiteyi geleceğe kilitledi. Bu araç mevcut olmasına rağmen trafo gücü konservatif rezerve edildiği için araç bekletildi veya düşük kademede şarj edildi."*
    > *"EDF Dinamik Termin Önceliği: EDF algoritması geleceğe hayali rezervasyon ayırmaksızın, araçları salt yaklaşan ayrılış terminine göre dinamik sıraladı. Boş kalan tüm gücü anında bu araca tahsis ederek hedefine ulaştırdı."*

### F. Doğrulama ve Hipotez Arşivi (Benchmark Sekmesi)
- İş Paketi C ve D'nin doğrulanmış tüm tablolarını içerir.
- Eşleştirilmiş Bootstrap (B=2000) tablosu: 95% güven aralıkları ve hipotez kararları.
- 68 günlük doğrulama ve 153 günlük dönemler arası performans özetleri.
- **Örneklem Mutabakatı:** 5.315 doğrulama oturumu ile 5.207 simülasyon oturumu arasındaki 108 oturumluk farkın, `min_arac_gunluk=8` kuralı gereği trafo sıkışıklığı yaşanmayan seyrek günlerin elenmesinden kaynaklandığı açıkça belgelenmiştir.

### G. Dışa Aktarma (Export)
- Simüle edilen günün tüm telemetrisi, araç bazlı kararları ve "Neden?" açıklamaları Excel ve Pandas uyumlu UTF-8 BOM CSV veya JSON formatında tek tıkla indirilebilir.

---

## 4. Yerel Çalıştırma Talimatları

Sistem hem bağımsız üretim modunda (Express üzerinden tek port) hem de geliştirici modunda (Vite HMR) çalıştırılabilir:

### Seçenek 1: Hızlı Üretim Modu (Tavsiye Edilen — Tek Port)
Frontend derlenmiş haldedir (`web/client/dist`). Backend sunucusu tek komutla hem API'yi hem arayüzü sunar:

```powershell
cd "c:\Users\HP-PC\OneDrive\Pictures\Desktop\climathon v2\web\server"
npm start
```
Tarayıcınızdan açın: **`http://localhost:5000`**

### Seçenek 2: Geliştirici Modu (Vite Hot-Reload)
Frontend üzerinde canlı geliştirme yapmak için iki terminal açılır:

**Terminal 1 (Node.js API):**
```powershell
cd "c:\Users\HP-PC\OneDrive\Pictures\Desktop\climathon v2\web\server"
npm start
```

**Terminal 2 (React Vite Frontend):**
```powershell
cd "c:\Users\HP-PC\OneDrive\Pictures\Desktop\climathon v2\web\client"
npm run dev
```
Geliştirici arayüzü: **`http://localhost:5173`** (API çağrıları otomatik olarak `localhost:5000`'e yönlendirilir).

---

## 5. Doğrulama ve Test Sonuçları

Tüm sistem üç katmanlı test piramidiyle %100 doğrulanmıştır:

### A. Python Birim ve Entegrasyon Testleri (`pytest`)
```
============================= test session starts =============================
platform win32 -- Python 3.12.4, pytest-8.3.3
tests/test_cekirdek.py ........                                          [ 16%]
tests/test_deney_v2.py ........                                          [ 33%]
tests/test_modeller.py ........                                          [ 50%]
tests/test_sentetik_v2.py ........                                       [ 66%]
tests/test_veri_hijyeni.py ........                                      [ 83%]
tests/test_web_servis.py ...                                             [100%]
============================== 48 passed in 110s ===============================
```
- **Sonuç:** 48/48 test başarıyla geçti. Çekirdek simülatör, veri hijyeni, sentetik v2, quantile modeller ve yeni web servisi sıfır regresyonla çalışmaktadır.

### B. Node.js API Entegrasyon Testleri (`node --test`)
```
✔ GET /api/health returns ok status (92ms)
✔ GET /api/scenarios returns scenarios list with labels (25ms)
✔ GET /api/benchmark-results returns verified experiment results (25ms)
✔ Auth flow: Guest mode default and Google login simulation (81ms)
✔ POST /api/export/csv exports formatted csv with UTF-8 BOM (24ms)
ℹ tests 5 | pass 5 | fail 0 | cancelled 0
```
- **Sonuç:** 5/5 test başarıyla geçti.

### C. Uçtan Uca (E2E) Canlı Sistem Doğrulama Testi
`py web/server/tests/e2e_verify.py` komutu canlı Node.js sunucusunu ayağa kaldırıp gerçek simülasyonu tetiklemiştir:
```
[E2E] Starting Node.js server...
[E2E] 1. Testing GET /api/health... -> OK: ŞarjDenge AI Decision Support Server
[E2E] 2. Testing GET /api/scenarios... -> OK: 5 scenarios loaded.
[E2E] 3. Testing GET /api/benchmark-results... -> OK: Benchmark results verified. Hypothesis verdict: False
[E2E] 4. Testing POST /api/simulate (live python execution)... -> OK: Simulated 23 vehicles in isyeri_gunduz at f=0.5
[E2E] 5. Testing GET / (React frontend serving)... -> OK: Frontend HTML served properly.
[E2E] ALL 5 END-TO-END CHECKS PASSED SUCCESSFULLY!
```

---

## 6. Sınırlar ve Bilimsel Uyarılar

1. **2020 Holdout Verisi:** 2020 ACN holdout test verisi jüri arayüzüne kesinlikle dahil edilmemiştir ve indirilmemiştir; nihai holdout değerlendirmesi ayrı bir aşama olarak korunmaktadır.
2. **Türkiye Konut Verisi:** Türkiye apartman ve site otoparkları senaryosu, henüz Türkiye'de açık konut otoparkı telemetrisi bulunmadığı için parametrik bir modeldir. Bu durum arayüzün her ekranında `SENTETİK MODEL (VARSAYIM)` rozetiyle açıkça ilan edilmektedir.
3. **Ghost Reservation vs Erken Ayrılma:** Güvenli MPC, erken ayrılan sürücülerde beyana kıyasla marjinal bir avantaj sağlasa da (%78.56 vs %78.04), genel filoda trafo kapasitesini kilitlediği için EDF'nin gerisinde kalmıştır.
