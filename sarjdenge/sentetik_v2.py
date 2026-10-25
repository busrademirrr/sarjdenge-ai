"""ŞarjDenge AI — Sentetik Şarj Oturumu Üretici (Sürüm 2.0.0).

Bu modül, Türkiye apartman, iş yeri ve karma otopark senaryoları için
dışsallaştırılmış yapılandırma (`config/senaryolar.yaml`) doğrultusunda
kod ve olasılık modelleriyle sentetik şarj oturumları üretir.

Kurallar ve Metodolojik Sınırlar:
1. Çekirdek modüllere (`turkiye.py`, `sentetik.py`, `data.py`) dokunulmaz.
2. Sentetik satırlar LLM tarafından değil, sabit rastgele tohumlu olasılık
   dağılımları ve ampirik örnekleme ile üretilir.
3. Gerçek ACN verisiyle sentetik veri kesin olarak ayrılmıştır:
   Çıktı şeması 16 standart ACN sütunu + 4 metadata sütunu (`veri_kaynagi="SENTETIK"`,
   `senaryo_id`, `tohum`, `uretici_surumu`) içerir.
4. `isyeri_gunduz` senaryosu ACN ampirik verisi ile kalibre edilmiştir.
5. `apartman_gece` senaryosu için ACN karşılığı ve anket verisi YOKTUR;
   tüm parametreler VARSAYIM olarak işaretlenmiştir ve duyarlılık aralıkları
   [min, tipik, max] ile incelenebilir.
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import yaml

VARSAYILAN_CONFIG_YOLU = pathlib.Path(__file__).parent.parent / "config" / "senaryolar.yaml"


def senaryo_yapilandirmasi_yukle(
    config_yolu: Optional[Union[str, pathlib.Path]] = None,
) -> Dict[str, Any]:
    """YAML yapılandırma dosyasını yükler."""
    yol = pathlib.Path(config_yolu or VARSAYILAN_CONFIG_YOLU)
    if not yol.exists():
        raise FileNotFoundError(f"Senaryo yapılandırma dosyası bulunamadı: {yol}")
    with open(yol, "r", encoding="utf-8-sig") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        raise ValueError(f"Senaryo yapılandırma dosyası geçersiz şema içeriyor: {yol}")
    return cfg


def acn_ampirik_veri_havuzu(
    acn_csv_yolu: Optional[Union[str, pathlib.Path]] = None,
) -> pd.DataFrame:
    """İş yeri senaryosu kalibrasyonu için temiz ACN oturumlarını yükler.
    
    Ortak ampirik örnekleme amacıyla bağlantı saati, süre, kWh, beyan gecikmesi
    ve beyan sapması sütunlarını hazırlar.
    """
    kok = pathlib.Path(__file__).parent.parent
    if acn_csv_yolu is None:
        adaylar = [
            kok / "data" / "ham" / "acn_20181231_20190630.csv",
            kok / "acn_oturumlar_v2.csv",
            kok / "acn_oturumlar_ocak_haziran.csv",
        ]
        for aday in adaylar:
            if aday.exists():
                acn_csv_yolu = aday
                break

    if acn_csv_yolu is None or not pathlib.Path(acn_csv_yolu).exists():
        # Veri dosyası bulunamazsa sentetik ampirik havuz döndür
        return pd.DataFrame()

    df = pd.read_csv(acn_csv_yolu)
    df["connectionTime"] = pd.to_datetime(df["connectionTime"], utc=True, errors="coerce")
    df["disconnectTime"] = pd.to_datetime(df["disconnectTime"], utc=True, errors="coerce")
    df["kWhDelivered"] = pd.to_numeric(df["kWhDelivered"], errors="coerce")
    
    df = df.dropna(subset=["connectionTime", "disconnectTime", "kWhDelivered"])
    df["sure_dk"] = (df.disconnectTime - df.connectionTime).dt.total_seconds() / 60.0
    df = df[(df.sure_dk >= 30.0) & (df.sure_dk <= 48.0 * 60.0) & (df.kWhDelivered >= 0.5)]
    
    # Yerel saat (Los Angeles) varış saati
    df["yerel_saat"] = df.connectionTime.dt.tz_convert("America/Los_Angeles").dt.hour + \
                       df.connectionTime.dt.tz_convert("America/Los_Angeles").dt.minute / 60.0

    # Beyan bilgileri
    ilk = "requestedDeparture_ilk" in df.columns
    if ilk and "requestedDeparture_ilk" in df:
        req_dep = pd.to_datetime(df["requestedDeparture_ilk"], utc=True, errors="coerce")
        req_kwh = pd.to_numeric(df["kWhRequested_ilk"], errors="coerce")
    else:
        req_dep = pd.to_datetime(df["requestedDeparture"], utc=True, errors="coerce")
        req_kwh = pd.to_numeric(df["kWhRequested"], errors="coerce")

    df["beyan_sure_dk"] = (req_dep - df.connectionTime).dt.total_seconds() / 60.0
    df["beyan_kwh"] = req_kwh
    df["beyan_kayma_dk"] = (req_dep - df.disconnectTime).dt.total_seconds() / 60.0
    
    gecikme_col = df["girdi_gecikme_dk"] if "girdi_gecikme_dk" in df else pd.Series(0.0, index=df.index)
    df["gecikme_dk"] = pd.to_numeric(gecikme_col, errors="coerce").fillna(2.0)

    # Geçerli beyan filtresi
    beyan_mask = df.beyan_sure_dk.notna() & (df.beyan_sure_dk > 0) & df.beyan_kwh.notna() & (df.beyan_kwh > 0)
    df_gecerli = df[beyan_mask].copy()

    # İş yeri saatlerine (06:00 - 14:00 varış) odaklan
    df_isyeri = df_gecerli[(df_gecerli.yerel_saat >= 6.0) & (df_gecerli.yerel_saat <= 14.0)]
    return df_isyeri.reset_index(drop=True) if len(df_isyeri) > 100 else df_gecerli.reset_index(drop=True)


def _parametreleri_hazirla(
    cfg: Dict[str, Any],
    senaryo_id: str,
    duyarlilik: str = "tipik",
    param_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Senaryo parametrelerini duyarlılık ve geçersiz kılmalar ile birleştirir."""
    if senaryo_id not in cfg:
        raise ValueError(f"Bilinmeyen senaryo_id: '{senaryo_id}'. Mevcut: {list(cfg.keys())}")
    
    p = dict(cfg[senaryo_id])
    genel = dict(cfg.get("genel", {}))
    
    # Duyarlılık ayarı varsa uygula
    duyarlilik_cfg = cfg.get("duyarlilik", {}).get(senaryo_id, {})
    if duyarlilik in duyarlilik_cfg:
        p.update(duyarlilik_cfg[duyarlilik])
    
    if param_overrides:
        p.update(param_overrides)
        
    p["_genel"] = genel
    return p


def uret(
    senaryo_id: str = "isyeri_gunduz",
    gun: int = 60,
    tohum: int = 42,
    yol: Optional[Union[str, pathlib.Path]] = None,
    config_yolu: Optional[Union[str, pathlib.Path]] = None,
    duyarlilik: str = "tipik",
    param_overrides: Optional[Dict[str, Any]] = None,
    baslangic_tarihi: str = "2026-01-05",
) -> pd.DataFrame:
    """Belirtilen senaryo için tam şemalı sentetik veri seti üretir.
    
    Dönen DataFrame kesinlikle 16 ACN sütunu + 4 metadata sütununa sahiptir.
    Fiziksel güç, süre ve enerji kısıtları matematiksel olarak garanti altındadır.
    """
    cfg = senaryo_yapilandirmasi_yukle(config_yolu)
    p = _parametreleri_hazirla(cfg, senaryo_id, duyarlilik, param_overrides)
    genel = p["_genel"]
    
    rng = np.random.default_rng(tohum)
    tz_str = genel.get("zaman_dilimi", "Europe/Istanbul")
    uretici_surumu = genel.get("uretici_surumu", "2.0.0")
    sarj_verimi = float(genel.get("sarj_verimi", 0.90))
    tatiller = set(genel.get("tatiller_tr_2026", []))
    
    soket_sayisi = int(p.get("soket_sayisi", 20))
    site_id = str(p.get("site_id", "TR_SITE"))
    soket_gucu_kw = float(p.get("soket_gucu_kw", 22.0))
    arac_obc_kw = float(p.get("arac_obc_kw", 11.0))
    # Efektif net şarj gücü (şebekeden bataryaya aktarılan)
    p_eff_kw = min(soket_gucu_kw, arac_obc_kw) * sarj_verimi

    arac_sayisi_havuz = int(p.get("arac_sayisi_havuz", 50))
    # Sürücü havuzu soket sayısından daima daha geniş olmalıdır
    arac_sayisi_havuz = max(arac_sayisi_havuz, int(soket_sayisi * 1.25))

    arac_olasiligi_haftaici = float(p.get("arac_olasiligi_haftaici", 0.65))
    hafta_sonu_carpani = float(p.get("hafta_sonu_carpani", 0.50))
    tatil_carpani = float(p.get("tatil_carpani", 0.40))
    kis_enerji_carpani = float(p.get("kis_enerji_carpani", 1.15))
    
    # Sürücü havuzu oluştur (Kişisel alışkanlıklar)
    suruculer = []
    for uid in range(arac_sayisi_havuz):
        suruculer.append({
            "uid": f"tr_{senaryo_id}_{uid:03d}",
            "varis_aliskanlik": float(rng.normal(0, 0.4)),  # kişisel saat kayması
            "cikis_aliskanlik": float(rng.normal(0, 0.3)),
            "enerji_egilimi": float(rng.lognormal(0, 0.20)),
            "beyan_hata_egilimi": float(rng.normal(0, 15.0)),
        })

    # ACN ampirik havuzunu hazırla (isyeri_gunduz ve karma için)
    acn_df = pd.DataFrame()
    if p.get("kalibrasyon_tipi") in ["ACN_AMPIRIK", "HIBRIT"]:
        acn_df = acn_ampirik_veri_havuzu()

    acn_kalibre_oldu = bool(senaryo_id == "isyeri_gunduz" and len(acn_df) > 50)

    baslangic = pd.Timestamp(baslangic_tarihi, tz=tz_str)
    satirlar = []
    sid = 0

    for d in range(gun):
        gun_ts = baslangic + pd.Timedelta(days=d)
        gun_str = gun_ts.strftime("%Y-%m-%d")
        
        # Gün tipi katsayısı
        is_weekend = gun_ts.dayofweek >= 5
        is_holiday = gun_str in tatiller
        
        pr = arac_olasiligi_haftaici
        if is_weekend:
            pr *= hafta_sonu_carpani
        if is_holiday:
            pr *= tatil_carpani
            
        # Mevsimsellik çarpanı (Ocak-Şubat-Aralık kış aylarında yüksek tüketim)
        ay = gun_ts.month
        is_winter = ay in [12, 1, 2]
        enerji_mevsim_carpani = kis_enerji_carpani if is_winter else 1.0

        # O gün gelecek araç sayısı (Binomial dağılım, soket ve sürücü havuzuyla sınırlı)
        n_arac = int(min(soket_sayisi, len(suruculer), rng.binomial(soket_sayisi, np.clip(pr, 0.01, 0.99))))
        if n_arac <= 0:
            continue
            
        secilen_suruculer = rng.choice(suruculer, size=n_arac, replace=False)

        for s_idx, surucu in enumerate(secilen_suruculer):
            # Senaryoya özel varış saati, süre ve enerji belirleme
            if senaryo_id == "isyeri_gunduz":
                # ACN Ortak Ampirik Örnekleme
                if len(acn_df) > 50:
                    ornek = acn_df.iloc[rng.integers(0, len(acn_df))]
                    varis_saat = float(np.clip(ornek["yerel_saat"] + surucu["varis_aliskanlik"] + rng.normal(0, 0.25), 6.5, 13.5))
                    sure_dk = float(np.clip(ornek["sure_dk"] * rng.lognormal(0, 0.15), 35.0, 16.0 * 60.0))
                    ham_kwh = float(ornek["kWhDelivered"] * surucu["enerji_egilimi"] * enerji_mevsim_carpani)
                    beyan_kayma = float(ornek["beyan_kayma_dk"] + surucu["beyan_hata_egilimi"] + rng.normal(0, 20.0))
                    gecikme_dk = float(np.clip(ornek["gecikme_dk"] + rng.normal(0, 1.0), -4.5, 28.0))
                    kwh_carpan = float(rng.uniform(1.05, 1.40))
                else:
                    # Parametrik ACN kalibrasyonu yedeği
                    varis_saat = float(np.clip(rng.normal(8.5, 1.1) + surucu["varis_aliskanlik"], 6.5, 13.0))
                    sure_dk = float(np.clip(rng.lognormal(np.log(480), 0.35), 45.0, 14.0 * 60.0))
                    ham_kwh = float(np.clip(rng.gamma(3.5, 3.8) * enerji_mevsim_carpani, 2.0, 50.0))
                    beyan_kayma = float(rng.normal(33.0, 60.0))
                    gecikme_dk = float(np.clip(rng.exponential(2.5) - 0.5, -4.5, 28.0))
                    kwh_carpan = float(rng.uniform(1.05, 1.45))
                    
                giris_ts = gun_ts + pd.Timedelta(hours=varis_saat)
                cikis_ts = giris_ts + pd.Timedelta(minutes=sure_dk)

            elif senaryo_id == "apartman_gece":
                # Konut Gece Davranış Varsayımı
                varis_ort = float(p.get("varis_saat_ort", 19.25))
                varis_sd = float(p.get("varis_saat_sd", 1.20))
                cikis_ort = float(p.get("cikis_saat_ort", 7.75))
                cikis_gun_sd = float(p.get("cikis_gunluk_sapma_sd", 0.45))
                
                varis_saat = float(np.clip(rng.normal(varis_ort, varis_sd) + surucu["varis_aliskanlik"], 16.0, 23.8))
                giris_ts = gun_ts + pd.Timedelta(hours=varis_saat)
                
                cikis_saat = float(np.clip(rng.normal(cikis_ort, cikis_gun_sd) + surucu["cikis_aliskanlik"], 5.5, 11.5))
                # Ertesi sabah çıkış
                cikis_ts = gun_ts + pd.Timedelta(days=1, hours=cikis_saat)
                sure_dk = (cikis_ts - giris_ts).total_seconds() / 60.0
                
                # Enerji ihtiyacı: lognormal (günlük yol ihtiyacı)
                log_ort = float(p.get("kwh_ihtiyac_log_ort", 2.35))
                log_sd = float(p.get("kwh_ihtiyac_log_sd", 0.45))
                ust_kwh = float(p.get("kwh_ihtiyac_ust_sinir", 65.0))
                
                ham_kwh = float(np.clip(np.exp(rng.normal(log_ort, log_sd)) * surucu["enerji_egilimi"] * enerji_mevsim_carpani, 1.5, ust_kwh))
                
                beyan_kayma = float(rng.normal(float(p.get("beyan_kayma_dk_ort", 30.0)), float(p.get("beyan_kayma_dk_sd", 75.0))))
                gecikme_dk = float(np.clip(rng.exponential(3.0) - 1.0, -4.5, 28.0))
                kwh_carpan = float(rng.uniform(1.10, 1.55))

            else:  # karma
                # %50 gündüz çalışanı, %50 gece sakini
                is_gece = s_idx % 2 == 1
                if is_gece:
                    varis_saat = float(np.clip(rng.normal(19.0, 1.2) + surucu["varis_aliskanlik"], 16.5, 23.5))
                    giris_ts = gun_ts + pd.Timedelta(hours=varis_saat)
                    cikis_ts = gun_ts + pd.Timedelta(days=1, hours=float(np.clip(rng.normal(7.8, 0.5), 6.0, 10.5)))
                    sure_dk = (cikis_ts - giris_ts).total_seconds() / 60.0
                    ham_kwh = float(np.clip(rng.gamma(2.8, 3.5) * enerji_mevsim_carpani, 2.0, 55.0))
                else:
                    varis_saat = float(np.clip(rng.normal(8.75, 1.0) + surucu["varis_aliskanlik"], 7.0, 12.5))
                    giris_ts = gun_ts + pd.Timedelta(hours=varis_saat)
                    sure_dk = float(np.clip(rng.lognormal(np.log(450), 0.30), 40.0, 12.0 * 60.0))
                    cikis_ts = giris_ts + pd.Timedelta(minutes=sure_dk)
                    ham_kwh = float(np.clip(rng.gamma(3.2, 3.5) * enerji_mevsim_carpani, 2.0, 45.0))

                beyan_kayma = float(rng.normal(30.0, 65.0))
                gecikme_dk = float(np.clip(rng.exponential(2.8) - 0.5, -4.5, 28.0))
                kwh_carpan = float(rng.uniform(1.08, 1.50))

            # ------------------------------------------------------------------
            # Fiziksel ve Mantıksal Sınırların Kesin Denetimi
            # ------------------------------------------------------------------
            sure_dk = max(30.0, (cikis_ts - giris_ts).total_seconds() / 60.0)
            cikis_ts = giris_ts + pd.Timedelta(minutes=sure_dk)
            sure_saat = sure_dk / 60.0
            
            # 1. Fiziksel maksimum teslim edilebilir enerji kısıtı: kWh <= P_eff * t
            max_fiziksel_kwh = p_eff_kw * sure_saat
            kwh_delivered = float(np.clip(ham_kwh, 0.5, max_fiziksel_kwh))
            
            # 2. Şarj tamamlanma anı (doneChargingTime): t_done = t_conn + kWh / P_eff
            sarj_suresi_saat = kwh_delivered / max(p_eff_kw, 0.1)
            done_ts = giris_ts + pd.Timedelta(hours=sarj_suresi_saat)
            if done_ts > cikis_ts:
                done_ts = cikis_ts
            if done_ts < giris_ts:
                done_ts = giris_ts

            # 3. Beyan ayrılış zamanı (requestedDeparture)
            # Kullanıcı çıkıştan ortalama beyan_kayma dk önce veya sonra ayrılacağını söyler
            beyan_dep_ts = cikis_ts - pd.Timedelta(minutes=beyan_kayma)
            # Beyan bağlantıdan en az 30 dk sonraya yapılmalıdır
            if beyan_dep_ts < giris_ts + pd.Timedelta(minutes=30.0):
                beyan_dep_ts = giris_ts + pd.Timedelta(minutes=30.0)
                
            minutes_available = (beyan_dep_ts - giris_ts).total_seconds() / 60.0
            
            # 4. Beyan edilen enerji (kWhRequested)
            # Kullanıcılar çoğunlukla gerçek teslimattan fazlasını talep eder
            kwh_requested = float(np.clip(kwh_delivered * kwh_carpan + rng.exponential(0.8), kwh_delivered, 95.0))

            # UTC Zaman Damgalarına Dönüşüm
            giris_utc = giris_ts.tz_convert("UTC")
            cikis_utc = cikis_ts.tz_convert("UTC")
            done_utc = done_ts.tz_convert("UTC")
            beyan_dep_utc = beyan_dep_ts.tz_convert("UTC")

            session_id = f"tr_{senaryo_id}_{sid:05d}"
            
            # 16 ACN standardı + 4 metadata kolonu
            satir = {
                "sessionID": session_id,
                "siteID": site_id,
                "connectionTime": giris_utc.strftime("%Y-%m-%d %H:%M:%S+00:00"),
                "disconnectTime": cikis_utc.strftime("%Y-%m-%d %H:%M:%S+00:00"),
                "doneChargingTime": done_utc.strftime("%Y-%m-%d %H:%M:%S+00:00"),
                "kWhDelivered": round(kwh_delivered, 3),
                "userID": surucu["uid"],
                "girdi_sayisi": 1,
                "girdi_degisti": 0,
                "kWhRequested_ilk": round(kwh_requested, 3),
                "requestedDeparture_ilk": beyan_dep_utc.strftime("%Y-%m-%d %H:%M:%S+00:00"),
                "minutesAvailable_ilk": round(minutes_available, 1),
                "kWhRequested": round(kwh_requested, 3),
                "requestedDeparture": beyan_dep_utc.strftime("%Y-%m-%d %H:%M:%S+00:00"),
                "minutesAvailable": round(minutes_available, 1),
                "girdi_gecikme_dk": round(gecikme_dk, 2),
                # 4 Metadata Kolonu
                "veri_kaynagi": "SENTETIK",
                "senaryo_id": senaryo_id,
                "tohum": tohum,
                "uretici_surumu": uretici_surumu,
            }
            satirlar.append(satir)
            sid += 1

    df_sonuc = pd.DataFrame(satirlar)
    df_sonuc.attrs["acn_kalibrasyonu"] = acn_kalibre_oldu
    if yol is not None:
        yol_p = pathlib.Path(yol)
        yol_p.parent.mkdir(parents=True, exist_ok=True)
        df_sonuc.to_csv(yol_p, index=False)

    return df_sonuc


def uret_tum_senaryolar(
    gun: int = 60,
    tohum: int = 42,
    cikti_dizin: Union[str, pathlib.Path] = "data/sentetik",
    config_yolu: Optional[Union[str, pathlib.Path]] = None,
) -> Dict[str, pd.DataFrame]:
    """Tüm standart senaryoları (`isyeri_gunduz`, `apartman_gece`, `karma`) üretir ve kaydeder."""
    dizin = pathlib.Path(cikti_dizin)
    dizin.mkdir(parents=True, exist_ok=True)
    
    senaryolar = ["isyeri_gunduz", "apartman_gece", "karma"]
    sonuclar = {}
    
    for s_id in senaryolar:
        hedef_csv = dizin / f"sentetik_{s_id}_tohum{tohum}.csv"
        df_s = uret(
            senaryo_id=s_id,
            gun=gun,
            tohum=tohum,
            yol=hedef_csv,
            config_yolu=config_yolu,
        )
        sonuclar[s_id] = df_s
        
    return sonuclar


def senaryo_istatistikleri(df: pd.DataFrame) -> Dict[str, Any]:
    """Verilen sentetik veri kümesi için özet istatistikler üretir."""
    c_time = pd.to_datetime(df["connectionTime"], utc=True)
    d_time = pd.to_datetime(df["disconnectTime"], utc=True)
    sure_dk = (d_time - c_time).dt.total_seconds() / 60.0
    
    # Yerel saat (Europe/Istanbul) varış saati
    yerel_varis = c_time.dt.tz_convert("Europe/Istanbul")
    varis_saat = yerel_varis.dt.hour + yerel_varis.dt.minute / 60.0

    return {
        "satir_sayisi": len(df),
        "benzersiz_kullanici": df["userID"].nunique(),
        "sure_dk_medyan": float(sure_dk.median()),
        "sure_dk_ortalama": float(sure_dk.mean()),
        "kwh_medyan": float(df["kWhDelivered"].median()),
        "kwh_ortalama": float(df["kWhDelivered"].mean()),
        "kwh_p90": float(df["kWhDelivered"].quantile(0.90)),
        "varis_saat_medyan": float(varis_saat.median()),
        "varis_saat_ortalama": float(varis_saat.mean()),
    }


if __name__ == "__main__":
    print("Sentetik veri üretici test ediliyor...")
    res = uret_tum_senaryolar(gun=30, tohum=42)
    for k, v in res.items():
        ist = senaryo_istatistikleri(v)
        print(f"[{k}] Satır: {len(v)}, Süre medyan: {ist['sure_dk_medyan']:.1f} dk, kWh medyan: {ist['kwh_medyan']:.2f}")
