# ADR 0001: Monorepo + FastAPI + Next.js + AWS ECS

## Decision
- Monorepo:
  - `apps/api` (FastAPI)
  - `apps/web` (Next.js)
- Postgres as system of record; Redis for caching/queues
- Celery workers for heavy tasks
- AWS from day one using ECS Fargate + RDS + ElastiCache + S3 + CloudFront

## Why
- Scales without early Kubernetes overhead.
- Hiring-friendly stack and clear boundaries.
