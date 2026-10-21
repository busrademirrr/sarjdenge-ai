import React, { useState } from 'react';
import { AlertCircle, ChevronDown, ChevronUp, CheckCircle2, Info } from 'lucide-react';

export default function TransparencyBanner() {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl p-4 sm:p-5 shadow-2xs mb-6">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start space-x-3.5">
          <div className="p-2 rounded-lg bg-slate-100 border border-slate-200 text-slate-700 mt-0.5 shrink-0">
            <AlertCircle className="w-5 h-5 text-slate-600" />
          </div>
          <div>
            <div className="flex items-center space-x-2 flex-wrap gap-y-1">
              <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                ├ûnkay─▒tl─▒ Hipotez De─şerlendirmesi
              </span>
              <span className="text-xs sm:text-sm font-bold text-slate-900">
                ├ûnkay─▒tl─▒ hipotez desteklenmedi
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-600 mt-1.5 leading-relaxed max-w-4xl">
              ├ûnkay─▒tl─▒ ba┼şar─▒ ├Âl├ğ├╝t├╝ kar┼ş─▒lanmad─▒: fark─▒n en az +2 y├╝zde puan olmas─▒ ve %95 g├╝ven aral─▒─ş─▒n─▒n alt s─▒n─▒r─▒n─▒n s─▒f─▒r─▒n ├╝zerinde bulunmas─▒ gerekiyordu.
              G├Âzlenen davran─▒┼ş i├ğin olas─▒ a├ğ─▒klama (├ğal─▒┼şma hipotezi), konservatif q80 enerji ve q20 s├╝re tahminlerinin LP-MPC'de kapasiteyi erken ad─▒mlarda belirli ara├ğlara ay─▒rmas─▒d─▒r.
            </p>
          </div>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center space-x-1.5 text-xs text-slate-700 hover:text-slate-900 font-semibold px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 border border-slate-200 transition shrink-0 ml-2"
        >
          <span>{expanded ? 'Kapat' : 'Olas─▒ Mekanizma & Bulgular'}</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-1 md:grid-cols-3 gap-3.5 text-xs text-slate-700">
          {/* Card 1: E┼şle┼ştirilmi┼ş Bootstrap Sonu├ğlar─▒ */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex items-center space-x-2 text-slate-800 font-bold mb-2">
              <Info className="w-4 h-4 shrink-0 text-slate-600" />
              <span>E┼şle┼ştirilmi┼ş Bootstrap (B = 2.000)</span>
            </div>
            <ul className="space-y-1.5 text-slate-600 text-xs">
              <li>ÔÇó <strong className="text-slate-800">f = 0,50:</strong> ╬ö = -0,17 y.p. (%95 GA: [-0,66, +0,28] y.p.)</li>
              <li>ÔÇó <strong className="text-slate-800">f = 0,70:</strong> ╬ö = -0,58 y.p. (%95 GA: [-1,06, -0,10] y.p.)</li>
              <li>ÔÇó <strong className="text-slate-800">f = 0,90:</strong> ╬ö = -0,02 y.p. (%95 GA: [-0,22, +0,17] y.p.)</li>
              <li className="text-slate-700 font-medium pt-1 border-t border-slate-200">S─▒f─▒r hipotezi reddedilemedi. G├╝ven aral─▒klar─▒ s─▒f─▒r─▒ kapsamakta veya alt─▒ndad─▒r.</li>
            </ul>
          </div>

          {/* Card 2: Olas─▒ Mekanizma */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex items-center space-x-2 text-slate-800 font-bold mb-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-slate-600" />
              <span>Olas─▒ Mekanizma (├çal─▒┼şma Hipotezi)</span>
            </div>
            <p className="text-slate-600 text-xs leading-relaxed">
              G├Âzlenen davran─▒┼ş i├ğin olas─▒ a├ğ─▒klama: Y├╝ksek <code className="text-slate-800 bg-slate-200/60 px-1 rounded font-mono text-xs">q80 enerji</code> ve k─▒sa <code className="text-slate-800 bg-slate-200/60 px-1 rounded font-mono text-xs">q20 s├╝re</code> k─▒s─▒tlar─▒n─▒n, LP-MPC ├ğ├Âz├╝c├╝s├╝nde kapasiteyi erken ad─▒mlarda konservatif bi├ğimde belirli ara├ğlara ay─▒rmas─▒d─▒r (hayalet kapasite rezervasyonu).
            </p>
          </div>

          {/* Card 3: De─şerlendirme Bulgusu */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex items-center space-x-2 text-slate-800 font-bold mb-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-slate-600" />
              <span>De─şerlendirme Bulgusu</span>
            </div>
            <p className="text-slate-600 text-xs leading-relaxed">
              Bu de─şerlendirmede EDF baz─▒ kapasite d├╝zeylerinde y├╝ksek hedef kar┼ş─▒lama sonu├ğlar─▒ vermi┼ştir. Algoritmalar─▒n performans─▒ kapasite d├╝zeyine ve kullan─▒lan metri─şe g├Âre kar┼ş─▒la┼şt─▒r─▒lmal─▒d─▒r.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
