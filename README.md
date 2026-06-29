# InterviewLoop-v2

InterviewLoop-v2 is a production-grade AI mock interview platform built as a full-stack engineering portfolio project. It combines secure authentication, AI-driven interview sessions, live speech and WebSocket flows, coding-round execution, analytics dashboards, signed reports, background workers, Docker orchestration, and CI/CD.

The project is intentionally structured like a real product system: clear service boundaries, repository and service layers, typed schemas, test coverage gates, container health checks, and deployment workflows.

## What It Demonstrates

- Production FastAPI architecture with SQLAlchemy, Pydantic v2, PostgreSQL, Redis, and Celery
- React 19 frontend with Vite, React Router, Axios interceptors, CSS Modules, protected routes, loading states, error boundaries, and toast notifications
- AI interview engine using Ollama with `qwen2.5:3b`, prompt templates, memory, retry, timeout, and structured output handling

| AI | Ollama, Qwen2.5:3b |

Pull the Ollama model:

```bash
docker compose exec ollama ollama pull qwen2.5:3b
```
- Secure auth flows: signup, OTP email verification, bcrypt password hashing, RS256 JWTs, refresh tokens, sessions, logout, reset password, rate limiting
- MFA and biometric authentication using TOTP, encrypted secrets, recovery codes, DeepFace ArcFace, OpenCV, and blink-based liveness checks
- Real-time systems: Deepgram WebSocket transcription, typed fallback, FastAPI WebSocket interview events, heartbeat, reconnect, cleanup
- Coding-round module with Monaco Editor and Docker sandbox execution with CPU, memory, process, timeout, network, and Bandit controls
- Report system with JSON/PDF generation, RSA signatures, verification endpoint, audit logs, and SHA256 hash chain
- Background processing with Redis, Celery workers, Celery beat, retry policies, cleanup jobs, email jobs, analytics updates, PDF generation, and Flower monitoring
- CI/CD with linting, tests, coverage reports, Docker image publishing, and guarded production deployment

## Tech Stack

| Layer | Stack |
| --- | --- |
| Backend | FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery, Pydantic v2 |
| Frontend | React 19, Vite, React Router, Axios, CSS Modules, Recharts, Monaco Editor |
| AI | Ollama, Qwen2.5:7b |
| Speech | Deepgram WebSocket streaming, typed fallback |
| Security | bcrypt, RS256 JWT, TOTP, encrypted secrets, recovery codes, audit logs |
| Reports | ReportLab PDF, RSA signatures, SHA256 hash chain |
| DevOps | Docker Compose, Nginx, GitHub Actions, GHCR |
| Testing | Pytest, pytest-cov, Vitest, Testing Library, Ruff, TypeScript |

## Repository Structure

```text
backend/
  app/
    api/v1/              FastAPI route modules
    core/                config, security, logging, encryption, errors
    models/              SQLAlchemy models
    repositories/        persistence boundary
    schemas/             Pydantic request/response contracts
    services/            application services and integrations
    workers/             Celery app and tasks
  tests/                 unit, API, integration-style tests

frontend/
  src/
    api/                 Axios client and interceptors
    auth/                signup, login, enrollment, auth APIs
    dashboard/           analytics dashboard
    interview/           setup, live interview, WebSocket hooks
    code_execution/      Monaco coding round
    report/              signed report UI
    components/          toast, error boundary, route fallbacks
    layouts/             protected app shell
    router/              lazy-loaded protected routes

docker/                  deployment notes and production env template
nginx/                   reverse proxy config
.github/workflows/       CI, Docker image publishing, deployment pipeline
```

## Local Development

Backend:

```bash
cd backend
python -m pip install -r requirements.txt
python -m pytest
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm ci
npm run lint
npm test
npm run build
npm run dev
```

App URLs:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/api/v1/health`
- API prefix: `http://localhost:8000/api/v1`

## Testing And Quality Gates

Backend CI gates:

```bash
ruff check backend
cd backend && python -m pytest
```

Current backend result:

```text
69 passed
Coverage: 81.89%
Coverage gate: 80%
```

Frontend CI gates:

```bash
cd frontend
npm run lint
npm test
npm run build
```

Current frontend result:

```text
3 test files passed
6 tests passed
Production build passed
```

## Docker

The stack includes:

- `nginx`
- `frontend`
- `backend`
- `postgres`
- `redis`
- `celery`
- `celery-beat`
- `flower`
- `ollama`

Run locally:

```bash
docker compose up --build
```

Pull the Ollama model:

```bash
docker compose exec ollama ollama pull qwen2.5:7b
```

Health checks:

```bash
curl http://localhost/health
curl http://localhost/api/v1/health
docker compose ps
```

Production image mode:

```bash
REGISTRY=ghcr.io \
IMAGE_PREFIX=owner/repo \
IMAGE_TAG=latest \
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

See `docker/README.md` for Docker operations and secret setup notes.

## CI/CD

GitHub Actions workflows are in `.github/workflows`.

`ci.yml`

- Backend dependency install
- Ruff lint
- Pytest with coverage XML and HTML reports
- Frontend dependency install
- TypeScript check
- Vitest
- Vite production build
- Docker Compose config validation
- Uploads coverage and frontend build artifacts

`docker.yml`

- Builds backend and frontend images
- Publishes to GitHub Container Registry
- Uses Buildx cache
- Tags images by branch, semantic version tag, commit SHA, and `latest` on default branch

`deploy.yml`

- Manual or post-Docker workflow deployment
- Uses GitHub protected `production` environment
- SSHes into the production host
- Uploads compose and Nginx files
- Pulls GHCR images using `docker-compose.prod.yml`
- Runs `docker compose up -d --remove-orphans`
- Performs a post-deploy health check

Required production secrets:

```text
PRODUCTION_HOST
PRODUCTION_USER
PRODUCTION_SSH_KEY
PRODUCTION_PATH
PRODUCTION_HEALTH_URL
```

Production runtime secrets belong in the server-side `.env`, using `docker/.env.production.example` as the checklist.

## Security Notes

- Real JWT private/public keys are not committed
- TOTP encryption keys are not committed
- Report signing keys are not committed
- Deepgram API keys are not committed
- Docker sandbox execution mounts the Docker socket and should only run on a trusted host
- Code execution containers are launched with network disabled and resource limits

## Interview Talking Points

- The backend uses repository and service layers so route handlers stay thin and testable.
- External providers are isolated behind services and mocked in tests.
- Coverage is enforced in CI with an 80% minimum gate.
- Docker health checks target real application endpoints, not just open ports.
- Frontend routes are lazy-loaded so Monaco and charting libraries do not inflate the initial bundle.
- Deployment is protected by GitHub environments and uses immutable image tags through GHCR.
- The system is designed around operational visibility: audit logs, Flower, health checks, structured errors, and coverage artifacts.
