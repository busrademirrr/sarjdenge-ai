"""┼ŞarjDenge AI ÔÇö Web Servisi ve Etkile┼şimli Sim├╝lasyon K├Âpr├╝s├╝ (─░┼ş Paketi E-UI).

Bu mod├╝l, web aray├╝z├╝ (Node.js API ve React frontend) i├ğin tek g├╝nl├╝k sim├╝lasyonlar─▒ y├╝r├╝t├╝r,
96 ad─▒ml─▒ (15 dk) ┼şebeke y├╝k e─şrilerini ve ara├ğ bazl─▒ detayl─▒ telemetriyi ├╝retir,
fiziksel "Neden?" (explainability) a├ğ─▒klamalar─▒n─▒ hesaplar ve sonu├ğlar─▒ JSON olarak sunar.

K─▒s─▒tlar:
- ├çekirdek mod├╝llere (data.py, tahmin.py, sim.py, deney.py, turkiye.py, sentetik.py, modeller.py, deney_v2.py) dokunulmaz.
- 2020 holdout verisi kullan─▒lmaz.
- T├╝m say─▒lar ger├ğek sim├╝lasyondan ├╝retilir; uydurma veya elle yaz─▒lm─▒┼ş metrik yoktur.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from sarjdenge import deney_v2, modeller, sentetik_v2, sim, veri_hijyeni

DK = 900.0  # 15 dakika (saniye cinsinden)
DT_H = 0.25  # saat cinsinden 15 dk
EPS = 1e-9
PROJE_KOK = pathlib.Path(__file__).parent.parent

# Senaryo Tan─▒mlar─▒
SENARYOLAR = {
    "acn_gercek_val": {
        "id": "acn_gercek_val",
        "ad": "ACN Ger├ğek Saha ÔÇö Do─şrulama K├╝mesi (Caltech/JPL 2019)",
        "etiket": "GER├çEK SAHA VER─░S─░",
        "veri_turu": "GERCEK",
        "aciklama": "ACN-Data Caltech ve JPL otoparklar─▒n─▒n OcakÔÇôHaziran 2019 do─şrulama d├Ânemi ├Âl├ğ├╝mleri (68 s─▒k─▒┼ş─▒k g├╝n, 5.207 oturum).",
        "varsayilan_gun": "2019-04-23",
        "mevcut_gunler": ["2019-04-23", "2019-04-30", "2019-05-13", "2019-05-16", "2019-04-22", "2019-05-07"],
        "varsayilan_f": 0.5,
        "site_id": "0001",
        "nominal_trafo_kapasitesi_kw": None,
    },
    "acn_gercek_ta": {
        "id": "acn_gercek_ta",
        "ad": "ACN Ger├ğek Saha ÔÇö D├Ânemler Aras─▒ Test (Caltech/JPL 2019)",
        "etiket": "GER├çEK SAHA VER─░S─░",
        "veri_turu": "GERCEK",
        "aciklama": "ACN-Data TemmuzÔÇôAral─▒k 2019 d├Ânemi ger├ğek ├Âl├ğ├╝mleri (148 g├╝n, 11.911 oturum).",
        "varsayilan_gun": "2019-10-15",
        "mevcut_gunler": ["2019-10-15", "2019-09-17", "2019-11-05", "2019-10-22", "2019-08-20"],
        "varsayilan_f": 0.5,
        "site_id": "0001",
        "nominal_trafo_kapasitesi_kw": None,
    },
    "isyeri_gunduz": {
        "id": "isyeri_gunduz",
        "ad": "T├╝rkiye ─░┼ş Yeri Kamp├╝s├╝ (ACN Kalibrasyonlu)",
        "etiket": "SENTET─░K MODEL (VARSAYIM)",
        "veri_turu": "SENTETIK",
        "aciklama": "config/senaryolar.yaml ile kalibre edilmi┼ş 30 soketli kurumsal ofis g├╝nd├╝z ┼şarj senaryosu.",
        "varsayilan_gun": "2026-03-10",
        "mevcut_gunler": ["2026-03-10", "2026-03-11", "2026-03-12", "2026-03-17", "2026-03-18"],
        "varsayilan_f": 0.5,
        "site_id": "TR_ISYERI",
        "nominal_trafo_kapasitesi_kw": 150.0,
    },
    "apartman_gece": {
        "id": "apartman_gece",
        "ad": "T├╝rkiye Apartman / Site Otopark─▒ (Gece ┼Şarj─▒)",
        "etiket": "SENTET─░K MODEL (VARSAYIM)",
        "veri_turu": "SENTETIK",
        "aciklama": "ACN kar┼ş─▒l─▒─ş─▒ bulunmayan, tamamen T├╝rkiye konut varsay─▒mlar─▒yla kurgulanm─▒┼ş 20 soketli gece ┼şarj modeli.",
        "varsayilan_gun": "2026-03-10",
        "mevcut_gunler": ["2026-03-10", "2026-03-11", "2026-03-12", "2026-03-17", "2026-03-18"],
        "varsayilan_f": 0.5,
        "site_id": "TR_APT",
        "nominal_trafo_kapasitesi_kw": 80.0,
    },
    "karma": {
        "id": "karma",
        "ad": "T├╝rkiye Karma Yerle┼şke (G├╝nd├╝z ─░┼ş + Gece Konut)",
        "etiket": "SENTET─░K MODEL (VARSAYIM)",
        "veri_turu": "SENTETIK",
        "aciklama": "G├╝nd├╝z ├ğal─▒┼şanlar─▒n─▒n ve gece site sakinlerinin ayn─▒ 40 soketi payla┼şt─▒─ş─▒ hibrit kentsel model.",
        "varsayilan_gun": "2026-03-10",
        "mevcut_gunler": ["2026-03-10", "2026-03-11", "2026-03-12", "2026-03-17", "2026-03-18"],
        "varsayilan_f": 0.5,
        "site_id": "TR_KARMA",
        "nominal_trafo_kapasitesi_kw": 200.0,
    },
}

YONTEM_ISIMLERI = {
    "fcfs_beyan": "FCFS (Beyan)",
    "edf_beyan": "EDF (Beyan)",
    "edf_tahmin_guvenli": "EDF (G├╝venli Tahmin)",
    "mpc_beyan": "MPC (Beyan)",
    "mpc_tahmin_guvenli": "MPC G├╝venli (Ana Hipotez)",
    "mpc_hibrit_asimetrik": "MPC Hibrit (Ke┼şifsel A1)",
}

YONTEM_RENKLERI = {
    "fcfs_beyan": "#EF4444",         # K─▒rm─▒z─▒
    "edf_beyan": "#3B82F6",          # Mavi
    "edf_tahmin_guvenli": "#8B5CF6", # Mor
    "mpc_beyan": "#F59E0B",          # Turuncu
    "mpc_tahmin_guvenli": "#10B981", # Z├╝mr├╝t Ye┼şili
    "mpc_hibrit_asimetrik": "#06B6D4", # Turkuaz
}


def simule_ve_profil_cikar(
    giris: np.ndarray,
    ayril: np.ndarray,
    e_gercek: np.ndarray,
    inan_ayril: np.ndarray,
    inan_kwh: np.ndarray,
    cap: float,
    yont_func: Any,
    max_adim: int = 96,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Her 15 dakikal─▒k ad─▒m i├ğin toplam ┼şebeke g├╝c├╝n├╝ ve ara├ğ bazl─▒ g├╝├ğleri kaydeder.

    Kapasite a┼ş─▒m─▒ durumunda sim.simule ile tamamen ayn─▒ kural denetimini uygular.
    """
    n = len(giris)
    teslim = np.zeros(n)
    hiz_gecmisi = np.zeros((max_adim, n))
    toplam_guc = np.zeros(max_adim)

    adim_ust = min(max_adim, int(ayril.max()) + 1)
    for t in range(adim_ust):
        aktif = np.where((giris <= t) & (t < ayril) & (teslim < e_gercek - EPS))[0]
        if aktif.size == 0:
            continue
        kalan = inan_kwh[aktif] - teslim[aktif]
        dep = np.maximum(inan_ayril[aktif], t + 1)
        hiz = yont_func(t, kalan, dep, giris[aktif], cap)

        if hiz.sum() > cap + 1e-6:
            raise AssertionError(f"Kapasite ihlali: {hiz.sum():.3f} > {cap:.3f}")

        hiz_gecmisi[t, aktif] = hiz
        toplam_guc[t] = hiz.sum()
        teslim[aktif] += np.minimum(hiz * DT_H, e_gercek[aktif] - teslim[aktif])

    return teslim, toplam_guc, hiz_gecmisi


def kontrolsuz_profil(
    giris: np.ndarray,
    ayril: np.ndarray,
    e_gercek: np.ndarray,
    max_adim: int = 96,
) -> np.ndarray:
    """Kapasite k─▒s─▒t─▒ olmadan, ara├ğlar─▒n maksimum g├╝├ğle (PMAX) ┼şarj profili."""
    n = len(giris)
    teslim = np.zeros(n)
    toplam_guc = np.zeros(max_adim)

    adim_ust = min(max_adim, int(ayril.max()) + 1)
    for t in range(adim_ust):
        aktif = np.where((giris <= t) & (t < ayril) & (teslim < e_gercek - EPS))[0]
        if aktif.size == 0:
            continue
        guc = np.minimum(sim.PMAX, (e_gercek[aktif] - teslim[aktif]) / DT_H)
        toplam_guc[t] = guc.sum()
        teslim[aktif] += guc * DT_H

    return toplam_guc


def arac_neden_aciklamasi(
    arac_idx: int,
    sat_oranlari: Dict[str, float],
    teslim_kwh: Dict[str, float],
    e_gercek: float,
    giris_dk: float,
    ayril_dk: float,
    beyan_dep_dk: float,
    tahmin_dep_dk: float,
    beyan_kwh: float,
    tahmin_kwh: float,
    erken_ayrildi: bool,
    cap_kw: float,
    es_zamanli_arac_sayisi: int,
) -> Dict[str, Any]:
    """Her ara├ğ i├ğin fiziksel sim├╝lasyon dinamiklerine dayal─▒ ┼şeffaf neden a├ğ─▒klamas─▒ ├╝retir."""
    nedenler = []
    detaylar = {}

    ok_mpc_guv = sat_oranlari.get("mpc_tahmin_guvenli", 0.0) >= 0.95
    ok_mpc_beyan = sat_oranlari.get("mpc_beyan", 0.0) >= 0.95
    ok_edf_beyan = sat_oranlari.get("edf_beyan", 0.0) >= 0.95
    ok_edf_guv = sat_oranlari.get("edf_tahmin_guvenli", 0.0) >= 0.95
    ok_fcfs = sat_oranlari.get("fcfs_beyan", 0.0) >= 0.95

    teslim_mpc_guv = teslim_kwh.get("mpc_tahmin_guvenli", 0.0)
    teslim_mpc_beyan = teslim_kwh.get("mpc_beyan", 0.0)
    teslim_edf_guv = teslim_kwh.get("edf_tahmin_guvenli", 0.0)

    sure_gercek_dk = max(0.0, ayril_dk - giris_dk)
    sure_saat = sure_gercek_dk / 60.0
    sure_beyan_dk = max(0.0, beyan_dep_dk - giris_dk)
    sure_beyan_saat = sure_beyan_dk / 60.0
    sure_tahmin_dk = max(0.0, tahmin_dep_dk - giris_dk)
    sure_tahmin_saat = sure_tahmin_dk / 60.0
    maks_mumkun_kwh = sim.PMAX * sure_saat

    # 1. Fiziksel / ┼Şebeke K─▒s─▒t─▒ Durumu
    if e_gercek > maks_mumkun_kwh:
        nedenler.append({
            "baslik": "Fiziksel S├╝re Yetersizli─şi",
            "kategori": "FIZIKSEL_LIMIT",
            "metin": f"Arac─▒n otoparkta kald─▒─ş─▒ ger├ğek s├╝re ({sure_gercek_dk:.1f} dk / {sure_saat:.1f} sa), talep etti─şi {e_gercek:.1f} kWh enerjiyi azami soket g├╝c├╝nde ({sim.PMAX:.1f} kW) bile tam ┼şarj etmek i├ğin yetersizdir (teorik azami: {maks_mumkun_kwh:.1f} kWh).",
            "derece": "kritik",
        })
    elif cap_kw < es_zamanli_arac_sayisi * 3.68:
        detaylar["sebeke_baskisi"] = "Y├╝ksek S─▒k─▒┼ş─▒kl─▒k: Trafo kapasitesi t├╝m ara├ğlara e┼şzamanl─▒ temel g├╝├ğ sa─şlamaya yetmiyor."

    # 2. Hayalet Kapasite Rezervasyonu Analizi (MPC G├╝venli neden geride kald─▒?)
    if teslim_mpc_guv < teslim_mpc_beyan - 0.5 or (not ok_mpc_guv and ok_mpc_beyan):
        nedenler.append({
            "baslik": "Olas─▒ A├ğ─▒klama: Hayalet Kapasite Rezervasyonu (├çal─▒┼şma Hipotezi)",
            "kategori": "MPC_TILSIMI",
            "metin": f"G├Âzlenen sim├╝lasyon davran─▒┼ş─▒na ili┼şkin olas─▒ a├ğ─▒klama: G├╝venli MPC modeli, di─şer ara├ğlar─▒n konservatif q80 enerji ({tahmin_kwh:.1f} kWh) ve dar q20 s├╝re ({sure_tahmin_dk:.1f} dk / {sure_tahmin_saat:.1f} sa) tahminlerini kar┼ş─▒lamak ├╝zere trafo kapasitesini erken ad─▒mlarda di─şer ara├ğlara ay─▒rm─▒┼ş olabilir (MPC G├╝venli: {teslim_mpc_guv:.1f} kWh, MPC Beyan: {teslim_mpc_beyan:.1f} kWh).",
            "derece": "uyari",
        })
    elif teslim_mpc_guv > teslim_mpc_beyan + 0.5:
        nedenler.append({
            "baslik": "Erken Ayr─▒l─▒┼ş ve G├╝venli Tahmin Korumas─▒",
            "kategori": "TAHMIN_AVANTAJI",
            "metin": f"Modelin q20 s├╝re tahmini ({sure_tahmin_dk:.1f} dk / {sure_tahmin_saat:.1f} sa), s├╝r├╝c├╝n├╝n beyan s├╝resine ({sure_beyan_dk:.1f} dk / {sure_beyan_saat:.1f} sa) k─▒yasla ┼şarj─▒ daha erken ad─▒mlara yo─şunla┼şt─▒rd─▒ ve ayr─▒l─▒┼ş ├Âncesinde daha y├╝ksek enerji teslim edilmesini sa─şlad─▒ (MPC G├╝venli: {teslim_mpc_guv:.1f} kWh, MPC Beyan: {teslim_mpc_beyan:.1f} kWh).",
            "derece": "olumlu",
        })

    # 3. EDF ├£st├╝nl├╝─ş├╝ Analizi
    if ok_edf_guv and not ok_mpc_guv:
        nedenler.append({
            "baslik": "EDF Dinamik Termin ├ûnceli─şi",
            "kategori": "EDF_USTUNLUK",
            "metin": f"EDF algoritmas─▒ gelece─şe kapasite rezervasyonu ay─▒rmaks─▒z─▒n, ara├ğlar─▒ yakla┼şan ayr─▒l─▒┼ş terminine g├Âre dinamik s─▒ralad─▒ ve mevcut g├╝c├╝ bu araca tahsis ederek hedefine ula┼şt─▒rd─▒.",
            "derece": "olumlu",
        })

    # 4. Erken Ayr─▒lma Durumu (ger├ğek algoritma teslimat─▒yla ko┼şulland─▒r─▒lm─▒┼ş)
    if erken_ayrildi:
        sapma_dk = max(0.0, beyan_dep_dk - ayril_dk)
        sapma_saat = sapma_dk / 60.0
        beyan_yontemleri = [
            ("FCFS", sat_oranlari.get("fcfs_beyan", 1.0), ok_fcfs),
            ("EDF (Beyan)", sat_oranlari.get("edf_beyan", 1.0), ok_edf_beyan),
            ("MPC (Beyan)", sat_oranlari.get("mpc_beyan", 1.0), ok_mpc_beyan),
        ]
        eksik_beyan_yontemleri = [
            f"{ad} (%{oran * 100:.0f})" for ad, oran, basarili in beyan_yontemleri if not basarili
        ]
        if not eksik_beyan_yontemleri:
            nedenler.append({
                "baslik": "Erken Ayr─▒l─▒┼ş (Hedef Kayb─▒ Olu┼şmad─▒)",
                "kategori": "ERKEN_AYRILMA_ZARARSIZ",
                "metin": f"S├╝r├╝c├╝ beyan etti─şi s├╝reden {sapma_dk:.0f} dk ({sapma_saat:.1f} sa) ├Ânce ayr─▒ld─▒; ancak mevcut park s├╝resi ({sure_gercek_dk:.1f} dk / {sure_saat:.1f} sa) yeterli oldu─şu i├ğin beyana dayal─▒ y├Ântemler (FCFS, EDF Beyan, MPC Beyan) enerji kayb─▒na u─şramadan hedefi (ÔëÑ%95) tamamlad─▒.",
                "derece": "bilgi",
            })
        else:
            nedenler.append({
                "baslik": "Erken Ayr─▒lan S├╝r├╝c├╝ Sapmas─▒ ve Eksik Teslim",
                "kategori": "ERKEN_AYRILMA",
                "metin": f"S├╝r├╝c├╝ beyan etti─şi s├╝reden {sapma_dk:.0f} dk ({sapma_saat:.1f} sa) ├Ânce otoparktan ayr─▒ld─▒. Bu ara├ğta hedef kar┼ş─▒lama e┼şi─şinin (%95) alt─▒nda kalan beyan tabanl─▒ y├Ântemler: {', '.join(eksik_beyan_yontemleri)}.",
                "derece": "uyari",
            })

    # 5. FCFS Kuyruk Hantall─▒─ş─▒
    if not ok_fcfs and (ok_edf_beyan or ok_mpc_beyan):
        nedenler.append({
            "baslik": "FCFS Kuyruk Gecikmesi",
            "kategori": "FCFS_KUSURU",
            "metin": "FCFS y├Ântemi ayr─▒l─▒┼ş aciliyetini dikkate almad─▒─ş─▒ i├ğin ├Ânce gelen ve uzun s├╝re kalacak ara├ğlar─▒ beslerken, bu arac─▒n terminini ka├ğ─▒rmas─▒na yol a├ğt─▒.",
            "derece": "bilgi",
        })

    if not nedenler:
        nedenler.append({
            "baslik": "Normal Planl─▒ ┼Şarj Tamamland─▒",
            "kategori": "STANDART",
            "metin": f"Ara├ğ planlay─▒c─▒ taraf─▒ndan zaman─▒nda ve k─▒s─▒tlara uygun olarak tam doluma (%{sat_oranlari.get('mpc_tahmin_guvenli', 1.0)*100:.1f}) ula┼şt─▒r─▒ld─▒.",
            "derece": "olumlu",
        })

    return {
        "nedenler": nedenler,
        "detaylar": detaylar,
        "ozet_hukum": nedenler[0]["baslik"],
    }


def beyan_oranlarini_yukle() -> Dict[str, Any]:
    """2019 H1 e─şitim k├╝mesinden ├Â─şrenilmi┼ş ampirik beyan kuantillerini y├╝kler."""
    json_yolu = PROJE_KOK / "config" / "beyan_oranlari.json"
    if json_yolu.exists():
        with open(json_yolu, "r", encoding="utf-8") as f:
            return json.load(f)
    # Geriye d├Ân├╝k g├╝venlik fallback'i
    return {
        "sure_oranlari": {"q20": 0.8889, "q50": 1.1062, "q80": 1.6352},
        "enerji_oranlari": {"q20": 0.3549, "q50": 0.6074, "q80": 0.8446},
    }


def esit_paylasim_kurali(t: int, kalan: np.ndarray, dep: np.ndarray, giris: np.ndarray, cap: float) -> np.ndarray:
    """Aktif ara├ğlara dinamik e┼şit g├╝├ğ payla┼ş─▒m─▒ kural─▒.

    Her ad─▒mda enerjisi hen├╝z dolmam─▒┼ş (kalan > EPS) aktif ara├ğlara
    kapasiteyi e┼şit payla┼şt─▒r─▒r: p_esit = _taban_seviye(min(PMAX, cap / m)).
    Her arac─▒n anl─▒k talebi (kalan / DT_H) tavan seviyesini a┼şamaz.
    Artan kapasite, var─▒┼ş s─▒ras─▒na (FCFS) g├Âre bir ├╝st ayr─▒k kademeye y├╝kseltilerek
    ve ard─▒ndan inan─▒lan enerjisi dolmu┼ş ara├ğlara f─▒rsat├ğ─▒ da─ş─▒t─▒larak de─şerlendirilir.
    """
    n = len(kalan)
    if n == 0:
        return np.zeros(0)
    isteyen = np.where(kalan > sim.EPS)[0]
    m = len(isteyen)
    if m == 0:
        return sim._firsatci(np.zeros(n), cap, kalan, giris)

    pay = sim._taban_seviye(min(sim.PMAX, cap / m))
    hiz = np.zeros(n)
    for i in isteyen:
        tavan = sim._tavan_seviye(max(kalan[i], 0.0) / sim.DT_H)
        hiz[i] = sim._taban_seviye(min(pay, tavan))

    rem = cap - hiz.sum()
    # Kalan g├╝c├╝ var─▒┼ş s─▒ras─▒na g├Âre kademe y├╝kselterek da─ş─▒t
    for i in np.argsort(giris, kind="stable"):
        if rem < sim.SEVIYELER[1] - sim.EPS:
            break
        if kalan[i] > sim.EPS:
            mevcut = hiz[i]
            sonraki = sim.SEVIYELER[sim.SEVIYELER > mevcut + sim.EPS]
            if sonraki.size and (sonraki[0] - mevcut) <= rem + sim.EPS:
                fark = sonraki[0] - mevcut
                hiz[i] = sonraki[0]
                rem -= fark

    return sim._firsatci(hiz, rem, kalan, giris)


def oturumlari_hazirla(
    senaryo_id: str,
    gun_secimi: Optional[str] = None,
    tohum: int = 42,
) -> Tuple[pd.DataFrame, pd.Timestamp, str, str]:
    """Se├ğilen senaryo ve g├╝n i├ğin sim├╝lasyona haz─▒r oturum veri ├ğer├ğevesi ├╝retir veya y├╝kler."""
    cfg = SENARYOLAR.get(senaryo_id, SENARYOLAR["isyeri_gunduz"])
    secili_gun = gun_secimi or cfg["varsayilan_gun"]

    # 2019 H1 e─şitim k├╝mesinden ├Â─şrenilmi┼ş ampirik beyan oran─▒ kuantillerini y├╝kle
    oranlar = beyan_oranlarini_yukle()
    sure_dict = oranlar.get("sure_oranlari", oranlar.get("sure_oranlari_gercek_bolu_beyan", {}))
    enerji_dict = oranlar.get("enerji_oranlari", oranlar.get("enerji_oranlari_gercek_bolu_beyan", {}))
    q_sure_20 = float(sure_dict.get("q20", 0.8889))
    q_sure_50 = float(sure_dict.get("q50", 1.1062))
    q_sure_80 = float(sure_dict.get("q80", 1.6352))
    q_kwh_20 = float(enerji_dict.get("q20", 0.3549))
    q_kwh_50 = float(enerji_dict.get("q50", 0.6074))
    q_kwh_80 = float(enerji_dict.get("q80", 0.8446))

    if cfg["veri_turu"] == "GERCEK":
        csv_dosya = "acn_oturumlar_v2.csv" if senaryo_id == "acn_gercek_val" else "acn_oturumlar_temmuz_aralik.csv"
        csv_yolu = PROJE_KOK / csv_dosya
        if not csv_yolu.exists():
            csv_yolu = PROJE_KOK / "data" / "ham" / csv_dosya

        df = veri_hijyeni.temizle(csv_yolu, sadece_beyanli=True)
        saha_id = cfg.get("site_id", "0001")
        gd = df[(df["gun"] == secili_gun) & (df["siteID"] == saha_id)].copy()
        if len(gd) == 0:
            # Alternatif g├╝n veya di─şer saha
            gd = df[df["gun"] == secili_gun].copy()
            if len(gd) == 0:
                en_yogun = df.groupby("gun").size().sort_values(ascending=False).index[0]
                gd = df[df["gun"] == en_yogun].copy()
                secili_gun = str(en_yogun)

        # Tahmin s├╝tunlar─▒n─▒ olu┼ştur (q20, q50, q80) ÔÇö 2019 H1 e─şitim k├╝mesinden ├Â─şrenilmi┼ş oranlar
        gd["tahmin_sure_q20"] = np.maximum(30.0, gd["minutesAvailable_ilk"] * q_sure_20)
        gd["tahmin_sure_q50"] = np.maximum(30.0, gd["minutesAvailable_ilk"] * q_sure_50)
        gd["tahmin_sure_q80"] = np.maximum(30.0, gd["minutesAvailable_ilk"] * q_sure_80)

        gd["tahmin_kwh_q20"] = np.clip(gd["kWhRequested_ilk"] * q_kwh_20, 1.0, 95.0)
        gd["tahmin_kwh_q50"] = np.clip(gd["kWhRequested_ilk"] * q_kwh_50, 1.0, 95.0)
        gd["tahmin_kwh_q80"] = np.clip(gd["kWhRequested_ilk"] * q_kwh_80, 1.0, 95.0)

        t0 = pd.Timestamp(secili_gun).tz_localize("America/Los_Angeles").tz_convert("UTC")
        veri_kaynagi_etiketi = f"GER├çEK SAHA VER─░S─░ (ACN-Data {saha_id} ÔÇö {secili_gun})"

    else:
        # Sentetik Senaryo ├£retimi (sentetik_v2 mod├╝l├╝ ile)
        df_sentetik = sentetik_v2.uret(
            senaryo_id=senaryo_id,
            gun=3,
            baslangic_tarihi=secili_gun,
            tohum=tohum,
        )
        # Sadece se├ğilen g├╝n├╝ filtrele
        df_sentetik["gun"] = pd.to_datetime(df_sentetik["connectionTime"]).dt.strftime("%Y-%m-%d")
        gd = df_sentetik[df_sentetik["gun"] == secili_gun].copy()
        if len(gd) == 0:
            gd = df_sentetik.iloc[:20].copy()

        # Sentetik tahminleri ekle ÔÇö 2019 H1 ampirik kuantilleri baseline olarak kullan─▒l─▒r
        gd["connectionTime"] = pd.to_datetime(gd["connectionTime"], utc=True)
        gd["disconnectTime"] = pd.to_datetime(gd["disconnectTime"], utc=True)
        gd["requestedDeparture"] = pd.to_datetime(gd["requestedDeparture"], utc=True)

        gd["tahmin_sure_q20"] = np.maximum(30.0, gd["minutesAvailable_ilk"] * q_sure_20)
        gd["tahmin_sure_q50"] = np.maximum(30.0, gd["minutesAvailable_ilk"] * q_sure_50)
        gd["tahmin_sure_q80"] = np.maximum(30.0, gd["minutesAvailable_ilk"] * q_sure_80)

        gd["tahmin_kwh_q20"] = np.clip(gd["kWhRequested_ilk"] * q_kwh_20, 1.0, 85.0)
        gd["tahmin_kwh_q50"] = np.clip(gd["kWhRequested_ilk"] * q_kwh_50, 1.0, 85.0)
        gd["tahmin_kwh_q80"] = np.clip(gd["kWhRequested_ilk"] * q_kwh_80, 1.0, 85.0)

        t0 = pd.Timestamp(secili_gun).tz_localize("Europe/Istanbul").tz_convert("UTC")
        veri_kaynagi_etiketi = f"SENTET─░K MODEL (VARSAYIM ÔÇö {cfg['ad']})"

    return gd, t0, secili_gun, veri_kaynagi_etiketi


def simulasyon_calistir_api(
    senaryo_id: str = "isyeri_gunduz",
    f: float = 0.5,
    cap_kw_override: Optional[float] = None,
    gun_secimi: Optional[str] = None,
    tohum: int = 42,
) -> Dict[str, Any]:
    """Web aray├╝z├╝ i├ğin tek g├╝nl├╝k tam sim├╝lasyonu y├╝r├╝t├╝r ve JSON s├Âzle┼şmesine uygun d├Ând├╝r├╝r."""
    f = float(f)
    f = max(0.3, min(1.2, f))

    gd, t0, secili_gun, veri_kaynagi_etiketi = oturumlari_hazirla(senaryo_id, gun_secimi=gun_secimi, tohum=tohum)
    kaynaklar = deney_v2.inanilan_kaynaklar(gd)

    giris = np.ceil(deney_v2.adimlar(gd["connectionTime"], t0)).astype(int)
    ayril = np.floor(deney_v2.adimlar(gd["disconnectTime"], t0)).astype(int)
    gec = ayril > giris

    if gec.sum() < 2:
        return {"hata": "Se├ğilen g├╝nde yeterli oturum bulunamad─▒.", "n": int(gec.sum())}

    giris = giris[gec]
    ayril = ayril[gec]
    e_gercek = gd["kWhDelivered"].to_numpy(dtype=float)[gec]
    n_arac = len(e_gercek)

    # Zaman ve beyan bilgileri
    bd_ts = kaynaklar["beyan"][0].loc[gd.index][gec].reset_index(drop=True)
    disc_ts = gd["disconnectTime"][gec].reset_index(drop=True)
    erken = (disc_ts < bd_ts - pd.Timedelta(minutes=15)).to_numpy()

    tepe_kw = sim.kontrolsuz_tepe(giris, ayril, e_gercek)
    cap_kw = float(cap_kw_override) if cap_kw_override is not None else max(float(f * tepe_kw), float(sim.SEVIYELER[1]))

    # 96 ad─▒ml─▒ zaman etiketleri (15 dakikal─▒k dilimler: 00:00, 00:15, ..., 23:45)
    zaman_etiketleri = [f"{saat:02d}:{dakika:02d}" for saat in range(24) for dakika in (0, 15, 30, 45)]

    # Kontrols├╝z Y├╝k Profili
    kontrolsuz_guc = kontrolsuz_profil(giris, ayril, e_gercek, max_adim=96)

    # Algoritma Ko┼şular─▒
    yontem_profilleri = {}
    yontem_teslim = {}
    yontem_kpi = {}
    hiz_matrisleri = {}

    secili_yontemler = {
        "fcfs_beyan": ("fcfs", "beyan"),
        "edf_beyan": ("edf", "beyan"),
        "edf_tahmin_guvenli": ("edf", "tahmin_guvenli"),
        "mpc_beyan": ("mpc", "beyan"),
        "mpc_tahmin_guvenli": ("mpc", "tahmin_guvenli"),
        "mpc_hibrit_asimetrik": ("mpc", "hibrit_asimetrik"),
    }

    for y_kod, (alg, kaynak_ad) in secili_yontemler.items():
        ts_series, kwh_arr = kaynaklar[kaynak_ad]
        ts_sub = ts_series.loc[gd.index][gec].reset_index(drop=True)
        inan_dep = np.maximum(np.floor(deney_v2.adimlar(ts_sub, t0)), giris + 1).astype(int)
        inan_kwh = np.asarray(kwh_arr)[gd.index.get_indexer(gd.index)][gec]

        yont_func = sim.mpc if alg == "mpc" else sim.kural(alg)

        teslim, toplam_guc, hiz_matrisi = simule_ve_profil_cikar(
            giris, ayril, e_gercek, inan_dep, inan_kwh, cap_kw, yont_func, max_adim=96
        )

        yontem_profilleri[y_kod] = [round(float(x), 2) for x in toplam_guc]
        yontem_teslim[y_kod] = teslim
        hiz_matrisleri[y_kod] = hiz_matrisi

        sat = teslim / np.maximum(e_gercek, 1e-6)
        ok = sat >= 0.95

        yontem_kpi[y_kod] = {
            "kod": y_kod,
            "ad": YONTEM_ISIMLERI.get(y_kod, y_kod),
            "renk": YONTEM_RENKLERI.get(y_kod, "#6B7280"),
            "basari_orani_yuzde": round(float(ok.mean() * 100.0), 2),
            "teslim_orani_yuzde": round(float(teslim.sum() / max(e_gercek.sum(), 1e-6) * 100.0), 2),
            "toplam_teslim_kwh": round(float(teslim.sum()), 2),
            "erken_ayrilan_basari_yuzde": round(float(ok[erken].mean() * 100.0), 2) if erken.any() else None,
            "p10_adillik_yuzde": round(float(np.percentile(sat, 10) * 100.0), 2),
            "p20_adillik_yuzde": round(float(np.percentile(sat, 20) * 100.0), 2),
            "kapasite_ihlali_kw": 0.0,
            "tepe_tirasi_kw": round(float(tepe_kw - max(toplam_guc)), 2),
        }

    # Ara├ğ Bazl─▒ Detay Telemetrisi ve Explainability ("Neden?")
    arac_listesi = []
    gd_gec = gd[gec].reset_index(drop=True)

    for i in range(n_arac):
        row = gd_gec.iloc[i]
        aid = str(row.get("sessionID", f"EV-{i+1:03d}"))

        g_adim = int(giris[i])
        a_adim = int(ayril[i])
        g_saat = f"{int(g_adim * 15 // 60):02d}:{int((g_adim * 15) % 60):02d}"
        a_saat = f"{int(a_adim * 15 // 60):02d}:{int((a_adim * 15) % 60):02d}"

        beyan_dk = float(row.get("minutesAvailable_ilk", (a_adim - g_adim) * 15.0))
        beyan_dep_saat = f"{int((g_adim * 15 + beyan_dk) // 60):02d}:{int((g_adim * 15 + beyan_dk) % 60):02d}"

        tahmin_dep_dk = float(row.get("tahmin_sure_q20", beyan_dk * 0.8))

        arac_sat = {}
        arac_teslim = {}
        arac_sarj_dakikalari = {}

        for y_kod in secili_yontemler.keys():
            t_kwh = float(yontem_teslim[y_kod][i])
            arac_teslim[y_kod] = round(t_kwh, 2)
            arac_sat[y_kod] = round(float(t_kwh / max(e_gercek[i], 1e-6)), 3)
            # Aktif ┼şarj dakikas─▒ say─▒s─▒
            arac_sarj_dakikalari[y_kod] = int(np.sum(hiz_matrisleri[y_kod][:, i] > 0.1) * 15)

        neden_analizi = arac_neden_aciklamasi(
            arac_idx=i,
            sat_oranlari=arac_sat,
            teslim_kwh=arac_teslim,
            e_gercek=float(e_gercek[i]),
            giris_dk=float(g_adim * 15.0),
            ayril_dk=float(a_adim * 15.0),
            beyan_dep_dk=float(g_adim * 15.0 + beyan_dk),
            tahmin_dep_dk=float(g_adim * 15.0 + tahmin_dep_dk),
            beyan_kwh=float(row.get("kWhRequested_ilk", e_gercek[i] * 1.2)),
            tahmin_kwh=float(row.get("tahmin_kwh_q80", e_gercek[i] * 1.1)),
            erken_ayrildi=bool(erken[i]),
            cap_kw=cap_kw,
            es_zamanli_arac_sayisi=int(np.sum((giris <= a_adim) & (ayril >= g_adim))),
        )

        sure_gercek_dk_val = round(float((a_adim - g_adim) * 15.0), 1)
        sure_beyan_dk_val = round(beyan_dk, 1)
        sure_tahmin_q20_dk_val = round(tahmin_dep_dk, 1)
        sure_tahmin_q50_dk_val = round(float(row.get("tahmin_sure_q50", beyan_dk)), 1)
        sure_tahmin_q80_dk_val = round(float(row.get("tahmin_sure_q80", beyan_dk * 1.2)), 1)

        arac_listesi.append({
            "arac_id": aid,
            "sira": i + 1,
            "kullanici_id": str(row.get("userID", f"U-{i+1}")),
            "giris_adim": g_adim,
            "ayril_adim": a_adim,
            "giris_saat": g_saat,
            "ayril_saat": a_saat,
            "beyan_ayril_saat": beyan_dep_saat,
            "sure_gercek_dk": sure_gercek_dk_val,
            "sure_gercek_saat": round(sure_gercek_dk_val / 60.0, 1),
            "sure_beyan_dk": sure_beyan_dk_val,
            "sure_beyan_saat": round(sure_beyan_dk_val / 60.0, 1),
            "sure_tahmin_q20_dk": sure_tahmin_q20_dk_val,
            "sure_tahmin_q20_saat": round(sure_tahmin_q20_dk_val / 60.0, 1),
            "sure_tahmin_q50_dk": sure_tahmin_q50_dk_val,
            "sure_tahmin_q80_dk": sure_tahmin_q80_dk_val,
            "talep_gercek_kwh": round(float(e_gercek[i]), 2),
            "talep_beyan_kwh": round(float(row.get("kWhRequested_ilk", e_gercek[i] * 1.2)), 2),
            "tahmin_kwh_q20": round(float(row.get("tahmin_kwh_q20", e_gercek[i] * 0.7)), 2),
            "tahmin_kwh_q50": round(float(row.get("tahmin_kwh_q50", e_gercek[i] * 0.9)), 2),
            "tahmin_kwh_q80": round(float(row.get("tahmin_kwh_q80", e_gercek[i] * 1.2)), 2),
            "erken_ayrildi": bool(erken[i]),
            "teslim_kwh": arac_teslim,
            "doyum_orani": arac_sat,
            "sarj_suresi_dk": arac_sarj_dakikalari,
            "neden_analizi": neden_analizi,
        })

    return {
        "senaryo_id": senaryo_id,
        "senaryo_bilgi": SENARYOLAR.get(senaryo_id, {}),
        "veri_kaynagi_etiketi": veri_kaynagi_etiketi,
        "tarih": secili_gun,
        "arac_sayisi": n_arac,
        "f_orani": f,
        "kapasite_siniri_kw": round(cap_kw, 2),
        "kontrolsuz_tepe_kw": round(float(tepe_kw), 2),
        "talep_toplam_kwh": round(float(e_gercek.sum()), 2),
        "zaman_etiketleri": zaman_etiketleri,
        "kontrolsuz_profil_kw": [round(float(x), 2) for x in kontrolsuz_guc],
        "yontem_profilleri": yontem_profilleri,
        "kpi_ozet": yontem_kpi,
        "araclar": arac_listesi,
    }


def kapasite_danismani_hesapla(
    senaryo_id: str = "isyeri_gunduz",
    gun_secimi: Optional[str] = None,
    tohum: int = 42,
    aday_kapasiteler: Optional[List[float]] = None,
    arama_cozunurlugu_kw: float = 0.5,
    esitlik_toleransi_kw: float = 0.5,
) -> Dict[str, Any]:
    """Kullan─▒c─▒n─▒n se├ğti─şi senaryo i├ğin FCFS, EDF, E┼şit Payla┼ş─▒m ve MPC y├Ântemlerinin
    %95 hedef kar┼ş─▒lama oran─▒n─▒ sa─şlayan asgari trafo kapasitesini (kW) hesaplar.

    Bu fonksiyon sarjdenge/urun.py i├ğindeki asgari kapasite tarama form├╝l├╝n├╝
    (ok = teslim / e >= 0.95, ok.mean() >= 0.95) temel al─▒r; ince arama ├ğ├Âz├╝n├╝rl├╝─ş├╝
    (varsay─▒lan ┬▒0.5 kW) ve e┼şitlik (tie-breaking) korumas─▒ i├ğerir.
    """
    gd, t0, secili_gun, veri_kaynagi_etiketi = oturumlari_hazirla(senaryo_id, gun_secimi=gun_secimi, tohum=tohum)
    cfg = SENARYOLAR.get(senaryo_id, SENARYOLAR["isyeri_gunduz"])
    kaynaklar = deney_v2.inanilan_kaynaklar(gd)

    giris = np.ceil(deney_v2.adimlar(gd["connectionTime"], t0)).astype(int)
    ayril = np.floor(deney_v2.adimlar(gd["disconnectTime"], t0)).astype(int)
    gec = ayril > giris

    if gec.sum() < 2:
        return {
            "hata": "Se├ğilen senaryo ve g├╝nde kapasite analizi i├ğin yeterli oturum bulunamad─▒.",
            "arac_sayisi": int(gec.sum()),
            "senaryo_id": senaryo_id,
        }

    giris = giris[gec]
    ayril = ayril[gec]
    e_gercek = gd["kWhDelivered"].to_numpy(dtype=float)[gec]
    n_arac = len(e_gercek)
    tepe_kw = float(sim.kontrolsuz_tepe(giris, ayril, e_gercek))
    nominal_kap_kw = cfg.get("nominal_trafo_kapasitesi_kw")

    # Fiziksel s├╝re ve g├╝├ğ yetersizli─şi denetimi (PMAX h─▒z─▒nda bile dolamayacak ara├ğlar)
    sure_saat = (ayril - giris) * sim.DT_H
    fiziksel_ulasilamaz = (e_gercek > sim.PMAX * sure_saat + 1e-6)
    n_ulasilamaz = int(fiziksel_ulasilamaz.sum())
    maks_ulasilabilir_oran = float((~fiziksel_ulasilamaz).mean())
    hedef_fiziksel_mumkun = bool(maks_ulasilabilir_oran >= 0.95 - 1e-6)

    # ─░nan─▒lan ayr─▒l─▒┼ş ve enerji de─şerleri (Beyan kayna─ş─▒ ÔÇö t├╝m y├Ântemler i├ğin ortak)
    ts_sub = kaynaklar["beyan"][0].loc[gd.index][gec].reset_index(drop=True)
    inan_dep = np.maximum(np.floor(deney_v2.adimlar(ts_sub, t0)), giris + 1).astype(int)
    inan_kwh = np.asarray(kaynaklar["beyan"][1])[gd.index.get_indexer(gd.index)][gec]

    pencere_saat = max(float((ayril.max() - giris.min()) * sim.DT_H), 1.0)
    teorik_alt_kw = max(
        float(sim.SEVIYELER[1]),
        np.floor((float(e_gercek.sum()) * 0.95 / pencere_saat) / arama_cozunurlugu_kw) * arama_cozunurlugu_kw,
    )

    # Aday Kapasiteler (kW)
    ozel_aday_verildi = aday_kapasiteler is not None and len(aday_kapasiteler) > 0
    if ozel_aday_verildi:
        adaylar = sorted([round(float(c), 1) for c in aday_kapasiteler if c > 0])
    else:
        k_fraksiyonlar = [0.25, 0.35, 0.45, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
        adaylar = sorted(list(set([
            round(max(float(sim.SEVIYELER[1]), round(f * tepe_kw / arama_cozunurlugu_kw) * arama_cozunurlugu_kw), 1)
            for f in k_fraksiyonlar
        ])))

    yontem_tanimlari = [
        {
            "kod": "fcfs",
            "ad": "FCFS (─░lk Gelen ─░lk ┼Şarj)",
            "fn": sim.kural("fcfs"),
            "renk": "#EF4444",
            "aciklama": "Ara├ğlar geli┼ş s─▒ras─▒na g├Âre tam g├╝├ğle ┼şarj edilir; ayr─▒l─▒┼ş aciliyeti g├Âzetilmez.",
        },
        {
            "kod": "edf",
            "ad": "EDF (En Erken Termin ├ûncelikli)",
            "fn": sim.kural("edf"),
            "renk": "#3B82F6",
            "aciklama": "Ayr─▒l─▒┼ş zaman─▒ en yak─▒n olan ara├ğlara ├Âncelik verilir; dinamik kuyruk y├Ânetimi.",
        },
        {
            "kod": "esit",
            "ad": "Aktif Ara├ğlara E┼şit G├╝├ğ Payla┼ş─▒m─▒",
            "fn": esit_paylasim_kurali,
            "renk": "#8B5CF6",
            "aciklama": "Mevcut kapasite o anda ba─şl─▒ ve ┼şarj bekleyen t├╝m ara├ğlara e┼şit b├Âl├╝n├╝r.",
        },
        {
            "kod": "mpc",
            "ad": "MPC (LP / HiGHS Optimizasyon)",
            "fn": sim.mpc,
            "renk": "#10B981",
            "aciklama": "Gelecek ufku boyunca ┼şebeke k─▒s─▒tlar─▒ alt─▒nda do─şrusal programlama optimizasyonu.",
        },
    ]

    def _degerlendir(fn: Any, cap_val: float) -> Dict[str, Any]:
        c_f = round(float(cap_val), 1)
        teslim = sim.simule(giris, ayril, e_gercek, inan_dep, inan_kwh, c_f, fn)
        sat = teslim / np.maximum(e_gercek, 1e-6)
        ok = sat >= 0.95 - 1e-6
        ok_yuzde = round(float(ok.mean() * 100.0), 1)
        teslim_yuzde = round(float(teslim.sum() / max(e_gercek.sum(), 1e-6) * 100.0), 1)
        yeterli = bool(ok.mean() >= 0.95 - 1e-6)
        return {
            "kapasite_kw": c_f,
            "hedef_karsilama_yuzde": ok_yuzde,
            "teslim_orani_yuzde": teslim_yuzde,
            "yeterli": yeterli,
        }

    yontem_sonuclari = []
    for y_cfg in yontem_tanimlari:
        tarama_harita: Dict[float, Dict[str, Any]] = {}
        ilk_gecen_aday = None
        son_kalan_aday = teorik_alt_kw

        for c in adaylar:
            nokta = _degerlendir(y_cfg["fn"], c)
            tarama_harita[nokta["kapasite_kw"]] = nokta
            if nokta["yeterli"] and ilk_gecen_aday is None:
                ilk_gecen_aday = nokta["kapasite_kw"]
            elif ilk_gecen_aday is None:
                son_kalan_aday = nokta["kapasite_kw"]

        asgari_kap = ilk_gecen_aday

        # ─░nce ├ğ├Âz├╝n├╝rl├╝kl├╝ hassasla┼şt─▒rma (varsay─▒lan 0.5 kW ad─▒m)
        if not ozel_aday_verildi and ilk_gecen_aday is not None:
            alt_k = max(float(sim.SEVIYELER[1]), min(son_kalan_aday, ilk_gecen_aday))
            ust_k = ilk_gecen_aday
            ince_adaylar = [
                round(float(x), 1)
                for x in np.arange(alt_k, ust_k + arama_cozunurlugu_kw * 0.5, arama_cozunurlugu_kw)
                if round(float(x), 1) <= ust_k + 1e-6
            ]
            if y_cfg["kod"] != "mpc" or len(ince_adaylar) <= 16:
                # Kural tabanl─▒ y├Ântemlerde ve orta/dar aral─▒klarda tam ince tarama (monotonluk varsay─▒m─▒na dayanmaz)
                for c_ince in ince_adaylar:
                    nokta = tarama_harita.get(c_ince) or _degerlendir(y_cfg["fn"], c_ince)
                    tarama_harita[c_ince] = nokta
                    if nokta["yeterli"]:
                        asgari_kap = nokta["kapasite_kw"]
                        break
            else:
                # Geni┼ş aral─▒kl─▒ MPC i├ğin iki a┼şamal─▒ kontroll├╝ tarama (2.0 kW ara ad─▒m -> 0.5 kW son ad─▒m)
                ara_adim = max(2.0, arama_cozunurlugu_kw * 4.0)
                ara_adaylar = [
                    round(float(x), 1)
                    for x in np.arange(alt_k, ust_k + ara_adim * 0.5, ara_adim)
                    if round(float(x), 1) <= ust_k + 1e-6
                ]
                if not ara_adaylar or ara_adaylar[-1] < ust_k - 1e-6:
                    ara_adaylar.append(ust_k)
                alt_lokal = alt_k
                ust_lokal = ust_k
                for c_ara in ara_adaylar:
                    nokta = tarama_harita.get(c_ara) or _degerlendir(y_cfg["fn"], c_ara)
                    tarama_harita[c_ara] = nokta
                    if nokta["yeterli"]:
                        ust_lokal = nokta["kapasite_kw"]
                        break
                    alt_lokal = nokta["kapasite_kw"]
                lokal_adaylar = [
                    round(float(x), 1)
                    for x in np.arange(alt_lokal, ust_lokal + arama_cozunurlugu_kw * 0.5, arama_cozunurlugu_kw)
                    if round(float(x), 1) <= ust_lokal + 1e-6
                ]
                for c_lok in lokal_adaylar:
                    nokta = tarama_harita.get(c_lok) or _degerlendir(y_cfg["fn"], c_lok)
                    tarama_harita[c_lok] = nokta
                    if nokta["yeterli"]:
                        asgari_kap = nokta["kapasite_kw"]
                        break

        tarama = [tarama_harita[k] for k in sorted(tarama_harita.keys())]
        tasarruf = round((tepe_kw - asgari_kap) / tepe_kw * 100.0, 1) if asgari_kap is not None and tepe_kw > 0 else 0.0

        yontem_sonuclari.append({
            "kod": y_cfg["kod"],
            "ad": y_cfg["ad"],
            "renk": y_cfg["renk"],
            "aciklama": y_cfg["aciklama"],
            "asgari_kapasite_kw": asgari_kap,
            "tasarruf_orani_yuzde": tasarruf,
            "basarili": asgari_kap is not None,
            "tarama": tarama,
        })

    # En d├╝┼ş├╝k asgari kapasiteyi sa─şlayan y├Ântem(ler)i tolerans dahilinde belirle
    basarililar = [y for y in yontem_sonuclari if y["asgari_kapasite_kw"] is not None]
    if basarililar:
        min_kap = min(y["asgari_kapasite_kw"] for y in basarililar)
        en_iyiler = [
            y for y in basarililar
            if abs(float(y["asgari_kapasite_kw"]) - float(min_kap)) <= esitlik_toleransi_kw + 1e-6
        ]
        esitlik_var = len(en_iyiler) > 1
        esit_yontemler = [y["ad"] for y in en_iyiler]
        esit_yontem_kodlari = [y["kod"] for y in en_iyiler]
        onerilen_kap = round(float(min_kap), 1)
        onerilen_tasarruf = round((tepe_kw - onerilen_kap) / tepe_kw * 100.0, 1) if tepe_kw > 0 else 0.0
        if onerilen_kap is not None and all(abs(c - onerilen_kap) > 0.05 for c in adaylar):
            adaylar = sorted(adaylar + [onerilen_kap])
            for y_idx, y_cfg in enumerate(yontem_tanimlari):
                mevcut_harita = {pt["kapasite_kw"]: pt for pt in yontem_sonuclari[y_idx]["tarama"]}
                if onerilen_kap not in mevcut_harita:
                    mevcut_harita[onerilen_kap] = _degerlendir(y_cfg["fn"], onerilen_kap)
                    yontem_sonuclari[y_idx]["tarama"] = [mevcut_harita[k] for k in sorted(mevcut_harita.keys())]
        if esitlik_var:
            onerilen_yontem = "En d├╝┼ş├╝k kapasite: y├Ântemler e┼şit"
        else:
            onerilen_yontem = en_iyiler[0]["ad"]
    else:
        esitlik_var = False
        esit_yontemler = []
        esit_yontem_kodlari = []
        onerilen_kap = None
        onerilen_tasarruf = 0.0
        onerilen_yontem = "Hedef kar┼ş─▒lanamad─▒ (Fiziksel s─▒n─▒r)" if not hedef_fiziksel_mumkun else "Belirlenemedi"

    if onerilen_kap is not None:
        if nominal_kap_kw is not None:
            kapasite_ozet_metni = (
                f"Bu senaryo i├ğin hesaplanan asgari trafo g├╝c├╝ {onerilen_kap:.1f} kW "
                f"(┬▒{arama_cozunurlugu_kw:.1f} kW arama ├ğ├Âz├╝n├╝rl├╝─ş├╝nde tahmini minimum); "
                f"senaryodaki nominal trafo kapasitesi {float(nominal_kap_kw):.1f} kW, "
                f"sim├╝le edilen kontrols├╝z tepe talebi {tepe_kw:.1f} kW."
            )
        else:
            kapasite_ozet_metni = (
                f"Bu senaryo i├ğin hesaplanan asgari trafo g├╝c├╝ {onerilen_kap:.1f} kW "
                f"(┬▒{arama_cozunurlugu_kw:.1f} kW arama ├ğ├Âz├╝n├╝rl├╝─ş├╝nde tahmini minimum); "
                f"sim├╝le edilen kontrols├╝z tepe talebi {tepe_kw:.1f} kW."
            )
    else:
        kapasite_ozet_metni = (
            f"Bu senaryoda fiziksel s├╝re veya maksimum soket g├╝c├╝ ({sim.PMAX:.1f} kW) s─▒n─▒r─▒ nedeniyle "
            f"%95 hedef kar┼ş─▒lama oran─▒na hi├ğbir trafo kapasitesinde ula┼ş─▒lamamaktad─▒r "
            f"(fiziksel eri┼şilemez ara├ğ: {n_ulasilamaz}/{n_arac})."
        )

    return {
        "senaryo_id": senaryo_id,
        "senaryo_ad": cfg["ad"],
        "etiket": cfg["etiket"],
        "veri_turu": cfg["veri_turu"],
        "sentetik_mi": cfg["veri_turu"] != "GERCEK",
        "veri_kaynagi_etiketi": veri_kaynagi_etiketi,
        "tarih": secili_gun,
        "arac_sayisi": n_arac,
        "kontrolsuz_tepe_kw": round(tepe_kw, 1),
        "nominal_trafo_kapasitesi_kw": round(float(nominal_kap_kw), 1) if nominal_kap_kw is not None else None,
        "arama_cozunurlugu_kw": arama_cozunurlugu_kw,
        "esitlik_toleransi_kw": esitlik_toleransi_kw,
        "hedef_olcutu": "%95 ara├ğ hedefe ula┼şma oran─▒ (teslim / talep >= 0.95)",
        "fiziksel_ulasilamaz_arac_sayisi": n_ulasilamaz,
        "hedef_fiziksel_mumkun": hedef_fiziksel_mumkun,
        "aday_kapasiteler_kw": adaylar,
        "yontemler": yontem_sonuclari,
        "esitlik_var": esitlik_var,
        "esit_yontemler": esit_yontemler,
        "esit_yontem_kodlari": esit_yontem_kodlari,
        "onerilen_yontem": onerilen_yontem,
        "onerilen_asgari_kapasite_kw": onerilen_kap,
        "azami_trafo_tasarrufu_yuzde": onerilen_tasarruf,
        "kapasite_ozet_metni": kapasite_ozet_metni,
    }


def main():
    parser = argparse.ArgumentParser(description="┼ŞarjDenge AI Web Servisi")
    parser.add_argument("--senaryolar", action="store_true", help="Mevcut senaryolar─▒ JSON olarak listeler")
    parser.add_argument("--advisor", action="store_true", help="Kapasite Dan─▒┼şman─▒ analizi ├ğal─▒┼şt─▒r─▒r")
    parser.add_argument("--senaryo", type=str, default="isyeri_gunduz", help="Senaryo ID")
    parser.add_argument("--f", type=float, default=0.5, help="Kapasite katsay─▒s─▒ f (0.4 - 1.0)")
    parser.add_argument("--cap", type=float, default=None, help="Do─şrudan kW kapasite s─▒n─▒r─▒ override")
    parser.add_argument("--gun", type=str, default=None, help="Tarih se├ğimi (YYYY-AA-GG)")
    parser.add_argument("--tohum", type=int, default=42, help="Rastgele ├╝retim tohumu")
    parser.add_argument("--json", action="store_true", help="JSON format─▒nda ├ğ─▒kt─▒ basar")

    args = parser.parse_args()

    if args.senaryolar:
        out = {"senaryolar": list(SENARYOLAR.values())}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    if args.advisor:
        sonuc = kapasite_danismani_hesapla(
            senaryo_id=args.senaryo,
            gun_secimi=args.gun,
            tohum=args.tohum,
        )
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
        return

    sonuc = simulasyon_calistir_api(
        senaryo_id=args.senaryo,
        f=args.f,
        cap_kw_override=args.cap,
        gun_secimi=args.gun,
        tohum=args.tohum,
    )

    print(json.dumps(sonuc, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
