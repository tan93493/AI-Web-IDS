import logging
from logging.config import fileConfig

from flask import current_app
from alembic import context

# --- BẮT ĐẦU PHẦN SỬA LỖI ---
# 1. Import trực tiếp db và các model của bạn
# Điều này đảm bảo Alembic "nhìn thấy" được schema
from extensions import db
import models
# --- KẾT THÚC PHẦN SỬA LỖI ---

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

def get_engine():
    try:
        # this works with Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        # this works with Flask-SQLAlchemy>=3
        return current_app.extensions['migrate'].db.engine

def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')

# add your model's MetaData object here
# for 'autogenerate' support
config.set_main_option('sqlalchemy.url', get_engine_url())

# --- BẮT ĐẦU PHẦN SỬA LỖI ---
# 2. Gán target_metadata trực tiếp từ db.metadata
# Đây là thay đổi quan trọng nhất
target_metadata = db.metadata
# --- KẾT THÚC PHẦN SỬA LỖI ---

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        # Sử dụng target_metadata đã được gán ở trên
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            # Sử dụng target_metadata đã được gán ở trên
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
