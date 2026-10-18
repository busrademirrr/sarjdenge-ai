import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

import scenariosRouter from './routes/scenarios.js';
import benchmarkRouter from './routes/benchmark.js';
import simulateRouter from './routes/simulate.js';
import authRouter from './routes/auth.js';
import exportRouter from './routes/export.js';

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

// API Routes
app.use('/api/scenarios', scenariosRouter);
app.use('/api/benchmark-results', benchmarkRouter);
app.use('/api/simulate', simulateRouter);
app.use('/api/auth', authRouter);
app.use('/api/export', exportRouter);

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    app: 'ŞarjDenge AI Decision Support Server',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
  });
});

// Serve frontend static build if available
const clientDist = path.resolve(__dirname, '../client/dist');
app.use(express.static(clientDist));

app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api')) {
    return next();
  }
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
  });
}

export default app;
