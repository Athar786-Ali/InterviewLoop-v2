# InterviewLoop-v2

Production-grade AI mock interview platform skeleton.

This repository intentionally contains architecture and configuration only. Business logic will be added in later phases.

## Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery, Pydantic v2
- Frontend: React 19, Vite, React Router, Axios, CSS Modules
- AI runtime boundary: Ollama as an external service

## Structure

```text
backend/
frontend/
docker/
nginx/
```

Domain folders are scaffolded for:

- auth
- interview
- dashboard
- report
- analytics
- code_execution
- crypto
- workers
- models
- schemas
- services
- middleware
- core
- tests

## Run

```bash
docker compose up --build
```
