"""ŞarjDenge AI — Beyan Oranı Kuantillerini Hesaplama ve Doğrulama Betiği.

Bu betik, 2019 H1 eğitim kümesini (%60 gün, 7.808 oturum) kullanarak
kullanıcı beyanı ile gerçekleşen değerler arasındaki oran kuantillerini (q20, q50, q80) hesaplar,
çıktıyı config/beyan_oranlari.json dosyasına yazar ve doğrulama kümesindeki (%40 gün, 5.315 oturum)
kapsam kalibrasyonunu doğrular.
"""

from __future__ import annotations

import json
import pathlib
import sys
import numpy as np
import pandas as pd

PROJE_KOK = pathlib.Path(__file__).resolve().parent.parent
if str(PROJE_KOK) not in sys.path:
    sys.path.insert(0, str(PROJE_KOK))

from sarjdenge import veri_hijyeni

CSV_YOLU = PROJE_KOK / "acn_oturumlar_v2.csv"
CIKTI_JSON = PROJE_KOK / "config" / "beyan_oranlari.json"


def hesapla():
    if not CSV_YOLU.exists():
        print(f"HATA: '{CSV_YOLU}' bulunamadı!", file=sys.stderr)
        sys.exit(1)

    df = veri_hijyeni.temizle(CSV_YOLU, sadece_beyanli=True)
    egit_df, val_df, kesim_gun = veri_hijyeni.zaman_bol(df, bolme=0.6)

    n_egit = len(egit_df)
    n_val = len(val_df)
    assert n_egit == 7808, f"Beklenen 7808 eğitim satırı, bulunan: {n_egit}"
    assert n_val == 5315, f"Beklenen 5315 doğrulama satırı, bulunan: {n_val}"

    # Süre Oranı: Gerçek Süre / Beyan Edilen Süre
    gecerli_sure = (egit_df["beyan_sure_dk"] > 0) & (egit_df["sure_dk"] > 0)
    oran_sure_egit = egit_df.loc[gecerli_sure, "sure_dk"] / egit_df.loc[gecerli_sure, "beyan_sure_dk"]

    # Enerji Oranı: Gerçek Teslim Enerji / Beyan Edilen Enerji
    gecerli_kwh = (egit_df["kWhRequested"] > 0) & (egit_df["kWhDelivered"] > 0)
    oran_kwh_egit = egit_df.loc[gecerli_kwh, "kWhDelivered"] / egit_df.loc[gecerli_kwh, "kWhRequested"]

    q_sure = np.percentile(oran_sure_egit, [20, 50, 80])
    q_kwh = np.percentile(oran_kwh_egit, [20, 50, 80])

    # Doğrulama kümesinde kapsam ölçümü
    v_sure = (val_df["beyan_sure_dk"] > 0) & (val_df["sure_dk"] > 0)
    oran_sure_val = val_df.loc[v_sure, "sure_dk"] / val_df.loc[v_sure, "beyan_sure_dk"]
    v_kwh = (val_df["kWhRequested"] > 0) & (val_df["kWhDelivered"] > 0)
    oran_kwh_val = val_df.loc[v_kwh, "kWhDelivered"] / val_df.loc[v_kwh, "kWhRequested"]

    cov_s20 = float((oran_sure_val <= q_sure[0]).mean())
    cov_s50 = float((oran_sure_val <= q_sure[1]).mean())
    cov_s80 = float((oran_sure_val <= q_sure[2]).mean())

    cov_k20 = float((oran_kwh_val <= q_kwh[0]).mean())
    cov_k50 = float((oran_kwh_val <= q_kwh[1]).mean())
    cov_k80 = float((oran_kwh_val <= q_kwh[2]).mean())

    sonuc = {
        "versiyon": "1.0.0",
        "tanim": "ŞarjDenge AI — Veriden Öğrenilen Beyan Oranı Kuantil Baseline'ı",
        "aciklama": "Kullanıcının ilk beyanı (minutesAvailable_ilk ve kWhRequested_ilk) ile gerçekleşen değerler (sure_dk ve kWhDelivered) arasındaki ampirik oran kuantilleri.",
        "egitim_kaynagi": "acn_oturumlar_v2.csv",
        "egitim_donemi_baslangic": "2019-01-01 00:00:00 America/Los_Angeles",
        "egitim_donemi_bitis": "2019-04-18 23:59:59 America/Los_Angeles",
        "kesim_gunu": str(kesim_gun),
        "egitim_satir_sayisi": n_egit,
        "dogrulama_satir_sayisi": n_val,
        "filtreler": {
            "sadece_beyanli": True,
            "min_sure_dk": 30.0,
            "max_sure_saat": 48.0,
            "min_kwh": 0.5,
            "girdi_gecikme_dk_aralik": [-5.0, 30.0],
            "gecerli_payda_kurali": "beyan_sure_dk > 0 ve kWhRequested > 0",
        },
        "sure_oranlari": {
            "q20": round(float(q_sure[0]), 4),
            "q50": round(float(q_sure[1]), 4),
            "q80": round(float(q_sure[2]), 4),
        },
        "enerji_oranlari": {
            "q20": round(float(q_kwh[0]), 4),
            "q50": round(float(q_kwh[1]), 4),
            "q80": round(float(q_kwh[2]), 4),
        },
        "dogrulama_kapsam_sonuclari": {
            "orneklem_sayisi": n_val,
            "sure_kapsam": {
                "q20_hedef_0.20": round(cov_s20, 4),
                "q50_hedef_0.50": round(cov_s50, 4),
                "q80_hedef_0.80": round(cov_s80, 4),
            },
            "enerji_kapsam": {
                "q20_hedef_0.20": round(cov_k20, 4),
                "q50_hedef_0.50": round(cov_k50, 4),
                "q80_hedef_0.80": round(cov_k80, 4),
            },
        },
        "fiziksel_sinirlar": {
            "min_sure_dk": 30.0,
            "min_kwh": 0.5,
            "maks_kwh": 95.0,
        },
    }

    CIKTI_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(CIKTI_JSON, "w", encoding="utf-8") as f:
        json.dump(sonuc, f, indent=2, ensure_ascii=False)

    print(f"Başarıyla hesaplandı ve kaydedildi: {CIKTI_JSON}")
    print(f"Süre Oranları: q20={sonuc['sure_oranlari']['q20']}, q50={sonuc['sure_oranlari']['q50']}, q80={sonuc['sure_oranlari']['q80']}")
    print(f"Enerji Oranları: q20={sonuc['enerji_oranlari']['q20']}, q50={sonuc['enerji_oranlari']['q50']}, q80={sonuc['enerji_oranlari']['q80']}")


if __name__ == "__main__":
    hesapla()
