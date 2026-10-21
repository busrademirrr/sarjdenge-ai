import { Router } from 'express';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const router = Router();
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, '../../..');

router.post('/', async (req, res) => {
  const { scenarioId = 'isyeri_gunduz', day, seed = 42 } = req.body;

  const pythonArgs = [
    '-m',
    'sarjdenge.web_servis',
    '--advisor',
    '--senaryo',
    String(scenarioId),
    '--tohum',
    String(seed),
  ];

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
          error: 'Kapasite Dan─▒┼şman─▒ hesaplama motoru hata verdi.',
          details: stderrData || stdoutData,
        });
      }

      try {
        const result = JSON.parse(stdoutData);
        res.json({
          success: true,
          advisor: result,
        });
      } catch (parseErr) {
        res.status(500).json({
          success: false,
          error: 'Kapasite Dan─▒┼şman─▒ ├ğ─▒kt─▒s─▒ JSON olarak okunamad─▒.',
          raw: stdoutData.slice(0, 500),
        });
      }
    });

    // 25 saniye zaman a┼ş─▒m─▒ kural─▒
    setTimeout(() => {
      if (!pyProcess.killed) {
        pyProcess.kill();
      }
    }, 25000);
  } catch (err) {
    res.status(500).json({
      success: false,
      error: 'Kapasite Dan─▒┼şman─▒ s├╝reci ba┼şlat─▒lamad─▒.',
      message: err.message,
    });
  }
});

export default router;
