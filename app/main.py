from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import init_db, close_db, run_migrations
from .ratelimit import RateLimitMiddleware
from .routes import auth_routes, problems, votes, admin, ideas


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

app.add_middleware(RateLimitMiddleware)

app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(problems.router, prefix="/api/v1")
app.include_router(votes.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(ideas.router, prefix="/api/v1")

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/privacy")
async def privacy():
    return FileResponse(STATIC_DIR / "privacy.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
