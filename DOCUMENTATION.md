# InsightStream – Proje Dokümantasyonu

> **Hedef kitle:** Projeyi hiç bilmeyen geliştiriciler ve DevOps ekipleri.

---

## İçindekiler

1. [Proje Hakkında](#1-proje-hakkında)
2. [Mimari Genel Bakış](#2-mimari-genel-bakış)
3. [Teknoloji Yığını](#3-teknoloji-yığını)
4. [Proje Yapısı](#4-proje-yapısı)
5. [Kurulum (Baştan Sona)](#5-kurulum-baştan-sona)
6. [Ortam Değişkenleri](#6-ortam-değişkenleri)
7. [API Referansı](#7-api-referansı)
8. [Özellikler ve İş Akışları](#8-özellikler-ve-iş-akışları)
9. [Docker ile Çalıştırma](#9-docker-ile-çalıştırma)
10. [CI/CD](#10-cicd)
11. [Sorun Giderme](#11-sorun-giderme)

---

## 1. Proje Hakkında

### InsightStream Nedir?

**InsightStream**, PDF belgeler üzerinde **RAG (Retrieval-Augmented Generation)** tabanlı sohbet yapmanızı sağlayan kurumsal seviye bir platformdur. Kullanıcılar PDF yükleyebilir, belgeye dayalı sorular sorabilir ve yapay zeka destekli yanıtlar alabilir.

### Temel Özellikler

- **PDF Yükleme:** Senkron veya asenkron (Celery) işleme
- **RAG Sohbet:** Belgeden alınan bağlama dayalı soru-cevap
- **Modlar:** Özet, Derin Analiz, Çocuğa Anlat
- **Streaming:** Token bazlı akışlı yanıtlar
- **TTS:** Yanıtları ses dosyasına dönüştürme
- **Kimlik Doğrulama:** JWT tabanlı güvenlik
- **Çok Kiracılı:** Kullanıcı bazlı veri izolasyonu

### RAG Nasıl Çalışır?

1. PDF metni çıkarılır ve parçalara (chunk) bölünür
2. Her parça vektörlere dönüştürülür (embedding)
3. Soru gelince benzer parçalar vektör aramasıyla bulunur
4. Bu parçalar + soru LLM’e (Gemini) gönderilir
5. Model sadece belgeye dayalı yanıt üretir

---

## 2. Mimari Genel Bakış

### Katmanlı Mimari

```
┌─────────────────────────────────────────┐
│  API (FastAPI Routes)                   │  ← HTTP istekleri
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Services (İş Mantığı)                  │  ← PDF, AI, Vector, Cache
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Repositories (Veri Erişimi)            │  ← User, Document, Chunk
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Altyapı                                │  ← PostgreSQL, Redis, FAISS
└─────────────────────────────────────────┘
```

### Tasarım İlkeleri

- **Service-Repository Pattern:** Veritabanı erişimi yalnızca repository’ler üzerinden
- **Bağımsız Modüller:** PDF, embedding, vektör depolama ve LLM birbirinden ayrık
- **Çok Kiracılı:** Her kullanıcının kendi dokümanları ve vektör alanı

---

## 3. Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| **Backend** | FastAPI, Python 3.11 |
| **Veritabanı** | PostgreSQL, SQLAlchemy, Alembic |
| **Önbellek** | Redis |
| **Kuyruk** | RabbitMQ, Celery |
| **Vektör DB** | FAISS (varsayılan, Pinecone/Weaviate desteklenir) |
| **AI/LLM** | Google Vertex AI (Gemini Flash/Pro) |
| **TTS** | Google Cloud Text-to-Speech |
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Shadcn/UI |
| **DevOps** | Docker, Docker Compose, Nginx, GitHub Actions |

---

## 4. Proje Yapısı

```
Explainly/
├── .github/workflows/ci.yml    # CI/CD pipeline
├── .env.example               # Örnek ortam değişkenleri
│
├── backend/                   # FastAPI uygulaması
│   ├── app/
│   │   ├── api/v1/            # REST endpoint'leri
│   │   │   ├── auth_routes.py
│   │   │   ├── health_routes.py
│   │   │   ├── pdf_routes.py
│   │   │   └── chat_routes.py
│   │   ├── core/              # Config, DB, güvenlik
│   │   ├── models/            # SQLAlchemy + Pydantic modelleri
│   │   ├── repositories/      # Veri erişim katmanı
│   │   └── services/          # İş mantığı
│   ├── workers/               # Celery task'ları
│   ├── alembic/               # Veritabanı migrasyonları
│   ├── tests/                 # Pytest testleri
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                  # Next.js uygulaması
│   ├── app/                   # Sayfalar ve layout
│   ├── components/            # React bileşenleri
│   ├── hooks/                 # Custom React hook'ları
│   ├── lib/                   # API client, yardımcılar
│   ├── Dockerfile
│   └── package.json
│
└── infra/                     # Altyapı
    ├── docker-compose.yml     # Tüm servisler
    └── nginx.conf             # Reverse proxy
```

---

## 5. Kurulum (Baştan Sona)

### Ön Koşullar

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **Redis** (opsiyonel, yerel dev için in-memory fallback var)
- **RabbitMQ** (sadece async PDF yükleme için gerekli)

### Adım 1: Projeyi Klonlayın

```bash
git clone <repo-url>
cd Explainly
```

### Adım 2: Backend Kurulumu

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### Adım 3: Ortam Değişkenleri

```bash
# Backend klasöründe
copy ..\.env.example .env

# .env dosyasını düzenleyin:
# - DATABASE_URL_SYNC (PostgreSQL bağlantı bilgisi)
# - JWT_SECRET_KEY (güçlü bir anahtar)
# - GCP bilgileri (opsiyonel, Vertex AI için)
```

### Adım 4: Veritabanı ve Migrasyonlar

```sql
-- PostgreSQL'de
CREATE DATABASE insightstream;
```

```bash
cd backend
alembic upgrade head
```

### Adım 5: Backend'i Çalıştırın

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Adım 6: Frontend Kurulumu

```bash
# Yeni terminal
cd frontend
npm install
npm run dev
```

### Adım 7: (Opsiyonel) Celery Worker

Async PDF yükleme için:

```bash
cd backend
celery -A workers.celery_app worker --loglevel=info -Q pdf
```

RabbitMQ ve Redis’in çalışıyor olması gerekir.

### Erişim Adresleri

| Servis | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Dokümantasyonu | http://localhost:8000/docs |
| Sağlık Kontrolü | http://localhost:8000/api/v1/health |

---

## 6. Ortam Değişkenleri

### Backend (.env)

| Değişken | Açıklama | Varsayılan |
|----------|----------|------------|
| `DATABASE_URL_SYNC` | PostgreSQL bağlantı URL’i | `postgresql://postgres:postgres@localhost:5432/insightstream` |
| `REDIS_URL` | Redis bağlantı URL’i | `redis://localhost:6379/0` |
| `RABBITMQ_URL` | RabbitMQ bağlantı URL’i | `amqp://guest:guest@localhost:5672//` |
| `JWT_SECRET_KEY` | JWT imzalama anahtarı | *(Değiştirin!)* |
| `GCP_PROJECT_ID` | Google Cloud proje ID | `your-gcp-project-id` |
| `GCP_LOCATION` | Vertex AI bölgesi | `us-central1` |
| `MAX_UPLOAD_SIZE_MB` | Max PDF boyutu (MB) | `50` |
| `RAG_DEFAULT_TOP_K` | Benzer parça sayısı | `5` |
| `FAISS_INDEX_PATH` | FAISS indeks klasörü | `./data/faiss` |
| `STORAGE_LOCAL_PATH` | Yerel dosya depolama | `./data/uploads` |

### Frontend

| Değişken | Açıklama |
|----------|----------|
| `NEXT_PUBLIC_API_BACKEND` | Backend API URL (build zamanında) |

---

## 7. API Referansı

Tüm endpoint’ler `/api/v1` prefix’i altındadır.

### Kimlik Doğrulama

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/auth/register` | Yeni kullanıcı kaydı |
| POST | `/auth/login` | Giriş, JWT token döner |
| POST | `/auth/refresh` | Token yenileme |

**Kayıt Örneği:**
```json
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "securepass123",
  "full_name": "Ad Soyad"
}
```

**Giriş Örneği:**
```json
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "securepass123"
}
// Yanıt: { "access_token": "...", "refresh_token": "..." }
```

### PDF

| Method | Endpoint | Auth | Açıklama |
|--------|----------|------|----------|
| POST | `/pdf/upload` | Hayır | Senkron yükleme, anında işleme |
| POST | `/pdf/upload/async` | Evet | Asenkron yükleme, job_id döner |
| GET | `/pdf/job/{job_id}` | Hayır | Async iş durumu |

**Sync Upload Yanıtı:**
```json
{
  "document_id": "uuid",
  "num_pages": 10,
  "num_chunks": 25
}
```

### Chat (RAG)

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/chat/ask` | Normal (tek seferde) yanıt |
| POST | `/chat/ask/stream` | SSE ile akışlı yanıt |
| POST | `/chat/answer-audio` | TTS ile ses dosyası |

**İstek Gövdesi:**
```json
{
  "document_id": "uuid",
  "messages": [
    { "role": "user", "content": "Bu belgede X nedir?" }
  ],
  "mode": "summary"  // "summary" | "deep_dive" | "explain_to_kid"
}
```

**Stream Event’leri:** `metadata`, `token`, `done`, `error`

### Sağlık

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/health` | Temel liveness |
| GET | `/health/ready` | Veritabanı bağlantısı dahil readiness |
| GET | `/health/metrics` | Prometheus metrikleri |

---

## 8. Özellikler ve İş Akışları

### Sync PDF Yükleme (Demo)

1. Kullanıcı PDF yükler
2. Sunucu metni çıkarır, chunk’lara böler
3. Embedding oluşturulur, FAISS’e yazılır
4. `document_id` döner
5. Bu ID ile sohbet başlatılabilir

### Async PDF Yükleme (Üretim)

1. Kullanıcı giriş yapar (JWT)
2. PDF yüklenir, dosya depolama’ya yazılır
3. Veritabanında `Document` kaydı oluşturulur
4. Celery task kuyruğa alınır
5. `job_id` döner
6. İstemci `/pdf/job/{job_id}` ile durumu takip eder
7. Worker PDF’i işler, chunk’ları ve vektörleri kaydeder

### RAG Sohbet Akışı

1. Kullanıcı soru girer
2. Soru vektörlere dönüştürülür
3. `document_id` için FAISS’te benzer chunk’lar bulunur
4. Chunk’lar + soru mode’a göre (summary/deep_dive/explain_to_kid) LLM’e gider
5. Yanıt üretilir (stream veya tek blok)

### RAG Modları

| Mod | Model | Kullanım |
|-----|-------|----------|
| `summary` | Gemini Flash | Hızlı özet |
| `deep_dive` | Gemini Pro | Detaylı analiz |
| `explain_to_kid` | Gemini Flash | Basit, anlaşılır açıklama |

---

## 9. Docker ile Çalıştırma

### Tüm Stack

```bash
cd infra
docker compose up -d
```

### Servisler

| Servis | Port | Açıklama |
|--------|------|----------|
| nginx | 80 | Reverse proxy, giriş noktası |
| postgres | 5432 | Veritabanı |
| redis | 6379 | Önbellek |
| rabbitmq | 5672, 15672 | Kuyruk + yönetim UI |
| fastapi | 8000 (internal) | Backend API |
| nextjs | 3000 (internal) | Frontend |
| celery_worker | - | PDF işleme worker |

### Erişim

- **Uygulama:** http://localhost
- **API:** http://localhost/api/v1/
- **RabbitMQ UI:** http://localhost:15672

### Migrasyonlar

```bash
docker compose -f infra/docker-compose.yml exec fastapi alembic upgrade head
```

---

## 10. CI/CD

**Konum:** `.github/workflows/ci.yml`

### Tetikleyiciler

- `push` ve `pull_request` → `main` / `master` branch’lerine

### İşler

| Job | Adımlar |
|-----|---------|
| **backend** | Python 3.11 → pip install → flake8 → pytest |
| **frontend** | Node 20 → npm ci → eslint → next build |
| **docker** | Backend ve frontend image’larını build et (sadece push’ta) |

### Yerel Test Komutları

```bash
# Backend
cd backend
flake8 app workers
pytest tests/ -v

# Frontend
cd frontend
npm run lint
npm run build
```

---

## 11. Sorun Giderme

### Backend başlamıyor

- `.env` dosyasının `backend/` içinde olduğundan emin olun
- PostgreSQL’in çalıştığını kontrol edin
- `DATABASE_URL_SYNC` formatı: `postgresql://user:pass@host:port/dbname`

### PDF yükleme hatası

- Maksimum dosya boyutu: 50 MB (varsayılan)
- Sadece PDF kabul edilir
- Async yükleme için RabbitMQ + Redis + Celery worker gerekli

### Chat "No index found" hatası

- Önce PDF yükleyip işlemin bitmesini bekleyin
- Sync upload sonrası hemen `document_id` kullanılabilir
- Async upload sonrası job tamamlanana kadar bekleyin

### Vertex AI / Gemini yanıt vermiyor

- GCP projesi ve Vertex AI API etkin olmalı
- `GOOGLE_APPLICATION_CREDENTIALS` veya gcloud login
- Kimlik bilgisi yoksa placeholder yanıtlar döner

### Frontend API’ye ulaşamıyor

- Backend 8000 portunda çalışıyor olmalı
- Geliştirme: Next.js rewrites `/api` isteklerini backend’e yönlendirir
- Docker: Nginx `/api` isteklerini fastapi servisine yönlendirir

### Docker Compose hataları

- `docker compose up` öncesi `infra/` klasöründe olduğunuzdan emin olun
- Port çakışmaları: 80, 5432, 6379, 5672 boş olmalı
- İlk çalıştırmada image build süresi uzun olabilir

---

## Ek Kaynaklar

- **API Swagger UI:** http://localhost:8000/docs
- **Mimari:** `ARCHITECTURE.md`
- **Proje Yapısı:** `PROJECT_STRUCTURE.md`
- **Ortam Örneği:** `.env.example`
