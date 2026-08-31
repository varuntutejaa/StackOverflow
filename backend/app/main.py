from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.base import Base
from app.db.session import engine

configure_logging()
log = get_logger("app")

limiter = Limiter(key_func=get_remote_address, default_limits=["240/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.using_sqlite:
        # zero-config local dev: make sure tables exist
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        log.info("sqlite_dev_schema_ready")
    log.info("startup", env=settings.env, version=__version__)
    yield
    log.info("shutdown")


app = FastAPI(
    title="Kaushal AI API",
    version=__version__,
    description=(
        "AI-powered multilingual voice livelihood mapping and NSQF-aligned "
        "skilling recommendations for SC communities under PM-AJAY (SIH26097).\n\n"
        "Records tagged `is_demo` / `is_simulated` are **DEMO/SIMULATED**."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time-ms"] = f"{(time.perf_counter() - start) * 1000:.1f}"
    response.headers["X-Kaushal-AI-Version"] = __version__
    return response


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded, slow down."})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=str(request.url), error=str(exc), exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/", tags=["meta"])
def root():
    return {
        "name": "Kaushal AI API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
        "api": settings.api_prefix,
    }


app.include_router(api_router, prefix=settings.api_prefix)

# health also at root for load balancers
from app.api.routes.meta import health as _health  # noqa: E402

app.add_api_route("/health", _health, tags=["meta"])
