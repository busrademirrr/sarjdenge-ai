"""Türkiye apartman sitesi için ETİKETLİ SENTETİK şarj oturumu üretici.

Gerçek Türkiye verisi yok (Cemil Bey de bilmiyor). Bu üretici varsayımlarını açıkça yazar;
sonuçlar "senaryo sonucu"dur, ölçüm değildir. Varsayımlar PARAMETRELER içinde, değiştirilebilir.

Davranış varsayımları (kaynaklı olmayanlar varsayımdır):
- Sürücüler akşam eve gelir (ort. 19:00) ve sabah çıkar (ort. 07:45); kişiye özgü alışkanlık vardır.
- Günlük ihtiyaç: yol 25-70 km x ~0,18 kWh/km (varsayım) -> çoğunlukla 5-13 kWh, bazı günler uzun yol.
- Beyan hatası ACN-Data'dan ÖDÜNÇ: kullanıcılar ort. ~33 dk sonra ayrılır, hata sapması ~75 dk.
- Beyan edilen enerji gerçeğin üstünde olma eğilimindedir (ACN'de teslim < talep oranı %90).
"""
import numpy as np
import pandas as pd

PARAMETRELER = dict(
    soket=20,               # sitedeki şarj noktası sayısı
    arac_olasiligi=0.55,    # bir soketin bir gece dolu olma olasılığı (hafta içi)
    hafta_sonu_carpani=0.7,
    varis_ort=19.0, varis_sd=1.2,        # saat
    cikis_ort=7.75, cikis_sd=0.6,        # saat (kişi başına alışkanlık ortalaması)
    cikis_gunluk_sd=0.45,                # alışkanlıktan günlük sapma (saat)
    kwh_ort_log=np.log(8.0), kwh_sd_log=0.55,
    kwh_ust=40.0,
    beyan_kayma_dk=33.0, beyan_sd_dk=75.0,   # ACN'den ödünç (beyan ayrılıştan erken/sapmalı)
    beyan_kwh_asiri=(1.0, 1.7),              # beyan edilen enerji = gerçek x U(a,b) (+ gürültü)
    kullanici=60,           # sitedeki farklı sürücü sayısı
)


def uret(gun=150, tohum=0, yol="turkiye_oturumlar.csv", p=None):
    p = {**PARAMETRELER, **(p or {})}
    rng = np.random.default_rng(tohum)
    kul = [dict(varis=rng.normal(p["varis_ort"], p["varis_sd"]),
                cikis=rng.normal(p["cikis_ort"], p["cikis_sd"]),
                kwh=np.exp(rng.normal(p["kwh_ort_log"], 0.35))) for _ in range(p["kullanici"])]
    tz = "Europe/Istanbul"
    baslangic = pd.Timestamp("2026-01-05", tz=tz)
    satir, sid = [], 0
    for d in range(gun):
        g = baslangic + pd.Timedelta(days=d)
        pr = p["arac_olasiligi"] * (p["hafta_sonu_carpani"] if g.dayofweek >= 5 else 1.0)
        n = int(min(p["soket"], rng.binomial(p["soket"], pr)))
        for u in rng.choice(p["kullanici"], n, replace=False):
            k = kul[u]
            giris = g + pd.Timedelta(hours=float(np.clip(rng.normal(k["varis"], 0.6), 16, 23.5)))
            cikis_saat = float(np.clip(rng.normal(k["cikis"], p["cikis_gunluk_sd"]), 5.0, 11.0))
            cikis = g + pd.Timedelta(days=1, hours=cikis_saat)
            kwh = float(np.clip(k["kwh"] * rng.lognormal(0, 0.45), 1.5, p["kwh_ust"]))
            beyan = cikis - pd.Timedelta(minutes=float(p["beyan_kayma_dk"] + rng.normal(0, p["beyan_sd_dk"])))
            beyan = max(beyan, giris + pd.Timedelta(minutes=45))
            talep = kwh * rng.uniform(*p["beyan_kwh_asiri"]) + rng.exponential(1.0)
            satir.append(dict(
                sessionID=f"t{sid}", siteID="TR01",
                connectionTime=giris.tz_convert("UTC"), disconnectTime=cikis.tz_convert("UTC"),
                doneChargingTime=cikis.tz_convert("UTC"), kWhDelivered=kwh, userID=f"tr{u}",
                girdi_sayisi=1, kWhRequested=talep, requestedDeparture=beyan.tz_convert("UTC"),
                minutesAvailable=(beyan - giris).total_seconds() / 60,
                requestedDeparture_ilk=beyan.tz_convert("UTC"), kWhRequested_ilk=talep,
                minutesAvailable_ilk=(beyan - giris).total_seconds() / 60,
                girdi_gecikme_dk=float(rng.exponential(3)), girdi_degisti=0))
            sid += 1
    pd.DataFrame(satir).to_csv(yol, index=False)
    return yol


if __name__ == "__main__":
    print(uret())
