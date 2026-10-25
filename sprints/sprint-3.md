# Sprint 3 — 2020 Holdout Değerlendirmesi, Türkiye Senaryoları ve Web Karar Destek Arayüzü

**Tarih Aralığı:** 11 Ekim 2026 – 17 Ekim 2026  
**Roller (Tek Kişilik Ekip):** Büşra Demir (Product Owner, Scrum Master, Developer)  
**Sprint Hedefi:** Dokunulmamış 2020 Holdout veri setinde bilimsel hipotez testlerini yürütmek, Türkiye elektrikli araç şarj alışkanlıklarını temsil eden sentetik senaryoları modellemek ve karar vericiler için modern bir React 18 + Node.js web arayüzü inşa etmek.

---

## 📋 Sprint 3 Product Backlog

| # | User Story / Görev | SP | Sorumlu | Durum |
|---|---|:---:|---|:---:|
| 1 | 2020 Holdout (4.043 oturum, 108 gün-saha) bağımsız hipotez ve küme bootstrap testi | 8 | Büşra | ✅ Tamamlandı |
| 2 | Türkiye sentetik senaryoları (`sarjdenge/sentetik_v2.py`, `turkiye.py` apartman & kampüs) | 7 | Büşra | ✅ Tamamlandı |
| 3 | Node.js Express API katmanı (`web/server/`) ve Python CLI köprüsü | 8 | Büşra | ✅ Tamamlandı |
| 4 | React 18 + Tailwind CSS + Lucide Icons kullanıcı paneli iskeleti | 8 | Büşra | ✅ Tamamlandı |
| 5 | 24 saatlik 96 adımlı interaktif güç eğrisi (`PowerCurveChart.jsx`) ve Gantt şeması | 8 | Büşra | ✅ Tamamlandı |
| 6 | Araç bazlı şarj telemetrisi ve "Neden Güç Kısıldı?" açıklanabilirlik paneli | 6 | Büşra | ✅ Tamamlandı |

**Toplam Tahmini:** 45 SP | **Tamamlanan:** 45 SP | **Kalan:** 0 SP

---

## 📝 Günlük Seyir Defteri (Daily Scrum)

- **Gün 1–2:** 2020 Holdout kümesi değerlendirildi. $f=0.5$'te fark $-1.35$ puan, takvim-günü küme bootstrap aralığı $[-2.48, -0.23]$ çıktı. Ana hipotezin reddedildiği kesinleşti. Sonuçlar bilimsel dürüstlükle raporlandı.
- **Gün 3–4:** Türkiye'deki konut ve iş yeri parklanma verilerine dayalı sentetik profiller modellendi. Apartman senaryosunda gece uzun parklanma nedeniyle bilginin değerinin azaldığı, dinamik paylaşımla 15 kW trafonun 20 araca yettiği gözlendi.
- **Gün 5–7:** Streamlit arayüzü yerine kurumsal seviyede React + Express mimarisine geçildi. Python alt süreci çağıran güvenli API rotaları kodlandı. Interaktif grafikler ve açıklanabilirlik kartları eklendi.

---

## 🔍 Sprint Review

- **Tamamlanan Çıktılar:**
  - `docs/HOLDOUT_2020_DEGERLENDIRME_RAPORU.md` yayımlandı.
  - `web/server` ve `web/client` tam entegre çalışır hale getirildi.
  - 4 senaryo (ACN Val, ACN TA, Karma Yerleşke, İş Yeri Kampüsü) web üzerinde canlı simüle edildi.
- **Kullanıcı Geri Bildirimi:** Simülasyonun etkileyici olduğu ancak site yöneticisinin asıl öğrenmek istediği şeyin "Bana kaç kW trafo lazım?" sorusu olduğu netleşti.

---

## 🔄 Sprint Retrospective

- **Güçlü Yönler:** React + Node.js mimarisine geçişin sağladığı yüksek hız, estetik ve profesyonel görünüm.
- **Geliştirilecek Yönler:** Sabit trafo oranları üzerinden simülasyon yapmak yerine, hedefi sağlayan minimum gücü otomatik arayan bir algoritma eksik.
- **Sprint 4 Kararı:** "Canlı Kapasite Danışmanı" (Capacity Advisor) motorunun yazılması, simülasyon girdi indekslemesinin denetlenmesi ve üretim dağıtımı.
