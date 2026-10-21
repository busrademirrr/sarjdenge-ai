import React, { useState } from 'react';
import {
  X,
  Lock,
  Mail,
  User,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  ArrowLeft,
  Shield,
  Zap,
} from 'lucide-react';
import { supabase, isSupabaseConfigured, getAuthRedirectUrl } from '../lib/supabaseClient.js';

export default function AuthModal({
  isOpen,
  onClose,
  initialView = 'signin',
  onAuthSuccess,
}) {
  const [view, setView] = useState(initialView); // 'signin' | 'signup' | 'forgot' | 'reset'
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Form alanlar─▒
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  if (!isOpen) return null;

  const resetForm = () => {
    setErrorMsg('');
    setSuccessMsg('');
    setPassword('');
    setConfirmPassword('');
  };

  const switchView = (newView) => {
    resetForm();
    setView(newView);
  };

  // 1. E-posta ve ┼Şifre ile Giri┼ş
  const handleSignIn = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (!email.trim() || !password) {
      setErrorMsg('L├╝tfen e-posta adresinizi ve ┼şifrenizi girin.');
      return;
    }

    if (!isSupabaseConfigured || !supabase) {
      setErrorMsg(
        'Supabase kimlik do─şrulama servisi hen├╝z yap─▒land─▒r─▒lmam─▒┼ş. L├╝tfen .env.local dosyas─▒ndaki Supabase URL ve anahtar─▒n─▒ kontrol edin.'
      );
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });

      if (error) {
        if (error.message.includes('Invalid login credentials')) {
          setErrorMsg('E-posta adresi veya ┼şifre hatal─▒. L├╝tfen bilgilerinizi kontrol edin.');
        } else if (error.message.includes('Email not confirmed')) {
          setErrorMsg('E-posta adresiniz hen├╝z do─şrulanmam─▒┼ş. L├╝tfen gelen kutunuzu kontrol edin.');
        } else {
          setErrorMsg(error.message || 'Giri┼ş yap─▒lamad─▒.');
        }
        return;
      }

      if (data?.session) {
        setSuccessMsg('Giri┼ş ba┼şar─▒l─▒! Oturumunuz a├ğ─▒l─▒yorÔÇĞ');
        setTimeout(() => {
          onAuthSuccess?.(data.session);
          onClose();
        }, 500);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Giri┼ş s─▒ras─▒nda beklenmeyen bir a─ş hatas─▒ olu┼ştu.');
    } finally {
      setLoading(false);
    }
  };

  // 2. Yeni Hesap Kayd─▒
  const handleSignUp = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (!fullName.trim()) {
      setErrorMsg('L├╝tfen ad─▒n─▒z─▒ ve soyad─▒n─▒z─▒ girin.');
      return;
    }
    if (!email.trim()) {
      setErrorMsg('L├╝tfen ge├ğerli bir e-posta adresi girin.');
      return;
    }
    if (!password || password.length < 6) {
      setErrorMsg('┼Şifreniz en az 6 karakter uzunlu─şunda olmal─▒d─▒r.');
      return;
    }
    if (password !== confirmPassword) {
      setErrorMsg('Girdi─şiniz ┼şifreler e┼şle┼şmiyor. L├╝tfen tekrar kontrol edin.');
      return;
    }

    if (!isSupabaseConfigured || !supabase) {
      setErrorMsg(
        'Supabase kimlik do─şrulama servisi yap─▒land─▒r─▒lmam─▒┼ş. L├╝tfen ortam de─şi┼şkenlerini kontrol edin.'
      );
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: {
          data: {
            full_name: fullName.trim(),
          },
          emailRedirectTo: getAuthRedirectUrl(),
        },
      });

      if (error) {
        if (error.message.includes('already registered')) {
          setErrorMsg('Bu e-posta adresi zaten kay─▒tl─▒. L├╝tfen giri┼ş yap─▒n.');
        } else {
          setErrorMsg(error.message || 'Kay─▒t i┼şlemi ba┼şar─▒s─▒z oldu.');
        }
        return;
      }

      // E-posta onay─▒ kapal─▒ysa oturum do─şrudan olu┼şur
      if (data?.session) {
        setSuccessMsg('Hesab─▒n─▒z ba┼şar─▒yla olu┼şturuldu! Y├ÂnlendiriliyorsunuzÔÇĞ');
        setTimeout(() => {
          onAuthSuccess?.(data.session);
          onClose();
        }, 600);
      } else {
        // E-posta onay─▒ a├ğ─▒ksa kullan─▒c─▒ya bildir
        setSuccessMsg(
          'Kay─▒t ba┼şar─▒l─▒! Hesab─▒n─▒z─▒ aktifle┼ştirmek i├ğin l├╝tfen e-posta adresinize g├Ânderilen do─şrulama ba─şlant─▒s─▒na t─▒klay─▒n.'
        );
      }
    } catch (err) {
      setErrorMsg(err.message || 'Kay─▒t s─▒ras─▒nda bir hata olu┼ştu.');
    } finally {
      setLoading(false);
    }
  };

  // 3. ┼Şifremi Unuttum (E-posta Talebi)
  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (!email.trim()) {
      setErrorMsg('L├╝tfen kay─▒tl─▒ e-posta adresinizi girin.');
      return;
    }

    if (!isSupabaseConfigured || !supabase) {
      setErrorMsg('Supabase ba─şlant─▒s─▒ bulunamad─▒.');
      return;
    }

    setLoading(true);
    try {
      const redirectUrl = `${getAuthRedirectUrl()}/#reset-password`;
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: redirectUrl,
      });

      if (error) {
        setErrorMsg(error.message || '┼Şifre s─▒f─▒rlama ba─şlant─▒s─▒ g├Ânderilemedi.');
        return;
      }

      setSuccessMsg(
        '┼Şifre s─▒f─▒rlama ba─şlant─▒s─▒ e-posta adresinize g├Ânderildi. L├╝tfen gelen kutunuzu (ve spam klas├Âr├╝n├╝) kontrol edin.'
      );
    } catch (err) {
      setErrorMsg(err.message || 'Ba─şlant─▒ g├Ânderilirken hata olu┼ştu.');
    } finally {
      setLoading(false);
    }
  };

  // 4. Yeni ┼Şifreyi Kaydetme (Kurtarma Ak─▒┼ş─▒)
  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (!password || password.length < 6) {
      setErrorMsg('Yeni ┼şifre en az 6 karakter olmal─▒d─▒r.');
      return;
    }
    if (password !== confirmPassword) {
      setErrorMsg('Yeni ┼şifreler birbiriyle e┼şle┼şmiyor.');
      return;
    }

    if (!isSupabaseConfigured || !supabase) {
      setErrorMsg('Supabase istemcisi haz─▒r de─şil.');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await supabase.auth.updateUser({
        password,
      });

      if (error) {
        setErrorMsg(error.message || '┼Şifre g├╝ncellenemedi. Ba─şlant─▒n─▒n s├╝resi dolmu┼ş olabilir.');
        return;
      }

      setSuccessMsg('┼Şifreniz ba┼şar─▒yla g├╝ncellendi! Yeni ┼şifrenizle giri┼ş yapabilirsiniz.');
      setTimeout(() => {
        if (data?.user) {
          onAuthSuccess?.({ user: data.user });
        }
        switchView('signin');
      }, 1500);
    } catch (err) {
      setErrorMsg(err.message || '┼Şifre g├╝ncellenirken hata olu┼ştu.');
    } finally {
      setLoading(false);
    }
  };

  // 5. Ger├ğek Google OAuth Giri┼şi
  const handleGoogleOAuth = async () => {
    setErrorMsg('');
    setSuccessMsg('');

    if (!isSupabaseConfigured || !supabase) {
      setErrorMsg(
        'Supabase yap─▒land─▒r─▒lmam─▒┼ş. Google ile giri┼ş i├ğin VITE_SUPABASE_URL ve VITE_SUPABASE_ANON_KEY gereklidir.'
      );
      return;
    }

    setLoading(true);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: getAuthRedirectUrl(),
        },
      });

      if (error) {
        setErrorMsg(
          `Google OAuth ba┼şlat─▒lamad─▒: ${error.message}. L├╝tfen Supabase Dashboard'da Google sa─şlay─▒c─▒s─▒n─▒n ve redirect URL'inin tan─▒ml─▒ oldu─şunu do─şrulay─▒n.`
        );
      }
    } catch (err) {
      setErrorMsg(err.message || 'Google ile giri┼ş s─▒ras─▒nda bir hata olu┼ştu.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Kullan─▒c─▒ Giri┼şi ve Kay─▒t"
        className="bg-white border border-slate-200/90 rounded-2xl max-w-md w-full p-6 sm:p-7 shadow-2xl transition-all"
      >
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
                <Zap className="w-4 h-4 fill-emerald-600 stroke-emerald-600" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">┼ŞarjDenge AI</h3>
                <p className="text-xs text-slate-500">Elektrikli Ara├ğ Ak─▒ll─▒ ┼Şarj & Kapasite Y├Ânetimi</p>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Pencereyi Kapat"
            className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* View Tabs (Sadece Signin & Signup i├ğin) */}
        {(view === 'signin' || view === 'signup') && (
          <div className="grid grid-cols-2 gap-1 p-1 bg-slate-100 rounded-xl my-4">
            <button
              type="button"
              onClick={() => switchView('signin')}
              className={`py-2 text-xs font-semibold rounded-lg transition text-center ${
                view === 'signin'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              Giri┼ş Yap
            </button>
            <button
              type="button"
              onClick={() => switchView('signup')}
              className={`py-2 text-xs font-semibold rounded-lg transition text-center ${
                view === 'signup'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              Hesap Olu┼ştur
            </button>
          </div>
        )}

        {/* Forgot Password Header */}
        {view === 'forgot' && (
          <div className="my-4">
            <button
              type="button"
              onClick={() => switchView('signin')}
              className="inline-flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-900 mb-2 font-medium"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Giri┼ş Ekran─▒na D├Ân</span>
            </button>
            <h4 className="text-sm font-bold text-slate-900">┼Şifrenizi mi Unuttunuz?</h4>
            <p className="text-xs text-slate-500 mt-0.5">
              Kay─▒tl─▒ e-posta adresinizi girin; size g├╝venli bir ┼şifre s─▒f─▒rlama ba─şlant─▒s─▒ g├Ânderelim.
            </p>
          </div>
        )}

        {/* Reset Password Header */}
        {view === 'reset' && (
          <div className="my-4">
            <h4 className="text-sm font-bold text-slate-900">Yeni ┼Şifre Belirleyin</h4>
            <p className="text-xs text-slate-500 mt-0.5">
              Kurtarma ba─şlant─▒s─▒ do─şruland─▒. L├╝tfen yeni ┼şifrenizi girin.
            </p>
          </div>
        )}

        {/* Feedback Alerts */}
        {errorMsg && (
          <div
            role="alert"
            className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-2"
          >
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
            <span className="leading-relaxed">{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div
            role="status"
            className="mb-4 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-start space-x-2"
          >
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 mt-0.5" />
            <span className="leading-relaxed">{successMsg}</span>
          </div>
        )}

        {/* Form 1: Giri┼ş Yap (SignIn) */}
        {view === 'signin' && (
          <form onSubmit={handleSignIn} className="space-y-3.5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">E-posta Adresi</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ornek@sirket.com"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-700 focus:border-emerald-700"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-semibold text-slate-700">┼Şifre</label>
                <button
                  type="button"
                  onClick={() => switchView('forgot')}
                  className="text-xs font-medium text-emerald-800 hover:text-emerald-950 hover:underline"
                >
                  ┼Şifremi unuttum
                </button>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="ÔÇóÔÇóÔÇóÔÇóÔÇóÔÇóÔÇóÔÇó"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-9 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-700 focus:border-emerald-700"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? '┼Şifreyi gizle' : '┼Şifreyi g├Âster'}
                  className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600 p-0.5"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center justify-center space-x-1.5"
            >
              {loading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              <span>{loading ? 'Giri┼ş Yap─▒l─▒yorÔÇĞ' : 'Giri┼ş Yap'}</span>
            </button>
          </form>
        )}

        {/* Form 2: Kay─▒t Ol (SignUp) */}
        {view === 'signup' && (
          <form onSubmit={handleSignUp} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Ad Soyad</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="B├╝┼şra Demir"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-700 focus:border-emerald-700"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">E-posta Adresi</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="busra.demir@sirket.com"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-700 focus:border-emerald-700"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">┼Şifre (En az 6 karakter)</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="ÔÇóÔÇóÔÇóÔÇóÔÇóÔÇóÔÇóÔÇó"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-9 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-700 focus:border-emerald-700"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? '┼Şifreyi gizle' : '┼Şifreyi g├Âster'}
                  className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600 p-0.5"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">┼Şifre Tekrar─▒</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="ÔÇóÔÇóÔÇóÔÇóÔÇóÔÇóÔÇóÔÇó"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-9 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-700 focus:border-emerald-700"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  aria-label={showConfirmPassword ? '┼Şifreyi gizle' : '┼Şifreyi g├Âster'}
                  className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600 p-0.5"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center justify-center space-x-1.5 mt-2"
            >
              {loading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              <span>{loading ? 'Hesap Olu┼şturuluyorÔÇĞ' : 'Hesap Olu┼ştur'}</span>
            </button>
          </form>
        )}

        {/* Form 3: ┼Şifremi Unuttum (Forgot) */}
        {view === 'forgot' && (
          <form onSubmit={handleForgotPassword} className="space-y-3.5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Kay─▒tl─▒ E-posta Adresi</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ornek@sirket.com"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-700 focus:border-emerald-700"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center justify-center space-x-1.5"
            >
              {loading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              <span>{loading ? 'G├ÂnderiliyorÔÇĞ' : 'S─▒f─▒rlama Ba─şlant─▒s─▒ G├Ânder'}</span>
            </button>
          </form>
        )}

        {/* Form 4: Yeni ┼Şifre Belirle (Reset) */}
        {view === 'reset' && (
          <form onSubmit={handleUpdatePassword} className="space-y-3.5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Yeni ┼Şifre</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="En az 6 karakter"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-9 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-700 focus:border-emerald-700"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? '┼Şifreyi gizle' : '┼Şifreyi g├Âster'}
                  className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600 p-0.5"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Yeni ┼Şifre Tekrar─▒</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="┼Şifreyi tekrar yaz─▒n"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-9 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-700 focus:border-emerald-700"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  aria-label={showConfirmPassword ? '┼Şifreyi gizle' : '┼Şifreyi g├Âster'}
                  className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600 p-0.5"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center justify-center space-x-1.5"
            >
              {loading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              <span>{loading ? 'KaydediliyorÔÇĞ' : '┼Şifreyi Kaydet'}</span>
            </button>
          </form>
        )}

        {/* Divider & Google OAuth Option (Signin / Signup modunda) */}
        {(view === 'signin' || view === 'signup') && (
          <div className="mt-4 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={handleGoogleOAuth}
              disabled={loading}
              className="w-full py-2.5 px-4 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition flex items-center justify-center space-x-2"
            >
              {/* Google G Logo SVG */}
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.66v3.05h3.9c2.28-2.1 3.645-5.2 3.645-9.15z"
                />
                <path
                  fill="#34A853"
                  d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.9-3.05c-1.08.72-2.45 1.16-4.03 1.16-3.1 0-5.74-2.1-6.68-4.93H1.26v3.15C3.26 21.36 7.36 24 12 24z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.32 14.27c-.24-.73-.38-1.51-.38-2.27s.14-1.54.38-2.27V6.58H1.26C.46 8.18 0 9.99 0 12s.46 3.82 1.26 5.42l4.06-3.15z"
                />
                <path
                  fill="#EA4335"
                  d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.36 0 3.26 2.64 1.26 6.58l4.06 3.15c.94-2.83 3.58-4.98 6.68-4.98z"
                />
              </svg>
              <span>Google ile Devam Et</span>
            </button>

            {/* Misafir Olarak Devam Et Butonu */}
            <div className="mt-3 text-center">
              <button
                type="button"
                onClick={onClose}
                className="text-xs text-slate-500 hover:text-slate-800 font-medium hover:underline"
              >
                Giri┼ş yapmadan devam et (Demo Modu)
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
