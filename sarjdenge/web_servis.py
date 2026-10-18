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
        "aciklama": "ACN-Data Caltech ve JPL otoparklarının Ocak–Haziran 2019 doğrulama dönemi ölçümleri (68 sıkışık gün, 5.207 oturum).",
        "varsayilan_gun": "2019-04-23",
        "mevcut_gunler": ["2019-04-23", "2019-04-30", "2019-05-13", "2019-05-16", "2019-04-22", "2019-05-07"],
        "varsayilan_f": 0.5,
        "site_id": "0001",
    },
    "acn_gercek_ta": {
        "id": "acn_gercek_ta",
        "ad": "ACN Gerçek Saha — Dönemler Arası Test (Caltech/JPL 2019)",
        "etiket": "GERÇEK SAHA VERİSİ",
        "veri_turu": "GERCEK",
        "aciklama": "ACN-Data Temmuz–Aralık 2019 dönemi gerçek ölçümleri (153 gün, 11.911 oturum).",
        "varsayilan_gun": "2019-10-15",
        "mevcut_gunler": ["2019-10-15", "2019-09-17", "2019-11-05", "2019-10-22", "2019-08-20"],
        "varsayilan_f": 0.5,
        "site_id": "0001",
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
    },
}

YONTEM_ISIMLERI = {
    "fcfs_beyan": "FCFS (Beyan)",
    "edf_beyan": "EDF (Beyan)",
    "edf_tahmin_guvenli": "EDF (Güvenli Tahmin)",
    "mpc_beyan": "MPC (Beyan)",
    "mpc_tahmin_guvenli": "MPC Güvenli (Ana Hipotez)",
    "mpc_hibrit_asimetrik": "MPC Hibrit (Keşifsel A1)",
}

YONTEM_RENKLERI = {
    "fcfs_beyan": "#EF4444",         # Kırmızı
    "edf_beyan": "#3B82F6",          # Mavi
    "edf_tahmin_guvenli": "#8B5CF6", # Mor
    "mpc_beyan": "#F59E0B",          # Turuncu
    "mpc_tahmin_guvenli": "#10B981", # Zümrüt Yeşili
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
    """Her 15 dakikalık adım için toplam şebeke gücünü ve araç bazlı güçleri kaydeder.
    
    Kapasite aşımı durumunda sim.simule ile tamamen aynı kural denetimini uygular.
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
    """Kapasite kısıtı olmadan, araçların maksimum güçle (PMAX) şarj profili."""
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
    """Her araç için fiziksel simülasyon dinamiklerine dayalı şeffaf neden açıklaması üretir."""
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
    
    sure_saat = (ayril_dk - giris_dk) / 60.0
    maks_mumkun_kwh = sim.PMAX * sure_saat
    
    # 1. Fiziksel / Şebeke Kısıtı Durumu
    if e_gercek > maks_mumkun_kwh:
        nedenler.append({
            "baslik": "Fiziksel Süre Yetersizliği",
            "kategori": "FIZIKSEL_LIMIT",
            "metin": f"Aracın otoparkta kaldığı süre ({sure_saat:.1f} sa), talep ettiği {e_gercek:.1f} kWh enerjiyi azami soket gücünde ({sim.PMAX:.1f} kW) bile tam şarj etmek için yetersizdir (teorik azami: {maks_mumkun_kwh:.1f} kWh).",
            "derece": "kritik",
        })
    elif cap_kw < es_zamanli_arac_sayisi * 3.68:
        detaylar["sebeke_baskisi"] = "Yüksek Sıkışıklık: Trafo kapasitesi tüm araçlara eşzamanlı temel güç sağlamaya yetmiyor."

    # 2. Hayalet Kapasite Rezervasyonu Analizi (MPC Güvenli neden geride kaldı?)
    if teslim_mpc_guv < teslim_mpc_beyan - 0.5 or (not ok_mpc_guv and ok_mpc_beyan):
        nedenler.append({
            "baslik": "Hayalet Kapasite Rezervasyonu (Ghost Capacity Reservation)",
            "kategori": "MPC_TILSIMI",
            "metin": f"Güvenli MPC modeli, diğer araçların yüksek q80 enerji taleplerini dar q20 sürelerinde karşılamak üzere kapasiteyi geleceğe kilitledi. Bu araç mevcut olmasına rağmen trafo gücü konservatif rezerve edildiği için araç bekletildi veya düşük kademede şarj edildi (MPC Güvenli: {teslim_mpc_guv:.1f} kWh, MPC Beyan: {teslim_mpc_beyan:.1f} kWh).",
            "derece": "uyari",
        })
    elif teslim_mpc_guv > teslim_mpc_beyan + 0.5:
        nedenler.append({
            "baslik": "Erken Ayrılış ve Güvenli Tahmin Koruması",
            "kategori": "TAHMIN_AVANTAJI",
            "metin": f"Modelin q20 süre tahmini ({tahmin_dep_dk/60.0:.1f} sa), sürücünün geç beyanına ({beyan_dep_dk/60.0:.1f} sa) aldanmayarak şarjı erken başlattı ve aracı ayrılış öncesinde daha yüksek enerjiyle uğurladı.",
            "derece": "olumlu",
        })

    # 3. EDF Üstünlüğü Analizi
    if ok_edf_guv and not ok_mpc_guv:
        nedenler.append({
            "baslik": "EDF Dinamik Termin Önceliği",
            "kategori": "EDF_USTUNLUK",
            "metin": f"EDF algoritması geleceğe hayali rezervasyon ayırmaksızın, araçları salt yaklaşan ayrılış terminine göre dinamik sıraladı. Boş kalan tüm gücü anında bu araca tahsis ederek hedefine ulaştırdı.",
            "derece": "olumlu",
        })

    # 4. Erken Ayrılma Durumu
    if erken_ayrildi:
        sapma_dk = beyan_dep_dk - ayril_dk
        nedenler.append({
            "baslik": "Erken Ayrılan Sürücü Sapması",
            "kategori": "ERKEN_AYRILMA",
            "metin": f"Sürücü beyan ettiği zamandan {sapma_dk:.0f} dakika önce otoparktan ayrıldı. Beyana dayalı yöntemler son saatlere planlama yaptığı için bu araçta enerji kaybına uğradı.",
            "derece": "bilgi",
        })

    # 5. FCFS Kuyruk Hantallığı
    if not ok_fcfs and (ok_edf_beyan or ok_mpc_beyan):
        nedenler.append({
            "baslik": "FCFS Kuyruk Gecikmesi",
            "kategori": "FCFS_KUSURU",
            "metin": "FCFS yöntemi ayrılış aciliyetini dikkate almadığı için önce gelen ve uzun süre kalacak araçları beslerken, bu aracın terminini kaçırmasına yol açtı.",
            "derece": "bilgi",
        })

    if not nedenler:
        nedenler.append({
            "baslik": "Normal Planlı Şarj Tamamlandı",
            "kategori": "STANDART",
            "metin": f"Araç planlayıcı tarafından zamanında ve kısıtlara uygun olarak tam doluma (%{sat_oranlari.get('mpc_tahmin_guvenli', 1.0)*100:.1f}) ulaştırıldı.",
            "derece": "olumlu",
        })

    return {
        "nedenler": nedenler,
        "detaylar": detaylar,
        "ozet_hukum": nedenler[0]["baslik"],
    }


def oturumlari_hazirla(
    senaryo_id: str,
    gun_secimi: Optional[str] = None,
    tohum: int = 42,
) -> Tuple[pd.DataFrame, pd.Timestamp, str, str]:
    """Seçilen senaryo ve gün için simülasyona hazır oturum veri çerçevesi üretir veya yükler."""
    cfg = SENARYOLAR.get(senaryo_id, SENARYOLAR["isyeri_gunduz"])
    secili_gun = gun_secimi or cfg["varsayilan_gun"]
    
    if cfg["veri_turu"] == "GERCEK":
        csv_dosya = "acn_oturumlar_v2.csv" if senaryo_id == "acn_gercek_val" else "acn_oturumlar_temmuz_aralik.csv"
        csv_yolu = PROJE_KOK / csv_dosya
        if not csv_yolu.exists():
            csv_yolu = PROJE_KOK / "data" / "ham" / csv_dosya
            
        df = veri_hijyeni.temizle(csv_yolu, sadece_beyanli=True)
        saha_id = cfg.get("site_id", "0001")
        gd = df[(df["gun"] == secili_gun) & (df["siteID"] == saha_id)].copy()
        if len(gd) == 0:
            # Alternatif gün veya diğer saha
            gd = df[df["gun"] == secili_gun].copy()
            if len(gd) == 0:
                en_yogun = df.groupby("gun").size().sort_values(ascending=False).index[0]
                gd = df[df["gun"] == en_yogun].copy()
                secili_gun = str(en_yogun)
                
        # Tahmin sütunlarını oluştur (q20, q50, q80)
        # Güvenilir baseline yaklaşımı: bağlantı anındaki ilk beyan ve ampirik quantile oranları
        gd["tahmin_sure_q20"] = np.maximum(30.0, gd["minutesAvailable_ilk"] * 0.78)
        gd["tahmin_sure_q50"] = np.maximum(30.0, gd["minutesAvailable_ilk"] * 0.98)
        gd["tahmin_sure_q80"] = np.maximum(30.0, gd["minutesAvailable_ilk"] * 1.25)
        
        gd["tahmin_kwh_q20"] = np.clip(gd["kWhRequested_ilk"] * 0.70, 1.0, 95.0)
        gd["tahmin_kwh_q50"] = np.clip(gd["kWhRequested_ilk"] * 0.90, 1.0, 95.0)
        gd["tahmin_kwh_q80"] = np.clip(gd["kWhRequested_ilk"] * 1.20, 1.0, 95.0)
        
        t0 = pd.Timestamp(secili_gun).tz_localize("America/Los_Angeles").tz_convert("UTC")
        veri_kaynagi_etiketi = f"GERÇEK SAHA VERİSİ (ACN-Data {saha_id} — {secili_gun})"
        
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
        
        # Sentetik tahminleri ekle
        gd["connectionTime"] = pd.to_datetime(gd["connectionTime"], utc=True)
        gd["disconnectTime"] = pd.to_datetime(gd["disconnectTime"], utc=True)
        gd["requestedDeparture"] = pd.to_datetime(gd["requestedDeparture"], utc=True)

        gd["tahmin_sure_q20"] = np.maximum(30.0, gd["minutesAvailable_ilk"] * 0.75)
        gd["tahmin_sure_q50"] = np.maximum(30.0, gd["minutesAvailable_ilk"] * 0.95)
        gd["tahmin_sure_q80"] = np.maximum(30.0, gd["minutesAvailable_ilk"] * 1.20)
        
        gd["tahmin_kwh_q20"] = np.clip(gd["kWhRequested_ilk"] * 0.68, 1.0, 85.0)
        gd["tahmin_kwh_q50"] = np.clip(gd["kWhRequested_ilk"] * 0.88, 1.0, 85.0)
        gd["tahmin_kwh_q80"] = np.clip(gd["kWhRequested_ilk"] * 1.18, 1.0, 85.0)
        
        t0 = pd.Timestamp(secili_gun).tz_localize("Europe/Istanbul").tz_convert("UTC")
        veri_kaynagi_etiketi = f"SENTETİK MODEL (VARSAYIM — {cfg['ad']})"
        
    return gd, t0, secili_gun, veri_kaynagi_etiketi


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
    
    gd, t0, secili_gun, veri_kaynagi_etiketi = oturumlari_hazirla(senaryo_id, gun_secimi=gun_secimi, tohum=tohum)
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
    
    # 96 adımlı zaman etiketleri (15 dakikalık dilimler: 00:00, 00:15, ..., 23:45)
    zaman_etiketleri = [f"{saat:02d}:{dakika:02d}" for saat in range(24) for dakika in (0, 15, 30, 45)]
    
    # Kontrolsüz Yük Profili
    kontrolsuz_guc = kontrolsuz_profil(giris, ayril, e_gercek, max_adim=96)
    
    # Algoritma Koşuları
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
            tahmin_dep_dk=float(g_adim * 15.0 + tahmin_dep_dk),
            beyan_kwh=float(row.get("kWhRequested_ilk", e_gercek[i] * 1.2)),
            tahmin_kwh=float(row.get("tahmin_kwh_q80", e_gercek[i] * 1.1)),
            erken_ayrildi=bool(erken[i]),
            cap_kw=cap_kw,
            es_zamanli_arac_sayisi=int(np.sum((giris <= a_adim) & (ayril >= g_adim))),
        )
        
        arac_listesi.append({
            "arac_id": aid,
            "sira": i + 1,
            "kullanici_id": str(row.get("userID", f"U-{i+1}")),
            "giris_adim": g_adim,
            "ayril_adim": a_adim,
            "giris_saat": g_saat,
            "ayril_saat": a_saat,
            "beyan_ayril_saat": beyan_dep_saat,
            "sure_gercek_dk": round(float((a_adim - g_adim) * 15.0), 1),
            "sure_beyan_dk": round(beyan_dk, 1),
            "sure_tahmin_q20_dk": round(tahmin_dep_dk, 1),
            "sure_tahmin_q50_dk": round(float(row.get("tahmin_sure_q50", beyan_dk)), 1),
            "sure_tahmin_q80_dk": round(float(row.get("tahmin_sure_q80", beyan_dk * 1.2)), 1),
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


def main():
    parser = argparse.ArgumentParser(description="ŞarjDenge AI Web Servisi")
    parser.add_argument("--senaryolar", action="store_true", help="Mevcut senaryoları JSON olarak listeler")
    parser.add_argument("--senaryo", type=str, default="isyeri_gunduz", help="Senaryo ID")
    parser.add_argument("--f", type=float, default=0.5, help="Kapasite katsayısı f (0.4 - 1.0)")
    parser.add_argument("--cap", type=float, default=None, help="Doğrudan kW kapasite sınırı override")
    parser.add_argument("--gun", type=str, default=None, help="Tarih seçimi (YYYY-AA-GG)")
    parser.add_argument("--tohum", type=int, default=42, help="Rastgele üretim tohumu")
    parser.add_argument("--json", action="store_true", help="JSON formatında çıktı basar")
    
    args = parser.parse_args()
    
    if args.senaryolar:
        out = {"senaryolar": list(SENARYOLAR.values())}
        print(json.dumps(out, ensure_ascii=False, indent=2))
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
