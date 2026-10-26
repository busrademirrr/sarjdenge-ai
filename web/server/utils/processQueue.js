/**
 * ŞarjDenge AI — Bellek Koruması ve Eşzamanlı İşlem Kuyruğu
 *
 * Render Free planındaki 512 MB RAM sınırını korumak için aynı anda
 * en fazla 1 Python hesabı çalıştırılır. Eşzamanlı gelen diğer istekler
 * sınırlı bir kuyrukta (max 4) bekler. Kuyruk bekleme süresi 60 saniyedir.
 * Render proxy sınırı (~100 sn) gözetilerek zaman aşımında veya kuyruk
 * dolduğunda kullanıcıya anlaşılır net bir meşgul yanıtı (HTTP 503) döner.
 */

class ProcessQueue {
  constructor(maxConcurrent = 1, maxQueue = 4, queueTimeoutMs = 60000) {
    this.maxConcurrent = maxConcurrent;
    this.maxQueue = maxQueue;
    this.queueTimeoutMs = queueTimeoutMs;
    this.activeCount = 0;
    this.queue = [];
  }

  async acquire() {
    // 1. Kapasite müsaitse anında kilidi al
    if (this.activeCount < this.maxConcurrent) {
      this.activeCount++;
      return () => this.release();
    }

    // 2. Kuyruk doluysa anında 503 dön (Render proxy sınırını koru)
    if (this.queue.length >= this.maxQueue) {
      const err = new Error(
        'Sunucu şu anda başka bir optimizasyon hesaplaması yürütüyor ve işlem sırası dolu. ' +
        'Render ücretsiz katmanı bellek (512 MB) ve proxy (~100 sn) sınırlarını korumak için lütfen 30–60 saniye sonra tekrar deneyin.'
      );
      err.status = 503;
      err.code = 'SERVER_BUSY';
      throw err;
    }

    // 3. Kuyruğa gir ve zaman aşımı mekanizmasını kur
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        const idx = this.queue.findIndex(item => item.resolve === resolve);
        if (idx !== -1) {
          this.queue.splice(idx, 1);
        }
        const err = new Error(
          'İşlem sırası zaman aşımına uğradı (60 sn). ' +
          'Render ücretsiz planında paylaşımlı CPU nedeniyle hesaplama sırası gecikti; lütfen birazdan tekrar deneyin.'
        );
        err.status = 503;
        err.code = 'QUEUE_TIMEOUT';
        reject(err);
      }, this.queueTimeoutMs);

      this.queue.push({
        resolve: () => {
          clearTimeout(timeoutId);
          this.activeCount++;
          resolve(() => this.release());
        },
        reject: (err) => {
          clearTimeout(timeoutId);
          reject(err);
        }
      });
    });
  }

  release() {
    this.activeCount = Math.max(0, this.activeCount - 1);
    if (this.queue.length > 0 && this.activeCount < this.maxConcurrent) {
      const next = this.queue.shift();
      next.resolve();
    }
  }

  get stats() {
    return {
      active: this.activeCount,
      queued: this.queue.length,
      maxConcurrent: this.maxConcurrent,
      maxQueue: this.maxQueue,
      queueTimeoutMs: this.queueTimeoutMs
    };
  }
}

export const pythonProcessQueue = new ProcessQueue(2, 10, 95000);
