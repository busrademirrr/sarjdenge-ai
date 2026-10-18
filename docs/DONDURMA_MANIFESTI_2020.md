# ŞarjDenge AI — Dondurulmuş Model ve Kod Manifesti (2020 Holdout Öncesi)

**Tarih:** 2026-10-17
**Amaç:** 2020-01-01 / 2020-03-01 ACN holdout test verisi çekilmeden ve değerlendirilmeden önce
tüm model ağırlıklarının, kodların, kuralların ve önceki deney sonuçlarının dondurulduğunu belgelemek.

| Dosya Yolu | Boyut (Byte) | SHA-256 Özeti | Durum |
| :--- | :---: | :--- | :---: |
| `ONKAYIT_2.md` | 4,904 | `cce9f51cc89525eaafcbff7854205e3bb27e8734c612343e45e28513d3d2f4bb` | DONDURULDU |
| `VERI_HAZIRLAMA_KURALLARI.md` | 6,036 | `85d8804036d41eb47401b09a7a0f729e15944248f9fa443ad9d14229e03ec072` | DONDURULDU |
| `data/hijyen.yaml` | 1,354 | `fe9ced58741be2d58ef4528e5d8b77f24c12593fb42240d74e0d5dca7361d410` | DONDURULDU |
| `config/senaryolar.yaml` | 11,120 | `7819bab168e5daa0b93af665cd34ca2c198e4260032509e54f5f5633247990be` | DONDURULDU |
| `data/MANIFEST.md` | 2,584 | `4c456fb2eccabcfa3351d3dbc4766569c0232cb43801aa8358ce252c561cdbb6` | DONDURULDU |
| `sarjdenge/modeller.py` | 21,355 | `494e695a71722b3fe4946714d945ca2dfe771119d259d796d812122b86c4344f` | DONDURULDU |
| `sarjdenge/veri_hijyeni.py` | 30,985 | `ee072dadf440e653df408a15a136d2872384dcd63309bb5203c52b1595aee236` | DONDURULDU |
| `sarjdenge/sentetik_v2.py` | 19,576 | `daa67921af0fc42a5d004ed112bfa28d46c2e0d257dde167712d1828988982d9` | DONDURULDU |
| `sarjdenge/sim.py` | 7,434 | `a912a7b39ea189bc3d939e9bc5505b7025c985c2bd4bd8606390f300221ae096` | DONDURULDU |
| `sarjdenge/deney_v2.py` | 12,229 | `bfdbd1cb889fdae3dd9e977b6b1e3988c0171d2fe819e2145448bf349b8727f3` | DONDURULDU |
| `sarjdenge/web_servis.py` | 24,037 | `27c4fa4a3747ad4be11c211bded3a8312e9472b358e1589df6c01ce0c127a212` | DONDURULDU |
| `sarjdenge/data.py` | 2,685 | `1cf8710e107014d23ce4e4af7be08c6dd5fb5bbd91af9b59e1490a160d6927e3` | DONDURULDU |
| `sarjdenge/tahmin.py` | 1,189 | `e1da1d66c96213048a4969af8565ccc8c2b9050f83a8ecb96ad78bcfb48906f0` | DONDURULDU |
| `sarjdenge/deney.py` | 15,165 | `f1ec7640d7c826cfb3b46248086990837469af270aea6956eb1d38c494383c50` | DONDURULDU |
| `sarjdenge/turkiye.py` | 3,775 | `286094405702a55af2fa502fb907331e12f838d781c469bb6175b6d5762f87fb` | DONDURULDU |
| `sarjdenge/sentetik.py` | 1,998 | `21a8b7136a71d390b68343690cd64a431a68ca8d50e7dfd6866062df8d9d0f65` | DONDURULDU |
| `data/deney_tablo_val.csv` | 3,489 | `cd744bfaed17a820df20079b6601c95ebebc3c279906de975a8e66520e4334de` | DONDURULDU |
| `data/deney_boot_val.csv` | 3,503 | `8bedd42cad0ff478d5f20b5983f4d1502f960d5e00bba47a55351355002020f7` | DONDURULDU |
| `data/deney_tablo_ta.csv` | 3,545 | `719c33eb0829f0a0f0fda141c5bf91c54854a980bab65544150139d099f94102` | DONDURULDU |
| `data/deney_boot_ta.csv` | 3,619 | `9eaadf075b1d3ddb8144a141854437abc57440f7c5e58bd84d5c39d79db39fd5` | DONDURULDU |

---
### Dondurma ve Kör Test Garantisi
1. Yukarıda listelenen dosyaların hiçbirinde 2020 holdout verisi çekildikten sonra değişiklik yapılamaz.
2. 2020 verisi model seçimi, hiperparametre optimizasyonu veya eşik ayarı için kullanılamaz.
3. Ön kayıtlı ana hipotez kuralı (Δ ≥ +0.02, %95 GA alt ucu > 0, q80 kapsam toleransı %80 ± 3 y.p.) aynen korunur.
