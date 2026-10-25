# Sprint 1 — Problem Tanımı, Veri Hijyeni ve Temel Simülatör

**Tarih Aralığı:** 27 Eylül 2026 – 03 Ekim 2026  
**Roller (Tek Kişilik Ekip):** Büşra Demir (Product Owner, Scrum Master, Developer)  
**Sprint Hedefi:** Ham ACN-Data şarj oturumlarında bilgi sızıntısını önleyen fiziksel hijyen şelalesini kurmak ve 15 dakikalık adımlarla kural tabanlı (FCFS, EDF, LLF) şarj simülatörünü hayata geçirmek.

---

## 📋 Sprint 1 Product Backlog

| # | User Story / Görev | SP | Sorumlu | Durum |
|---|---|:---:|---|:---:|
| 1 | Ham ACN-Data (32.509 oturum) veri temizleme kurallarının (`hijyen.yaml`) kodlanması | 8 | Büşra | ✅ Tamamlandı |
| 2 | Sürücü bağlantı anı ilk beyanını (`requestedDeparture_ilk`, `kWhRequested_ilk`) yakalayan yükleyici | 5 | Büşra | ✅ Tamamlandı |
| 3 | Sızıntısız kullanıcı geçmişi çıkarımı (`strict_shift=True`, geçmiş seansları kaydırma) | 5 | Büşra | ✅ Tamamlandı |
| 4 | 15 dakikalık zaman adımlı temel simülasyon döngüsü (`sarjdenge/sim.py`) | 8 | Büşra | ✅ Tamamlandı |
| 5 | Kural tabanlı planlayıcılar: FCFS (İlk Gelen), EDF (Erken Ayrılacak Olan), LLF (En Az Esneklik) | 5 | Büşra | ✅ Tamamlandı |
| 6 | Ayrık şarj kademeleri (0, 1.66, 3.33, 4.99, 6.66 kW) ve sıfır kapasite ihlali assertion testi | 4 | Büşra | ✅ Tamamlandı |

**Toplam Tahmini:** 35 SP | **Tamamlanan:** 35 SP | **Kalan:** 0 SP

---

## 📝 Günlük Seyir Defteri (Daily Scrum)

Tek kişilik ekip modelinde Daily Scrum, her sabah yazılı teknik seyir defteri (engineering log) formatında yürütülmüştür:
- **Gün 1–2:** ACN-Data portalı veri yapısı incelendi. Sürücülerin ayrılış zamanını güncelleyebildiği fark edildi; geleceğe yönelik bilgi sızıntısını (leakage) önlemek için yalnızca `_ilk` kayıtlarının kullanılması kuralı getirildi.
- **Gün 3–4:** 30 dakikadan kısa, 48 saatten uzun ve 0.5 kWh altı oturumlar temizlendi. 14.219 fiziksel temiz oturum elde edildi.
- **Gün 5–7:** 15 dakikalık zaman adımlı simülatör yazıldı. FCFS ve EDF kuralları test edildi. Şebeke tavanı aşıldığında sistemin hata fırlattığı doğrulanarak sıfır ihlal kuralı garantilendi.

---

## 🔍 Sprint Review

- **Tamamlanan Çıktılar:**
  - `sarjdenge/data.py` ve `sarjdenge/veri_hijyeni.py` tamamlandı.
  - 14.219 oturumluk temiz veri seti oluşturuldu.
  - Temel kural tabanlı simülatör ve 10 çekirdek birim testi geçti.
- **Demo:** Kontrolsüz tepe gücünün $f=0.5$ kapasite kısıtı altında FCFS ve EDF ile tepe tıraşlama davranışı doğrulandı.

---

## 🔄 Sprint Retrospective

- **Güçlü Yönler:** Veri hijyeni kurallarının kaynak koddan soyutlanıp YAML dosyasına dökülmesi temiz bir mimari sağladı.
- **Geliştirilecek Yönler:** Kural tabanlı yöntemlerin gelecekteki ayrılışları ve belirsizlikleri hesaba katamadığı görüldü.
- **Sprint 2 Kararı:** Kullanıcı kalış süresi ve enerji ihtiyacını olasılıksal tahmin eden Quantile Regresyon ve HiGHS LP-MPC motoruna geçilmesi kararlaştırıldı.
