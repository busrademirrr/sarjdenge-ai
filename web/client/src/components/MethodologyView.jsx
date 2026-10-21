import React from 'react';
import { BookOpen, CheckCircle2, AlertCircle, ShieldCheck, Cpu, GitCommit } from 'lucide-react';

const CONCEPTS = [
  {
    id: 'yp-vs-pct',
    icon: CheckCircle2,
    iconColor: 'text-emerald-700',
    title: 'Y├╝zde (%) ile Y├╝zde Puan─▒ (y.p.) Ayr─▒m─▒',
    summary:
      '─░ki ba┼şar─▒ oran─▒ aras─▒ndaki do─şrudan aritmetik fark y├╝zde puan─▒ (y.p.) ile ifade edilir; ├Ânkay─▒tl─▒ hipotez e┼şi─şimiz mutlak ╬ö ÔëÑ +2,00 y.p. olarak tan─▒mlanm─▒┼şt─▒r.',
    details: [
      'Y├╝zde Puan─▒ (y.p.): ├ûrne─şin %90 ba┼şar─▒dan %92 ba┼şar─▒ya ├ğ─▒k─▒┼ş tam olarak +2,00 y.p. mutlak art─▒┼şt─▒r.',
      'G├Âreceli De─şi┼şim (%): Oran─▒n kendi ├╝zerindeki b├╝y├╝me y├╝zdesidir (%90ÔÇÖdan %92ÔÇÖye ├ğ─▒k─▒┼ş g├Âreceli %2,22 b├╝y├╝medir).',
      '├ûnkay─▒t Kural─▒: Ba┼şar─▒ ├Âl├ğ├╝t├╝ ╬ö ÔëÑ +2,00 y.p. ve %95 g├╝ven aral─▒─ş─▒ alt s─▒n─▒r─▒n─▒n 0 ├╝zerinde olmas─▒d─▒r.',
    ],
  },
  {
    id: 'phantom-reservation',
    icon: AlertCircle,
    iconColor: 'text-amber-700',
    title: 'Hayalet Kapasite Rezervasyonu (├çal─▒┼şma Hipotezi)',
    summary:
      'Konservatif q20 s├╝re ve q80 enerji tahminlerinin, LP-MPC ├ğ├Âz├╝c├╝s├╝nde erken ad─▒mlarda kapasiteyi belirli ara├ğlara ay─▒rarak di─şer ara├ğlar─▒n ┼şarj─▒n─▒ geciktirmi┼ş olabilece─şi de─şerlendirilmektedir.',
    details: [
      'Model, erken ayr─▒lma riskine kar┼ş─▒ kal─▒┼ş s├╝resini k─▒sa (q20) ve enerji talebini y├╝ksek (q80) tahmin eder.',
      'LP-MPC ├ğ├Âz├╝c├╝s├╝ bu varsay─▒lan aciliyeti kar┼ş─▒lamak i├ğin erken ad─▒mlarda kapasiteyi belirli ara├ğlara y├Ânlendirir.',
      'Bu a├ğ─▒klama kan─▒tlanm─▒┼ş nedensellik de─şil, sim├╝lasyon bulgular─▒yla uyumlu bir ├ğal─▒┼şma hipotezidir.',
    ],
  },
  {
    id: 'edf-dynamics',
    icon: Cpu,
    iconColor: 'text-emerald-700',
    title: 'EDF Algoritmas─▒n─▒n ├çal─▒┼şma Dinamikleri',
    summary:
      'EDF (En Erken Ayr─▒l─▒┼ş ├ûncelikli), her 15 dakikal─▒k ad─▒mda prize ba─şl─▒ ara├ğlar─▒ ayr─▒l─▒┼ş terminine g├Âre s─▒ralar ve mevcut kapasiteyi gelecek ad─▒mlara rezervasyon kilitlemeden anl─▒k da─ş─▒t─▒r.',
    details: [
      'Ayr─▒l─▒┼ş─▒ en yak─▒n araca g├╝c├╝ an─▒nda verir, artan g├╝c├╝ s─▒radaki araca devreder.',
      'Bu de─şerlendirmede EDF baz─▒ kapasite d├╝zeylerinde y├╝ksek hedef kar┼ş─▒lama sonu├ğlar─▒ vermi┼ştir.',
      'Algoritmalar─▒n performans─▒ kapasite d├╝zeyine ve kullan─▒lan metri─şe g├Âre kar┼ş─▒la┼şt─▒r─▒lmal─▒d─▒r.',
    ],
  },
  {
    id: 'data-separation',
    icon: ShieldCheck,
    iconColor: 'text-emerald-700',
    title: 'Ger├ğek Saha Verisi vs. Sentetik Model Ayr─▒m─▒',
    summary:
      'ACN-Data (Caltech ve JPL) ger├ğek saha telemetrisi ile T├╝rkiye apartman/i┼şyeri otoparklar─▒ i├ğin kurgulanan parametrik sentetik senaryolar birbirinden kesin olarak ayr─▒lm─▒┼şt─▒r.',
    details: [
      'Ger├ğek Saha Verisi: Caltech ve JPL sahalar─▒ndaki 2019 ACN-Data ├Âl├ğ├╝mleridir (do─şrulama protokol├╝nde 68 g├╝n, 5.207 oturum).',
      'Sentetik Konut/─░┼şyeri Modeli: config/senaryolar.yaml i├ğindeki m├╝hendislik ve modelleme varsay─▒mlar─▒yla (tipik 11/22 kW AC g├╝├ğ ve g├╝nl├╝k s├╝r├╝┼ş enerjisi parametreleriyle) kurgulanan sim├╝lasyondur; resm├« kurum istatisti─şi de─şildir.',
    ],
  },
  {
    id: 'live-vs-offline',
    icon: GitCommit,
    iconColor: 'text-emerald-700',
    title: 'Canl─▒ Kuantil Baseline vs. ├çevrimd─▒┼ş─▒ ML Modelleri',
    summary:
      'Canl─▒ sim├╝lasyon aray├╝z├╝nde ampirik beyan oran─▒ kuantilleri (q20 s├╝re, q80 enerji) ve HiGHS LP-MPC ├ğ├Âz├╝c├╝s├╝ ├ğal─▒┼ş─▒rken; ├ğevrimd─▒┼ş─▒ deney hatt─▒nda HGB/GBR kuantil regresyon modelleri de─şerlendirilmi┼ştir.',
    details: [
      'Canl─▒ Web Servisi (sarjdenge/web_servis.py): 2019 H1 e─şitim kesitinden (7.808 oturum) ├Â─şrenilen sabit kuantil oranlar─▒ (q20 = 0,8889 s├╝re, q80 = 0,8446 enerji) kullan─▒l─▒r.',
      '├çevrimd─▒┼ş─▒ Deney Hatt─▒ (tahmin.py, modeller.py): HistGradientBoostingRegressor ve GradientBoostingRegressor modelleri 5.315 do─şrulama oturumu ve 68 s─▒k─▒┼ş─▒k g├╝ndeki 5.207 sim├╝lasyon oturumu (fark: 108 oturum) ├╝zerinde test edilmi┼ştir.',
    ],
  },
];

export default function MethodologyView() {
  return (
    <div className="space-y-4">
      {/* Compact Header */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-4 sm:p-5 shadow-2xs">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 shrink-0">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">
              Metodoloji & Terimler S├Âzl├╝─ş├╝
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Model ├ğ─▒kt─▒lar─▒, hipotez testleri ve sim├╝lasyon kavramlar─▒n─▒n ├Âzet referans k─▒lavuzu
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
                  <span>Ayr─▒nt─▒l─▒ A├ğ─▒klama</span>
                  <span className="text-slate-400 group-open:rotate-180 transition-transform">Ôû¥</span>
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
