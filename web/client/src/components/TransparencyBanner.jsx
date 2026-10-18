import React, { useState } from 'react';
import { AlertCircle, ChevronDown, ChevronUp, CheckCircle2, Info, Sparkles } from 'lucide-react';

export default function TransparencyBanner() {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-slate-900/90 border border-amber-500/30 rounded-2xl p-4 sm:p-5 shadow-lg shadow-amber-950/10 mb-6">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start space-x-3.5">
          <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/25 text-amber-400 mt-0.5 shrink-0">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2 flex-wrap gap-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
                Bilimsel Şeffaflık Bildirimi
              </span>
              <span className="text-xs sm:text-sm font-bold text-white">
                Ön Kayıtlı Ana Hipotez: Desteklenmedi (H₀ Korundu)
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1.5 leading-relaxed max-w-4xl">
              Ön kayıt edilen <code className="text-amber-200 bg-slate-950 px-1.5 py-0.5 rounded border border-amber-500/20 font-mono text-[11px]">Δ = mpc_tahmin_guvenli - mpc_beyan ≥ +2,00 y.p.</code> eşiği sağlanamamıştır.
              Tahmin destekli güvenli MPC, şebeke kapasitesini konservatif biçimde geleceğe rezerve ettiği için filo genelinde üstünlük sağlayamamış; termin odaklı <strong className="text-emerald-400 font-semibold">EDF (Earliest Deadline First) algoritması</strong> tüm kısıt düzeylerinde en yüksek başarıyı elde etmiştir.
            </p>
          </div>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center space-x-1.5 text-xs text-amber-300 hover:text-amber-200 font-medium px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/25 transition shrink-0 ml-2"
        >
          <span>{expanded ? 'Kapat' : 'Fiziksel Mekanizma & Kanıt'}</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-amber-500/20 grid grid-cols-1 md:grid-cols-3 gap-3.5 text-xs text-slate-300">
          {/* Card 1: Eşleştirilmiş Bootstrap Sonuçları */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
            <div className="flex items-center space-x-2 text-amber-400 font-bold mb-2">
              <Info className="w-4 h-4 shrink-0" />
              <span>Eşleştirilmiş Bootstrap (B = 2.000)</span>
            </div>
            <ul className="space-y-1.5 text-slate-400 text-[11px]">
              <li>• <strong className="text-slate-200">f = 0,50:</strong> Δ = -0,17 y.p. (%95 GA: [-0,66, +0,28] y.p.)</li>
              <li>• <strong className="text-slate-200">f = 0,70:</strong> Δ = -0,58 y.p. (%95 GA: [-1,06, -0,10] y.p.)</li>
              <li>• <strong className="text-slate-200">f = 0,90:</strong> Δ = -0,02 y.p. (%95 GA: [-0,22, +0,17] y.p.)</li>
              <li className="text-amber-300/90 pt-1 border-t border-slate-800/80">Tüm güven aralıkları sıfırı kapsamakta veya sıfırın altında kalmaktadır.</li>
            </ul>
          </div>

          {/* Card 2: Fiziksel Mekanizma */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
            <div className="flex items-center space-x-2 text-rose-400 font-bold mb-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>Hayalet Kapasite Rezervasyonu</span>
            </div>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              Modelin yüksek <code className="text-slate-200 bg-slate-900 px-1 rounded">q80 enerji</code> hedefini kısa <code className="text-slate-200 bg-slate-900 px-1 rounded">q20 süre</code> penceresinde tamamlama kısıtı, MPC çözücüsünün mevcut gücü geleceğe kilitlemesine yol açmıştır. Araçlar beklenen sürede ayrılmadığında kilitlenen kapasite atıl kalmış, diğer araçlar güçsüz bırakılmıştır.
            </p>
          </div>

          {/* Card 3: Neden EDF Kazandı? */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
            <div className="flex items-center space-x-2 text-emerald-400 font-bold mb-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Neden EDF Kazandı?</span>
            </div>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              EDF geleceğe rezervasyon tutmaz. Yaklaşan ayrılış terminine göre gücü anlık dağıtarak o anki ayrılabilir şarj kapasitesini her adımda %100 kullanır. Erken ayrılan araçlarda <strong className="text-emerald-300">79,0%–89,0% başarı</strong> ve <strong className="text-emerald-300">p10 = 94,0%–98,0% adillik</strong> sağlamıştır.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
