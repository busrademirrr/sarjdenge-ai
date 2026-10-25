import React, { useState, useEffect, useRef } from 'react';
import { Cpu, AlertTriangle, CheckCircle2, Info, RefreshCw } from 'lucide-react';
import { ADVISOR_METHOD_META } from '../utils/algorithmMeta.js';

export default function CapacityAdvisor({
  scenarios,
  selectedScenarioId,
  onSelectScenario,
  day,
  onChangeDay,
}) {
  const enableMultiDay = import.meta.env.VITE_ENABLE_MULTIDAY === 'true';
  const [loading, setLoading] = useState(false);
  const [advisorData, setAdvisorData] = useState(null);
  const [error, setError] = useState(null);
  const [isMultiDay, setIsMultiDay] = useState(false);
  const activeControllerRef = useRef(null);

  const currentScenario = scenarios?.find((s) => s.id === selectedScenarioId) || scenarios?.[0];

  const runAdvisor = async (scId = selectedScenarioId, dayVal = day, multiDayMode = isMultiDay) => {
    // 1. Önceki tamamlanmamış isteği iptal et (yarış durumu / race condition koruması)
    if (activeControllerRef.current) {
      activeControllerRef.current.abort();
    }

    const controller = new AbortController();
    activeControllerRef.current = controller;

    setLoading(true);
    setError(null);

    // Makul istemci bekleme süresi: Çok günlü için 210 sn, örnek gün için 40 sn
    const clientTimeoutMs = multiDayMode ? 210000 : 40000;
    let clientTimedOut = false;
    const timeoutId = setTimeout(() => {
      clientTimedOut = true;
      controller.abort();
    }, clientTimeoutMs);

    try {
      const res = await fetch('/api/capacity-advisor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          scenarioId: scId,
          day: dayVal,
          multiDay: multiDayMode,
        }),
      });

      clearTimeout(timeoutId);

      const data = await res.json();
      // Yeni bir istek başladıysa eski yanıtın UI'ı ezmesini önle
      if (activeControllerRef.current !== controller) return;

      if (data.success && data.advisor && !data.advisor.hata) {
        setAdvisorData(data.advisor);
      } else {
        setAdvisorData(null);
        setError(data.error || data.advisor?.hata || 'Kapasite analizi hesaplanamadı.');
      }
    } catch (err) {
      clearTimeout(timeoutId);
      // Başka bir istek başladığı için iptal edildiyse hiçbir hata veya durum değişikliği yapma
      if (err.name === 'AbortError' && !clientTimedOut) {
        return;
      }
      if (activeControllerRef.current !== controller) return;

      setAdvisorData(null);
      if (clientTimedOut) {
        const sec = Math.round(clientTimeoutMs / 1000);
        setError(`Kapasite Danışmanı hesaplaması istemci zaman aşımına uğradı (${sec} sn).`);
      } else {
        console.error('Advisor fetch error:', err);
        setError('Kapasite Danışmanı servisine bağlanırken ağ hatası oluştu.');
      }
    } finally {
      if (activeControllerRef.current === controller) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    if (selectedScenarioId) {
      runAdvisor(selectedScenarioId, day, isMultiDay);
    }
    return () => {
      if (activeControllerRef.current) {
        activeControllerRef.current.abort();
      }
    };
  }, [selectedScenarioId, day, isMultiDay]);

  // Seçilen yöntemin adını temiz göster; eşitlik durumunda orijinal metni koru
  const formatMethodDisplay = (rawName) => {
    if (!rawName) return '—';
    const str = String(rawName);
    if (str.includes('En düşük kapasite')) return str;
    return str.replace(/\s*\(([^)]+)\)/, ' — $1');
  };

  return (
    <div className="space-y-5">
      {/* 1. Belirgin Üst Seçim ve Kontrol Alanı */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 shrink-0 shadow-2xs">
              <Cpu className="w-5 h-5" />
            </div>
            <div className="flex items-center flex-wrap gap-2">
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">
                Canlı Kapasite Danışmanı
              </h2>
              {advisorData && (
                <>
                  <span
                    className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-md text-xs font-medium ${
                      advisorData.sentetik_mi
                        ? 'bg-amber-50 text-amber-800 border border-amber-200/70'
                        : 'bg-blue-50 text-blue-800 border border-blue-200/70'
                    }`}
                  >
                    {advisorData.sentetik_mi ? (
                      <>
                        <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0" />
                        <span>SENTETİK SENARYO (TÜRKİYE VARSAYIMI)</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-3 h-3 text-blue-600 shrink-0" />
                        <span>GERÇEK SAHA VERİSİ (ACN-Data)</span>
                      </>
                    )}
                  </span>

                  {advisorData.acn_kalibrasyonu === false && (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300">
                      ACN kalibrasyonu uygulanmadı
                    </span>
                  )}

                  {advisorData.ornek_gun && !isMultiDay && (
                    <span className="text-xs font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                      Örnek Gün ({advisorData.tarih})
                    </span>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Kontroller: Senaryo + Tarih + Ayrı Çok Günlü Mod Düğmesi + Yeniden Hesapla */}
          <div className="flex flex-wrap items-center gap-2">
            <select
              aria-label="Senaryo Seçimi"
              value={selectedScenarioId}
              onChange={(e) => onSelectScenario(e.target.value)}
              className="bg-slate-50 hover:bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-700 transition min-w-[200px]"
            >
              {scenarios?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>

            {!isMultiDay && (
              <select
                aria-label="Simülasyon Tarihi"
                value={day}
                onChange={(e) => onChangeDay(e.target.value)}
                className="bg-slate-50 hover:bg-white border border-slate-200 rounded-lg px-2.5 py-2 text-xs font-medium text-slate-800 tabular-nums focus:outline-none focus:ring-1 focus:ring-emerald-700 transition w-32"
              >
                {currentScenario?.availableDays?.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                )) || <option value={day}>{day}</option>}
              </select>
            )}

            {/* Ayrı Çok Günlü Mod Düğmesi (Varsayılan Kapalı, VITE_ENABLE_MULTIDAY ile kontrol edilir) */}
            {enableMultiDay && (
            <button
              type="button"
              onClick={() => setIsMultiDay((prev) => !prev)}
              className={`relative inline-flex flex-col items-center justify-center px-3 py-1 rounded-lg border text-xs font-semibold transition ${
                isMultiDay
                  ? 'bg-emerald-50 border-emerald-500 text-emerald-900 shadow-2xs'
                  : 'bg-white hover:bg-slate-50 border-slate-200 text-slate-700'
              }`}
              title="Geniş veri seti üzerinde 20 gün taranır (1–2 dakika sürebilir)"
            >
              <span className="text-[10px] font-medium text-amber-800 bg-amber-100 px-1.5 py-0.2 rounded border border-amber-300 leading-tight mb-0.5">
                1–2 dakika sürebilir
              </span>
              <span className="inline-flex items-center space-x-1">
                <span>Çok Günlü Mod (≥20 Gün)</span>
                {isMultiDay ? (
                  <span className="text-emerald-700 font-bold ml-1 text-[11px]">(Açık)</span>
                ) : (
                  <span className="text-slate-400 font-normal ml-1 text-[11px]">(Kapalı)</span>
                )}
              </span>
            </button>
            )}

            <button
              onClick={() => runAdvisor(selectedScenarioId, day, isMultiDay)}
              disabled={loading}
              className="inline-flex items-center justify-center space-x-2 px-4 py-2 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white rounded-lg text-xs sm:text-sm font-semibold shadow-xs transition whitespace-nowrap"
            >
              <RefreshCw className={`w-4 h-4 shrink-0 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Hesaplanıyor…' : 'Yeniden Hesapla'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Kompakt Yüklenme Durumu */}
      {loading && (
        <div className="bg-white border border-slate-200 rounded-xl py-6 px-4 flex items-center justify-center space-x-2.5 shadow-2xs">
          <RefreshCw className="w-4 h-4 text-emerald-700 animate-spin shrink-0" />
          <span className="text-xs font-semibold text-slate-700">
            {isMultiDay
              ? 'Çok günlü kapasite analizi yürütülüyor (≥20 gün taranıyor, bu işlem 1–2 dakika sürebilir)…'
              : 'Kapasite hesaplanıyor… (Ücretsiz sunucu yavaş olabilir, hesaplama 30–60 sn sürebilir)'}
          </span>
        </div>
      )}

      {/* Hata Durumu */}
      {error && !loading && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-3.5 text-xs text-rose-900 flex items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={() => runAdvisor(selectedScenarioId, day, isMultiDay)}
            className="px-3 py-1 rounded-lg text-xs font-semibold bg-rose-700 text-white shrink-0 hover:bg-rose-800 transition"
          >
            Tekrar Dene
          </button>
        </div>
      )}

      {advisorData && !loading && (
        <>
          {/* 2. Ana Sonuç Paneli: Asgari Trafo Gücü ve Seçilen Yöntem Odaklı */}
          <div className="bg-white border border-slate-200/90 rounded-xl p-5 sm:p-6 shadow-2xs">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center tabular-nums">
              {/* Birincil Sonuç: Asgari Trafo Gücü + Seçilen Yöntem */}
              <div className="lg:col-span-8 flex flex-col sm:flex-row sm:items-center gap-5 sm:gap-8 lg:border-r border-slate-100 lg:pr-6">
                <div className="shrink-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Asgari Trafo Gücü
                    </span>
                    <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                      ±{advisorData.arama_cozunurlugu_kw ?? 0.5} kW
                    </span>
                  </div>
                  <div className="flex items-baseline space-x-1.5 mt-1.5">
                    <span className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-none">
                      {advisorData.onerilen_asgari_kapasite_kw ?? '—'}
                    </span>
                    <span className="text-lg sm:text-xl text-slate-600 font-bold">kW</span>
                  </div>
                </div>

                <div className="sm:border-l border-slate-100 sm:pl-7">
                  <span className="text-xs font-medium text-slate-500 block">
                    {advisorData.esitlik_var ? 'Eşit Minimum Yöntemler' : 'En Düşük Kapasiteli Yöntem'}
                  </span>
                  <span className="text-base sm:text-lg font-bold text-emerald-800 mt-1 block leading-snug">
                    {formatMethodDisplay(advisorData.onerilen_yontem)}
                  </span>
                  <span className="text-xs text-slate-500 mt-1 block">
                    {advisorData.esitlik_var
                      ? (advisorData.esit_yontemler || []).map(formatMethodDisplay).join(' • ')
                      : `${advisorData.arac_sayisi} araçlık seçili kesit sonucu`}
                  </span>
                </div>
              </div>

              {/* İkincil Bilgiler: Kontrolsüz Pik, Trafo Durumu ve Karar Kriteri */}
              <div className="lg:col-span-4 space-y-1.5 text-xs">
                <div className="flex items-center justify-between text-slate-500">
                  <span>Kontrolsüz Pik</span>
                  <span className="font-semibold text-slate-700">{advisorData.kontrolsuz_tepe_kw} kW</span>
                </div>
                {advisorData.trafo_durumu && (
                  <div className="flex items-center justify-between text-slate-500">
                    <span>Trafo Durumu</span>
                    <span className="font-semibold text-slate-800">{advisorData.trafo_durumu}</span>
                  </div>
                )}
                <div className="flex items-center justify-between text-slate-500">
                  <span>Karar Kriteri</span>
                  <span className="font-medium text-slate-600">≥%95 Oran & Azami 1 Kaçırma</span>
                </div>
              </div>
            </div>
            {(advisorData.kapasite_ozet_metni || advisorData.fiziksel_ulasilamaz_arac_sayisi > 0) && (
              <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500">
                {advisorData.kapasite_ozet_metni && <span>{advisorData.kapasite_ozet_metni}</span>}
                {advisorData.fiziksel_ulasilamaz_arac_sayisi > 0 && (
                  <span className="text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200/70">
                    {advisorData.fiziksel_ulasilamaz_arac_sayisi} araç kalış süresi azlığı nedeniyle tam dolamaz (Sınırsız trafo gücünde bile P_max=7.4 kW soket sınırı)
                  </span>
                )}
              </div>
            )}
          </div>

          {/* 3. Dört Algoritma Kartı: Daha Görünür ve Dengeli Boyut */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {advisorData.yontemler.map((y) => {
              const isLowest = advisorData.esit_yontem_kodlari?.includes(y.kod);
              const meta = ADVISOR_METHOD_META[y.kod] || { symbol: '●', tag: 'Algoritma', color: y.renk || '#059669' };

              return (
                <div
                  key={y.kod}
                  className={`rounded-xl p-5 flex flex-col justify-between transition min-h-[152px] ${
                    isLowest
                      ? 'bg-emerald-50/20 border-2 border-emerald-600 shadow-xs'
                      : 'bg-white border border-slate-200/90 shadow-2xs hover:border-slate-300'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2.5">
                      <span className="inline-flex items-center space-x-1.5 text-xs font-medium text-slate-500 truncate">
                        <span
                          className="w-2.5 h-2.5 rounded-full shrink-0"
                          style={{ backgroundColor: meta.color }}
                        />
                        <span className="truncate">{meta.tag}</span>
                      </span>
                      {isLowest && (
                        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-md bg-emerald-100/80 text-emerald-900 border border-emerald-300 leading-none shrink-0">
                          {advisorData.esitlik_var ? 'Eşit Min.' : 'En Düşük'}
                        </span>
                      )}
                    </div>

                    <h3 className="text-sm sm:text-base font-bold text-slate-900 leading-snug">
                      {y.ad}
                    </h3>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-200/60 flex items-baseline justify-between tabular-nums">
                    <div>
                      <span className="text-xs font-medium text-slate-500 block">Asgari Güç</span>
                      {y.arac_ozeti && (
                        <span className="text-[11px] text-slate-500 block mt-0.5">
                          {y.arac_ozeti} {y.kacirilan_arac_sayisi > 0 ? `(${y.kacirilan_arac_sayisi} kaçırılan)` : ''}
                        </span>
                      )}
                      {(y.fiziksel_imkansiz_arac_sayisi !== undefined || advisorData.fiziksel_imkansiz_arac_sayisi !== undefined) && (
                        <span className="text-[11px] text-slate-500 block mt-0.5">
                          fiziksel olarak imkânsız araç: {y.fiziksel_imkansiz_arac_sayisi ?? advisorData.fiziksel_imkansiz_arac_sayisi ?? 0}
                        </span>
                      )}
                      {y.monoton_degil && (
                        <span className="text-[10px] text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200 block mt-1">
                          Kalıcı geçiş: {y.ilk_kalici_gecis_kw} kW
                        </span>
                      )}
                    </div>
                    <div className="flex items-baseline space-x-1">
                      <span
                        className={`text-2xl sm:text-3xl font-extrabold tracking-tight ${
                          isLowest ? 'text-emerald-900' : 'text-slate-900'
                        }`}
                      >
                        {y.asgari_kapasite_kw !== null ? y.asgari_kapasite_kw : 'Erişilemedi'}
                      </span>
                      {y.asgari_kapasite_kw !== null && (
                        <span className="text-xs sm:text-sm font-bold text-slate-600">kW</span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Çok Günlü Dağılım Matrisi (≥20 Gün) */}
          {advisorData.cok_gunlu_analiz && (
            <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3.5">
                <div>
                  <h3 className="text-sm sm:text-base font-bold text-slate-900">
                    Çok Günlü Kapasite Dağılımı ({advisorData.cok_gunlu_analiz.toplam_gun} Gün / Tohum)
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Farklı gün koşullarındaki asgari trafo gücü dağılımı (Medyan, p10 ve p90 sınırları)
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs sm:text-sm tabular-nums">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-600 bg-slate-50/80">
                      <th className="py-2.5 px-4 font-semibold">Yöntem</th>
                      <th className="py-2.5 px-4 text-right font-semibold" title="Yöntemin asgari bir trafo gücü ile hedefi (≥%95 araç doyumu) karşılayabildiği gün sayısı ve oranı">
                        Başarılı Gün Oranı (%)
                      </th>
                      <th className="py-2.5 px-4 text-right font-semibold">Medyan Güç</th>
                      <th className="py-2.5 px-4 text-right font-semibold">p10 (Düşük Talep)</th>
                      <th className="py-2.5 px-4 text-right font-semibold">p90 (Yüksek Sıkışıklık)</th>
                      <th className="py-2.5 px-4 text-right font-semibold">Min – Maks</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {advisorData.cok_gunlu_analiz.yontemler.map((yo) => {
                      const meta = ADVISOR_METHOD_META[yo.kod] || { color: '#059669' };
                      const yuzde =
                        yo.erisme_orani_yuzde !== undefined
                          ? Math.round(yo.erisme_orani_yuzde)
                          : Math.round(((yo.orneklem_sayisi || 0) / (advisorData.cok_gunlu_analiz.toplam_gun || 1)) * 100);
                      return (
                        <tr key={yo.kod} className="hover:bg-slate-50/80 transition">
                          <td className="py-2.5 px-4 font-semibold text-slate-900">
                            <span style={{ color: meta.color }}>{yo.ad}</span>
                          </td>
                          <td className="py-2.5 px-4 text-right text-slate-700 font-medium">
                            {yo.orneklem_sayisi !== undefined
                              ? `${yo.orneklem_sayisi}/${advisorData.cok_gunlu_analiz.toplam_gun} (%${yuzde})`
                              : '—'}
                          </td>
                          <td className="py-2.5 px-4 text-right font-bold text-slate-900">
                            {yo.medyan_kw !== null ? `${yo.medyan_kw} kW` : '—'}
                          </td>
                          <td className="py-2.5 px-4 text-right text-slate-700">
                            {yo.p10_kw !== null ? `${yo.p10_kw} kW` : '—'}
                          </td>
                          <td className="py-2.5 px-4 text-right text-slate-700">
                            {yo.p90_kw !== null ? `${yo.p90_kw} kW` : '—'}
                          </td>
                          <td className="py-2.5 px-4 text-right text-slate-500">
                            {yo.min_kw !== null && yo.maks_kw !== null ? `${yo.min_kw} – ${yo.maks_kw} kW` : '—'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Dağılım Tablosu Metrik ve Başarı Açıklaması */}
              <div className="mt-3 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600 leading-relaxed flex items-start space-x-2">
                <Info className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p>
                    <strong>Yüzde ve Başarı Tanımı:</strong> Tablodaki <code>(%30, %100 vb.)</code> yüzdeleri; ilgili yöntemin asgari bir trafo kapasitesiyle hedefi (≥%95 araç doyumu VE en fazla 1 kaçırılan araç) karşılayabildiği günlerin oranını belirtir.
                  </p>
                  <p>
                    <strong>Medyan ve Dağılım Hesabı:</strong> Medyan, p10 ve p90 güç değerleri <u>yalnızca bu başarılı günler üzerinden</u> hesaplanır. Fiziksel kısıtlar veya aşırı talep nedeniyle hedefin kurtarılamadığı başarısız günlerde sonlu bir asgari güç bulunamadığından kapasite dağılımına dahil edilmez (eksik gün olarak gösterilir).
                  </p>
                </div>
              </div>

              {advisorData.cok_gunlu_analiz.haric_tutulan_gun_sayisi > 0 && (
                <div className="mt-2.5 text-[11px] text-amber-700 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-200">
                  Not: {advisorData.cok_gunlu_analiz.haric_tutulan_gun_sayisi} gün veri yetersizliği veya aşırı kısıt nedeniyle analize dahil edilemedi.
                </div>
              )}
            </div>
          )}

          {/* 4. Kapasite Tarama Matrisi: Düzenli Satır Aralıkları ve Başlıklar */}
          <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3.5">
              <h3 className="text-sm sm:text-base font-bold text-slate-900">
                Kapasite Tarama Matrisi
              </h3>
              <span className="text-xs font-medium text-slate-500 tabular-nums">
                Hedef karşılama eşiği: ≥%95,0
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs sm:text-sm tabular-nums">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-600 bg-slate-50/80">
                    <th className="py-3 px-4 font-semibold whitespace-nowrap">Aday Kapasite</th>
                    {advisorData.yontemler.map((y) => {
                      const meta = ADVISOR_METHOD_META[y.kod] || { symbol: '●', color: y.renk };
                      return (
                        <th key={y.kod} className="py-3 px-4 text-center font-semibold">
                          <span style={{ color: meta.color }} className="font-bold inline-flex items-center space-x-1.5">
                            <span aria-hidden="true">{meta.symbol}</span>
                            <span>{y.ad}</span>
                          </span>
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {advisorData.aday_kapasiteler_kw.map((capKw, idx) => {
                    const isMinRow =
                      Math.abs(Number(capKw) - Number(advisorData.onerilen_asgari_kapasite_kw)) < 0.05;
                    return (
                      <tr
                        key={capKw}
                        className={`hover:bg-slate-50/80 transition ${
                          isMinRow ? 'bg-emerald-50/20' : ''
                        }`}
                      >
                        <td className="py-3 px-4 font-bold text-slate-900 whitespace-nowrap">
                          <div className="flex items-center space-x-2">
                            <span>{capKw} kW</span>
                            {isMinRow && (
                              <span className="px-2 py-0.5 text-[11px] font-bold bg-emerald-100/80 text-emerald-900 border border-emerald-300 rounded">
                                ÖNERİLEN ASGARİ
                              </span>
                            )}
                          </div>
                        </td>

                        {advisorData.yontemler.map((y) => {
                          const step =
                            y.tarama.find((t) => Math.abs(Number(t.kapasite_kw) - Number(capKw)) < 0.05) ||
                            y.tarama[idx];
                          const ok = step?.yeterli;
                          return (
                            <td key={y.kod} className="py-3 px-4 text-center whitespace-nowrap">
                              <span
                                className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-md text-xs font-semibold ${
                                  ok
                                    ? 'bg-emerald-50 text-emerald-900 border border-emerald-200'
                                    : 'text-slate-500'
                                }`}
                              >
                                <span aria-hidden="true">{ok ? '✓' : '—'}</span>
                                <span>%{step?.hedef_karsilama_yuzde ?? '—'}</span>
                              </span>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* 5. Açılır Kapsam Sınırları ve Yöntem Açıklamaları */}
          <details className="bg-white border border-slate-200/90 rounded-xl p-4 shadow-2xs group text-xs text-slate-600">
            <summary className="font-semibold text-slate-800 cursor-pointer flex items-center justify-between list-none">
              <span className="flex items-center space-x-2">
                <Info className="w-4 h-4 text-emerald-700 shrink-0" />
                <span>Kapsam Sınırları ve Yöntem Açıklamaları</span>
              </span>
              <span className="text-lg text-slate-400 group-open:rotate-180 transition-transform inline-block leading-none select-none">▾</span>
            </summary>
            <div className="mt-2.5 pt-2.5 border-t border-slate-100 space-y-2 leading-relaxed">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {advisorData.yontemler.map((y) => (
                  <div key={y.kod} className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <strong className="text-slate-800 block">{y.ad}</strong>
                    <span className="text-slate-500">{y.aciklama}</span>
                  </div>
                ))}
              </div>
              <p className="text-slate-500">
                <strong>Kapsam ve Veri Kaynağı:</strong> {advisorData.veri_kaynagi_etiketi}. Sonuçlar yalnızca seçili günlük kesitin ({advisorData.arac_sayisi} araç) simülasyon çıktısıdır; genel algoritma üstünlüğü kanıtı olarak yorumlanamaz.
              </p>
            </div>
          </details>
        </>
      )}
    </div>
  );
}
