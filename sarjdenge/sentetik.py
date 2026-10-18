"""SADECE KOD TESTİ İÇİN sentetik oturumlar. Sonuç olarak sunulamaz."""
import numpy as np
import pandas as pd


def uret(gun=60, tohum=0, yol="sentetik_oturumlar.csv"):
    rng = np.random.default_rng(tohum)
    satir = []
    kullanici = {s: [(rng.uniform(7, 10), rng.uniform(4, 10)) for _ in range(40)] for s in ["0001", "0002"]}
    tarih = pd.Timestamp("2019-01-02", tz="America/Los_Angeles")
    sid = 0
    for d in range(gun):
        gun_ts = tarih + pd.Timedelta(days=d)
        if gun_ts.dayofweek >= 5:
            continue
        for site, n in [("0001", 45), ("0002", 30)]:
            for _ in range(n):
                u = rng.integers(0, 40)
                alis, sure = kullanici[site][u]
                giris = gun_ts + pd.Timedelta(hours=float(np.clip(rng.normal(alis, 0.8), 5, 15)))
                dur = float(np.clip(sure * rng.lognormal(0, 0.35), 0.7, 14))
                cikis = giris + pd.Timedelta(hours=dur)
                kwh = float(np.clip(rng.gamma(3, 3.5), 1, 45))
                beyan_cik = cikis - pd.Timedelta(minutes=float(33 + rng.normal(0, 90)))
                satir.append(dict(
                    sessionID=f"s{sid}", siteID=site,
                    connectionTime=giris.tz_convert("UTC"), disconnectTime=cikis.tz_convert("UTC"),
                    doneChargingTime=cikis.tz_convert("UTC"), kWhDelivered=kwh, userID=f"u{site}{u}",
                    girdi_sayisi=1, kWhRequested=(talep := kwh * rng.uniform(1.0, 1.8) + rng.exponential(2)),
                    requestedDeparture=beyan_cik.tz_convert("UTC"), minutesAvailable=max((beyan_cik - giris).total_seconds() / 60, 30),
                    requestedDeparture_ilk=beyan_cik.tz_convert("UTC"), kWhRequested_ilk=talep, minutesAvailable_ilk=max((beyan_cik - giris).total_seconds() / 60, 30), girdi_gecikme_dk=float(rng.exponential(3)), girdi_degisti=0))
                sid += 1
    pd.DataFrame(satir).to_csv(yol, index=False)
    return yol


if __name__ == "__main__":
    print(uret())
