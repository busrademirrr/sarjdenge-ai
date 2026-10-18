"""Ürün katmanı: Türkiye apartman senaryosunda kapasite karar analizi + demo verisi (JSON).

Çıktılar:
  - kapasite taraması: her kapasite (kW) için yöntem başına zamanında hedefe ulaşan araç oranı
  - "yeterli kapasite": %95 araç hedefine ulaşan en küçük kapasite, yöntem başına
  - tek gün ayrıntısı: araç araç güç planı (ŞarjDenge vs statik paylaşım)
UYARI: Türkiye verisi etiketli sentetiktir (turkiye.py). Sonuçlar senaryo sonucudur.
"""
import argparse
import json

import numpy as np
import pandas as pd

from . import data, deney, sim, tahmin, turkiye

V = 0.23                                   # kV (tek faz 230 V)
SEVIYE_A = np.array([0, 8, 16, 24, 32])    # akım seviyeleri (A)
HEDEF = 0.95                               # "yeterli" sayılması için araç oranı


def kur(soket):
    sim.SEVIYELER = SEVIYE_A * V
    sim.PMAX = float(sim.SEVIYELER[-1])
    data.TZ = "Europe/Istanbul"
    return sim.PMAX


def statik(soket):
    """Statik güç paylaşımı: kapasite soket sayısına eşit bölünür; araç varsa o payı alır."""
    def f(t, kalan, dep, giris, cap):
        pay = sim._taban_seviye(min(sim.PMAX, cap / soket))
        hiz = np.where(kalan > sim.EPS, pay, 0.0)
        return hiz
    return f


def simule_kayit(giris, ayril, e, inan_ayril, inan_kwh, cap, yontem, adim_n):
    n = len(giris)
    teslim = np.zeros(n)
    guc = np.zeros((adim_n, n))
    for t in range(min(int(ayril.max()) + 1, adim_n)):
        aktif = np.where((giris <= t) & (t < ayril) & (teslim < e - sim.EPS))[0]
        if aktif.size == 0:
            continue
        kalan = inan_kwh[aktif] - teslim[aktif]
        dep = np.maximum(inan_ayril[aktif], t + 1)
        hiz = yontem(t, kalan, dep, giris[aktif], cap)
        assert hiz.sum() <= cap + 1e-6, "kapasite ihlali"
        guc[t, aktif] = hiz
        teslim[aktif] += np.minimum(hiz * sim.DT_H, e[aktif] - teslim[aktif])
    return teslim, guc


def hazirla(csv, bolme=0.6):
    df = data.yukle(csv)
    X = data.ozellikler(df)
    gunler = np.array(sorted(df.gun.unique()))
    kesim = gunler[int(len(gunler) * bolme)]
    egit = df.gun < kesim
    test = (df.gun >= kesim) & df.beyan_var
    tah = tahmin.Tahminci().egit(X[egit], df.sure_dk[egit], df.kWhDelivered[egit])
    dt = df[test].copy()
    T = tah.tahmin(X[test])
    return dt, T, deney.inanilan(dt, T), (tah, X, df, egit)


def gun_verisi(dt, kaynaklar, idx_gun, gun):
    idx = dt.index[dt.gun == gun]
    gd = dt.loc[idx]
    pos = dt.index.get_indexer(idx)
    t0 = pd.Timestamp(gun).tz_localize(data.TZ).tz_convert("UTC")
    giris = np.ceil(deney.adimlar(gd.connectionTime, t0)).astype(int)
    ayril = np.floor(deney.adimlar(gd.disconnectTime, t0)).astype(int)
    gec = ayril > giris
    return idx[gec], pos[gec], t0, giris[gec], ayril[gec], gd.kWhDelivered.to_numpy()[gec]


def inan(kaynaklar, kaynak, idx, pos, t0, giris):
    ts, kwh = kaynaklar[kaynak]
    dep = np.maximum(np.floor(deney.adimlar(ts.loc[idx].reset_index(drop=True), t0)), giris + 1).astype(int)
    return dep, np.asarray(kwh)[pos]


def calistir(csv, soket=20, kapasiteler=(5, 6, 8, 10, 12, 15, 20, 40, 80), detay_kap=8,
             min_arac=8, log=print):
    kur(soket)
    dt, T, kaynaklar, _ = hazirla(csv)
    yont = {
        "statik": (statik(soket), "beyan"),
        "fcfs_beyan": (sim.kural("fcfs"), "beyan"),
        "mpc_beyan": (sim.mpc, "beyan"),
        "milp_beyan": (sim.mpc_milp, "beyan"),
        # Ürün planlayıcısı: tamamlama odaklı MILP + belirsizlik tahmini (enerji-LP FCFS'in gerisinde kaldı)
        "sarjdenge": (sim.mpc_milp, "tahmin_guvenli"),
    }
    gunler = sorted(dt.gun.unique())
    satir = []
    for gun in gunler:
        idx, pos, t0, giris, ayril, e = gun_verisi(dt, kaynaklar, None, gun)
        if len(idx) < min_arac:
            continue
        for cap in kapasiteler:
            for ad, (fn, kaynak) in yont.items():
                dep, kwh = inan(kaynaklar, kaynak, idx, pos, t0, giris)
                teslim = sim.simule(giris, ayril, e, dep, kwh, float(cap), fn)
                ok = teslim / e >= 0.95
                satir.append(dict(gun=gun, cap=cap, yontem=ad, n=len(e), ok=ok.mean(),
                                  teslim_orani=teslim.sum() / e.sum()))
    res = pd.DataFrame(satir)
    tab = res.groupby(["cap", "yontem"]).agg(ok=("ok", "mean"), teslim=("teslim_orani", "mean"),
                                             gun=("gun", "nunique")).reset_index()
    log(tab.pivot(index="cap", columns="yontem", values="ok").round(3).to_string())

    yeterli = {}
    for ad in yont:
        g = tab[(tab.yontem == ad) & (tab.ok >= HEDEF)].sort_values("cap")
        yeterli[ad] = float(g.cap.iloc[0]) if len(g) else None
    log("yeterli kapasite (kW):", yeterli)

    fark = []
    for cap, g in res.groupby("cap"):
        piv = g.pivot_table(index="gun", columns="yontem", values="ok")
        for a, b in [("sarjdenge", "mpc_beyan"), ("sarjdenge", "statik"), ("sarjdenge", "fcfs_beyan"),
                         ("sarjdenge", "milp_beyan"), ("milp_beyan", "fcfs_beyan")]:
            m, lo, hi = deney.bootstrap_fark(piv[a], piv[b])
            fark.append(dict(cap=cap, karsilastirma=f"{a} - {b}", fark=m, alt=lo, ust=hi))
    fark = pd.DataFrame(fark)

    # tek gün ayrıntısı: araç sayısı en çok 14'e yakın bir test günü
    en = {g: len(dt.index[dt.gun == g]) for g in gunler}
    gun = min(gunler, key=lambda g: abs(en[g] - 13))
    idx, pos, t0, giris, ayril, e = gun_verisi(dt, kaynaklar, None, gun)
    adim_n = int(ayril.max()) + 2
    ayrinti = {}
    for ad in ["statik", "sarjdenge"]:
        fn, kaynak = yont[ad]
        dep, kwh = inan(kaynaklar, kaynak, idx, pos, t0, giris)
        teslim, guc = simule_kayit(giris, ayril, e, dep, kwh, float(detay_kap), fn, adim_n)
        ayrinti[ad] = dict(teslim=teslim.round(2).tolist(), guc=guc.round(3).tolist())
    gd = dt.loc[idx]
    dep_g, kwh_g = inan(kaynaklar, "tahmin_guvenli", idx, pos, t0, giris)
    dep_b, kwh_b = inan(kaynaklar, "beyan", idx, pos, t0, giris)
    araclar = []
    for i in range(len(idx)):
        araclar.append(dict(
            giris=int(giris[i]), ayril=int(ayril[i]), kwh=round(float(e[i]), 2),
            beyan_ayril=int(dep_b[i]), beyan_kwh=round(float(kwh_b[i]), 2),
            tahmin_ayril=int(dep_g[i]), tahmin_kwh=round(float(kwh_g[i]), 2)))
    detay = dict(gun=str(pd.Timestamp(gun).date()), kap=float(detay_kap), adim_n=adim_n,
                 t0_saat_yerel=0, araclar=araclar, **ayrinti)
    ozet = dict(
        etiket="SENTETİK TÜRKİYE SENARYOSU (ölçüm değil)", soket=soket,
        parametreler={k: (v if not isinstance(v, (np.floating,)) else float(v))
                      for k, v in turkiye.PARAMETRELER.items()},
        seviye_kw=[round(float(x), 3) for x in sim.SEVIYELER],
        hedef=HEDEF, test_gun=int(len(gunler)),
        tarama=tab.round(4).to_dict("records"), yeterli=yeterli,
        fark=fark.round(4).to_dict("records"), detay=detay)
    return ozet


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="turkiye_oturumlar.csv")
    ap.add_argument("--uret", action="store_true", help="önce sentetik Türkiye verisini üret")
    ap.add_argument("--gun", type=int, default=150)
    ap.add_argument("--soket", type=int, default=20)
    ap.add_argument("--detay-kap", type=float, default=8)
    ap.add_argument("--cikti", default="demo_veri.json")
    a = ap.parse_args(argv)
    if a.uret:
        turkiye.uret(a.gun, yol=a.csv, p=dict(soket=a.soket))
    ozet = calistir(a.csv, a.soket, detay_kap=a.detay_kap)
    with open(a.cikti, "w", encoding="utf-8") as fh:
        json.dump(ozet, fh, ensure_ascii=False)
    print(a.cikti, "yazıldı")


if __name__ == "__main__":
    main()
