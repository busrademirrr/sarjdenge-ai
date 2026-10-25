# ==========================================
# ŞarjDenge AI — Canlı Dağıtım (Render) Çok Aşamalı Dockerfile
# Aşama 1: Node 20 ile React Build (Vite)
# Aşama 2: Python 3.12-slim + Node 20 (Express API + HiGHS LP Optimizasyonu)
# ==========================================

# ------------------------------------------
# Aşama 1: React Frontend Derleme
# ------------------------------------------
FROM node:20-slim AS frontend-builder
WORKDIR /app/web/client

COPY web/client/package*.json ./
RUN npm ci --no-audit --no-fund

COPY web/client/ ./
# Çok günlü mod derleme bayrağı ile kapalı
ENV VITE_ENABLE_MULTIDAY=false
RUN npm run build

# ------------------------------------------
# Aşama 2: Üretim Çalışma Zamanı (Runtime)
# ------------------------------------------
FROM python:3.12-slim

# Node.js 20 kurulumu
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Python bağımlılıklarını kur (yerel sürümlerle sabitlenmiş requirements.txt)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 2. Node.js backend bağımlılıklarını kur
COPY web/server/package*.json ./web/server/
RUN npm ci --prefix web/server --omit=dev --no-audit --no-fund

# 3. Uygulama ve model kodlarını kopyala
COPY sarjdenge/ ./sarjdenge/
COPY config/ ./config/
COPY data/ ./data/
COPY web/server/ ./web/server/

# 4. Aşama 1'den derlenen React statik çıktılarını kopyala
COPY --from=frontend-builder /app/web/client/dist ./web/client/dist

# 5. Yalnızca simülasyonun gerektirdiği sütunları içeren asgari ve anonim veri kümesi
COPY acn_oturumlar_v2.csv acn_oturumlar_temmuz_aralik.csv ./
RUN python3 -c "import pandas as pd; \
    cols = ['doneChargingTime', 'userID', 'girdi_sayisi', 'girdi_degisti']; \
    for f in ['acn_oturumlar_v2.csv', 'acn_oturumlar_temmuz_aralik.csv']: \
        df = pd.read_csv(f); \
        df.drop(columns=[c for c in cols if c in df.columns], errors='ignore').to_csv(f, index=False)"

# Ortam değişkenleri
ENV NODE_ENV=production
ENV PORT=5000
ENV PYTHON_EXECUTABLE=python3
ENV ENABLE_MULTIDAY=false

EXPOSE 5000

# Sağlık kontrolü (GET /healthz anında 200 döner, Python tetiklemez)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:' + (process.env.PORT || 5000) + '/healthz', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

CMD ["node", "web/server/index.js"]
