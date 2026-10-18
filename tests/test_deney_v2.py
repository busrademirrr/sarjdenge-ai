"""ŞarjDenge AI — MPC Simülasyonu ve Karar Mekanizması Birim/Entegrasyon Testleri (İş Paketi D)."""

import pathlib
import numpy as np
import pandas as pd
import pytest

from sarjdenge import deney_v2, modeller, veri_hijyeni

PROJE_KOK = pathlib.Path(__file__).parent.parent
CSV_V2 = PROJE_KOK / "acn_oturumlar_v2.csv"


def test_gelecek_bilgisi_sizintisi_yoklugu():
    """Online planlayıcının inandığı ayrılış ve kWh hedefleri gerçek değerleri kesinlikle sızdırmamalıdır."""
    if not CSV_V2.exists():
        pytest.skip(f"{CSV_V2} bulunamadı")

    df = veri_hijyeni.temizle(CSV_V2, sadece_beyanli=True).iloc[:100].copy()
    # Sentetik tahmin sütunları ekle
    df["tahmin_sure_q20"] = 300.0
    df["tahmin_sure_q50"] = 450.0
    df["tahmin_sure_q80"] = 600.0
    df["tahmin_kwh_q20"] = 8.0
    df["tahmin_kwh_q50"] = 12.0
    df["tahmin_kwh_q80"] = 18.0

    kaynaklar = deney_v2.inanilan_kaynaklar(df)

    # 1. Beyan kaynağı: gerçek disconnectTime veya gerçek kWhDelivered'a eşit olamaz
    bd_ts, kwh_beyan = kaynaklar["beyan"]
    assert not (bd_ts.to_numpy() == df["disconnectTime"].to_numpy()).all()
    assert not (kwh_beyan == df["kWhDelivered"].to_numpy()).all()

    # 2. Tahmin güvenli kaynağı: connectionTime + sure_q20 olmalı
    q20_dep, kwh_q80 = kaynaklar["tahmin_guvenli"]
    beklenen_dep = df["connectionTime"] + pd.to_timedelta(300.0, unit="m")
    assert (q20_dep == beklenen_dep).all()
    assert (kwh_q80 == 18.0).all()


def test_kapasite_asimi_yoklugu():
    """Simülasyon sırasında hiçbir yöntemde güç sınırı/kapasite ihlali yaşanmamalıdır."""
    if not CSV_V2.exists():
        pytest.skip(f"{CSV_V2} bulunamadı")

    df = veri_hijyeni.temizle(CSV_V2, sadece_beyanli=True)
    # İlk 3 günün verisiyle mini simülasyon
    ilk_gunler = sorted(df["gun"].unique())[:3]
    df_mini = df[df["gun"].isin(ilk_gunler)].copy()

    df_mini["tahmin_sure_q20"] = 320.0
    df_mini["tahmin_sure_q50"] = 480.0
    df_mini["tahmin_sure_q80"] = 620.0
    df_mini["tahmin_kwh_q20"] = 6.0
    df_mini["tahmin_kwh_q50"] = 11.0
    df_mini["tahmin_kwh_q80"] = 16.0

    res = deney_v2.deney_calistir(
        df_mini,
        kapasiteler=(0.5, 0.7),
        min_arac_gunluk=5,
        secili_yontemler={
            "fcfs_beyan": ("fcfs", "beyan"),
            "mpc_beyan": ("mpc", "beyan"),
            "mpc_tahmin_guvenli": ("mpc", "tahmin_guvenli"),
        }
    )

    assert len(res) > 0
    assert (res["kapasite_ihlali"] == 0).all(), "Kapasite ihlali tespit edildi!"


def test_adil_karsilastirma_ayni_kosullar():
    """Tüm algoritmalar aynı gün, aynı oturum ve aynı kapasite kısıtları altında çalıştırılmalıdır."""
    if not CSV_V2.exists():
        pytest.skip(f"{CSV_V2} bulunamadı")

    df = veri_hijyeni.temizle(CSV_V2, sadece_beyanli=True)
    ilk_gunler = sorted(df["gun"].unique())[:2]
    df_mini = df[df["gun"].isin(ilk_gunler)].copy()

    df_mini["tahmin_sure_q20"] = 320.0
    df_mini["tahmin_sure_q50"] = 480.0
    df_mini["tahmin_sure_q80"] = 620.0
    df_mini["tahmin_kwh_q20"] = 6.0
    df_mini["tahmin_kwh_q50"] = 11.0
    df_mini["tahmin_kwh_q80"] = 16.0

    yontemler = {
        "fcfs_beyan": ("fcfs", "beyan"),
        "edf_beyan": ("edf", "beyan"),
        "mpc_beyan": ("mpc", "beyan"),
        "mpc_tahmin_guvenli": ("mpc", "tahmin_guvenli"),
    }
    res = deney_v2.deney_calistir(df_mini, kapasiteler=(0.5,), min_arac_gunluk=5, secili_yontemler=yontemler)

    # Her gün ve saha için tüm yöntemlerin araç sayısı (n) ve cap_kw birebir aynı olmalı
    for (saha, gun), grup in res.groupby(["saha", "gun"]):
        assert len(grup) == len(yontemler)
        assert grup["n"].nunique() == 1, f"{gun} gününde yöntemlerin oturum sayıları farklı!"
        assert grup["cap_kw"].nunique() == 1, f"{gun} gününde yöntemlerin kapasite sınırları farklı!"


def test_bootstrap_tekrarlanabilirligi():
    """Eşleştirilmiş bootstrap aynı tohumla birebir aynı ortalama farkı ve CI sınırlarını vermelidir."""
    a = np.array([0.85, 0.90, 0.78, 0.92, 0.88, 0.95, 0.82])
    b = np.array([0.80, 0.87, 0.75, 0.90, 0.85, 0.91, 0.80])

    m1, lo1, hi1 = deney_v2.bootstrap_eslestirilmis_fark(a, b, n_boot=500, tohum=42)
    m2, lo2, hi2 = deney_v2.bootstrap_eslestirilmis_fark(a, b, n_boot=500, tohum=42)

    assert m1 == m2
    assert lo1 == lo2
    assert hi1 == hi2
    assert m1 > 0.0
    assert lo1 <= m1 <= hi1


def test_erken_ayrilan_ve_adillik_metrikleri():
    """Erken ayrılan başarı ve p10 adillik metrikleri [0.0, 1.0] aralığında olmalıdır."""
    if not CSV_V2.exists():
        pytest.skip(f"{CSV_V2} bulunamadı")

    df = veri_hijyeni.temizle(CSV_V2, sadece_beyanli=True)
    ilk_gun = sorted(df["gun"].unique())[0]
    df_mini = df[df["gun"] == ilk_gun].copy()

    df_mini["tahmin_sure_q20"] = 300.0
    df_mini["tahmin_sure_q50"] = 450.0
    df_mini["tahmin_sure_q80"] = 600.0
    df_mini["tahmin_kwh_q20"] = 7.0
    df_mini["tahmin_kwh_q50"] = 11.0
    df_mini["tahmin_kwh_q80"] = 15.0

    res = deney_v2.deney_calistir(
        df_mini,
        kapasiteler=(0.7,),
        min_arac_gunluk=4,
        secili_yontemler={"mpc_beyan": ("mpc", "beyan")}
    )

    if len(res) > 0:
        row = res.iloc[0]
        assert 0.0 <= row["ok"] <= 1.0
        assert 0.0 <= row["teslim_orani"] <= 1.0
        assert 0.0 <= row["p10"] <= 1.0
        if not np.isnan(row["erken_ok"]):
            assert 0.0 <= row["erken_ok"] <= 1.0
