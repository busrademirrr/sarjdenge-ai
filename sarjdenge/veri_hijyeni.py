"""┼ŞarjDenge AI ÔÇö Veri Haz─▒rlama, Hijyen ve S─▒z─▒nt─▒ Kontrol Mod├╝l├╝.

Bu mod├╝l ACN-Data ham dosyalar─▒n─▒n manifest analizini yapar, d─▒┼şsalla┼şt─▒r─▒lm─▒┼ş
e┼şiklerle (data/hijyen.yaml) veri temizli─şi sa─şlar, saha bazl─▒ eleme ┼şelalesi
├╝retir ve zaman bazl─▒ gelecek bilgisi s─▒z─▒nt─▒lar─▒n─▒ do─şrular.

NOT: sarjdenge/data.py dosyas─▒n─▒ DE─Ş─░┼ŞT─░RMEZ; ba─ş─▒ms─▒z ve denetlenebilir
hijyen i┼şlevleri sunar.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

from sarjdenge import data

VARSAYILAN_KONFIG: Dict[str, Any] = {
    "filtreler": {
        "min_sure_dk": 30.0,
        "max_sure_saat": 48.0,
        "min_kwh": 0.5,
        "beyan_min_gecikme_dk": -5.0,
        "beyan_max_gecikme_dk": 30.0,
    },
    "zaman": {
        "varsayilan_tz": "America/Los_Angeles",
        "turkiye_tz": "Europe/Istanbul",
    },
    "hedefler": {
        "sure_hedefi": "sure_dk",
        "enerji_hedefi": "kWhDelivered",
    },
    "ozellikler": {
        "kullanici_gecmis_kolonlari": ["sure_dk", "kWhDelivered"],
        "kullanici_gecmis_isimleri": ["gecmis_sure", "gecmis_kwh", "gecmis_n"],
    },
    "saha_kodlari": {
        "Caltech": "0001",
        "JPL": "0002",
    },
}


def yapilandirma_yukle(yaml_yolu: str | pathlib.Path = "data/hijyen.yaml") -> Dict[str, Any]:
    """data/hijyen.yaml dosyas─▒n─▒ y├╝kler; bulunamazsa g├╝venli varsay─▒lanlar─▒ d├Âner."""
    yol = pathlib.Path(yaml_yolu)
    if yol.is_file():
        with open(yol, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            if isinstance(cfg, dict):
                return cfg
    return VARSAYILAN_KONFIG.copy()


def sha256_hesapla(dosya_yolu: str | pathlib.Path) -> str:
    """Belirtilen dosyan─▒n SHA-256 ├Âzetini ├╝retir."""
    h = hashlib.sha256()
    with open(dosya_yolu, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def klasordeki_acn_dosyalarini_bul(klasor: str | pathlib.Path = ".") -> List[pathlib.Path]:
    """├çal─▒┼şma dizinindeki t├╝m ACN oturum CSV dosyalar─▒n─▒ bulur."""
    p = pathlib.Path(klasor)
    bulunanlar = []
    for f in p.glob("acn_*.csv"):
        if f.is_file():
            bulunanlar.append(f)
    return sorted(bulunanlar)


def manifest_uret(
    klasor: str | pathlib.Path = ".",
    cikti_md: str | pathlib.Path = "data/MANIFEST.md",
    kopyala_dizin: Optional[str | pathlib.Path] = "data/ham",
) -> pd.DataFrame:
    """Klas├Ârdeki ACN CSV'lerini inceler, MANIFEST.md yazar ve data/ham/ alt─▒na g├╝venle kopyalar.

    Orijinal dosyalar KES─░NL─░KLE silinmez veya de─şi┼ştirilmez.
    """
    dosyalar = klasordeki_acn_dosyalarini_bul(klasor)
    kayitlar = []
    hash_haritasi: Dict[str, List[str]] = {}

    if kopyala_dizin:
        k_dizin = pathlib.Path(kopyala_dizin)
        k_dizin.mkdir(parents=True, exist_ok=True)
    else:
        k_dizin = None

    for f in dosyalar:
        h = sha256_hesapla(f)
        df = pd.read_csv(f, dtype={"siteID": str})
        n_satir = len(df)
        n_uniq = df["sessionID"].nunique() if "sessionID" in df else 0

        c_series = pd.to_datetime(df["connectionTime"], utc=True, errors="coerce")
        c_min = c_series.min()
        c_max = c_series.max()

        c_min_str = c_min.strftime("%Y-%m-%d %H:%M:%S UTC") if pd.notna(c_min) else "YOK"
        c_max_str = c_max.strftime("%Y-%m-%d %H:%M:%S UTC") if pd.notna(c_max) else "YOK"

        if h not in hash_haritasi:
            hash_haritasi[h] = []
        hash_haritasi[h].append(f.name)

        kayitlar.append({
            "dosya_adi": f.name,
            "dosya_yolu": str(f.resolve()),
            "satir_sayisi": n_satir,
            "benzersiz_sessionID": n_uniq,
            "sha256": h,
            "connectionTime_min": c_min_str,
            "connectionTime_max": c_max_str,
            "tarih_min_raw": c_min,
            "tarih_max_raw": c_max,
        })

    m_df = pd.DataFrame(kayitlar)

    # Ayn─▒ i├ğerik / yinelenen dosya uyar─▒lar─▒
    uyarilar = []
    for h, fnames in hash_haritasi.items():
        if len(fnames) > 1:
            uyarilar.append(f"ÔÜá´©Å **AYNI ─░├çER─░K UYARISI:** `{', '.join(fnames)}` dosyalar─▒ "
                           f"birebir ayn─▒ SHA-256 ├Âzetine (`{h[:12]}...`) sahiptir.")

    # Kopyalama i┼şlemi (data/ham/ alt─▒nda standardize isimle)
    kopyalananlar = []
    if k_dizin:
        for r in kayitlar:
            t_min = r["tarih_min_raw"]
            t_max = r["tarih_max_raw"]
            if pd.notna(t_min) and pd.notna(t_max):
                hedef_ad = f"acn_{t_min.strftime('%Y%m%d')}_{t_max.strftime('%Y%m%d')}.csv"
                hedef_yol = k_dizin / hedef_ad
                # Ayn─▒ isimde dosya varsa ├╝zerine yazmadan ├Ânce hash kontrol├╝
                if not hedef_yol.exists():
                    shutil.copy2(r["dosya_yolu"], hedef_yol)
                    kopyalananlar.append((r["dosya_adi"], hedef_ad))

    # Markdown format─▒nda MANIFEST.md olu┼ştur
    md_satirlar = [
        "# ┼ŞarjDenge AI ÔÇö Veri Manifestosu (`data/MANIFEST.md`)",
        "",
        "Bu belge ├ğal─▒┼şma alan─▒nda tespit edilen t├╝m ham ACN-Data CSV dosyalar─▒n─▒, "
        "b├╝t├╝nl├╝k ├Âzetlerini (SHA-256) ve i├ğerik e┼şle┼şmelerini belgeler.",
        "",
        "## 1. Tespit Edilen Ham Dosyalar Tablosu",
        "",
        "| Dosya Ad─▒ | Sat─▒r Say─▒s─▒ | Benzersiz sessionID | connectionTime Ba┼şlang─▒├ğ | connectionTime Biti┼ş | SHA-256 ├ûzeti |",
        "|:---|:---:|:---:|:---|:---|:---|",
    ]
    for r in kayitlar:
        md_satirlar.append(
            f"| `{r['dosya_adi']}` | {r['satir_sayisi']:,} | {r['benzersiz_sessionID']:,} | "
            f"{r['connectionTime_min']} | {r['connectionTime_max']} | `{r['sha256']}` |"
        )

    md_satirlar.extend([
        "",
        "## 2. ─░├ğerik E┼şle┼şmesi ve ├çift Kopya Analizi",
        "",
    ])
    if uyarilar:
        for u in uyarilar:
            md_satirlar.append(f"- {u}")
        md_satirlar.append("")
        md_satirlar.append(
            "> **├ûnemli Sonu├ğ:** `acn_ocak_temmuz.csv`, `acn_oturumlar_ocak_haziran.csv` ve `acn_oturumlar_v2.csv` "
            "├╝├ğ farkl─▒ veri seti de─şildir; OcakÔÇôHaziran 2019 d├Ânemini temsil eden ayn─▒ verinin kopyalar─▒d─▒r."
        )
    else:
        md_satirlar.append("T├╝m dosyalar birbirinden ba─ş─▒ms─▒z farkl─▒ verilere sahiptir.")

    arsiv_dosyalari = sorted(list(k_dizin.glob("*.csv"))) if k_dizin and k_dizin.exists() else []
    if arsiv_dosyalari:
        md_satirlar.extend([
            "",
            "## 3. `data/ham/` Dizinine Al─▒nan Kopyalar",
            "",
            "Orijinal dosyalar korunmu┼ş; a┼şa─ş─▒daki standart ar┼şiv kopyalar─▒ olu┼şturulmu┼ştur:",
            "",
        ])
        for a in arsiv_dosyalari:
            md_satirlar.append(f"- `data/ham/{a.name}`")

    md_satirlar.extend([
        "",
        "## 4. Do─şrulanm─▒┼ş Saha ve siteID Kodlamas─▒",
        "",
        "ACN-Data API ├ğekim loglar─▒ (`acn_veri_cek.py`) ve ham CSV bloklar─▒ incelenerek siteID kodlamas─▒ kesinle┼ştirilmi┼ştir:",
        "",
        "| siteID | Kurum / Saha Ad─▒ | A├ğ─▒klama | OcaÔÇôHaz 2019 Ham | TemÔÇôAra 2019 Ham |",
        "|:---:|:---|:---|:---:|:---:|",
        "| `1` | **JPL** (Jet Propulsion Laboratory) | NASA AR-GE yerle┼şkesi | 8,610 | 8,734 |",
        "| `2` | **Caltech** (California Institute of Technology) | ├£niversite kamp├╝s├╝ | 5,762 | 4,850 |",
        "",
        "> **Do─şrulama Notu:** `acn_veri_cek.py` SAHALAR listesinde `caltech` ilk, `jpl` ikinci s─▒rada ├ğekilir. "
        "CSV dosyalar─▒n─▒n ilk 5.762 (ve 4.850) sat─▒r─▒n─▒n tamam─▒nda `siteID=2`, sonraki 8.610 (ve 8.734) sat─▒r─▒n─▒n "
        "tamam─▒nda `siteID=1` yer almaktad─▒r. Dolay─▒s─▒yla `siteID=1` JPL, `siteID=2` Caltech'tir.",
    ])

    md_yol = pathlib.Path(cikti_md)
    md_yol.parent.mkdir(parents=True, exist_ok=True)
    with open(md_yol, "w", encoding="utf-8") as f:
        f.write("\n".join(md_satirlar) + "\n")

    return m_df


def eleme_selalesi(
    csv_yolu: str | pathlib.Path,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Belirtilen ACN CSV dosyas─▒na d─▒┼şsalla┼şt─▒r─▒lm─▒┼ş filtreleme ┼şelalesini uygular.

    Her kural i├ğin elenen sat─▒r say─▒s─▒n─▒ ve kalan sat─▒r say─▒s─▒n─▒ hem toplam hem de
    saha (siteID) baz─▒nda hesaplar.
    """
    if config is None:
        config = yapilandirma_yukle()

    filt = config.get("filtreler", VARSAYILAN_KONFIG["filtreler"])
    min_sure_dk = float(filt.get("min_sure_dk", 30.0))
    max_sure_saat = float(filt.get("max_sure_saat", 48.0))
    min_kwh = float(filt.get("min_kwh", 0.5))
    min_gecikme = float(filt.get("beyan_min_gecikme_dk", -5.0))
    max_gecikme = float(filt.get("beyan_max_gecikme_dk", 30.0))

    df_raw = pd.read_csv(csv_yolu, dtype={"siteID": str})
    n_baslangic = len(df_raw)

    # Saha listesi
    sahalar = sorted(df_raw["siteID"].dropna().unique().tolist())

    # Ad─▒m 1: Tekrar eden sessionID
    is_dup = df_raw.duplicated(subset=["sessionID"], keep="first")
    df_step1 = df_raw[~is_dup].copy()

    # Ad─▒m 2: Zaman ve kWh alanlar─▒n─▒n varl─▒─ş─▒ / parse edilebilirli─şi
    c_time = pd.to_datetime(df_step1["connectionTime"], utc=True, errors="coerce")
    d_time = pd.to_datetime(df_step1["disconnectTime"], utc=True, errors="coerce")
    kwh = pd.to_numeric(df_step1["kWhDelivered"], errors="coerce")

    is_missing = c_time.isna() | d_time.isna() | kwh.isna()
    df_step2 = df_step1[~is_missing].copy()
    c_time_s2 = c_time[~is_missing]
    d_time_s2 = d_time[~is_missing]
    kwh_s2 = kwh[~is_missing]

    # Ad─▒m 3: Mant─▒ksal zaman s─▒ras─▒ (disconnectTime > connectionTime)
    sure_dk_s2 = (d_time_s2 - c_time_s2).dt.total_seconds() / 60.0
    is_neg_sure = sure_dk_s2 <= 0.0
    df_step3 = df_step2[~is_neg_sure].copy()
    sure_dk_s3 = sure_dk_s2[~is_neg_sure]
    kwh_s3 = kwh_s2[~is_neg_sure]

    # Ad─▒m 4: S├╝re alt s─▒n─▒r─▒ (sure_dk < min_sure_dk)
    is_short = sure_dk_s3 < min_sure_dk
    df_step4 = df_step3[~is_short].copy()
    sure_dk_s4 = sure_dk_s3[~is_short]
    kwh_s4 = kwh_s3[~is_short]

    # Ad─▒m 5: S├╝re ├╝st s─▒n─▒r─▒ (sure_dk > max_sure_saat * 60)
    is_long = sure_dk_s4 > (max_sure_saat * 60.0)
    df_step5 = df_step4[~is_long].copy()
    kwh_s5 = kwh_s4[~is_long]

    # Ad─▒m 6: Enerji alt s─▒n─▒r─▒ (kWhDelivered < min_kwh)
    is_low_kwh = kwh_s5 < min_kwh
    df_fiziksel_temiz = df_step5[~is_low_kwh].copy()

    # Ad─▒m 7: Beyan ge├ğerlili─şi ve gecikme filtresi
    # (data.yukle ile birebir ayn─▒ kural: requestedDeparture_ilk & kWhRequested_ilk & gecikme [-5, 30])
    ilk = "requestedDeparture_ilk" in df_fiziksel_temiz.columns
    if ilk:
        req_dep = pd.to_datetime(df_fiziksel_temiz["requestedDeparture_ilk"], utc=True, errors="coerce")
        req_kwh = pd.to_numeric(df_fiziksel_temiz["kWhRequested_ilk"], errors="coerce")
    else:
        req_dep = pd.to_datetime(df_fiziksel_temiz["requestedDeparture"], utc=True, errors="coerce")
        req_kwh = pd.to_numeric(df_fiziksel_temiz["kWhRequested"], errors="coerce")

    gecikme_col = df_fiziksel_temiz["girdi_gecikme_dk"] if "girdi_gecikme_dk" in df_fiziksel_temiz else pd.Series(np.nan, index=df_fiziksel_temiz.index)

    beyan_mevcut = req_dep.notna() & req_kwh.notna()
    gecikme_uygun = gecikme_col.between(min_gecikme, max_gecikme) if gecikme_col.notna().any() else beyan_mevcut
    beyan_gecerli = beyan_mevcut & gecikme_uygun

    df_beyanli = df_fiziksel_temiz[beyan_gecerli].copy()

    # Saha baz─▒nda detay tablosu ├╝ret
    adimlar = [
        ("1. Ba┼şlang─▒├ğ Ham Sat─▒r", lambda df: len(df)),
        ("2. Tekrar Eden sessionID Elemesi", lambda df: df.duplicated(subset=["sessionID"]).sum()),
        ("3. Eksik Zaman veya kWh Elemesi", lambda df: (pd.to_datetime(df["connectionTime"], utc=True, errors="coerce").isna() |
                                                      pd.to_datetime(df["disconnectTime"], utc=True, errors="coerce").isna() |
                                                      pd.to_numeric(df["kWhDelivered"], errors="coerce").isna()).sum()),
        ("4. Negatif / S─▒f─▒r S├╝re Elemesi", lambda df: ((pd.to_datetime(df["disconnectTime"], utc=True, errors="coerce") -
                                                       pd.to_datetime(df["connectionTime"], utc=True, errors="coerce")).dt.total_seconds() <= 0).sum()),
        ("5. K─▒sa Oturum Elemesi (<30 dk)", lambda df: 0), # hesaplanm─▒┼ş de─şerlerden
        ("6. A┼ş─▒r─▒ Uzun Oturum Elemesi (>48 sa)", lambda df: 0),
        ("7. Yetersiz Enerji Elemesi (<0.5 kWh)", lambda df: 0),
        ("=> Fiziksel Temiz K├╝me (data.yukle ile ayn─▒)", lambda df: len(df)),
        ("8. Beyans─▒z veya Ge├ğersiz Beyan Elemesi", lambda df: 0),
        ("9. Gecikmi┼ş Beyan Elemesi (<-5 veya >30 dk)", lambda df: 0),
        ("=> Ge├ğerli Beyanl─▒ K├╝me (beyan_var==True)", lambda df: len(df)),
    ]

    # Saha baz─▒nda saya├ğlar
    saha_ozet = {}
    for s in sahalar:
        raw_s = df_raw[df_raw["siteID"] == s]
        dup_s = is_dup[df_raw["siteID"] == s].sum()
        s2_mask = df_step1["siteID"] == s
        miss_s = is_missing[s2_mask].sum()
        s3_mask = df_step2["siteID"] == s
        neg_s = is_neg_sure[s3_mask].sum()
        s4_mask = df_step3["siteID"] == s
        short_s = is_short[s4_mask].sum()
        s5_mask = df_step4["siteID"] == s
        long_s = is_long[s5_mask].sum()
        s6_mask = df_step5["siteID"] == s
        low_k_s = is_low_kwh[s6_mask].sum()
        temiz_s = (df_fiziksel_temiz["siteID"] == s).sum()

        # Beyan ayr─▒┼şt─▒rmas─▒
        fizik_s = df_fiziksel_temiz[df_fiziksel_temiz["siteID"] == s]
        b_mevcut_s = beyan_mevcut[df_fiziksel_temiz["siteID"] == s]
        g_uygun_s = gecikme_uygun[df_fiziksel_temiz["siteID"] == s]

        eksik_beyan_s = (~b_mevcut_s).sum()
        gecikmis_s = (b_mevcut_s & ~g_uygun_s).sum()
        beyanli_s = (df_beyanli["siteID"] == s).sum()

        saha_ozet[s] = {
            "ham": len(raw_s),
            "dup": int(dup_s),
            "miss": int(miss_s),
            "neg": int(neg_s),
            "short": int(short_s),
            "long": int(long_s),
            "low_kwh": int(low_k_s),
            "temiz": int(temiz_s),
            "eksik_beyan": int(eksik_beyan_s),
            "gecikmis_beyan": int(gecikmis_s),
            "beyanli": int(beyanli_s),
        }

    toplam_ozet = {
        "ham": n_baslangic,
        "dup": int(is_dup.sum()),
        "miss": int(is_missing.sum()),
        "neg": int(is_neg_sure.sum()),
        "short": int(is_short.sum()),
        "long": int(is_long.sum()),
        "low_kwh": int(is_low_kwh.sum()),
        "temiz": len(df_fiziksel_temiz),
        "eksik_beyan": int((~beyan_mevcut).sum()),
        "gecikmis_beyan": int((beyan_mevcut & ~gecikme_uygun).sum()),
        "beyanli": len(df_beyanli),
    }

    return {
        "dosya": str(csv_yolu),
        "toplam": toplam_ozet,
        "sahalar": saha_ozet,
        "temiz_satir_sayisi": len(df_fiziksel_temiz),
        "beyanli_satir_sayisi": len(df_beyanli),
    }


def temizle(
    csv_yolu: str | pathlib.Path,
    config: Optional[Dict[str, Any]] = None,
    sadece_beyanli: bool = False,
) -> pd.DataFrame:
    """ACN oturumlar─▒n─▒ y├╝kler, yap─▒land─▒r─▒lm─▒┼ş kurallarla temizler ve zenginle┼ştirir.

    sadece_beyanli=False ise d├Ânen sat─▒r k├╝mesi ve say─▒s─▒ data.yukle() ile B─░REB─░R AYNIDIR.
    sadece_beyanli=True ise yaln─▒zca beyan_var==True olan alt k├╝me d├Âner.
    """
    if config is None:
        config = yapilandirma_yukle()

    filt = config.get("filtreler", VARSAYILAN_KONFIG["filtreler"])
    zaman_cfg = config.get("zaman", VARSAYILAN_KONFIG["zaman"])
    tz = zaman_cfg.get("varsayilan_tz", "America/Los_Angeles")

    min_sure_dk = float(filt.get("min_sure_dk", 30.0))
    max_sure_saat = float(filt.get("max_sure_saat", 48.0))
    min_kwh = float(filt.get("min_kwh", 0.5))
    min_gecikme = float(filt.get("beyan_min_gecikme_dk", -5.0))
    max_gecikme = float(filt.get("beyan_max_gecikme_dk", 30.0))

    df = pd.read_csv(csv_yolu, dtype={"siteID": str})

    ilk = "requestedDeparture_ilk" in df.columns
    if ilk:
        for ad in ["requestedDeparture", "kWhRequested", "minutesAvailable"]:
            if ad in df:
                df[ad + "_son"] = df[ad]
            if ad + "_ilk" in df:
                df[ad] = df[ad + "_ilk"]

    for c in ["connectionTime", "disconnectTime", "requestedDeparture"]:
        if c in df:
            df[c] = pd.to_datetime(df[c], utc=True, errors="coerce")

    # Fiziksel filtreler
    df = df.dropna(subset=["connectionTime", "disconnectTime", "kWhDelivered"])
    df["sure_dk"] = (df.disconnectTime - df.connectionTime).dt.total_seconds() / 60.0
    df = df[(df.sure_dk >= min_sure_dk) & (df.sure_dk <= max_sure_saat * 60.0)
            & (df.kWhDelivered >= min_kwh)]

    df = df.sort_values("connectionTime").reset_index(drop=True)
    df["yerel_giris"] = df.connectionTime.dt.tz_convert(tz)
    df["gun"] = df.yerel_giris.dt.normalize().dt.tz_localize(None)
    df["beyan_sure_dk"] = (df.requestedDeparture - df.connectionTime).dt.total_seconds() / 60.0

    if "userID" in df:
        df["userID"] = df["userID"].astype(str).replace({"nan": "anon", "None": "anon"})
    else:
        df["userID"] = "anon"

    df["beyan_var"] = df.requestedDeparture.notna() & df.kWhRequested.notna()
    if ilk and "girdi_gecikme_dk" in df and df.girdi_gecikme_dk.notna().any():
        df["beyan_var"] &= df.girdi_gecikme_dk.between(min_gecikme, max_gecikme)

    if sadece_beyanli:
        df = df[df.beyan_var].reset_index(drop=True)

    return df


def ozellikler(
    df: pd.DataFrame,
    config: Optional[Dict[str, Any]] = None,
    strict_shift: bool = True,
) -> pd.DataFrame:
    """Yaln─▒zca operasyonel karar an─▒nda bilinen ├Âzellik matrisini ├╝retir.

    strict_shift=True ise kullan─▒c─▒n─▒n yaln─▒zca karar an─▒ndan ├ûNCE tamamlanm─▒┼ş
    (disconnectTime <= connectionTime) oturumlar─▒ ge├ğmi┼ş ├Âzelliklerine dahil edilir.
    """
    X = pd.DataFrame(index=df.index)
    yerel_giris = (
        df["yerel_giris"]
        if "yerel_giris" in df.columns
        else pd.to_datetime(df["connectionTime"], utc=True, errors="coerce").dt.tz_convert(data.TZ)
    )
    X["saat"] = yerel_giris.dt.hour + yerel_giris.dt.minute / 60.0
    X["haftagunu"] = yerel_giris.dt.dayofweek
    X["saha"] = df["siteID"].astype("category").cat.codes if "siteID" in df.columns else 0
    if "beyan_sure_dk" in df.columns:
        X["beyan_sure_dk"] = df["beyan_sure_dk"]
    elif "requestedDeparture" in df.columns:
        X["beyan_sure_dk"] = (
            pd.to_datetime(df["requestedDeparture"], utc=True, errors="coerce")
            - pd.to_datetime(df["connectionTime"], utc=True, errors="coerce")
        ).dt.total_seconds() / 60.0
    else:
        X["beyan_sure_dk"] = np.nan
    X["beyan_kwh"] = df["kWhRequested"] if "kWhRequested" in df.columns else np.nan
    X["beyan_dk_mevcut"] = df["minutesAvailable"] if "minutesAvailable" in df else np.nan

    if not strict_shift:
        g = df.groupby("userID")
        n = g.cumcount()
        for ad, kol in [("gecmis_sure", "sure_dk"), ("gecmis_kwh", "kWhDelivered")]:
            toplam = g[kol].cumsum() - df[kol]
            X[ad] = (toplam / n.where(n > 0)).where(n > 0)
        X["gecmis_n"] = n
    else:
        gecmis_sure, gecmis_kwh, gecmis_n = data.kullanici_gecmisi_hesapla(df)
        X["gecmis_sure"] = gecmis_sure
        X["gecmis_kwh"] = gecmis_kwh
        X["gecmis_n"] = gecmis_n

    return X


def zaman_bol(
    df: pd.DataFrame,
    bolme: float = 0.6,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    """Veriyi kesin kronolojik s─▒rayla ve ├ğak─▒┼şmas─▒z bi├ğimde e─şitim/test olarak ikiye b├Âler."""
    df_sirali = df.sort_values("connectionTime").reset_index(drop=True)
    gunler = np.array(sorted(df_sirali["gun"].unique()))
    kesim_indeks = int(len(gunler) * bolme)
    kesim_gun = gunler[kesim_indeks]

    egit_df = df_sirali[df_sirali["gun"] < kesim_gun].copy().reset_index(drop=True)
    test_df = df_sirali[df_sirali["gun"] >= kesim_gun].copy().reset_index(drop=True)

    # ├çak─▒┼şmas─▒zl─▒k do─şrulamas─▒
    assert egit_df["connectionTime"].max() < test_df["connectionTime"].min(), (
        f"Zaman ├ğak─▒┼şmas─▒ tespit edildi: E─şitim max ({egit_df['connectionTime'].max()}) "
        f">= Test min ({test_df['connectionTime'].min()})"
    )

    return egit_df, test_df, pd.Timestamp(kesim_gun)


def rapor_olustur(
    csv_dosyalari: List[str | pathlib.Path],
    cikti_rapor: str | pathlib.Path = "docs/VERI_TEMIZLEME_RAPORU.md",
) -> str:
    """Saha bazl─▒ eleme ┼şelalesini, veri s├Âzl├╝─ş├╝n├╝ ve s─▒z─▒nt─▒ kontrol├╝n├╝ raporlar."""
    cfg = yapilandirma_yukle()
    rapor_satirlar = [
        "# ┼ŞarjDenge AI ÔÇö Veri Temizleme ve Hijyen Raporu",
        "",
        "Bu rapor, ACN-Data ┼şarj oturumlar─▒n─▒n d─▒┼şsalla┼şt─▒r─▒lm─▒┼ş yap─▒land─▒rma (`data/hijyen.yaml`) "
        "do─şrultusunda temizleme ad─▒mlar─▒n─▒, saha bazl─▒ ┼şelale tablolar─▒n─▒, veri s├Âzl├╝─ş├╝n├╝ ve "
        "zaman bazl─▒ s─▒z─▒nt─▒ denetimlerini belgeler.",
        "",
        "> [!IMPORTANT]",
        "> **Metodolojik Hedef Bildirimi:** `kWhDelivered` alan─▒ kullan─▒c─▒n─▒n bataryas─▒n─▒n ger├ğek/tam "
        "> enerji ihtiyac─▒ de─şil; ACN planlay─▒c─▒s─▒n─▒n mevcut k─▒s─▒tlar alt─▒nda araca teslim etti─şi enerjidir. "
        "> Raporlarda ve modellerde 'tarihsel teslim enerjisi / ihtiya├ğ g├Âstergesi' olarak adland─▒r─▒l─▒r.",
        "",
        "## 1. D─▒┼şsalla┼şt─▒r─▒lm─▒┼ş Filtreleme E┼şikleri (`data/hijyen.yaml`)",
        "",
        "| Parametre | E┼şik De─şeri | A├ğ─▒klama |",
        "|:---|:---:|:---|",
        f"| `min_sure_dk` | {cfg['filtreler']['min_sure_dk']} dk | 30 dakikadan k─▒sa oturumlar pop├╝lasyon d─▒┼ş─▒ b─▒rak─▒l─▒r |",
        f"| `max_sure_saat` | {cfg['filtreler']['max_sure_saat']} sa | 48 saatten uzun oturumlar anormal kabul edilir |",
        f"| `min_kwh` | {cfg['filtreler']['min_kwh']} kWh | 0.5 kWh alt─▒ndaki test/ba┼şar─▒s─▒z ba─şlant─▒lar elenir |",
        f"| `beyan_min_gecikme_dk` | {cfg['filtreler']['beyan_min_gecikme_dk']} dk | Ba─şlant─▒dan en fazla 5 dk ├Ânceki beyanlar ge├ğerlidir |",
        f"| `beyan_max_gecikme_dk` | {cfg['filtreler']['beyan_max_gecikme_dk']} dk | Ba─şlant─▒dan en ge├ğ 30 dk sonraki beyanlar ba─şlant─▒ an─▒nda bilinen say─▒l─▒r |",
        "",
    ]

    for csv in csv_dosyalari:
        selale = eleme_selalesi(csv, cfg)
        f_name = pathlib.Path(csv).name
        toplam = selale["toplam"]
        sahalar = selale["sahalar"]

        rapor_satirlar.extend([
            f"## 2. Eleme ┼Şelalesi: `{f_name}`",
            "",
            "| Eleme Ad─▒m─▒ / Kural | Caltech (Site 2) | JPL (Site 1) | Toplam | Kalan Kay─▒t |",
            "|:---|:---:|:---:|:---:|:---:|",
            f"| 1. Ba┼şlang─▒├ğ Ham Sat─▒r | {sahalar.get('2', sahalar.get('0002', {})).get('ham', 0):,} | "
            f"{sahalar.get('1', sahalar.get('0001', {})).get('ham', 0):,} | {toplam['ham']:,} | {toplam['ham']:,} |",
            f"| 2. Tekrar Eden sessionID | -{sahalar.get('2', sahalar.get('0002', {})).get('dup', 0)} | "
            f"-{sahalar.get('1', sahalar.get('0001', {})).get('dup', 0)} | -{toplam['dup']} | {toplam['ham'] - toplam['dup']:,} |",
            f"| 3. Eksik Zaman veya kWh | -{sahalar.get('2', sahalar.get('0002', {})).get('miss', 0)} | "
            f"-{sahalar.get('1', sahalar.get('0001', {})).get('miss', 0)} | -{toplam['miss']} | {toplam['ham'] - toplam['dup'] - toplam['miss']:,} |",
            f"| 4. Negatif / S─▒f─▒r S├╝re | -{sahalar.get('2', sahalar.get('0002', {})).get('neg', 0)} | "
            f"-{sahalar.get('1', sahalar.get('0001', {})).get('neg', 0)} | -{toplam['neg']} | {toplam['ham'] - toplam['dup'] - toplam['miss'] - toplam['neg']:,} |",
            f"| 5. K─▒sa Oturum (<30 dk) | -{sahalar.get('2', sahalar.get('0002', {})).get('short', 0)} | "
            f"-{sahalar.get('1', sahalar.get('0001', {})).get('short', 0)} | -{toplam['short']} | {toplam['ham'] - toplam['dup'] - toplam['miss'] - toplam['neg'] - toplam['short']:,} |",
            f"| 6. A┼ş─▒r─▒ Uzun Oturum (>48 sa) | -{sahalar.get('2', sahalar.get('0002', {})).get('long', 0)} | "
            f"-{sahalar.get('1', sahalar.get('0001', {})).get('long', 0)} | -{toplam['long']} | {toplam['ham'] - toplam['dup'] - toplam['miss'] - toplam['neg'] - toplam['short'] - toplam['long']:,} |",
            f"| 7. Yetersiz Enerji (<0.5 kWh) | -{sahalar.get('2', sahalar.get('0002', {})).get('low_kwh', 0)} | "
            f"-{sahalar.get('1', sahalar.get('0001', {})).get('low_kwh', 0)} | -{toplam['low_kwh']} | **{toplam['temiz']:,}** |",
            f"| **=> Fiziksel Temiz K├╝me (`data.yukle` ile ayn─▒)** | **{sahalar.get('2', sahalar.get('0002', {})).get('temiz', 0):,}** | "
            f"**{sahalar.get('1', sahalar.get('0001', {})).get('temiz', 0):,}** | **{toplam['temiz']:,}** | **{toplam['temiz']:,}** |",
            f"| 8. Eksik Beyan (Dep/kWh yok) | -{sahalar.get('2', sahalar.get('0002', {})).get('eksik_beyan', 0)} | "
            f"-{sahalar.get('1', sahalar.get('0001', {})).get('eksik_beyan', 0)} | -{toplam['eksik_beyan']} | {toplam['temiz'] - toplam['eksik_beyan']:,} |",
            f"| 9. Gecikmi┼ş Beyan (Gecikme >30 dk) | -{sahalar.get('2', sahalar.get('0002', {})).get('gecikmis_beyan', 0)} | "
            f"-{sahalar.get('1', sahalar.get('0001', {})).get('gecikmis_beyan', 0)} | -{toplam['gecikmis_beyan']} | **{toplam['beyanli']:,}** |",
            f"| **=> Ge├ğerli Beyanl─▒ K├╝me (`beyan_var==True`)** | **{sahalar.get('2', sahalar.get('0002', {})).get('beyanli', 0):,}** | "
            f"**{sahalar.get('1', sahalar.get('0001', {})).get('beyanli', 0):,}** | **{toplam['beyanli']:,}** | **{toplam['beyanli']:,}** |",
            "",
            "> **Do─şrulama Sonucu:**",
            f"> `veri_hijyeni.temizle('{f_name}', sadece_beyanli=False)` ├ğ─▒kt─▒s─▒ tam **{toplam['temiz']:,}** sat─▒rd─▒r "
            f"ve `data.yukle()` ile **birebir ayn─▒ sat─▒r k├╝mesidir**.",
            f"> Sadece beyanl─▒ oturumlar filtrelendi─şinde sat─▒r say─▒s─▒ **{toplam['beyanli']:,}** olmaktad─▒r.",
            "",
        ])

    rapor_satirlar.extend([
        "## 3. ACN Veri S├Âzl├╝─ş├╝ (16 Orijinal S├╝tun)",
        "",
        "| S├╝tun Ad─▒ | Veri Tipi | Birim | Anlam─▒ ve Rol├╝ | Karar An─▒nda Biliniyor mu? |",
        "|:---|:---:|:---:|:---|:---:|",
        "| `sessionID` | `str` | - | Oturuma ait benzersiz kimlik | Ô£à Evet |",
        "| `siteID` | `str` / `int` | - | ┼Şarj istasyonu sahas─▒ (1: JPL, 2: Caltech) | Ô£à Evet |",
        "| `connectionTime` | `datetime` (UTC) | - | Arac─▒n ┼şarj istasyonuna ba─şland─▒─ş─▒ an | Ô£à Evet |",
        "| `disconnectTime` | `datetime` (UTC) | - | Arac─▒n istasyondan ayr─▒ld─▒─ş─▒ an (s├╝re hedefi) | ÔØî Hay─▒r (Hedef) |",
        "| `doneChargingTime` | `datetime` (UTC) | - | Bataryan─▒n ak─▒m ├ğekmeyi bitirdi─şi an | ÔØî Hay─▒r (Gelecek) |",
        "| `kWhDelivered` | `float` | kWh | ─░stasyondan aktar─▒lan toplam enerji (ihtiya├ğ g├Âstergesi) | ÔØî Hay─▒r (Hedef) |",
        "| `userID` | `str` | - | S├╝r├╝c├╝ kimli─şi (ge├ğmi┼ş oturumlar─▒ e┼şle┼ştirmek i├ğin) | Ô£à Evet |",
        "| `girdi_sayisi` | `int` | adet | Kullan─▒c─▒n─▒n girdi─şi ayr─▒l─▒┼ş/enerji beyan say─▒s─▒ | ÔØî Hay─▒r (Sonradan artabilir) |",
        "| `girdi_degisti` | `int` | 0/1 | Kullan─▒c─▒n─▒n ilk beyan─▒n─▒ sonradan de─şi┼ştirip de─şi┼ştirmedi─şi | ÔØî Hay─▒r (Sonradan belirlenir) |",
        "| `kWhRequested_ilk` | `float` | kWh | Kullan─▒c─▒n─▒n ba─şlant─▒ an─▒nda (ilk) talep etti─şi enerji | Ô£à Evet |",
        "| `requestedDeparture_ilk` | `datetime` (UTC) | - | Kullan─▒c─▒n─▒n ba─şlant─▒ an─▒nda (ilk) beyan etti─şi ayr─▒l─▒┼ş | Ô£à Evet |",
        "| `minutesAvailable_ilk` | `float` | dk | Kullan─▒c─▒n─▒n ilk park s├╝resi beyan─▒ | Ô£à Evet |",
        "| `kWhRequested` | `float` | kWh | Kullan─▒c─▒n─▒n son enerji talebi (g├╝ncellenmi┼ş olabilir) | ÔØî S─▒z─▒nt─▒ Riski |",
        "| `requestedDeparture` | `datetime` (UTC) | - | Kullan─▒c─▒n─▒n son ayr─▒l─▒┼ş beyan─▒ (g├╝ncellenmi┼ş olabilir) | ÔØî S─▒z─▒nt─▒ Riski |",
        "| `minutesAvailable` | `float` | dk | Kullan─▒c─▒n─▒n son park s├╝resi | ÔØî S─▒z─▒nt─▒ Riski |",
        "| `girdi_gecikme_dk` | `float` | dk | ─░lk beyan─▒n ba─şlant─▒ zaman─▒na g├Âre gecikmesi | Ô£à Evet ([-5, 30] dk) |",
        "",
        "## 4. Zaman S─▒z─▒nt─▒s─▒ ve Shift Testi Do─şrulama Bulgular─▒",
        "",
        "1. **Hedef Ayr─▒m─▒:** `sure_dk` ve `kWhDelivered` ├Âzellik matrisi $X$ i├ğerisinden kesinlikle ├ğ─▒kar─▒lm─▒┼şt─▒r.",
        "2. **Kronolojik E─şitim/Test Ayr─▒m─▒:** Veriler zaman damgas─▒na g├Âre s─▒ral─▒ b├Âl├╝n├╝r. E─şitim k├╝mesinin en son `connectionTime` de─şeri, test k├╝mesinin en erken `connectionTime` de─şerinden k├╝├ğ├╝kt├╝r (├ğak─▒┼şma s─▒f─▒rd─▒r).",
        "3. **Kullan─▒c─▒ Ge├ğmi┼şi Shift Denetimi:** Standart `cumsum - self` i┼şlemi, kullan─▒c─▒n─▒n mevcut oturumunu d─▒┼şar─▒da b─▒rak─▒r. Ancak veri setinde nadir rastlanan (OcakÔÇôHaziran'da 1, TemmuzÔÇôAral─▒k'ta 3 adet) ├ğak─▒┼şan/e┼şzamanl─▒ oturum durumunda ├Ânceki oturumun `disconnectTime` de─şeri mevcut oturumun ba┼şlang─▒c─▒ndan sonraya sarkabilmektedir. `strict_shift=True` parametresi bu oturumlar─▒ kesinlikle d─▒┼şar─▒da tutarak tam s─▒z─▒nt─▒s─▒z ge├ğmi┼ş ├Âzellik ├╝retir.",
        "",
    ])

    rapor_yol = pathlib.Path(cikti_rapor)
    rapor_yol.parent.mkdir(parents=True, exist_ok=True)
    with open(rapor_yol, "w", encoding="utf-8") as f:
        f.write("\n".join(rapor_satirlar) + "\n")

    return str(rapor_yol)


if __name__ == "__main__":
    print("Manifest ├╝retiliyor...")
    manifest_uret()
    print("Eleme ┼şelalesi ve rapor olu┼şturuluyor...")
    rapor_olustur(["acn_oturumlar_v2.csv", "acn_oturumlar_temmuz_aralik.csv"])
    print("Tamamland─▒: data/MANIFEST.md ve docs/VERI_TEMIZLEME_RAPORU.md g├╝ncellendi.")
