import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

import scenariosRouter from './routes/scenarios.js';
import benchmarkRouter from './routes/benchmark.js';
import simulateRouter, { executePythonSimulate } from './routes/simulate.js';
import capacityAdvisorRouter, { executePythonAdvisor } from './routes/capacityAdvisor.js';
import exportRouter from './routes/export.js';
import { executeWithCacheAndSingleFlight } from './utils/calculationCache.js';

dotenv.config();

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Request logger
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    if (process.env.NODE_ENV !== 'test') {
      console.log(`[API] ${req.method} ${req.originalUrl} -> ${res.statusCode} (${duration}ms)`);
    }
  });
  next();
});

// Health check (Anında 200 döner, hiçbir hesaplama tetiklemez)
app.get('/healthz', (req, res) => res.status(200).send('OK'));
app.get('/api/healthz', (req, res) => res.status(200).send('OK'));
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    app: 'ŞarjDenge AI Decision Support Server',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
  });
});

// API Routes
app.use('/api/scenarios', scenariosRouter);
app.use('/api/benchmark-results', benchmarkRouter);
app.use('/api/simulate', simulateRouter);
app.use('/api/capacity-advisor', capacityAdvisorRouter);
app.use('/api/export', exportRouter);

// Serve frontend static build if available
const clientDist = path.resolve(__dirname, '../client/dist');
app.use(express.static(clientDist, {
  setHeaders: (res, filePath) => {
    if (filePath.endsWith('.html')) {
      res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
    }
  }
}));

app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api')) {
    return next();
  }
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
  res.sendFile(path.join(clientDist, 'index.html'), err => {
    if (err) {
      res.status(200).send(`
        <!DOCTYPE html>
        <html>
        <head><title>ŞarjDenge AI Backend</title></head>
        <body style="font-family: sans-serif; padding: 40px; text-align: center;">
          <h2>⚡ ŞarjDenge AI API Servisi Çalışıyor</h2>
          <p>Frontend geliştirme sunucusu port 5173'te çalışmaktadır.</p>
          <p><a href="/api/scenarios">/api/scenarios</a> • <a href="/api/benchmark-results">/api/benchmark-results</a></p>
        </body>
        </html>
      `);
    }
  });
});

// Global Error Handler
app.use((err, req, res, next) => {
  console.error('[API Error]:', err);
  res.status(500).json({
    success: false,
    error: 'Sunucu tarafında bir hata meydana geldi.',
    details: err.message,
  });
});

const isTest = process.env.NODE_ENV === 'test' || process.argv.some(arg => arg.includes('test'));

if (!isTest) {
  app.listen(PORT, () => {
    console.log(`⚡ ŞarjDenge AI Backend http://localhost:${PORT} üzerinde dinliyor.`);

    // Arka plan ön-ısıtma (Warm-up): /healthz bundan bağımsız anında döner.
    // Sırayla varsayılan simülasyon ve tek günlük danışman çalıştırılıp LRU önbelleğe alınır.
    setTimeout(async () => {
      console.log('[Warm-up] Arka planda varsayılan senaryolar önbelleğe alınıyor...');
      try {
        const simParams = { scenarioId: 'isyeri_gunduz', f: 0.5, day: '2026-03-10' };
        await executeWithCacheAndSingleFlight('simulate', simParams, () => executePythonSimulate(simParams));
        console.log('[Warm-up] Varsayılan simülasyon önbelleğe alındı.');

        const advParams = { scenarioId: 'isyeri_gunduz', day: '2026-03-10' };
        await executeWithCacheAndSingleFlight('capacityAdvisor', advParams, () => executePythonAdvisor(advParams));
        console.log('[Warm-up] Varsayılan Kapasite Danışmanı önbelleğe alındı.');
        console.log('[Warm-up] Ön-ısıtma tamamlandı. İlk kullanıcı istekleri anında (1ms) yanıtlanacak.');
      } catch (warmErr) {
        console.warn('[Warm-up] Arka plan ön-ısıtma sırasında uyarı (isteğe bağlı adım):', warmErr.message);
      }
    }, 1000);
  });
}

export default app;
