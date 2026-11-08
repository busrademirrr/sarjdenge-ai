import os
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sarjdenge import veri_hijyeni, sim, deney_v2
from sarjdenge.web_servis import esit_paylasim_kurali

# 1. Veri Yükleme ve Hijyen Filtreleme
csv_path = 'acn_oturumlar_ocak_haziran.csv'
print(f"Veri okunuyor: {csv_path}")
df = veri_hijyeni.temizle(csv_path, sadece_beyanli=True)
print(f"Temizlenmis beyanli veri boyutu: {len(df)}")

# Caltech sahası (siteID '0002') üzerinde ilk 18 geçerli gün
df_caltech = df[df['siteID'].isin(['0002', '2', 2])].copy()
unique_days = sorted(df_caltech['gun'].unique())
secili_gunler = unique_days[:18]
print(f"Analiz edilecek ilk 18 keşifsel gün: {secili_gunler}")

yontem_tanimlari = [
    ("FCFS (İlk Gelen İlk Şarj)", sim.kural("fcfs")),
    ("EDF (Erken Ayrılana Öncelik)", sim.kural("edf")),
    ("Eşit Güç Paylaşımı", esit_paylasim_kurali),
    ("LP Tabanlı MPC", sim.mpc),
]

arama_cozunurlugu_kw = 0.5
sonuclar = {ad: [] for ad, _ in yontem_tanimlari}
gecerli_gun_sayisi = 0

for g in secili_gunler:
    gd = df_caltech[df_caltech['gun'] == g].sort_values('connectionTime').reset_index(drop=True)
    if len(gd) < 4:
        continue
    
    t0 = gd['connectionTime'].min()
    kaynaklar = deney_v2.inanilan_kaynaklar(gd)
    
    giris_tam = np.ceil(deney_v2.adimlar(gd['connectionTime'], t0)).astype(int)
    ayril_tam = np.floor(deney_v2.adimlar(gd['disconnectTime'], t0)).astype(int)
    gec = ayril_tam > giris_tam
    
    if gec.sum() < 4:
        continue
        
    giris = giris_tam[gec]
    ayril = ayril_tam[gec]
    e_gercek = gd['kWhDelivered'].to_numpy(dtype=float)[gec]
    tepe_kw = float(sim.kontrolsuz_tepe(giris, ayril, e_gercek))
    if tepe_kw <= 0:
        continue
    tepe_kw = round(tepe_kw, 1)
    
    sure_saat = (ayril - giris) * sim.DT_H
    fiziksel_imkansiz = (sim.PMAX * sure_saat < 0.95 * e_gercek - 1e-6)
    karsilanabilir = ~fiziksel_imkansiz
    n_karsilanabilir = int(karsilanabilir.sum())
    
    if n_karsilanabilir == 0:
        continue
        
    taban_kw = max(
        float(sim.SEVIYELER[1]),
        round(0.05 * tepe_kw / arama_cozunurlugu_kw) * arama_cozunurlugu_kw,
    )
    
    ts_sub = kaynaklar["beyan"][0].loc[gd.index][gec].reset_index(drop=True)
    inan_dep = np.maximum(np.floor(deney_v2.adimlar(ts_sub, t0)), giris + 1).astype(int)
    inan_kwh = np.asarray(kaynaklar["beyan"][1])[gd.index.get_indexer(gd.index)][gec]
    
    def _eval(fn, cap_val):
        c_f = round(float(cap_val), 1)
        teslim = sim.simule(giris, ayril, e_gercek, inan_dep, inan_kwh, c_f, fn)
        sat = teslim / np.maximum(e_gercek, 1e-6)
        ok = sat >= 0.95 - 1e-6
        ok_k = ok[karsilanabilir]
        ok_sayisi = int(ok_k.sum())
        kacirilan_arac = int(n_karsilanabilir - ok_sayisi)
        ok_orani = float(ok_sayisi / n_karsilanabilir)
        return bool((ok_orani >= 0.95 - 1e-6) and (kacirilan_arac <= 1))
        
    gun_ok = True
    gun_kap = {}
    for ad, fn in yontem_tanimlari:
        if not _eval(fn, tepe_kw):
            gun_ok = False
            break
        # İkili arama
        low_idx = int(round(taban_kw / arama_cozunurlugu_kw))
        high_idx = int(round(tepe_kw / arama_cozunurlugu_kw))
        best_kw = tepe_kw
        while low_idx <= high_idx:
            mid_idx = (low_idx + high_idx) // 2
            c_mid = round(mid_idx * arama_cozunurlugu_kw, 1)
            if _eval(fn, c_mid):
                best_kw = c_mid
                high_idx = mid_idx - 1
            else:
                low_idx = mid_idx + 1
        gun_kap[ad] = best_kw
        
    if gun_ok:
        gecerli_gun_sayisi += 1
        for ad, _ in yontem_tanimlari:
            sonuclar[ad].append(gun_kap[ad])

print(f"Başarıyla simüle edilen keşifsel gün sayısı: {gecerli_gun_sayisi}")
for ad in sonuclar:
    print(f"{ad}: {sonuclar[ad]}")

# 2. Grafik Çizimi (Ampirik CDF / Kapasite-Risk Eğrisi)
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'
fig, ax = plt.subplots(figsize=(7.2, 4.5), dpi=300)

renkler = {
    "FCFS (İlk Gelen İlk Şarj)": "#7f7f7f",
    "EDF (Erken Ayrılana Öncelik)": "#1f77b4",
    "Eşit Güç Paylaşımı": "#ff7f0e",
    "LP Tabanlı MPC": "#2ca02c"
}
stiller = {
    "FCFS (İlk Gelen İlk Şarj)": ":",
    "EDF (Erken Ayrılana Öncelik)": "-",
    "Eşit Güç Paylaşımı": "--",
    "LP Tabanlı MPC": "-."
}

# Ortak x ekseni aralığı
min_c = min(min(vals) for vals in sonuclar.values())
max_c = max(max(vals) for vals in sonuclar.values())
x_grid = np.linspace(max(0, min_c - 2), max_c + 5, 300)

for ad, vals in sonuclar.items():
    vals = np.sort(vals)
    y_vals = np.array([np.mean(vals <= x) for x in x_grid])
    ax.plot(x_grid, y_vals, label=ad, color=renkler[ad], linestyle=stiller[ad], linewidth=2.0)

# %95 Hizmet Güvence Düzeyi (1 - alpha = 0.95)
ax.axhline(0.95, color="#d62728", linestyle="--", linewidth=1.2, label="%95 Güvence Eşiği (1 - α = 0,95)")

ax.set_xlabel("Bağlantı Gücü / Kapasite (kW)", fontsize=9.5, fontweight="bold")
ax.set_ylabel("Hedefin Karşılandığı Günlerin Oranı (1 - α)", fontsize=9.5, fontweight="bold")
ax.set_title("Planlama Kurallarına Göre Kapasite–Risk Eğrileri\n(ACN-Data 2019 İlk Yarı Keşifsel Günler, τ = 0,95)", fontsize=10.5, fontweight="bold")
ax.set_ylim(-0.02, 1.05)
ax.set_xlim(x_grid[0], x_grid[-1])
ax.grid(True, linestyle=":", alpha=0.6)
ax.legend(loc="lower right", fontsize=8.5, framealpha=0.95)

plt.tight_layout()
os.makedirs("docs", exist_ok=True)
out_png = "docs/sekil2_kapasite_risk_egrisi.png"
plt.savefig(out_png, dpi=300)
print(f"Grafik kaydedildi: {out_png}")

# Kopya artifact dizinine
artifact_dir = r"C:\Users\HP-PC\.gemini\antigravity\brain\bfa06e6f-39c3-42a2-b9ad-5c3db15ad755"
shutil.copy(out_png, os.path.join(artifact_dir, "sekil2_kapasite_risk_egrisi.png"))
print("Artifact dizinine kopyalandı.")
