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
                Önkayıtlı Hipotez Değerlendirmesi
              </span>
              <span className="text-xs sm:text-sm font-bold text-slate-900">
                Önkayıtlı hipotez desteklenmedi
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-600 mt-1.5 leading-relaxed max-w-4xl">
              Önkayıtlı başarı ölçütü karşılanmadı: farkın en az +2 yüzde puan olması ve %95 güven aralığının alt sınırının sıfırın üzerinde bulunması gerekiyordu.
              Gözlenen davranış için olası açıklama (çalışma hipotezi), konservatif q80 enerji ve q20 süre tahminlerinin LP-MPC'de kapasiteyi erken adımlarda belirli araçlara ayırmasıdır.
            </p>
          </div>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center space-x-1.5 text-xs text-slate-700 hover:text-slate-900 font-semibold px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 border border-slate-200 transition shrink-0 ml-2"
        >
          <span>{expanded ? 'Kapat' : 'Olası Mekanizma & Bulgular'}</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-1 md:grid-cols-3 gap-3.5 text-xs text-slate-700">
          {/* Card 1: Eşleştirilmiş Bootstrap Sonuçları */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex items-center space-x-2 text-slate-800 font-bold mb-2">
              <Info className="w-4 h-4 shrink-0 text-slate-600" />
              <span>Eşleştirilmiş Bootstrap (B = 2.000)</span>
            </div>
            <ul className="space-y-1.5 text-slate-600 text-xs">
              <li>• <strong className="text-slate-800">f = 0,50:</strong> Δ = -0,17 y.p. (%95 GA: [-0,66, +0,28] y.p.)</li>
              <li>• <strong className="text-slate-800">f = 0,70:</strong> Δ = -0,58 y.p. (%95 GA: [-1,06, -0,10] y.p.)</li>
              <li>• <strong className="text-slate-800">f = 0,90:</strong> Δ = -0,02 y.p. (%95 GA: [-0,22, +0,17] y.p.)</li>
              <li className="text-slate-700 font-medium pt-1 border-t border-slate-200">Önkayıtlı ölçüt karşılanmadı: f=0,5 ve 0,7'de fark negatif, f=0,9'da sıfırdan ayırt edilemiyor.</li>
            </ul>
          </div>

          {/* Card 2: Gözlenen Davranış İçin Olası Açıklama */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex items-center space-x-2 text-slate-800 font-bold mb-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-slate-600" />
              <span>Gözlenen Davranış İçin Olası Açıklama</span>
            </div>
            <p className="text-slate-600 text-xs leading-relaxed">
              Güvenli q80 hedefi oturumların yaklaşık %12'sinde (2020 holdout) gerçek ihtiyacın %95'inin altında kalıyor; kullanıcı beyanında bu oran %2,55. Dar kapasitede bu araçlar hedefe ulaşamıyor. Bu, gözlenen farkla uyumlu bir açıklamadır; nedensel olarak kanıtlanmamıştır.
            </p>
          </div>

          {/* Card 3: Değerlendirme Bulgusu */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex items-center space-x-2 text-slate-800 font-bold mb-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-slate-600" />
              <span>Değerlendirme Bulgusu</span>
            </div>
            <p className="text-slate-600 text-xs leading-relaxed">
              Bu değerlendirmede EDF bazı kapasite düzeylerinde yüksek hedef karşılama sonuçları vermiştir. Algoritmaların performansı kapasite düzeyine ve kullanılan metriğe göre karşılaştırılmalıdır.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
