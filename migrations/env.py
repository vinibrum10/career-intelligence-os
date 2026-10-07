import os

from alembic import context
from sqlalchemy import create_engine, pool
from app.profiles.models import Base


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name == "career"
    if type_ == "table":
        return parent_names.get("schema_name") == "career"
    return True


options = dict(target_metadata=Base.metadata, include_schemas=True, include_name=include_name)
if context.is_offline_mode():
    context.configure(url=os.environ["DATABASE_URL"], literal_binds=True, **options)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(os.environ["DATABASE_URL"], poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, **options)
        with context.begin_transaction():
            context.run_migrations()
