# Sprint 4 — Canlı Kapasite Danışmanı, Bilimsel Denetim, E2E Testler ve Dağıtım

**Tarih Aralığı:** 18 Ekim 2026 – 25 Ekim 2026  
**Roller (Tek Kişilik Ekip):** Büşra Demir (Product Owner, Scrum Master, Developer)  
**Sprint Hedefi:** İkili arama tabanlı Kapasite Danışmanı motorunu geliştirmek, kod ve veri indeksleme denetimini (erratum) tamamlamak, 17/17 Playwright E2E test otomasyonunu kurmak ve projeyi üretim ortamına taşımak.

---

## 📋 Sprint 4 Product Backlog

| # | User Story / Görev | SP | Sorumlu | Durum |
|---|---|:---:|---|:---:|
| 1 | İkili arama (binary search) tabanlı "Canlı Kapasite Danışmanı" algoritması (`web_servis.py`) | 10 | Büşra | ✅ Tamamlandı |
| 2 | Tek Günlük Hızlı Mod (10 sn) ve Çok Günlü ($\ge 20$ Gün) analiz modu | 8 | Büşra | ✅ Tamamlandı |
| 3 | Fiziksel imkânsız araçların tespiti ve başarı kriterinin karşılanabilir araçlara uyarlanması | 5 | Büşra | ✅ Tamamlandı |
| 4 | 22 Ekim simülasyon girdi indeksleme hatasının tespiti, düzeltilmesi ve erratum raporu | 5 | Büşra | ✅ Tamamlandı |
| 5 | Playwright gerçek tarayıcı E2E testleri (Kapasite Danışmanı ve Hipotez sekmeleri) | 8 | Büşra | ✅ Tamamlandı |
| 6 | Üretim Dockerfile, .dockerignore ve Cloudflare Tunnel canlı dağıtım rehberi (`DEPLOY.md`) | 6 | Büşra | ✅ Tamamlandı |

**Toplam Tahmini:** 42 SP | **Tamamlanan:** 42 SP | **Kalan:** 0 SP

---

## 📝 Günlük Seyir Defteri (Daily Scrum)

- **Gün 1–2:** Kapasite Danışmanı ikili arama motoru geliştirildi. $\%95$ tamamlama ve $\le 1$ kaçırılan kriteri altında asgari kW değeri 0.5 kW hassasiyetle hesaplandı.
- **Gün 3:** 22 Ekim'de simülasyon girdi indekslemesinde bir kayma tespit edildi; düzeltildi ve `docs/ERRATUM_2026-10-22.md` belgelendi.
- **Gün 4–5:** Çok günlü modda 20 günlük analiz hızlandırıldı; sentetik senaryolarda ön tarama ile süre 9 saniyeye indirildi. Fiziksel olarak şarj olması imkânsız araçlar ayrıştırıldı.
- **Gün 6–7:** Playwright E2E testleri (17/17) başarıyla geçti. Dockerfile ve `.dockerignore` hazırlandı. Yerel kaynak ölçümleri alındı (~220 MB RAM, 10 sn istek). Final teslim dokümantasyonu tamamlandı.

---

## 🔍 Sprint Review

- **Tamamlanan Çıktılar:**
  - Canlı Kapasite Danışmanı arayüzü ve API'si kusursuz çalıştı.
  - 56/56 Pytest, 8/8 Server Testi ve 17/17 Playwright E2E testi %100 yeşil.
  - Tek komutla canlıya çıkış imkânı sunan Docker ve Cloudflare Tunnel yapılandırması hazırlandı.
- **Canlı Ölçüm Başarısı:** Tek günlük Kapasite Danışmanı 10.9 saniyede, Canlı Simülasyon 4.4 saniyede 200 OK ile yanıt üretti.

---

## 🔄 Sprint Retrospective

- **Güçlü Yönler:**
  - Tek kişilik ekip olmasına rağmen veri mühendisliğinden E2E test otomasyonuna kadar kurumsal standartta bir ürün ortaya kondu.
  - Bilimsel dürüstlükten taviz verilmedi; önkayıtlı hipotez sonuçları net ve şeffaf şekilde sunuldu.
  - "Kapasite Danışmanı" özelliği projeyi soyut bir algoritmadan doğrudan site yöneticilerinin satın alma kararına rehberlik eden somut bir SaaS ürününe dönüştürdü.
- **Gelecek Vizyonu:**
  - OCPP 2.0.1 entegrasyonu ile sahadaki şarj istasyonlarına doğrudan gerçek zamanlı akım komutu gönderme.
  - Dinamik elektrik tarifeleri (gün öncesi piyasası) ile maliyet optimizasyonunun eklenmesi.
