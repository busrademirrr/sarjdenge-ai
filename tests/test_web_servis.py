"""┼ŞarjDenge AI ÔÇö Web Servisi Testleri (─░┼ş Paketi E-UI).

Bu mod├╝l, web_servis.py bile┼şeninin senaryo y├╝kleme, profil ├ğ─▒karma,
fiziksel neden a├ğ─▒klay─▒c─▒s─▒ ve API sim├╝lasyon fonksiyonlar─▒n─▒ do─şrular.
"""

import pytest
import numpy as np
from sarjdenge import web_servis


def test_senaryo_tanimlari():
    """T├╝m senaryolar─▒n gerekli etiketleri ve alanlar─▒ i├ğerdi─şini do─şrular."""
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
    """Sentetik senaryo i├ğin sim├╝lasyonun 96 ad─▒ml─▒ profil ve KPI ├╝retti─şini do─şrular."""
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
    """Ara├ğ a├ğ─▒klay─▒c─▒s─▒n─▒n fiziksel nedenleri do─şru ├╝retti─şini do─şrular."""
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
    # Hayalet rezervasyon uyar─▒s─▒ ├╝retilmi┼ş olmal─▒
    assert "MPC_TILSIMI" in kategoriler or "ERKEN_AYRILMA" in kategoriler


def test_arac_dakika_saat_donusum_tutarliligi():
    """Gece giri┼ş yapan ara├ğta (├Âr. 18:45 = 1125 dk) 757.2 dk s├╝renin 12.6 saat olarak
    hesapland─▒─ş─▒n─▒, mutlak ayr─▒l─▒┼ş dakikas─▒ (1882.2 / 60 = 31.4 saat) ile kar─▒┼şt─▒r─▒lmad─▒─ş─▒n─▒ do─şrular."""
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
    """Erken ayr─▒lan ancak FCFS, EDF (Beyan) ve MPC (Beyan) y├Ântemlerinde %100 hedefe ula┼şan
    bir ara├ğta 'enerji kayb─▒na u─şrad─▒' iddias─▒n─▒n g├Âsterilmedi─şini do─şrular."""
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
    assert "enerji kayb─▒na u─şrad─▒" not in metin_tam
    assert "enerji kayb─▒na u─şramadan hedefi (ÔëÑ%95) tamamlad─▒" in metin_tam

