from contextlib import asynccontextmanager

from fastapi import FastAPI
from .database import init_db, close_db, run_migrations
from .routes import auth_routes, problems, votes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await run_migrations()
    yield
    await close_db()


app = FastAPI(
    title="aifixdb",
    description="The fix database built by AI, for AI.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(problems.router, prefix="/api/v1")
app.include_router(votes.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
