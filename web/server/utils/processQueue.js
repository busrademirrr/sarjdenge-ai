/**
 * ŞarjDenge AI — Bellek Koruması ve Eşzamanlı İşlem Kuyruğu
 *
 * Render Free planındaki 512 MB RAM sınırını korumak için aynı anda
 * en fazla 1 Python hesabı çalıştırılır. Eşzamanlı gelen diğer istekler
 * sınırlı bir kuyrukta bekler; kuyruk dolarsa veya bekleme süresi aşılırsa
 * kullanıcıya net bir meşgul mesajı (HTTP 503) döner.
 */

class ProcessQueue {
  constructor(maxConcurrent = 1, maxQueue = 2, queueTimeoutMs = 15000) {
    this.maxConcurrent = maxConcurrent;
    this.maxQueue = maxQueue;
    this.queueTimeoutMs = queueTimeoutMs;
    this.activeCount = 0;
    this.queue = [];
  }

  async acquire() {
    if (this.activeCount < this.maxConcurrent) {
      this.activeCount++;
      return () => this.release();
    }

    if (this.queue.length >= this.maxQueue) {
      const err = new Error('Sunucu şu anda başka bir optimizasyon hesaplaması yürütüyor. Bellek sınırını (512 MB) korumak için lütfen birkaç saniye sonra tekrar deneyin.');
      err.status = 503;
      err.code = 'SERVER_BUSY';
      throw err;
    }

    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        const idx = this.queue.findIndex(item => item.resolve === resolve);
        if (idx !== -1) {
          this.queue.splice(idx, 1);
        }
        const err = new Error('İşlem sırası zaman aşımına uğradı (15 sn). Sunucu meşgul, lütfen tekrar deneyin.');
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
      maxConcurrent: this.maxConcurrent
    };
  }
}

export const pythonProcessQueue = new ProcessQueue(1, 2, 15000);
