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
