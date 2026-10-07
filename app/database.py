import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

database_url = os.environ["DATABASE_URL"]
engine = create_engine(database_url, pool_pre_ping=True)
SessionFactory = sessionmaker(engine, expire_on_commit=False)


def get_session():
    with SessionFactory() as session:
        yield session
