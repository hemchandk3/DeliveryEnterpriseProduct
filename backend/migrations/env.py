from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Register all ORM models on Base.metadata before Alembic reads it -- both
# for autogenerate diffing and so `Base` below is the single source of
# truth for the schema (never hand-duplicated into this file).
import app.models  # noqa: F401
from app.config import get_settings
from app.db import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    """The real DB URL always comes from app settings (DATABASE_URL / .env),
    never from alembic.ini -- so `alembic upgrade head` and the running app
    are guaranteed to target the same database. `-x db_url=...` on the CLI
    overrides it for one-off use (e.g. pointing at a scratch DB in CI).
    """
    x_args = context.get_x_argument(as_dictionary=True)
    return x_args.get("db_url") or get_settings().database_url


def run_migrations_offline() -> None:
    url = _database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=url.startswith("sqlite"),
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = _database_url()
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=url.startswith("sqlite"),
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
