# ŞarjDenge AI — Ön Kayıt 2 (Taze Dönem Test Protokolü)

**Durum: KİLİTLENDİ (Aşama 2 — Veri Hijyeni Kapsamında)**  
**Tarih:** 2026-10-17  
**Hedef Test Dönemi:** 2020-01-01 (dahil) ile 2020-03-01 (hariç) arası ACN-Data (Caltech ve JPL)  

---

## 1. Test Dönemi ve Veri Güvenliği

1. **Hedef Dönem:** `2020-01-01 00:00:00 UTC` ile `2020-03-01 00:00:00 UTC` arasındaki oturumlar.
2. **Kör Deney Dokunulmazlığı:** Bu döneme ait veriler indirilmeden önce tüm veri temizleme kuralları, model mimarileri ve optimizasyon parametreleri dondurulmuştur. Test verisi model seçimi, eşik ayarı veya hiperparametre optimizasyonu için kesinlikle kullanılamaz.
3. **Güvenli İndirme Yolu:** `acn_veri_cek.py` betiği proje köküne yazmayacak şekilde izole edilmiş `data/holdout_2020_01_02/` dizinine yönlendirilecektir. İndirme sonrasında dosyanın SHA-256 özeti kaydedilecek ve ham CSV salt okunur olarak korunacaktır.
4. **Geçmiş Verilerin Durumu:** 2019 yılına ait Ocak–Haziran ve Temmuz–Aralık verileri geliştirme ve doğrulama amacıyla kullanıldığından artık "taze kör test" niteliğinde değildir. 2020 dönemi nihai bağımsız test kümesidir.

---

## 2. Dondurulan Görev ve Metrik Tanımları

### Görev 1: Süre ve Tarihsel Teslim Enerjisi Tahmini (ML)
- **Süre Hedefi:** `sure_dk = (disconnectTime - connectionTime).total_seconds() / 60` (dakika).
- **Enerji Hedefi:** `kWhDelivered` (kWh). Bu değer ACN istasyonunun kısıtlar altında teslim ettiği enerjidir; kullanıcının tam batarya ihtiyacı olduğu iddia edilmeyecek, "tarihsel teslim enerjisi / ihtiyaç göstergesi" olarak sunulacaktır.
- **Kantil Modelleri:** Süre için q20 ve q50; enerji için q50 ve q80.
- **Tahmin Metrikleri:** SMAPE, MAE ve Pinball Loss.
- **Kapsama Kalibrasyonu Hedefi:** 
  - Süre q20 kapsaması: $\approx 0.20$
  - Enerji q80 kapsaması: $0.80 \pm 0.03$ (Tolerans aralığı: $[0.77, 0.83]$)
- **Baseline:** Kullanıcı ilk beyanı (`requestedDeparture_ilk`, `kWhRequested_ilk`). Yalnızca `beyan_var == True` olan oturumlarda eşleştirilmiş olarak kıyaslanır.

### Görev 2: Kapasite Kısıtlı Çizelgeleme ve Karar Desteği (MPC)
- **Simülasyon Adımı:** 15 dakika ($DT\_H = 0.25$ saat).
- **Ayrık Akım Seviyeleri:** 0, 8, 16, 24, 32 A $\times$ 208 V (ACN EVSE seviyeleri).
- **Kapasite Senaryoları:** Günün kontrolsüz tepe gücünün $f \in \{0.5, 0.7, 0.9\}$ katı.
- **Değerlendirme Metrikleri:**
  - `ok`: Zamanında $\ge \%95$ teslim alan araç oranı.
  - `erken_ok`: Erken ayrılan oturumlarda zamanında hedefe ulaşma oranı.
  - `teslim`: Ortalama enerji karşılama oranı ($\text{teslim edilen} / \text{hedef}$).
  - `p10`: En dezavantajlı %10'luk dilimin teslim oranı.
  - `kapasite_ihlali`: Simülasyonda gözlenen kapasite aşımı (sıfır ihlal zorunludur).
- **Belirsizlik:** Günler üzerinden eşleştirilmiş bootstrap %95 güven aralığı ($B = 1000$ tekrar).

---

## 3. Önceden Belirlenmiş Başarı Eşiği ve Hipotez Kuralı

- **Ana Karşılaştırma:** $\Delta = mpc\_tahmin\_guvenli - mpc\_beyan$
- **Başarı Eşiği:** $\Delta \ge +0.02$ (+2 yüzde puan) VE bootstrap %95 GA alt ucu $> 0$.
- **Kural:** Test sonuçları bu eşiği sağlamazsa (`esik_gecti == False`), sonuçlar olduğu gibi dürüstçe raporlanacaktır; geriye dönük eşik veya hipotez değiştirilmeyecektir.
- **Aday 1 (mpc_hibrit_asimetrik) Kuralı:** Aday 1 sonuçları $mpc\_tahmin\_guvenli$ yöntemine göre bir iyileşme olarak raporlanacak; ancak genel referans $mpc\_beyan$ karşısında anlamlı üstünlük göstermiyorsa tüm yöntemlerden üstün olduğu iddia edilmeyecektir.

---

## 4. Zaman Sızıntısı ve İzolasyon Garantileri

1. **Özellik Matrisi Denetimi:** Karar anından sonra belirlenen hiçbir alan (`disconnectTime`, `doneChargingTime`, son kullanıcı girdileri `kWhRequested`, `requestedDeparture`) özellik matrisinde yer almayacaktır.
2. **Kullanıcı Geçmişi Shift Garantisi:** Kullanıcı geçmişi özellikleri (`gecmis_sure`, `gecmis_kwh`, `gecmis_n`) yalnızca karar anından önce fiilen tamamlanmış ($disconnectTime \le connectionTime$) oturumlardan üretilecektir (`strict_shift=True`).
3. **Parametre Sabitleme:** Normalizasyon, kategori kodlamaları ve model ağırlıkları yalnızca geliştirme kümesinde eğitilmiş olarak dondurulacaktır.

---

## 5. Kilit ve İmza Kaydı

- **Veri Hazırlama Kuralları Hash:** [`VERI_HAZIRLAMA_KURALLARI.md`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/VERI_HAZIRLAMA_KURALLARI.md) SHA-256
- **Veri Hijyeni Yapılandırması Hash:** [`data/hijyen.yaml`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/data/hijyen.yaml) SHA-256
- **Test Paketi Durumu:** `tests/test_veri_hijyeni.py` ve `tests/test_cekirdek.py` (22/22 test geçti).
- **Onay Durumu:** Kilitlendi. Test verisi indirme izni bekleniyor.
