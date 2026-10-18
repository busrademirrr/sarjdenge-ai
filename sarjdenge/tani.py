"""POST-HOC TEŞHİS (hipotez testi DEĞİL). Neden tahmin doğruluğu hizmet düzeyine yansımıyor?

Önceden yazılmış deney (deney.py) başarısız oldu; bu betik nedeni anlamak için bilgi kaynaklarını ayırır:
  beyan | tahmin_guvenli | oracle (gerçek ayrılış + gerçek kWh: üst sınır)
  | sure_tahmin_kwh_beyan | sure_beyan_kwh_tahmin (hangi bileşen zarar veriyor?)
Sonuçlar keşif amaçlıdır; yeni bir iddia için taze veriyle yeni, önceden yazılmış kural gerekir.
deney.py'ye dokunmaz, onun işlevlerini kullanır.
"""
import argparse

import numpy as np
import pandas as pd

from . import data, deney, sim, tahmin


def calistir(csv, bolme=0.6, gun_siniri=40, kapasiteler=(0.5, 0.7), sahalar=("0001", "0002"),
             algoritmalar=("edf", "mpc"), min_arac=8, log=print):
    df = data.yukle(csv)
    df = df[df.siteID.isin(sahalar)].reset_index(drop=True)
    X = data.ozellikler(df)
    gunler = np.array(sorted(df.gun.unique()))
    kesim = gunler[int(len(gunler) * bolme)]
    egit = df.gun < kesim
    test = (df.gun >= kesim) & df.beyan_var
    tah = tahmin.Tahminci().egit(X[egit], df.sure_dk[egit], df.kWhDelivered[egit])
    dt = df[test].copy()
    T = tah.tahmin(X[test])
    k = deney.inanilan(dt, T)
    k["oracle"] = (dt.disconnectTime, dt.kWhDelivered.to_numpy())
    k["sure_tahmin_kwh_beyan"] = (k["tahmin_guvenli"][0], k["beyan"][1])
    k["sure_beyan_kwh_tahmin"] = (k["beyan"][0], k["tahmin_guvenli"][1])
    kaynak_adlari = ["beyan", "tahmin_guvenli", "oracle", "sure_tahmin_kwh_beyan", "sure_beyan_kwh_tahmin"]
    test_gunleri = sorted(dt.gun.unique())[:gun_siniri]
    satir = []
    for site, ds in dt.groupby("siteID"):
        for gun in test_gunleri:
            idx = ds.index[ds.gun == gun]
            if len(idx) < min_arac:
                continue
            gd = dt.loc[idx]
            pos = dt.index.get_indexer(idx)
            t0 = pd.Timestamp(gun).tz_localize(data.TZ).tz_convert("UTC")
            giris = np.ceil(deney.adimlar(gd.connectionTime, t0)).astype(int)
            ayril = np.floor(deney.adimlar(gd.disconnectTime, t0)).astype(int)
            gec = ayril > giris
            if gec.sum() < min_arac:
                continue
            giris, ayril = giris[gec], ayril[gec]
            e = gd.kWhDelivered.to_numpy()[gec]
            tepe = sim.kontrolsuz_tepe(giris, ayril, e)
            for f in kapasiteler:
                cap = max(f * tepe, sim.SEVIYELER[1])
                for alg in algoritmalar:
                    yont = sim.mpc if alg == "mpc" else sim.kural(alg)
                    for ks in kaynak_adlari:
                        ts, kwh = k[ks]
                        dep = np.maximum(np.floor(deney.adimlar(ts.loc[idx][gec].reset_index(drop=True), t0)),
                                         giris + 1).astype(int)
                        teslim = sim.simule(giris, ayril, e, dep, np.asarray(kwh)[pos][gec], cap, yont)
                        satir.append(dict(saha=site, gun=gun, f=f, alg=alg, kaynak=ks,
                                          ok=float((teslim / e >= 0.95).mean())))
        log(f"saha {site} bitti")
    res = pd.DataFrame(satir)
    tab = res.groupby(["f", "alg", "kaynak"]).ok.mean().unstack("kaynak")[kaynak_adlari].round(3)
    log(tab.to_string())
    fark = []
    for (f, alg), g in res.groupby(["f", "alg"]):
        piv = g.pivot_table(index=["saha", "gun"], columns="kaynak", values="ok")
        for ks in kaynak_adlari[1:]:
            m, lo, hi = deney.bootstrap_fark(piv[ks], piv["beyan"])
            fark.append(dict(f=f, alg=alg, karsilastirma=f"{ks} - beyan", fark=m, alt=lo, ust=hi))
    fark = pd.DataFrame(fark).round(3)
    log(fark.to_string(index=False))
    return res, tab, fark


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="acn_oturumlar_v2.csv")
    ap.add_argument("--gun", type=int, default=40)
    ap.add_argument("--kapasite", default="0.5,0.7")
    ap.add_argument("--cikti", default="tani_sonuclari.csv")
    a = ap.parse_args(argv)
    res, tab, fark = calistir(a.csv, gun_siniri=a.gun, kapasiteler=tuple(float(x) for x in a.kapasite.split(",")))
    res.to_csv(a.cikti, index=False)
    print(f"{a.cikti} yazıldı (POST-HOC teşhis; hipotez testi değil).")


if __name__ == "__main__":
    main()
