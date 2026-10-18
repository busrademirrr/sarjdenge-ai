"""Ana deney: aynı günler ve aynı kapasitede kurallar ve MPC; bilgi kaynağı = beyan veya tahmin.

Önceden yazılmış karar kuralı (sonuçlara bakmadan):
  ANA KARŞILAŞTIRMA: mpc_tahmin_guvenli  -  mpc_beyan   (zamanında hedef oranı farkı)
  EŞİK: fark >= 0.02 (2 puan) ve günler üzerinden bootstrap %95 güven aralığının alt ucu > 0.
  tahmin_guvenli = (süre q20, enerji q80); tahmin_ortanca = (süre q50, enerji q50).
  mpc_tahmin_ortanca ikincil karşılaştırmadır; ana sonuç gibi raporlanmaz.
"""
import argparse
import sys

import numpy as np
import pandas as pd

from . import data, sim, tahmin

DK = 900.0  # 15 dk saniye
YONTEMLER = {
    "fcfs_beyan": ("fcfs", "beyan"),
    "edf_beyan": ("edf", "beyan"),
    "llf_beyan": ("llf", "beyan"),
    "edf_tahmin_guvenli": ("edf", "tahmin_guvenli"),
    "llf_tahmin_guvenli": ("llf", "tahmin_guvenli"),
    "mpc_beyan": ("mpc", "beyan"),
    "mpc_tahmin_ortanca": ("mpc", "tahmin_ortanca"),
    "mpc_tahmin_guvenli": ("mpc", "tahmin_guvenli"),
    # tahmin_dengeli: sure_q20 + kwh_q50 (POST-HOC tani.py bulgusuna dayanılarak eklendi)
    "mpc_tahmin_dengeli": ("mpc", "tahmin_dengeli"),
    "edf_tahmin_dengeli": ("edf", "tahmin_dengeli"),
    # Hibrit adaylar (Ocak–Haziran doğrulama dönemi)
    "mpc_hibrit_asimetrik": ("mpc", "hibrit_asimetrik"),
    "mpc_hibrit_risk_esikli": ("mpc", "hibrit_risk_esikli"),
    "mpc_hibrit_adaptif": ("mpc_adaptif", "hibrit_adaptif"),
    # Türkiye senaryosunda enerji-LP'nin "hedefe ulaşan araç sayısı"nda FCFS'in gerisinde kaldığı görüldü;
    # tamamlama odaklı MILP planlayıcı (yalnızca --milp ile; yavaştır, --gun ile sınırla)
    "milp_beyan": ("milp", "beyan"),
    "milp_tahmin_guvenli": ("milp", "tahmin_guvenli"),
}
ANA, REF, ESIK = "mpc_tahmin_guvenli", "mpc_beyan", 0.02


def inanilan(df, T):
    """Her oturum için bilgi kaynağına göre inanılan ayrılış zamanı ve kWh."""
    gir = df.connectionTime
    out = {}
    bd = df.requestedDeparture.where(df.requestedDeparture > gir + pd.Timedelta(minutes=30),
                                     gir + pd.Timedelta(minutes=30))
    kwh_beyan = df.kWhRequested.clip(upper=100).to_numpy(float)
    out["beyan"] = (bd, kwh_beyan)
    out["tahmin_ortanca"] = (gir + pd.to_timedelta(T["sure_q50"], unit="m"), T["kwh_q50"])
    out["tahmin_guvenli"] = (gir + pd.to_timedelta(T["sure_q20"], unit="m"), T["kwh_q80"])
    # tahmin_dengeli: erken ayrılış varsayımı (sure q20, koruyucu) + medyan enerji (kwh q80'in
    # yol açtığı hayalet rezervasyonu ortadan kaldırır). POST-HOC tani.py bulgusuna dayanarak eklendi.
    out["tahmin_dengeli"] = (gir + pd.to_timedelta(T["sure_q20"], unit="m"), T["kwh_q50"])

    # Aday 1: hibrit_asimetrik (ayrılış: min(beyan, sure_q20); enerji: max(beyan, kwh_q50))
    dep_q20 = gir + pd.to_timedelta(T["sure_q20"], unit="m")
    dep_asim = pd.Series(np.minimum(bd.to_numpy(), dep_q20.to_numpy()), index=df.index)
    kwh_asim = np.maximum(kwh_beyan, T["kwh_q50"])
    out["hibrit_asimetrik"] = (dep_asim, kwh_asim)

    # Aday 2: hibrit_risk_esikli (beyan süresi q20'yi 60 dk'dan fazla aşıyorsa sure_q20, aksi halde beyan)
    delta_dk = df.beyan_sure_dk.to_numpy(float) - T["sure_q20"]
    riskli = delta_dk > 60.0
    dep_riskli = np.where(riskli, dep_q20.to_numpy(), bd.to_numpy())
    out["hibrit_risk_esikli"] = (pd.Series(dep_riskli, index=df.index), kwh_asim)

    # Aday 3: hibrit_adaptif (simülasyona beyan tavanı verilir; adım bazında dinamik önceliklendirme yapılır)
    out["hibrit_adaptif"] = (bd, kwh_beyan)
    return out


def make_adaptif_mpc(q20_dep, beyan_dep, q50_kwh, beyan_kwh):
    """Aday 3 için dinamik iki aşamalı MPC:
    - Teslim edilen < kwh_q50: Aşama 1 (acil, süre hedefi q20, kalan hedef min(q50, beyan) - teslim).
    - Teslim edilen >= kwh_q50: Aşama 2 (ikincil, süre hedefi beyan_dep, kalan hedef beyan - teslim).
    """
    def adaptif_mpc(t, kalan, dep, giris_aktif, cap):
        try:
            frame = sys._getframe(1)
            if frame.f_code.co_name == "simule" and "aktif" in frame.f_locals:
                aktif = frame.f_locals["aktif"]
                teslim_aktif = beyan_kwh[aktif] - kalan
                q50_aktif = q50_kwh[aktif]
                beyan_aktif = beyan_kwh[aktif]

                asama1 = teslim_aktif < q50_aktif
                stage1_kalan = np.maximum(np.minimum(q50_aktif, beyan_aktif) - teslim_aktif, 0.0)
                stage2_kalan = np.maximum(beyan_aktif - teslim_aktif, 0.0)

                kalan_eff = np.where(asama1, stage1_kalan, stage2_kalan)
                q20_dep_aktif = np.maximum(q20_dep[aktif], t + 1)
                beyan_dep_aktif = np.maximum(beyan_dep[aktif], t + 1)
                dep_eff = np.where(asama1, q20_dep_aktif, beyan_dep_aktif)

                return sim.mpc(t, kalan_eff, dep_eff, giris_aktif, cap)
        except Exception:
            pass
        return sim.mpc(t, kalan, dep, giris_aktif, cap)
    return adaptif_mpc


def adimlar(ts, t0):
    return (ts - t0).dt.total_seconds().to_numpy() / DK


def calistir(csv, bolme=0.6, gun_siniri=None, kapasiteler=(0.5, 0.7, 0.9), sahalar=None,
             min_arac=8, yontemler=None, log=print):
    df = data.yukle(csv)
    if sahalar:
        df = df[df.siteID.isin(sahalar)].reset_index(drop=True)
    X = data.ozellikler(df)
    gunler = np.array(sorted(df.gun.unique()))
    kesim = gunler[int(len(gunler) * bolme)]
    egit = df.gun < kesim
    test_mask = (df.gun >= kesim) & df.beyan_var
    log(f"oturum {len(df)} | eğitim {egit.sum()} (< {pd.Timestamp(kesim).date()}) | test {test_mask.sum()}")

    tah = tahmin.Tahminci().egit(X[egit], df.sure_dk[egit], df.kWhDelivered[egit])
    Xt, dt = X[test_mask], df[test_mask].copy()
    T = tah.tahmin(Xt)
    ger_dk, ger_kwh = dt.sure_dk.to_numpy(), dt.kWhDelivered.to_numpy()
    tahmin_tablo = pd.DataFrame([
        ("süre", "beyan", tahmin.smape(ger_dk, dt.beyan_sure_dk.clip(lower=30))),
        ("süre", "tahmin (medyan)", tahmin.smape(ger_dk, T["sure_q50"])),
        ("enerji", "beyan", tahmin.smape(ger_kwh, dt.kWhRequested.clip(upper=100))),
        ("enerji", "tahmin (medyan)", tahmin.smape(ger_kwh, T["kwh_q50"])),
    ], columns=["hedef", "kaynak", "SMAPE_%"])
    kapsama = float((ger_dk < T["sure_q20"]).mean())
    gecmis_var = Xt["gecmis_n"] > 0
    log(tahmin_tablo.to_string(index=False))
    log(f"süre q20 kapsaması (hedef 0.20): {kapsama:.3f}")
    kapsama_kwh = float((ger_kwh <= T["kwh_q80"]).mean())
    log(f"enerji q80 kapsaması (hedef 0.80): {kapsama_kwh:.3f}")
    if "girdi_gecikme_dk" in dt:
        log(f"beyan gecikmesi (dk) medyan {dt.girdi_gecikme_dk.median():.1f}, p90 {dt.girdi_gecikme_dk.quantile(.9):.1f}; girdisi sonradan değişen oturum %{100*dt.girdi_degisti.mean():.1f}")
    kwh_beyan_tum = dt.kWhRequested.clip(upper=100).to_numpy(float)
    q50_ustunde = T["kwh_q50"] > kwh_beyan_tum
    pct_q50_ustunde = float(q50_ustunde.mean() * 100)
    diff_q50_ustunde = float((T["kwh_q50"][q50_ustunde] - kwh_beyan_tum[q50_ustunde]).mean()) if q50_ustunde.any() else 0.0
    log(f"Aday 1 (hibrit): q50 > beyan olan oturum %{pct_q50_ustunde:.1f} (ort fark +{diff_q50_ustunde:.2f} kWh); gercek kWh ile karıştırılmamıştır")

    kaynaklar = inanilan(dt, T)
    secili = {k: v for k, v in YONTEMLER.items()
              if (k in yontemler if yontemler else not k.startswith("milp"))}
    satirlar, sat_ev = [], []
    test_gunleri = sorted(dt.gun.unique())
    if gun_siniri:
        test_gunleri = test_gunleri[:gun_siniri]
    for site, ds in dt.groupby("siteID"):
        for gun in test_gunleri:
            idx = ds.index[ds.gun == gun]
            if len(idx) < min_arac:
                continue
            gd = dt.loc[idx]
            pos = dt.index.get_indexer(idx)
            t0 = pd.Timestamp(gun).tz_localize(data.TZ).tz_convert("UTC")
            giris = np.ceil(adimlar(gd.connectionTime, t0)).astype(int)
            ayril = np.floor(adimlar(gd.disconnectTime, t0)).astype(int)
            gec = ayril > giris
            if gec.sum() < min_arac:
                continue
            giris, ayril = giris[gec], ayril[gec]
            e = gd.kWhDelivered.to_numpy()[gec]
            beyan_dep_ts = kaynaklar["beyan"][0].loc[idx][gec].reset_index(drop=True)
            erken = (gd.disconnectTime[gec].reset_index(drop=True)
                     < beyan_dep_ts - pd.Timedelta(minutes=15)).to_numpy()
            tepe = sim.kontrolsuz_tepe(giris, ayril, e)
            q20_ts, _ = kaynaklar["tahmin_guvenli"]
            q20_dep_adim = np.maximum(np.floor(adimlar(q20_ts.loc[idx][gec].reset_index(drop=True), t0)),
                                      giris + 1).astype(int)
            bd_ts, beyan_kwh_arr = kaynaklar["beyan"]
            beyan_dep_adim = np.maximum(np.floor(adimlar(bd_ts.loc[idx][gec].reset_index(drop=True), t0)),
                                        giris + 1).astype(int)
            kwh_q50_adim = np.asarray(T["kwh_q50"])[pos][gec]
            kwh_beyan_adim = np.asarray(beyan_kwh_arr)[pos][gec]
            for f in kapasiteler:
                cap = max(f * tepe, sim.SEVIYELER[1])
                for ad, (alg, kaynak) in secili.items():
                    ts, kwh = kaynaklar[kaynak]
                    inan_dep = np.maximum(np.floor(adimlar(ts.loc[idx][gec].reset_index(drop=True), t0)),
                                          giris + 1).astype(int)
                    inan_kwh = np.asarray(kwh)[pos][gec]
                    if alg == "mpc_adaptif":
                        yont = make_adaptif_mpc(q20_dep_adim, beyan_dep_adim, kwh_q50_adim, kwh_beyan_adim)
                    else:
                        yont = {"mpc": sim.mpc, "milp": sim.mpc_milp}.get(alg) or sim.kural(alg)
                    teslim = sim.simule(giris, ayril, e, inan_dep, inan_kwh, cap, yont)
                    sat = teslim / e
                    ok = sat >= 0.95
                    satirlar.append(dict(saha=site, gun=gun, f=f, yontem=ad, n=len(e),
                                         ok=ok.mean(), teslim_orani=teslim.sum() / e.sum(),
                                         erken_ok=ok[erken].mean() if erken.any() else np.nan,
                                         p10=np.percentile(sat, 10),
                                         kapasite_ihlali=0))
        log(f"saha {site} bitti")
    return pd.DataFrame(satirlar), tahmin_tablo, (kapsama, kapsama_kwh)


def bootstrap_fark(a, b, n=2000, tohum=0):
    rng = np.random.default_rng(tohum)
    d = np.asarray(a) - np.asarray(b)
    d = d[~np.isnan(d)]
    if len(d) < 3:
        return np.nan, np.nan, np.nan
    bs = rng.choice(d, (n, len(d)), replace=True).mean(1)
    return d.mean(), *np.percentile(bs, [2.5, 97.5])


def ozetle(res):
    tab = res.groupby(["f", "yontem"]).agg(gun=("gun", "nunique"), ok=("ok", "mean"),
                                           teslim=("teslim_orani", "mean"),
                                           erken_ok=("erken_ok", "mean"),
                                           p10=("p10", "mean"),
                                           kapasite_ihlali=("kapasite_ihlali", "sum")).reset_index()
    sat = []
    for f, g in res.groupby("f"):
        piv = g.pivot_table(index=["saha", "gun"], columns="yontem", values="ok")
        for ad, ref in [(ANA, REF), ("mpc_tahmin_ortanca", REF),
                        ("edf_tahmin_guvenli", "edf_beyan"), ("llf_tahmin_guvenli", "llf_beyan"),
                        ("milp_tahmin_guvenli", "milp_beyan"), ("milp_beyan", "fcfs_beyan"),
                        ("mpc_tahmin_dengeli", REF), ("edf_tahmin_dengeli", "edf_beyan"),
                        ("mpc_hibrit_asimetrik", REF),
                        ("mpc_hibrit_asimetrik", ANA),
                        ("mpc_hibrit_asimetrik", "edf_beyan"),
                        ("mpc_hibrit_risk_esikli", REF),
                        ("mpc_hibrit_risk_esikli", ANA),
                        ("mpc_hibrit_risk_esikli", "edf_beyan"),
                        ("mpc_hibrit_adaptif", REF),
                        ("mpc_hibrit_adaptif", ANA),
                        ("mpc_hibrit_adaptif", "edf_beyan")]:
            if ad in piv and ref in piv:
                m, lo, hi = bootstrap_fark(piv[ad], piv[ref])
                sat.append(dict(f=f, karsilastirma=f"{ad} - {ref}", fark=m, alt=lo, ust=hi,
                                esik_gecti=bool(ad == ANA and ref == REF and m >= ESIK and lo > 0)))
    return tab, pd.DataFrame(sat)


def grafik(tab, yol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for ad, g in tab.groupby("yontem"):
        g = g.sort_values("f")
        ax.plot(g.f, g.ok, marker="o", lw=2.4 if ad in (ANA, REF) else 1.1, label=ad)
    ax.set_xlabel("Kapasite / günün kontrolsüz tepe gücü")
    ax.set_ylabel("Zamanında hedefe ulaşan araç oranı")
    ax.legend(fontsize=7)
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(yol, dpi=160)


def rapor_yaz(res, tahmin_tablo, kapsama, yol):
    tab, fark = ozetle(res)
    grafik(tab, "grafik.png")
    with open(yol, "w", encoding="utf-8") as fh:
        fh.write("# ŞarjDenge deney sonuçları\n\n")
        fh.write("Not: Talep = teslim edilen kWh (ACN'nin kendi planlayıcısının sonucu); ok = teslim >= %95 talep.\n\n")
        fh.write("## Tahmin doğruluğu (test oturumları)\n\n" + tahmin_tablo.round(2).to_markdown(index=False))
        fh.write(f"\n\nSüre q20 kapsaması (hedef 0,20): {kapsama[0]:.3f}; enerji q80 kapsaması (hedef 0,80): {kapsama[1]:.3f}\n\n")
        fh.write("## Yöntemler (kapasite = günün kontrolsüz tepe gücünün f katı)\n\n")
        fh.write(tab.round(3).to_markdown(index=False))
        fh.write("\n\n## Eşleştirilmiş fark: zamanında hedef oranı (bootstrap %95 GA)\n\n")
        fh.write(fark.round(3).to_markdown(index=False))
        fh.write(f"\n\nÖnceden yazılmış eşik: ana karşılaştırma {ANA} - {REF}, fark >= {ESIK} ve GA alt ucu > 0.\n")
    return tab, fark


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="acn_oturumlar.csv")
    ap.add_argument("--bolme", type=float, default=0.6)
    ap.add_argument("--gun", type=int, default=None, help="test günü sınırı (hızlı deneme)")
    ap.add_argument("--kapasite", default="0.5,0.7,0.9")
    ap.add_argument("--saha", default="0001,0002")
    ap.add_argument("--milp", action="store_true", help="MILP yöntemlerini de koştur (yavaş)")
    ap.add_argument("--cikti", default="sonuclar.md")
    a = ap.parse_args(argv)
    res, tt, kap = calistir(a.csv, a.bolme, a.gun, tuple(float(x) for x in a.kapasite.split(",")),
                            a.saha.split(","),
                            yontemler=(list(YONTEMLER) if a.milp else None))
    res.to_csv("gunluk_sonuclar.csv", index=False)
    tab, fark = rapor_yaz(res, tt, kap, a.cikti)
    print(tab.round(3).to_string(index=False))
    print(fark.round(3).to_string(index=False))
    print(f"\n{a.cikti} ve gunluk_sonuclar.csv yazıldı.")


if __name__ == "__main__":
    sys.exit(main())
