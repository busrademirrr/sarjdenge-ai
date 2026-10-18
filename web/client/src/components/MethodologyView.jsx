import React from 'react';
import { BookOpen, CheckCircle2, AlertCircle, ShieldCheck, Cpu, GitCommit } from 'lucide-react';

export default function MethodologyView() {
  return (
    <div className="space-y-6">
      {/* Introduction */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-xl">
        <div className="flex items-center space-x-3 mb-3">
          <BookOpen className="w-5 h-5 text-emerald-400 shrink-0" />
          <h2 className="text-base sm:text-lg font-bold text-white">
            ŞarjDenge AI — Bilimsel Metodoloji, Terimler ve Hipotez Sözlüğü
          </h2>
        </div>
        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
          Bu karar destek sistemi, Climathon 2026 kapsamında otoparklardaki dinamik trafo ve şarj gücü kapasite kısıtları altında elektrikli araç şarjını yönetmek amacıyla geliştirilmiştir. Aşağıdaki kılavuz; jüri heyetinin model çıktılarını, hipotez testlerini ve fiziksel simülasyon dinamiklerini tam bir bilimsel şeffaflıkla değerlendirmesini sağlar.
        </p>
      </div>

      {/* Grid of Key Concepts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Concept 1: Yüzde vs Yüzde Puanı */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center space-x-2 text-emerald-400 font-bold text-xs sm:text-sm mb-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>Yüzde (%) ile Yüzde Puanı (y.p.) Ayrımı</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Metriklerimizin karşılaştırılmasında oransal değişim ile mutlak fark kesin olarak ayrılmıştır:
          </p>
          <ul className="mt-2.5 space-y-1.5 text-xs text-slate-400">
            <li>• <strong className="text-slate-200">Yüzde Puanı (y.p. / p.p.):</strong> İki başarı oranı arasındaki doğrudan aritmetik farktır. Örneğin %90 başarıdan %92 başarıya çıkış tam olarak <span className="text-emerald-400 font-mono font-semibold">+2,00 y.p.</span> mutlak artıştır.</li>
            <li>• <strong className="text-slate-200">Göreceli Değişim (%):</strong> Oranın kendi üzerindeki büyüme yüzdesidir (%90'dan %92'ye çıkış göreceli %2,22 büyümedir).</li>
            <li>• <strong className="text-slate-200">Ön Kayıt Kuralı:</strong> Hipotez eşiğimiz mutlak <code className="text-amber-300 bg-slate-950 px-1.5 py-0.5 rounded border border-amber-500/20 font-mono text-[11px]">Δ ≥ +2,00 y.p.</code> olarak tanımlanmıştır.</li>
          </ul>
        </div>

        {/* Concept 2: Hayalet Kapasite Rezervasyonu */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center space-x-2 text-rose-400 font-bold text-xs sm:text-sm mb-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>Hayalet Kapasite Rezervasyonu (Çalışma Hipotezi)</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Tahmin destekli güvenli MPC'nin ana hipotezde geride kalmasının fiziksel temelidir:
          </p>
          <p className="mt-2 text-xs text-slate-400 leading-relaxed">
            Model, erken ayrılma riskine karşı süreyi konservatif biçimde kısa (<code className="text-slate-200 bg-slate-950 px-1 py-0.5 rounded">q20 süre</code>) ve enerjiyi yüksek (<code className="text-slate-200 bg-slate-950 px-1 py-0.5 rounded">q80 enerji</code>) tahmin etmiştir. MPC optimizasyon çözücüsü, bu varsayılan gelecekteki yoğun şarjı garanti etmek için mevcut adımlarda ayrılabilir kapasiteyi kilitler. Ancak araçlar çoğunlukla tahmin edilenden daha uzun süre kaldığı veya daha az enerjiye ihtiyaç duyduğu için rezerve edilen kapasite kullanılmaz; o esnada otoparkta bekleyen diğer araçlar gereksiz yere güçsüz bırakılır.
          </p>
        </div>

        {/* Concept 3: Neden EDF Algoritması Kazandı? */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center space-x-2 text-sky-400 font-bold text-xs sm:text-sm mb-2">
            <Cpu className="w-4 h-4 shrink-0" />
            <span>Neden En Erken Termin (EDF) Algoritması Üstündür?</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            EDF (Earliest Deadline First), şebeke kapasitesini paylaştırırken hiçbir araca gelecekteki adımlar için hayali kapasite saklamaz:
          </p>
          <ul className="mt-2.5 space-y-1.5 text-xs text-slate-400">
            <li>• Her 15 dakikalık adımda prize bağlı araçları ayrılış terminine göre sıralar.</li>
            <li>• Ayrılışı en yakın araca azami gücü anında verir, artan gücü sıradaki araca devreder.</li>
            <li>• Kapasiteyi anlık olarak %100 kullandığı için erken ayrılan sürücülerde <strong className="text-emerald-300">79,0%–89,0% başarı</strong> ve p10 adillikte <strong className="text-emerald-300">94,0%–98,0% oranına</strong> ulaşmıştır.</li>
          </ul>
        </div>

        {/* Concept 4: Veri Ayrımı ve Sentetik vs Saha */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center space-x-2 text-purple-400 font-bold text-xs sm:text-sm mb-2">
            <ShieldCheck className="w-4 h-4 shrink-0" />
            <span>Gerçek Saha Verisi vs Sentetik Model Ayrımı</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Projede veri kaynakları kesin bir etik kuralla birbirinden ayrılmıştır:
          </p>
          <ul className="mt-2.5 space-y-1.5 text-xs text-slate-400">
            <li>• <strong className="text-emerald-400">Gerçek Saha Verisi:</strong> Caltech ve JPL sahalarındaki ACN-Data 2019 ölçümleridir. 68 gün ve 5.207 oturumdan oluşur.</li>
            <li>• <strong className="text-amber-400">Sentetik Konut/İşyeri Modeli:</strong> Türkiye apartman otoparklarında henüz açık saha telemetrisi bulunmadığı için EPDK mevzuatı, Togg T10X katalogları ve şehir içi sürüş istatistikleriyle kurgulanmış parametrik simülasyondur. Kesinlikle gerçek ölçüm gibi sunulmaz.</li>
          </ul>
        </div>
      </div>

      {/* Excluded Sessions Reconciliation Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center space-x-2 mb-2 text-white font-bold text-xs sm:text-sm">
          <GitCommit className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Örneklem Açıklaması: 5.315 Doğrulama Oturumu vs 5.207 Simülasyon Oturumu</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          İş Paketi C'de ML modelleri toplam <strong>5.315 oturum</strong> üzerinde doğrulanmıştır. İş Paketi D'deki simülasyonda ise toplam <strong>5.207 oturum</strong> yer almaktadır.
        </p>
        <div className="mt-2.5 p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-300 font-mono">
          5.315 (Toplam Doğrulama) - 5.207 (Simülasyon Oturumu) = 108 Dışlanan Seyrek Oturum
        </div>
        <p className="text-xs text-slate-400 mt-2.5 leading-relaxed">
          <strong className="text-slate-300">Dışlama Sebebi:</strong> Deney koşucusu (<code className="text-slate-300 bg-slate-950 px-1 py-0.5 rounded">deney_v2.py</code>), günlük aktif araç sayısı 8'den az olan seyrek günleri (<code className="text-slate-300 bg-slate-950 px-1 py-0.5 rounded">min_arac_gunluk=8</code>) elemiştir. Bir günde sadece 2-3 araç bağlandığında şarj gücü tavanına asla yaklaşılmadığı için sıkışıklık oluşmaz ve algoritmaların performans farkı ölçülemez.
        </p>
      </div>
    </div>
  );
}
