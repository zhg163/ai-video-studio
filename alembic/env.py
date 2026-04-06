"""Alembic environment configuration for async PostgreSQL."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import our models so metadata is populated
from packages.common.config import settings
from packages.common.database import Base
from packages.domain.models import (  # noqa: F401
    AssetFile,
    AuditLog,
    GenerationTask,
    Project,
    ProjectMember,
    ProjectVersion,
    RenderTask,
    ReviewComment,
    Tenant,
    UserAccount,
)

config = context.config

# Override sqlalchemy.url from settings
config.set_main_option("sqlalchemy.url", settings.postgres_dsn_sync)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
