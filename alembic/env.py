"""
Alembic マイグレーション環境設定

DATABASE_URL 環境変数が設定されている場合はそちらを優先する。
"""
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# alembic.ini の [alembic] セクションを読み込む
config = context.config

# ロギング設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# アプリケーションのメタデータをインポート（autogenerate で使用）
from app.models import Base  # noqa: E402
target_metadata = Base.metadata

# DATABASE_URL 環境変数を優先する
db_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """オフラインモード: SQLを出力するだけでDBに接続しない"""
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
    """オンラインモード: DBに接続してマイグレーションを実行する"""
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
