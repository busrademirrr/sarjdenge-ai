import { Router } from 'express';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const router = Router();
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, '../../..');

router.post('/', async (req, res) => {
  const { scenarioId = 'isyeri_gunduz', f = 0.5, capKw, day, seed = 42 } = req.body;

  const pythonArgs = [
    '-m',
    'sarjdenge.web_servis',
    '--senaryo',
    String(scenarioId),
    '--f',
    String(f),
    '--tohum',
    String(seed),
    '--json',
  ];

  if (capKw !== undefined && capKw !== null) {
    pythonArgs.push('--cap', String(capKw));
  }
  if (day) {
    pythonArgs.push('--gun', String(day));
  }

  const pythonExecutable = process.platform === 'win32' ? 'py' : 'python3';

  try {
    const pyProcess = spawn(pythonExecutable, pythonArgs, {
      cwd: PROJECT_ROOT,
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    });

    let stdoutData = '';
    let stderrData = '';

    pyProcess.stdout.on('data', chunk => {
      stdoutData += chunk.toString('utf-8');
    });

    pyProcess.stderr.on('data', chunk => {
      stderrData += chunk.toString('utf-8');
    });

    pyProcess.on('close', code => {
      if (code !== 0) {
        return res.status(500).json({
          success: false,
          error: 'Simülasyon motoru hata verdi.',
          details: stderrData || stdoutData,
        });
      }

      try {
        const result = JSON.parse(stdoutData);
        res.json({
          success: true,
          simulation: result,
        });
      } catch (parseErr) {
        res.status(500).json({
          success: false,
          error: 'Simülasyon çıktısı JSON olarak okunamadı.',
          raw: stdoutData.slice(0, 500),
        });
      }
    });

    // 25 saniye zaman aşımı kuralı
    setTimeout(() => {
      if (!pyProcess.killed) {
        pyProcess.kill();
      }
    }, 25000);
  } catch (err) {
    res.status(500).json({
      success: false,
      error: 'Simülasyon süreci başlatılamadı.',
      message: err.message,
    });
  }
});

export default router;
