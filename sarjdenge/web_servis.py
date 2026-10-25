"""ŞarjDenge AI — Web Servisi ve Etkileşimli Simülasyon Köprüsü (İş Paketi E-UI).

Bu modül, web arayüzü (Node.js API ve React frontend) için tek günlük simülasyonları yürütür,
96 adımlı (15 dk) şebeke yük eğrilerini ve araç bazlı detaylı telemetriyi üretir,
fiziksel "Neden?" (explainability) açıklamalarını hesaplar ve sonuçları JSON olarak sunar.

Kısıtlar:
- Çekirdek modüllere (data.py, tahmin.py, sim.py, deney.py, turkiye.py, sentetik.py, modeller.py, deney_v2.py) dokunulmaz.
- 2020 holdout verisi kullanılmaz.
- Tüm sayılar gerçek simülasyondan üretilir; uydurma veya elle yazılmış metrik yoktur.
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

# Senaryo Tanımları
SENARYOLAR = {
    "acn_gercek_val": {
        "id": "acn_gercek_val",
        "ad": "ACN Gerçek Saha — Doğrulama Kümesi (Caltech/JPL 2019)",
        "etiket": "GERÇEK SAHA VERİSİ",
        "veri_turu": "GERCEK",
        "aciklama": "ACN-Data Caltech ve JPL otoparklarının Ocak–Haziran 2019 doğrulama dönemi ölçümleri.",
        "varsayilan_gun": "2019-04-23",
        "mevcut_gunler": ["2019-04-23", "2019-04-30", "2019-05-13", "2019-05-16", "2019-04-22", "2019-05-07"],
        "varsayilan_f": 0.5,
        "site_id": "0001",
        "nominal_trafo_kapasitesi_kw": None,
    },
    "acn_gercek_ta": {
        "id": "acn_gercek_ta",
        "ad": "ACN Gerçek Saha — Dönemler Arası Test (Caltech/JPL 2019)",
        "etiket": "GERÇEK SAHA VERİSİ",
        "veri_turu": "GERCEK",
        "aciklama": "ACN-Data Temmuz–Aralık 2019 dönemi gerçek ölçümleri.",
        "varsayilan_gun": "2019-10-15",
        "mevcut_gunler": ["2019-10-15", "2019-09-17", "2019-11-05", "2019-10-22", "2019-08-20"],
        "varsayilan_f": 0.5,
        "site_id": "0001",
        "nominal_trafo_kapasitesi_kw": None,
    },
    "isyeri_gunduz": {
        "id": "isyeri_gunduz",
        "ad": "Türkiye İş Yeri Kampüsü (ACN Kalibrasyonlu)",
        "etiket": "SENTETİK MODEL (VARSAYIM)",
        "veri_turu": "SENTETIK",
        "aciklama": "config/senaryolar.yaml ile kalibre edilmiş 30 soketli kurumsal ofis gündüz şarj senaryosu.",
        "varsayilan_gun": "2026-03-10",
        "mevcut_gunler": ["2026-03-10", "2026-03-11", "2026-03-12", "2026-03-17", "2026-03-18"],
        "varsayilan_f": 0.5,
        "site_id": "TR_ISYERI",
        "nominal_trafo_kapasitesi_kw": 150.0,
    },
    "apartman_gece": {
        "id": "apartman_gece",
        "ad": "Türkiye Apartman / Site Otoparkı (Gece Şarjı)",
        "etiket": "SENTETİK MODEL (VARSAYIM)",
        "veri_turu": "SENTETIK",
        "aciklama": "ACN karşılığı bulunmayan, tamamen Türkiye konut varsayımlarıyla kurgulanmış 20 soketli gece şarj modeli.",
        "varsayilan_gun": "2026-03-10",
        "mevcut_gunler": ["2026-03-10", "2026-03-11", "2026-03-12", "2026-03-17", "2026-03-18"],
        "varsayilan_f": 0.5,
        "site_id": "TR_APT",
        "nominal_trafo_kapasitesi_kw": 80.0,
    },
    "karma": {
        "id": "karma",
        "ad": "Türkiye Karma Yerleşke (Gündüz İş + Gece Konut)",
        "etiket": "SENTETİK MODEL (VARSAYIM)",
        "veri_turu": "SENTETIK",
        "aciklama": "Gündüz çalışanlarının ve gece site sakinlerinin aynı 40 soketi paylaştığı hibrit kentsel model.",
        "varsayilan_gun": "2026-03-10",
        "mevcut_gunler": ["2026-03-10", "2026-03-11", "2026-03-12", "2026-03-17", "2026-03-18"],
        "varsayilan_f": 0.5,
        "site_id": "TR_KARMA",
        "nominal_trafo_kapasitesi_kw": 200.0,
    },
}

YONTEM_ISIMLERI = {
    "fcfs_beyan": "FCFS (Beyan)",
    "esit_beyan": "Eşit Güç Paylaşımı",
    "edf_beyan": "EDF (Beyan)",
    "edf_tahmin_guvenli": "EDF (kuantil oranı)",
    "mpc_beyan": "MPC (Beyan)",
    "mpc_tahmin_guvenli": "MPC (kuantil oranı)",
    "mpc_hibrit_asimetrik": "MPC Hibrit (Keşifsel A1)",
}

YONTEM_RENKLERI = {
    "fcfs_beyan": "#EF4444",         # Kırmızı
    "esit_beyan": "#0D9488",         # Deniz Yeşili (Teal)
    "edf_beyan": "#3B82F6",          # Mavi
    "edf_tahmin_guvenli": "#8B5CF6", # Mor
    "mpc_beyan": "#F59E0B",          # Turuncu
    "mpc_tahmin_guvenli": "#10B981", # Zümrüt Yeşili
    "mpc_hibrit_asimetrik": "#06B6D4", # Turkuaz
}


def adim_saat_etiketi(adim: int) -> str:
    """15 dakikalık adım indeksini saat etiketine dönüştürür; gün aşımında '+1g 02:15' biçimini kullanır."""
    adim_int = max(0, int(adim))
    gun_farki = adim_int // 96
    gun_ici = adim_int % 96
    saat = (gun_ici * 15) // 60
    dakika = (gun_ici * 15) % 60
    if gun_farki == 0:
        return f"{saat:02d}:{dakika:02d}"
    return f"+{gun_farki}g {saat:02d}:{dakika:02d}"


def zaman_etiketleri_uret(toplam_adim: int) -> List[str]:
    """0..toplam_adim-1 aralığındaki tüm 15 dakikalık adımlar için zaman etiketlerini üretir."""
    n_adim = max(96, int(toplam_adim))
    return [adim_saat_etiketi(t) for t in range(n_adim)]


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
    """Her 15 dakikalık adım için toplam şebeke gücünü ve araç bazlı güçleri kaydeder.

    Kapasite aşımı durumunda sim.simule ile tamamen aynı kural denetimini uygular.
    Gece yarısını aşan oturumlarda (ayril > 96) simülasyon tüm oturumlar tamamlanana
    kadar dinamik ufukta devam eder; teslim edilen enerji sim.simule ile birebir özdeştir.
    """
    n = len(giris)
    teslim = np.zeros(n)
    tam_ufuk = max(max_adim, (int(ayril.max()) + 1) if n > 0 else max_adim)
    hiz_gecmisi = np.zeros((tam_ufuk, n))
    toplam_guc = np.zeros(tam_ufuk)

    son_adim = (int(ayril.max()) + 1) if n > 0 else 0
    for t in range(son_adim):
        aktif = np.where((giris <= t) & (t < ayril) & (teslim < e_gercek - EPS))[0]
        if aktif.size == 0:
            continue
        kalan = np.nan_to_num(inan_kwh[aktif] - teslim[aktif], nan=0.0, posinf=100.0, neginf=0.0)
        dep = np.maximum(inan_ayril[aktif], t + 1)
        hiz = yont_func(t, kalan, dep, giris[aktif], cap)

        if (hiz < -1e-6).any():
            raise AssertionError(f"Negatif güç tahsisi tespit edildi: min={hiz.min():.3f}")
        if (hiz > sim.PMAX + 1e-6).any():
            raise AssertionError(f"Soket azami güç sınırı aşıldı: max={hiz.max():.3f} > {sim.PMAX:.3f}")
        if hiz.sum() > cap + 1e-6:
            raise AssertionError(f"Kapasite ihlali: {hiz.sum():.3f} > {cap:.3f}")

        hiz_gecmisi[t, aktif] = hiz
        toplam_guc[t] = float(hiz.sum())
        teslim[aktif] += np.minimum(hiz * DT_H, e_gercek[aktif] - teslim[aktif])

    return teslim, toplam_guc, hiz_gecmisi


def kontrolsuz_profil(
    giris: np.ndarray,
    ayril: np.ndarray,
    e_gercek: np.ndarray,
    max_adim: int = 96,
) -> np.ndarray:
    """Kapasite kısıtı olmadan, araçların maksimum güçle (PMAX) şarj profili."""
    n = len(giris)
    teslim = np.zeros(n)
    tam_ufuk = max(max_adim, (int(ayril.max()) + 1) if n > 0 else max_adim)
    toplam_guc = np.zeros(tam_ufuk)

    son_adim = (int(ayril.max()) + 1) if n > 0 else 0
    for t in range(son_adim):
        aktif = np.where((giris <= t) & (t < ayril) & (teslim < e_gercek - EPS))[0]
        if aktif.size == 0:
            continue
        guc = np.minimum(sim.PMAX, (e_gercek[aktif] - teslim[aktif]) / DT_H)
        toplam_guc[t] = float(guc.sum())
        teslim[aktif] += guc * DT_H

    return toplam_guc


def dakika_saat_etiketi(mutlak_dk: float) -> str:
    """Gün başından (00:00) itibaren mutlak dakikayı HH:MM veya '+1g HH:MM' biçimine çevirir."""
    dk_int = max(0, int(round(float(mutlak_dk))))
    gun_farki = dk_int // 1440
    gun_ici = dk_int % 1440
    saat = gun_ici // 60
    dakika = gun_ici % 60
    if gun_farki == 0:
        return f"{saat:02d}:{dakika:02d}"
    return f"+{gun_farki}g {saat:02d}:{dakika:02d}"


def arac_neden_aciklamasi(
    arac_idx: int,
    sat_oranlari: Dict[str, float],
    teslim_kwh: Dict[str, float],
    e_gercek: float,
    giris_dk: float,
    ayril_dk: float,
    beyan_dep_dk: Optional[float] = None,
    tahmin_dep_dk: Optional[float] = None,
    beyan_kwh: float = 0.0,
    tahmin_kwh: Optional[float] = None,
    erken_ayrildi: bool = False,
    cap_kw: float = 50.0,
    es_zamanli_arac_sayisi: int = 1,
    sure_beyan_dk: Optional[float] = None,
    sure_tahmin_dk: Optional[float] = None,
) -> Dict[str, Any]:
    """Her araç için simülasyon verilerine dayalı, kesin nedensellik iddiası içermeyen karar notu üretir."""
    nedenler = []
    detaylar = {}

    tahmin_var = (
        "mpc_tahmin_guvenli" in sat_oranlari
        and tahmin_kwh is not None
        and not np.isnan(float(tahmin_kwh))
        and float(tahmin_kwh) > 0
        and (
            (sure_tahmin_dk is not None and not np.isnan(float(sure_tahmin_dk)) and float(sure_tahmin_dk) > 0)
            or (tahmin_dep_dk is not None and not np.isnan(float(tahmin_dep_dk)) and float(tahmin_dep_dk) > float(giris_dk))
        )
    )

    ok_mpc_guv = sat_oranlari.get("mpc_tahmin_guvenli", 0.0) >= 0.95 if tahmin_var else False
    ok_mpc_beyan = sat_oranlari.get("mpc_beyan", 0.0) >= 0.95
    ok_edf_beyan = sat_oranlari.get("edf_beyan", 0.0) >= 0.95
    ok_edf_guv = sat_oranlari.get("edf_tahmin_guvenli", 0.0) >= 0.95 if "edf_tahmin_guvenli" in sat_oranlari else False
    ok_fcfs = sat_oranlari.get("fcfs_beyan", 0.0) >= 0.95

    teslim_mpc_guv = teslim_kwh.get("mpc_tahmin_guvenli", 0.0)
    teslim_mpc_beyan = teslim_kwh.get("mpc_beyan", 0.0)

    sure_gercek_dk = max(0.0, float(ayril_dk) - float(giris_dk))
    sure_saat = sure_gercek_dk / 60.0

    if sure_beyan_dk is not None and not np.isnan(float(sure_beyan_dk)):
        sure_beyan_dk_val = max(0.0, float(sure_beyan_dk))
        mutlak_beyan_dep_dk = float(giris_dk) + sure_beyan_dk_val
    elif beyan_dep_dk is not None and not np.isnan(float(beyan_dep_dk)):
        mutlak_beyan_dep_dk = float(beyan_dep_dk)
        sure_beyan_dk_val = max(0.0, mutlak_beyan_dep_dk - float(giris_dk))
    else:
        sure_beyan_dk_val = sure_gercek_dk
        mutlak_beyan_dep_dk = float(ayril_dk)
    sure_beyan_saat = sure_beyan_dk_val / 60.0

    if sure_tahmin_dk is not None and not np.isnan(float(sure_tahmin_dk)):
        sure_tahmin_dk_val = max(0.0, float(sure_tahmin_dk))
        mutlak_tahmin_dep_dk = float(giris_dk) + sure_tahmin_dk_val
    elif tahmin_dep_dk is not None and not np.isnan(float(tahmin_dep_dk)):
        mutlak_tahmin_dep_dk = float(tahmin_dep_dk)
        sure_tahmin_dk_val = max(0.0, mutlak_tahmin_dep_dk - float(giris_dk))
    else:
        sure_tahmin_dk_val = 0.0
        mutlak_tahmin_dep_dk = float(giris_dk)
    sure_tahmin_saat = sure_tahmin_dk_val / 60.0

    giris_saat_str = dakika_saat_etiketi(giris_dk)
    ayril_saat_str = dakika_saat_etiketi(ayril_dk)
    beyan_cikis_saat_str = dakika_saat_etiketi(mutlak_beyan_dep_dk)
    tahmin_cikis_saat_str = dakika_saat_etiketi(mutlak_tahmin_dep_dk)

    maks_mumkun_kwh = sim.PMAX * sure_saat

    # 1. Süre ve Soket Gücü Sınırı
    if e_gercek > maks_mumkun_kwh:
        nedenler.append({
            "baslik": "Olası Neden: Kalış Süresi ve Soket Gücü Sınırı",
            "kategori": "FIZIKSEL_LIMIT",
            "metin": (
                f"Aracın otoparkta kaldığı süre ({sure_gercek_dk:.1f} dk / {sure_saat:.1f} sa, "
                f"{giris_saat_str}–{ayril_saat_str}), talep edilen {e_gercek:.1f} kWh enerjiyi "
                f"azami soket gücünde ({sim.PMAX:.1f} kW) tamamlamak için yeterli olmayabilir "
                f"(bu sürede üst sınır: {maks_mumkun_kwh:.1f} kWh)."
            ),
            "derece": "kritik",
        })
    elif cap_kw < es_zamanli_arac_sayisi * 3.68:
        detaylar["sebeke_baskisi"] = "Yüksek eşzamanlı talep: Trafo kapasitesi tüm bağlı araçlara aynı anda taban güç sağlamaya yetmeyebilir."

    # 2. Kapasite Rezervasyonu Analizi (yalnızca tahmin yöntemi çalıştırıldıysa)
    if tahmin_var and (teslim_mpc_guv < teslim_mpc_beyan - 0.5 or (not ok_mpc_guv and ok_mpc_beyan)):
        nedenler.append({
            "baslik": "Olası Neden: Hayalet Kapasite Rezervasyonu (Çalışma Hipotezi)",
            "kategori": "MPC_TILSIMI",
            "metin": (
                f"Olası neden: MPC (kuantil oranı) yönteminin q80 enerji ({float(tahmin_kwh):.1f} kWh) ve "
                f"q20 süre ({sure_tahmin_dk_val:.1f} dk / {sure_tahmin_saat:.1f} sa, öngörülen çıkış {tahmin_cikis_saat_str}) "
                f"varsayımlarıyla erken adımlarda kapasiteyi diğer araçlara ayırmış olması bu durumla ilişkili olabilir "
                f"(MPC kuantil oranı: {teslim_mpc_guv:.1f} kWh, MPC Beyan: {teslim_mpc_beyan:.1f} kWh)."
            ),
            "derece": "uyari",
        })
    elif tahmin_var and teslim_mpc_guv > teslim_mpc_beyan + 0.5:
        nedenler.append({
            "baslik": "Olası Neden: Erken Ayrılış ve Kuantil Oranı Etkisi",
            "kategori": "TAHMIN_AVANTAJI",
            "metin": (
                f"Olası neden: q20 süre tahmininin ({sure_tahmin_dk_val:.1f} dk / {sure_tahmin_saat:.1f} sa, "
                f"öngörülen çıkış {tahmin_cikis_saat_str}) beyan süresine ({sure_beyan_dk_val:.1f} dk / {sure_beyan_saat:.1f} sa, "
                f"beyan çıkışı {beyan_cikis_saat_str}) göre daha kısa olması, gücün erken adımlarda verilmesiyle ilişkili olabilir "
                f"(MPC kuantil oranı: {teslim_mpc_guv:.1f} kWh, MPC Beyan: {teslim_mpc_beyan:.1f} kWh)."
            ),
            "derece": "olumlu",
        })

    # 3. EDF Termin Önceliği Analizi
    if tahmin_var and ok_edf_guv and not ok_mpc_guv:
        nedenler.append({
            "baslik": "Olası Neden: EDF Termin Önceliği",
            "kategori": "EDF_USTUNLUK",
            "metin": (
                "Olası neden: EDF yönteminin gelecek adımlar için kapasite ayırmadan mevcut gücü "
                "yaklaşan ayrılış terminine göre dağıtması bu aracın hedefine ulaşmasıyla ilişkili olabilir."
            ),
            "derece": "olumlu",
        })

    # 4. Erken Ayrılma Durumu
    if erken_ayrildi:
        sapma_dk = max(0.0, mutlak_beyan_dep_dk - float(ayril_dk))
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
                "baslik": "Erken Ayrılış (Hedef Karşılandı)",
                "kategori": "ERKEN_AYRILMA_ZARARSIZ",
                "metin": (
                    f"Sürücü beyan ettiği süreden ({sure_beyan_dk_val:.1f} dk, beyan çıkışı {beyan_cikis_saat_str}) "
                    f"{sapma_dk:.0f} dk ({sapma_saat:.1f} sa) önce ({ayril_saat_str}) ayrıldı; ancak mevcut park süresi "
                    f"({sure_gercek_dk:.1f} dk / {sure_saat:.1f} sa) yeterli olduğu için beyana dayalı yöntemler "
                    f"(FCFS, EDF Beyan, MPC Beyan) enerji kaybına uğramadan hedefi (≥%95) tamamladı."
                ),
                "derece": "bilgi",
            })
        else:
            nedenler.append({
                "baslik": "Olası Neden: Erken Ayrılış ve Eksik Teslim",
                "kategori": "ERKEN_AYRILMA",
                "metin": (
                    f"Olası neden: Sürücünün beyan ettiği süreden ({sure_beyan_dk_val:.1f} dk, beyan çıkışı {beyan_cikis_saat_str}) "
                    f"{sapma_dk:.0f} dk ({sapma_saat:.1f} sa) önce ({ayril_saat_str}) ayrılması, şarjın tamamlanamamasıyla ilişkili olabilir. "
                    f"Hedef eşiğinin (%95) altında kalan beyan tabanlı yöntemler: {', '.join(eksik_beyan_yontemleri)}."
                ),
                "derece": "uyari",
            })

    # 5. FCFS Sıralama Farkı
    if not ok_fcfs and (ok_edf_beyan or ok_mpc_beyan):
        nedenler.append({
            "baslik": "Olası Neden: FCFS Varış Sırası Önceliği",
            "kategori": "FCFS_KUSURU",
            "metin": (
                "Olası neden: FCFS yönteminin ayrılış aciliyetini gözetmeden varış sırasına göre güç tahsisi yapması, "
                "bu aracın hedef enerjinin altında kalmasıyla ilişkili olabilir."
            ),
            "derece": "bilgi",
        })

    if not nedenler:
        ref_oran = sat_oranlari.get("mpc_tahmin_guvenli", sat_oranlari.get("mpc_beyan", sat_oranlari.get("edf_beyan", 1.0)))
        if ref_oran >= 0.95:
            nedenler.append({
                "baslik": "Planlı Şarj Tamamlandı",
                "kategori": "STANDART",
                "metin": (
                    f"Araç kalış süresi ({sure_gercek_dk:.1f} dk / {sure_saat:.1f} sa, {giris_saat_str}–{ayril_saat_str}) "
                    f"içinde hedef karşılama eşiğine (%{ref_oran * 100:.1f}) ulaştı."
                ),
                "derece": "olumlu",
            })
        else:
            nedenler.append({
                "baslik": "Belirgin Tekil Neden Tespit Edilemedi",
                "kategori": "BELIRSIZ",
                "metin": (
                    f"Mevcut telemetriyle tek bir baskın neden belirlenemedi; eşzamanlı trafo talebi ve ayrık güç kademeleri "
                    f"teslim oranıyla (%{ref_oran * 100:.1f}) ilişkili olabilir."
                ),
                "derece": "bilgi",
            })

    return {
        "nedenler": nedenler,
        "detaylar": detaylar,
        "ozet_hukum": nedenler[0]["baslik"],
    }


def beyan_oranlarini_yukle() -> Dict[str, Any]:
    """2019 H1 eğitim kümesinden öğrenilmiş ampirik beyan kuantillerini yükler."""
    json_yolu = PROJE_KOK / "config" / "beyan_oranlari.json"
    if json_yolu.exists():
        with open(json_yolu, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    # Geriye dönük güvenlik fallback'i
    return {
        "sure_oranlari": {"q20": 0.8889, "q50": 1.1062, "q80": 1.6352},
        "enerji_oranlari": {"q20": 0.3549, "q50": 0.6074, "q80": 0.8446},
    }


def esit_paylasim_kurali(t: int, kalan: np.ndarray, dep: np.ndarray, giris: np.ndarray, cap: float) -> np.ndarray:
    """Aktif araçlara dinamik eşit güç paylaşımı kuralı.

    Her adımda enerjisi henüz dolmamış (kalan > EPS) aktif araçlara
    kapasiteyi eşit paylaştırır: p_esit = _taban_seviye(min(PMAX, cap / m)).
    Her aracın anlık talebi (kalan / DT_H) tavan seviyesini aşamaz.
    Artan kapasite, varış sırasına (FCFS) göre bir üst ayrık kademeye yükseltilerek
    ve ardından inanılan enerjisi dolmuş araçlara fırsatçı dağıtılarak değerlendirilir.
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
    # Kalan gücü varış sırasına göre kademe yükselterek dağıt
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
) -> Tuple[pd.DataFrame, pd.Timestamp, str, str, bool]:
    """Seçilen senaryo ve gün için simülasyona hazır oturum veri çerçevesi üretir veya yükler.
    
    Gerçek ACN gününde veri yoksa sessizce başka güne düşmez, açık ValueError üretir.
    Dönen 5. eleman (acn_kalibrasyonu) ACN ampirik kalibrasyonunun geçerliliğini belirtir.
    """
    if senaryo_id not in SENARYOLAR:
        raise ValueError(
            f"Geçersiz senaryo kimliği: '{senaryo_id}'. "
            f"Desteklenen senaryolar: {', '.join(SENARYOLAR.keys())}"
        )
    cfg = SENARYOLAR[senaryo_id]
    secili_gun = str(gun_secimi).strip() if gun_secimi else cfg["varsayilan_gun"]

    try:
        pd.to_datetime(secili_gun, format="%Y-%m-%d", errors="raise")
    except Exception as exc:
        raise ValueError(f"Geçersiz tarih biçimi: '{secili_gun}'. Beklenen biçim: YYYY-AA-GG.") from exc

    # 2019 H1 eğitim kümesinden öğrenilmiş ampirik beyan oranı kuantillerini yükle
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
        if not csv_yolu.exists():
            raise FileNotFoundError(
                f"Gerçek saha veri dosyası bulunamadı: '{csv_dosya}'. "
                f"Kontrol edilen konumlar: '{PROJE_KOK / csv_dosya}', '{csv_yolu}'."
            )

        df = veri_hijyeni.temizle(csv_yolu, sadece_beyanli=True)
        saha_id = cfg.get("site_id", "0001")
        gd = df[(df["gun"] == secili_gun) & (df["siteID"] == saha_id)].copy()
        if len(gd) == 0:
            # Alternatif saha kontrolü
            gd = df[df["gun"] == secili_gun].copy()
            if len(gd) == 0:
                raise ValueError(f"Seçilen tarihte ({secili_gun}) gerçek saha verisinde oturum bulunamadı.")

        min_ilk = pd.to_numeric(gd["minutesAvailable_ilk"], errors="coerce").where(lambda s: s > 0, 480.0).fillna(480.0)
        kwh_ilk = pd.to_numeric(gd["kWhRequested_ilk"], errors="coerce").where(lambda s: s > 0, 12.0).fillna(12.0)

        # Tahmin sütunlarını oluştur (q20, q50, q80) — 2019 H1 eğitim kümesinden öğrenilmiş oranlar
        gd["tahmin_sure_q20"] = np.maximum(30.0, min_ilk * q_sure_20)
        gd["tahmin_sure_q50"] = np.maximum(30.0, min_ilk * q_sure_50)
        gd["tahmin_sure_q80"] = np.maximum(30.0, min_ilk * q_sure_80)

        gd["tahmin_kwh_q20"] = np.clip(kwh_ilk * q_kwh_20, 1.0, 95.0)
        gd["tahmin_kwh_q50"] = np.clip(kwh_ilk * q_kwh_50, 1.0, 95.0)
        gd["tahmin_kwh_q80"] = np.clip(kwh_ilk * q_kwh_80, 1.0, 95.0)

        t0 = pd.Timestamp(secili_gun).tz_localize("America/Los_Angeles").tz_convert("UTC")
        veri_kaynagi_etiketi = f"GERÇEK SAHA VERİSİ (ACN-Data {saha_id} — {secili_gun})"
        acn_kalibrasyonu = True

    else:
        # Sentetik Senaryo Üretimi (sentetik_v2 modülü ile)
        df_sentetik = sentetik_v2.uret(
            senaryo_id=senaryo_id,
            gun=3,
            baslangic_tarihi=secili_gun,
            tohum=tohum,
        )
        # Sadece seçilen günü filtrele
        df_sentetik["gun"] = pd.to_datetime(df_sentetik["connectionTime"]).dt.strftime("%Y-%m-%d")
        gd = df_sentetik[df_sentetik["gun"] == secili_gun].copy()
        if len(gd) == 0:
            gd = df_sentetik.iloc[:20].copy()

        # Sentetik tahminleri ekle — 2019 H1 ampirik kuantilleri baseline olarak kullanılır
        gd["connectionTime"] = pd.to_datetime(gd["connectionTime"], utc=True)
        gd["disconnectTime"] = pd.to_datetime(gd["disconnectTime"], utc=True)
        gd["requestedDeparture"] = pd.to_datetime(gd["requestedDeparture"], utc=True)

        min_ilk = pd.to_numeric(gd["minutesAvailable_ilk"], errors="coerce").where(lambda s: s > 0, 480.0).fillna(480.0)
        kwh_ilk = pd.to_numeric(gd["kWhRequested_ilk"], errors="coerce").where(lambda s: s > 0, 12.0).fillna(12.0)

        gd["tahmin_sure_q20"] = np.maximum(30.0, min_ilk * q_sure_20)
        gd["tahmin_sure_q50"] = np.maximum(30.0, min_ilk * q_sure_50)
        gd["tahmin_sure_q80"] = np.maximum(30.0, min_ilk * q_sure_80)

        gd["tahmin_kwh_q20"] = np.clip(kwh_ilk * q_kwh_20, 1.0, 85.0)
        gd["tahmin_kwh_q50"] = np.clip(kwh_ilk * q_kwh_50, 1.0, 85.0)
        gd["tahmin_kwh_q80"] = np.clip(kwh_ilk * q_kwh_80, 1.0, 85.0)

        t0 = pd.Timestamp(secili_gun).tz_localize("Europe/Istanbul").tz_convert("UTC")
        veri_kaynagi_etiketi = f"SENTETİK MODEL (VARSAYIM — {cfg['ad']})"
        acn_kalibrasyonu = bool(getattr(df_sentetik, "attrs", {}).get("acn_kalibrasyonu", False))

    return gd, t0, secili_gun, veri_kaynagi_etiketi, acn_kalibrasyonu


def simulasyon_calistir_api(
    senaryo_id: str = "isyeri_gunduz",
    f: float = 0.5,
    cap_kw_override: Optional[float] = None,
    gun_secimi: Optional[str] = None,
    tohum: int = 42,
) -> Dict[str, Any]:
    """Web arayüzü için tek günlük tam simülasyonu yürütür ve JSON sözleşmesine uygun döndürür."""
    f = float(f)
    f = max(0.3, min(1.2, f))

    try:
        gd, t0, secili_gun, veri_kaynagi_etiketi, acn_kalibrasyonu = oturumlari_hazirla(senaryo_id, gun_secimi=gun_secimi, tohum=tohum)
    except (ValueError, FileNotFoundError) as exc:
        return {"hata": str(exc), "senaryo_id": senaryo_id}
    kaynaklar = deney_v2.inanilan_kaynaklar(gd)

    giris = np.ceil(deney_v2.adimlar(gd["connectionTime"], t0)).astype(int)
    ayril = np.floor(deney_v2.adimlar(gd["disconnectTime"], t0)).astype(int)
    gec = ayril > giris

    if gec.sum() < 2:
        return {"hata": "Seçilen günde yeterli oturum bulunamadı.", "n": int(gec.sum())}

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

    # Dinamik simülasyon ufku: en az 96 adım (24 saat) veya en geç ayrılış adımını kapsayacak uzunluk
    ufuk_adim = max(96, int(ayril.max()) + 1)
    zaman_etiketleri = zaman_etiketleri_uret(ufuk_adim)

    # Kontrolsüz Yük Profili
    kontrolsuz_guc = kontrolsuz_profil(giris, ayril, e_gercek, max_adim=ufuk_adim)

    # Algoritma Koşuları
    yontem_profilleri = {}
    yontem_teslim = {}
    yontem_kpi = {}
    hiz_matrisleri = {}

    cfg = SENARYOLAR.get(senaryo_id, {})
    sentetik_mi = cfg.get("veri_turu") != "GERCEK"

    if sentetik_mi:
        # Sentetik senaryolarda ACN'den öğrenilen kuantil oranı kalibre olmadığı için tahmin yöntemleri gizlenir
        secili_yontemler = {
            "fcfs_beyan": ("fcfs", "beyan"),
            "esit_beyan": ("esit", "beyan"),
            "edf_beyan": ("edf", "beyan"),
            "mpc_beyan": ("mpc", "beyan"),
        }
        kuantil_kalibrasyon_notu = "Sentetik senaryoda kuantil oranı kalibre değil"
        tahmin_aktif = False
    else:
        secili_yontemler = {
            "fcfs_beyan": ("fcfs", "beyan"),
            "esit_beyan": ("esit", "beyan"),
            "edf_beyan": ("edf", "beyan"),
            "edf_tahmin_guvenli": ("edf", "tahmin_guvenli"),
            "mpc_beyan": ("mpc", "beyan"),
            "mpc_tahmin_guvenli": ("mpc", "tahmin_guvenli"),
            "mpc_hibrit_asimetrik": ("mpc", "hibrit_asimetrik"),
        }
        kuantil_kalibrasyon_notu = None
        tahmin_aktif = True

    for y_kod, (alg, kaynak_ad) in secili_yontemler.items():
        ts_series, kwh_arr = kaynaklar[kaynak_ad]
        ts_sub = ts_series.loc[gd.index][gec].reset_index(drop=True)
        inan_dep = np.maximum(np.floor(deney_v2.adimlar(ts_sub, t0)), giris + 1).astype(int)
        inan_kwh = np.asarray(kwh_arr)[gd.index.get_indexer(gd.index)][gec]

        if alg == "mpc":
            yont_func = sim.mpc
        elif alg == "esit":
            yont_func = esit_paylasim_kurali
        else:
            yont_func = sim.kural(alg)

        teslim, toplam_guc, hiz_matrisi = simule_ve_profil_cikar(
            giris, ayril, e_gercek, inan_dep, inan_kwh, cap_kw, yont_func, max_adim=ufuk_adim
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

    # Araç Bazlı Detay Telemetrisi ve Explainability ("Neden?")
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
            # Aktif şarj dakikası sayısı
            arac_sarj_dakikalari[y_kod] = int(np.sum(hiz_matrisleri[y_kod][:, i] > 0.1) * 15)

        neden_analizi = arac_neden_aciklamasi(
            arac_idx=i,
            sat_oranlari=arac_sat,
            teslim_kwh=arac_teslim,
            e_gercek=float(e_gercek[i]),
            giris_dk=float(g_adim * 15.0),
            ayril_dk=float(a_adim * 15.0),
            beyan_dep_dk=float(g_adim * 15.0 + beyan_dk),
            tahmin_dep_dk=float(g_adim * 15.0 + tahmin_dep_dk) if "mpc_tahmin_guvenli" in secili_yontemler else None,
            beyan_kwh=float(row.get("kWhRequested_ilk", e_gercek[i] * 1.2)),
            tahmin_kwh=float(row.get("tahmin_kwh_q80", e_gercek[i] * 1.1)) if "mpc_tahmin_guvenli" in secili_yontemler else None,
            erken_ayrildi=bool(erken[i]),
            cap_kw=cap_kw,
            es_zamanli_arac_sayisi=int(np.sum((giris <= a_adim) & (ayril >= g_adim))),
            sure_beyan_dk=float(beyan_dk),
            sure_tahmin_dk=float(tahmin_dep_dk) if "mpc_tahmin_guvenli" in secili_yontemler else None,
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
        "kuantil_kalibrasyon_notu": kuantil_kalibrasyon_notu,
        "acn_kalibrasyonu": acn_kalibrasyonu,
        "tahmin_aktif": tahmin_aktif,
        "sentetik_mi": sentetik_mi,
    }


def kapasite_danismani_hesapla(
    senaryo_id: str = "isyeri_gunduz",
    gun_secimi: Optional[str] = None,
    tohum: int = 42,
    aday_kapasiteler: Optional[List[float]] = None,
    arama_cozunurlugu_kw: float = 0.5,
    esitlik_toleransi_kw: float = 0.5,
    cok_gunlu: bool = False,
) -> Dict[str, Any]:
    """Kullanıcının seçtiği senaryo için FCFS, EDF, Eşit Paylaşım ve MPC yöntemlerinin
    başarı kriterini (hedef karşılama >= %95 VE kaçırılan araç <= 1) sağlayan asgari
    trafo kapasitesini (kW) 0.5 kW çözünürlükle hesaplar.
    """
    try:
        gd, t0, secili_gun, veri_kaynagi_etiketi, acn_kalibrasyonu = oturumlari_hazirla(
            senaryo_id, gun_secimi=gun_secimi, tohum=tohum
        )
    except (ValueError, FileNotFoundError) as exc:
        return {"hata": str(exc), "senaryo_id": senaryo_id}
    cfg = SENARYOLAR.get(senaryo_id, SENARYOLAR["isyeri_gunduz"])
    kaynaklar = deney_v2.inanilan_kaynaklar(gd)

    giris = np.ceil(deney_v2.adimlar(gd["connectionTime"], t0)).astype(int)
    ayril = np.floor(deney_v2.adimlar(gd["disconnectTime"], t0)).astype(int)
    gec = ayril > giris

    if gec.sum() < 2:
        return {
            "hata": "Seçilen senaryo ve günde kapasite analizi için yeterli oturum bulunamadı.",
            "arac_sayisi": int(gec.sum()),
            "senaryo_id": senaryo_id,
        }

    giris = giris[gec]
    ayril = ayril[gec]
    e_gercek = gd["kWhDelivered"].to_numpy(dtype=float)[gec]
    n_arac = len(e_gercek)
    tepe_kw = float(sim.kontrolsuz_tepe(giris, ayril, e_gercek))
    nominal_kap_kw = cfg.get("nominal_trafo_kapasitesi_kw")

    # Fiziksel süre ve güç yetersizliği denetimi (PMAX hızında sınırsız kapasitede bile dolamayacak araçlar)
    sure_saat = (ayril - giris) * sim.DT_H
    fiziksel_imkansiz = (sim.PMAX * sure_saat < 0.95 * e_gercek - 1e-6)
    n_fiziksel_imkansiz = int(fiziksel_imkansiz.sum())
    karsilanabilir = ~fiziksel_imkansiz
    n_karsilanabilir = int(karsilanabilir.sum())
    fiziksel_ulasilamaz = fiziksel_imkansiz
    n_ulasilamaz = n_fiziksel_imkansiz
    hedef_fiziksel_mumkun = bool(n_karsilanabilir > 0)

    # İnanılan ayrılış ve enerji değerleri (Beyan kaynağı — tüm yöntemler için ortak)
    ts_sub = kaynaklar["beyan"][0].loc[gd.index][gec].reset_index(drop=True)
    inan_dep = np.maximum(np.floor(deney_v2.adimlar(ts_sub, t0)), giris + 1).astype(int)
    inan_kwh = np.asarray(kaynaklar["beyan"][1])[gd.index.get_indexer(gd.index)][gec]

    # Taban kapasite: %5 taban seviyesi (en az birinci ayrık kademe sim.SEVIYELER[1])
    taban_kw = max(
        float(sim.SEVIYELER[1]),
        round(0.05 * tepe_kw / arama_cozunurlugu_kw) * arama_cozunurlugu_kw,
    )

    # Aday Kapasiteler (kW)
    ozel_aday_verildi = aday_kapasiteler is not None and len(aday_kapasiteler) > 0
    if ozel_aday_verildi:
        adaylar = sorted([round(float(c), 1) for c in aday_kapasiteler if c > 0])
    else:
        k_fraksiyonlar = [0.05, 0.15, 0.25, 0.35, 0.45, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
        adaylar = sorted(list(set([
            round(max(taban_kw, round(f * tepe_kw / arama_cozunurlugu_kw) * arama_cozunurlugu_kw), 1)
            for f in k_fraksiyonlar
        ])))

    yontem_tanimlari = [
        {
            "kod": "fcfs",
            "ad": "FCFS (İlk Gelen İlk Şarj)",
            "fn": sim.kural("fcfs"),
            "renk": "#EF4444",
            "aciklama": "Araçlar geliş sırasına göre tam güçle şarj edilir; ayrılış aciliyeti gözetilmez.",
        },
        {
            "kod": "edf",
            "ad": "EDF (En Erken Termin Öncelikli)",
            "fn": sim.kural("edf"),
            "renk": "#3B82F6",
            "aciklama": "Ayrılış zamanı en yakın olan araçlara öncelik verilir; dinamik kuyruk yönetimi.",
        },
        {
            "kod": "esit",
            "ad": "Aktif Araçlara Eşit Güç Paylaşımı",
            "fn": esit_paylasim_kurali,
            "renk": "#8B5CF6",
            "aciklama": "Mevcut kapasite o anda bağlı ve şarj bekleyen tüm araçlara eşit bölünür.",
        },
        {
            "kod": "mpc",
            "ad": "MPC (LP / HiGHS Optimizasyon)",
            "fn": sim.mpc,
            "renk": "#10B981",
            "aciklama": "Gelecek ufku boyunca şebeke kısıtları altında doğrusal programlama optimizasyonu.",
        },
    ]

    def _degerlendir(fn: Any, cap_val: float) -> Dict[str, Any]:
        c_f = round(float(cap_val), 1)
        teslim = sim.simule(giris, ayril, e_gercek, inan_dep, inan_kwh, c_f, fn)
        sat = teslim / np.maximum(e_gercek, 1e-6)
        ok = sat >= 0.95 - 1e-6
        if n_karsilanabilir > 0:
            ok_k = ok[karsilanabilir]
            ok_sayisi = int(ok_k.sum())
            kacirilan_arac = int(n_karsilanabilir - ok_sayisi)
            ok_orani = float(ok_sayisi / n_karsilanabilir)
            ok_yuzde = round(ok_orani * 100.0, 1)
            # TEK BAŞARI KRİTERİ: Karşılanabilir araçların >= %95'i VE en fazla 1'i kaçırılıyor
            yeterli = bool((ok_orani >= 0.95 - 1e-6) and (kacirilan_arac <= 1))
        else:
            ok_sayisi = 0
            kacirilan_arac = 0
            ok_yuzde = 0.0
            yeterli = False
        teslim_yuzde = round(float(teslim.sum() / max(e_gercek.sum(), 1e-6) * 100.0), 1)
        return {
            "kapasite_kw": c_f,
            "hedef_karsilama_yuzde": ok_yuzde,
            "teslim_orani_yuzde": teslim_yuzde,
            "kacirilan_arac_sayisi": kacirilan_arac,
            "basarili_arac_sayisi": ok_sayisi,
            "toplam_arac_sayisi": n_arac,
            "karsilanabilir_arac_sayisi": n_karsilanabilir,
            "fiziksel_imkansiz_arac_sayisi": n_fiziksel_imkansiz,
            "fiziksel_ulasilamaz_arac_sayisi": n_fiziksel_imkansiz,
            "arac_ozeti": f"{ok_sayisi}/{n_karsilanabilir} araç" if n_karsilanabilir > 0 else f"0/{n_arac} araç",
            "yeterli": yeterli,
        }

    yontem_sonuclari = []
    for y_cfg in yontem_tanimlari:
        tarama_harita: Dict[float, Dict[str, Any]] = {}
        for c in adaylar:
            nokta = _degerlendir(y_cfg["fn"], c)
            tarama_harita[nokta["kapasite_kw"]] = nokta

        # Tepe kapasite testi
        tepe_noktasi = tarama_harita.get(round(tepe_kw, 1)) or _degerlendir(y_cfg["fn"], tepe_kw)
        tarama_harita[tepe_noktasi["kapasite_kw"]] = tepe_noktasi

        asgari_kap = None
        if ozel_aday_verildi:
            # Özel aday kapasiteler verildiğinde yalnızca bu adaylar değerlendirilir
            for c_oz in adaylar:
                if tarama_harita[c_oz]["yeterli"]:
                    asgari_kap = c_oz
                    break
        elif tepe_noktasi["yeterli"]:
            # Aday taramasından daraltılmış aralık bul (Hızlı İkili Arama Hızlandırması)
            basarili_adaylar = [c for c in adaylar if tarama_harita.get(c, {}).get("yeterli")]
            if basarili_adaylar:
                c_high = min(basarili_adaylar)
                basarisiz_alt = [c for c in adaylar if c < c_high and not tarama_harita.get(c, {}).get("yeterli")]
                c_low = max(basarisiz_alt) if basarisiz_alt else taban_kw
            else:
                c_high = tepe_kw
                c_low = max(adaylar)

            low_idx = int(round(c_low / arama_cozunurlugu_kw))
            high_idx = int(round(c_high / arama_cozunurlugu_kw))
            best_kw = c_high

            while low_idx <= high_idx:
                mid_idx = (low_idx + high_idx) // 2
                c_mid = round(mid_idx * arama_cozunurlugu_kw, 1)
                nokta = tarama_harita.get(c_mid) or _degerlendir(y_cfg["fn"], c_mid)
                tarama_harita[c_mid] = nokta
                if nokta["yeterli"]:
                    best_kw = c_mid
                    high_idx = mid_idx - 1
                else:
                    low_idx = mid_idx + 1
            asgari_kap = best_kw

        # Monotonluk kontrolü: C > asgari_kap olan noktalarda yeterli == False denetimi
        monoton_degil = False
        ilk_kalici_gecis_kw = asgari_kap
        if asgari_kap is not None:
            ust_noktalar = sorted([k for k in tarama_harita.keys() if k > asgari_kap + 1e-6])
            ihlal_noktalari = [k for k in ust_noktalar if not tarama_harita[k]["yeterli"]]
            if ihlal_noktalari:
                monoton_degil = True
                son_ihlal = max(ihlal_noktalari)
                kalici_adaylar = [k for k in ust_noktalar if k > son_ihlal and tarama_harita[k]["yeterli"]]
                ilk_kalici_gecis_kw = min(kalici_adaylar) if kalici_adaylar else round(tepe_kw, 1)

        tarama = [tarama_harita[k] for k in sorted(tarama_harita.keys())]

        # Başarılı noktadaki araç özeti; asgari kapasite bulunamadığında tepe kapasitedeki gerçek durum korunur
        basarili_nokta = tarama_harita.get(asgari_kap) if asgari_kap is not None else None
        en_iyi_nokta = basarili_nokta or tepe_noktasi
        arac_ozeti_str = en_iyi_nokta["arac_ozeti"] if en_iyi_nokta else f"0/{n_arac} araç"
        kacirilan_str = en_iyi_nokta["kacirilan_arac_sayisi"] if en_iyi_nokta else 0
        tasarruf = round((tepe_kw - asgari_kap) / tepe_kw * 100.0, 1) if asgari_kap is not None and tepe_kw > 0 else 0.0

        yontem_sonuclari.append({
            "kod": y_cfg["kod"],
            "ad": y_cfg["ad"],
            "renk": y_cfg["renk"],
            "aciklama": y_cfg["aciklama"],
            "asgari_kapasite_kw": asgari_kap,
            "monoton_degil": monoton_degil,
            "ilk_kalici_gecis_kw": ilk_kalici_gecis_kw,
            "basarili": asgari_kap is not None,
            "arac_ozeti": arac_ozeti_str,
            "kacirilan_arac_sayisi": kacirilan_str,
            "fiziksel_imkansiz_arac_sayisi": n_fiziksel_imkansiz,
            "karsilanabilir_arac_sayisi": n_karsilanabilir,
            "tasarruf_orani_yuzde": tasarruf,
            "tarama": tarama,
        })

    # En düşük asgari kapasiteyi sağlayan yöntem(ler)i tolerans dahilinde belirle
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

        # Matris tablosu için önerilen kapasiteyi taramalara dahil et
        if onerilen_kap is not None and all(abs(c - onerilen_kap) > 0.05 for c in adaylar):
            adaylar = sorted(list(set(adaylar + [onerilen_kap])))
            for y_idx, y_cfg in enumerate(yontem_tanimlari):
                mevcut_harita = {pt["kapasite_kw"]: pt for pt in yontem_sonuclari[y_idx]["tarama"]}
                if onerilen_kap not in mevcut_harita:
                    mevcut_harita[onerilen_kap] = _degerlendir(y_cfg["fn"], onerilen_kap)
                    yontem_sonuclari[y_idx]["tarama"] = [mevcut_harita[k] for k in sorted(mevcut_harita.keys())]

        if esitlik_var:
            # Eşitlik durumunda yöntem adlarını listele: "EDF ve MPC eşit: 28,5 kW"
            kisa_adlar = [y["ad"].split(" (")[0].replace("Aktif Araçlara ", "") for y in en_iyiler]
            if len(kisa_adlar) == 2:
                esit_metin = f"{kisa_adlar[0]} ve {kisa_adlar[1]}"
            else:
                esit_metin = f"{', '.join(kisa_adlar[:-1])} ve {kisa_adlar[-1]}"
            onerilen_yontem = f"{esit_metin} eşit: {onerilen_kap:.1f} kW".replace(".", ",")
        else:
            onerilen_yontem = f"{en_iyiler[0]['ad']}: {onerilen_kap:.1f} kW".replace(".", ",")
    else:
        esitlik_var = False
        esit_yontemler = []
        esit_yontem_kodlari = []
        onerilen_kap = None
        onerilen_yontem = "Hedef karşılanamadı (Fiziksel sınır)" if not hedef_fiziksel_mumkun else "Belirlenemedi"

    # Trafo yeterlilik durumu ve sade metin
    if onerilen_kap is not None:
        if nominal_kap_kw is not None:
            if onerilen_kap <= nominal_kap_kw:
                trafo_durumu_kisa = f"Mevcut trafo yeterli: kontrolsüz tepe {tepe_kw:.1f} kW"
            else:
                trafo_durumu_kisa = f"Mevcut trafo yetersiz: kontrolsüz tepe {tepe_kw:.1f} kW"
            kapasite_ozet_metni = (
                f"{trafo_durumu_kisa} (asgari güç {onerilen_kap:.1f} kW, "
                f"mevcut trafo {float(nominal_kap_kw):.1f} kW)."
            )
        else:
            trafo_durumu_kisa = f"Asgari güç {onerilen_kap:.1f} kW, kontrolsüz tepe {tepe_kw:.1f} kW"
            kapasite_ozet_metni = (
                f"Bu senaryo için hesaplanan asgari trafo gücü {onerilen_kap:.1f} kW "
                f"(kontrolsüz tepe {tepe_kw:.1f} kW)."
            )
    else:
        trafo_durumu_kisa = "Hedef fiziksel olarak karşılanamadı"
        kapasite_ozet_metni = (
            f"Fiziksel süre veya maksimum soket gücü ({sim.PMAX:.1f} kW) sınırı nedeniyle "
            f"%95 hedef karşılama ve azami 1 araç kaçırma kriterine hiçbir güç seviyesinde ulaşılamamaktadır "
            f"(fiziksel erişilemez: {n_ulasilamaz}/{n_arac} araç)."
        )

    sonuc = {
        "senaryo_id": senaryo_id,
        "senaryo_ad": cfg["ad"],
        "etiket": cfg["etiket"],
        "veri_turu": cfg["veri_turu"],
        "sentetik_mi": cfg["veri_turu"] != "GERCEK",
        "acn_kalibrasyonu": acn_kalibrasyonu,
        "veri_kaynagi_etiketi": veri_kaynagi_etiketi,
        "tarih": secili_gun,
        "ornek_gun": True,
        "arac_sayisi": n_arac,
        "kontrolsuz_tepe_kw": round(tepe_kw, 1),
        "nominal_trafo_kapasitesi_kw": round(float(nominal_kap_kw), 1) if nominal_kap_kw is not None else None,
        "arama_cozunurlugu_kw": arama_cozunurlugu_kw,
        "esitlik_toleransi_kw": esitlik_toleransi_kw,
        "hedef_olcutu": "Karşılanabilir araçların ≥%95'i ve azami 1 kaçırılan araç",
        "fiziksel_ulasilamaz_arac_sayisi": n_fiziksel_imkansiz,
        "fiziksel_imkansiz_arac_sayisi": n_fiziksel_imkansiz,
        "karsilanabilir_arac_sayisi": n_karsilanabilir,
        "hedef_fiziksel_mumkun": hedef_fiziksel_mumkun,
        "aday_kapasiteler_kw": adaylar,
        "yontemler": yontem_sonuclari,
        "esitlik_var": esitlik_var,
        "esit_yontemler": esit_yontemler,
        "esit_yontem_kodlari": esit_yontem_kodlari,
        "onerilen_yontem": onerilen_yontem,
        "onerilen_asgari_kapasite_kw": onerilen_kap,
        "azami_trafo_tasarrufu_yuzde": round((tepe_kw - onerilen_kap) / tepe_kw * 100.0, 1) if onerilen_kap is not None and tepe_kw > 0 else 0.0,
        "trafo_durumu": trafo_durumu_kisa,
        "kapasite_ozet_metni": kapasite_ozet_metni,
    }

    if cok_gunlu:
        sonuc["cok_gunlu_analiz"] = cok_gunlu_kapasite_analizi(
            senaryo_id=senaryo_id,
            n_gun=20,
            tohum_baslangic=tohum,
            gun_secimi=secili_gun,
            gun_1_sonuc=sonuc,
        )

    return sonuc


def cok_gunlu_kapasite_analizi(
    senaryo_id: str = "isyeri_gunduz",
    n_gun: int = 20,
    tohum_baslangic: int = 42,
    gun_secimi: Optional[str] = None,
    gun_1_sonuc: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """En az 20 gün veya sentetik tohum üzerinden 4 yöntemin asgari trafo gücünü (kW)
    hızlı ikili arama ile tarayarak medyan, p10 ve p90 değerlerini hesaplar."""
    cfg = SENARYOLAR.get(senaryo_id, SENARYOLAR["isyeri_gunduz"])
    sentetik_mi = cfg.get("veri_turu") != "GERCEK"
    arama_cozunurlugu_kw = 0.5

    yontem_tanimlari = [
        ("fcfs", sim.kural("fcfs")),
        ("edf", sim.kural("edf")),
        ("esit", esit_paylasim_kurali),
        ("mpc", sim.mpc),
    ]

    yontem_degerleri: Dict[str, List[float]] = {
        "fcfs": [],
        "edf": [],
        "esit": [],
        "mpc": [],
    }

    gun_listesi: List[str] = []
    haric_tutulanlar: List[Dict[str, str]] = []

    # 1. Gün 1 sonucu hazır verildiyse mükerrer simülasyonu önle ve doğrudan kaydet
    gun_1_dahil = False
    if gun_1_sonuc and "yontemler" in gun_1_sonuc and not gun_1_sonuc.get("hata"):
        etiket_1 = f"Tohum {tohum_baslangic}" if sentetik_mi else (gun_secimi or cfg["varsayilan_gun"])
        gun_listesi.append(etiket_1)
        for y in gun_1_sonuc["yontemler"]:
            if y.get("asgari_kapasite_kw") is not None and y.get("kod") in yontem_degerleri:
                yontem_degerleri[y["kod"]].append(float(y["asgari_kapasite_kw"]))
        gun_1_dahil = True

    def _gun_coz(gd_sub: pd.DataFrame, t0_sub: Any, kaynaklar_sub: Dict[str, Any]) -> Tuple[Optional[Dict[str, Optional[float]]], Optional[str]]:
        giris_tam = np.ceil(deney_v2.adimlar(gd_sub["connectionTime"], t0_sub)).astype(int)
        ayril_tam = np.floor(deney_v2.adimlar(gd_sub["disconnectTime"], t0_sub)).astype(int)
        gec = ayril_tam > giris_tam

        if gec.sum() < 2:
            return None, "Yetersiz oturum"

        giris = giris_tam[gec]
        ayril = ayril_tam[gec]
        e_gercek = gd_sub["kWhDelivered"].to_numpy(dtype=float)[gec]
        tepe_kw = float(sim.kontrolsuz_tepe(giris, ayril, e_gercek))
        if tepe_kw <= 0:
            return None, "Tepe güç sıfır"
        tepe_kw = round(tepe_kw, 1)

        # Fiziksel süre ve güç yetersizliği denetimi (PMAX hızında sınırsız kapasitede bile dolamayacak araçlar)
        sure_saat = (ayril - giris) * sim.DT_H
        fiziksel_imkansiz = (sim.PMAX * sure_saat < 0.95 * e_gercek - 1e-6)
        n_fiziksel_imkansiz = int(fiziksel_imkansiz.sum())
        karsilanabilir = ~fiziksel_imkansiz
        n_karsilanabilir = int(karsilanabilir.sum())

        if n_karsilanabilir == 0:
            # Fiziksel olarak karşılanabilir araç bulunmayan gün: asgari kapasite bulunamaz
            return {kod: None for kod, _ in yontem_tanimlari}, None

        taban_kw = max(
            float(sim.SEVIYELER[1]),
            round(0.05 * tepe_kw / arama_cozunurlugu_kw) * arama_cozunurlugu_kw,
        )

        ts_sub = kaynaklar_sub["beyan"][0].loc[gd_sub.index][gec].reset_index(drop=True)
        inan_dep = np.maximum(np.floor(deney_v2.adimlar(ts_sub, t0_sub)), giris + 1).astype(int)
        inan_kwh = np.asarray(kaynaklar_sub["beyan"][1])[gd_sub.index.get_indexer(gd_sub.index)][gec]

        def _eval_hizli(fn: Any, cap_val: float) -> bool:
            c_f = round(float(cap_val), 1)
            teslim = sim.simule(giris, ayril, e_gercek, inan_dep, inan_kwh, c_f, fn)
            sat = teslim / np.maximum(e_gercek, 1e-6)
            ok = sat >= 0.95 - 1e-6
            ok_k = ok[karsilanabilir]
            ok_sayisi = int(ok_k.sum())
            kacirilan_arac = int(n_karsilanabilir - ok_sayisi)
            ok_orani = float(ok_sayisi / n_karsilanabilir)
            return bool((ok_orani >= 0.95 - 1e-6) and (kacirilan_arac <= 1))

        gun_kapasiteleri: Dict[str, Optional[float]] = {}
        for kod, fn in yontem_tanimlari:
            if not _eval_hizli(fn, tepe_kw):
                gun_kapasiteleri[kod] = None
                continue

            # Hızlı kaba aralık daraltma: tepe_kw üzerinden [0.25, 0.50, 0.75] ile aralığı daralt
            c_lo = taban_kw
            c_hi = tepe_kw
            for frac in [0.25, 0.50, 0.75]:
                c_probe = round(max(taban_kw, frac * tepe_kw / arama_cozunurlugu_kw) * arama_cozunurlugu_kw, 1)
                if c_probe > c_lo and c_probe < c_hi:
                    if _eval_hizli(fn, c_probe):
                        c_hi = c_probe
                        break
                    else:
                        c_lo = c_probe

            low_idx = int(round(c_lo / arama_cozunurlugu_kw))
            high_idx = int(round(c_hi / arama_cozunurlugu_kw))
            best_kw = c_hi

            while low_idx <= high_idx:
                mid_idx = (low_idx + high_idx) // 2
                c_mid = round(mid_idx * arama_cozunurlugu_kw, 1)
                if _eval_hizli(fn, c_mid):
                    best_kw = c_mid
                    high_idx = mid_idx - 1
                else:
                    low_idx = mid_idx + 1

            gun_kapasiteleri[kod] = best_kw

        return gun_kapasiteleri, None

    if sentetik_mi:
        # Sentetik senaryo: tohum serisi üzerinden hızlı tara
        baslangic_idx = 1 if gun_1_dahil else 0
        tohumlar = [tohum_baslangic + i for i in range(baslangic_idx, n_gun)]
        for thm in tohumlar:
            try:
                gd, t0, _, _, _ = oturumlari_hazirla(senaryo_id, tohum=thm)
                kaynaklar = deney_v2.inanilan_kaynaklar(gd)
                kapasiteler, hata_nedeni = _gun_coz(gd, t0, kaynaklar)
                if hata_nedeni:
                    haric_tutulanlar.append({"gun": f"Tohum {thm}", "neden": hata_nedeni})
                    continue
                gun_listesi.append(f"Tohum {thm}")
                if kapasiteler:
                    for kod, kap in kapasiteler.items():
                        if kap is not None:
                            yontem_degerleri[kod].append(kap)
            except Exception as exc:
                haric_tutulanlar.append({"gun": f"Tohum {thm}", "neden": str(exc)})
    else:
        # Gerçek veri: Doğru CSV dosyasını belirle ve verileri tek seferde yükle
        csv_dosya = "acn_oturumlar_temmuz_aralik.csv" if senaryo_id == "acn_gercek_ta" else "acn_oturumlar_v2.csv"
        csv_yolu = PROJE_KOK / csv_dosya
        if not csv_yolu.exists():
            csv_yolu = PROJE_KOK / "data" / "ham" / csv_dosya

        try:
            df_raw = pd.read_csv(csv_yolu, usecols=["connectionTime"])
            df_raw["gun"] = pd.to_datetime(df_raw["connectionTime"], utc=True).dt.strftime("%Y-%m-%d")
            tum_gunler = sorted(df_raw["gun"].value_counts()[lambda c: c >= 8].index.tolist())
        except Exception as exc:
            tum_gunler = []

        gun_1_adi = gun_secimi or cfg["varsayilan_gun"]
        if gun_1_dahil:
            kalan_gun_adaylari = [g for g in tum_gunler if g != gun_1_adi][: (n_gun - 1)]
        else:
            kalan_gun_adaylari = tum_gunler[:n_gun]

        for g in kalan_gun_adaylari:
            try:
                gd, t0, _, _, _ = oturumlari_hazirla(senaryo_id, gun_secimi=g)
                kaynaklar = deney_v2.inanilan_kaynaklar(gd)
                kapasiteler, hata_nedeni = _gun_coz(gd, t0, kaynaklar)
                if hata_nedeni:
                    haric_tutulanlar.append({"gun": g, "neden": hata_nedeni})
                    continue
                gun_listesi.append(g)
                if kapasiteler:
                    for kod, kap in kapasiteler.items():
                        if kap is not None:
                            yontem_degerleri[kod].append(kap)
            except Exception as exc:
                haric_tutulanlar.append({"gun": g, "neden": str(exc)})

    yontem_ozetleri = []
    yontem_adlari = {
        "fcfs": "FCFS (İlk Gelen İlk Şarj)",
        "edf": "EDF (En Erken Termin Öncelikli)",
        "esit": "Aktif Araçlara Eşit Güç Paylaşımı",
        "mpc": "MPC (LP Optimizasyon)",
    }
    toplam_gun_sayisi = len(gun_listesi)

    for kod in ["fcfs", "edf", "esit", "mpc"]:
        vals = yontem_degerleri[kod]
        if vals:
            yontem_ozetleri.append({
                "kod": kod,
                "ad": yontem_adlari[kod],
                "medyan_kw": round(float(np.median(vals)), 1),
                "p10_kw": round(float(np.percentile(vals, 10)), 1),
                "p90_kw": round(float(np.percentile(vals, 90)), 1),
                "min_kw": round(float(np.min(vals)), 1),
                "maks_kw": round(float(np.max(vals)), 1),
                "orneklem_sayisi": len(vals),
                "toplam_gun_sayisi": toplam_gun_sayisi,
                "erisme_orani_yuzde": round(len(vals) / max(toplam_gun_sayisi, 1) * 100.0, 1),
            })
        else:
            yontem_ozetleri.append({
                "kod": kod,
                "ad": yontem_adlari[kod],
                "medyan_kw": None,
                "p10_kw": None,
                "p90_kw": None,
                "min_kw": None,
                "maks_kw": None,
                "orneklem_sayisi": 0,
                "toplam_gun_sayisi": toplam_gun_sayisi,
                "erisme_orani_yuzde": 0.0,
            })

    return {
        "senaryo_id": senaryo_id,
        "toplam_gun": toplam_gun_sayisi,
        "hedef_gun_sayisi": n_gun,
        "degerlendirilen_gun_sayisi": toplam_gun_sayisi,
        "haric_tutulan_gun_sayisi": len(haric_tutulanlar),
        "haric_tutulanlar": haric_tutulanlar,
        "yontemler": yontem_ozetleri,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="ŞarjDenge AI Web Servisi")
    parser.add_argument("--senaryolar", action="store_true", help="Mevcut senaryoları JSON olarak listeler")
    parser.add_argument("--advisor", action="store_true", help="Kapasite Danışmanı analizi çalıştırır")
    parser.add_argument("--cok-gunlu", action="store_true", help="Kapasite danışmanı için çok günlü analizi çalıştırır")
    parser.add_argument("--senaryo", type=str, default="isyeri_gunduz", help="Senaryo ID")
    parser.add_argument("--f", type=float, default=0.5, help="Kapasite katsayısı f (0.4 - 1.0)")
    parser.add_argument("--cap", type=float, default=None, help="Doğrudan kW kapasite sınırı override")
    parser.add_argument("--gun", type=str, default=None, help="Tarih seçimi (YYYY-AA-GG)")
    parser.add_argument("--tohum", type=int, default=42, help="Rastgele üretim tohumu")
    parser.add_argument("--json", action="store_true", help="JSON formatında çıktı basar")

    args = parser.parse_args()

    try:
        if args.senaryolar:
            out = {"senaryolar": list(SENARYOLAR.values())}
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return

        if args.advisor:
            sonuc = kapasite_danismani_hesapla(
                senaryo_id=args.senaryo,
                gun_secimi=args.gun,
                tohum=args.tohum,
                cok_gunlu=args.cok_gunlu,
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
    except Exception as exc:
        print(json.dumps({"hata": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
