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

import pathlib
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from sarjdenge import modeller, sim, veri_hijyeni

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
) -> Dict[str, Tuple[pd.Series, np.ndarray]]:
    """Her oturum için planlayıcının karar anında inandığı ayrılış zamanı ve kWh hedefini üretir.
    
    Gelecek bilgisi sızıntısını engeller: Gerçek disconnectTime veya gerçek kWhDelivered asla kullanılmaz!
    """
    gir = df["connectionTime"]
    out = {}

    # 1. Beyan Kaynağı (Bağlantı anında bilinen ilk beyanlar *_ilk)
    # requestedDeparture en az bağlantı + 30 dk olmalıdır
    bd = df["requestedDeparture"].where(
        df["requestedDeparture"] > gir + pd.Timedelta(minutes=30),
        gir + pd.Timedelta(minutes=30)
    )
    kwh_beyan = df["kWhRequested"].clip(upper=100.0).to_numpy(dtype=float)
    out["beyan"] = (bd, kwh_beyan)

    # 2. Tahmin Ortanca (Süre q50, Enerji q50)
    dep_q50 = gir + pd.to_timedelta(df["tahmin_sure_q50"], unit="m")
    kwh_q50 = df["tahmin_kwh_q50"].to_numpy(dtype=float)
    out["tahmin_ortanca"] = (dep_q50, kwh_q50)

    # 3. Tahmin Güvenli (Süre q20, Enerji q80) — Ana Hipotez
    dep_q20 = gir + pd.to_timedelta(df["tahmin_sure_q20"], unit="m")
    kwh_q80 = df["tahmin_kwh_q80"].to_numpy(dtype=float)
    out["tahmin_guvenli"] = (dep_q20, kwh_q80)

    # 4. Keşifsel Aday 1: Hibrit Asimetrik (Ayrılış: min(beyan, q20); Enerji: max(beyan, q50))
    dep_asim = pd.Series(np.minimum(bd.to_numpy(), dep_q20.to_numpy()), index=df.index)
    kwh_asim = np.maximum(kwh_beyan, kwh_q50)
    out["hibrit_asimetrik"] = (dep_asim, kwh_asim)

    return out


def simule_gun(
    gd: pd.DataFrame,
    kaynaklar: Dict[str, Tuple[pd.Series, np.ndarray]],
    t0: pd.Timestamp,
    kapasiteler: Tuple[float, ...] = (0.5, 0.7, 0.9),
    secili_yontemler: Optional[Dict[str, Tuple[str, str]]] = None,
) -> List[Dict[str, Any]]:
    """Tek bir gün ve sahadaki oturumlar için simülasyonu çalıştırır."""
    if secili_yontemler is None:
        secili_yontemler = YONTEMLER

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
            ts_series, kwh_arr = kaynaklar[kaynak]
            ts_sub = ts_series.loc[gd.index][gec].reset_index(drop=True)
            inan_dep = np.maximum(np.floor(adimlar(ts_sub, t0)), giris + 1).astype(int)
            inan_kwh = np.asarray(kwh_arr)[gd.index.get_indexer(gd.index)][gec]

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
    kaynaklar = inanilan_kaynaklar(df_tahminli)
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
