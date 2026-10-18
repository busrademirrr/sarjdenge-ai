"""ŞarjDenge AI — Sentetik Veri v2 Birim ve Doğrulama Testleri.

Bu testler sentetik veri üreticisinin şema doğruluğunu, tekrarlanabilirliğini,
fiziksel kapasite kısıtlarını, zaman tutarlılığını, duyarlılık parametrelerini
ve veri hijyeni/ML boru hattı uyumluluğunu test eder.
"""

import numpy as np
import pandas as pd
import pytest

from sarjdenge import sentetik_v2, veri_hijyeni

SENARYOLAR = ["isyeri_gunduz", "apartman_gece", "karma"]
BEKLENEN_KOLONLAR = [
    "sessionID", "siteID", "connectionTime", "disconnectTime", "doneChargingTime",
    "kWhDelivered", "userID", "girdi_sayisi", "girdi_degisti", "kWhRequested_ilk",
    "requestedDeparture_ilk", "minutesAvailable_ilk", "kWhRequested", "requestedDeparture",
    "minutesAvailable", "girdi_gecikme_dk", "veri_kaynagi", "senaryo_id", "tohum", "uretici_surumu"
]


@pytest.mark.parametrize("senaryo_id", SENARYOLAR)
def test_sentetik_v2_schema_20_kolon(senaryo_id):
    """Her senaryo tam olarak 16 ACN + 4 metadata kolonuna sahip olmalı ve SENTETIK olarak etiketlenmeli."""
    df = sentetik_v2.uret(senaryo_id=senaryo_id, gun=10, tohum=100)
    
    assert len(df) > 0, f"{senaryo_id} için veri üretilemedi"
    assert list(df.columns) == BEKLENEN_KOLONLAR, f"{senaryo_id} şeması 20 sütunla uyuşmuyor"
    assert (df["veri_kaynagi"] == "SENTETIK").all(), "veri_kaynagi sütunu 'SENTETIK' olmalı"
    assert (df["senaryo_id"] == senaryo_id).all(), f"senaryo_id '{senaryo_id}' ile uyuşmuyor"
    assert (df["tohum"] == 100).all(), "tohum değeri yanlış kaydedilmiş"
    assert (df["uretici_surumu"] == "2.0.0").all(), "uretici_surumu '2.0.0' olmalı"


def test_sentetik_v2_tekrarlanabilirlik_tohum():
    """Aynı tohum tam olarak aynı DataFrame'i üretmeli; farklı tohum farklı oturumlar üretmeli."""
    df1 = sentetik_v2.uret(senaryo_id="apartman_gece", gun=15, tohum=42)
    df2 = sentetik_v2.uret(senaryo_id="apartman_gece", gun=15, tohum=42)
    df3 = sentetik_v2.uret(senaryo_id="apartman_gece", gun=15, tohum=99)

    pd.testing.assert_frame_equal(df1, df2)
    assert not df1.equals(df3), "Farklı tohumlar farklı sonuç üretmeli"
    assert df1["kWhDelivered"].iloc[0] != df3["kWhDelivered"].iloc[0] or \
           df1["connectionTime"].iloc[0] != df3["connectionTime"].iloc[0]


@pytest.mark.parametrize("senaryo_id", SENARYOLAR)
def test_sentetik_v2_fiziksel_kapasite_ve_zaman_sinirlari(senaryo_id):
    """Fiziksel güç, süre ve enerji kısıtları kesinlikle ihlal edilmemelidir."""
    df = sentetik_v2.uret(senaryo_id=senaryo_id, gun=20, tohum=42)
    
    c_time = pd.to_datetime(df["connectionTime"], utc=True)
    d_time = pd.to_datetime(df["disconnectTime"], utc=True)
    done_time = pd.to_datetime(df["doneChargingTime"], utc=True)
    
    # 1. Zaman tutarlılığı
    sure_dk = (d_time - c_time).dt.total_seconds() / 60.0
    assert (sure_dk >= 30.0).all(), "30 dakikadan kısa oturum üretilmemeli"
    assert (sure_dk <= 48.0 * 60.0).all(), "48 saatten uzun oturum üretilmemeli"

    # 2. doneChargingTime sınırları: c_time <= done_time <= d_time
    assert (done_time >= c_time - pd.Timedelta(seconds=1)).all(), "doneChargingTime bağlantı anından önce olamaz"
    assert (done_time <= d_time + pd.Timedelta(seconds=1)).all(), "doneChargingTime ayrılış anından sonra olamaz"

    # 3. Enerji alt ve üst sınırları
    assert (df["kWhDelivered"] >= 0.5).all(), "0.5 kWh altı teslimat üretilmemeli"
    
    # P_eff = min(soket, obc) * sarj_verimi <= 22 * 0.9 = 19.8 kW
    # kWh <= P_eff * (sure_saat)
    p_eff_max = 22.0 * 0.90
    max_kwh_fiziksel = p_eff_max * (sure_dk / 60.0) + 0.05
    assert (df["kWhDelivered"] <= max_kwh_fiziksel).all(), "Fiziksel şarj gücü kapasitesi aşıldı"


def test_sentetik_v2_beyan_tutarliligi():
    """Kullanıcı beyan zamanı ve süresi matematiksel olarak tutarlı olmalıdır."""
    df = sentetik_v2.uret(senaryo_id="isyeri_gunduz", gun=15, tohum=42)
    
    c_time = pd.to_datetime(df["connectionTime"], utc=True)
    req_dep = pd.to_datetime(df["requestedDeparture_ilk"], utc=True)
    
    hesaplanan_dk = (req_dep - c_time).dt.total_seconds() / 60.0
    fark = np.abs(df["minutesAvailable_ilk"] - hesaplanan_dk)
    assert (fark < 0.2).all(), "minutesAvailable_ilk ile (requestedDeparture - connectionTime) uyuşmuyor"
    
    # Kullanıcı talep enerjisi teslim edilen enerjiden küçük olmamalı (talep >= teslim)
    assert (df["kWhRequested_ilk"] >= df["kWhDelivered"] - 0.001).all()
    # Gecikme [-5, 30] aralığında
    assert (df["girdi_gecikme_dk"] >= -5.0).all()
    assert (df["girdi_gecikme_dk"] <= 30.0).all()


def test_sentetik_v2_duyarlilik_analizi_parametre_yonu():
    """Min/Tipik/Max duyarlılık ayarları beklenen parametrik yönde değişim üretmeli."""
    df_min = sentetik_v2.uret(senaryo_id="apartman_gece", gun=25, tohum=42, duyarlilik="min")
    df_tip = sentetik_v2.uret(senaryo_id="apartman_gece", gun=25, tohum=42, duyarlilik="tipik")
    df_max = sentetik_v2.uret(senaryo_id="apartman_gece", gun=25, tohum=42, duyarlilik="max")

    # Soket sayısı ve doluluk min'de 10 soket @ 0.35, tipik'te 20 soket @ 0.65, max'ta 50 soket @ 0.85
    # Üretilen toplam oturum sayısı monoton artmalıdır: len(min) < len(tip) < len(max)
    assert len(df_min) < len(df_tip) < len(df_max), (
        f"Duyarlılık yönü tutarsız: min={len(df_min)}, tip={len(df_tip)}, max={len(df_max)}"
    )


def test_sentetik_v2_senaryolar_farklilik_ve_etiketleme():
    """Apartman (gece) ve İş Yeri (gündüz) senaryoları belirgin davranış farklılıkları göstermelidir."""
    df_apt = sentetik_v2.uret(senaryo_id="apartman_gece", gun=30, tohum=42)
    df_isy = sentetik_v2.uret(senaryo_id="isyeri_gunduz", gun=30, tohum=42)

    ist_apt = sentetik_v2.senaryo_istatistikleri(df_apt)
    ist_isy = sentetik_v2.senaryo_istatistikleri(df_isy)

    # 1. Varış saatleri: Apartman akşam (17-22), İş yeri sabah (7-11)
    assert 17.0 <= ist_apt["varis_saat_medyan"] <= 22.0, f"Apt varış beklenmedik: {ist_apt['varis_saat_medyan']}"
    assert 7.0 <= ist_isy["varis_saat_medyan"] <= 11.5, f"İş yeri varış beklenmedik: {ist_isy['varis_saat_medyan']}"

    # 2. Park süresi: Gece parkı (~10-14 saat) gündüz mesaisinden (~7-9 saat) daha uzundur
    assert ist_apt["sure_dk_medyan"] > ist_isy["sure_dk_medyan"], (
        f"Apartman süresi ({ist_apt['sure_dk_medyan']} dk) iş yerinden ({ist_isy['sure_dk_medyan']} dk) uzun olmalı"
    )


def test_sentetik_v2_veri_hijyeni_ve_data_yukle_uyumlulugu(tmp_path):
    """Sentetik veri çıktısı veri_hijyeni modülü ve sızıntısız özellik çıkarımı ile tam uyumlu olmalı."""
    yol = tmp_path / "test_sentetik.csv"
    sentetik_v2.uret(senaryo_id="isyeri_gunduz", gun=25, tohum=42, yol=yol)

    # veri_hijyeni.temizle ile temizleme
    df_temiz = veri_hijyeni.temizle(yol, sadece_beyanli=False)
    assert len(df_temiz) > 0

    # strict_shift ile özellik çıkarımı
    X = veri_hijyeni.ozellikler(df_temiz, strict_shift=True)
    assert "saat" in X.columns
    assert "gecmis_n" in X.columns
    assert "sure_dk" not in X.columns  # Hedef değişken sızmamalı

    # Zaman sıralı bölme
    egit, test, kesim = veri_hijyeni.zaman_bol(df_temiz, bolme=0.6)
    assert len(egit) > 0 and len(test) > 0
    assert egit["connectionTime"].max() < test["connectionTime"].min()
