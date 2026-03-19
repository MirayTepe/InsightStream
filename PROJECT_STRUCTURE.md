# InsightStream Project Structure

## Full Folder Structure (Phases 1–7)

```
Explainly/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI
├── ARCHITECTURE.md
├── PROJECT_STRUCTURE.md
├── .env.example
├── .env.dev
├── .env.prod
│
├── backend/
│   ├── app/                    # FastAPI application
│   ├── workers/                # Celery tasks
│   ├── alembic/                # DB migrations
│   ├── tests/                  # Pytest tests
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── setup.cfg               # Flake8 config
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── package.json
│
└── infra/
    ├── docker-compose.yml      # Full stack
    └── nginx.conf              # Reverse proxy
```

## Docker Compose (from infra/)

```bash
cd infra
docker compose up -d
```

Services: postgres, redis, rabbitmq, fastapi, celery_worker, nextjs, nginx

- **App**: http://localhost
- **API**: http://localhost/api/v1/
- **RabbitMQ UI**: http://localhost:15672

## CI/CD

- **Trigger**: push/PR to main or master
- **Backend**: flake8, pytest
- **Frontend**: eslint, next build
- **Docker**: build backend + frontend images (on push only)

## Run migrations

```bash
docker compose -f infra/docker-compose.yml exec fastapi alembic upgrade head
```
