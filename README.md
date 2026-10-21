# ┼ŞarjDenge AI: deney paketi (v0.1)

Soru: Ayn─▒ MPC, s├╝r├╝c├╝ beyan─▒ yerine tahmin edilen ayr─▒l─▒┼ş ve enerjiyle ├ğal─▒┼ş─▒nca, kapasite k─▒s─▒t─▒ alt─▒nda
ara├ğlar─▒n zaman─▒nda hedefe ula┼şma oran─▒ art─▒yor mu?

## Kurulum (PowerShell)

> **SSL sertifika sorunu varsa** (`CERTIFICATE_VERIFY_FAILED`) a┼şa─ş─▒daki komutu kullan─▒n:

```powershell
py -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

Normal a─şda yeterli olan komut:

```powershell
py -m pip install -r requirements.txt
```

## Ad─▒mlar

1. `$env:ACN_TOKEN = "anahtar─▒n─▒z"` (kodun i├ğine yazmay─▒n)
2. `py acn_veri_cek.py` ÔåÆ `acn_oturumlar_v2.csv` (ilk ve son kullan─▒c─▒ girdisini kaydeder)
3. `py -m pytest -q` ÔåÆ t├╝m testlerin ge├ğti─şini do─şrula
4. `py -m sarjdenge.deney --csv acn_oturumlar_v2.csv --gun 5` (h─▒zl─▒ deneme), sonra `--gun` olmadan tam ├ğal─▒┼şt─▒rma
   ÔåÆ `sonuclar.md`, `gunluk_sonuclar.csv`, `grafik.png`
5. `py -W ignore -m sarjdenge.urun --uret` ÔåÆ `demo_veri.json` (T├╝rkiye sentetik senaryosu)
6. `py -m streamlit run arayuz.py` ÔåÆ aray├╝z├╝ taray─▒c─▒da a├ğ

### Yaln─▒zca aray├╝z├╝ denemek (ACN verisi olmadan)

```powershell
py -W ignore -m sarjdenge.urun --uret   # demo_veri.json ├╝retir (~30 sn)
py -m streamlit run arayuz.py
```

## Tasar─▒m kararlar─▒
- Sim├╝lasyon 15 dk ad─▒ml─▒; ara├ğ g├╝c├╝ ayr─▒k seviyelerde: 0, 8, 16, 24, 32 A x 208 V (ACN temel EVSE).
- **Talep ve Enerji Tan─▒m─▒:** ACN verisindeki `kWhDelivered` de─şeri arac─▒n ger├ğek toplam batarya ihtiyac─▒/kapasitesi DE─Ş─░L; o ┼şarj oturumunda EVSE taraf─▒ndan araca fiilen teslim edilmi┼ş enerjidir (tarihsel teslim enerjisi / ihtiya├ğ g├Âstergesi). Hedef tamamlama kriteri: `ok = teslim >= %95 talep`.
- Beyan = ba─şlant─▒dan en ge├ğ 30 dk sonra girilen ─░LK kullan─▒c─▒ girdisi (sonradan g├╝ncellenen girdi s─▒z─▒nt─▒ yarat─▒r).
- Tahmin yaln─▒zca ba─şlant─▒ an─▒nda bilinen ├Âzelliklerle; zaman s─▒ras─▒yla b├Âlme (ilk %60 g├╝n e─şitim, kalan test).
- Her g├╝n ba─ş─▒ms─▒z sim├╝le edilir; ├Ânceki g├╝nden devreden ara├ğ yok (s─▒n─▒rlama).
- Her saha ayr─▒ a─ş; kapasite = g├╝n├╝n sim├╝le edilen kontrols├╝z tepe g├╝c├╝n├╝n f kat─▒ (f = 0,5 / 0,7 / 0,9).
- Kapasite ihlali olursa program hata verir (s─▒f─▒r ihlal zorunlu).
- MPC: do─şrusal program (scipy HiGHS), toplam enerjiyi maksimize eder, erken ┼şarja k├╝├ğ├╝k a─ş─▒rl─▒k verir;
  ilk ad─▒m ayr─▒k seviyeye a┼şa─ş─▒ yuvarlan─▒r, artan kapasite kesir kayb─▒ en b├╝y├╝k ara├ğlara da─ş─▒t─▒l─▒r.

## ├ûnceden yaz─▒lm─▒┼ş karar kural─▒ ve Deneysel Sonu├ğ
- **Ana kar┼ş─▒la┼şt─▒rma:** `mpc_tahmin_guvenli - mpc_beyan` (zaman─▒nda hedef oran─▒ fark─▒).
- **E┼şik:** fark >= 0,02 (+2 y├╝zde puan─▒) ve g├╝nler ├╝zerinden bootstrap %95 GA alt ucu > 0.
- `tahmin_guvenli` = (s├╝re q20, enerji q80); `tahmin_ortanca` = (s├╝re q50, enerji q50, ikincil).
- **Deneysel Do─şrulama Sonucu:** Bu ana hipotez ne 2019 do─şrulama d├Âneminde ne de 2020 test d├Âneminde **desteklenmemi┼ş; s─▒f─▒r hipotezi reddedilememi┼ştir** (2019 do─şrulamas─▒nda f=0.5 i├ğin ╬ö = -0.17 yp, f=0.7 i├ğin ╬ö = -0.58 yp; 2020 testinde f=0.5 i├ğin ╬ö = -0.65 yp, f=0.7 i├ğin ╬ö = -0.82 yp). Bu de─şerlendirme k├╝mesinde dar ve orta kapasitelerde `edf_beyan` daha iyi sonu├ğ vermi┼ştir; makine ├Â─şrenmesi tahmin hatas─▒n─▒n d├╝┼şmesi otomatik olarak daha iyi bir planlama ba┼şar─▒s─▒na d├Ân├╝┼şmemi┼ştir.

## S─▒n─▒rlamalar ve Bilimsel S─▒n─▒rlar
- **Canl─▒ Web Servisi ve ├çevrimd─▒┼ş─▒ Model Ayr─▒m─▒:** Canl─▒ web aray├╝z├╝ ve API servisi (`sarjdenge/web_servis.py`), 2019 H1 e─şitim verisinden ├Â─şrenilen ampirik beyan oran─▒ kuantillerini (`config/beyan_oranlari.json`) ve HiGHS do─şrusal programlama (LP) optimizasyonunu kullan─▒r. ├çevrimd─▒┼ş─▒ ara┼şt─▒rma hatt─▒ndaki GBR ve HGB modelleri canl─▒ serviste do─şrudan model serile┼ştirmesiyle ├ğal─▒┼şt─▒r─▒lmamaktad─▒r.
- **ACN ve T├╝rkiye Senaryosu Ayr─▒m─▒:** ACN bir i┼şyeri ┼şarj a─ş─▒ verisidir (Caltech ve JPL). T├╝rkiye konut/apartman senaryolar─▒ (`sarjdenge/turkiye.py`, `sarjdenge/sentetik.py`, `sarjdenge/sentetik_v2.py`) **kesinlikle ger├ğek saha ├Âl├ğ├╝m├╝ de─şildir; kod tabanl─▒ sentetik senaryolard─▒r**.
- **2020 Verisi Durumu:** 2020 d├Ânemi (OcakÔÇô┼Şubat 2020) daha ├Ânce incelenmi┼ş ve de─şerlendirilmi┼ştir; gelecekteki model se├ğimi veya hiperparametre ayar─▒ i├ğin **dokunulmam─▒┼ş test seti olarak adland─▒r─▒lamaz ve kullan─▒lamaz**.
- **2021 ─░leriye D├Ân├╝k Deney S─▒n─▒r─▒:** ACN-Data portal─▒na eri┼şim sorunlar─▒ nedeniyle 2021 ileriye d├Ân├╝k veri envanteri ve deneyi ger├ğekle┼ştirilememi┼ştir; bu durum projenin g├╝ncel veri s─▒n─▒r─▒ olarak a├ğ─▒k├ğa belgelenmi┼ştir.
- **Ham Veri Say─▒lar─▒ Mutabakat─▒:**
  - 2019 H1: `acn_oturumlar_v2.csv` (`data/ham/acn_20181231_20190630.csv`) 14.372 ham veri sat─▒r─▒ (1 ba┼şl─▒k sat─▒r─▒ ile 14.373 sat─▒r) i├ğerir. Fiziksel hijyen sonras─▒ (-139 k─▒sa, -14 uzun, -0 d├╝┼ş├╝k enerji) 14.219 temiz oturum kal─▒r; beyan filtresiyle (-1.004 eksik, -92 gecikmi┼ş beyan) 13.123 ge├ğerli oturuma (7.808 e─şitim + 5.315 do─şrulama) ula┼ş─▒l─▒r.
  - 2019 H2: `acn_oturumlar_temmuz_aralik.csv` (`data/ham/acn_20190630_20191230.csv`) 13.584 ham veri sat─▒r─▒ (1 ba┼şl─▒k sat─▒r─▒ ile 13.585 sat─▒r) i├ğerir. Fiziksel hijyen sonras─▒ (-131 k─▒sa, -8 uzun) 13.445 temiz oturum, beyan filtresi sonras─▒ 12.298 ge├ğerli oturum kal─▒r.
  - 2020 Holdout: `data/holdout_2020_01_02/acn_holdout_20200101_20200301_ham.csv` 4.553 ham veri sat─▒r─▒ (1 ba┼şl─▒k sat─▒r─▒ ile 4.554 sat─▒r: 1.670 Caltech + 2.883 JPL) i├ğerir. `sarjdenge/veri_hijyeni.py` ile do─şrulanm─▒┼ş elemede -62 k─▒sa (<30 dk), -3 a┼ş─▒r─▒ uzun (>48 sa) ve -0 d├╝┼ş├╝k enerji (<0.5 kWh) elenerek 4.488 fiziksel temiz oturum; beyan filtresiyle (-379 eksik, -37 gecikmi┼ş) 4.072 ge├ğerli beyanl─▒ oturum elde edilir (eski bir ara taslakta ge├ğen 82/7/1 ara d─▒┼şlama say─▒lar─▒ ve 2.417 say─▒s─▒ kilitli ham CSV'den yeniden ├╝retilemedi─şi i├ğin resmi ┼şelaleyle birle┼ştirilmemi┼ştir).
- **Model Hatt─▒ Ayr─▒m─▒:** Projede iki model hatt─▒ bulunmaktad─▒r:
  1. `sarjdenge/tahmin.py`: v1 ├ğekirdek tahmincisi; `HistGradientBoostingRegressor(loss="quantile", max_iter=150, learning_rate=0.06, max_depth=4)` kullan─▒r ve s├╝re i├ğin `log1p` hedef d├Ân├╝┼ş├╝m├╝ uygular.
  2. `sarjdenge/modeller.py`: v2 model se├ğim hatt─▒; ┼şampiyon model olarak se├ğilen Scikit-learn `GradientBoostingRegressor(loss="quantile", n_estimators=60, max_depth=4)` + `SimpleImputer` pipeline'─▒n─▒ i├ğerir.

## G├╝ncelleme (14 Ekim): T├╝rkiye sentetik senaryosu ve tamamlama odakl─▒ planlay─▒c─▒
- `py -W ignore -m sarjdenge.urun --uret` : etiketli sentetik T├╝rkiye apartman senaryosu + kapasite taramas─▒ (demo_veri.json).
- Bulgu (tamamen sentetik sim├╝lasyon, saha ├Âl├ğ├╝m├╝ de─şil): Gece uzun park edildi─şinde bilgi kalitesi neredeyse de─şersiz; m├╝kemmel bilgi (oracle) bile beyandan iyi de─şil. Enerji-LP planlay─▒c─▒ "hedefe ula┼şan ara├ğ say─▒s─▒"nda FCFS'in gerisinde kalabilmektedir (enerjiyi yaymaktad─▒r). Tamamlama odakl─▒ MILP (`sim.mpc_milp`) LP'den belirgin iyi, FCFS d├╝zeyindedir.
- Tahminin de─şeri k─▒sa/belirsiz park pencerelerinde (i┼ş yeri) aranmal─▒d─▒r: `py -W ignore -m sarjdenge.deney --csv acn_oturumlar_v2.csv --gun 5 --milp`
