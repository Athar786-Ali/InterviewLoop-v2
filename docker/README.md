# InterviewLoop-v2 Docker Deployment

## Services

The production compose stack runs:

- `nginx` reverse proxy on port `80`
- `frontend` static React build served by Nginx
- `backend` FastAPI app on internal port `8000`
- `postgres` PostgreSQL 16 with persistent storage
- `redis` Redis 7 with append-only persistence
- `celery` background worker
- `celery-beat` scheduled cleanup and analytics jobs
- `flower` Celery monitoring on `127.0.0.1:5555`
- `ollama` model runtime on `127.0.0.1:11434`

## Configuration

Use `docker/.env.production.example` as the secret checklist for production values. Real deployments should inject secrets from the platform secret manager, especially:

- `JWT_PRIVATE_KEY`
- `JWT_PUBLIC_KEY`
- `REPORT_SIGNATURE_PRIVATE_KEY`
- `REPORT_SIGNATURE_PUBLIC_KEY`
- `TOTP_SECRET_ENCRYPTION_KEY`
- `DEEPGRAM_API_KEY`
- database password values

The default compose file is runnable for local production-like smoke testing, but the checked-in defaults are not production secrets.

## Run

```bash
docker compose up --build
```

Pull the interview model after Ollama is healthy:

```bash
docker compose exec ollama ollama pull qwen2.5:7b
```

## Health Checks

```bash
curl http://localhost/health
curl http://localhost/api/v1/health
docker compose ps
```

## Persistent Volumes

Compose creates named volumes for:

- `postgres_data`
- `redis_data`
- `backend_reports`
- `celery_beat_data`
- `flower_data`
- `ollama_data`

## Code Execution Sandbox

The backend mounts `/var/run/docker.sock` so the coding module can launch isolated runtime containers with:

- network disabled
- memory limits
- CPU limits
- process limits
- read-only workspace mount

Only enable this on a trusted Docker host.
