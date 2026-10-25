"""ACN-Data oturumlarını yükle, temizle, özellik üret."""
import heapq

import numpy as np
import pandas as pd

TZ = "America/Los_Angeles"


def yukle(csv_yolu, min_sure_dk=30, min_kwh=0.5, max_sure_saat=48, max_gecikme_dk=30):
    df = pd.read_csv(csv_yolu, dtype={"siteID": str})
    ilk = "requestedDeparture_ilk" in df.columns
    if ilk:  # bağlantı anına en yakın (ilk) kullanıcı girdisini beyan olarak kullan
        for ad in ["requestedDeparture", "kWhRequested", "minutesAvailable"]:
            if ad in df.columns:
                df[ad + "_son"] = df[ad]
            if ad + "_ilk" in df.columns:
                df[ad] = df[ad + "_ilk"]
    else:
        print("UYARI: CSV'de ilk girdi sütunları yok; beyan = son girdi (sızıntı riski). acn_veri_cek.py ile yeniden çekin.")
    for c in ["connectionTime", "disconnectTime", "requestedDeparture"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], utc=True, errors="coerce")
    df = df.dropna(subset=["connectionTime", "disconnectTime", "kWhDelivered"])
    df["sure_dk"] = (df.disconnectTime - df.connectionTime).dt.total_seconds() / 60
    df = df[(df.sure_dk >= min_sure_dk) & (df.sure_dk <= max_sure_saat * 60)
            & (df.kWhDelivered >= min_kwh)]
    df = df.sort_values("connectionTime").reset_index(drop=True)
    df["yerel_giris"] = df.connectionTime.dt.tz_convert(TZ)
    df["gun"] = df.yerel_giris.dt.normalize().dt.tz_localize(None)
    df["beyan_sure_dk"] = (df.requestedDeparture - df.connectionTime).dt.total_seconds() / 60
    if "userID" in df.columns:
        df["userID"] = df["userID"].fillna("anon").astype(str).str.strip().replace({"nan": "anon", "None": "anon", "": "anon"})
    else:
        df["userID"] = "anon"
    df["beyan_var"] = df.requestedDeparture.notna() & df.kWhRequested.notna()
    if ilk and "girdi_gecikme_dk" in df.columns and df.girdi_gecikme_dk.notna().any():  # beyan bağlantıdan en geç 30 dk sonra girildiyse "bağlantı anında bilinen" say
        df["beyan_var"] &= df.girdi_gecikme_dk.between(-5, max_gecikme_dk)
    elif ilk:
        print("UYARI: girdi zamanı (modifiedAt) yok; gecikme filtresi uygulanamadı.")
    return df


def kullanici_gecmisi_hesapla(df: pd.DataFrame):
    """Her oturum için yalnızca o oturumun connectionTime anından önce tamamlanmış
    (disconnectTime <= connectionTime) aynı kullanıcı oturumlarından geçmiş özetini hesaplar.

    Kurallar:
    - userID == 'anon' (veya eksik/boş) olan kayıtlar arasında geçmiş oluşturulmaz.
    - Mevcut oturumun veya aynı connectionTime anında başlayan eşzamanlı oturumların
      hedef değerleri (sure_dk, kWhDelivered) kendi özelliklerine dahil edilmez.
    - Hemen önceki oturum çakışsa bile (disconnectTime > connectionTime), daha eski
      tamamlanmış oturumlar (disconnectTime <= connectionTime) geçmiş ortalamasına dahil edilir.
    """
    n_rows = len(df)
    arr_sure = np.full(n_rows, np.nan, dtype=float)
    arr_kwh = np.full(n_rows, np.nan, dtype=float)
    arr_n = np.zeros(n_rows, dtype=int)

    if n_rows == 0 or "userID" not in df.columns:
        return arr_sure, arr_kwh, arr_n

    uid_ser = (
        df["userID"]
        .fillna("anon")
        .astype(str)
        .str.strip()
        .replace({"nan": "anon", "None": "anon", "": "anon"})
    )

    conn_ser = pd.to_datetime(df["connectionTime"], utc=True, errors="coerce")
    disc_ser = pd.to_datetime(df["disconnectTime"], utc=True, errors="coerce")

    if "sure_dk" in df.columns:
        sure_arr = pd.to_numeric(df["sure_dk"], errors="coerce").to_numpy(dtype=float)
    else:
        sure_arr = ((disc_ser - conn_ser).dt.total_seconds() / 60.0).to_numpy(dtype=float)

    kwh_arr = pd.to_numeric(df["kWhDelivered"], errors="coerce").to_numpy(dtype=float)

    conn_valid = conn_ser.notna().to_numpy()
    disc_valid = disc_ser.notna().to_numpy()
    conn_ns = conn_ser.dt.tz_localize(None).astype("datetime64[ns]").astype("int64").to_numpy()
    disc_ns = disc_ser.dt.tz_localize(None).astype("datetime64[ns]").astype("int64").to_numpy()

    for uid, grp_idx in df.groupby(uid_ser, sort=False).groups.items():
        if uid == "anon" or len(grp_idx) <= 1:
            continue

        pos_list = df.index.get_indexer(grp_idx)
        valid_mask = conn_valid[pos_list]
        if not valid_mask.any():
            continue

        pos_valid = pos_list[valid_mask]
        c_vals = conn_ns[pos_valid]

        # Deterministik sıralama: önce connectionTime, eşitlikte orijinal pozisyon
        order = np.lexsort((pos_valid, c_vals))
        ord_pos = pos_valid[order]
        ord_conn = c_vals[order]
        ord_disc = disc_ns[ord_pos]
        ord_disc_ok = disc_valid[ord_pos]
        ord_sure = sure_arr[ord_pos]
        ord_kwh = kwh_arr[ord_pos]

        bekleyen = []  # min-heap: (disc_ns, sure_dk, kwh)
        cum_sure = 0.0
        cum_kwh = 0.0
        cum_count = 0

        m = len(ord_pos)
        i = 0
        while i < m:
            t_conn = ord_conn[i]
            j = i + 1
            while j < m and ord_conn[j] == t_conn:
                j += 1

            # 1. Bu bağlantı anından önce veya tam o anda tamamlanmış önceki oturumları geçmişe ekle
            while bekleyen and bekleyen[0][0] <= t_conn:
                _, s_val, k_val = heapq.heappop(bekleyen)
                cum_sure += s_val
                cum_kwh += k_val
                cum_count += 1

            # 2. Aynı connectionTime anındaki oturumlara mevcut geçmiş ortalamasını ata
            if cum_count > 0:
                ort_sure = cum_sure / cum_count
                ort_kwh = cum_kwh / cum_count
                for k in range(i, j):
                    p = ord_pos[k]
                    arr_n[p] = cum_count
                    arr_sure[p] = ort_sure
                    arr_kwh[p] = ort_kwh

            # 3. Bu gruptaki oturumları kendi tamamlanma zamanlarıyla bekleyen kuyruğuna ekle
            for k in range(i, j):
                if (
                    ord_disc_ok[k]
                    and not np.isnan(ord_sure[k])
                    and not np.isnan(ord_kwh[k])
                ):
                    heapq.heappush(
                        bekleyen,
                        (int(ord_disc[k]), float(ord_sure[k]), float(ord_kwh[k])),
                    )

            i = j

    return arr_sure, arr_kwh, arr_n


def ozellikler(df):
    """Yalnızca bağlantı anında bilinen özellikler; geçmiş = aynı kullanıcının tamamlanmış önceki oturumları."""
    X = pd.DataFrame(index=df.index)
    yerel_giris = (
        df["yerel_giris"]
        if "yerel_giris" in df.columns
        else pd.to_datetime(df["connectionTime"], utc=True, errors="coerce").dt.tz_convert(TZ)
    )
    X["saat"] = yerel_giris.dt.hour + yerel_giris.dt.minute / 60
    X["haftagunu"] = yerel_giris.dt.dayofweek
    X["saha"] = df["siteID"].astype("category").cat.codes if "siteID" in df.columns else 0
    if "beyan_sure_dk" in df.columns:
        X["beyan_sure_dk"] = df["beyan_sure_dk"]
    elif "requestedDeparture" in df.columns:
        X["beyan_sure_dk"] = (
            pd.to_datetime(df["requestedDeparture"], utc=True, errors="coerce")
            - pd.to_datetime(df["connectionTime"], utc=True, errors="coerce")
        ).dt.total_seconds() / 60
    else:
        X["beyan_sure_dk"] = np.nan
    X["beyan_kwh"] = df["kWhRequested"] if "kWhRequested" in df.columns else np.nan
    X["beyan_dk_mevcut"] = df["minutesAvailable"] if "minutesAvailable" in df.columns else np.nan

    gecmis_sure, gecmis_kwh, gecmis_n = kullanici_gecmisi_hesapla(df)
    X["gecmis_sure"] = gecmis_sure
    X["gecmis_kwh"] = gecmis_kwh
    X["gecmis_n"] = gecmis_n
    return X
