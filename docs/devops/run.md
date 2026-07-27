# Build & run locally

Scaffolding for the Techwave Delivery Intelligence & Governed Agent
Platform: a FastAPI backend (`backend/`, see PR #1), Postgres+pgvector, and
Redis, wired for reproducible local dev and enforced in CI.

## Prerequisites

- Docker Desktop (or a compatible Docker Engine + Compose v2 CLI)
- Python 3.12 (only needed if you want to run the backend outside Docker)

## 1. Configure environment (12-factor, no secrets committed)

```bash
cp .env.example .env
```

Fill in real values in `.env` (never commit it — it's gitignored). The
important ones:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection string (defaults to the compose `db` service) |
| `GITHUB_TOKEN` | Scoped GitHub token for the ingest connector |
| `JIRA_BASE_URL` / `JIRA_EMAIL` / `JIRA_TOKEN` | Jira Cloud connector auth |
| `JIRA_STORY_POINTS_FIELD` | Instance-specific custom field id (see `backend/.env.example`) |

`backend/.env.example` documents the same backend-application variables in
isolation, for running the backend without Docker.

## 2. Run the full stack (Postgres + pgvector, Redis, backend API)

```bash
docker compose up --build
```

This starts:
- `db` — `pgvector/pgvector:pg16`, with the `vector` extension enabled
  automatically via `infra/postgres/init-extensions.sql` on first boot.
- `redis` — `redis:7-alpine`.
- `backend` — built from `backend/Dockerfile`, waiting on both healthchecks
  before it starts, exposed on `http://localhost:8000`.

Verify it's healthy:

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

Tear down (keeps the `pgdata` volume so you don't lose local data):

```bash
docker compose down
```

Add `-v` to also drop the Postgres volume (destructive — local data only).

## 3. Run the backend without Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

By default this uses the SQLite fallback in `app/config.py`
(`sqlite:///./delivery.db`) unless `DATABASE_URL` is set in your shell/`.env`
to point at a running Postgres instance.

## 4. Run the same checks CI runs

```bash
cd backend
pip install -e ".[dev]" mypy
ruff check .
ruff format --check .
mypy --config-file mypy.ini
coverage run -m pytest
coverage report -m --fail-under=80
```

## CI pipeline (`.github/workflows/ci.yml`)

Two jobs run on every push/PR to `main`:

1. **`backend-quality-gates`** — `ruff check`, `ruff format --check`,
   `mypy`, then `pytest` under `coverage`. The coverage step **fails the
   build** if line coverage drops below **80%**
   (`coverage report --fail-under=80`), per
   `docs/ENGINEERING_STANDARDS.md` §3 (unit-test coverage gate, owner:
   developer/frontend, verified by QA). This is a hard gate, not advisory —
   it is not bypassed to get a build green.
2. **`security-scan`** — runs `gitleaks` against the full git history. If a
   `.gitleaks.toml` baseline exists at the repo root (owned by the security
   agent), it's used automatically; otherwise gitleaks' default ruleset
   applies. This satisfies "gates in the pipeline, not around it" — the
   step always scans, it never rubber-stamps.

Enabling these as **required** status checks on `main` (branch protection)
is a one-time repo-admin setting outside this PR's scope — flagged here so
it doesn't get missed.

## Known gaps to close (tracked, not silently patched around)

- `backend/pyproject.toml` (PR #1) declares no Postgres driver and no
  `mypy` dev dependency yet. `backend/Dockerfile` installs
  `psycopg[binary]` + `pgvector` directly so the compose stack works today;
  CI installs `mypy` directly for the same reason. Once confirmed, these
  should move into `backend/pyproject.toml`'s `dependencies` / `dev` extra
  so there's one source of truth for backend dependencies.
- `DATABASE_URL`'s default in `app/config.py` is SQLite; docker-compose
  overrides it to point at the `db` Postgres service. Both are intentional
  (SQLite for fast local/unit-test iteration, Postgres+pgvector for the
  real stack) — not a conflict, just worth knowing which one you're on.
