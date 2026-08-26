from logging.config import fileConfig
import sys
from pathlib import Path

# ضمان إضافة مسار /app للـ sys.path لتفادي ModuleNotFoundError: No module named 'src'
BASE_DIR = Path(__file__).resolve().parents[4]  # الوصول لـ /app
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from schemas.minirag_base import SQLAlchemyBase
from alembic import context
from src.models.db_schemas import (
    Project,
    Asset,
    DataChunk,
    Conversation,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = SQLAlchemyBase.metadata


# 💡 دالة استثناء الجداول الديناميكية من Alembic (تمنع خطأ UndefinedTable)
def include_object(object, name, type_, reflected, compare_to):
    if name and name.startswith("collection_"):
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,  # 👈 إضافة الفلتر هنا
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,  # 👈 إضافة الفلتر هنا
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()