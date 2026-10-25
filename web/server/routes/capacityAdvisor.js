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
 * Tek bir Kapasite Danışmanı hesabını Python motoru üzerinden çalıştırır
 */
export async function executePythonAdvisor(params = {}) {
  const { scenarioId = 'isyeri_gunduz', day, seed = 42, multiDay = false } = params;
  const numSeed = Number.isFinite(Number(seed)) ? Math.trunc(Number(seed)) : 42;

  const pythonArgs = [
    '-m',
    'sarjdenge.web_servis',
    '--advisor',
    '--senaryo',
    String(scenarioId),
    '--tohum',
    String(numSeed),
  ];

  if (multiDay) {
    pythonArgs.push('--cok-gunlu');
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

      // Tek gün için 65 sn, çok gün için 210 sn
      const timeoutLimit = multiDay ? 210000 : 65000;
      const timeoutSec = Math.round(timeoutLimit / 1000);
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
        console.error(`[Python Engine] Advisor HATA: ${err.message}`);
        const spawnErr = new Error('Kapasite Danışmanı süreci başlatılamadı.');
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
          console.error(`[Python Engine] Advisor ZAMAN AŞIMI (${duration}ms) | Senaryo: ${scenarioId}`);
          const toErr = new Error(`Kapasite Danışmanı hesaplaması zaman aşımına uğradı (${timeoutSec} sn).`);
          toErr.status = 504;
          return reject(toErr);
        }

        if (code !== 0) {
          let extractedError = 'Kapasite Danışmanı hesaplama motoru hata verdi.';
          try {
            const parsedErr = JSON.parse(stderrData.replace(/^\uFEFF/, '').trim());
            if (parsedErr?.hata) {
              extractedError = parsedErr.hata;
            }
          } catch {
            // Ham stderr korunur
          }
          console.error(`[Python Engine] Advisor HATA (${code}) [${duration}ms]: ${extractedError}`);
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

          if (!result || !Array.isArray(result.yontemler) || !(result.arac_sayisi > 0)) {
            const valErr = new Error('Seçilen senaryo ve günde geçerli kapasite analizi üretilemedi.');
            valErr.status = 422;
            return reject(valErr);
          }

          // Başarılı hesaplama süresi logu (Render loglarında görünür)
          console.log(`[Python Engine] Advisor tamamlandı (${duration}ms) | Senaryo: ${scenarioId}, Gün: ${day || 'varsayılan'}`);
          resolve(result);
        } catch (parseErr) {
          console.error(`[Python Engine] Advisor JSON parse hatası (${duration}ms):`, parseErr);
          const pErr = new Error('Kapasite Danışmanı çıktısı JSON olarak okunamadı.');
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
  const { scenarioId = 'isyeri_gunduz', day, seed = 42, multiDay = false } = req.body || {};

  // 1. Çok günlü mod üretim/dağıtım ortamında kapalıysa doğrudan reddet
  if (multiDay && process.env.ENABLE_MULTIDAY !== 'true') {
    return res.status(400).json({
      success: false,
      error: 'Çok günlü mod bu ortamda bellek ve süre sınırları nedeniyle devre dışı bırakılmıştır.',
    });
  }

  if (!VALID_SCENARIO_IDS.has(String(scenarioId))) {
    return res.status(400).json({
      success: false,
      error: `Geçersiz senaryo kimliği: '${scenarioId}'. Desteklenen senaryolar: ${Array.from(VALID_SCENARIO_IDS).join(', ')}.`,
    });
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
    const { data: result, source } = await executeWithCacheAndSingleFlight('capacityAdvisor', req.body, async () => {
      return await executePythonAdvisor(req.body);
    });

    return res.json({
      success: true,
      advisor: result,
      _source: source,
    });
  } catch (err) {
    const statusCode = err.status || 500;
    return res.status(statusCode).json({
      success: false,
      error: err.message || 'Kapasite analizi üretilemedi.',
      code: err.code,
      details: err.details,
    });
  }
});

export default router;
