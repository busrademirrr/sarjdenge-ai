"""ŞarjDenge AI — Web Servisi Testleri (İş Paketi E-UI).

Bu modül, web_servis.py bileşeninin senaryo yükleme, profil çıkarma,
fiziksel neden açıklayıcısı ve API simülasyon fonksiyonlarını doğrular.
"""

import pytest
import numpy as np
from sarjdenge import web_servis


def test_senaryo_tanimlari():
    """Tüm senaryoların gerekli etiketleri ve alanları içerdiğini doğrular."""
    senaryolar = web_servis.SENARYOLAR
    assert "acn_gercek_val" in senaryolar
    assert "isyeri_gunduz" in senaryolar
    assert "apartman_gece" in senaryolar
    assert "karma" in senaryolar

    for s_id, s_info in senaryolar.items():
        assert "id" in s_info
        assert "etiket" in s_info
        assert "veri_turu" in s_info
        assert s_info["veri_turu"] in ("GERCEK", "SENTETIK")
        assert len(s_info["mevcut_gunler"]) > 0


def test_simulasyon_calistir_sentetik():
    """Sentetik senaryo için simülasyonun 96 adımlı profil ve KPI ürettiğini doğrular."""
    res = web_servis.simulasyon_calistir_api(
        senaryo_id="isyeri_gunduz",
        f=0.5,
        gun_secimi="2026-03-10",
        tohum=42,
    )

    assert "hata" not in res
    assert res["senaryo_id"] == "isyeri_gunduz"
    assert res["arac_sayisi"] > 0
    beklenen_ufuk = max(96, max(a["ayril_adim"] for a in res["araclar"]) + 1)
    assert len(res["zaman_etiketleri"]) == beklenen_ufuk
    assert len(res["kontrolsuz_profil_kw"]) == beklenen_ufuk
    assert res["kapasite_siniri_kw"] > 0

    for y_kod in res["yontem_profilleri"].keys():
        assert len(res["yontem_profilleri"][y_kod]) == beklenen_ufuk
        assert all(p >= 0.0 for p in res["yontem_profilleri"][y_kod])
        assert max(res["yontem_profilleri"][y_kod]) <= res["kapasite_siniri_kw"] + 1e-3
        assert y_kod in res["kpi_ozet"]
        kpi = res["kpi_ozet"][y_kod]
        assert 0.0 <= kpi["basari_orani_yuzde"] <= 100.0
        assert 0.0 <= kpi["teslim_orani_yuzde"] <= 100.0
        assert kpi["kapasite_ihlali_kw"] == 0.0


def test_simulasyon_gece_yarisi_asan_oturumlar():
    """Gece yarısını aşan oturumlarda (apartman_gece) simülasyon ufkunun max(ayril)+1 adıma uzadığını,
    '+1g 02:15' biçiminde etiket ürettiğini, 24:00 sonrasında güç dizisinin sıfırdan büyük değerler
    içerdiğini ve KPI'ların kapasite_danismani_hesapla ile aynı kapasitede tutarlı çıktığını doğrular."""
    res = web_servis.simulasyon_calistir_api(
        senaryo_id="apartman_gece",
        f=0.5,
        gun_secimi="2026-03-10",
        tohum=42,
    )
    assert "hata" not in res
    assert res["arac_sayisi"] == 14

    max_ayril = max(a["ayril_adim"] for a in res["araclar"])
    beklenen_ufuk = max(96, max_ayril + 1)
    assert beklenen_ufuk > 96
    assert len(res["zaman_etiketleri"]) == beklenen_ufuk
    assert len(res["kontrolsuz_profil_kw"]) == beklenen_ufuk
    assert "+1g 02:15" in res["zaman_etiketleri"]
    # Çok günlü etiket desteği kontrolü
    assert web_servis.adim_saat_etiketi(96 + 9) == "+1g 02:15"
    assert web_servis.adim_saat_etiketi(192 + 5) == "+2g 01:15"

    # 24:00 sonrasında (indeks >= 96) kontrolsüz ve algoritmik güç dizilerinde sıfır olmayan değerler bulunmalı
    assert any(p > 0.0 for p in res["kontrolsuz_profil_kw"][96:])
    for y_kod in ["fcfs_beyan", "esit_beyan", "edf_beyan", "mpc_beyan"]:
        prof = res["yontem_profilleri"][y_kod]
        assert len(prof) == beklenen_ufuk
        assert any(p > 0.0 for p in prof[96:])
        assert res["kpi_ozet"][y_kod]["basari_orani_yuzde"] == 100.0
        assert res["kpi_ozet"][y_kod]["kapasite_ihlali_kw"] == 0.0

    # Kapasite danışmanı ile aynı kapasitede (cap_kw) KPI tutarlılığı
    cap_kw = res["kapasite_siniri_kw"]
    danisman = web_servis.kapasite_danismani_hesapla(
        senaryo_id="apartman_gece",
        gun_secimi="2026-03-10",
        tohum=42,
        aday_kapasiteler=[cap_kw],
    )
    esleme = {"fcfs": "fcfs_beyan", "edf": "edf_beyan", "esit": "esit_beyan", "mpc": "mpc_beyan"}
    for y_dan in danisman["yontemler"]:
        sim_kod = esleme[y_dan["kod"]]
        nokta = y_dan["tarama"][0]
        assert nokta["kapasite_kw"] == round(cap_kw, 1)
        assert pytest.approx(nokta["hedef_karsilama_yuzde"], abs=0.15) == res["kpi_ozet"][sim_kod]["basari_orani_yuzde"]
        assert pytest.approx(nokta["teslim_orani_yuzde"], abs=0.15) == res["kpi_ozet"][sim_kod]["teslim_orani_yuzde"]


def test_simulasyon_hatali_girdi_yonetimi():
    """Geçersiz senaryo veya veri bulunmayan tarihte yapılandırılmış hata döndüğünü doğrular."""
    res_bad_scen = web_servis.simulasyon_calistir_api(senaryo_id="olmayan_senaryo", f=0.5)
    assert "hata" in res_bad_scen

    res_bad_date = web_servis.simulasyon_calistir_api(
        senaryo_id="acn_gercek_val",
        f=0.5,
        gun_secimi="2099-12-31",
    )
    assert "hata" in res_bad_date


def test_kapasite_danismani_api_tum_algoritmalar():
    """Kapasite danışmanının 4 algoritmayı aynı kesit üzerinde karşılaştırdığını doğrular."""
    res = web_servis.kapasite_danismani_hesapla(
        senaryo_id="isyeri_gunduz",
        gun_secimi="2026-03-10",
        tohum=42,
    )
    assert "hata" not in res
    assert res["arac_sayisi"] > 0
    kodlar = [y["kod"] for y in res["yontemler"]]
    assert set(kodlar) == {"fcfs", "edf", "esit", "mpc"}
    assert res["onerilen_asgari_kapasite_kw"] is not None
    assert res["onerilen_asgari_kapasite_kw"] > 0


def test_arac_neden_aciklamasi():
    """Araç açıklayıcısının fiziksel nedenleri doğru ürettiğini doğrular."""
    neden = web_servis.arac_neden_aciklamasi(
        arac_idx=0,
        sat_oranlari={"mpc_tahmin_guvenli": 0.60, "mpc_beyan": 1.0, "edf_beyan": 1.0, "fcfs_beyan": 0.7},
        teslim_kwh={"mpc_tahmin_guvenli": 6.0, "mpc_beyan": 10.0, "edf_beyan": 10.0},
        e_gercek=10.0,
        giris_dk=480.0,
        ayril_dk=960.0,
        beyan_dep_dk=1000.0,
        tahmin_dep_dk=800.0,
        beyan_kwh=12.0,
        tahmin_kwh=15.0,
        erken_ayrildi=True,
        cap_kw=25.0,
        es_zamanli_arac_sayisi=10,
    )

    assert "nedenler" in neden
    assert len(neden["nedenler"]) > 0
    kategoriler = [n["kategori"] for n in neden["nedenler"]]
    # Hayalet rezervasyon uyarısı üretilmiş olmalı
    assert "MPC_TILSIMI" in kategoriler or "ERKEN_AYRILMA" in kategoriler


def test_arac_dakika_saat_donusum_tutarliligi():
    """Gece giriş yapan araçta (ör. 18:45 = 1125 dk) 757.2 dk sürenin 12.6 saat olarak
    hesaplandığını, mutlak ayrılış dakikası (1882.2 / 60 = 31.4 saat) ile karıştırılmadığını doğrular."""
    giris_dk = 1125.0
    sure_tahmin_q20_dk = 757.2
    sure_beyan_dk = 840.0
    neden = web_servis.arac_neden_aciklamasi(
        arac_idx=0,
        sat_oranlari={"mpc_tahmin_guvenli": 1.0, "mpc_beyan": 0.80, "edf_beyan": 1.0, "fcfs_beyan": 1.0},
        teslim_kwh={"mpc_tahmin_guvenli": 15.0, "mpc_beyan": 12.0, "edf_beyan": 15.0},
        e_gercek=15.0,
        giris_dk=giris_dk,
        ayril_dk=giris_dk + 780.0,
        beyan_dep_dk=giris_dk + sure_beyan_dk,
        tahmin_dep_dk=giris_dk + sure_tahmin_q20_dk,
        beyan_kwh=18.0,
        tahmin_kwh=16.0,
        erken_ayrildi=True,
        cap_kw=30.0,
        es_zamanli_arac_sayisi=8,
    )
    metinler = " ".join(n["metin"] for n in neden["nedenler"])
    assert "757.2 dk / 12.6 sa" in metinler
    assert "31.4 sa" not in metinler


def test_arac_yuzde_yuz_hedefte_yanlis_enerji_kaybi_gosterilmemesi():
    """Erken ayrılan ancak FCFS, EDF (Beyan) ve MPC (Beyan) yöntemlerinde %100 hedefe ulaşan
    bir araçta 'enerji kaybına uğradı' iddiasının gösterilmediğini doğrular."""
    neden_tam = web_servis.arac_neden_aciklamasi(
        arac_idx=1,
        sat_oranlari={"mpc_tahmin_guvenli": 1.0, "mpc_beyan": 1.0, "edf_beyan": 1.0, "fcfs_beyan": 1.0},
        teslim_kwh={"mpc_tahmin_guvenli": 12.0, "mpc_beyan": 12.0, "edf_beyan": 12.0, "fcfs_beyan": 12.0},
        e_gercek=12.0,
        giris_dk=480.0,
        ayril_dk=840.0,
        beyan_dep_dk=900.0,
        tahmin_dep_dk=800.0,
        beyan_kwh=14.0,
        tahmin_kwh=13.0,
        erken_ayrildi=True,
        cap_kw=40.0,
        es_zamanli_arac_sayisi=6,
    )
    kategoriler_tam = [n["kategori"] for n in neden_tam["nedenler"]]
    metin_tam = " ".join(n["metin"] for n in neden_tam["nedenler"])
    assert "ERKEN_AYRILMA_ZARARSIZ" in kategoriler_tam
    assert "enerji kaybına uğradı" not in metin_tam
    assert "enerji kaybına uğramadan hedefi (≥%95) tamamladı" in metin_tam


def test_arac_neden_aciklamasi_ihtiyatli_dil_ve_bos_tahmin():
    """Karar notlarında kesin nedensellik ('fiziksel', 'yol açmıştır', 'yol açtı', 'kilitledi')
    bulunmadığını, gün aşımı saat etiketlerinin doğru üretildiğini ve boş tahminde kanıtsız
    tahmin nedeni üretilmediğini doğrular."""
    # 1. Gün aşımı ve FCFS farkı durumu (tahmin verisi olmadan)
    neden_bos_tahmin = web_servis.arac_neden_aciklamasi(
        arac_idx=2,
        sat_oranlari={"fcfs_beyan": 0.65, "edf_beyan": 1.0, "mpc_beyan": 1.0},
        teslim_kwh={"fcfs_beyan": 13.0, "edf_beyan": 20.0, "mpc_beyan": 20.0},
        e_gercek=20.0,
        giris_dk=1155.0,  # 19:15
        ayril_dk=1575.0,  # +1g 02:15 (420 dk kalış)
        sure_beyan_dk=480.0,
        sure_tahmin_dk=None,
        beyan_kwh=22.0,
        tahmin_kwh=None,
        erken_ayrildi=True,
        cap_kw=25.0,
        es_zamanli_arac_sayisi=10,
    )
    kategoriler = [n["kategori"] for n in neden_bos_tahmin["nedenler"]]
    tum_metin = " ".join(n["baslik"] + " " + n["metin"] for n in neden_bos_tahmin["nedenler"]).lower()

    # Tahmin verisi yokken tahmin kaynaklı neden üretilmemeli
    assert "MPC_TILSIMI" not in kategoriler
    assert "TAHMIN_AVANTAJI" not in kategoriler
    # Gün aşımı saat etiketi (+1g 02:15) ve beyan çıkışı (+1g 03:15) doğru yer almalı
    assert "+1g 02:15" in tum_metin
    assert "+1g 03:15" in tum_metin
    # Kesin nedensellik ifadeleri bulunmamalı
    for yasak in ["fiziksel", "yol açmıştır", "yol açtı", "kilitledi"]:
        assert yasak not in tum_metin
    assert "olası neden" in tum_metin or "ilişkili olabilir" in tum_metin


