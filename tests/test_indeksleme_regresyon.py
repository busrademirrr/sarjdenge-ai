"""ŞarjDenge AI — İndeksleme Hatası Regresyon ve İndeks Güvenliği Testleri.

Bu test modülü, sarjdenge/deney_v2.py:169 satırındaki
    inan_kwh = np.asarray(kwh_arr)[gd.index.get_indexer(gd.index)][gec]
ifadesinden kaynaklanan veri eşleme hatasını belgeler, denetler ve
Adım 2'de uygulanacak güvenlik kalkanlarını test etmek üzere tasarlanmıştır.

Bölüm 1: Mevcut Koddaki Hatanın Kanıtı ve Beklenen Doğru Eşleştirme Testleri
Bölüm 2: Düzeltme Sonrasında Uygulanacak Güvenlik Kontrolleri (Adım 2 Ayrılmış Testler)
"""

import os
import pathlib
import unittest.mock
import numpy as np
import pandas as pd
import pytest

from sarjdenge import deney_v2, sim


# ---------------------------------------------------------------------------
# Sentetik Test Veri Üreticisi (İzole, Deterministik, Kullanıcı Verisiz)
# ---------------------------------------------------------------------------
def _sentetik_iki_gunluk_veri():
    """2 günlük, her gün 5 araçlık, oturum kimliği ve bilinen kWh değerleri içeren DataFrame.
    
    Not: Enerji değerleri deney_v2 içindeki clip(0.5, 100.0) sınırları dahilinde seçilmiştir:
      1. Gün: [10.0, 15.0, 20.0, 25.0, 30.0]
      2. Gün: [50.0, 60.0, 70.0, 80.0, 90.0]
    """
    t0 = pd.Timestamp("2019-01-01 00:00:00+00:00")
    t1 = pd.Timestamp("2019-01-02 00:00:00+00:00")
    data = []

    # 1. Gün (5 araç): kWh = [10.0, 15.0, 20.0, 25.0, 30.0]
    for i in range(5):
        val = float(10.0 + 5.0 * i)
        data.append({
            "session_id": f"S1_{i+1}",
            "connectionTime": t0 + pd.Timedelta(hours=8, minutes=15 * i),
            "disconnectTime": t0 + pd.Timedelta(hours=16, minutes=15 * i),
            "kWhRequested": val,
            "kWhDelivered": val,
            "siteID": "test_saha",
            "gun": "2019-01-01",
        })

    # 2. Gün (5 araç): kWh = [50.0, 60.0, 70.0, 80.0, 90.0]
    for i in range(5):
        val = float(50.0 + 10.0 * i)
        data.append({
            "session_id": f"S2_{i+1}",
            "connectionTime": t1 + pd.Timedelta(hours=8, minutes=15 * i),
            "disconnectTime": t1 + pd.Timedelta(hours=16, minutes=15 * i),
            "kWhRequested": val,
            "kWhDelivered": val,
            "siteID": "test_saha",
            "gun": "2019-01-02",
        })

    return pd.DataFrame(data)


# ===========================================================================
# BÖLÜM 1: Mevcut Koddaki İndeksleme Hatasını Belgeleyen ve Ortaya Çıkaran Testler
# ===========================================================================

def test_mevcut_kod_gunler_arasi_indeksleme_hatasini_gosterir():
    """Mevcut deney_v2.py:169 satırının 2. güne 1. günün kWh değerlerini atadığını belgeler.
    
    Hata Mekanizması:
    gd.index.get_indexer(gd.index) çağrısı bir indeksi kendisi üzerinde aradığı için
    daima [0, 1, ..., len(gd)-1] döner. Bu da kwh_arr'ın en başındaki (1. gün)
    elemanları çeker.
    """
    df = _sentetik_iki_gunluk_veri()
    kaynaklar = deney_v2.inanilan_kaynaklar(df)
    _, kwh_arr = kaynaklar["beyan"]

    gd_gun2 = df[df["gun"] == "2019-01-02"]
    gec = np.ones(len(gd_gun2), dtype=bool)

    # Mevcut satır 169 ifadesi:
    inan_kwh_mevcut = np.asarray(kwh_arr)[gd_gun2.index.get_indexer(gd_gun2.index)][gec]

    # Mevcut kodun HATASI: 2. gün oturumları [50..90] yerine 1. günün [10..30] değerlerini almıştır!
    assert np.array_equal(inan_kwh_mevcut, [10.0, 15.0, 20.0, 25.0, 30.0]), (
        "Mevcut kod 1. günün değerlerini sızdırmalıydı (hata yeniden üretilemedi)."
    )
    beklenen_gun2_kwh = gd_gun2["kWhRequested"].to_numpy(dtype=float)
    assert not np.array_equal(inan_kwh_mevcut, beklenen_gun2_kwh), (
        "Mevcut kodun 2. gün değerleriyle eşleşmemesi beklenir."
    )


def test_mevcut_kod_siralanmamis_indekslerde_yanlis_konum_alir():
    """Mevcut kodda gd.index sıralanmamış olduğunda etiket bazlı değil konumsal sıra alındığını belgeler."""
    df = _sentetik_iki_gunluk_veri()
    kaynaklar = deney_v2.inanilan_kaynaklar(df)
    _, kwh_arr = kaynaklar["beyan"]

    # 1. Gün indekslerini kasıtlı olarak ters/karışık sıralayalım: [4, 2, 0, 3, 1]
    karisik_indeksler = [4, 2, 0, 3, 1]
    gd_karisik = df.loc[karisik_indeksler]
    gec = np.ones(len(gd_karisik), dtype=bool)

    # Mevcut satır 169 ifadesi:
    inan_kwh_mevcut = np.asarray(kwh_arr)[gd_karisik.index.get_indexer(gd_karisik.index)][gec]

    # get_indexer kendi üzerinde arandığında yine [0, 1, 2, 3, 4] döndürür;
    # bu da orijinal [10, 15, 20, 25, 30] dizisinin ilk 5 elemanını verir.
    # Oysa beklenen etiket eşleşmesi [30.0, 20.0, 10.0, 25.0, 15.0] olmalıdır!
    beklenen_etiket_kwh = gd_karisik["kWhRequested"].to_numpy(dtype=float)
    assert not np.array_equal(inan_kwh_mevcut, beklenen_etiket_kwh), (
        "Mevcut kod sıralanmamış indekslerde etiketleri doğru eşleştiremez."
    )


def test_simule_gun_gercek_akis_gec_maskesi_ve_ayni_oturum_eslesmesi():
    """Gerçek simule_gun veri akışında gec maskesi uygulandıktan sonra zaman ve kWh değerlerinin
    aynı oturumlara ait olduğunu doğrular.
    
    1. ve 2. günün verilerinde birer oturumun süresi 0 yapılarak gec maskesiyle elenir.
    Simülatöre giden inan_dep ve inan_kwh değerleri yakalanır; mevcut koddaki uyumsuzluk belgelenir.
    """
    df = _sentetik_iki_gunluk_veri()

    # 2. günün 2. aracının ayrılışını girişine eşitleyelim (gec = False olsun)
    # İndeks 6: S2_2 aracı
    df.loc[6, "disconnectTime"] = df.loc[6, "connectionTime"]

    kaynaklar = deney_v2.inanilan_kaynaklar(df)
    ts_series, kwh_arr = kaynaklar["beyan"]

    gd_gun2 = df[df["gun"] == "2019-01-02"]
    t0_gun2 = pd.Timestamp("2019-01-02 00:00:00+00:00")

    giris = np.ceil(deney_v2.adimlar(gd_gun2["connectionTime"], t0_gun2)).astype(int)
    ayril = np.floor(deney_v2.adimlar(gd_gun2["disconnectTime"], t0_gun2)).astype(int)
    gec = ayril > giris

    # gec: [True, False, True, True, True] -> Hayatta kalan 4 araç: S2_1, S2_3, S2_4, S2_5
    assert gec.sum() == 4
    assert not gec[1]  # S2_2 elendi

    # Mevcut kodun ürettiği inan_kwh:
    inan_kwh_mevcut = np.asarray(kwh_arr)[gd_gun2.index.get_indexer(gd_gun2.index)][gec]

    # Mevcut kod 1. günün ilk 5 elemanından 1. indeksi eler: [10, 20, 25, 30]
    assert np.array_equal(inan_kwh_mevcut, [10.0, 20.0, 25.0, 30.0])

    # Oysa S2_1, S2_3, S2_4, S2_5 için beklenen gerçek değerler: [50.0, 70.0, 80.0, 90.0] olmalıdır!
    beklenen_kwh = gd_gun2.loc[gec, "kWhRequested"].to_numpy(dtype=float)
    assert np.array_equal(beklenen_kwh, [50.0, 70.0, 80.0, 90.0])
    assert not np.array_equal(inan_kwh_mevcut, beklenen_kwh), (
        "Mevcut kod gec maskesi sonrası 2. günün oturumlarıyla eşleşmiyor."
    )


def test_farkli_gunlerde_enerji_eslestirme_dogru_sozlesmesi():
    """Düzeltme sonrası geçerli olacak kwh_series.loc[gd.index][gec] sözleşmesini doğrular."""
    df = _sentetik_iki_gunluk_veri()

    # Düzeltilmiş yapı: kwh bir pd.Series olarak df.index ile birebir hizalıdır:
    kwh_series_duzeltilmis = pd.Series(df["kWhRequested"].to_numpy(dtype=float), index=df.index)

    gd_gun2 = df[df["gun"] == "2019-01-02"]
    gec = np.ones(len(gd_gun2), dtype=bool)

    # Düzeltilmiş satır 169 mantığı:
    inan_kwh_duzeltilmis = kwh_series_duzeltilmis.loc[gd_gun2.index][gec].to_numpy(dtype=float)

    # 2. gün oturumları kesin olarak kendi kWh değerlerini [50..90] almalıdır:
    assert np.array_equal(inan_kwh_duzeltilmis, [50.0, 60.0, 70.0, 80.0, 90.0]), (
        "Düzeltilmiş mantık 2. güne kendi değerlerini tam ve eksiksiz atamalıdır."
    )


def test_simule_gun_duzeltilmis_entegrasyon_dogrulamasi():
    """deney_v2.simule_gun fonksiyonunun 2. günde sim.simule motoruna tam olarak 2. günün değerlerini aktardığını doğrular."""
    df = _sentetik_iki_gunluk_veri()
    kaynaklar = deney_v2.inanilan_kaynaklar(df)
    gd_gun2 = df[df["gun"] == "2019-01-02"]
    t0_gun2 = pd.Timestamp("2019-01-02 00:00:00+00:00")

    yakalanan_inan_kwh = []
    gercek_simule = sim.simule

    def sahte_simule(giris, ayril, e_gercek, inan_dep, inan_kwh, cap, yont_func):
        yakalanan_inan_kwh.append(np.copy(inan_kwh))
        return gercek_simule(giris, ayril, e_gercek, inan_dep, inan_kwh, cap, yont_func)

    with unittest.mock.patch.object(sim, "simule", side_effect=sahte_simule):
        res = deney_v2.simule_gun(
            gd=gd_gun2,
            kaynaklar=kaynaklar,
            t0=t0_gun2,
            kapasiteler=(0.7,),
            secili_yontemler={"fcfs_beyan": ("fcfs", "beyan")},
        )

    assert len(res) > 0
    assert len(yakalanan_inan_kwh) > 0
    # 2. günün sim.simule motoruna iletilen inan_kwh değeri kesin olarak [50..90] olmalı:
    assert np.array_equal(yakalanan_inan_kwh[0], [50.0, 60.0, 70.0, 80.0, 90.0]), (
        f"simule_gun 2. güne yanlış enerji aktardı: {yakalanan_inan_kwh[0]}"
    )


# ===========================================================================
# BÖLÜM 2: Düzeltme Sonrasında Uygulanacak Güvenlik Kontrolleri
# (deney_v2.py henüz değiştirilmediği için bu kontroller Adım 2 sonrasına ayrılmıştır)
# ===========================================================================

class TestDuzeltmeSonrasiGuvenlikKontrolleri:
    """Bu sınıf, Adım 2'de deney_v2.py güncellendikten sonra aktifleşecek
    indeks güvenliği ve üzerine yazmayı önleme kalkanlarını denetler.
    
    Henüz uygulanmamış kontroller varmış gibi davranılmaz; deney_v2.py güncellenene
    kadar durum açıkça tespit edilip testler atlanır (skip).
    """

    @pytest.fixture(autouse=True)
    def kontrol_guvenlik_kalkani_aktif_mi(self):
        """deney_v2.py içinde güvenlik kalkanının bulunup bulunmadığını kontrol eder."""
        self.kalkan_mevcut = getattr(deney_v2, "INDEKS_GUVENLIK_KALKANI", False)

    def test_yinelenen_indekslerin_guvenli_reddedilmesi(self):
        """df_tahminli.index benzersiz olmadığında açık ValueError fırlatılmalıdır."""
        if not self.kalkan_mevcut:
            pytest.skip("deney_v2.py henüz güncellenmedi (Adım 2: İndeks güvenlik kalkanı bekleniyor).")

        df = _sentetik_iki_gunluk_veri()
        # Kasıtlı yinelenen indeks oluşturalım: [0, 0, 2, 3, ...]
        df.index = [0, 0] + list(range(2, len(df)))

        with pytest.raises(ValueError, match="benzersiz değil"):
            deney_v2.deney_calistir(df)

    def test_hizasiz_series_indekslerinin_guvenli_reddedilmesi(self):
        """Enerji veya zaman dizisi df_tahminli ile tam hizalı değilse açık ValueError fırlatılmalıdır."""
        if not self.kalkan_mevcut:
            pytest.skip("deney_v2.py henüz güncellenmedi (Adım 2: İndeks güvenlik kalkanı bekleniyor).")

        df = _sentetik_iki_gunluk_veri()
        # Kaynak serisi yanlış indeksli olduğunda
        bozuk_kaynaklar = deney_v2.inanilan_kaynaklar(df)
        ts_s, kwh_s = bozuk_kaynaklar["beyan"]
        # İndeksi kaydıralım
        bozuk_kwh_s = pd.Series(kwh_s.to_numpy(), index=list(range(100, 100 + len(df))))
        bozuk_kaynaklar["beyan"] = (ts_s, bozuk_kwh_s)

        t0 = pd.Timestamp("2019-01-01 00:00:00+00:00")
        with pytest.raises(ValueError, match="tam hizalı değil|uyuşmuyor"):
            deney_v2.simule_gun(df[df["gun"] == "2019-01-01"], bozuk_kaynaklar, t0)

    def test_duzeltilmis_cikti_dosyasi_mevcutsa_deneyin_baslamadan_durmasi(self, tmp_path):
        """data/deney_tablo_val_duzeltilmis.csv gibi hedef dosyalardan biri mevcutsa deney FileExistsError ile durmalıdır."""
        if not self.kalkan_mevcut:
            pytest.skip("deney_v2.py henüz güncellenmedi (Adım 2: Çıktı dosya koruma kalkanı bekleniyor).")

        # Var olan sahte bir düzeltilmiş çıktı dosyası taklit edelim
        var_olan_dosya = tmp_path / "deney_tablo_val_duzeltilmis.csv"
        var_olan_dosya.write_text("saha,gun,f,ok\n", encoding="utf-8")

        with unittest.mock.patch.object(deney_v2, "DUZELTILMIS_VAL_DOSYASI", var_olan_dosya):
            with pytest.raises(FileExistsError, match="zaten diskte mevcut|zaten mevcut"):
                deney_v2.tam_deney_hattini_calistir()
