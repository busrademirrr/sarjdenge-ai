# ŞarjDenge AI — Canlı Yayın ve Dağıtım Kılavuzu (DEPLOY.md)

Bu doküman, ŞarjDenge AI uygulamasının (Node.js Express + React Vite + Python SciPy/HiGHS) canlıya alınması için test edilmiş yöntemleri içerir.

---

## 1. Yöntem (ÖNERİLEN / 1. ASIL YOL): Cloudflare Tunnel ile Anında Canlıya Çıkış
*Kredi kartı gerektirmez, 0 saniye soğuk açılış, yerel bilgisayar donanımını (hızlı CPU/RAM) kullanır, video çekimi için en kararlı yoldur.*

### Adım 1: Uygulamanın Yerelde Çalıştığından Emin Olun
Backend (Express) port 5000'de derlenmiş React frontend'i (`web/client/dist`) ile birlikte sunar:
```bash
# Frontend'i derleyin (gerekirse):
npm run build --prefix web/client

# Backend'i başlatın:
node web/server/index.js
```
Tarayıcınızdan `http://localhost:5000` adresini açıp çalıştığını doğrulayın.

### Adım 2: Cloudflare Tunnel İstemcisini Yükleyin ve Çalıştırın
1. `cloudflared` aracını indirin:
   - Windows PowerShell (yönetici veya normal):
     ```powershell
     winget install --id Cloudflare.cloudflared
     ```
   - Veya doğrudan resmi siteden `cloudflared-windows-amd64.exe` indirin.
2. Tüneli tek komutla açın (hesap veya giriş gerekmez):
   ```bash
   cloudflared tunnel --url http://localhost:5000
   ```
3. Terminalde şu şekilde bir çıktı belirecektir:
   ```text
   +--------------------------------------------------------------------------------------------+
   |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
   |  https://random-subdomain.trycloudflare.com                                                |
   +--------------------------------------------------------------------------------------------+
   ```
4. Verilen `https://...trycloudflare.com` linki anında tüm dünyada ve mobilde erişilebilirdir.
5. 2 dakikalık tanıtım videosunu bu link üzerinden çekebilir ve jüri formuna ekleyebilirsiniz.

> **Önemli Not:** Bilgisayarınızı ve terminali açık tuttuğunuz sürece link kesintisiz çalışır.

---

## 2. Yöntem (YEDEK / 2. YOL): Render.com Ücretsiz Web Service (Docker)
*Bilgisayarı açık bırakmak istemiyorsanız, bulutta 7/24 barınan ücretsiz seçenek.*

### Adım 1: GitHub Deposunu Hazırlayın
Hazırlanan `Dockerfile` ve `.dockerignore` dosyalarını commit edip GitHub'a push yapın:
```bash
git add Dockerfile .dockerignore DEPLOY.md docker-compose.yml
git commit -m "feat(deploy): Dockerfile ve dagitim yapilandirmasi eklendi"
git push origin main
```

### Adım 2: Render.com Üzerinde Servis Oluşturun
1. [render.com](https://render.com) adresine gidin ve GitHub hesabınızla giriş yapın (Kredi kartı gerekmez).
2. **New +** düğmesine tıklayın ve **Web Service** seçeneğini seçin.
3. Proje GitHub deponuzu bağlayın.
4. Ayarları şu şekilde doldurun:
   - **Name:** `sarjdenge-ai`
   - **Region:** Frankfurt (EU) (Türkiye'ye en yakın lokasyon)
   - **Runtime:** `Docker`
   - **Instance Type:** `Free` (0.1 vCPU, 512 MB RAM)
5. **Advanced Settings** (Gelişmiş Ayarlar):
   - **Health Check Path:** `/api/health`
   - Ortam Değişkeni: `PORT=5000`
6. **Create Web Service** butonuna basın.

> **Uyarı:** Render Free katmanında servis 15 dakika hareketsiz kalınca uyur. İlk açılış (cold start) **50–80 saniye** sürebilir. Jüriye link göndermeden önce linki kendiniz açıp uyandırmanız önerilir.

---

## 3. Yerel Docker ile Doğrulama (İsteğe Bağlı)
Elinizdeki Docker Desktop ile imajı yerelde test etmek isterseniz:
```bash
# İmajı oluştur:
docker build -t sarjdenge-ai:latest .

# Container'ı çalıştır:
docker run -d -p 5000:5000 --name sarjdenge sarjdenge-ai:latest

# Kontrol et:
curl http://localhost:5000/api/health
```
Tarayıcıdan `http://localhost:5000` adresine gidin.
