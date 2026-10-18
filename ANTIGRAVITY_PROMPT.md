Sen bu projede kıdemli Python geliştiricisi, makine öğrenmesi mühendisi ve ürün geliştiricisi olarak çalışacaksın.
Proje: ŞarjDenge AI (Climathon 2026). Önce PROJE_BAGLAMI.md ve README.md dosyalarını oku; bağlam orada.

ÇALIŞMA DÜZENİ: İKİ AŞAMA
AŞAMA 1 (şimdi): Yalnızca incele. Hiçbir dosyayı oluşturma, değiştirme veya silme.
1. Klasör yapısını ve tüm dosyaları oku. Hiçbir dosyanın var olduğunu varsayma.
2. `py -m pip install -r requirements.txt` ve `py -m pytest -q` çalıştır; çıktıyı olduğu gibi raporla.
3. Bana şunu sun: mevcut durum, çalışan/çalışmayan parçalar, riskler, eksikler ve uygulama planın
   (en fazla 5 adım, her adımda hangi dosyaları değiştireceğin ve nedeni).
4. Onayımı bekle. Onaydan sonra AŞAMA 2'ye geç.

AŞAMA 2 (onaydan sonra), küçük adımlarla, her adımdan sonra test çalıştır ve sonucu bildir:
A. Test ve paket: tests/ genişlet (sim.py, data.py, turkiye.py, urun.py için); README'yi
   çalıştırma talimatlarıyla güncelle. Mevcut testleri silme.
B. Arayüz (Streamlit tercih; kurulumu en az olanı seç, nedenini yaz). Türkçe. Üç ekran:
   1) Kapasite karar aracı: kullanıcı soket sayısı ve toplam kapasiteyi (kW) seçer; "hedefin %95'i
      zamanında" için yeterli kapasite yöntemlere göre (statik, fcfs, mpc, sarjdenge) gösterilir.
   2) Tek gün görünümü: zaman ekseninde toplam güç + kapasite çizgisi; araç araç plan tablosu
      (giriş/ayrılış, tahmini ayrılış aralığı, hedef kWh, teslim edilen kWh, durum).
   3) Yöntem karşılaştırma: kapasiteye göre zamanında hedefe ulaşan araç oranı; kapasite
      yetersizliğinin hangi saatlerde oluştuğunu gösteren rapor.
   Veri kaynağı yalnızca demo_veri.json (python -m sarjdenge.urun --uret ile üretilir) ve
   sonuclar.md / gunluk_sonuclar.csv. Dosya yoksa örnek sonuç UYDURMA; açık uyarı göster.
C. Tekrarlanabilirlik: run.ps1'i çalışır hâle getir (veri çek -> deney -> demo verisi -> arayüz).

KESİN KURALLAR
1. `sarjdenge/sim.py`, `deney.py`, `data.py`, `tahmin.py` içindeki mantığı DEĞİŞTİRME. Hata veya
   iyileştirme görürsen önce bana yaz (hangi satır, neden, etkisi); onayım olmadan dokunma.
   `deney.py` içindeki önceden yazılmış karar kuralı (ANA, REF, ESIK) sabit kalır.
2. ACN API anahtarı, parola veya gizli bilgi koda/dosyaya yazılmaz. Yalnızca `ACN_TOKEN` ortam değişkeni.
3. Arayüzdeki HER sayı sonuç dosyalarından okunur. Kodda elle yazılmış sonuç sayısı olmaz.
4. Gerçek (ACN) ile sentetik (Türkiye) sonuçları birbirinden ayır. Sentetik her yerde
   "Sentetik senaryo, ölçüm değil" etiketiyle görünür. "Saha sonucu", "kanıtlandı" gibi ifadeler yasak.
5. Hedefleri veya eşikleri sonuçlara göre sonradan değiştirme. Gerçek deney sonucunu yorumlama;
   sadece okunabilir şekilde göster. Yorumu ben yapacağım.
6. Çalıştırmadığın testi başarılı gösterme. Hata varsa tam hata metniyle yaz.
7. Gereksiz dosya, bağımlılık veya özellik ekleme. Önce çalışan, test edilebilir MVP.
8. Kod değişikliğinden önce hangi dosyaları değiştireceğini ve nedenini açıkla.
9. Arayüz ve dokümantasyon Türkçe.

KABUL ÖLÇÜTLERİ
- `py -m pytest -q` geçer ve çıktısı bana raporlanır.
- Arayüz yerelde açılır, demo_veri.json yoksa açık uyarı verir, varsa grafikleri çizer.
- Sentetik etiketi her ekranda görünür; kodda sabit sonuç sayısı yoktur.
- Çekirdek dosyalarda (sim, deney, data, tahmin) onaysız hiçbir değişiklik yoktur.
