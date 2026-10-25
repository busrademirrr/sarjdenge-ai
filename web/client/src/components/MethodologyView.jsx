import React from 'react';
import { BookOpen, CheckCircle2, AlertCircle, ShieldCheck, Cpu, GitCommit, Info } from 'lucide-react';

const CONCEPTS = [
  {
    id: 'yp-vs-pct',
    icon: CheckCircle2,
    iconColor: 'text-emerald-700',
    title: 'Yüzde (%) ile Yüzde Puanı (y.p.) Ayrımı',
    summary:
      'İki başarı oranı arasındaki doğrudan aritmetik fark yüzde puanı (y.p.) ile ifade edilir; önkayıtlı hipotez eşiğimiz mutlak Δ ≥ +2,00 y.p. olarak tanımlanmıştır.',
    details: [
      'Yüzde Puanı (y.p.): Örneğin %90 başarıdan %92 başarıya çıkış tam olarak +2,00 y.p. mutlak artıştır.',
      'Göreceli Değişim (%): Oranın kendi üzerindeki büyüme yüzdesidir (%90’dan %92’ye çıkış göreceli %2,22 büyümedir).',
      'Önkayıt Kuralı: Başarı ölçütü Δ ≥ +2,00 y.p. ve %95 güven aralığı alt sınırının 0 üzerinde olmasıdır.',
    ],
  },
  {
    id: 'phantom-reservation',
    icon: AlertCircle,
    iconColor: 'text-amber-700',
    title: 'Gözlenen Davranış İçin Olası Açıklama',
    summary:
      "Güvenli q80 hedefi oturumların yaklaşık %12'sinde (2020 holdout) gerçek ihtiyacın %95'inin altında kalıyor; kullanıcı beyanında bu oran %2,55. Dar kapasitede bu araçlar hedefe ulaşamıyor. Bu, gözlenen farkla uyumlu bir açıklamadır; nedensel olarak kanıtlanmamıştır.",
    details: [
      "Güvenli q80 hedefi oturumların yaklaşık %12'sinde (2020 holdout) gerçek ihtiyacın %95'inin altında kalmaktadır.",
      "Kullanıcı beyanında bu oran yalnızca %2,55 seviyesindedir.",
      "Dar kapasitede bu araçlar hedefe ulaşamamakta olup bu durum gözlenen farkla uyumlu bir açıklamadır; nedensel olarak kanıtlanmamıştır.",
    ],
  },
  {
    id: 'edf-dynamics',
    icon: Cpu,
    iconColor: 'text-emerald-700',
    title: 'EDF Algoritmasının Çalışma Dinamikleri',
    summary:
      'EDF (En Erken Ayrılış Öncelikli), her 15 dakikalık adımda prize bağlı araçları ayrılış terminine göre sıralar ve mevcut kapasiteyi gelecek adımlara rezervasyon kilitlemeden anlık dağıtır.',
    details: [
      'Ayrılışı en yakın araca gücü anında verir, artan gücü sıradaki araca devreder.',
      'Bu değerlendirmede EDF bazı kapasite düzeylerinde yüksek hedef karşılama sonuçları vermiştir.',
      'Algoritmaların performansı kapasite düzeyine ve kullanılan metriğe göre karşılaştırılmalıdır.',
    ],
  },
  {
    id: 'data-separation',
    icon: ShieldCheck,
    iconColor: 'text-emerald-700',
    title: 'Gerçek Saha Verisi vs. Sentetik Model Ayrımı',
    summary:
      'ACN-Data (Caltech ve JPL) gerçek saha telemetrisi ile Türkiye apartman/işyeri otoparkları için kurgulanan parametrik sentetik senaryolar birbirinden kesin olarak ayrılmıştır.',
    details: [
      'Gerçek Saha Verisi: Caltech ve JPL sahalarındaki 2019 ACN-Data ölçümleridir (doğrulama protokolünde 68 gün-saha, 5.207 oturum).',
      'Sentetik Konut/İşyeri Modeli: config/senaryolar.yaml içindeki mühendislik ve modelleme varsayımlarıyla (azami 6,66 kW [sim.PMAX, 208 V, 32 A] soket gücü ve günlük sürüş enerjisi parametreleriyle) kurgulanan simülasyondur; resmî kurum istatistiği değildir.',
    ],
  },
  {
    id: 'live-vs-offline',
    icon: GitCommit,
    iconColor: 'text-emerald-700',
    title: 'Canlı Kuantil Baseline vs. Çevrimdışı ML Modelleri',
    summary:
      'Canlı simülasyon arayüzünde ampirik beyan oranı kuantilleri (q20 süre, q80 enerji) ve HiGHS LP-MPC çözücüsü çalışırken; çevrimdışı deney hattında HGB/GBR kuantil regresyon modelleri değerlendirilmiştir.',
    details: [
      'Canlı Web Servisi (sarjdenge/web_servis.py): 2019 H1 eğitim kesitinden (7.808 oturum) öğrenilen sabit kuantil oranları (q20 = 0,8889 süre, q80 = 0,8446 enerji) kullanılır.',
      'Çevrimdışı Deney Hattı (tahmin.py, modeller.py): HistGradientBoostingRegressor ve GradientBoostingRegressor modelleri 5.315 doğrulama oturumu ve 68 gün-sahadaki 5.207 simülasyon oturumu (fark: 108 oturum) üzerinde test edilmiştir.',
    ],
  },
];

export default function MethodologyView() {
  return (
    <div className="space-y-4">
      {/* 22 Ekim Düzeltme Notu */}
      <div className="bg-blue-50/80 border border-blue-200/90 rounded-xl p-3 sm:p-3.5 text-xs text-blue-900 flex items-center space-x-2.5 shadow-2xs">
        <Info className="w-4 h-4 text-blue-700 shrink-0" />
        <span className="font-medium">
          22 Ekim 2026'da simülasyon girişinde indeksleme hatası bulundu ve düzeltildi; eski sonuçlar korunmuştur, yeniden hesaplanan sonuçlar burada gösterilmektedir.
        </span>
      </div>

      {/* Compact Header */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-4 sm:p-5 shadow-2xs">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 shrink-0">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">
              Metodoloji & Terimler Sözlüğü
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Model çıktıları, hipotez testleri ve simülasyon kavramlarının özet referans kılavuzu
            </p>
          </div>
        </div>
      </div>

      {/* Concept Cards: Title + 1-2 Sentence Summary + Expandable Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {CONCEPTS.map((item) => {
          const IconComponent = item.icon;
          return (
            <div
              key={item.id}
              className={`bg-white border border-slate-200/90 rounded-xl p-4 shadow-2xs flex flex-col justify-between ${
                item.id === 'live-vs-offline' ? 'md:col-span-2' : ''
              }`}
            >
              <div>
                <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm mb-1.5">
                  <IconComponent className={`w-4 h-4 shrink-0 ${item.iconColor}`} />
                  <span>{item.title}</span>
                </div>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                  {item.summary}
                </p>
              </div>

              <details className="mt-3 pt-2.5 border-t border-slate-100 group text-xs text-slate-600">
                <summary className="font-semibold text-emerald-800 hover:text-emerald-900 cursor-pointer flex items-center justify-between list-none">
                  <span>Ayrıntılı Açıklama</span>
                  <span className="text-lg text-slate-400 group-open:rotate-180 transition-transform inline-block leading-none select-none">▾</span>
                </summary>
                <ul className="mt-2 space-y-1.5 text-slate-600 leading-relaxed list-disc pl-4">
                  {item.details.map((line, idx) => (
                    <li key={idx}>{line}</li>
                  ))}
                </ul>
              </details>
            </div>
          );
        })}
      </div>
    </div>
  );
}
