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
    assert len(res["zaman_etiketleri"]) == 96
    assert len(res["kontrolsuz_profil_kw"]) == 96
    assert res["kapasite_siniri_kw"] > 0
    
    for y_kod in ["fcfs_beyan", "edf_beyan", "edf_tahmin_guvenli", "mpc_beyan", "mpc_tahmin_guvenli"]:
        assert y_kod in res["yontem_profilleri"]
        assert len(res["yontem_profilleri"][y_kod]) == 96
        assert y_kod in res["kpi_ozet"]
        kpi = res["kpi_ozet"][y_kod]
        assert 0.0 <= kpi["basari_orani_yuzde"] <= 100.0
        assert 0.0 <= kpi["teslim_orani_yuzde"] <= 100.0
        assert kpi["kapasite_ihlali_kw"] == 0.0


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
