"""ŞarjDenge AI — Quantile Modelleri ve Model Seçimi Birim/Entegrasyon Testleri (İş Paketi C)."""

import pathlib
import numpy as np
import pandas as pd
import pytest

from sarjdenge import modeller, sim, veri_hijyeni

PROJE_KOK = pathlib.Path(__file__).parent.parent
CSV_V2 = PROJE_KOK / "acn_oturumlar_v2.csv"
CSV_TEMMUZ = PROJE_KOK / "acn_oturumlar_temmuz_aralik.csv"


def test_strict_shift_ve_hedef_sizintisi_yoklugu():
    """Özellik matrisi X içinde hedef veya gelecek değişkenler kesinlikle bulunmamalıdır."""
    if not CSV_V2.exists():
        pytest.skip(f"{CSV_V2} bulunamadı")

    veri = modeller.egitim_dogrulama_hazirla(CSV_V2, bolme=0.6)
    X_egit, X_val = veri["X_egit"], veri["X_val"]

    yasakli_sutunlar = [
        "sure_dk", "kWhDelivered", "disconnectTime", "doneChargingTime",
        "target_sure_dk", "target_kwh_delivered", "girdi_sayisi", "girdi_degisti"
    ]
    for yasak in yasakli_sutunlar:
        assert yasak not in X_egit.columns, f"Sızıntı tespit edildi: {yasak} X_egit matrisinde bulundu!"
        assert yasak not in X_val.columns, f"Sızıntı tespit edildi: {yasak} X_val matrisinde bulundu!"

    # strict_shift kontrolü: ilk oturumu olan kullanıcıların gecmis_n == 0 olmalı
    assert (X_egit.loc[X_egit["gecmis_n"] == 0, "gecmis_sure"].isna()).all()
    assert (X_val.loc[X_val["gecmis_n"] == 0, "gecmis_sure"].isna()).all()


def test_gece_yarisi_kronolojik_gun_bolumu():
    """Eğitim ve doğrulama kümeleri yerel gün sınırında (00:00:00) ayrılmalı ve çakışma olmamalıdır."""
    if not CSV_V2.exists():
        pytest.skip(f"{CSV_V2} bulunamadı")

    veri = modeller.egitim_dogrulama_hazirla(CSV_V2, bolme=0.6)
    egit_df, val_df = veri["egit_df"], veri["val_df"]

    assert len(egit_df) > 0 and len(val_df) > 0
    assert egit_df["connectionTime"].max() < val_df["connectionTime"].min()

    # Aynı güne ait oturumların bölünmediği kontrolü
    egit_gunler = set(egit_df["gun"])
    val_gunler = set(val_df["gun"])
    assert len(egit_gunler.intersection(val_gunler)) == 0, "Aynı gün hem eğitim hem doğrulama kümesinde bulundu!"


def test_quantile_monotonlugu_ve_duzeltme():
    """Monotonlaştırma fonksiyonu kesişen nicelik tahminlerini q20 <= q50 <= q80 yapmalıdır."""
    # Kasıtlı olarak kesişen sentetik diziler
    q20_raw = np.array([120.0, 500.0, 300.0, 40.0])
    q50_raw = np.array([100.0, 450.0, 300.0, 50.0])  # 0. ve 1. indekslerde kesişim
    q80_raw = np.array([80.0, 600.0, 300.0, 60.0])   # 0. indekste q20 > q80

    q20_duz, q50_duz, q80_duz, n_cross, cross_rate = modeller.monotonlastir(q20_raw, q50_raw, q80_raw)

    assert n_cross == 2
    assert cross_rate == 0.50
    assert (q20_duz <= q50_duz).all()
    assert (q50_duz <= q80_duz).all()

    # Düzeltilmiş değerlerin doğruluğu (0. indeks: 80 <= 100 <= 120)
    assert q20_duz[0] == 80.0
    assert q50_duz[0] == 100.0
    assert q80_duz[0] == 120.0


def test_model_secim_skoru_olcek_bagimsizligi():
    """Model Seçim Skoru (MSS) s_egit ölçeği ile normalize edilmeli ve kapsam cezasını eklemelidir."""
    y_true = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    q20 = np.array([8.0, 16.0, 24.0, 32.0, 40.0])
    q50 = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    q80 = np.array([12.0, 24.0, 36.0, 48.0, 60.0])

    s_egit = 15.0
    skor = modeller.model_secim_skoru(y_true, q20, q50, q80, s_egit=s_egit, gamma=1.0)

    assert "mss" in skor
    assert "pinball_ort" in skor
    assert "pinball_norm" in skor
    assert skor["pinball_norm"] == pytest.approx(skor["pinball_ort"] / s_egit, rel=1e-5)
    assert skor["mss"] >= skor["pinball_norm"]  # Kapsam hatası eklendiği için mss >= pinball_norm


def test_deterministik_egitim_ve_cikarim():
    """Sabit tohumla eğitilen HistGradientBoosting modeli aynı girdide bit düzeyinde aynı tahmini vermelidir."""
    if not CSV_V2.exists():
        pytest.skip(f"{CSV_V2} bulunamadı")

    veri = modeller.egitim_dogrulama_hazirla(CSV_V2, bolme=0.6)
    X_sample = veri["X_egit"].iloc[:500]
    y_sample = veri["y_egit_sure"][:500]

    m1 = modeller.HistGradientBoostingQuantileModel(random_state=42)
    m1.fit(X_sample, y_sample)
    p20_1, p50_1, p80_1 = m1.predict_quantiles(X_sample)

    m2 = modeller.HistGradientBoostingQuantileModel(random_state=42)
    m2.fit(X_sample, y_sample)
    p20_2, p50_2, p80_2 = m2.predict_quantiles(X_sample)

    np.testing.assert_array_equal(p20_1, p20_2)
    np.testing.assert_array_equal(p50_1, p50_2)
    np.testing.assert_array_equal(p80_1, p80_2)


def test_sim_uyumluluk_kolonlari():
    """tahminleri_ekle() çıktısı sim.py simülatörü ile eksiksiz uyumlu olmalı ve simüle edilebilmelidir."""
    if not CSV_V2.exists():
        pytest.skip(f"{CSV_V2} bulunamadı")

    df = veri_hijyeni.temizle(CSV_V2, sadece_beyanli=True)
    df_mini = df.iloc[:100].copy()

    m_sure = modeller.GlobalEmpirikQuantileModel()
    m_sure.fit(df_mini, df_mini["sure_dk"])

    m_kwh = modeller.GlobalEmpirikQuantileModel()
    m_kwh.fit(df_mini, df_mini["kWhDelivered"])

    df_tahminli = modeller.tahminleri_ekle(df_mini, sure_modeli=m_sure, enerji_modeli=m_kwh)

    beklenen_tahmin_kolonlari = [
        "tahmin_sure_q20", "tahmin_sure_q50", "tahmin_sure_q80",
        "tahmin_kwh_q20", "tahmin_kwh_q50", "tahmin_kwh_q80"
    ]
    for c in beklenen_tahmin_kolonlari:
        assert c in df_tahminli.columns, f"{c} kolonu eksik!"

    # sim.simule ile doğrudan çekirdek simülasyon testi
    giris = np.array([0, 2, 4])
    ayril = np.array([16, 20, 24])
    e_gercek = np.array([10.0, 15.0, 20.0])
    inan_ayril = np.array([12, 18, 22])
    inan_kwh = df_tahminli["tahmin_kwh_q80"].iloc[:3].to_numpy()
    cap = 20.0

    teslim = sim.simule(giris, ayril, e_gercek, inan_ayril, inan_kwh, cap, yontem=sim.mpc)
    assert len(teslim) == 3
    assert (teslim <= e_gercek + 1e-6).all()
    assert (teslim >= 0.0).all()


def test_ilk_beyan_zorunlulugu(tmp_path):
    """requestedDeparture_ilk veya kWhRequested_ilk sütunları eksikse egitim_dogrulama_hazirla() hata vermelidir."""
    df_sahte = pd.DataFrame({
        "sessionID": ["s1"],
        "connectionTime": ["2019-01-01 08:00:00+00:00"],
        "disconnectTime": ["2019-01-01 16:00:00+00:00"],
        "kWhDelivered": [15.0],
        "requestedDeparture": ["2019-01-01 16:00:00+00:00"],
        "kWhRequested": [20.0],
        # *_ilk sütunları yok!
    })
    sahte_csv = tmp_path / "sahte.csv"
    df_sahte.to_csv(sahte_csv, index=False)

    with pytest.raises(ValueError, match="ilk beyan sütunları"):
        modeller.egitim_dogrulama_hazirla(sahte_csv)
