from contextlib import asynccontextmanager

import asyncpg

from app.config import settings

# Global variable to hold the database pool
db_pool = None


@asynccontextmanager
async def lifespan_context(_: "FastAPI"):
    global db_pool
    # Setup: create the DB pool using the URL from settings
    db_pool = await asyncpg.create_pool(dsn=settings.database_url)
    yield
    # Cleanup: close the DB pool
    await db_pool.close()
