"""Çekirdek değişmezleri: kapasite aşılmaz, enerji fazla teslim edilmez, veri şeması doğru."""
import numpy as np
import pandas as pd

from sarjdenge import data, sim, turkiye


def _ornek(n=8, tohum=0):
    rng = np.random.default_rng(tohum)
    giris = np.sort(rng.integers(0, 20, n))
    ayril = giris + rng.integers(8, 30, n)
    e = rng.uniform(3, 20, n)
    inan_ayril = np.maximum(ayril - rng.integers(0, 6, n), giris + 1)
    inan_kwh = e * rng.uniform(1.0, 1.5, n)
    return giris, ayril, e, inan_ayril, inan_kwh


def test_kapasite_asilmaz_ve_enerji_asilmaz():
    giris, ayril, e, ia, ik = _ornek()
    for ad in ["fcfs", "edf", "llf"]:
        teslim = sim.simule(giris, ayril, e, ia, ik, 10.0, sim.kural(ad))  # ihlalde AssertionError
        assert (teslim <= e + 1e-6).all()
    teslim = sim.simule(giris, ayril, e, ia, ik, 10.0, sim.mpc)
    assert (teslim <= e + 1e-6).all()


def test_milp_kapasite_asilmaz():
    giris, ayril, e, ia, ik = _ornek(6, 1)
    teslim = sim.simule(giris, ayril, e, ia, ik, 8.0, sim.mpc_milp)
    assert (teslim <= e + 1e-6).all()


def test_bol_kapasitede_herkes_dolar():
    giris, ayril, e, ia, ik = _ornek(5, 2)
    teslim = sim.simule(giris, ayril, e, ia, ik, 1000.0, sim.kural("fcfs"))
    assert (teslim >= 0.95 * e).all()


def test_turkiye_uretici_sema(tmp_path):
    yol = turkiye.uret(gun=10, yol=str(tmp_path / "t.csv"))
    df = pd.read_csv(yol)
    for kol in ["connectionTime", "disconnectTime", "kWhDelivered", "kWhRequested_ilk",
                "requestedDeparture_ilk", "girdi_gecikme_dk"]:
        assert kol in df.columns
    assert (df.kWhDelivered > 0).all()


def test_veri_yukle_turkiye(tmp_path):
    yol = turkiye.uret(gun=20, yol=str(tmp_path / "t.csv"))
    eski = data.TZ
    data.TZ = "Europe/Istanbul"
    try:
        df = data.yukle(yol)
    finally:
        data.TZ = eski
    assert len(df) > 0 and df.beyan_var.any()


# ── sim.py ek testler ───────────────────────────────────────────────────────

def test_sifir_arac_bos_teslim():
    """Aktif araç yokken simülasyon çökmemeli ve sıfır teslim etmeli."""
    giris  = np.array([5])
    ayril  = np.array([10])
    e      = np.array([2.0])
    teslim = sim.simule(giris, ayril, e, ayril, e, 20.0, sim.kural("fcfs"))
    assert teslim.shape == (1,)


def test_mpc_tekil_arac_dolar():
    """Tek araç, yeterli kapasite ve süre: MPC %95'ini teslim etmeli."""
    giris  = np.array([0])
    ayril  = np.array([8])
    e      = np.array([5.0])
    inan_a = np.array([8])
    inan_k = np.array([5.0])
    teslim = sim.simule(giris, ayril, e, inan_a, inan_k, 10.0, sim.mpc)
    assert teslim[0] >= 0.95 * e[0], f"teslim={teslim[0]:.3f} < 0.95*{e[0]}"


def test_kontrolsuz_tepe_pozitif():
    """Kontrolsüz tepe, en az bir araç aktifken pozitif olmalı."""
    giris = np.array([0, 1, 2])
    ayril = np.array([4, 5, 6])
    e     = np.array([3.0, 4.0, 2.0])
    tepe  = sim.kontrolsuz_tepe(giris, ayril, e)
    assert tepe > 0


def test_edf_teslim_enerji_asilmaz():
    """EDF yöntemi enerji üst sınırını asmamalı."""
    giris, ayril, e, ia, ik = _ornek(10, 99)
    teslim = sim.simule(giris, ayril, e, ia, ik, 15.0, sim.kural("edf"))
    assert (teslim <= e + 1e-6).all()


# ── data.py ek testler ──────────────────────────────────────────────────────

def test_ozellik_sutunlari(tmp_path):
    """ozellikler() doğru sütun adlarını üretmeli."""
    yol = turkiye.uret(gun=15, yol=str(tmp_path / "t.csv"))
    eski = data.TZ
    data.TZ = "Europe/Istanbul"
    try:
        df = data.yukle(yol)
        X  = data.ozellikler(df)
    finally:
        data.TZ = eski
    for kol in ["saat", "haftagunu", "saha", "beyan_sure_dk", "beyan_kwh", "gecmis_n"]:
        assert kol in X.columns, f"eksik sütun: {kol}"


def test_veri_filtreleme(tmp_path):
    """Kısa oturumlar (< 30 dk) ve sıfır kWh oturumlar filtrelenmeli."""
    yol = turkiye.uret(gun=10, yol=str(tmp_path / "f.csv"))
    eski = data.TZ
    data.TZ = "Europe/Istanbul"
    try:
        df = data.yukle(yol)
    finally:
        data.TZ = eski
    assert (df.sure_dk >= 30).all()
    assert (df.kWhDelivered >= 0.5).all()


# ── turkiye.py ek testler ───────────────────────────────────────────────────

def test_turkiye_tarih_araligi(tmp_path):
    """Üretilen oturumlar belirtilen gün sayısı kadar tarihe yayılmalı."""
    yol = turkiye.uret(gun=7, yol=str(tmp_path / "tk.csv"))
    df  = pd.read_csv(yol)
    df["connectionTime"] = pd.to_datetime(df["connectionTime"], format="ISO8601", utc=True)
    assert len(df) > 0
    gun_farki = (df.connectionTime.max() - df.connectionTime.min()).days
    assert gun_farki >= 5, f"gün farkı çok az: {gun_farki}"


def test_turkiye_beyan_giris_sonrasi(tmp_path):
    """Beyan edilen ayrılış, bağlantıdan sonra olmalı."""
    yol = turkiye.uret(gun=10, yol=str(tmp_path / "b.csv"))
    df  = pd.read_csv(yol)
    df["connectionTime"]         = pd.to_datetime(df.connectionTime, format="ISO8601", utc=True)
    df["requestedDeparture_ilk"] = pd.to_datetime(df.requestedDeparture_ilk, format="ISO8601", utc=True)
    gecerli = df.dropna(subset=["requestedDeparture_ilk"])
    assert (gecerli.requestedDeparture_ilk > gecerli.connectionTime).all()


# ── urun.py ek testler ──────────────────────────────────────────────────────

def test_urun_json_semasi(tmp_path):
    """urun.calistir() çıktısında zorunlu anahtarlar bulunmalı."""
    from sarjdenge import urun
    csv_yol     = turkiye.uret(gun=30, yol=str(tmp_path / "u.csv"))
    eski_tz     = data.TZ
    eski_sev    = sim.SEVIYELER.copy()
    eski_pmax   = sim.PMAX
    try:
        urun.kur(soket=20)   # sim.SEVIYELER ve data.TZ'yi Türkiye değerlerine ayarla
        ozet = urun.calistir(csv_yol, soket=20,
                             kapasiteler=(80, 120, 160),
                             detay_kap=120, min_arac=3)
    finally:
        data.TZ       = eski_tz
        sim.SEVIYELER = eski_sev
        sim.PMAX      = eski_pmax
    for anahtar in ["etiket", "soket", "parametreler", "tarama", "yeterli", "detay"]:
        assert anahtar in ozet, f"eksik anahtar: {anahtar}"
    assert "SENTETİK" in ozet["etiket"].upper()


def test_urun_yeterli_kapasite_anahtarlari(tmp_path):
    """yeterli sözlüğü beklenen yöntem adlarını içermeli."""
    from sarjdenge import urun
    csv_yol     = turkiye.uret(gun=30, yol=str(tmp_path / "y.csv"))
    eski_tz     = data.TZ
    eski_sev    = sim.SEVIYELER.copy()
    eski_pmax   = sim.PMAX
    try:
        urun.kur(soket=20)   # sim.SEVIYELER ve data.TZ'yi Türkiye değerlerine ayarla
        ozet = urun.calistir(csv_yol, soket=20,
                             kapasiteler=(80, 120, 160),
                             detay_kap=120, min_arac=3)
    finally:
        data.TZ       = eski_tz
        sim.SEVIYELER = eski_sev
        sim.PMAX      = eski_pmax
    for ad in ["statik", "fcfs_beyan", "mpc_beyan", "milp_beyan", "sarjdenge"]:
        assert ad in ozet["yeterli"], f"eksik yöntem: {ad}"
