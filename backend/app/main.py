import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException
from starlette.responses import Response

from app.api.v1 import admin, auth, events, features, registrations, users
from app.core.body_limit import BodyLimitMiddleware
from app.core.config import settings
from app.core.contracts import add_examples
from app.core.errors import DomainError
from app.db.database import engine
from app.schemas.errors import ErrorResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
app = FastAPI(
    title=settings.app_name,
    version="1.1.0",
    responses={
        code: {"model": ErrorResponse, "description": description}
        for code, description in {
            400: "Invalid domain operation or expired action token",
            401: "Missing, expired, or revoked authentication",
            403: "Insufficient permission, inactive account, or email not verified",
            404: "Resource not found or not publicly visible",
            409: "State conflict",
            413: "Upload exceeds allowed size",
            422: "Request validation failed",
            429: "Rate limit exceeded; see Retry-After",
            500: "Unexpected server error",
            503: "Service unavailable",
        }.items()
    },
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "Retry-After", "Content-Disposition"],
)
app.add_middleware(BodyLimitMiddleware)


@app.middleware("http")
async def request_context(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", request_id):
        request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.monotonic()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    if request.headers.get("authorization") or "/auth/" in request.url.path:
        response.headers["Cache-Control"] = "no-store"
    logging.getLogger(__name__).info(
        "request_id=%s method=%s status=%s duration_ms=%.1f",
        request_id,
        request.method,
        response.status_code,
        (time.monotonic() - started) * 1000,
    )
    return response


def error_body(request: Request, code: str, message: str, details: Any = None) -> dict[str, object]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": getattr(request.state, "request_id", None),
        }
    }


@app.exception_handler(DomainError)
async def domain_error(request: Request, exc: DomainError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else {}
    if exc.status_code == 429:
        headers["Retry-After"] = str(exc.details["retry_after"])
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(request, exc.code, exc.message, exc.details),
        headers=headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"location": list(error["loc"]), "message": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=error_body(request, "validation_error", "Request validation failed", details),
    )


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(request, "http_error", str(exc.detail)),
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logging.getLogger(__name__).exception(
        "Unhandled request error", extra={"request_id": getattr(request.state, "request_id", None)}
    )
    return JSONResponse(
        status_code=500,
        content=error_body(request, "internal_error", "An unexpected error occurred"),
    )


for router in (
    auth.router,
    users.router,
    admin.router,
    events.router,
    events.organizer_router,
    registrations.router,
    features.router,
):
    app.include_router(router, prefix="/api/v1")


@app.get("/health/live", tags=["Health"])
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["Health"])
def readiness() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise DomainError("not_ready", "Database is unavailable", 503) from exc
    return {"status": "ready"}


def openapi_document() -> dict[str, Any]:
    if app.openapi_schema is None:
        app.openapi_schema = add_examples(
            get_openapi(title=app.title, version=app.version, routes=app.routes)
        )
    return app.openapi_schema


app.openapi = openapi_document  # type: ignore[method-assign]
