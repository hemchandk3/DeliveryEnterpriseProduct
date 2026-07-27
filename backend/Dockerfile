# syntax=docker/dockerfile:1
# Dockerfile for the Techwave Delivery Intelligence backend (FastAPI).
# Built from backend/ as context (see docker-compose.yml `build.context`).
#
# Layout/entrypoint match backend/app/main.py (`app = FastAPI(...)`,
# `GET /health`) and backend/pyproject.toml (setuptools, package `app*`)
# from PR #1 (feat/foundation-ingest). No secrets are baked into the image;
# all config comes from environment variables at run time (12-factor),
# see backend/.env.example and the root .env.example.

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# curl -> container healthcheck; libpq5 -> runtime lib for the Postgres
# driver installed below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy only what's needed to resolve dependencies first for better layer
# caching, then the application package.
COPY pyproject.toml ./
COPY app ./app

# Install the backend package exactly as declared in backend/pyproject.toml,
# plus the Postgres driver + pgvector client needed to talk to the
# docker-compose `db` service (pgvector/pgvector image). These two extra
# packages are NOT yet in backend/pyproject.toml `dependencies` (PR #1 ships
# with a SQLite default and no Postgres driver) -- flagged for the developer
# to fold into pyproject.toml once confirmed, tracked in docs/devops/run.md.
RUN pip install --no-cache-dir . "psycopg[binary]>=3.1" "pgvector>=0.3"

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
