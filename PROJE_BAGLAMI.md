# ŞarjDenge AI — Proje Bağlamı (ajan için)

## Amaç
Apartman sitesi ve iş yeri otoparklarında EV şarj gücünü, tesisin trafo/bağlantı kapasitesini
aşmadan planlayan sistem. Araç ayrılış zamanı ve enerji ihtiyacı tahmin edilir; MPC/optimizasyon
kapasite altında güç planı üretir. Climathon 2026 (Siemens + YGA + UP School), tek kişilik ekip,
final teslimi 25 Ekim 2026 23:59. Araştırma/prototip aşamasındadır; üstünlük KANITLANMAMIŞTIR.

## Dosyalar
- `acn_veri_cek.py` : ACN-Data (Caltech) oturumlarını çeker -> `acn_oturumlar_v2.csv`. Token yalnızca `ACN_TOKEN` ortam değişkeninden.
- `sarjdenge/data.py` : yükleme/temizleme/özellik. Beyan = bağlantıdan <=30 dk sonra girilen İLK kullanıcı girdisi.
- `sarjdenge/tahmin.py` : kantil gradient boosting (süre q20/q50, enerji q50/q80).
- `sarjdenge/sim.py` : 15 dk adımlı simülatör; kurallar fcfs/edf/llf; `mpc` (enerji-LP); `mpc_milp` (tamamlama odaklı MILP).
- `sarjdenge/deney.py` : ACN deneyi. ÖNCEDEN YAZILMIŞ KARAR KURALI: ana karşılaştırma `mpc_tahmin_guvenli - mpc_beyan`,
  eşik fark>=0,02 ve bootstrap %95 GA alt ucu>0. Bu kural sonuçlara bakıldıktan sonra DEĞİŞTİRİLMEZ.
- `sarjdenge/turkiye.py` : ETİKETLİ SENTETİK Türkiye apartman senaryosu üretici (varsayımlar dosyada).
- `sarjdenge/urun.py` : Türkiye senaryosunda kapasite taraması + tek gün ayrıntısı -> `demo_veri.json`.
- `sarjdenge/sentetik.py` : yalnızca kod testi içindir; sonuç değildir.
- `tests/test_cekirdek.py` : çekirdek değişmezleri.

## Bilinen bulgular (sentetik Türkiye senaryosu; ölçüm değil)
- Statik güç paylaşımı %95 araç hedefi için ~80 kW, dinamik yöntemler ~12 kW gerektirdi (20 soketli site).
- Gece uzun parkta bilgi kalitesi neredeyse değersiz (oracle bile beyandan iyi değil).
- Enerji-LP "hedefe ulaşan araç sayısı"nda FCFS'in gerisinde; MILP LP'den iyi, FCFS düzeyinde.
- Tahminin değeri kısa/belirsiz pencerelerde (iş yeri, ACN) aranmalı; gerçek ACN deneyi henüz koşulmadı.

## Bilinen tuhaflıklar (sessizce düzeltme, bana bildir)
- `data.TZ` modül düzeyinde global; `urun.kur()` onu Europe/Istanbul yapar, `sim.SEVIYELER`/`PMAX` de global değişir.
- Her gün bağımsız simüle edilir; önceki günden devreden araç yok.
- ACN'de "talep" = teslim edilen kWh (ACN'nin kendi planlayıcısının sonucu), gerçek talep değildir.
- MILP yavaştır (adım başına çözüm); büyük günlerde `--gun` ile sınırla.

## Dürüstlük kuralları
- Sentetik ile gerçek ayrı etiketlenir: "Sentetik senaryo, ölçüm değil".
- Sonuç uydurulmaz; veri yoksa arayüz açık uyarı gösterir.
- Önceden belirlenen hedefler sonuçlara göre sonradan değiştirilmez.
