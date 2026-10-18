"""ACN-Data'dan oturumları çek; hem İLK hem SON kullanıcı girdisini kaydet.

Neden: son girdi oturum sırasında güncellenmiş olabilir ve gerçek ayrılışı sızdırabilir.
Tahmin deneyinde bağlantı anına yakın ilk girdi kullanılır.

PowerShell:
    py -m pip install acnportal pandas
    $env:ACN_TOKEN = "anahtarınız"
    py acn_veri_cek.py                       # varsayılan: 2019-01-01 .. 2019-07-01
    py acn_veri_cek.py 2019-01-01 2019-10-01
"""
import os
import sys
from datetime import datetime

import pandas as pd

SAHALAR = ["caltech", "jpl"]


def _ts(x):
    return pd.to_datetime(x, utc=True, errors="coerce")


def duzlestir(o):
    r = {k: o.get(k) for k in ["sessionID", "siteID", "connectionTime", "disconnectTime",
                               "doneChargingTime", "kWhDelivered", "userID"]}
    girdiler = o.get("userInputs") or []
    r["girdi_sayisi"] = len(girdiler)
    r["girdi_degisti"] = int(len(girdiler) > 1)
    if girdiler:
        sirali = sorted(girdiler, key=lambda g: (_ts(g.get("modifiedAt")) if g.get("modifiedAt") is not None
                                                  else pd.Timestamp.max.tz_localize("UTC")))
        ilk, son = sirali[0], sirali[-1]
        for ad, g in [("_ilk", ilk), ("", son)]:
            r["kWhRequested" + ad] = g.get("kWhRequested")
            r["requestedDeparture" + ad] = g.get("requestedDeparture")
            r["minutesAvailable" + ad] = g.get("minutesAvailable")
        r["girdi_gecikme_dk"] = (_ts(ilk.get("modifiedAt")) - _ts(o.get("connectionTime"))).total_seconds() / 60
    return r


def main():
    from acnportal import acndata
    token = os.environ.get("ACN_TOKEN")
    if not token:
        sys.exit('ACN_TOKEN yok. Önce: $env:ACN_TOKEN = "anahtarınız"')
    bas = datetime.strptime(sys.argv[1], "%Y-%m-%d") if len(sys.argv) > 1 else datetime(2019, 1, 1)
    son = datetime.strptime(sys.argv[2], "%Y-%m-%d") if len(sys.argv) > 2 else datetime(2019, 7, 1)
    client = acndata.DataClient(token)
    tum = []
    for site in SAHALAR:
        print(f"[{site}] {bas.date()} - {son.date()} çekiliyor...", flush=True)
        s = [duzlestir(x) for x in client.get_sessions_by_time(site, bas, son)]
        print(f"  {len(s)} oturum", flush=True)
        tum += s
    df = pd.DataFrame(tum)
    df.to_csv("acn_oturumlar_v2.csv", index=False)
    print(f"\nacn_oturumlar_v2.csv yazıldı ({len(df)} oturum).")
    if "girdi_gecikme_dk" in df:
        print("ilk girdi gecikmesi (dk): medyan %.1f, p90 %.1f" % (df.girdi_gecikme_dk.median(), df.girdi_gecikme_dk.quantile(.9)))
        print("girdisi sonradan değişen oturum: %%%.1f" % (100 * df.girdi_degisti.mean()))


if __name__ == "__main__":
    main()
