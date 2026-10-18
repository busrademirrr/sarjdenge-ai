"""ŞarjDenge AI — 2020 Holdout Verisi Güvenli Çekim Betiği (İş Paketi F).

Bu betik, Ön Kayıt 2 (`ONKAYIT_2.md`) belgesinde taahhüt edilen 1 Ocak 2020 – 1 Mart 2020
tarih aralığına ait Caltech ve JPL oturumlarını ACN-Data API üzerinden güvenli biçimde çeker.

Güvenlik ve Bütünlük Kuralları:
1. API token'ı ASLA koda, mesajlara, loglara veya dosyalara yazılmaz.
2. Token ortam değişkeninden (`ACN_API_TOKEN` veya `ACN_TOKEN`) okunur; yoksa `getpass` ile gizli alınır.
3. Mevcut hiçbir dosyanın (`acn_veri_cek.py`, `acn_oturumlar_v2.csv` vb.) üzerine yazmaz.
4. Veriler izole olarak `data/holdout_2020_01_02/` dizinine hem ham JSON hem 16 sütunlu CSV olarak kaydedilir.
5. Oturumların çekim zamanı, satır sayıları, zaman sınırları ve SHA-256 özetleri `data/holdout_2020_01_02/MANIFEST.md` dosyasına kaydedilir.
"""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd

PROJE_KOK = pathlib.Path(__file__).parent.parent
CIKTI_DIZINI = PROJE_KOK / "data" / "holdout_2020_01_02"
SAHALAR = ["caltech", "jpl"]

# Ön Kayıt 2 Zaman Sınırları:
# 2020-01-01 00:00:00 UTC (Dahil)  [Los Angeles: 2019-12-31 16:00:00 PST]
# 2020-03-01 00:00:00 UTC (Hariç)  [Los Angeles: 2020-02-29 16:00:00 PST] (2020 artık yıldır, Şubat 29 çeker)
BASLANGIC_UTC = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
BITIS_UTC = datetime(2020, 3, 1, 0, 0, 0, tzinfo=timezone.utc)


def sha256_dosya(dosya_yolu: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(dosya_yolu, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def token_al() -> str:
    """API token'ını güvenli biçimde alır. Token'ı kesinlikle konsola veya loga basmaz."""
    token = os.environ.get("ACN_API_TOKEN") or os.environ.get("ACN_TOKEN")
    if token and token.strip():
        return token.strip()

    print("[GÜVENLİK] Ortam değişkeni (ACN_API_TOKEN) bulunamadı.")
    try:
        token = getpass.getpass("Lütfen ACN-Data API Token'ınızı giriniz (yazarken ekranda görünmez): ")
    except Exception:
        token = input("Lütfen ACN-Data API Token'ınızı giriniz: ")

    if not token or not token.strip():
        sys.exit("[HATA] API Token girilmedi. İşlem durduruldu.")

    return token.strip()


def duzlestir_16_sutun(o: Dict[str, Any]) -> Dict[str, Any]:
    """Ham oturum sözlüğünü VERI_HAZIRLAMA_KURALLARI.md içindeki 16 standart sütuna dönüştürür."""
    r = {
        "sessionID": o.get("sessionID") or o.get("_id"),
        "siteID": o.get("siteID"),
        "connectionTime": o.get("connectionTime"),
        "disconnectTime": o.get("disconnectTime"),
        "doneChargingTime": o.get("doneChargingTime"),
        "kWhDelivered": o.get("kWhDelivered"),
        "userID": o.get("userID"),
    }

    girdiler = o.get("userInputs") or []
    r["girdi_sayisi"] = len(girdiler)
    r["girdi_degisti"] = int(len(girdiler) > 1)

    if girdiler:
        # Girdileri modifiedAt tarihine göre kronolojik sırala
        def parse_mod(g):
            m = g.get("modifiedAt")
            if m is not None:
                return pd.to_datetime(m, utc=True, errors="coerce")
            return pd.Timestamp.max.tz_localize("UTC")

        sirali = sorted(girdiler, key=parse_mod)
        ilk, son = sirali[0], sirali[-1]

        for ad, g in [("_ilk", ilk), ("", son)]:
            r["kWhRequested" + ad] = g.get("kWhRequested")
            r["requestedDeparture" + ad] = g.get("requestedDeparture")
            r["minutesAvailable" + ad] = g.get("minutesAvailable")

        # İlk girdi gecikmesi (dakika)
        try:
            t_ilk = pd.to_datetime(ilk.get("modifiedAt"), utc=True)
            t_conn = pd.to_datetime(o.get("connectionTime"), utc=True)
            r["girdi_gecikme_dk"] = (t_ilk - t_conn).total_seconds() / 60.0
        except Exception:
            r["girdi_gecikme_dk"] = None
    else:
        for ad in ["_ilk", ""]:
            r["kWhRequested" + ad] = None
            r["requestedDeparture" + ad] = None
            r["minutesAvailable" + ad] = None
        r["girdi_gecikme_dk"] = None

    return r


def holdout_cek():
    """ACN API üzerinden 2020-01-01 .. 2020-03-01 holdout verilerini indirir ve doğrular."""
    token = token_al()

    try:
        from acnportal import acndata
    except ImportError:
        sys.exit("[HATA] 'acnportal' kütüphanesi yüklü değil. Kurulum için: py -m pip install acnportal")

    CIKTI_DIZINI.mkdir(parents=True, exist_ok=True)

    client = acndata.DataClient(token)
    cekme_zamani_utc = datetime.now(timezone.utc).isoformat()

    print(f"\n========================================================")
    print(f"ŞarjDenge AI — 2020 Holdout Verisi Güvenli İndirme")
    print(f"Hedef Dönem (UTC): {BASLANGIC_UTC.isoformat()} -> {BITIS_UTC.isoformat()}")
    print(f"Hedef Dönem (PST): 2019-12-31 16:00:00 -> 2020-02-29 16:00:00")
    print(f"Hedef Klasör: {CIKTI_DIZINI.resolve()}")
    print(f"========================================================\n")

    manifest_satirlar = [
        "# ŞarjDenge AI — 2020 Holdout Veri İndirme Manifesti",
        "",
        f"**İndirme Zamanı (UTC):** `{cekme_zamani_utc}`  ",
        f"**Zaman Dilimi:** UTC  ",
        f"**Planlanan Başlangıç (UTC):** `{BASLANGIC_UTC.isoformat()}` (Dahil)  ",
        f"**Planlanan Bitiş (UTC):** `{BITIS_UTC.isoformat()}` (Hariç)  ",
        f"**Saha Yerel Saati Karşılığı:** America/Los_Angeles (PST, UTC-8): `2019-12-31 16:00:00` -> `2020-02-29 16:00:00`  ",
        "",
        "## 1. Çekilen Dosyalar ve Bütünlük Özeti",
        "",
        "| Saha | Dosya Adı | Format | Satır/Kayıt Sayısı | SHA-256 Özeti |",
        "| :--- | :--- | :---: | :---: | :--- |",
    ]

    tum_oturumlar_duzlestirilmis = []

    for site in SAHALAR:
        print(f"[{site.upper()}] ACN API sorgulanıyor...", flush=True)

        try:
            # acnportal DataClient üzerinden oturumları çek
            # Not: get_sessions_by_time start ve end için datetime bekler
            raw_sessions = list(client.get_sessions_by_time(site, start=BASLANGIC_UTC, end=BITIS_UTC))
        except Exception as e:
            sys.exit(f"[HATA] {site} verisi çekilirken API hatası oluştu: {e}")

        # Sınır kontrolü: connectionTime >= BASLANGIC_UTC and connectionTime < BITIS_UTC
        gecerli_raw = []
        for s in raw_sessions:
            c_time = pd.to_datetime(s.get("connectionTime"), utc=True)
            if c_time >= BASLANGIC_UTC and c_time < BITIS_UTC:
                gecerli_raw.append(s)

        print(f"[{site.upper()}] API'den dönen: {len(raw_sessions)} kayıt, Hedef aralıkta ({BASLANGIC_UTC.date()} - {BITIS_UTC.date()}): {len(gecerli_raw)} kayıt.")

        # 1. Ham JSON olarak kaydet
        json_dosya = CIKTI_DIZINI / f"{site}_20200101_20200301_raw.json"
        with open(json_dosya, "w", encoding="utf-8") as f:
            json.dump(gecerli_raw, f, ensure_ascii=False, indent=2, default=str)
        hash_json = sha256_dosya(json_dosya)
        manifest_satirlar.append(f"| {site.upper()} | `{json_dosya.name}` | Ham JSON | {len(gecerli_raw)} | `{hash_json}` |")

        # 2. 16 Standart sütunlu CSV olarak kaydet
        duz = [duzlestir_16_sutun(s) for s in gecerli_raw]
        df_site = pd.DataFrame(duz)
        csv_site_dosya = CIKTI_DIZINI / f"{site}_20200101_20200301_ham.csv"
        df_site.to_csv(csv_site_dosya, index=False)
        hash_csv = sha256_dosya(csv_site_dosya)
        manifest_satirlar.append(f"| {site.upper()} | `{csv_site_dosya.name}` | Ham 16 Sütun CSV | {len(df_site)} | `{hash_csv}` |")

        tum_oturumlar_duzlestirilmis.extend(duz)

    # 3. Birleşik Holdout CSV dosyası
    df_tum = pd.DataFrame(tum_oturumlar_duzlestirilmis)
    birlesik_csv_dosya = CIKTI_DIZINI / "acn_holdout_20200101_20200301_ham.csv"
    df_tum.to_csv(birlesik_csv_dosya, index=False)
    hash_birlesik = sha256_dosya(birlesik_csv_dosya)
    manifest_satirlar.append(f"| BİRLEŞİK | `{birlesik_csv_dosya.name}` | Ham 16 Sütun CSV | {len(df_tum)} | `{hash_birlesik}` |")

    # 2. Şema ve İstatistik Tablosu
    manifest_satirlar.extend([
        "",
        "## 2. Şema ve Veri İstatistikleri",
        "",
        f"- **Toplam Ham Oturum:** {len(df_tum)}",
        f"- **Tekil sessionID:** {df_tum['sessionID'].nunique() if len(df_tum) else 0}",
        f"- **Saha Dağılımı:** {dict(df_tum['siteID'].value_counts()) if len(df_tum) else {}}",
        f"- **En Erken connectionTime:** `{df_tum['connectionTime'].min() if len(df_tum) else 'Yok'}`",
        f"- **En Geç connectionTime:** `{df_tum['connectionTime'].max() if len(df_tum) else 'Yok'}`",
        f"- **Sütun Sayısı:** {len(df_tum.columns)} (Beklenen: 16)",
        "",
        "### Sütun Listesi",
        f"`{list(df_tum.columns)}`",
        "",
        "---",
        "### Güvenlik Bildirimi",
        "- API token hiçbir dosyaya veya loga yazılmamıştır.",
        "- Ham holdout verileri salt okunur arşiv olarak saklanacak, üzerine yazılmayacaktır.",
        "- Model performans değerlendirmesine geçmeden önce veri bütünlüğü onayı beklenmelidir.",
    ])

    manifest_yolu = CIKTI_DIZINI / "MANIFEST.md"
    with open(manifest_yolu, "w", encoding="utf-8") as f:
        f.write("\n".join(manifest_satirlar))

    print(f"\n[BAŞARILI] Holdout verileri başarıyla indirildi ve manifest oluşturuldu:")
    print(f"  -> Manifest: {manifest_yolu.resolve()}")
    print(f"  -> Toplam Oturum: {len(df_tum)}")
    print(f"  -> Birleşik Dosya: {birlesik_csv_dosya.name} (SHA-256: {hash_birlesik[:16]}...)\n")


if __name__ == "__main__":
    holdout_cek()
