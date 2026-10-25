import React from 'react';
import { Check } from 'lucide-react';

export default function ScenarioSelector({ scenarios, selectedScenarioId, onSelectScenario }) {
  return (
    <div className="mb-3.5">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
        {scenarios.map((sc) => {
          const isSelected = sc.id === selectedScenarioId;
          const isReal = sc.badgeType === 'real';

          return (
            <button
              type="button"
              key={sc.id}
              onClick={() => onSelectScenario(sc.id)}
              className={`text-left rounded-xl p-3 border transition-all flex flex-col justify-between ${
                isSelected
                  ? 'bg-emerald-50/30 border-emerald-600 ring-1 ring-emerald-600/15'
                  : 'bg-white hover:bg-slate-50/70 border-slate-200/90 hover:border-slate-300'
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-1.5 mb-1.5">
                  <span
                    className={`text-[11px] font-medium px-2 py-0.5 rounded-md ${
                      isReal
                        ? 'bg-blue-50 text-blue-800'
                        : 'bg-amber-50 text-amber-800'
                    }`}
                  >
                    {isReal ? 'ACN Gerçek Saha' : 'Sentetik'}
                  </span>

                  {isSelected && (
                    <span className="w-4 h-4 rounded-full bg-emerald-700 text-white flex items-center justify-center shrink-0">
                      <Check className="w-2.5 h-2.5 stroke-[3]" />
                    </span>
                  )}
                </div>

                <h3 className="font-semibold text-xs sm:text-sm text-slate-900 leading-snug line-clamp-2">
                  {sc.name}
                </h3>
              </div>

              <div className="mt-2 pt-1.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 tabular-nums">
                <span>{sc.sockets} Soket</span>
                <span>•</span>
                <span>{sc.socketPowerKw} kW</span>
                <span>•</span>
                <span>{sc.transformerKw} kW</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
