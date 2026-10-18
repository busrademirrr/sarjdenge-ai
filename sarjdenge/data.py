"""ACN-Data oturumlarını yükle, temizle, özellik üret."""
import numpy as np
import pandas as pd

TZ = "America/Los_Angeles"


def yukle(csv_yolu, min_sure_dk=30, min_kwh=0.5, max_sure_saat=48, max_gecikme_dk=30):
    df = pd.read_csv(csv_yolu, dtype={"siteID": str})
    ilk = "requestedDeparture_ilk" in df.columns
    if ilk:  # bağlantı anına en yakın (ilk) kullanıcı girdisini beyan olarak kullan
        for ad in ["requestedDeparture", "kWhRequested", "minutesAvailable"]:
            df[ad + "_son"] = df[ad]
            df[ad] = df[ad + "_ilk"]
    else:
        print("UYARI: CSV'de ilk girdi sütunları yok; beyan = son girdi (sızıntı riski). acn_veri_cek.py ile yeniden çekin.")
    for c in ["connectionTime", "disconnectTime", "requestedDeparture"]:
        df[c] = pd.to_datetime(df[c], utc=True, errors="coerce")
    df = df.dropna(subset=["connectionTime", "disconnectTime", "kWhDelivered"])
    df["sure_dk"] = (df.disconnectTime - df.connectionTime).dt.total_seconds() / 60
    df = df[(df.sure_dk >= min_sure_dk) & (df.sure_dk <= max_sure_saat * 60)
            & (df.kWhDelivered >= min_kwh)]
    df = df.sort_values("connectionTime").reset_index(drop=True)
    df["yerel_giris"] = df.connectionTime.dt.tz_convert(TZ)
    df["gun"] = df.yerel_giris.dt.normalize().dt.tz_localize(None)
    df["beyan_sure_dk"] = (df.requestedDeparture - df.connectionTime).dt.total_seconds() / 60
    df["userID"] = df["userID"].astype(str).replace({"nan": "anon", "None": "anon"})
    df["beyan_var"] = df.requestedDeparture.notna() & df.kWhRequested.notna()
    if ilk and df.girdi_gecikme_dk.notna().any():  # beyan bağlantıdan en geç 30 dk sonra girildiyse "bağlantı anında bilinen" say
        df["beyan_var"] &= df.girdi_gecikme_dk.between(-5, max_gecikme_dk)
    elif ilk:
        print("UYARI: girdi zamanı (modifiedAt) yok; gecikme filtresi uygulanamadı.")
    return df


def ozellikler(df):
    """Yalnızca bağlantı anında bilinen özellikler; geçmiş = aynı kullanıcının önceki oturumları."""
    X = pd.DataFrame(index=df.index)
    X["saat"] = df.yerel_giris.dt.hour + df.yerel_giris.dt.minute / 60
    X["haftagunu"] = df.yerel_giris.dt.dayofweek
    X["saha"] = df.siteID.astype("category").cat.codes
    X["beyan_sure_dk"] = df.beyan_sure_dk
    X["beyan_kwh"] = df.kWhRequested
    X["beyan_dk_mevcut"] = df.minutesAvailable if "minutesAvailable" in df else np.nan
    g = df.groupby("userID")
    n = g.cumcount()
    for ad, kol in [("gecmis_sure", "sure_dk"), ("gecmis_kwh", "kWhDelivered")]:
        toplam = g[kol].cumsum() - df[kol]
        X[ad] = (toplam / n.where(n > 0)).where(n > 0)
    X["gecmis_n"] = n
    return X
