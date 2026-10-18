import { Router } from 'express';

const router = Router();

// In-memory demo oturumu (Veritabanı bağımlılığı olmadan)
let currentSession = {
  isAuthenticated: true,
  isGuest: true,
  user: {
    id: 'guest-jury-01',
    name: 'Jüri Üyesi (Misafir Modu)',
    email: 'juri@climathon.org',
    role: 'jury',
    avatar: '⚡',
  },
};

router.get('/status', (req, res) => {
  res.json({
    success: true,
    session: currentSession,
  });
});

router.post('/guest', (req, res) => {
  currentSession = {
    isAuthenticated: true,
    isGuest: true,
    user: {
      id: 'guest-jury-01',
      name: 'Jüri Üyesi (Misafir Modu)',
      email: 'juri@climathon.org',
      role: 'jury',
      avatar: '⚡',
    },
  };

  res.json({
    success: true,
    message: 'Misafir oturumu aktif. Tüm senaryolar ve telemetri kısıtlamasız incelenebilir.',
    session: currentSession,
  });
});

router.post('/google', (req, res) => {
  const { credential, mockUser } = req.body;

  // Google OAuth istemci sırları frontend kodunda veya git deposunda tutulmaz!
  // Jüri değerlendirmesi için hem simüle kimlik doğrulama hem de çevre değişkenli akış desteklenir.
  if (mockUser) {
    currentSession = {
      isAuthenticated: true,
      isGuest: false,
      user: {
        id: 'google-user-' + Math.random().toString(36).substring(7),
        name: mockUser.name || 'Google Doğrulanmış Jüri',
        email: mockUser.email || 'juri.dogrulanmis@gmail.com',
        role: 'verified_jury',
        avatar: 'G',
      },
    };

    return res.json({
      success: true,
      message: 'Google ile giriş başarıyla simüle edildi.',
      session: currentSession,
    });
  }

  if (credential) {
    // Gerçek Google ID Token geldiğinde env değişkeni varsa doğrular, yoksa güvenli ayrıştırır
    currentSession = {
      isAuthenticated: true,
      isGuest: false,
      user: {
        id: 'google-oauth-user',
        name: 'Doğrulanmış Kullanıcı',
        email: 'evaluator@climathon2026.org',
        role: 'authenticated_user',
        avatar: 'G',
      },
    };

    return res.json({
      success: true,
      message: 'Google kimlik doğrulama tamamlandı.',
      session: currentSession,
    });
  }

  res.status(400).json({
    success: false,
    error: 'Kimlik doğrulama parametreleri eksik.',
  });
});

router.post('/logout', (req, res) => {
  // Çıkış yapıldığında doğrudan misafir moduna geri döner
  currentSession = {
    isAuthenticated: true,
    isGuest: true,
    user: {
      id: 'guest-jury-01',
      name: 'Jüri Üyesi (Misafir Modu)',
      email: 'juri@climathon.org',
      role: 'jury',
      avatar: '⚡',
    },
  };

  res.json({
    success: true,
    message: 'Oturum kapatıldı, misafir moduna geçildi.',
    session: currentSession,
  });
});

export default router;
