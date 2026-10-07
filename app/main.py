import os

from agno.db.postgres import PostgresDb
from agno.os import AgentOS
from sqlalchemy import create_engine, text

database_url = os.environ["DATABASE_URL"]
engine = create_engine(database_url, pool_pre_ping=True)
runtime = AgentOS(
    id="career-intelligence-os",
    name="Career Intelligence OS",
    description="Local infrastructure foundation. Career options remain open.",
    db=PostgresDb(db_url=database_url),
    agents=[],
    teams=[],
    workflows=[],
)
app = runtime.get_app()


@app.get("/health/ready")
def ready():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        version = connection.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).scalar_one()
    return {"status": "ready", "database": "connected", "pgvector": version}
