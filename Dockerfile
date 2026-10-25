# ==========================================
# ŞarjDenge AI — Üretim Docker İmajı
# Node.js 20 (Express API + Vite Statik Sunucu) + Python 3.11 (SciPy/HiGHS Optimizasyon)
# ==========================================

FROM python:3.11-slim

# Sistem bağımlılıkları ve Node.js 20 kurulumu
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Python bağımlılıklarını kur (önbellekten azami yararlanma)
COPY requirements.txt ./
# Üretim API motoru için gerekli çekirdek kütüphaneler
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    scipy \
    scikit-learn \
    pyyaml

# 2. Node.js backend bağımlılıklarını kur
COPY web/server/package*.json ./web/server/
RUN npm ci --prefix web/server --omit=dev --no-audit --no-fund

# 3. Gerekli uygulama kodlarını ve derlenmiş frontend'i kopyala
COPY sarjdenge/ ./sarjdenge/
COPY config/ ./config/
COPY web/server/ ./web/server/
COPY web/client/dist/ ./web/client/dist/

# 4. Yalnızca web servisinin ihtiyaç duyduğu veri dosyaları
COPY acn_oturumlar_v2.csv ./
COPY acn_oturumlar_temmuz_aralik.csv ./

# Ortam değişkenleri
ENV NODE_ENV=production
ENV PORT=5000
ENV PYTHON_EXECUTABLE=python3

# Express portu
EXPOSE 5000

# Sağlık kontrolü
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:5000/api/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

# Başlatma komutu
CMD ["node", "web/server/index.js"]
