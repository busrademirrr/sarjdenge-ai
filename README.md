# ŞarjDenge AI: deney paketi (v0.1)

Soru: Aynı MPC, sürücü beyanı yerine tahmin edilen ayrılış ve enerjiyle çalışınca, kapasite kısıtı altında
araçların zamanında hedefe ulaşma oranı artıyor mu?

## Kurulum (PowerShell)

> **SSL sertifika sorunu varsa** (`CERTIFICATE_VERIFY_FAILED`) aşağıdaki komutu kullanın:

```powershell
py -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

Normal ağda yeterli olan komut:

```powershell
py -m pip install -r requirements.txt
```

## Adımlar

1. `$env:ACN_TOKEN = "anahtarınız"` (kodun içine yazmayın)
2. `py acn_veri_cek.py` → `acn_oturumlar_v2.csv` (ilk ve son kullanıcı girdisini kaydeder)
3. `py -m pytest -q` → tüm testlerin geçtiğini doğrula
4. `py -m sarjdenge.deney --csv acn_oturumlar_v2.csv --gun 5` (hızlı deneme), sonra `--gun` olmadan tam çalıştırma
   → `sonuclar.md`, `gunluk_sonuclar.csv`, `grafik.png`
5. `py -W ignore -m sarjdenge.urun --uret` → `demo_veri.json` (Türkiye sentetik senaryosu)
6. `py -m streamlit run arayuz.py` → arayüzü tarayıcıda aç

### Yalnızca arayüzü denemek (ACN verisi olmadan)

```powershell
py -W ignore -m sarjdenge.urun --uret   # demo_veri.json üretir (~30 sn)
py -m streamlit run arayuz.py
```

## Tasarım kararları
- Simülasyon 15 dk adımlı; araç gücü ayrık seviyelerde: 0, 8, 16, 24, 32 A x 208 V (ACN temel EVSE).
- Talep = teslim edilen kWh (ACN'nin kendi planlayıcısının sonucu; gerçek talep değil). ok = teslim >= %95 talep.
- Beyan = bağlantıdan en geç 30 dk sonra girilen İLK kullanıcı girdisi (sonradan güncellenen girdi sızıntı yaratır).
- Tahmin yalnızca bağlantı anında bilinen özelliklerle; zaman sırasıyla bölme (ilk %60 gün eğitim, kalan test).
- Her gün bağımsız simüle edilir; önceki günden devreden araç yok (sınırlama).
- Her saha ayrı ağ; kapasite = günün kontrolsüz tepe gücünün f katı (f = 0,5 / 0,7 / 0,9).
- Kapasite ihlali olursa program hata verir (sıfır ihlal zorunlu).
- MPC: doğrusal program (scipy HiGHS), toplam enerjiyi maksimize eder, erken şarja küçük ağırlık verir;
  ilk adım ayrık seviyeye aşağı yuvarlanır, artan kapasite kesir kaybı en büyük araçlara dağıtılır.

## Önceden yazılmış karar kuralı (sonuçlara bakmadan)
Ana karşılaştırma: `mpc_tahmin_guvenli - mpc_beyan` (zamanında hedef oranı farkı).
Eşik: fark >= 0,02 ve günler üzerinden bootstrap %95 GA alt ucu > 0.
`tahmin_guvenli` = (süre q20, enerji q80); `tahmin_ortanca` = (süre q50, enerji q50, ikincil).
Not: `tahmin_guvenli` tanımındaki enerji q80, sentetik veriyle yapılan kod testinden sonra (gerçek veriye bakmadan) seçildi.

## Sınırlamalar
ACN işyeri verisidir; Türkiye konut senaryosu ayrı ve sentetik olarak etiketlenmelidir.
`sentetik.py` yalnızca kod testi içindir; ürettiği sayılar sonuç değildir.

## Güncelleme (14 Ekim): Türkiye senaryosu ve tamamlama odaklı planlayıcı
- `py -W ignore -m sarjdenge.urun --uret` : etiketli sentetik Türkiye apartman senaryosu + kapasite taraması (demo_veri.json).
- Bulgu (sentetik, ölçüm değil): gece uzun park edildiğinde bilgi kalitesi neredeyse değersiz; mükemmel bilgi (oracle)
  bile beyandan iyi değil. Enerji-LP planlayıcı "hedefe ulaşan araç sayısı"nda FCFS'in gerisinde (enerjiyi yayıyor).
  Tamamlama odaklı MILP (`sim.mpc_milp`) LP'den belirgin iyi, FCFS düzeyinde.
- Tahminin değeri kısa/belirsiz park pencerelerinde (iş yeri) aranmalı: `py -W ignore -m sarjdenge.deney --csv acn_oturumlar_v2.csv --gun 5 --milp`
