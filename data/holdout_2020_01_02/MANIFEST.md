# ŞarjDenge AI — 2020 Holdout Veri İndirme Manifesti

**İndirme Zamanı (UTC):** `2026-10-17T14:35:55.186965+00:00`  
**Zaman Dilimi:** UTC  
**Planlanan Başlangıç (UTC):** `2020-01-01T00:00:00+00:00` (Dahil)  
**Planlanan Bitiş (UTC):** `2020-03-01T00:00:00+00:00` (Hariç)  
**Saha Yerel Saati Karşılığı:** America/Los_Angeles (PST, UTC-8): `2019-12-31 16:00:00` -> `2020-02-29 16:00:00`  

## 1. Çekilen Dosyalar ve Bütünlük Özeti

| Saha | Dosya Adı | Format | Satır/Kayıt Sayısı | SHA-256 Özeti |
| :--- | :--- | :---: | :---: | :--- |
| CALTECH | `caltech_20200101_20200301_raw.json` | Ham JSON | 1670 | `10537bb88faaedf67af541b2fd07c93a1f81ff3fbe1f786ec120b5c7b332ea18` |
| CALTECH | `caltech_20200101_20200301_ham.csv` | Ham 16 Sütun CSV | 1670 | `8e0b10c0a0f5dd70f622c89de684d8b6bb2584e1a895caa291d8418dd2b67dcb` |
| JPL | `jpl_20200101_20200301_raw.json` | Ham JSON | 2883 | `6c6caaebd3ff7531ce2eecbb3bba1e031dd69265ce6d42ffcaadbf71fe2b580a` |
| JPL | `jpl_20200101_20200301_ham.csv` | Ham 16 Sütun CSV | 2883 | `64824c3d09a325ba6c521ad83189a33c9fb2f1856f1ce020a8f4ec2784a01598` |
| BİRLEŞİK | `acn_holdout_20200101_20200301_ham.csv` | Ham 16 Sütun CSV | 4553 | `ca3d2a5f1dca96b85842f7f6d7036cf335c3a640ea27e7b507dd1bd5196a574e` |

## 2. Şema ve Veri İstatistikleri

- **Toplam Ham Oturum:** 4553
- **Tekil sessionID:** 4553
- **Saha Dağılımı:** {'0001': np.int64(2883), '0002': np.int64(1670)}
- **En Erken connectionTime:** `2019-12-31 16:11:24-08:00`
- **En Geç connectionTime:** `2020-02-29 15:35:14-08:00`
- **Sütun Sayısı:** 16 (Beklenen: 16)

### Sütun Listesi
`['sessionID', 'siteID', 'connectionTime', 'disconnectTime', 'doneChargingTime', 'kWhDelivered', 'userID', 'girdi_sayisi', 'girdi_degisti', 'kWhRequested_ilk', 'requestedDeparture_ilk', 'minutesAvailable_ilk', 'kWhRequested', 'requestedDeparture', 'minutesAvailable', 'girdi_gecikme_dk']`

---
### Güvenlik Bildirimi
- API token hiçbir dosyaya veya loga yazılmamıştır.
- Ham holdout verileri salt okunur arşiv olarak saklanacak, üzerine yazılmayacaktır.
- Model performans değerlendirmesine geçmeden önce veri bütünlüğü onayı beklenmelidir.