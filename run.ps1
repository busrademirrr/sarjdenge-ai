# ŞarjDenge AI — Tam Akış (PowerShell)
# Önce: $env:ACN_TOKEN = "anahtarınız"
# ACN verisi olmadan sadece sentetik senaryo + arayüz için: 4. adımı atlayın

# 1) Bağımlılıkları kur
py -m pip install -r requirements.txt

# 2) Testleri çalıştır (hepsi geçmeli)
py -m pytest -q
if ($LASTEXITCODE -ne 0) { Write-Error "Testler başarısız; devam edilmiyor."; exit 1 }

# 3) ACN verisi çek (ACN_TOKEN gerekli; yoksa bu adımı atlayın)
if ($env:ACN_TOKEN) {
    py acn_veri_cek.py
    # ACN deneyi (hızlı: --gun 5; tam çalıştırma için --gun parametresini kaldırın)
    py -W ignore -m sarjdenge.deney --csv acn_oturumlar_v2.csv --gun 5
} else {
    Write-Warning "ACN_TOKEN tanımlanmamış; ACN adımları atlandı."
}

# 4) Türkiye sentetik demo verisi üret -> demo_veri.json
py -W ignore -m sarjdenge.urun --uret --cikti demo_veri.json

# 5) Arayüzü aç
py -m streamlit run arayuz.py
