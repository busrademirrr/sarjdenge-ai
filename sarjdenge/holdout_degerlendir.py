"""
ŞarjDenge AI — 2020 Holdout Yeniden Eğitim ve Nihai Değerlendirme Modülü.

Bu modül:
1. Seçenek A uyarınca 2019 yılının 25.421 beyanlı oturumuyla GradientBoosting şampiyon
   modellerini dondurulmuş hiperparametrelerle (n_estimators=60, max_depth=4, seed=42) eğitir.
2. 2019 ve 2020 verilerini birleştirerek strict_shift=True ile sızıntısız özellik matrisini üretir.
3. 2020 holdout test oturumları (4.072 oturum) üzerinde süre ve enerji quantile tahminlerini üretir,
   monotonlaştırır, metrikleri (Pinball, MSS, MAE, kapsam) hesaplar.
4. Dondurulmuş simülatör ve deney hattı (deney_v2) ile FCFS, EDF, LLF, MPC-Beyan, MPC-Tahmin-Ortanca,
   MPC-Tahmin-Güvenli ve Hibrit Asimetrik yöntemlerini 0.5, 0.7, 0.9 kapasitelerinde simüle eder.
5. Eşleştirilmiş gün bazlı bootstrap (B=2000, tohum=42) ile ön kayıt ana hipotezini test eder.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from sarjdenge import deney_v2, modeller, sim, veri_hijyeni

PROJE_KOK = pathlib.Path(__file__).parent.parent
HOLDOUT_DIR = PROJE_KOK / "data" / "holdout_2020_01_02"


def holdout_degerlendir(
    n_boot: int = 2000,
    tohum: int = 42,
    log=print,
) -> Dict[str, Any]:
    t_baslangic = time.time()
    log("=" * 70)
    log("ŞARJDENGE AI — 2020 HOLDOUT DEĞERLENDİRME VE HİPOTEZ TESTİ")
    log("=" * 70)

    # 1. Veri Yükleme ve Temizleme
    cfg = veri_hijyeni.yapilandirma_yukle(PROJE_KOK / "data" / "hijyen.yaml")
    
    log("\n[1/5] Veri setleri yükleniyor ve temizleniyor...")
    df_h1 = veri_hijyeni.temizle(PROJE_KOK / "acn_oturumlar_v2.csv", config=cfg, sadece_beyanli=True)
    df_h2 = veri_hijyeni.temizle(PROJE_KOK / "acn_oturumlar_temmuz_aralik.csv", config=cfg, sadece_beyanli=True)
    df_2019 = pd.concat([df_h1, df_h2], ignore_index=True)
    
    # Kati Bitiş Kuralı kontrolü
    c_2019 = pd.to_datetime(df_2019["connectionTime"], utc=True)
    d_2019 = pd.to_datetime(df_2019["disconnectTime"], utc=True)
    t0_cutoff = pd.Timestamp("2020-01-01 00:00:00+00:00")
    mask_cutoff = (c_2019 < t0_cutoff) & (d_2019 < t0_cutoff)
    df_2019 = df_2019[mask_cutoff].sort_values("connectionTime").reset_index(drop=True)
    
    f_holdout_csv = HOLDOUT_DIR / "acn_holdout_20200101_20200301_ham.csv"
    df_2020 = veri_hijyeni.temizle(f_holdout_csv, config=cfg, sadece_beyanli=True)
    df_2020 = df_2020.sort_values("connectionTime").reset_index(drop=True)

    log(f"  2019 Eğitim Oturum Sayısı (Seçenek A): {len(df_2019):,}")
    log(f"  2020 Holdout Test Oturum Sayısı:        {len(df_2020):,}")

    set_19 = set(df_2019["sessionID"])
    set_20 = set(df_2020["sessionID"])
    assert len(set_19.intersection(set_20)) == 0, "HATA: 2019 ve 2020 arasında çakışan sessionID tespit edildi!"

    # 2. Sızıntısız Özellik Matrisi Üretimi (strict_shift=True)
    log("\n[2/5] Sızıntısız özellik matrisi üretiliyor (strict_shift=True)...")
    df_tum = pd.concat([df_2019, df_2020], ignore_index=True).sort_values("connectionTime").reset_index(drop=True)
    X_tum = veri_hijyeni.ozellikler(df_tum, strict_shift=True)

    mask_train = df_tum["sessionID"].isin(set_19)
    mask_test = df_tum["sessionID"].isin(set_20)

    X_train = X_tum[mask_train].copy().reset_index(drop=True)
    X_test = X_tum[mask_test].copy().reset_index(drop=True)
    df_test = df_tum[mask_test].copy().reset_index(drop=True)

    y_train_sure = df_tum.loc[mask_train, "sure_dk"].to_numpy(dtype=float)
    y_train_kwh = df_tum.loc[mask_train, "kWhDelivered"].to_numpy(dtype=float)

    y_test_sure = df_test["sure_dk"].to_numpy(dtype=float)
    y_test_kwh = df_test["kWhDelivered"].to_numpy(dtype=float)

    # Ölçek hesaplama (YALNIZCA 2019 eğitim verisinden)
    s_sure_egit = modeller.hesapla_egitim_olcegi(y_train_sure)
    s_kwh_egit = modeller.hesapla_egitim_olcegi(y_train_kwh)
    log(f"  2019 Normalizasyon Ölçekleri: s_sure = {s_sure_egit:.2f} dk, s_kwh = {s_kwh_egit:.2f} kWh")

    # 3. Model Eğitimi ve Tahmin
    log("\n[3/5] Dondurulmuş GradientBoosting modelleri eğitiliyor...")
    m_sure = modeller.GradientBoostingQuantileModel(n_estimators=60, max_depth=4, random_state=42)
    m_sure.fit(X_train, y_train_sure)

    m_kwh = modeller.GradientBoostingQuantileModel(n_estimators=60, max_depth=4, random_state=42)
    m_kwh.fit(X_train, y_train_kwh)

    log("  2020 Holdout tahminleri üretiliyor ve monotonlaştırılıyor...")
    q20_s_raw, q50_s_raw, q80_s_raw = m_sure.predict_quantiles(X_test)
    q20_s_duz, q50_s_duz, q80_s_duz, n_c_s, r_c_s = modeller.monotonlastir(q20_s_raw, q50_s_raw, q80_s_raw)

    q20_k_raw, q50_k_raw, q80_k_raw = m_kwh.predict_quantiles(X_test)
    q20_k_duz, q50_k_duz, q80_k_duz, n_c_k, r_c_k = modeller.monotonlastir(q20_k_raw, q50_k_raw, q80_k_raw)

    # Tahmin Metrikleri Hesaplama
    metrik_sure = modeller.model_secim_skoru(y_test_sure, q20_s_duz, q50_s_duz, q80_s_duz, s_egit=s_sure_egit, gamma=1.0)
    metrik_sure["crossing_sayisi"] = n_c_s
    metrik_sure["crossing_orani"] = r_c_s
    metrik_sure["ham_pinball_ort"] = float((modeller.pinball_loss(y_test_sure, q20_s_raw, 0.2) +
                                            modeller.pinball_loss(y_test_sure, q50_s_raw, 0.5) +
                                            modeller.pinball_loss(y_test_sure, q80_s_raw, 0.8)) / 3.0)
    metrik_sure["mae_q50"] = modeller.mae(y_test_sure, q50_s_duz)
    metrik_sure["coverage_q20"] = float(np.mean(y_test_sure <= q20_s_duz))
    metrik_sure["coverage_q50"] = float(np.mean(y_test_sure <= q50_s_duz))
    metrik_sure["coverage_q80"] = float(np.mean(y_test_sure <= q80_s_duz))

    metrik_kwh = modeller.model_secim_skoru(y_test_kwh, q20_k_duz, q50_k_duz, q80_k_duz, s_egit=s_kwh_egit, gamma=1.0)
    metrik_kwh["crossing_sayisi"] = n_c_k
    metrik_kwh["crossing_orani"] = r_c_k
    metrik_kwh["ham_pinball_ort"] = float((modeller.pinball_loss(y_test_kwh, q20_k_raw, 0.2) +
                                           modeller.pinball_loss(y_test_kwh, q50_k_raw, 0.5) +
                                           modeller.pinball_loss(y_test_kwh, q80_k_raw, 0.8)) / 3.0)
    metrik_kwh["mae_q50"] = modeller.mae(y_test_kwh, q50_k_duz)
    metrik_kwh["coverage_q20"] = float(np.mean(y_test_kwh <= q20_k_duz))
    metrik_kwh["coverage_q50"] = float(np.mean(y_test_kwh <= q50_k_duz))
    metrik_kwh["coverage_q80"] = float(np.mean(y_test_kwh <= q80_k_duz))

    # Beyan Referans Metrikleri
    beyan_sure_arr = df_test["beyan_sure_dk"].clip(lower=30.0).to_numpy(dtype=float)
    beyan_kwh_arr = df_test["kWhRequested"].clip(upper=100.0).to_numpy(dtype=float)
    mae_beyan_sure = modeller.mae(y_test_sure, beyan_sure_arr)
    mae_beyan_kwh = modeller.mae(y_test_kwh, beyan_kwh_arr)

    log("\n--- 2020 HOLDOUT TAHMİN PERFORMANSI ---")
    log(f"Süre Modeli (GradientBoosting):")
    log(f"  MSS Skoru (Dimensionless):     {metrik_sure['mss']:.4f}")
    log(f"  Normalize Pinball Loss:        {metrik_sure['pinball_norm']:.4f}")
    log(f"  Ham Ortalama Pinball Loss:     {metrik_sure['pinball_ort']:.2f} dk")
    log(f"  MAE q50 (Tahmin vs Beyan):     {metrik_sure['mae_q50']:.2f} dk vs {mae_beyan_sure:.2f} dk")
    log(f"  Kapsam q20 (Hedef: 0.20):      {metrik_sure['coverage_q20']:.3f}")
    log(f"  Kapsam q50 (Hedef: 0.50):      {metrik_sure['coverage_q50']:.3f}")
    log(f"  Kapsam q80 (Hedef: 0.80):      {metrik_sure['coverage_q80']:.3f}")
    log(f"  Quantile Crossing Oranı:       %{metrik_sure['crossing_orani']*100:.2f} ({metrik_sure['crossing_sayisi']} adet)")

    log(f"\nEnerji Modeli (GradientBoosting):")
    log(f"  MSS Skoru (Dimensionless):     {metrik_kwh['mss']:.4f}")
    log(f"  Normalize Pinball Loss:        {metrik_kwh['pinball_norm']:.4f}")
    log(f"  Ham Ortalama Pinball Loss:     {metrik_kwh['pinball_ort']:.2f} kWh")
    log(f"  MAE q50 (Tahmin vs Beyan):     {metrik_kwh['mae_q50']:.2f} kWh vs {mae_beyan_kwh:.2f} kWh")
    log(f"  Kapsam q20 (Hedef: 0.20):      {metrik_kwh['coverage_q20']:.3f}")
    log(f"  Kapsam q50 (Hedef: 0.50):      {metrik_kwh['coverage_q50']:.3f}")
    log(f"  Kapsam q80 (Hedef: 0.80 ±0.03):{metrik_kwh['coverage_q80']:.3f}")
    kwh_q80_gecerli = bool(0.77 <= metrik_kwh['coverage_q80'] <= 0.83)
    log(f"  Kapsam Toleransı Karşılandı mı:{kwh_q80_gecerli}")
    log(f"  Quantile Crossing Oranı:       %{metrik_kwh['crossing_orani']*100:.2f} ({metrik_kwh['crossing_sayisi']} adet)")

    # 4. MPC Simülasyonu
    log("\n[4/5] 2020 Holdout üzerinde MPC simülasyonları yürütülüyor...")
    df_test_tahminli = df_test.copy()
    df_test_tahminli["tahmin_sure_q20"] = q20_s_duz
    df_test_tahminli["tahmin_sure_q50"] = q50_s_duz
    df_test_tahminli["tahmin_sure_q80"] = q80_s_duz
    df_test_tahminli["tahmin_kwh_q20"] = q20_k_duz
    df_test_tahminli["tahmin_kwh_q50"] = q50_k_duz
    df_test_tahminli["tahmin_kwh_q80"] = q80_k_duz

    res_df = deney_v2.deney_calistir(
        df_test_tahminli,
        kapasiteler=(0.5, 0.7, 0.9),
        min_arac_gunluk=8,
    )

    log(f"  Simüle edilen gün-saha satırı: {len(res_df):,}")
    log(f"  Kapasite ihlali kontrolü: Toplam ihlal = {res_df['kapasite_ihlali'].sum()}")
    assert res_df["kapasite_ihlali"].sum() == 0, "KRİTİK HATA: Kapasite ihlali tespit edildi!"

    # 5. Bootstrap Hipotez Testi
    log("\n[5/5] Eşleştirilmiş Bootstrap Hipotez Testi yürütülüyor (B=2000, tohum=42)...")
    tablo_ozet, boot_ozet = deney_v2.deney_sonuclarini_ozetle(res_df, n_boot=n_boot, tohum=tohum)

    log("\n--- YÖNTEM PERFORMANS ÖZETİ ---")
    log(tablo_ozet.to_string(index=False))

    log("\n--- BOOTSTRAP HİPOTEZ TESTİ SONUÇLARI ---")
    log(boot_ozet[["f", "karsilastirma", "tur", "fark_yuzde_puan", "ci_95_alt_puan", "ci_95_ust_puan", "ana_hipotez_desteklendi_mi"]].to_string(index=False))

    # Dosyalara Kayıt
    res_df.to_csv(HOLDOUT_DIR / "deney_gunluk_holdout_2020.csv", index=False)
    tablo_ozet.to_csv(HOLDOUT_DIR / "deney_tablo_holdout_2020.csv", index=False)
    boot_ozet.to_csv(HOLDOUT_DIR / "deney_boot_holdout_2020.csv", index=False)

    tahmin_kayit = {
        "egitim_oturum_sayisi": len(df_2019),
        "test_oturum_sayisi": len(df_2020),
        "s_sure_egit": s_sure_egit,
        "s_kwh_egit": s_kwh_egit,
        "sure_metrikleri": metrik_sure,
        "kwh_metrikleri": metrik_kwh,
        "mae_beyan_sure": mae_beyan_sure,
        "mae_beyan_kwh": mae_beyan_kwh,
    }
    with open(HOLDOUT_DIR / "tahmin_metrikleri_holdout_2020.json", "w", encoding="utf-8") as jf:
        json.dump(tahmin_kayit, jf, indent=2, ensure_ascii=False)

    toplam_sure = time.time() - t_baslangic
    log(f"\nDeğerlendirme tamamlandı ({toplam_sure:.1f} saniye). Dosyalar kaydedildi: {HOLDOUT_DIR}")

    return {
        "tablo_ozet": tablo_ozet,
        "boot_ozet": boot_ozet,
        "tahmin_metrikleri": tahmin_kayit,
        "res_df": res_df,
    }


if __name__ == "__main__":
    holdout_degerlendir()
