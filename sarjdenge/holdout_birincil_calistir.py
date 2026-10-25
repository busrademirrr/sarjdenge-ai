"""
ŞarjDenge AI — 2020 Holdout Birincil Değerlendirme (Tüm Uygun Günler, min_arac_gunluk=1).

Bu modül:
- Ön kayıtlı birincil değerlendirme kapsamında 2020 holdout verisinin tüm uygun günlerini
  (min_arac_gunluk=1, simülatörün teknik alt sınırı olan gec.sum() >= 4 sağlayan 108 gün-saha, 4.043 oturum)
  üzerinde FCFS, EDF, LLF, MPC-Beyan, MPC-Tahmin-Ortanca, MPC-Tahmin-Güvenli ve Hibrit Asimetrik
  yöntemlerini çalıştırır.
- Mevcut N >= 8 duyarlılık analizi sonuçlarını (3.940 oturum, 89 gün-saha) data/holdout_2020_01_02/
  altında `*_duyarlilik_n8.csv` olarak korur.
- Eşleştirilmiş gün bazlı bootstrap %95 güven aralıklarını (B=2000, tohum=42) hesaplar.
- Erken ayrılan oturumlar için edf_tahmin vs edf_beyan farkı bootstrap GA'sını hesaplar.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
import shutil

import numpy as np
import pandas as pd

from sarjdenge import deney_v2, modeller, veri_hijyeni

PROJE_KOK = pathlib.Path(__file__).parent.parent
HOLDOUT_DIR = PROJE_KOK / "data" / "holdout_2020_01_02"

# Düzeltilmiş Çıktı Dosyaları (Eski CSV'lerin üzerine kesinlikle yazılmaz)
CIKTI_GUNLUK = HOLDOUT_DIR / "deney_gunluk_holdout_2020_birincil_duzeltilmis.csv"
CIKTI_TABLO = HOLDOUT_DIR / "deney_tablo_holdout_2020_birincil_duzeltilmis.csv"
CIKTI_BOOT = HOLDOUT_DIR / "deney_boot_holdout_2020_birincil_duzeltilmis.csv"
CIKTI_BOOT_ERKEN = HOLDOUT_DIR / "deney_boot_erken_holdout_2020_duzeltilmis.csv"

HEDEF_CIKTILAR = [CIKTI_GUNLUK, CIKTI_TABLO, CIKTI_BOOT, CIKTI_BOOT_ERKEN]


def duzeltilmis_cikti_dosyalarini_denetle() -> None:
    """Yeni düzeltilmiş holdout çıktı dosyalarından biri bile varsa deneyi baştan durdurur."""
    mevcutlar = [str(p.name) for p in HEDEF_CIKTILAR if p.exists()]
    if mevcutlar:
        raise FileExistsError(
            f"GÜVENLİK KALKANI: Düzeltilmiş holdout çıktı dosyaları zaten mevcut: {mevcutlar}. "
            "Üzerine yazma kesinlikle engellendi. Deney başlatılmadan durduruldu."
        )


def guvenli_cikti_yaz(ciktilar: list[tuple[pd.DataFrame, pathlib.Path]]) -> list[pathlib.Path]:
    """Dört yeni CSV çıktısını kısmi yazım ve üzerine yazma riskini önleyerek güvenle yazar.
    
    Adımlar:
    1. Hedef dosyaların hiçbirinin mevcut olmadığını doğrular.
    2. Her DataFrame'i benzersiz bir geçici dosyaya yazar (.tmp_<pid>_<ts>.csv).
    3. Tüm geçici dosyaların varlığını ve boş olmadığını doğrular.
    4. Yayımlama öncesinde hedeflerin hâlâ mevcut olmadığını tekrar doğrular.
    5. Path.rename (hedef varsa FileExistsError fırlatan atomik işlem) ile hedefe taşır.
    6. Yazma hatası olursa yalnızca bu süreçte açılmış geçici dosyaları temizler.
    7. Taşıma sırasında hata olursa kısmi yayın durumunu açıkça yönetir ve bildirir.
    """
    duzeltilmis_cikti_dosyalarini_denetle()

    olusturulan_tmp = []
    basariyla_tasinanlar = []

    try:
        ts_now = int(time.time())
        pid = os.getpid()
        for df, hedef_yol in ciktilar:
            tmp_ad = f"{hedef_yol.stem}.tmp_{pid}_{ts_now}.csv"
            tmp_yol = hedef_yol.with_name(tmp_ad)
            df.to_csv(tmp_yol, index=False)
            olusturulan_tmp.append((tmp_yol, hedef_yol))

        for tmp_yol, _ in olusturulan_tmp:
            if not tmp_yol.exists() or tmp_yol.stat().st_size == 0:
                raise IOError(f"Geçici çıktı dosyası doğrulanamadı veya boş: {tmp_yol.name}")

        duzeltilmis_cikti_dosyalarini_denetle()

        for tmp_yol, hedef_yol in olusturulan_tmp:
            tmp_yol.rename(hedef_yol)
            basariyla_tasinanlar.append(hedef_yol)

    except Exception as exc:
        for tmp_yol, hedef_yol in olusturulan_tmp:
            if hedef_yol not in basariyla_tasinanlar and tmp_yol.exists():
                try:
                    tmp_yol.unlink()
                except OSError:
                    pass
        if basariyla_tasinanlar:
            raise RuntimeError(
                f"KRİTİK HATA: Kısmi yayın oluştu! Başarıyla taşınanlar: {[p.name for p in basariyla_tasinanlar]}. "
                f"Hata nedeni: {exc}"
            ) from exc
        raise

    return basariyla_tasinanlar


def main():
    t_start = time.time()
    print("=" * 70)
    print("ŞARJDENGE AI — 2020 HOLDOUT BİRİNCİL DEĞERLENDİRME (TÜM UYGUN GÜNLER)")
    print("=" * 70)

    # 1. Güvenlik Kalkanı Kontrolü (Hedef dosyaların varlığı denetlenir, eski dosyalar korunur)
    print("\n[1/5] Güvenlik kalkanı denetleniyor...")
    duzeltilmis_cikti_dosyalarini_denetle()
    print("  Hedef çıktı dosyalarının mevcut olmadığı doğrulandı; eski CSV dosyaları korundu.")

    # 2. Veri Hazırlama (Aynı Option A ve Sızıntısız strict_shift=True)
    print("\n[2/5] 2019 Eğitim ve 2020 Test verileri hazırlanıyor...")
    cfg = veri_hijyeni.yapilandirma_yukle(PROJE_KOK / "data" / "hijyen.yaml")
    df_h1 = veri_hijyeni.temizle(PROJE_KOK / "acn_oturumlar_v2.csv", config=cfg, sadece_beyanli=True)
    df_h2 = veri_hijyeni.temizle(PROJE_KOK / "acn_oturumlar_temmuz_aralik.csv", config=cfg, sadece_beyanli=True)
    df_2019 = pd.concat([df_h1, df_h2], ignore_index=True)

    t0_cutoff = pd.Timestamp("2020-01-01 00:00:00+00:00")
    mask_cutoff = (pd.to_datetime(df_2019["connectionTime"], utc=True) < t0_cutoff) & (pd.to_datetime(df_2019["disconnectTime"], utc=True) < t0_cutoff)
    df_2019 = df_2019[mask_cutoff].sort_values("connectionTime").reset_index(drop=True)

    f_holdout_csv = HOLDOUT_DIR / "acn_holdout_20200101_20200301_ham.csv"
    df_2020 = veri_hijyeni.temizle(f_holdout_csv, config=cfg, sadece_beyanli=True).sort_values("connectionTime").reset_index(drop=True)

    set_19 = set(df_2019["sessionID"])
    set_20 = set(df_2020["sessionID"])

    df_tum = pd.concat([df_2019, df_2020], ignore_index=True).sort_values("connectionTime").reset_index(drop=True)
    X_tum = veri_hijyeni.ozellikler(df_tum, strict_shift=True)

    mask_train = df_tum["sessionID"].isin(set_19)
    mask_test = df_tum["sessionID"].isin(set_20)

    X_train = X_tum[mask_train].copy().reset_index(drop=True)
    X_test = X_tum[mask_test].copy().reset_index(drop=True)
    df_test = df_tum[mask_test].copy().reset_index(drop=True)

    y_train_sure = df_tum.loc[mask_train, "sure_dk"].to_numpy(dtype=float)
    y_train_kwh = df_tum.loc[mask_train, "kWhDelivered"].to_numpy(dtype=float)

    # 3. Model Eğitimi ve Tahmin
    print("\n[3/5] Dondurulmuş GradientBoosting modelleri eğitiliyor...")
    m_sure = modeller.GradientBoostingQuantileModel(n_estimators=60, max_depth=4, random_state=42)
    m_sure.fit(X_train, y_train_sure)

    m_kwh = modeller.GradientBoostingQuantileModel(n_estimators=60, max_depth=4, random_state=42)
    m_kwh.fit(X_train, y_train_kwh)

    q20_s, q50_s, q80_s = m_sure.predict_quantiles(X_test)
    q20_s_d, q50_s_d, q80_s_d, _, _ = modeller.monotonlastir(q20_s, q50_s, q80_s)

    q20_k, q50_k, q80_k = m_kwh.predict_quantiles(X_test)
    q20_k_d, q50_k_d, q80_k_d, _, _ = modeller.monotonlastir(q20_k, q50_k, q80_k)

    df_test_tahminli = df_test.copy()
    df_test_tahminli["tahmin_sure_q20"] = q20_s_d
    df_test_tahminli["tahmin_sure_q50"] = q50_s_d
    df_test_tahminli["tahmin_sure_q80"] = q80_s_d
    df_test_tahminli["tahmin_kwh_q20"] = q20_k_d
    df_test_tahminli["tahmin_kwh_q50"] = q50_k_d
    df_test_tahminli["tahmin_kwh_q80"] = q80_k_d

    # 4. Tüm Uygun Günler Üzerinde Simülasyon (min_arac_gunluk=1)
    print("\n[4/5] 2020 Holdout tüm uygun günlerde simüle ediliyor (min_arac_gunluk=1)...")
    res_df = deney_v2.deney_calistir(
        df_test_tahminli,
        kapasiteler=(0.5, 0.7, 0.9),
        min_arac_gunluk=1,
    )

    n_pairs = res_df.groupby(["saha", "gun"]).ngroups
    n_sessions_per_f = res_df[res_df["yontem"] == "mpc_beyan"]["n"].sum()
    print(f"  Simüle edilen gün-saha çifti: {n_pairs}")
    print(f"  Toplam simüle edilen oturum: {n_sessions_per_f}")
    print(f"  Toplam simülasyon satırı: {len(res_df)}")
    print(f"  Kapasite ihlali: {res_df['kapasite_ihlali'].sum()}")
    assert res_df["kapasite_ihlali"].sum() == 0, "Kapasite ihlali tespit edildi!"

    # 5. Bootstrap Analizi ve Karşılaştırma
    print("\n[5/5] Eşleştirilmiş Bootstrap Hipotez Testi yürütülüyor (B=2000, tohum=42)...")
    tablo_ozet, boot_ozet = deney_v2.deney_sonuclarini_ozetle(res_df, n_boot=2000, tohum=42)

    # Erken ayrılan oturumlar için ek bootstrap (EDF Tahmin vs EDF Beyan)
    boot_erken_list = []
    for f_val, sub_df in res_df.groupby("f"):
        piv_erken = sub_df.pivot_table(index=["saha", "gun"], columns="yontem", values="erken_ok")
        m, lo, hi = deney_v2.bootstrap_eslestirilmis_fark(piv_erken["edf_tahmin_guvenli"], piv_erken["edf_beyan"], n_boot=2000, tohum=42)
        n_valid_days = int((piv_erken["edf_tahmin_guvenli"] - piv_erken["edf_beyan"]).dropna().count())
        boot_erken_list.append({
            "f": f_val,
            "karsilastirma": "edf_tahmin_guvenli - edf_beyan (erken_ok)",
            "fark_yuzde_puan": float(m * 100.0),
            "ci_95_alt_puan": float(lo * 100.0),
            "ci_95_ust_puan": float(hi * 100.0),
            "n_gun_erken": n_valid_days,
            "anlamli_mi": bool(lo > 0.0 or hi < 0.0),
        })
    df_boot_erken = pd.DataFrame(boot_erken_list)

    print("\n=== TÜM UYGUN GÜNLER BİRİNCİL DEĞERLENDİRME TABLOSU ===")
    print(tablo_ozet.to_string(index=False))

    print("\n=== TÜM UYGUN GÜNLER BOOTSTRAP HİPOTEZ TESTİ ===")
    print(boot_ozet[["f", "karsilastirma", "tur", "fark_yuzde_puan", "ci_95_alt_puan", "ci_95_ust_puan", "ana_hipotez_desteklendi_mi"]].to_string(index=False))

    print("\n=== ERKEN AYRILANLAR BOOTSTRAP ANALİZİ ===")
    print(df_boot_erken.to_string(index=False))

    # Dosyalara Kayıt (Güvenli, iki aşamalı, kısmi yazım korumalı atomik kayıt)
    yazilacaklar = [
        (res_df, CIKTI_GUNLUK),
        (tablo_ozet, CIKTI_TABLO),
        (boot_ozet, CIKTI_BOOT),
        (df_boot_erken, CIKTI_BOOT_ERKEN),
    ]
    kaydedilenler = guvenli_cikti_yaz(yazilacaklar)

    print(f"\nTüm düzeltilmiş birincil holdout dosyaları kaydedildi ({time.time() - t_start:.1f}s)")
    for p in kaydedilenler:
        print(f"  - {p.name}")


if __name__ == "__main__":
    main()
