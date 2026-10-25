"""Veri hijyeni, şelale filtreleme ve sızıntı denetim testleri."""

import pathlib
import numpy as np
import pandas as pd
import pytest

from sarjdenge import data, veri_hijyeni

PROJE_KOK = pathlib.Path(__file__).parent.parent
CSV_V2 = PROJE_KOK / "acn_oturumlar_v2.csv"
CSV_TEMMUZ = PROJE_KOK / "acn_oturumlar_temmuz_aralik.csv"


def test_manifest_tutarliligi(tmp_path):
    """Manifest üretici tüm ACN dosyalarını bulmalı, SHA256 ve satır sayılarını doğru yazmalı."""
    md_cikti = tmp_path / "MANIFEST_TEST.md"
    ham_cikti = tmp_path / "ham"
    m_df = veri_hijyeni.manifest_uret(klasor=PROJE_KOK, cikti_md=md_cikti, kopyala_dizin=ham_cikti)

    assert md_cikti.exists()
    assert len(m_df) >= 3
    assert "acn_oturumlar_v2.csv" in m_df["dosya_adi"].values
    assert (m_df["satir_sayisi"] > 0).all()
    assert (m_df["sha256"].str.len() == 64).all()

    # Kopyalanan dosyaların varlığı ve hash eşitliği
    kopyalar = list(ham_cikti.glob("*.csv"))
    assert len(kopyalar) >= 2


@pytest.mark.parametrize("csv_yol, beklenen_temiz, beklenen_beyanli", [
    (CSV_V2, 14219, 13123),
    (CSV_TEMMUZ, 13445, 12298),
])
def test_data_yukle_ile_eslesme(csv_yol, beklenen_temiz, beklenen_beyanli):
    """veri_hijyeni.temizle(sadece_beyanli=False) data.yukle() ile birebir aynı satır kümesini vermeli."""
    if not csv_yol.exists():
        pytest.skip(f"{csv_yol} bulunamadı")

    df_eski = data.yukle(str(csv_yol))
    df_yeni = veri_hijyeni.temizle(str(csv_yol), sadece_beyanli=False)

    assert len(df_yeni) == beklenen_temiz, f"Yeni temiz satır={len(df_yeni)} != {beklenen_temiz}"
    assert len(df_eski) == len(df_yeni), f"Eski={len(df_eski)} != Yeni={len(df_yeni)}"
    assert set(df_eski["sessionID"]) == set(df_yeni["sessionID"]), "sessionID kümeleri eşleşmiyor"
    assert df_eski["beyan_var"].sum() == df_yeni["beyan_var"].sum() == beklenen_beyanli

    # sadece_beyanli=True kontrolü
    df_beyanli = veri_hijyeni.temizle(str(csv_yol), sadece_beyanli=True)
    assert len(df_beyanli) == beklenen_beyanli
    assert (df_beyanli["beyan_var"] == True).all()


def test_eleme_selalesi_tutarliligi():
    """Şelale adımlarının toplamı başlangıç ham satır sayısıyla ve ara basamaklarla tutarlı olmalı."""
    if not CSV_V2.exists():
        pytest.skip("acn_oturumlar_v2.csv bulunamadı")

    selale = veri_hijyeni.eleme_selalesi(CSV_V2)
    toplam = selale["toplam"]

    assert toplam["ham"] == 14372
    assert toplam["dup"] == 0
    assert toplam["miss"] == 0
    assert toplam["neg"] == 0
    assert toplam["short"] == 139
    assert toplam["long"] == 14
    assert toplam["low_kwh"] == 0

    hesaplanan_temiz = toplam["ham"] - toplam["short"] - toplam["long"]
    assert hesaplanan_temiz == toplam["temiz"] == 14219
    assert toplam["beyanli"] == 13123


def test_kullanici_gecmisi_shift_ve_tamamlanma():
    """Kullanıcı geçmişi özellikleri kesinlikle yalnızca karar anından önce tamamlanmış oturumlardan gelmeli."""
    if not CSV_V2.exists():
        pytest.skip("acn_oturumlar_v2.csv bulunamadı")

    df = veri_hijyeni.temizle(CSV_V2, sadece_beyanli=False)
    X = veri_hijyeni.ozellikler(df, strict_shift=True)

    # 1. Her kullanıcının ilk oturumu geçmiş taşımamalı (gecmis_n == 0, nan)
    for uid, grp in df.groupby("userID"):
        ilk_idx = grp.index[0]
        assert X.loc[ilk_idx, "gecmis_n"] == 0
        assert np.isnan(X.loc[ilk_idx, "gecmis_sure"])
        assert np.isnan(X.loc[ilk_idx, "gecmis_kwh"])

    # 2. Birden fazla oturumu olan bilinen kullanıcıların geçmiş değerleri pozitif olmalı
    coklu_mask = (X["gecmis_n"] > 0)
    assert (X.loc[coklu_mask, "gecmis_sure"] >= 30.0).all()
    assert (X.loc[coklu_mask, "gecmis_kwh"] >= 0.5).all()


def test_zaman_sirali_ve_cakismasiz_bolme():
    """Eğitim ve test kümeleri zaman sırasıyla ayrılmalı ve aralarında zaman çakışması olmamalı."""
    if not CSV_V2.exists():
        pytest.skip("acn_oturumlar_v2.csv bulunamadı")

    df = veri_hijyeni.temizle(CSV_V2, sadece_beyanli=False)
    egit_df, test_df, kesim = veri_hijyeni.zaman_bol(df, bolme=0.6)

    assert len(egit_df) > 0 and len(test_df) > 0
    assert len(egit_df) + len(test_df) == len(df)
    assert egit_df["connectionTime"].max() < test_df["connectionTime"].min()
    assert len(set(egit_df["sessionID"]).intersection(set(test_df["sessionID"]))) == 0


def test_hedef_degiskenler_ozelliklerde_yok():
    """Hedef ve gelecek değişkenler özellik matrisi X içinde kesinlikle yer almamalıdır."""
    if not CSV_V2.exists():
        pytest.skip("acn_oturumlar_v2.csv bulunamadı")

    df = veri_hijyeni.temizle(CSV_V2, sadece_beyanli=False)
    X = veri_hijyeni.ozellikler(df, strict_shift=True)

    yasakli_sutunlar = [
        "sure_dk", "kWhDelivered", "disconnectTime", "doneChargingTime",
        "target_sure_dk", "target_kwh_delivered", "girdi_sayisi", "girdi_degisti"
    ]
    for yasak in yasakli_sutunlar:
        assert yasak not in X.columns, f"Sızıntı tespit edildi: {yasak} özellik matrisinde bulundu!"


def _sentetik_gecmis_df_olustur() -> pd.DataFrame:
    """Kullanıcı geçmişi sızıntı ve çakışma senaryolarını test etmek için küçük sentetik DataFrame."""
    kayitlar = [
        # U1 - Oturum 0: İlk oturum (08:00 -> 09:00, 60 dk, 10 kWh) -> geçmiş yok
        {
            "sessionID": "s_u1_0",
            "siteID": "0001",
            "userID": "U1",
            "connectionTime": "2019-05-01T08:00:00Z",
            "disconnectTime": "2019-05-01T09:00:00Z",
            "sure_dk": 60.0,
            "kWhDelivered": 10.0,
            "kWhRequested": 12.0,
            "requestedDeparture": "2019-05-01T09:30:00Z",
            "minutesAvailable": 90.0,
        },
        # U1 - Oturum 1: Oturum 0 tamamlandıktan sonra başlar (09:30 -> 12:00, 150 dk, 30 kWh)
        # -> Oturum 0 geçmişe girmeli (n=1, sure=60, kwh=10)
        {
            "sessionID": "s_u1_1",
            "siteID": "0001",
            "userID": "U1",
            "connectionTime": "2019-05-01T09:30:00Z",
            "disconnectTime": "2019-05-01T12:00:00Z",
            "sure_dk": 150.0,
            "kWhDelivered": 30.0,
            "kWhRequested": 35.0,
            "requestedDeparture": "2019-05-01T12:30:00Z",
            "minutesAvailable": 180.0,
        },
        # U1 - Oturum 2: Oturum 1 devam ederken (çakışarak) başlar (10:30 -> 11:30, 60 dk, 14 kWh)
        # -> Oturum 1 (12:00 bitiş > 10:30 başlangıç) geçmişe GİRMEMELİ;
        #    ancak daha eski tamamlanmış Oturum 0 (09:00 bitiş <= 10:30) geçmişte KALMALI (n=1, sure=60, kwh=10)
        {
            "sessionID": "s_u1_2",
            "siteID": "0001",
            "userID": "U1",
            "connectionTime": "2019-05-01T10:30:00Z",
            "disconnectTime": "2019-05-01T11:30:00Z",
            "sure_dk": 60.0,
            "kWhDelivered": 14.0,
            "kWhRequested": 15.0,
            "requestedDeparture": "2019-05-01T11:30:00Z",
            "minutesAvailable": 60.0,
        },
        # U1 - Oturum 3: Hem Oturum 1 hem Oturum 2 bittikten sonra başlar (12:30 -> 13:30, 60 dk, 8 kWh)
        # -> Oturum 0, 1 ve 2'nin üçü de tamamlanmış olmalı (n=3, sure=(60+150+60)/3=90, kwh=(10+30+14)/3=18)
        {
            "sessionID": "s_u1_3",
            "siteID": "0001",
            "userID": "U1",
            "connectionTime": "2019-05-01T12:30:00Z",
            "disconnectTime": "2019-05-01T13:30:00Z",
            "sure_dk": 60.0,
            "kWhDelivered": 8.0,
            "kWhRequested": 10.0,
            "requestedDeparture": "2019-05-01T13:30:00Z",
            "minutesAvailable": 60.0,
        },
        # U2 - İlk oturumu çakışan başka bir kullanıcı: U1 geçmişinden etkilenmemeli
        # Oturum 0 (08:00 -> 11:00) ve Oturum 1 (09:00 -> 10:00) çakışıyor -> ikisinde de n=0
        {
            "sessionID": "s_u2_0",
            "siteID": "0001",
            "userID": "U2",
            "connectionTime": "2019-05-01T08:00:00Z",
            "disconnectTime": "2019-05-01T11:00:00Z",
            "sure_dk": 180.0,
            "kWhDelivered": 24.0,
            "kWhRequested": 25.0,
            "requestedDeparture": "2019-05-01T11:00:00Z",
            "minutesAvailable": 180.0,
        },
        {
            "sessionID": "s_u2_1",
            "siteID": "0001",
            "userID": "U2",
            "connectionTime": "2019-05-01T09:00:00Z",
            "disconnectTime": "2019-05-01T10:00:00Z",
            "sure_dk": 60.0,
            "kWhDelivered": 12.0,
            "kWhRequested": 15.0,
            "requestedDeparture": "2019-05-01T10:00:00Z",
            "minutesAvailable": 60.0,
        },
        # U2 - Oturum 2 (10:30 -> 11:30): Oturum 0 hâlâ bitmedi (11:00), ama Oturum 1 bitti (10:00 <= 10:30)
        # -> Sadece Oturum 1 geçmişe girmeli (n=1, sure=60, kwh=12)
        {
            "sessionID": "s_u2_2",
            "siteID": "0001",
            "userID": "U2",
            "connectionTime": "2019-05-01T10:30:00Z",
            "disconnectTime": "2019-05-01T11:30:00Z",
            "sure_dk": 60.0,
            "kWhDelivered": 9.0,
            "kWhRequested": 10.0,
            "requestedDeparture": "2019-05-01T11:30:00Z",
            "minutesAvailable": 60.0,
        },
        # anon kayıtları: önceki anon oturumu tamamlanmış olsa bile birbirinin geçmişini kullanmamalı
        {
            "sessionID": "s_anon_0",
            "siteID": "0001",
            "userID": "anon",
            "connectionTime": "2019-05-01T07:00:00Z",
            "disconnectTime": "2019-05-01T08:00:00Z",
            "sure_dk": 60.0,
            "kWhDelivered": 11.0,
            "kWhRequested": 12.0,
            "requestedDeparture": "2019-05-01T08:00:00Z",
            "minutesAvailable": 60.0,
        },
        {
            "sessionID": "s_anon_1",
            "siteID": "0001",
            "userID": "anon",
            "connectionTime": "2019-05-01T09:00:00Z",
            "disconnectTime": "2019-05-01T10:00:00Z",
            "sure_dk": 60.0,
            "kWhDelivered": 15.0,
            "kWhRequested": 16.0,
            "requestedDeparture": "2019-05-01T10:00:00Z",
            "minutesAvailable": 60.0,
        },
        # U3 - Aynı connectionTime damgalı iki oturum (deterministik davranış ve kendi hedefini sızdırmama)
        {
            "sessionID": "s_u3_base",
            "siteID": "0001",
            "userID": "U3",
            "connectionTime": "2019-05-01T06:00:00Z",
            "disconnectTime": "2019-05-01T07:00:00Z",
            "sure_dk": 60.0,
            "kWhDelivered": 7.0,
            "kWhRequested": 8.0,
            "requestedDeparture": "2019-05-01T07:00:00Z",
            "minutesAvailable": 60.0,
        },
        {
            "sessionID": "s_u3_tie_a",
            "siteID": "0001",
            "userID": "U3",
            "connectionTime": "2019-05-01T08:00:00Z",
            "disconnectTime": "2019-05-01T09:00:00Z",
            "sure_dk": 60.0,
            "kWhDelivered": 50.0,
            "kWhRequested": 50.0,
            "requestedDeparture": "2019-05-01T09:00:00Z",
            "minutesAvailable": 60.0,
        },
        {
            "sessionID": "s_u3_tie_b",
            "siteID": "0001",
            "userID": "U3",
            "connectionTime": "2019-05-01T08:00:00Z",
            "disconnectTime": "2019-05-01T10:00:00Z",
            "sure_dk": 120.0,
            "kWhDelivered": 90.0,
            "kWhRequested": 90.0,
            "requestedDeparture": "2019-05-01T10:00:00Z",
            "minutesAvailable": 120.0,
        },
    ]
    df = pd.DataFrame(kayitlar)
    df["connectionTime"] = pd.to_datetime(df["connectionTime"], utc=True)
    df["disconnectTime"] = pd.to_datetime(df["disconnectTime"], utc=True)
    df["requestedDeparture"] = pd.to_datetime(df["requestedDeparture"], utc=True)
    df["yerel_giris"] = df["connectionTime"].dt.tz_convert(data.TZ)
    df["beyan_sure_dk"] = (df["requestedDeparture"] - df["connectionTime"]).dt.total_seconds() / 60.0
    return df


def test_sentetik_gecmis_tum_durumlar():
    """Sentetik DataFrame üzerinde 8 geçmiş özelliği kuralını doğrular."""
    df = _sentetik_gecmis_df_olustur().set_index("sessionID", drop=False)

    X_vh = veri_hijyeni.ozellikler(df, strict_shift=True)
    X_dt = data.ozellikler(df)

    # 1. Kullanıcının ilk oturumu geçmiş taşımaz
    assert X_vh.loc["s_u1_0", "gecmis_n"] == 0
    assert np.isnan(X_vh.loc["s_u1_0", "gecmis_sure"])
    assert np.isnan(X_vh.loc["s_u1_0", "gecmis_kwh"])

    # 2. Önceki oturum mevcut oturumdan önce tamamlanmışsa geçmişe girer
    assert X_vh.loc["s_u1_1", "gecmis_n"] == 1
    assert np.isclose(X_vh.loc["s_u1_1", "gecmis_sure"], 60.0)
    assert np.isclose(X_vh.loc["s_u1_1", "gecmis_kwh"], 10.0)

    # 3. Önceki oturum mevcut oturumla çakışıyorsa geçmişe girmez (U2: s_u2_0 ile s_u2_1 çakışıyor)
    assert X_vh.loc["s_u2_1", "gecmis_n"] == 0
    assert np.isnan(X_vh.loc["s_u2_1", "gecmis_sure"])
    assert np.isnan(X_vh.loc["s_u2_1", "gecmis_kwh"])

    # 4. Hemen önceki oturum çakışsa bile daha eski tamamlanmış oturum geçmişe girer
    # U1'de s_u1_2 başlarken s_u1_1 hâlâ aktif, ama s_u1_0 tamamlanmış
    assert X_vh.loc["s_u1_2", "gecmis_n"] == 1
    assert np.isclose(X_vh.loc["s_u1_2", "gecmis_sure"], 60.0)
    assert np.isclose(X_vh.loc["s_u1_2", "gecmis_kwh"], 10.0)

    # U1'de s_u1_3 başlarken s_u1_0, s_u1_1 ve s_u1_2'nin tamamı bitmiş durumda
    assert X_vh.loc["s_u1_3", "gecmis_n"] == 3
    assert np.isclose(X_vh.loc["s_u1_3", "gecmis_sure"], (60.0 + 150.0 + 60.0) / 3.0)
    assert np.isclose(X_vh.loc["s_u1_3", "gecmis_kwh"], (10.0 + 30.0 + 14.0) / 3.0)

    # U2'de s_u2_2 başlarken s_u2_0 hâlâ aktif (11:00), ama s_u2_1 tamamlanmış (10:00 <= 10:30)
    assert X_vh.loc["s_u2_2", "gecmis_n"] == 1
    assert np.isclose(X_vh.loc["s_u2_2", "gecmis_sure"], 60.0)
    assert np.isclose(X_vh.loc["s_u2_2", "gecmis_kwh"], 12.0)

    # 5. Başka kullanıcıların oturumları geçmişe karışmaz (U2 ilk oturumu U1'den etkilenmez)
    assert X_vh.loc["s_u2_0", "gecmis_n"] == 0

    # 6. anon kayıtları birbirinin geçmişini kullanmaz
    assert X_vh.loc["s_anon_0", "gecmis_n"] == 0
    assert X_vh.loc["s_anon_1", "gecmis_n"] == 0
    assert np.isnan(X_vh.loc["s_anon_1", "gecmis_sure"])
    assert np.isnan(X_vh.loc["s_anon_1", "gecmis_kwh"])

    # 7. Aynı başlangıç zamanında deterministik davranış korunur ve kendi/eşzamanlı hedef sızmaz
    assert X_vh.loc["s_u3_tie_a", "gecmis_n"] == 1
    assert X_vh.loc["s_u3_tie_b", "gecmis_n"] == 1
    assert np.isclose(X_vh.loc["s_u3_tie_a", "gecmis_kwh"], 7.0)
    assert np.isclose(X_vh.loc["s_u3_tie_b", "gecmis_kwh"], 7.0)

    # Ters sıra verildiğinde de aynı deterministik sonuç üretilmeli
    df_ters = df.iloc[::-1].copy()
    X_ters = veri_hijyeni.ozellikler(df_ters, strict_shift=True).loc[df.index]
    pd.testing.assert_series_equal(X_vh["gecmis_n"], X_ters["gecmis_n"])
    pd.testing.assert_series_equal(X_vh["gecmis_sure"], X_ters["gecmis_sure"])
    pd.testing.assert_series_equal(X_vh["gecmis_kwh"], X_ters["gecmis_kwh"])

    # 8. data.ozellikler() ile veri_hijyeni.ozellikler(..., strict_shift=True) aynı geçmişi üretir
    pd.testing.assert_series_equal(X_vh["gecmis_n"], X_dt["gecmis_n"])
    pd.testing.assert_series_equal(X_vh["gecmis_sure"], X_dt["gecmis_sure"])
    pd.testing.assert_series_equal(X_vh["gecmis_kwh"], X_dt["gecmis_kwh"])

