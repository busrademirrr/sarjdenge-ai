import { Router } from 'express';
import { spawn, spawnSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import { SCENARIOS } from './scenarios.js';
import { pythonProcessQueue } from '../utils/processQueue.js';

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

  // 2. Bellek koruması: Eşzamanlı Python sürecini 1 ile sınırla
  let releaseLock;
  try {
    releaseLock = await pythonProcessQueue.acquire();
  } catch (queueErr) {
    return res.status(queueErr.status || 503).json({
      success: false,
      error: queueErr.message,
      code: queueErr.code || 'SERVER_BUSY',
    });
  }

  let lockReleased = false;
  const safeRelease = () => {
    if (!lockReleased && typeof releaseLock === 'function') {
      lockReleased = true;
      releaseLock();
    }
  };

  const pythonExecutable = resolvePythonExecutable();

  try {
    const pyProcess = spawn(pythonExecutable, pythonArgs, {
      cwd: PROJECT_ROOT,
      env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' },
    });

    let stdoutData = '';
    let stderrData = '';
    let responded = false;
    let timedOut = false;

    const timeoutLimit = multiDay ? 210000 : 35000;
    const timeoutSec = Math.round(timeoutLimit / 1000);
    const timeoutId = setTimeout(() => {
      timedOut = true;
      if (!pyProcess.killed) {
        pyProcess.kill();
      }
    }, timeoutLimit);

    req.on('close', () => {
      if (!responded && !pyProcess.killed) {
        pyProcess.kill();
        safeRelease();
      }
    });

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
      if (process.env.NODE_ENV !== 'test') {
        console.error('[Advisor Spawn Error]:', err);
      }
      return res.status(500).json({
        success: false,
        error: 'Kapasite Danışmanı süreci başlatılamadı.',
        details: err.message,
      });
    });

    pyProcess.on('close', code => {
      clearTimeout(timeoutId);
      safeRelease();
      if (responded) return;
      responded = true;

      if (timedOut) {
        return res.status(504).json({
          success: false,
          error: `Kapasite Danışmanı hesaplaması zaman aşımına uğradı (${timeoutSec} sn).`,
        });
      }

      if (code !== 0) {
        let extractedError = 'Kapasite Danışmanı hesaplama motoru hata verdi.';
        try {
          const parsedErr = JSON.parse(stderrData.replace(/^\uFEFF/, '').trim());
          if (parsedErr?.hata) {
            extractedError = parsedErr.hata;
          }
        } catch {
          // Ham stderr ayrıntılarda korunur
        }
        if (process.env.NODE_ENV !== 'test') {
          console.error('[Advisor Engine Error]:', stderrData || stdoutData);
        }
        return res.status(500).json({
          success: false,
          error: extractedError,
          details: stderrData || stdoutData,
        });
      }

      try {
        const cleanJson = stdoutData.replace(/^\uFEFF/, '').trim();
        const result = JSON.parse(cleanJson);

        if (result?.hata) {
          return res.status(422).json({
            success: false,
            error: result.hata,
            details: result,
          });
        }

        if (!result || !Array.isArray(result.yontemler) || !(result.arac_sayisi > 0)) {
          return res.status(422).json({
            success: false,
            error: 'Seçilen senaryo ve günde geçerli kapasite analizi üretilemedi.',
          });
        }

        return res.json({
          success: true,
          advisor: result,
        });
      } catch (parseErr) {
        if (process.env.NODE_ENV !== 'test') {
          console.error('[Advisor Parse Error]:', parseErr, stdoutData.slice(0, 500));
        }
        return res.status(500).json({
          success: false,
          error: 'Kapasite Danışmanı çıktısı JSON olarak okunamadı.',
          raw: stdoutData.slice(0, 500),
        });
      }
    });
  } catch (err) {
    safeRelease();
    res.status(500).json({
      success: false,
      error: 'Kapasite Danışmanı süreci başlatılamadı.',
      message: err.message,
    });
  }
});

export default router;
