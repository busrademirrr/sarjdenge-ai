"""ŞarjDenge AI — Streamlit Arayüzü (Türkçe)

Veri kaynağı: demo_veri.json (sentetik Türkiye senaryosu)
              sonuclar.md / gunluk_sonuclar.csv (ACN deney sonuçları, opsiyonel)

Dosya yoksa açık uyarı gösterilir; kodda elle yazılmış sonuç sayısı YOKTUR.
Her ekranda "Sentetik senaryo, ölçüm değil" etiketi görünür.
Yöntem listesi dinamiktir; demo_veri.json içindeki tüm yöntemleri genel olarak gösterir.
"""

import json
import os
import pathlib

import numpy as np
import pandas as pd
import streamlit as st

# ── Sayfa ayarları ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ŞarjDenge AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJE_KOK = pathlib.Path(__file__).parent
DEMO_JSON = PROJE_KOK / "demo_veri.json"
SONUCLAR_CSV = PROJE_KOK / "gunluk_sonuclar.csv"
SONUCLAR_MD = PROJE_KOK / "sonuclar.md"

SENTETIK_ETIKET = "⚠️ Sentetik senaryo, ölçüm değil"

# Bilinen yöntemler için etiket ve renk önerileri; bilinmeyenler dinamik türetilir
YONTEM_AD_ONERILERI = {
    "statik": "Statik paylaşım",
    "fcfs_beyan": "FCFS (beyan)",
    "mpc_beyan": "MPC (beyan)",
    "milp_beyan": "MILP (beyan)",
    "sarjdenge": "ŞarjDenge (MILP+tahmin)",
}

BILINEN_RENKLER = {
    "statik": "#e74c3c",
    "fcfs_beyan": "#e67e22",
    "mpc_beyan": "#3498db",
    "milp_beyan": "#9b59b6",
    "sarjdenge": "#2ecc71",
}

EK_RENKLER = [
    "#1abc9c", "#34495e", "#f39c12", "#d35400", "#16a085",
    "#27ae60", "#2980b9", "#8e44ad", "#2c3e50", "#7f8c8d"
]


def yontem_adi(yontem_kodu: str) -> str:
    """Yöntem kodundan insan tarafından okunabilir etiket üretir (sabit liste kısıtlaması olmadan)."""
    return YONTEM_AD_ONERILERI.get(yontem_kodu, yontem_kodu.replace("_", " ").title())


def yontem_renk_sozlugu(yontem_listesi) -> dict:
    """Verilen yöntem listesi için dinamik renk sözlüğü oluşturur."""
    renkler = {}
    ek_idx = 0
    for y in yontem_listesi:
        if y in BILINEN_RENKLER:
            renkler[y] = BILINEN_RENKLER[y]
        else:
            renkler[y] = EK_RENKLER[ek_idx % len(EK_RENKLER)]
            ek_idx += 1
    return renkler


# ── Veri yükleme ─────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Demo verisi yükleniyor…")
def demo_yukle():
    if not DEMO_JSON.exists():
        return None
    with open(DEMO_JSON, encoding="utf-8") as fh:
        return json.load(fh)


@st.cache_data(show_spinner="Günlük sonuçlar yükleniyor…")
def gunluk_yukle():
    if not SONUCLAR_CSV.exists():
        return None
    return pd.read_csv(SONUCLAR_CSV)


# ── Yardımcılar ───────────────────────────────────────────────────────────────

def uyari_kutusu(mesaj: str):
    st.warning(mesaj, icon="⚠️")


def sentetik_rozet():
    st.caption(SENTETIK_ETIKET)


def veri_yok_uyarisi(dosya: str, komut: str):
    st.error(
        f"**{dosya}** bulunamadı.  \n"
        f"Önce şunu çalıştırın:  \n```\n{komut}\n```",
        icon="🚫",
    )


# ── Ekran 1: Kapasite Karar Aracı ────────────────────────────────────────────

def ekran_kapasite(demo):
    st.header("⚡ Kapasite Karar Aracı")
    sentetik_rozet()
    st.markdown(
        "Soket sayısı ve toplam bağlantı kapasitesini (kW) girin.  \n"
        "Her yöntem için **araçların %95'inin zamanında şarjı bitirmesi** için "
        "gereken en küçük kapasite gösterilir."
    )

    col1, col2 = st.columns(2)
    with col1:
        soket = st.number_input("Soket sayısı", min_value=1, max_value=200,
                                value=int(demo.get("soket", 20)), step=1)
    with col2:
        kullanici_cap = st.number_input(
            "Toplam bağlantı kapasitesi (kW)", min_value=1.0, max_value=500.0,
            value=15.0, step=1.0,
            help="Trafo/bağlantı kapasite sınırınız"
        )

    # demo'daki yeterli kapasite değerleri (yöntem bazlı dinamik)
    yeterli: dict = demo.get("yeterli", {})
    tarama_df = pd.DataFrame(demo.get("tarama", []))

    if tarama_df.empty or not yeterli:
        uyari_kutusu("demo_veri.json içinde kapasite taraması bulunamadı.")
        return

    st.subheader("Yöntem Başına Yeterli Kapasite (kW)")
    sentetik_rozet()

    # Yöntemleri dinamik sütunlarla göster
    tum_yontemler = list(yeterli.keys())
    renk_haritasi = yontem_renk_sozlugu(tum_yontemler)

    kart_cols = st.columns(len(tum_yontemler))
    for col, yont in zip(kart_cols, tum_yontemler):
        cap_val = yeterli[yont]
        ad = yontem_adi(yont)
        if cap_val is None:
            metin = "Sağlanamadı"
            delta_renk = "off"
        else:
            metin = f"{cap_val:.0f} kW"
            delta_renk = "normal"
        col.metric(
            label=ad,
            value=metin,
            delta=("✅ Yeterli" if cap_val is not None and cap_val <= kullanici_cap else
                   "❌ Yetersiz" if cap_val is not None else "—"),
            delta_color=delta_renk,
        )

    # Kapasite tarama grafiği
    st.subheader("Kapasite — Başarı Oranı Grafiği")
    sentetik_rozet()

    hedef_cizgi = demo.get("hedef", 0.95)

    import altair as alt

    # Sabit liste filtrelemesi YOKTUR; gelen tüm yöntemler dinamik olarak grafiğe eklenir
    long_df = tarama_df.copy()
    long_df["yontem_ad"] = long_df["yontem"].apply(yontem_adi)

    mevcut_yontemler = sorted(long_df["yontem"].unique().tolist())
    mevcut_etiketler = [yontem_adi(y) for y in mevcut_yontemler]
    mevcut_renkler = [renk_haritasi.get(y, "#95a5a6") for y in mevcut_yontemler]

    base = alt.Chart(long_df).encode(
        x=alt.X("cap:Q", title="Kapasite (kW)"),
        y=alt.Y("ok:Q", title="Araçların %95 hedefine ulaşma oranı",
                scale=alt.Scale(domain=[0, 1])),
        color=alt.Color("yontem_ad:N",
                        scale=alt.Scale(domain=mevcut_etiketler, range=mevcut_renkler),
                        legend=alt.Legend(title="Yöntem")),
        tooltip=["cap", "yontem_ad", alt.Tooltip("ok:Q", format=".3f")],
    )

    cizgi = base.mark_line(point=True, strokeWidth=2)

    hedef_df = pd.DataFrame({"y": [hedef_cizgi]})
    hedef_c = alt.Chart(hedef_df).mark_rule(
        color="gray", strokeDash=[4, 4]
    ).encode(y="y:Q")

    kullanici_df = pd.DataFrame({"x": [kullanici_cap]})
    kullanici_c = alt.Chart(kullanici_df).mark_rule(
        color="black", strokeDash=[6, 3], strokeWidth=2
    ).encode(x="x:Q")

    grafik = (cizgi + hedef_c + kullanici_c).properties(
        width=700, height=380,
        title="Kapasite taraması (Türkiye apartman senaryosu — sentetik)"
    ).interactive()

    st.altair_chart(grafik, use_container_width=True)
    st.caption(f"Kesik gri çizgi = %{hedef_cizgi*100:.0f} hedef | Siyah kesik çizgi = girilen kapasite")


# ── Ekran 2: Tek Gün Görünümü ─────────────────────────────────────────────────

def ekran_tek_gun(demo):
    st.header("📅 Tek Gün Görünümü")
    sentetik_rozet()

    detay: dict = demo.get("detay", {})
    if not detay:
        uyari_kutusu("demo_veri.json içinde detay verisi bulunamadı.")
        return

    gun_str = detay.get("gun", "?")
    kap = detay.get("kap", "?")
    adim_n = detay.get("adim_n", 96)
    araclar = detay.get("araclar", [])

    st.markdown(f"**Seçilen gün:** `{gun_str}` | **Kapasite:** `{kap} kW` | "
                f"**Araç sayısı:** `{len(araclar)}`")
    sentetik_rozet()

    # Zaman ekseni (15 dk adım → saat)
    adimlar = np.arange(adim_n)
    saatler = adimlar * 0.25  # saat cinsinden

    # Toplam güç hesapla
    def toplam_guc(guc_listesi):
        arr = np.array(guc_listesi, dtype=float)   # (adim_n, n_arac)
        return arr.sum(axis=1)

    # Detayda bulunan yöntemleri dinamik al
    guc_sozluk = {"Saat": saatler}
    detay_yontemleri = [k for k in detay.keys() if isinstance(detay[k], dict) and "guc" in detay[k]]
    for dy in detay_yontemleri:
        etiket = yontem_adi(dy)
        guc_sozluk[etiket] = toplam_guc(detay[dy].get("guc", []))

    guc_sozluk["Kapasite sınırı"] = [float(kap)] * len(saatler)
    guc_df = pd.DataFrame(guc_sozluk)

    import altair as alt

    guc_long = guc_df.melt("Saat", var_name="Kaynak", value_name="Güç (kW)")

    renk_haritasi = yontem_renk_sozlugu(detay_yontemleri)
    renk_map = {yontem_adi(k): v for k, v in renk_haritasi.items()}
    renk_map["Kapasite sınırı"] = "#7f8c8d"

    grafik_guc = (
        alt.Chart(guc_long)
        .mark_line()
        .encode(
            x=alt.X("Saat:Q", title="Saat (yerel)"),
            y=alt.Y("Güç (kW):Q", title="Toplam Güç (kW)"),
            color=alt.Color("Kaynak:N",
                            scale=alt.Scale(
                                domain=list(renk_map.keys()),
                                range=list(renk_map.values())
                            )),
            strokeDash=alt.condition(
                alt.datum.Kaynak == "Kapasite sınırı",
                alt.value([4, 4]), alt.value([0])
            ),
            tooltip=["Saat", "Kaynak", alt.Tooltip("Güç (kW):Q", format=".2f")],
        )
        .properties(
            width=700, height=300,
            title=f"Toplam güç profili — {gun_str} (sentetik)"
        )
        .interactive()
    )

    st.altair_chart(grafik_guc, use_container_width=True)
    st.caption(SENTETIK_ETIKET)

    # Araç araç plan tablosu
    st.subheader("Araç Planı")
    sentetik_rozet()

    def adim_saat(adim):
        """Adımı HH:MM formatına çevir (gece 00:00 üzerinden)."""
        h = int(adim * 0.25)
        m = int((adim * 0.25 - h) * 60)
        return f"{h:02d}:{m:02d}"

    satirlar = []
    for i, a in enumerate(araclar):
        satir = {
            "Araç #": i + 1,
            "Giriş": adim_saat(a["giris"]),
            "Ayrılış": adim_saat(a["ayril"]),
            "Tahmin ayrılış": adim_saat(a.get("tahmin_ayril", a["ayril"])),
            "Hedef (kWh)": round(float(a["kwh"]), 2),
        }
        for dy in detay_yontemleri:
            teslim_list = detay[dy].get("teslim", [])
            teslim_val = float(teslim_list[i]) if i < len(teslim_list) else float("nan")
            etiket = yontem_adi(dy)
            satir[f"{etiket} (kWh)"] = round(teslim_val, 2)
            satir[f"{etiket} Durum"] = "✅" if teslim_val >= 0.95 * float(a["kwh"]) else "❌"
        satirlar.append(satir)

    tablo = pd.DataFrame(satirlar)
    st.dataframe(tablo, use_container_width=True, hide_index=True)

    metrik_cols = st.columns(len(detay_yontemleri))
    for col, dy in zip(metrik_cols, detay_yontemleri):
        etiket = yontem_adi(dy)
        oran = sum(1 for r in satirlar if r.get(f"{etiket} Durum") == "✅") / max(len(satirlar), 1)
        col.metric(f"{etiket} — Hedefe Ulaşan", f"%{oran*100:.1f}")

    st.caption(SENTETIK_ETIKET)


# ── Ekran 3: Yöntem Karşılaştırma ─────────────────────────────────────────────

def ekran_karsilastirma(demo):
    st.header("📊 Yöntem Karşılaştırma")
    sentetik_rozet()

    tarama_df = pd.DataFrame(demo.get("tarama", []))
    fark_df = pd.DataFrame(demo.get("fark", []))

    if tarama_df.empty:
        uyari_kutusu("demo_veri.json içinde tarama verisi bulunamadı.")
        return

    import altair as alt

    # Kapasite başına yöntem karşılaştırma kutusu (tüm yöntemler genel olarak listelenir)
    st.subheader("Kapasiteye Göre Başarı Oranı (yöntem × kapasite)")
    sentetik_rozet()

    long_df = tarama_df.copy()
    long_df["yontem_ad"] = long_df["yontem"].apply(yontem_adi)

    tum_yontemler = sorted(long_df["yontem"].unique().tolist())
    renk_haritasi = yontem_renk_sozlugu(tum_yontemler)
    mevcut_etiketler = [yontem_adi(y) for y in tum_yontemler]
    mevcut_renkler = [renk_haritasi.get(y, "#95a5a6") for y in tum_yontemler]

    bar = (
        alt.Chart(long_df)
        .mark_bar()
        .encode(
            x=alt.X("cap:O", title="Kapasite (kW)"),
            y=alt.Y("ok:Q", title="Zamanında %95 hedefine ulaşan araç oranı",
                    scale=alt.Scale(domain=[0, 1])),
            color=alt.Color("yontem_ad:N",
                            scale=alt.Scale(domain=mevcut_etiketler, range=mevcut_renkler),
                            legend=alt.Legend(title="Yöntem")),
            xOffset="yontem_ad:N",
            tooltip=["cap", "yontem_ad", alt.Tooltip("ok:Q", format=".3f"),
                     alt.Tooltip("gun:Q", title="Gün sayısı")],
        )
        .properties(width=700, height=350,
                    title="Yöntem karşılaştırması (sentetik Türkiye senaryosu)")
    )

    hedef_df2 = pd.DataFrame({"y": [demo.get("hedef", 0.95)]})
    hedef_c2 = alt.Chart(hedef_df2).mark_rule(
        color="gray", strokeDash=[4, 4]
    ).encode(y="y:Q")

    st.altair_chart((bar + hedef_c2).interactive(), use_container_width=True)

    # Fark tablosu (bootstrap GA)
    if not fark_df.empty:
        st.subheader("Fark Analizi (Bootstrap %95 GA)")
        sentetik_rozet()

        goster = fark_df[["cap", "karsilastirma", "fark", "alt", "ust"]].copy()
        # Karşılaştırma etiketlerini de okunabilir yap
        def ceviri(metin):
            for k in tum_yontemler:
                metin = metin.replace(k, yontem_adi(k))
            return metin
        goster["karsilastirma"] = goster["karsilastirma"].apply(ceviri)
        goster.columns = ["Kapasite (kW)", "Karşılaştırma", "Fark", "GA alt", "GA üst"]
        st.dataframe(goster.round(3), use_container_width=True, hide_index=True)

        st.caption(
            "Fark analizi sentetik senaryo üzerinden hesaplanmıştır. "
            "Pozitif fark ilk yöntemin lehinedir; aralık 0'ı kapsıyorsa fark istatistiksel olarak anlamlı değildir. "
            + SENTETIK_ETIKET
        )

    # Kapasite yetersizliği — hangi kapasitelerde %95 sağlanamıyor
    st.subheader("Kapasite Yetersizliği Raporu")
    sentetik_rozet()

    hedef = demo.get("hedef", 0.95)
    yetersiz = tarama_df[tarama_df.ok < hedef][["cap", "yontem", "ok"]].copy()
    yetersiz["yontem_ad"] = yetersiz["yontem"].apply(yontem_adi)

    if yetersiz.empty:
        st.success("Tüm kapasite-yöntem kombinasyonları %95 hedefini sağlıyor.")
    else:
        piv_yok = yetersiz.pivot_table(
            index="cap", columns="yontem_ad", values="ok", aggfunc="mean"
        ).round(3)
        st.markdown("**Hedefin altında kalan (ok < %95) kapasite/yöntem kombinasyonları:**")
        st.dataframe(piv_yok, use_container_width=True)
        st.caption(SENTETIK_ETIKET)

    # ACN deney sonuçları (varsa)
    st.divider()
    st.subheader("ACN Deney Sonuçları (gerçek veri — opsiyonel)")
    if SONUCLAR_CSV.exists():
        acn_df = gunluk_yukle()
        if acn_df is not None:
            st.dataframe(acn_df.head(50), use_container_width=True, hide_index=True)
            st.caption("Kaynak: ACN-Data (Caltech). Gerçek ölçüm verisi.")
        else:
            uyari_kutusu("gunluk_sonuclar.csv okunamadı.")
    else:
        st.info(
            "**gunluk_sonuclar.csv** bulunamadı — ACN deneyi henüz çalıştırılmamış.  \n"
            "Çalıştırmak için:\n"
            "```\npy -W ignore -m sarjdenge.deney --csv acn_oturumlar_v2.csv\n```",
            icon="ℹ️",
        )


# ── Ana uygulama ──────────────────────────────────────────────────────────────

def main():
    st.title("⚡ ŞarjDenge AI")
    st.markdown(
        "EV şarj gücü optimizasyonu — kapasite kısıtlı apartman ve iş yeri otoparklarında "
        "akıllı güç planlaması.  \n"
        f"*Climathon 2026 · {SENTETIK_ETIKET}*"
    )

    demo = demo_yukle()

    if demo is None:
        veri_yok_uyarisi(
            "demo_veri.json",
            "py -W ignore -m sarjdenge.urun --uret"
        )
        st.stop()

    # Etiket her zaman görünür
    st.sidebar.markdown(f"### {SENTETIK_ETIKET}")
    st.sidebar.markdown(
        f"**Senaryo:** {demo.get('etiket', '?')}  \n"
        f"**Soket:** {demo.get('soket', '?')}  \n"
        f"**Test günü:** {demo.get('test_gun', '?')}  \n"
        f"**Hedef:** %{demo.get('hedef', 0.95) * 100:.0f} araç ≥ %95 teslim"
    )
    st.sidebar.divider()
    st.sidebar.markdown(
        "**Veri kaynağı:** `demo_veri.json`  \n"
        "Üretmek için:\n"
        "```\npy -W ignore -m sarjdenge.urun --uret\n```"
    )

    sekme1, sekme2, sekme3 = st.tabs([
        "⚡ Kapasite Karar Aracı",
        "📅 Tek Gün Görünümü",
        "📊 Yöntem Karşılaştırma",
    ])

    with sekme1:
        ekran_kapasite(demo)

    with sekme2:
        ekran_tek_gun(demo)

    with sekme3:
        ekran_karsilastirma(demo)


if __name__ == "__main__":
    main()
