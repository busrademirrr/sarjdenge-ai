"""ŞarjDenge AI — Kapasite Danışmanı ve Eşit Paylaşım Sınır Durum Testleri.

Bu test modülü aşağıdaki sınır ve güvenlik durumlarını doğrular:
1. Tekillik (tek araç veya sıfır araç durumu)
2. Fiziksel olarak erişilemeyen hedefler (PMAX * süre < talep)
3. Ayrık güç kademeleri ve trafo kapasite sınırının aşılmaması
4. Gece yarısını aşan oturumlar (gece şarjı)
5. Aktif Araçlara Eşit Güç Paylaşımı (esit_paylasim_kurali) dinamikleri
6. Tekrarlanabilirlik (determinizm ve tutarlılık)
7. 2019 H1 verisinden öğrenilen beyan oranları JSON bütünlüğü
"""

import json
import pathlib
import pytest
import numpy as np
import pandas as pd

from sarjdenge import sim, web_servis

PROJE_KOK = pathlib.Path(__file__).resolve().parent.parent


def test_beyan_oranlari_json_yukleme_ve_degerler():
    """config/beyan_oranlari.json dosyasının varlığı ve H1 kuantil değerleri doğrulanır."""
    json_yolu = PROJE_KOK / "config" / "beyan_oranlari.json"
    assert json_yolu.exists(), "config/beyan_oranlari.json bulunamadı!"

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
    """Eşit paylaşım kuralının araçlara eşit güç tahsis ettiğini ve kapasiteyi aşmadığını test eder."""
    t = 0
    # 4 araç, her birinin 20 kWh ihtiyacı var
    kalan = np.array([20.0, 20.0, 20.0, 20.0])
    dep = np.array([20, 20, 20, 20])
    giris = np.array([0, 0, 0, 0])
    cap = 15.0  # 15 kW kapasite

    hiz = web_servis.esit_paylasim_kurali(t, kalan, dep, giris, cap)

    assert len(hiz) == 4
    assert hiz.sum() <= cap + 1e-6, f"Kapasite aşıldı: {hiz.sum()} > {cap}"
    # Ayrık seviyelerden biri olmalı
    for h in hiz:
        assert any(np.isclose(h, sim.SEVIYELER, atol=1e-5)), f"Geçersiz seviye: {h}"
    # Araçlar eşit durumda başladığı için hız farkı en fazla bir ayrık kademe olabilir
    assert hiz.max() - hiz.min() <= sim.SEVIYELER[1] + 1e-5


def test_esit_paylasim_talep_tamamlanmis_arac():
    """Kalan ihtiyacı 0 olan araçlara eşit pay verilmemeli, sadece artan güç fırsatçı verilmeli."""
    t = 5
    kalan = np.array([0.0, 15.0, 15.0])
    dep = np.array([20, 20, 20])
    giris = np.array([0, 0, 0])
    cap = 10.0

    hiz = web_servis.esit_paylasim_kurali(t, kalan, dep, giris, cap)
    assert hiz.sum() <= cap + 1e-6
    # İlk aracın ihtiyacı 0 olduğu için öncelikli eşit payı talep eden 2. ve 3. araç alır
    assert hiz[1] >= hiz[0]
    assert hiz[2] >= hiz[0]


def test_esit_paylasim_bos_kume():
    """Hiç araç olmadığında boş dizi dönmeli."""
    hiz = web_servis.esit_paylasim_kurali(0, np.zeros(0), np.zeros(0), np.zeros(0), 20.0)
    assert len(hiz) == 0


def test_tekillik_tek_arac():
    """Tek bir araç varken kapasite danışmanı veya eşit paylaşım hatasız çalışmalı."""
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
    """Kalış süresi çok kısa olan ve PMAX ile dahi dolamayacak araçların analizi."""
    # 1 saat kalış (4 adım), 50 kWh talep (PMAX 6.656 kW -> azami 6.656 kWh alınabilir)
    giris = np.array([0])
    ayril = np.array([4])
    e_gercek = np.array([50.0])

    sure_saat = (ayril - giris) * sim.DT_H
    fiziksel_ulasilamaz = (e_gercek > sim.PMAX * sure_saat + 1e-6)
    assert fiziksel_ulasilamaz[0] == True

    # Simülasyon yine de güvenli çalışmalı ve kapasiteyi aşmamalı
    teslim = sim.simule(giris, ayril, e_gercek, ayril, e_gercek, 100.0, sim.kural("fcfs"))
    assert teslim[0] <= sim.PMAX * 1.0 + 1e-5


def test_gece_yarisini_asan_oturumlar():
    """Gece yarısını aşan oturumlarda simülasyon ve ayrık seviye sürekliliği."""
    # 22:00'de giriş (adım 88), ertesi gün 06:00'da ayrılış (adım 112)
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
    """Aynı girdilerle çağrılan kapasite danışmanı birebir özdeş sonuçlar üretmelidir."""
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
    """Tüm yöntemlerde minimum kapasite eşit olduğunda tek bir yöntem (ör. FCFS) kazanan ilan edilmemeli, yöntem adları listelenmelidir."""
    # 1. apartman_gece senaryosunda gerçek 0.5 kW çözünürlüklü hesaplamada 4 yöntem de 15.0 kW verir
    sonuc_apt = web_servis.kapasite_danismani_hesapla(
        senaryo_id="apartman_gece",
        gun_secimi="2026-03-10",
        tohum=42,
    )
    assert sonuc_apt["esitlik_var"] is True
    assert "eşit: 15,0 kW" in sonuc_apt["onerilen_yontem"]
    assert set(sonuc_apt["esit_yontem_kodlari"]) == {"fcfs", "edf", "esit", "mpc"}
    assert sonuc_apt["onerilen_asgari_kapasite_kw"] == 15.0

    # 2. Özel aday kapasite listesinde eşitlik durumunda da tekil kazanan seçilmemeli
    sonuc_ozel = web_servis.kapasite_danismani_hesapla(
        senaryo_id="apartman_gece",
        gun_secimi="2026-03-10",
        tohum=42,
        aday_kapasiteler=[10.0, 16.8, 30.0],
    )
    assert sonuc_ozel["esitlik_var"] is True
    assert "eşit:" in sonuc_ozel["onerilen_yontem"]
    assert len(sonuc_ozel["esit_yontemler"]) == 4


def test_kapasite_danismani_ince_cozunurluk_ve_ozet_metni():
    """Kaba ızgara artefaktı yerine ±0.5 kW çözünürlük ve nominal trafo özeti üretilmeli."""
    sonuc = web_servis.kapasite_danismani_hesapla(
        senaryo_id="isyeri_gunduz",
        gun_secimi="2026-03-10",
        tohum=42,
    )
    assert sonuc["arama_cozunurlugu_kw"] == 0.5
    assert sonuc["nominal_trafo_kapasitesi_kw"] == 150.0
    assert sonuc["esitlik_var"] is False
    assert "EDF" in sonuc["onerilen_yontem"]
    assert "27,0 kW" in sonuc["onerilen_yontem"]
    assert sonuc["onerilen_asgari_kapasite_kw"] == 27.0
    assert "Mevcut trafo yeterli" in sonuc["kapasite_ozet_metni"]
    assert "27.0 kW" in sonuc["kapasite_ozet_metni"]
    assert sonuc["fiziksel_ulasilamaz_arac_sayisi"] >= 1
    assert sonuc["fiziksel_imkansiz_arac_sayisi"] == 1
    assert sonuc["karsilanabilir_arac_sayisi"] == 22


def test_kapasite_danismani_monotonluk_ve_tek_kriter():
    """Başarı kriterinin (oran >= 0.95 VE kaçırılan <= 1) ve monotonluk alanlarının doğrulanması."""
    sonuc = web_servis.kapasite_danismani_hesapla(
        senaryo_id="isyeri_gunduz",
        gun_secimi="2026-03-10",
        tohum=42,
    )
    for y in sonuc["yontemler"]:
        assert "monoton_degil" in y
        assert "ilk_kalici_gecis_kw" in y
        assert "arac_ozeti" in y
        assert "kacirilan_arac_sayisi" in y
        if y["basarili"]:
            assert y["kacirilan_arac_sayisi"] <= 1
    assert "ornek_gun" in sonuc
    assert sonuc["ornek_gun"] is True


def test_beyan_oranlari_2019_h1_yeniden_uretilebilirlik():
    """config/beyan_oranlari.json içindeki kuantil oranlarının yalnızca 2019 H1 eğitim bölümünden (7.808 oturum)
    birebir yeniden üretilebildiğini doğrular."""
    from sarjdenge import veri_hijyeni

    csv_yolu = PROJE_KOK / "acn_oturumlar_v2.csv"
    json_yolu = PROJE_KOK / "config" / "beyan_oranlari.json"
    assert csv_yolu.exists(), "acn_oturumlar_v2.csv bulunamadı!"
    assert json_yolu.exists(), "config/beyan_oranlari.json bulunamadı!"

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


def test_cok_gunlu_kapasite_analizi_sentetik():
    """Çok günlü modda sentetik senaryoda 20 gün/tohumun başarıyla değerlendirildiğini ve
    dağılım istatistiklerinin (medyan, p10, p90) eksiksiz hesaplandığını test eder."""
    res = web_servis.kapasite_danismani_hesapla(
        senaryo_id="isyeri_gunduz",
        tohum=42,
        cok_gunlu=True,
    )
    assert "cok_gunlu_analiz" in res
    cg = res["cok_gunlu_analiz"]
    assert cg["toplam_gun"] == 20
    assert cg["hedef_gun_sayisi"] == 20
    assert len(cg["yontemler"]) == 4

    for yo in cg["yontemler"]:
        assert yo["kod"] in ["fcfs", "edf", "esit", "mpc"]
        assert yo["orneklem_sayisi"] > 0
        assert yo["medyan_kw"] is not None
        assert yo["p10_kw"] is not None
        assert yo["p90_kw"] is not None
        assert yo["p10_kw"] <= yo["medyan_kw"] <= yo["p90_kw"]
        assert yo["min_kw"] <= yo["maks_kw"]


def test_cok_gunlu_kapasite_analizi_acn_gercek_ta_0_gun_hatasi_duzeltildi():
    """Dönemler arası test (acn_gercek_ta) senaryosunda doğru CSV dosyasından 20 günün
    toplandığını ve '0 Gün' hatasının çözüldüğünü doğrular."""
    res = web_servis.kapasite_danismani_hesapla(
        senaryo_id="acn_gercek_ta",
        gun_secimi="2019-10-15",
        cok_gunlu=True,
    )
    assert "cok_gunlu_analiz" in res
    cg = res["cok_gunlu_analiz"]
    assert cg["toplam_gun"] == 20
    assert cg["hedef_gun_sayisi"] == 20
    for yo in cg["yontemler"]:
        assert yo["orneklem_sayisi"] > 0
        assert yo["medyan_kw"] is not None


def test_hedef_karsilanamadiginda_gercek_arac_ozeti_korunur():
    """Asgari kapasite bulunamadığında '0/N araç (N kaçırılan)' yerine tepe kapasitedeki
    gerçek araç durumu ve kaçırılan sayısının yansıtıldığını doğrular."""
    # Aday kapasiteyi kasıtlı olarak imkansız düşük bir değere kısıtla
    res = web_servis.kapasite_danismani_hesapla(
        senaryo_id="isyeri_gunduz",
        gun_secimi="2026-03-10",
        tohum=42,
        aday_kapasiteler=[5.0],  # 5 kW ile 23 aracın %95'i tamamlanamaz
    )
    for y in res["yontemler"]:
        # asgari_kapasite_kw None olmalı ama arac_ozeti tepe noktasından gelmeli (0/22 araç olmamalı)
        assert y["asgari_kapasite_kw"] is None
        assert y["arac_ozeti"] != "0/22 araç"
        assert "22 araç" in y["arac_ozeti"]


