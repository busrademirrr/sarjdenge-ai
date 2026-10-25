import { Router } from 'express';
import { spawn, spawnSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import { SCENARIOS } from './scenarios.js';
import { pythonProcessQueue } from '../utils/processQueue.js';
import { executeWithCacheAndSingleFlight } from '../utils/calculationCache.js';

const router = Router();
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, '../../..');

const VALID_SCENARIO_IDS = new Set(SCENARIOS.map(s => s.id));
const DATE_REGEX = /^\d{4}-\d{2}-\d{2}$/;

let cachedPythonExecutable = null;
function resolvePythonExecutable() {
  if (process.env.PYTHON_EXECUTABLE) {
    return process.env.PYTHON_EXECUTABLE;
  }
  if (cachedPythonExecutable) {
    return cachedPythonExecutable;
  }
  const candidates = process.platform === 'win32' ? ['python', 'py', 'python3'] : ['python3', 'python'];
  for (const cmd of candidates) {
    try {
      const check = spawnSync(cmd, ['--version'], { encoding: 'utf-8', timeout: 3000 });
      if (check.status === 0) {
        cachedPythonExecutable = cmd;
        return cmd;
      }
    } catch {
      // Sonraki adayı dene
    }
  }
  cachedPythonExecutable = process.platform === 'win32' ? 'py' : 'python3';
  return cachedPythonExecutable;
}

/**
 * Tek bir simülasyonu Python motoru üzerinden çalıştırır
 */
export async function executePythonSimulate(params = {}) {
  const { scenarioId = 'isyeri_gunduz', f = 0.5, capKw, day, seed = 42 } = params;
  const numF = Number(f);
  const numSeed = Number.isFinite(Number(seed)) ? Math.trunc(Number(seed)) : 42;

  const pythonArgs = [
    '-m',
    'sarjdenge.web_servis',
    '--senaryo',
    String(scenarioId),
    '--f',
    String(numF),
    '--tohum',
    String(numSeed),
    '--json',
  ];

  if (capKw !== undefined && capKw !== null && capKw !== '') {
    pythonArgs.push('--cap', String(Number(capKw)));
  }
  if (day !== undefined && day !== null && String(day).trim() !== '') {
    pythonArgs.push('--gun', String(day).trim());
  }

  let releaseLock;
  try {
    releaseLock = await pythonProcessQueue.acquire();
  } catch (queueErr) {
    throw queueErr;
  }

  let lockReleased = false;
  const safeRelease = () => {
    if (!lockReleased && typeof releaseLock === 'function') {
      lockReleased = true;
      releaseLock();
    }
  };

  const pythonExecutable = resolvePythonExecutable();
  const startTime = Date.now();

  return new Promise((resolve, reject) => {
    try {
      const pyProcess = spawn(pythonExecutable, pythonArgs, {
        cwd: PROJECT_ROOT,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' },
      });

      let stdoutData = '';
      let stderrData = '';
      let responded = false;
      let timedOut = false;

      // Render 100s proxy sınırına uygun makul süre (50 sn)
      const timeoutLimit = 50000;
      const timeoutId = setTimeout(() => {
        timedOut = true;
        if (!pyProcess.killed) {
          pyProcess.kill();
        }
      }, timeoutLimit);

      pyProcess.stdout.on('data', chunk => {
        stdoutData += chunk.toString('utf-8');
      });

      pyProcess.stderr.on('data', chunk => {
        stderrData += chunk.toString('utf-8');
      });

      pyProcess.on('error', err => {
        clearTimeout(timeoutId);
        safeRelease();
        if (responded) return;
        responded = true;
        console.error(`[Python Engine] Simulate HATA: ${err.message}`);
        const spawnErr = new Error('Simülasyon süreci başlatılamadı.');
        spawnErr.status = 500;
        spawnErr.details = err.message;
        reject(spawnErr);
      });

      pyProcess.on('close', code => {
        clearTimeout(timeoutId);
        safeRelease();
        if (responded) return;
        responded = true;

        const duration = Date.now() - startTime;

        if (timedOut) {
          console.error(`[Python Engine] Simulate ZAMAN AŞIMI (${duration}ms) | Senaryo: ${scenarioId}`);
          const toErr = new Error('Simülasyon hesaplaması zaman aşımına uğradı (50 sn).');
          toErr.status = 504;
          return reject(toErr);
        }

        if (code !== 0) {
          let extractedError = 'Simülasyon motoru hata verdi.';
          try {
            const parsedErr = JSON.parse(stderrData.replace(/^\uFEFF/, '').trim());
            if (parsedErr?.hata) {
              extractedError = parsedErr.hata;
            }
          } catch {
            // Ham stderr korunur
          }
          console.error(`[Python Engine] Simulate HATA (${code}) [${duration}ms]: ${extractedError}`);
          const procErr = new Error(extractedError);
          procErr.status = 500;
          procErr.details = stderrData || stdoutData;
          return reject(procErr);
        }

        try {
          const cleanJson = stdoutData.replace(/^\uFEFF/, '').trim();
          const result = JSON.parse(cleanJson);

          if (result?.hata) {
            const bizErr = new Error(result.hata);
            bizErr.status = 422;
            bizErr.details = result;
            return reject(bizErr);
          }

          if (!result || !result.kpi_ozet || !Array.isArray(result.araclar) || !(result.arac_sayisi > 0)) {
            const valErr = new Error('Seçilen senaryo ve günde geçerli simülasyon sonucu üretilemedi.');
            valErr.status = 422;
            return reject(valErr);
          }

          // Başarılı hesaplama süresi logu (Render loglarında görünür)
          console.log(`[Python Engine] Simulate tamamlandı (${duration}ms) | Senaryo: ${scenarioId}, f: ${numF}, Gün: ${day || 'varsayılan'}`);
          resolve(result);
        } catch (parseErr) {
          console.error(`[Python Engine] Simulate JSON parse hatası (${duration}ms):`, parseErr);
          const pErr = new Error('Simülasyon çıktısı JSON olarak okunamadı.');
          pErr.status = 500;
          pErr.raw = stdoutData.slice(0, 500);
          reject(pErr);
        }
      });
    } catch (err) {
      safeRelease();
      reject(err);
    }
  });
}

router.post('/', async (req, res) => {
  const { scenarioId = 'isyeri_gunduz', f = 0.5, capKw, day, seed = 42 } = req.body || {};

  if (!VALID_SCENARIO_IDS.has(String(scenarioId))) {
    return res.status(400).json({
      success: false,
      error: `Geçersiz senaryo kimliği: '${scenarioId}'. Desteklenen senaryolar: ${Array.from(VALID_SCENARIO_IDS).join(', ')}.`,
    });
  }

  const numF = Number(f);
  if (!Number.isFinite(numF) || numF <= 0 || numF > 2.0) {
    return res.status(400).json({
      success: false,
      error: `Geçersiz kapasite katsayısı (f = ${f}). Değer (0, 2.0] aralığında sayısal olmalıdır.`,
    });
  }

  if (capKw !== undefined && capKw !== null && capKw !== '') {
    const numCap = Number(capKw);
    if (!Number.isFinite(numCap) || numCap <= 0) {
      return res.status(400).json({
        success: false,
        error: `Geçersiz trafo kapasitesi (capKw = ${capKw}). Değer pozitif bir sayı olmalıdır.`,
      });
    }
  }

  if (day !== undefined && day !== null && String(day).trim() !== '') {
    const dayStr = String(day).trim();
    if (!DATE_REGEX.test(dayStr) || Number.isNaN(Date.parse(dayStr))) {
      return res.status(400).json({
        success: false,
        error: `Geçersiz tarih biçimi: '${day}'. Beklenen biçim: YYYY-AA-GG.`,
      });
    }
  }

  try {
    const { data: result, source } = await executeWithCacheAndSingleFlight('simulate', req.body, async () => {
      return await executePythonSimulate(req.body);
    });

    return res.json({
      success: true,
      simulation: result,
      _source: source,
    });
  } catch (err) {
    const statusCode = err.status || 500;
    return res.status(statusCode).json({
      success: false,
      error: err.message || 'Simülasyon yürütülemedi.',
      code: err.code,
      details: err.details,
    });
  }
});

export default router;
