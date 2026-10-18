import React, { useState } from 'react';
import { X, ShieldCheck, UserCheck, LogOut, CheckCircle2 } from 'lucide-react';

export default function AuthModal({ session, onUpdateSession, onClose }) {
  const [loading, setLoading] = useState(false);
  const [simName, setSimName] = useState('');
  const [simEmail, setSimEmail] = useState('');

  const handleGuestLogin = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/auth/guest', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        onUpdateSession(data.session);
        onClose();
      }
    } catch (err) {
      alert('Misafir oturumu açılamadı.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSimLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('/api/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mockUser: {
            name: simName || 'Jüri Üyesi',
            email: simEmail || 'juri.evaluator@climathon2026.org',
          },
        }),
      });
      const data = await res.json();
      if (data.success) {
        onUpdateSession(data.session);
        onClose();
      }
    } catch (err) {
      alert('Google simülasyon girişi başarısız.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-md w-full p-6 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">Kullanıcı & Jüri Oturumu</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Current status */}
        <div className="py-4 space-y-4">
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block font-semibold">Mevcut Oturum</span>
            <div className="flex items-center justify-between mt-1">
              <div>
                <span className="text-sm font-bold text-white block">{session?.user?.name || 'Misafir'}</span>
                <span className="text-xs text-slate-400">{session?.user?.email || 'juri@climathon.org'}</span>
              </div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                session?.isGuest
                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              }`}>
                {session?.isGuest ? 'Misafir Modu' : 'Doğrulanmış Jüri'}
              </span>
            </div>
          </div>

          {/* Quick Guest Mode Action */}
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <h4 className="text-xs font-bold text-slate-300 mb-1">Misafir Jüri Modu (Varsayılan & Sıfır Engel)</h4>
            <p className="text-[11px] text-slate-400 mb-3 leading-relaxed">
              Hesap açma, şifre veya OAuth zorunluluğu olmadan tüm simülasyonları, 96 adımlı güç grafiklerini ve araç bazlı kararları doğrudan deneyebilirsiniz.
            </p>
            <button
              onClick={handleGuestLogin}
              disabled={loading}
              className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            >
              Misafir Modunu Etkinleştir
            </button>
          </div>

          {/* Optional Google Login Simulation */}
          <form onSubmit={handleGoogleSimLogin} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2.5">
            <h4 className="text-xs font-bold text-slate-300">Opsiyonel: Google ile Giriş</h4>
            <p className="text-[11px] text-slate-400">
              Google OAuth gizli anahtarları depoya konulmaz; değerlendirme için simüle doğrulanmış profil oluşturabilirsiniz.
            </p>
            <input
              type="text"
              placeholder="Ad Soyad (Örn: Prof. Dr. Ayşe Yılmaz)"
              value={simName}
              onChange={(e) => setSimName(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 text-white rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-emerald-500"
            />
            <input
              type="email"
              placeholder="E-posta (Örn: ayse.yilmaz@climathon.org)"
              value={simEmail}
              onChange={(e) => setSimEmail(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 text-white rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-emerald-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-slate-950 transition font-bold"
            >
              Google Girişini Simüle Et
            </button>
          </form>
        </div>

        <div className="pt-3 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white transition"
          >
            Kapat
          </button>
        </div>
      </div>
    </div>
  );
}
