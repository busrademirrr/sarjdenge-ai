"""ŞarjDenge AI — MPC Simülasyonu ve Karar Mekanizması Entegrasyonu (İş Paketi D).

Bu modül, İş Paketi C'de seçilen GradientBoosting şampiyon modellerinin tahminlerini
dondurulmuş simülatör çekirdeğine (`sarjdenge/sim.py`) aktarır; FCFS, EDF, LLF,
mpc_beyan ve mpc_tahmin_guvenli algoritmalarını adil ve özdeş koşullarda karşılaştırır.

Metodolojik Kurallar ve Kısıtlar:
1. Çekirdek modüllere (data.py, tahmin.py, sim.py, deney.py, turkiye.py, sentetik.py) dokunulmaz.
2. 2020 verisi indirilmez ve incelenmez.
3. Ön kayıt ana hipotezi aynen korunur:
   Δ = mpc_tahmin_guvenli - mpc_beyan >= +0.02 (+2 yüzde puanı) ve %95 güven aralığı alt ucu > 0.
4. Kapasiteler (f = 0.5, 0.7, 0.9) ayrı ayrı eşleştirilmiş gün bazlı bootstrap (B=2000) ile değerlendirilir.
5. Hibrit A1 yöntemi (mpc_hibrit_asimetrik) ana hipotezden ayrı, keşifsel analiz olarak raporlanır.
6. Gerçek ayrılış ve teslim enerjisi online planlamada asla görülmez, yalnızca değerlendirmede kullanılır.
"""

from __future__ import annotations

import os
import pathlib
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from sarjdenge import modeller, sim, veri_hijyeni

# Düzeltilmiş yeni sonuç dosyaları (Eski CSV'lerin üzerine asla yazılmaz)
DUZELTILMIS_VAL_DOSYASI = pathlib.Path("data/deney_tablo_val_duzeltilmis.csv")
DUZELTILMIS_BOOT_VAL_DOSYASI = pathlib.Path("data/deney_boot_val_duzeltilmis.csv")
DUZELTILMIS_TA_DOSYASI = pathlib.Path("data/deney_tablo_ta_duzeltilmis.csv")
DUZELTILMIS_BOOT_TA_DOSYASI = pathlib.Path("data/deney_boot_ta_duzeltilmis.csv")

# İndeks güvenlik kalkanı ve regresyon koruması aktif
INDEKS_GUVENLIK_KALKANI = True


def duzeltilmis_cikti_dosyalarini_denetle() -> None:
    """Yeni sonuç dosyalarından biri bile diskte mevcutsa üzerine yazmayı önlemek için FileExistsError fırlatır."""
    hedef_dosyalar = [
        DUZELTILMIS_VAL_DOSYASI,
        DUZELTILMIS_BOOT_VAL_DOSYASI,
        DUZELTILMIS_TA_DOSYASI,
        DUZELTILMIS_BOOT_TA_DOSYASI,
    ]
    for dosya in hedef_dosyalar:
        dosya_p = pathlib.Path(dosya)
        if dosya_p.exists():
            raise FileExistsError(
                f"GÜVENLİK ENGELİ: Düzeltilmiş sonuç dosyası '{dosya_p}' zaten diskte mevcut! "
                "Eski veya mevcut deney sonuçlarının üzerine yazılması kesinlikle yasaktır."
            )

DK = 900.0  # 15 dakika (saniye cinsinden simülasyon adımı)
TZ_ACN = "America/Los_Angeles"

YONTEMLER = {
    "fcfs_beyan": ("fcfs", "beyan"),
    "edf_beyan": ("edf", "beyan"),
    "llf_beyan": ("llf", "beyan"),
    "mpc_beyan": ("mpc", "beyan"),
    "mpc_tahmin_ortanca": ("mpc", "tahmin_ortanca"),
    "mpc_tahmin_guvenli": ("mpc", "tahmin_guvenli"),
    "edf_tahmin_guvenli": ("edf", "tahmin_guvenli"),
    "llf_tahmin_guvenli": ("llf", "tahmin_guvenli"),
    # Keşifsel Aday 1 (Ana hipotezden ayrı raporlanır)
    "mpc_hibrit_asimetrik": ("mpc", "hibrit_asimetrik"),
}

ANA_HIPOTEZ_YONTEMI = "mpc_tahmin_guvenli"
REFERANS_YONTEM = "mpc_beyan"
HIPOTEZ_ESIK = 0.02  # +2 yüzde puanı


def adimlar(ts_series: pd.Series, t0: pd.Timestamp) -> np.ndarray:
    """Zaman damgası serisini t0 referans anından itibaren 15 dakikalık adımlara dönüştürür."""
    return (ts_series - t0).dt.total_seconds().to_numpy() / DK


def inanilan_kaynaklar(
    df: pd.DataFrame,
) -> Dict[str, Tuple[pd.Series, pd.Series]]:
    """Her oturum için planlayıcının karar anında inandığı ayrılış zamanı ve kWh hedefini üretir.
    
    Gelecek bilgisi sızıntısını engeller: Gerçek disconnectTime veya gerçek kWhDelivered asla kullanılmaz!
    Eksik ayrılış beyanı veya eksik tahmin sütunu bulunduğunda güvenli varsayılanlara geri döner.
    Tüm enerji ve zaman kaynakları df.index ile birebir hizalı pd.Series olarak üretilir.
    """
    gir = pd.to_datetime(df["connectionTime"], utc=True)
    out = {}

    # 1. Beyan Kaynağı (Bağlantı anında bilinen ilk beyanlar *_ilk)
    # requestedDeparture eksikse minutesAvailable_ilk veya 480 dk fallback kullanılır
    if "minutesAvailable_ilk" in df.columns:
        fallback_dk = pd.to_numeric(df["minutesAvailable_ilk"], errors="coerce").fillna(480.0).clip(lower=30.0)
    elif "minutesAvailable" in df.columns:
        fallback_dk = pd.to_numeric(df["minutesAvailable"], errors="coerce").fillna(480.0).clip(lower=30.0)
    else:
        fallback_dk = pd.Series(480.0, index=df.index)

    fallback_dep = gir + pd.to_timedelta(fallback_dk, unit="m")
    if "requestedDeparture" in df.columns:
        req_dep = pd.to_datetime(df["requestedDeparture"], utc=True, errors="coerce").fillna(fallback_dep)
    else:
        req_dep = fallback_dep

    # requestedDeparture en az bağlantı + 30 dk olmalıdır
    bd = req_dep.where(
        req_dep > gir + pd.Timedelta(minutes=30),
        gir + pd.Timedelta(minutes=30),
    )

    if "kWhRequested" in df.columns:
        kwh_raw = pd.to_numeric(df["kWhRequested"], errors="coerce")
    elif "kWhRequested_ilk" in df.columns:
        kwh_raw = pd.to_numeric(df["kWhRequested_ilk"], errors="coerce")
    else:
        kwh_raw = pd.Series(12.0, index=df.index)

    kwh_beyan = kwh_raw.where(kwh_raw > 0, 12.0).fillna(12.0).clip(lower=0.5, upper=100.0).astype(float)
    out["beyan"] = (bd, kwh_beyan)

    beyan_sure_dk = ((bd - gir).dt.total_seconds() / 60.0).clip(lower=30.0)

    # 2. Tahmin Ortanca (Süre q50, Enerji q50) — eksikse beyan fallback
    if "tahmin_sure_q50" in df.columns:
        s_q50 = pd.to_numeric(df["tahmin_sure_q50"], errors="coerce").where(lambda s: s > 0, beyan_sure_dk).fillna(beyan_sure_dk).clip(lower=30.0)
    else:
        s_q50 = beyan_sure_dk
    dep_q50 = gir + pd.to_timedelta(s_q50, unit="m")

    if "tahmin_kwh_q50" in df.columns:
        k_q50 = pd.to_numeric(df["tahmin_kwh_q50"], errors="coerce").where(lambda s: s > 0, kwh_beyan).fillna(kwh_beyan).clip(lower=0.5, upper=100.0).astype(float)
    else:
        k_q50 = kwh_beyan.copy()
    out["tahmin_ortanca"] = (dep_q50, k_q50)

    # 3. Tahmin Güvenli (Süre q20, Enerji q80) — Ana Hipotez — eksikse beyan fallback
    if "tahmin_sure_q20" in df.columns:
        s_q20 = pd.to_numeric(df["tahmin_sure_q20"], errors="coerce").where(lambda s: s > 0, beyan_sure_dk).fillna(beyan_sure_dk).clip(lower=30.0)
    else:
        s_q20 = beyan_sure_dk
    dep_q20 = gir + pd.to_timedelta(s_q20, unit="m")

    if "tahmin_kwh_q80" in df.columns:
        k_q80 = pd.to_numeric(df["tahmin_kwh_q80"], errors="coerce").where(lambda s: s > 0, kwh_beyan).fillna(kwh_beyan).clip(lower=0.5, upper=100.0).astype(float)
    else:
        k_q80 = kwh_beyan.copy()
    out["tahmin_guvenli"] = (dep_q20, k_q80)

    # 4. Keşifsel Aday 1: Hibrit Asimetrik (Ayrılış: min(beyan, q20); Enerji: max(beyan, q50))
    dep_asim = pd.Series(np.minimum(bd.to_numpy(), dep_q20.to_numpy()), index=df.index)
    kwh_asim = pd.Series(np.maximum(kwh_beyan.to_numpy(), k_q50.to_numpy()), index=df.index, dtype=float)
    out["hibrit_asimetrik"] = (dep_asim, kwh_asim)

    # İndeks Birebir Hizalama Güvencesi:
    for k_ad, (ts_s, kwh_s) in out.items():
        if not isinstance(kwh_s, pd.Series):
            raise TypeError(f"'{k_ad}' enerji kaynağı pd.Series olmalıdır!")
        if not kwh_s.index.equals(df.index):
            raise ValueError(f"'{k_ad}' enerji serisi df.index ile tam hizalı değil!")
        if not ts_s.index.equals(df.index):
            raise ValueError(f"'{k_ad}' zaman serisi df.index ile tam hizalı değil!")

    return out


def simule_gun(
    gd: pd.DataFrame,
    kaynaklar: Dict[str, Tuple[pd.Series, pd.Series]],
    t0: pd.Timestamp,
    kapasiteler: Tuple[float, ...] = (0.5, 0.7, 0.9),
    secili_yontemler: Optional[Dict[str, Tuple[str, str]]] = None,
) -> List[Dict[str, Any]]:
    """Tek bir gün ve sahadaki oturumlar için simülasyonu çalıştırır."""
    if secili_yontemler is None:
        secili_yontemler = YONTEMLER

    # Güvenlik Kontrolleri: Hizasız serileri engelle
    for k_ad, (ts_series, kwh_source) in kaynaklar.items():
        if not isinstance(kwh_source, pd.Series):
            raise TypeError(f"'{k_ad}' enerji kaynağı pd.Series olmalıdır, {type(kwh_source)} bulundu.")
        if not gd.index.isin(kwh_source.index).all():
            raise ValueError(f"'{k_ad}' enerji kaynağı gd.index ile tam hizalı değil; eksik indeksler var!")
        if not gd.index.isin(ts_series.index).all():
            raise ValueError(f"'{k_ad}' zaman kaynağı gd.index ile tam hizalı değil; eksik indeksler var!")

    giris = np.ceil(adimlar(gd["connectionTime"], t0)).astype(int)
    ayril = np.floor(adimlar(gd["disconnectTime"], t0)).astype(int)
    gec = ayril > giris
    if gec.sum() < 4:
        return []

    giris = giris[gec]
    ayril = ayril[gec]
    e_gercek = gd["kWhDelivered"].to_numpy(dtype=float)[gec]
    n_arac = len(e_gercek)

    # Erken ayrılma tanımı: gerçek ayrılış, beyan edilen süreden en az 15 dk önce mi?
    bd_ts = kaynaklar["beyan"][0].loc[gd.index][gec].reset_index(drop=True)
    disc_ts = gd["disconnectTime"][gec].reset_index(drop=True)
    erken = (disc_ts < bd_ts - pd.Timedelta(minutes=15)).to_numpy()

    # Kontrolsüz tepe gücü
    tepe = sim.kontrolsuz_tepe(giris, ayril, e_gercek)
    gun_sonuclari = []

    for f in kapasiteler:
        cap = max(float(f * tepe), float(sim.SEVIYELER[1]))

        for ad, (alg, kaynak) in secili_yontemler.items():
            ts_series, kwh_series = kaynaklar[kaynak]
            ts_sub = ts_series.loc[gd.index][gec].reset_index(drop=True)
            kwh_sub = kwh_series.loc[gd.index][gec].reset_index(drop=True)

            # Çift taraflı satır ve uzunluk hizalama güvencesi
            if len(ts_sub) != len(kwh_sub) or len(kwh_sub) != int(gec.sum()):
                raise ValueError(
                    f"Zaman ve enerji alt küme uzunlukları uyuşmuyor: ts={len(ts_sub)}, kwh={len(kwh_sub)}, gec={int(gec.sum())}"
                )

            inan_dep = np.maximum(np.floor(adimlar(ts_sub, t0)), giris + 1).astype(int)
            inan_kwh = kwh_sub.to_numpy(dtype=float)

            yont_func = sim.mpc if alg == "mpc" else sim.kural(alg)
            
            # Simülasyon yürütme (Kapasite aşımı olursa simule AssertionError fırlatır)
            teslim = sim.simule(giris, ayril, e_gercek, inan_dep, inan_kwh, cap, yont_func)

            # Başarı ve adillik metrikleri
            sat = teslim / np.maximum(e_gercek, 1e-6)
            ok = sat >= 0.95

            gun_sonuclari.append({
                "saha": str(gd["siteID"].iloc[0]),
                "gun": gd["gun"].iloc[0],
                "f": f,
                "cap_kw": cap,
                "tepe_kw": tepe,
                "yontem": ad,
                "n": n_arac,
                "ok": float(ok.mean()),
                "teslim_orani": float(teslim.sum() / max(e_gercek.sum(), 1e-6)),
                "erken_ok": float(ok[erken].mean()) if erken.any() else np.nan,
                "p10": float(np.percentile(sat, 10)),
                "p20": float(np.percentile(sat, 20)),
                "kapasite_ihlali": 0,  # sim.simule ihlalde hata fırlatır, tamamlandıysa 0'dır
            })

    return gun_sonuclari


def deney_calistir(
    df_tahminli: pd.DataFrame,
    kapasiteler: Tuple[float, ...] = (0.5, 0.7, 0.9),
    min_arac_gunluk: int = 8,
    secili_yontemler: Optional[Dict[str, Tuple[str, str]]] = None,
) -> pd.DataFrame:
    """Tüm gün ve sahalar üzerinde adil simülasyon deneyini yürütür."""
    # 1. df_tahminli indeksinin benzersizlik kontrolü (Güvenlik Kalkanı)
    if not df_tahminli.index.is_unique:
        raise ValueError("HATA: df_tahminli indeksi benzersiz değil! Yinelenen indeksler tespit edildi.")

    kaynaklar = inanilan_kaynaklar(df_tahminli)

    # 2. Üretilen kaynak serilerinin df_tahminli ile tam hizalı olma denetimi
    for k_ad, (ts_s, kwh_s) in kaynaklar.items():
        if not kwh_s.index.equals(df_tahminli.index):
            raise ValueError(f"HATA: '{k_ad}' enerji dizisi indeksi df_tahminli ile tam hizalı değil!")
        if not ts_s.index.equals(df_tahminli.index):
            raise ValueError(f"HATA: '{k_ad}' zaman dizisi indeksi df_tahminli ile tam hizalı değil!")

    tum_satirlar = []

    for site, ds in df_tahminli.groupby("siteID"):
        for gun, gd in ds.groupby("gun"):
            if len(gd) < min_arac_gunluk:
                continue
            t0 = pd.Timestamp(gun).tz_localize(TZ_ACN).tz_convert("UTC")
            res_gun = simule_gun(
                gd=gd,
                kaynaklar=kaynaklar,
                t0=t0,
                kapasiteler=kapasiteler,
                secili_yontemler=secili_yontemler,
            )
            tum_satirlar.extend(res_gun)

    return pd.DataFrame(tum_satirlar)


def bootstrap_eslestirilmis_fark(
    a_serisi: Union[pd.Series, np.ndarray],
    b_serisi: Union[pd.Series, np.ndarray],
    n_boot: int = 2000,
    tohum: int = 42,
) -> Tuple[float, float, float]:
    """Eşleştirilmiş gün bazlı fark için %95 bootstrap güven aralığı hesaplar.
    
    Dönüş: (ortalama_fark, alt_sinir_%2.5, ust_sinir_%97.5)
    """
    rng = np.random.default_rng(tohum)
    d = np.asarray(a_serisi, dtype=float) - np.asarray(b_serisi, dtype=float)
    d = d[~np.isnan(d)]
    if len(d) < 3:
        return np.nan, np.nan, np.nan
    bs_ornekler = rng.choice(d, size=(n_boot, len(d)), replace=True).mean(axis=1)
    lo, hi = np.percentile(bs_ornekler, [2.5, 97.5])
    return float(np.mean(d)), float(lo), float(hi)


def deney_sonuclarini_ozetle(
    res_df: pd.DataFrame,
    n_boot: int = 2000,
    tohum: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Deney sonuçlarını yöntem ve kapasite bazında özetler; bootstrap hipotez testlerini yürütür."""
    # 1. Yöntem Bazlı Özet Tablo
    tablo_ozet = res_df.groupby(["f", "yontem"]).agg(
        gun_sayisi=("gun", "nunique"),
        toplam_oturum=("n", "sum"),
        basari_orani=("ok", "mean"),
        teslim_orani=("teslim_orani", "mean"),
        erken_ayrilan_basari=("erken_ok", "mean"),
        p10_adillik=("p10", "mean"),
        p20_adillik=("p20", "mean"),
        kapasite_ihlali=("kapasite_ihlali", "sum"),
    ).reset_index()

    # 2. Eşleştirilmiş Bootstrap Hipotez Testleri Tablosu
    karsilastirmalar = [
        (ANA_HIPOTEZ_YONTEMI, REFERANS_YONTEM, "Ana Hipotez"),
        ("mpc_tahmin_ortanca", REFERANS_YONTEM, "İkincil Tahmin"),
        ("edf_tahmin_guvenli", "edf_beyan", "EDF Karşılaştırması"),
        ("llf_tahmin_guvenli", "llf_beyan", "LLF Karşılaştırması"),
        ("mpc_hibrit_asimetrik", REFERANS_YONTEM, "Keşifsel Aday 1 vs Beyan"),
        ("mpc_hibrit_asimetrik", ANA_HIPOTEZ_YONTEMI, "Keşifsel Aday 1 vs Güvenli MPC"),
    ]

    boot_satirlar = []
    for f_val, sub_df in res_df.groupby("f"):
        piv = sub_df.pivot_table(index=["saha", "gun"], columns="yontem", values="ok")

        for ad, ref, aciklama in karsilastirmalar:
            if ad in piv.columns and ref in piv.columns:
                m, lo, hi = bootstrap_eslestirilmis_fark(piv[ad], piv[ref], n_boot=n_boot, tohum=tohum)
                esik_gecti = bool(ad == ANA_HIPOTEZ_YONTEMI and ref == REFERANS_YONTEM and m >= HIPOTEZ_ESIK and lo > 0.0)
                boot_satirlar.append({
                    "f": f_val,
                    "karsilastirma": f"{ad} - {ref}",
                    "tur": aciklama,
                    "fark_yuzde_puan": float(m * 100.0),
                    "ci_95_alt_puan": float(lo * 100.0),
                    "ci_95_ust_puan": float(hi * 100.0),
                    "fark_ham": float(m),
                    "ci_95_alt_ham": float(lo),
                    "ci_95_ust_ham": float(hi),
                    "ana_hipotez_desteklendi_mi": esik_gecti,
                })

    return tablo_ozet, pd.DataFrame(boot_satirlar)


def tam_deney_hattini_calistir(
    csv_ocak_haziran: Union[str, pathlib.Path] = "acn_oturumlar_v2.csv",
    csv_temmuz_aralik: Union[str, pathlib.Path] = "acn_oturumlar_temmuz_aralik.csv",
    n_boot: int = 2000,
    tohum: int = 42,
) -> Dict[str, Any]:
    """Tüm deney boru hattını (Ocak–Haziran Doğrulama ve Temmuz–Aralık Dönemler Arası) baştan sona yürütür."""
    # 0. Çıktı Dosya Kalkanı: Yeni sonuç dosyalarından biri bile varsa baştan dur
    duzeltilmis_cikti_dosyalarini_denetle()

    # 1. Modelleri Karşılaştır ve Şampiyonları Eğit
    model_sonuc = modeller.modelleri_karsilastir(csv_ocak_haziran, bolme=0.6)
    sampiyon_sure = model_sonuc["sampiyon_sure_modeli"]
    sampiyon_kwh = model_sonuc["sampiyon_kwh_modeli"]

    # Ocak–Haziran Doğrulama Kümesi Simülasyonu
    val_df = model_sonuc["veri"]["val_df"].copy()
    val_df_tahminli = modeller.tahminleri_ekle(val_df, sampiyon_sure, sampiyon_kwh)
    res_val = deney_calistir(val_df_tahminli)
    tablo_val, boot_val = deney_sonuclarini_ozetle(res_val, n_boot=n_boot, tohum=tohum)

    # 2. Temmuz–Aralık Dönemler Arası Doğrulama (Retrained Şampiyonlar)
    ta_hazirlik = modeller.donemler_arasi_dogrula(
        model_sonuc["sampiyon_sure"], model_sonuc["sampiyon_kwh"],
        csv_ocak_haziran=csv_ocak_haziran, csv_temmuz_aralik=csv_temmuz_aralik
    )
    ta_df = ta_hazirlik["df_temmuz_aralik"].copy()
    ta_df_tahminli = modeller.tahminleri_ekle(ta_df, ta_hazirlik["m_sure_retrained"], ta_hazirlik["m_kwh_retrained"])
    res_ta = deney_calistir(ta_df_tahminli)
    tablo_ta, boot_ta = deney_sonuclarini_ozetle(res_ta, n_boot=n_boot, tohum=tohum)

    return {
        "model_sonuc": model_sonuc,
        "ta_hazirlik": ta_hazirlik,
        "res_val": res_val,
        "tablo_val": tablo_val,
        "boot_val": boot_val,
        "res_ta": res_ta,
        "tablo_ta": tablo_ta,
        "boot_ta": boot_ta,
    }


def duzeltilmis_deneyi_kaydet(sonuclar: Dict[str, Any]) -> Dict[str, pathlib.Path]:
    """Düzeltilmiş deney sonuçlarını yalnızca yeni *_duzeltilmis.csv dosyalarına yazar."""
    duzeltilmis_cikti_dosyalarini_denetle()

    yollar = {
        "tablo_val": DUZELTILMIS_VAL_DOSYASI,
        "boot_val": DUZELTILMIS_BOOT_VAL_DOSYASI,
        "tablo_ta": DUZELTILMIS_TA_DOSYASI,
        "boot_ta": DUZELTILMIS_BOOT_TA_DOSYASI,
    }

    sonuclar["tablo_val"].to_csv(DUZELTILMIS_VAL_DOSYASI, index=False)
    sonuclar["boot_val"].to_csv(DUZELTILMIS_BOOT_VAL_DOSYASI, index=False)
    sonuclar["tablo_ta"].to_csv(DUZELTILMIS_TA_DOSYASI, index=False)
    sonuclar["boot_ta"].to_csv(DUZELTILMIS_BOOT_TA_DOSYASI, index=False)

    return yollar


if __name__ == "__main__":
    print("Düzeltilmiş Deney Hattı Başlatılıyor...")
    sonuclar = tam_deney_hattini_calistir()
    yazilanlar = duzeltilmis_deneyi_kaydet(sonuclar)
    print("Düzeltilmiş Deney Başarıyla Tamamlandı ve Kaydedildi:")
    for k, v in yazilanlar.items():
        print(f"  {k}: {v}")
