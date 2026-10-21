"""┼ŞarjDenge AI ÔÇö Kapasite Dan─▒┼şman─▒ ve E┼şit Payla┼ş─▒m S─▒n─▒r Durum Testleri.

Bu test mod├╝l├╝ a┼şa─ş─▒daki s─▒n─▒r ve g├╝venlik durumlar─▒n─▒ do─şrular:
1. Tekillik (tek ara├ğ veya s─▒f─▒r ara├ğ durumu)
2. Fiziksel olarak eri┼şilemeyen hedefler (PMAX * s├╝re < talep)
3. Ayr─▒k g├╝├ğ kademeleri ve trafo kapasite s─▒n─▒r─▒n─▒n a┼ş─▒lmamas─▒
4. Gece yar─▒s─▒n─▒ a┼şan oturumlar (gece ┼şarj─▒)
5. Aktif Ara├ğlara E┼şit G├╝├ğ Payla┼ş─▒m─▒ (esit_paylasim_kurali) dinamikleri
6. Tekrarlanabilirlik (determinizm ve tutarl─▒l─▒k)
7. 2019 H1 verisinden ├Â─şrenilen beyan oranlar─▒ JSON b├╝t├╝nl├╝─ş├╝
"""

import json
import pathlib
import pytest
import numpy as np
import pandas as pd

from sarjdenge import sim, web_servis

PROJE_KOK = pathlib.Path(__file__).resolve().parent.parent


def test_beyan_oranlari_json_yukleme_ve_degerler():
    """config/beyan_oranlari.json dosyas─▒n─▒n varl─▒─ş─▒ ve H1 kuantil de─şerleri do─şrulan─▒r."""
    json_yolu = PROJE_KOK / "config" / "beyan_oranlari.json"
    assert json_yolu.exists(), "config/beyan_oranlari.json bulunamad─▒!"

    with open(json_yolu, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["egitim_satir_sayisi"] == 7808
    assert data["dogrulama_satir_sayisi"] == 5315

    sure_q = data["sure_oranlari"]
    enerji_q = data["enerji_oranlari"]

    assert pytest.approx(sure_q["q20"], rel=1e-3) == 0.8889
    assert pytest.approx(sure_q["q50"], rel=1e-3) == 1.1062
    assert pytest.approx(sure_q["q80"], rel=1e-3) == 1.6352

    assert pytest.approx(enerji_q["q20"], rel=1e-3) == 0.3549
    assert pytest.approx(enerji_q["q50"], rel=1e-3) == 0.6074
    assert pytest.approx(enerji_q["q80"], rel=1e-3) == 0.8446


def test_esit_paylasim_kurali_temel_ve_kapasite_siniri():
    """E┼şit payla┼ş─▒m kural─▒n─▒n ara├ğlara e┼şit g├╝├ğ tahsis etti─şini ve kapasiteyi a┼şmad─▒─ş─▒n─▒ test eder."""
    t = 0
    # 4 ara├ğ, her birinin 20 kWh ihtiyac─▒ var
    kalan = np.array([20.0, 20.0, 20.0, 20.0])
    dep = np.array([20, 20, 20, 20])
    giris = np.array([0, 0, 0, 0])
    cap = 15.0  # 15 kW kapasite

    hiz = web_servis.esit_paylasim_kurali(t, kalan, dep, giris, cap)

    assert len(hiz) == 4
    assert hiz.sum() <= cap + 1e-6, f"Kapasite a┼ş─▒ld─▒: {hiz.sum()} > {cap}"
    # Ayr─▒k seviyelerden biri olmal─▒
    for h in hiz:
        assert any(np.isclose(h, sim.SEVIYELER, atol=1e-5)), f"Ge├ğersiz seviye: {h}"
    # Ara├ğlar e┼şit durumda ba┼şlad─▒─ş─▒ i├ğin h─▒z fark─▒ en fazla bir ayr─▒k kademe olabilir
    assert hiz.max() - hiz.min() <= sim.SEVIYELER[1] + 1e-5


def test_esit_paylasim_talep_tamamlanmis_arac():
    """Kalan ihtiyac─▒ 0 olan ara├ğlara e┼şit pay verilmemeli, sadece artan g├╝├ğ f─▒rsat├ğ─▒ verilmeli."""
    t = 5
    kalan = np.array([0.0, 15.0, 15.0])
    dep = np.array([20, 20, 20])
    giris = np.array([0, 0, 0])
    cap = 10.0

    hiz = web_servis.esit_paylasim_kurali(t, kalan, dep, giris, cap)
    assert hiz.sum() <= cap + 1e-6
    # ─░lk arac─▒n ihtiyac─▒ 0 oldu─şu i├ğin ├Âncelikli e┼şit pay─▒ talep eden 2. ve 3. ara├ğ al─▒r
    assert hiz[1] >= hiz[0]
    assert hiz[2] >= hiz[0]


def test_esit_paylasim_bos_kume():
    """Hi├ğ ara├ğ olmad─▒─ş─▒nda bo┼ş dizi d├Ânmeli."""
    hiz = web_servis.esit_paylasim_kurali(0, np.zeros(0), np.zeros(0), np.zeros(0), 20.0)
    assert len(hiz) == 0


def test_tekillik_tek_arac():
    """Tek bir ara├ğ varken kapasite dan─▒┼şman─▒ veya e┼şit payla┼ş─▒m hatas─▒z ├ğal─▒┼şmal─▒."""
    t = 0
    kalan = np.array([10.0])
    dep = np.array([10])
    giris = np.array([0])
    cap = 20.0

    hiz = web_servis.esit_paylasim_kurali(t, kalan, dep, giris, cap)
    assert len(hiz) == 1
    assert hiz[0] <= sim.PMAX + 1e-6
    assert hiz[0] <= cap + 1e-6


def test_fiziksel_olarak_ulasilamaz_hedef():
    """Kal─▒┼ş s├╝resi ├ğok k─▒sa olan ve PMAX ile dahi dolamayacak ara├ğlar─▒n analizi."""
    # 1 saat kal─▒┼ş (4 ad─▒m), 50 kWh talep (PMAX 6.656 kW -> azami 6.656 kWh al─▒nabilir)
    giris = np.array([0])
    ayril = np.array([4])
    e_gercek = np.array([50.0])

    sure_saat = (ayril - giris) * sim.DT_H
    fiziksel_ulasilamaz = (e_gercek > sim.PMAX * sure_saat + 1e-6)
    assert fiziksel_ulasilamaz[0] == True

    # Sim├╝lasyon yine de g├╝venli ├ğal─▒┼şmal─▒ ve kapasiteyi a┼şmamal─▒
    teslim = sim.simule(giris, ayril, e_gercek, ayril, e_gercek, 100.0, sim.kural("fcfs"))
    assert teslim[0] <= sim.PMAX * 1.0 + 1e-5


def test_gece_yarisini_asan_oturumlar():
    """Gece yar─▒s─▒n─▒ a┼şan oturumlarda sim├╝lasyon ve ayr─▒k seviye s├╝reklili─şi."""
    # 22:00'de giri┼ş (ad─▒m 88), ertesi g├╝n 06:00'da ayr─▒l─▒┼ş (ad─▒m 112)
    giris = np.array([88, 90])
    ayril = np.array([112, 115])
    e_gercek = np.array([25.0, 30.0])

    cap = 10.0
    teslim_esit = sim.simule(giris, ayril, e_gercek, ayril, e_gercek, cap, web_servis.esit_paylasim_kurali)
    teslim_edf = sim.simule(giris, ayril, e_gercek, ayril, e_gercek, cap, sim.kural("edf"))

    assert len(teslim_esit) == 2
    assert len(teslim_edf) == 2
    assert teslim_esit.sum() > 0
    assert teslim_edf.sum() > 0


def test_kapasite_danismani_determinizm():
    """Ayn─▒ girdilerle ├ğa─şr─▒lan kapasite dan─▒┼şman─▒ birebir ├Âzde┼ş sonu├ğlar ├╝retmelidir."""
    sonuc1 = web_servis.kapasite_danismani_hesapla(
        senaryo_id="isyeri_gunduz",
        gun_secimi="2026-03-10",
        tohum=42,
    )
    sonuc2 = web_servis.kapasite_danismani_hesapla(
        senaryo_id="isyeri_gunduz",
        gun_secimi="2026-03-10",
        tohum=42,
    )

    assert sonuc1["onerilen_asgari_kapasite_kw"] == sonuc2["onerilen_asgari_kapasite_kw"]
    assert sonuc1["kontrolsuz_tepe_kw"] == sonuc2["kontrolsuz_tepe_kw"]
    assert sonuc1["onerilen_yontem"] == sonuc2["onerilen_yontem"]
    assert len(sonuc1["yontemler"]) == len(sonuc2["yontemler"])
    for y1, y2 in zip(sonuc1["yontemler"], sonuc2["yontemler"]):
        assert y1["kod"] == y2["kod"]
        assert y1["asgari_kapasite_kw"] == y2["asgari_kapasite_kw"]
        assert y1["tasarruf_orani_yuzde"] == y2["tasarruf_orani_yuzde"]


def test_kapasite_danismani_esitlik_tie_breaking():
    """T├╝m y├Ântemlerde minimum kapasite e┼şit oldu─şunda tek bir y├Ântem (├Âr. FCFS) kazanan ilan edilmemeli."""
    # 1. apartman_gece senaryosunda ger├ğek 0.5 kW ├ğ├Âz├╝n├╝rl├╝kl├╝ hesaplamada 4 y├Ântem de 15.0 kW verir
    sonuc_apt = web_servis.kapasite_danismani_hesapla(
        senaryo_id="apartman_gece",
        gun_secimi="2026-03-10",
        tohum=42,
    )
    assert sonuc_apt["esitlik_var"] is True
    assert sonuc_apt["onerilen_yontem"] == "En d├╝┼ş├╝k kapasite: y├Ântemler e┼şit"
    assert set(sonuc_apt["esit_yontem_kodlari"]) == {"fcfs", "edf", "esit", "mpc"}
    assert sonuc_apt["onerilen_asgari_kapasite_kw"] == 15.0

    # 2. ├ûzel aday kapasite listesinde e┼şitlik durumunda da tekil kazanan se├ğilmemeli
    sonuc_ozel = web_servis.kapasite_danismani_hesapla(
        senaryo_id="apartman_gece",
        gun_secimi="2026-03-10",
        tohum=42,
        aday_kapasiteler=[10.0, 16.8, 30.0],
    )
    assert sonuc_ozel["esitlik_var"] is True
    assert sonuc_ozel["onerilen_yontem"] == "En d├╝┼ş├╝k kapasite: y├Ântemler e┼şit"
    assert len(sonuc_ozel["esit_yontemler"]) == 4


def test_kapasite_danismani_ince_cozunurluk_ve_ozet_metni():
    """Kaba ─▒zgara artefakt─▒ yerine ┬▒0.5 kW ├ğ├Âz├╝n├╝rl├╝k ve nominal trafo ├Âzeti ├╝retilmeli."""
    sonuc = web_servis.kapasite_danismani_hesapla(
        senaryo_id="isyeri_gunduz",
        gun_secimi="2026-03-10",
        tohum=42,
    )
    assert sonuc["arama_cozunurlugu_kw"] == 0.5
    assert sonuc["nominal_trafo_kapasitesi_kw"] == 150.0
    assert sonuc["esitlik_var"] is False
    assert sonuc["onerilen_yontem"] == "EDF (En Erken Termin ├ûncelikli)"
    assert sonuc["onerilen_asgari_kapasite_kw"] == 30.0
    assert "senaryodaki nominal trafo kapasitesi 150.0 kW" in sonuc["kapasite_ozet_metni"]
    assert "30.0 kW" in sonuc["kapasite_ozet_metni"]
    assert sonuc["fiziksel_ulasilamaz_arac_sayisi"] >= 1


def test_beyan_oranlari_2019_h1_yeniden_uretilebilirlik():
    """config/beyan_oranlari.json i├ğindeki kuantil oranlar─▒n─▒n yaln─▒zca 2019 H1 e─şitim b├Âl├╝m├╝nden (7.808 oturum)
    birebir yeniden ├╝retilebildi─şini do─şrular."""
    from sarjdenge import veri_hijyeni

    csv_yolu = PROJE_KOK / "acn_oturumlar_v2.csv"
    json_yolu = PROJE_KOK / "config" / "beyan_oranlari.json"
    assert csv_yolu.exists(), "acn_oturumlar_v2.csv bulunamad─▒!"
    assert json_yolu.exists(), "config/beyan_oranlari.json bulunamad─▒!"

    with open(json_yolu, "r", encoding="utf-8") as f:
        kayitli = json.load(f)

    df = veri_hijyeni.temizle(csv_yolu, sadece_beyanli=True)
    egit_df, val_df, _ = veri_hijyeni.zaman_bol(df, bolme=0.6)

    assert len(egit_df) == 7808
    assert len(val_df) == 5315

    gecerli_sure = (egit_df["beyan_sure_dk"] > 0) & (egit_df["sure_dk"] > 0)
    oran_sure = egit_df.loc[gecerli_sure, "sure_dk"] / egit_df.loc[gecerli_sure, "beyan_sure_dk"]

    gecerli_kwh = (egit_df["kWhRequested"] > 0) & (egit_df["kWhDelivered"] > 0)
    oran_kwh = egit_df.loc[gecerli_kwh, "kWhDelivered"] / egit_df.loc[gecerli_kwh, "kWhRequested"]

    q_sure = np.percentile(oran_sure, [20, 50, 80])
    q_kwh = np.percentile(oran_kwh, [20, 50, 80])

    assert round(float(q_sure[0]), 4) == kayitli["sure_oranlari"]["q20"]
    assert round(float(q_sure[1]), 4) == kayitli["sure_oranlari"]["q50"]
    assert round(float(q_sure[2]), 4) == kayitli["sure_oranlari"]["q80"]

    assert round(float(q_kwh[0]), 4) == kayitli["enerji_oranlari"]["q20"]
    assert round(float(q_kwh[1]), 4) == kayitli["enerji_oranlari"]["q50"]
    assert round(float(q_kwh[2]), 4) == kayitli["enerji_oranlari"]["q80"]

