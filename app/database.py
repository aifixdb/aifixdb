import asyncpg
from .config import settings

pool: asyncpg.Pool | None = None


async def init_db():
    global pool
    pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=1,
        max_size=5,
    )


async def close_db():
    global pool
    if pool:
        await pool.close()


async def run_migrations():
    """Run SQL migrations on startup."""
    import pathlib

    migrations_dir = pathlib.Path(__file__).parent.parent / "migrations"
    async with pool.acquire() as conn:
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            await conn.execute(sql_file.read_text())
