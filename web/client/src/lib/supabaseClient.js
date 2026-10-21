import { createClient } from '@supabase/supabase-js';

const env =
  (typeof import.meta !== 'undefined' && import.meta && import.meta.env) ||
  (typeof process !== 'undefined' && process && process.env) ||
  {};

// Hem Vite standart VITE_* hem de Next.js tarz─▒ NEXT_PUBLIC_* de─şi┼şkenlerini destekler
const supabaseUrl =
  env.VITE_SUPABASE_URL ||
  env.NEXT_PUBLIC_SUPABASE_URL ||
  '';

const supabaseAnonKey =
  env.VITE_SUPABASE_ANON_KEY ||
  env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
  '';

// Supabase yap─▒land─▒rmas─▒n─▒n ge├ğerli olup olmad─▒─ş─▒n─▒ do─şrula
export const isSupabaseConfigured = Boolean(
  supabaseUrl &&
  supabaseAnonKey &&
  supabaseUrl.startsWith('https://') &&
  !supabaseUrl.includes('your-project')
);

// Tekil Supabase istemcisi
export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
      },
    })
  : null;

/**
 * Kullan─▒c─▒ ad─▒ veya e-posta adresinden iki harfli profesyonel avatar ├╝retir.
 * ├ûrnek: "B├╝┼şra Demir" -> "BD", "ahmet@gmail.com" -> "AH"
 */
export function getInitials(fullName, email = '') {
  if (fullName && typeof fullName === 'string') {
    const parts = fullName.trim().split(/\s+/).filter(Boolean);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    if (parts.length === 1 && parts[0].length >= 2) {
      return parts[0].slice(0, 2).toUpperCase();
    }
    if (parts.length === 1 && parts[0].length === 1) {
      return parts[0].toUpperCase();
    }
  }

  if (email && typeof email === 'string') {
    const username = email.split('@')[0] || '';
    const clean = username.replace(/[^a-zA-Z0-9]/g, '');
    if (clean.length >= 2) {
      return clean.slice(0, 2).toUpperCase();
    }
    if (clean.length === 1) {
      return clean.toUpperCase();
    }
  }

  return '┼ŞD'; // ┼ŞarjDenge varsay─▒lan─▒
}

/**
 * ┼Şifre yenileme ve OAuth geri d├Ân├╝┼ş adresini belirler.
 */
export function getAuthRedirectUrl() {
  if (typeof window === 'undefined') return '';
  return `${window.location.origin}`;
}
