# ŞarjDenge AI — Veri Manifestosu (`data/MANIFEST.md`)

Bu belge çalışma alanında tespit edilen tüm ham ACN-Data CSV dosyalarını, bütünlük özetlerini (SHA-256) ve içerik eşleşmelerini belgeler.

## 1. Tespit Edilen Ham Dosyalar Tablosu

| Dosya Adı | Satır Sayısı | Benzersiz sessionID | connectionTime Başlangıç | connectionTime Bitiş | SHA-256 Özeti |
|:---|:---:|:---:|:---|:---|:---|
| `acn_ocak_temmuz.csv` | 14,372 | 14,372 | 2018-12-31 21:12:43 UTC | 2019-06-30 20:51:54 UTC | `3e6e6aa2a199a7c11600d6620ecec3b68043b54818e41ec417ca991110df635e` |
| `acn_oturumlar_ocak_haziran.csv` | 14,372 | 14,372 | 2018-12-31 21:12:43 UTC | 2019-06-30 20:51:54 UTC | `3e6e6aa2a199a7c11600d6620ecec3b68043b54818e41ec417ca991110df635e` |
| `acn_oturumlar_temmuz_aralik.csv` | 13,584 | 13,584 | 2019-06-30 22:06:14 UTC | 2019-12-30 20:54:20 UTC | `d71566824db127c4f07d115e0502d1b3eaf72a45e8a1cae1bb49debca2ece230` |
| `acn_oturumlar_v2.csv` | 14,372 | 14,372 | 2018-12-31 21:12:43 UTC | 2019-06-30 20:51:54 UTC | `3e6e6aa2a199a7c11600d6620ecec3b68043b54818e41ec417ca991110df635e` |

## 2. İçerik Eşleşmesi ve Çift Kopya Analizi

- ⚠️ **AYNI İÇERİK UYARISI:** `acn_ocak_temmuz.csv, acn_oturumlar_ocak_haziran.csv, acn_oturumlar_v2.csv` dosyaları birebir aynı SHA-256 özetine (`3e6e6aa2a199...`) sahiptir.

> **Önemli Sonuç:** `acn_ocak_temmuz.csv`, `acn_oturumlar_ocak_haziran.csv` ve `acn_oturumlar_v2.csv` üç farklı veri seti değildir; Ocak–Haziran 2019 dönemini temsil eden aynı verinin kopyalarıdır.

## 3. `data/ham/` Dizinine Alınan Kopyalar

Orijinal dosyalar korunmuş; aşağıdaki standart arşiv kopyaları oluşturulmuştur:

- `data/ham/acn_20181231_20190630.csv`
- `data/ham/acn_20190630_20191230.csv`

## 4. Doğrulanmış Saha ve siteID Kodlaması

ACN-Data API çekim logları (`acn_veri_cek.py`) ve ham CSV blokları incelenerek siteID kodlaması kesinleştirilmiştir:

| siteID | Kurum / Saha Adı | Açıklama | Oca–Haz 2019 Ham | Tem–Ara 2019 Ham |
|:---:|:---|:---|:---:|:---:|
| `1` | **JPL** (Jet Propulsion Laboratory) | NASA AR-GE yerleşkesi | 8,610 | 8,734 |
| `2` | **Caltech** (California Institute of Technology) | Üniversite kampüsü | 5,762 | 4,850 |

> **Doğrulama Notu:** `acn_veri_cek.py` SAHALAR listesinde `caltech` ilk, `jpl` ikinci sırada çekilir. CSV dosyalarının ilk 5.762 (ve 4.850) satırının tamamında `siteID=2`, sonraki 8.610 (ve 8.734) satırının tamamında `siteID=1` yer almaktadır. Dolayısıyla `siteID=1` JPL, `siteID=2` Caltech'tir.
