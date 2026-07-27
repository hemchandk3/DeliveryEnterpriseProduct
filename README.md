# DeliveryEnterpriseProduct

Techwave Delivery Intelligence & Governed Agent Platform.

## Local development

See [`docs/devops/run.md`](docs/devops/run.md) for how to build and run the
stack (Postgres + pgvector, Redis, FastAPI backend) with Docker Compose, or
the backend on its own.

CI (`.github/workflows/ci.yml`) enforces ruff, mypy, a pytest coverage gate
(>= 80%, hard fail below), and a gitleaks secret scan on every PR to `main`.
See `docs/ENGINEERING_STANDARDS.md` for the full set of quality gates.
