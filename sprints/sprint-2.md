# Sprint 2 — Quantile ML Modelleri, HiGHS LP-MPC ve Ön Kayıt Protokolü

**Tarih Aralığı:** 04 Ekim 2026 – 10 Ekim 2026  
**Roller (Tek Kişilik Ekip):** Büşra Demir (Product Owner, Scrum Master, Developer)  
**Sprint Hedefi:** Kullanıcı belirsizliklerini olasılıksal modelleyen Quantile Regresyon modellerini geliştirmek, SciPy HiGHS doğrusal programlama (LP) tabanlı MPC çözücüsünü entegre etmek ve ana araştırma hipotezini önceden kilitlemek.

---

## 📋 Sprint 2 Product Backlog

| # | User Story / Görev | SP | Sorumlu | Durum |
|---|---|:---:|---|:---:|
| 1 | Boyutsuzlaştırma ve özellik mühendisliği (`s_sure=336.71 dk`, `s_kwh=11.13 kWh`) | 5 | Büşra | ✅ Tamamlandı |
| 2 | Gradient Boosting Quantile Regressor: Süre ($q_{20}, q_{50}$) ve Enerji ($q_{50}, q_{80}$) | 8 | Büşra | ✅ Tamamlandı |
| 3 | Quantile crossing (kuantil çakışması) düzeltmesi ve monotonlaştırma | 4 | Büşra | ✅ Tamamlandı |
| 4 | SciPy `linprog` (HiGHS) tabanlı Model Öngörülü Kontrol (LP-MPC) optimizasyon motoru | 10 | Büşra | ✅ Tamamlandı |
| 5 | Ön Kayıt Protokolü (`ONKAYIT_2.md`): Ana karar kuralı ve bootstrap eşiklerinin kilitlenmesi | 5 | Büşra | ✅ Tamamlandı |
| 6 | 2019 H1 eğitim/doğrulama kümesinde ($N=5.207$) eşleştirilmiş bootstrap ($B=2000$) deneyi | 8 | Büşra | ✅ Tamamlandı |

**Toplam Tahmini:** 40 SP | **Tamamlanan:** 40 SP | **Kalan:** 0 SP

---

## 📝 Günlük Seyir Defteri (Daily Scrum)

- **Gün 1–2:** Sürücülerin beyan ettikleri enerji ile teslim edilen enerji arasındaki fark analiz edildi. Beyanların teslim edilen enerjiyi ortalama $+10.19$ kWh abarttığı tespit edildi.
- **Gün 3–4:** Scikit-learn tabanlı `GradientBoostingRegressor(loss="quantile")` eğitildi. Enerji MAE'si kullanıcı beyanında 10.40 kWh iken modelde 3.49 kWh'ye düşürüldü.
- **Gün 5–6:** Rolling-horizon prensibiyle 15 dakikada bir çözülen HiGHS LP-MPC entegre edildi. Erken şarja küçük bir ağırlık indirim katsayısı ($w_0 = 1.0 \to w_H = 0.5$) verildi.
- **Gün 7:** Ön kayıt dokümanı donduruldu. Ana hipotez: $\Delta = \text{mpc\_tahmin\_guvenli} - \text{mpc\_beyan} \ge +0.02$ ve %95 GA alt sınırı $> 0$.

---

## 🔍 Sprint Review

- **Tamamlanan Çıktılar:**
  - `sarjdenge/tahmin.py` ve `sarjdenge/modeller.py` tamamlandı.
  - HiGHS çözücüsü saniyede yüzlerce LP alt problemini sıfır ihlalle çözdü.
  - Ön kayıtlı karar kuralı resmileştirildi.
- **İlk Bulgular:** 2019 doğrulamasında $f=0.5$ için $\Delta = -2.22$ puan çıktı; model hatası düşmesine rağmen şarj başarısı beyanın gerisinde kaldı.

---

## 🔄 Sprint Retrospective

- **Güçlü Yönler:** LP-MPC çözücüsünün HiGHS ile olağanüstü hızlı ve kararlı çalışması.
- **Geliştirilecek Yönler:** Tahminin neden daha iyi şarj sonucu üretmediği araştırılmalı ("hayalet rezervasyon" mekanizması).
- **Sprint 3 Kararı:** Dokunulmamış 2020 Holdout kümesinde doğrulama yapılması ve sonuçların karar vericilere interaktif sunulacağı modern bir Web UI geliştirilmesi.
