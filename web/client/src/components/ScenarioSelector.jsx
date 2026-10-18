import React from 'react';
import { Building2, Home, Layers, Database, Sparkles, Check } from 'lucide-react';

export default function ScenarioSelector({ scenarios, selectedScenarioId, onSelectScenario }) {
  const getIcon = (id) => {
    switch (id) {
      case 'isyeri_gunduz':
        return <Building2 className="w-4 h-4 text-sky-400" />;
      case 'apartman_gece':
        return <Home className="w-4 h-4 text-indigo-400" />;
      case 'karma':
        return <Layers className="w-4 h-4 text-purple-400" />;
      case 'acn_gercek_val':
      case 'acn_gercek_ta':
        return <Database className="w-4 h-4 text-emerald-400" />;
      default:
        return <Sparkles className="w-4 h-4 text-amber-400" />;
    }
  };

  return (
    <div className="space-y-3 mb-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xs font-bold tracking-wider text-slate-300 uppercase">
            1. Şarj Senaryosu Seçimi
          </h2>
          <p className="text-xs text-slate-400">
            Farklı otopark kullanım modelleri; gerçek saha telemetrisi (ACN-Data) ve doğrulanmış sentetik senaryolar olarak etiketlenmiştir.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {scenarios.map((sc) => {
          const isSelected = sc.id === selectedScenarioId;
          const isReal = sc.badgeType === 'real';

          return (
            <div
              key={sc.id}
              onClick={() => onSelectScenario(sc.id)}
              className={`relative cursor-pointer rounded-2xl p-4 border transition-all ${
                isSelected
                  ? 'bg-slate-900 border-emerald-500/80 shadow-md shadow-emerald-500/10 ring-1 ring-emerald-500/40'
                  : 'bg-slate-900/60 hover:bg-slate-900 border-slate-800 hover:border-slate-700/80'
              }`}
            >
              {/* Top Row: Icon + Badge + Selection Check */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <div className="p-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 shrink-0">
                    {getIcon(sc.id)}
                  </div>
                  <span
                    className={`inline-block text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-md border ${
                      isReal
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                    }`}
                  >
                    {isReal ? 'Saha Verisi (ACN)' : 'Sentetik Model'}
                  </span>
                </div>

                {isSelected && (
                  <div className="w-5 h-5 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center shrink-0">
                    <Check className="w-3 h-3 stroke-[3]" />
                  </div>
                )}
              </div>

              {/* Title & Subtitle */}
              <h3 className="font-bold text-sm text-white">{sc.name}</h3>
              <p className="text-[11px] text-slate-400 mt-0.5 mb-2">{sc.subName}</p>

              {/* Description */}
              <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                {sc.description}
              </p>

              {/* Infrastructure Stats Footer */}
              <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                <span>{sc.sockets} Soket</span>
                <span className="text-slate-600">•</span>
                <span>{sc.socketPowerKw} kW AC</span>
                <span className="text-slate-600">•</span>
                <span title="Tesisin anma trafo kapasitesi">Tesis Trafosu: {sc.transformerKw} kW</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
