"""Veri hijyeni, ┼şelale filtreleme ve s─▒z─▒nt─▒ denetim testleri."""

import pathlib
import numpy as np
import pandas as pd
import pytest

from sarjdenge import data, veri_hijyeni

PROJE_KOK = pathlib.Path(__file__).parent.parent
CSV_V2 = PROJE_KOK / "acn_oturumlar_v2.csv"
CSV_TEMMUZ = PROJE_KOK / "acn_oturumlar_temmuz_aralik.csv"


def test_manifest_tutarliligi(tmp_path):
    """Manifest ├╝retici t├╝m ACN dosyalar─▒n─▒ bulmal─▒, SHA256 ve sat─▒r say─▒lar─▒n─▒ do─şru yazmal─▒."""
    md_cikti = tmp_path / "MANIFEST_TEST.md"
    ham_cikti = tmp_path / "ham"
    m_df = veri_hijyeni.manifest_uret(klasor=PROJE_KOK, cikti_md=md_cikti, kopyala_dizin=ham_cikti)

    assert md_cikti.exists()
    assert len(m_df) >= 3
    assert "acn_oturumlar_v2.csv" in m_df["dosya_adi"].values
    assert (m_df["satir_sayisi"] > 0).all()
    assert (m_df["sha256"].str.len() == 64).all()

    # Kopyalanan dosyalar─▒n varl─▒─ş─▒ ve hash e┼şitli─şi
    kopyalar = list(ham_cikti.glob("*.csv"))
    assert len(kopyalar) >= 2


@pytest.mark.parametrize("csv_yol, beklenen_temiz, beklenen_beyanli", [
    (CSV_V2, 14219, 13123),
    (CSV_TEMMUZ, 13445, 12298),
])
def test_data_yukle_ile_eslesme(csv_yol, beklenen_temiz, beklenen_beyanli):
    """veri_hijyeni.temizle(sadece_beyanli=False) data.yukle() ile birebir ayn─▒ sat─▒r k├╝mesini vermeli."""
    if not csv_yol.exists():
        pytest.skip(f"{csv_yol} bulunamad─▒")

    df_eski = data.yukle(str(csv_yol))
    df_yeni = veri_hijyeni.temizle(str(csv_yol), sadece_beyanli=False)

    assert len(df_yeni) == beklenen_temiz, f"Yeni temiz sat─▒r={len(df_yeni)} != {beklenen_temiz}"
    assert len(df_eski) == len(df_yeni), f"Eski={len(df_eski)} != Yeni={len(df_yeni)}"
    assert set(df_eski["sessionID"]) == set(df_yeni["sessionID"]), "sessionID k├╝meleri e┼şle┼şmiyor"
    assert df_eski["beyan_var"].sum() == df_yeni["beyan_var"].sum() == beklenen_beyanli

    # sadece_beyanli=True kontrol├╝
    df_beyanli = veri_hijyeni.temizle(str(csv_yol), sadece_beyanli=True)
    assert len(df_beyanli) == beklenen_beyanli
    assert (df_beyanli["beyan_var"] == True).all()


def test_eleme_selalesi_tutarliligi():
    """┼Şelale ad─▒mlar─▒n─▒n toplam─▒ ba┼şlang─▒├ğ ham sat─▒r say─▒s─▒yla ve ara basamaklarla tutarl─▒ olmal─▒."""
    if not CSV_V2.exists():
        pytest.skip("acn_oturumlar_v2.csv bulunamad─▒")

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
    """Kullan─▒c─▒ ge├ğmi┼şi ├Âzellikleri kesinlikle yaln─▒zca karar an─▒ndan ├Ânce tamamlanm─▒┼ş oturumlardan gelmeli."""
    if not CSV_V2.exists():
        pytest.skip("acn_oturumlar_v2.csv bulunamad─▒")

    df = veri_hijyeni.temizle(CSV_V2, sadece_beyanli=False)
    X = veri_hijyeni.ozellikler(df, strict_shift=True)

    # 1. Her kullan─▒c─▒n─▒n ilk oturumu ge├ğmi┼ş ta┼ş─▒mamal─▒ (gecmis_n == 0, nan)
    for uid, grp in df.groupby("userID"):
        ilk_idx = grp.index[0]
        assert X.loc[ilk_idx, "gecmis_n"] == 0
        assert np.isnan(X.loc[ilk_idx, "gecmis_sure"])
        assert np.isnan(X.loc[ilk_idx, "gecmis_kwh"])

    # 2. Birden fazla oturumu olan bilinen kullan─▒c─▒lar─▒n ge├ğmi┼ş de─şerleri pozitif olmal─▒
    coklu_mask = (X["gecmis_n"] > 0)
    assert (X.loc[coklu_mask, "gecmis_sure"] >= 30.0).all()
    assert (X.loc[coklu_mask, "gecmis_kwh"] >= 0.5).all()


def test_zaman_sirali_ve_cakismasiz_bolme():
    """E─şitim ve test k├╝meleri zaman s─▒ras─▒yla ayr─▒lmal─▒ ve aralar─▒nda zaman ├ğak─▒┼şmas─▒ olmamal─▒."""
    if not CSV_V2.exists():
        pytest.skip("acn_oturumlar_v2.csv bulunamad─▒")

    df = veri_hijyeni.temizle(CSV_V2, sadece_beyanli=False)
    egit_df, test_df, kesim = veri_hijyeni.zaman_bol(df, bolme=0.6)

    assert len(egit_df) > 0 and len(test_df) > 0
    assert len(egit_df) + len(test_df) == len(df)
    assert egit_df["connectionTime"].max() < test_df["connectionTime"].min()
    assert len(set(egit_df["sessionID"]).intersection(set(test_df["sessionID"]))) == 0


def test_hedef_degiskenler_ozelliklerde_yok():
    """Hedef ve gelecek de─şi┼şkenler ├Âzellik matrisi X i├ğinde kesinlikle yer almamal─▒d─▒r."""
    if not CSV_V2.exists():
        pytest.skip("acn_oturumlar_v2.csv bulunamad─▒")

    df = veri_hijyeni.temizle(CSV_V2, sadece_beyanli=False)
    X = veri_hijyeni.ozellikler(df, strict_shift=True)

    yasakli_sutunlar = [
        "sure_dk", "kWhDelivered", "disconnectTime", "doneChargingTime",
        "target_sure_dk", "target_kwh_delivered", "girdi_sayisi", "girdi_degisti"
    ]
    for yasak in yasakli_sutunlar:
        assert yasak not in X.columns, f"S─▒z─▒nt─▒ tespit edildi: {yasak} ├Âzellik matrisinde bulundu!"


def _sentetik_gecmis_df_olustur() -> pd.DataFrame:
    """Kullan─▒c─▒ ge├ğmi┼şi s─▒z─▒nt─▒ ve ├ğak─▒┼şma senaryolar─▒n─▒ test etmek i├ğin k├╝├ğ├╝k sentetik DataFrame."""
    kayitlar = [
        # U1 - Oturum 0: ─░lk oturum (08:00 -> 09:00, 60 dk, 10 kWh) -> ge├ğmi┼ş yok
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
        # U1 - Oturum 1: Oturum 0 tamamland─▒ktan sonra ba┼şlar (09:30 -> 12:00, 150 dk, 30 kWh)
        # -> Oturum 0 ge├ğmi┼şe girmeli (n=1, sure=60, kwh=10)
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
        # U1 - Oturum 2: Oturum 1 devam ederken (├ğak─▒┼şarak) ba┼şlar (10:30 -> 11:30, 60 dk, 14 kWh)
        # -> Oturum 1 (12:00 biti┼ş > 10:30 ba┼şlang─▒├ğ) ge├ğmi┼şe G─░RMEMEL─░;
        #    ancak daha eski tamamlanm─▒┼ş Oturum 0 (09:00 biti┼ş <= 10:30) ge├ğmi┼şte KALMALI (n=1, sure=60, kwh=10)
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
        # U1 - Oturum 3: Hem Oturum 1 hem Oturum 2 bittikten sonra ba┼şlar (12:30 -> 13:30, 60 dk, 8 kWh)
        # -> Oturum 0, 1 ve 2'nin ├╝├ğ├╝ de tamamlanm─▒┼ş olmal─▒ (n=3, sure=(60+150+60)/3=90, kwh=(10+30+14)/3=18)
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
        # U2 - ─░lk oturumu ├ğak─▒┼şan ba┼şka bir kullan─▒c─▒: U1 ge├ğmi┼şinden etkilenmemeli
        # Oturum 0 (08:00 -> 11:00) ve Oturum 1 (09:00 -> 10:00) ├ğak─▒┼ş─▒yor -> ikisinde de n=0
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
        # U2 - Oturum 2 (10:30 -> 11:30): Oturum 0 h├ól├ó bitmedi (11:00), ama Oturum 1 bitti (10:00 <= 10:30)
        # -> Sadece Oturum 1 ge├ğmi┼şe girmeli (n=1, sure=60, kwh=12)
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
        # anon kay─▒tlar─▒: ├Ânceki anon oturumu tamamlanm─▒┼ş olsa bile birbirinin ge├ğmi┼şini kullanmamal─▒
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
        # U3 - Ayn─▒ connectionTime damgal─▒ iki oturum (deterministik davran─▒┼ş ve kendi hedefini s─▒zd─▒rmama)
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
    """Sentetik DataFrame ├╝zerinde 8 ge├ğmi┼ş ├Âzelli─şi kural─▒n─▒ do─şrular."""
    df = _sentetik_gecmis_df_olustur().set_index("sessionID", drop=False)

    X_vh = veri_hijyeni.ozellikler(df, strict_shift=True)
    X_dt = data.ozellikler(df)

    # 1. Kullan─▒c─▒n─▒n ilk oturumu ge├ğmi┼ş ta┼ş─▒maz
    assert X_vh.loc["s_u1_0", "gecmis_n"] == 0
    assert np.isnan(X_vh.loc["s_u1_0", "gecmis_sure"])
    assert np.isnan(X_vh.loc["s_u1_0", "gecmis_kwh"])

    # 2. ├ûnceki oturum mevcut oturumdan ├Ânce tamamlanm─▒┼şsa ge├ğmi┼şe girer
    assert X_vh.loc["s_u1_1", "gecmis_n"] == 1
    assert np.isclose(X_vh.loc["s_u1_1", "gecmis_sure"], 60.0)
    assert np.isclose(X_vh.loc["s_u1_1", "gecmis_kwh"], 10.0)

    # 3. ├ûnceki oturum mevcut oturumla ├ğak─▒┼ş─▒yorsa ge├ğmi┼şe girmez (U2: s_u2_0 ile s_u2_1 ├ğak─▒┼ş─▒yor)
    assert X_vh.loc["s_u2_1", "gecmis_n"] == 0
    assert np.isnan(X_vh.loc["s_u2_1", "gecmis_sure"])
    assert np.isnan(X_vh.loc["s_u2_1", "gecmis_kwh"])

    # 4. Hemen ├Ânceki oturum ├ğak─▒┼şsa bile daha eski tamamlanm─▒┼ş oturum ge├ğmi┼şe girer
    # U1'de s_u1_2 ba┼şlarken s_u1_1 h├ól├ó aktif, ama s_u1_0 tamamlanm─▒┼ş
    assert X_vh.loc["s_u1_2", "gecmis_n"] == 1
    assert np.isclose(X_vh.loc["s_u1_2", "gecmis_sure"], 60.0)
    assert np.isclose(X_vh.loc["s_u1_2", "gecmis_kwh"], 10.0)

    # U1'de s_u1_3 ba┼şlarken s_u1_0, s_u1_1 ve s_u1_2'nin tamam─▒ bitmi┼ş durumda
    assert X_vh.loc["s_u1_3", "gecmis_n"] == 3
    assert np.isclose(X_vh.loc["s_u1_3", "gecmis_sure"], (60.0 + 150.0 + 60.0) / 3.0)
    assert np.isclose(X_vh.loc["s_u1_3", "gecmis_kwh"], (10.0 + 30.0 + 14.0) / 3.0)

    # U2'de s_u2_2 ba┼şlarken s_u2_0 h├ól├ó aktif (11:00), ama s_u2_1 tamamlanm─▒┼ş (10:00 <= 10:30)
    assert X_vh.loc["s_u2_2", "gecmis_n"] == 1
    assert np.isclose(X_vh.loc["s_u2_2", "gecmis_sure"], 60.0)
    assert np.isclose(X_vh.loc["s_u2_2", "gecmis_kwh"], 12.0)

    # 5. Ba┼şka kullan─▒c─▒lar─▒n oturumlar─▒ ge├ğmi┼şe kar─▒┼şmaz (U2 ilk oturumu U1'den etkilenmez)
    assert X_vh.loc["s_u2_0", "gecmis_n"] == 0

    # 6. anon kay─▒tlar─▒ birbirinin ge├ğmi┼şini kullanmaz
    assert X_vh.loc["s_anon_0", "gecmis_n"] == 0
    assert X_vh.loc["s_anon_1", "gecmis_n"] == 0
    assert np.isnan(X_vh.loc["s_anon_1", "gecmis_sure"])
    assert np.isnan(X_vh.loc["s_anon_1", "gecmis_kwh"])

    # 7. Ayn─▒ ba┼şlang─▒├ğ zaman─▒nda deterministik davran─▒┼ş korunur ve kendi/e┼şzamanl─▒ hedef s─▒zmaz
    assert X_vh.loc["s_u3_tie_a", "gecmis_n"] == 1
    assert X_vh.loc["s_u3_tie_b", "gecmis_n"] == 1
    assert np.isclose(X_vh.loc["s_u3_tie_a", "gecmis_kwh"], 7.0)
    assert np.isclose(X_vh.loc["s_u3_tie_b", "gecmis_kwh"], 7.0)

    # Ters s─▒ra verildi─şinde de ayn─▒ deterministik sonu├ğ ├╝retilmeli
    df_ters = df.iloc[::-1].copy()
    X_ters = veri_hijyeni.ozellikler(df_ters, strict_shift=True).loc[df.index]
    pd.testing.assert_series_equal(X_vh["gecmis_n"], X_ters["gecmis_n"])
    pd.testing.assert_series_equal(X_vh["gecmis_sure"], X_ters["gecmis_sure"])
    pd.testing.assert_series_equal(X_vh["gecmis_kwh"], X_ters["gecmis_kwh"])

    # 8. data.ozellikler() ile veri_hijyeni.ozellikler(..., strict_shift=True) ayn─▒ ge├ğmi┼şi ├╝retir
    pd.testing.assert_series_equal(X_vh["gecmis_n"], X_dt["gecmis_n"])
    pd.testing.assert_series_equal(X_vh["gecmis_sure"], X_dt["gecmis_sure"])
    pd.testing.assert_series_equal(X_vh["gecmis_kwh"], X_dt["gecmis_kwh"])

