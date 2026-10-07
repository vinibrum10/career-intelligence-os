from agno.db.postgres import PostgresDb
from agno.os import AgentOS
from sqlalchemy import text
from app.database import database_url, engine
from app.profiles.router import router as profile_router
from app.web import router as web_router

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
app.include_router(profile_router)
app.include_router(web_router)


@app.get("/health/ready")
def ready():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        version = connection.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).scalar_one()
    return {"status": "ready", "database": "connected", "pgvector": version}
