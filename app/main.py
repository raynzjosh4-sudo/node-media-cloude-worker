from contextlib import asynccontextmanager
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response

from app.authentication.email_auth.router import router as auth_router
from app.products.router import router as products_router
from app.orders.router import router as orders_router
from app.profile.router import router as profile_router
from app.saved_items.router import router as saved_items_router
from app.records.router import router as records_router
from app.notifications.router import router as notifications_router
from app.promotions.router import router as promotions_router
from app.admin.router import router as admin_router
from pathlib import Path
from starlette.staticfiles import StaticFiles

from app.core.config import (
    allowed_hosts,
    cors_allowed_origins,
    is_production,
    validate_production_config,
)
from app.core.error_handling import (
    handle_http_exception,
    handle_httpx_exception,
    handle_unexpected_exception,
    handle_validation_exception,
)
from app.core.http_client import lifespan_http_client
from sqlalchemy import text
from app.db.session import engine, init_db
import httpx


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Initialize database tables on startup
    init_db()
    validate_production_config()
    async with lifespan_http_client(app):
        yield


app = FastAPI(
    title="N.O.D.E. API",
    version="1.0.0",
    docs_url=None if is_production() else "/docs",
    redoc_url=None if is_production() else "/redoc",
    openapi_url=None if is_production() else "/openapi.json",
    lifespan=lifespan,
)
app.add_exception_handler(StarletteHTTPException, handle_http_exception)
app.add_exception_handler(RequestValidationError, handle_validation_exception)
app.add_exception_handler(httpx.HTTPError, handle_httpx_exception)
app.add_exception_handler(Exception, handle_unexpected_exception)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts())
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(profile_router)
app.include_router(saved_items_router)
app.include_router(records_router)
app.include_router(notifications_router)
app.include_router(promotions_router)
app.include_router(admin_router)

# Mount static files for email images, assets, and local image uploads
static_path = Path(__file__).parent / "static"
static_path.mkdir(parents=True, exist_ok=True)  # ensure it always exists
(static_path / "uploads").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    request_id = uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def readiness() -> dict[str, str]:
    # Verify database connection is alive
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ready"}
