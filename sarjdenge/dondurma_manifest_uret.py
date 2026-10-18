"""ŞarjDenge AI — Dondurma Manifesti Üretici (İş Paketi F - Holdout Hazırlık).

Bu betik, 2020 taze holdout testi öncesinde mevcut tüm model, simülasyon,
kurallar, yapılandırmalar ve deney tablolarının SHA-256 kriptografik özetlerini
hesaplar ve dondurma manifestini oluşturur.
"""

import hashlib
import pathlib

PROJE_KOK = pathlib.Path(__file__).parent.parent

KONTROL_DOSYALARI = [
    # 1. Ön Kayıt ve Kurallar
    "ONKAYIT_2.md",
    "VERI_HAZIRLAMA_KURALLARI.md",
    "data/hijyen.yaml",
    "config/senaryolar.yaml",
    "data/MANIFEST.md",
    
    # 2. Modeller ve Veri Hattı
    "sarjdenge/modeller.py",
    "sarjdenge/veri_hijyeni.py",
    "sarjdenge/sentetik_v2.py",
    
    # 3. Simülasyon ve Deney Kodları
    "sarjdenge/sim.py",
    "sarjdenge/deney_v2.py",
    "sarjdenge/web_servis.py",
    
    # 4. Korunan Çekirdek Dosyalar
    "sarjdenge/data.py",
    "sarjdenge/tahmin.py",
    "sarjdenge/deney.py",
    "sarjdenge/turkiye.py",
    "sarjdenge/sentetik.py",
    
    # 5. Doğrulanmış Önceki Deney Çıktıları
    "data/deney_tablo_val.csv",
    "data/deney_boot_val.csv",
    "data/deney_tablo_ta.csv",
    "data/deney_boot_ta.csv",
]


def sha256_hesapla(dosya_yolu: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(dosya_yolu, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def manifest_olustur() -> str:
    satirlar = [
        "# ŞarjDenge AI — Dondurulmuş Model ve Kod Manifesti (2020 Holdout Öncesi)",
        "",
        "**Tarih:** 2026-10-17",
        "**Amaç:** 2020-01-01 / 2020-03-01 ACN holdout test verisi çekilmeden ve değerlendirilmeden önce",
        "tüm model ağırlıklarının, kodların, kuralların ve önceki deney sonuçlarının dondurulduğunu belgelemek.",
        "",
        "| Dosya Yolu | Boyut (Byte) | SHA-256 Özeti | Durum |",
        "| :--- | :---: | :--- | :---: |",
    ]

    for rel_path in KONTROL_DOSYALARI:
        tam_yol = PROJE_KOK / rel_path
        if not tam_yol.exists():
            satirlar.append(f"| `{rel_path}` | — | BULUNAMADI | ❌ |")
            continue
        boyut = tam_yol.stat().st_size
        ozet = sha256_hesapla(tam_yol)
        satirlar.append(f"| `{rel_path}` | {boyut:,} | `{ozet}` | DONDURULDU |")

    satirlar.append("")
    satirlar.append("---")
    satirlar.append("### Dondurma ve Kör Test Garantisi")
    satirlar.append("1. Yukarıda listelenen dosyaların hiçbirinde 2020 holdout verisi çekildikten sonra değişiklik yapılamaz.")
    satirlar.append("2. 2020 verisi model seçimi, hiperparametre optimizasyonu veya eşik ayarı için kullanılamaz.")
    satirlar.append("3. Ön kayıtlı ana hipotez kuralı (Δ ≥ +0.02, %95 GA alt ucu > 0, q80 kapsam toleransı %80 ± 3 y.p.) aynen korunur.")
    satirlar.append("")

    icerik = "\n".join(satirlar)
    
    cikti_yolu = PROJE_KOK / "docs" / "DONDURMA_MANIFESTI_2020.md"
    with open(cikti_yolu, "w", encoding="utf-8") as f:
        f.write(icerik)
        
    return icerik


if __name__ == "__main__":
    cikti = manifest_olustur()
    print(cikti)
