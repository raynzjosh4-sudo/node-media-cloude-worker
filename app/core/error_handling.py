import logging
from typing import Any
from uuid import uuid4

import httpx
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

_ERROR_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "invalid_request",
    429: "rate_limited",
    500: "internal_error",
    502: "upstream_error",
    503: "service_unavailable",
    504: "upstream_timeout",
}


def _request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if request_id is None:
        request_id = uuid4().hex
        request.state.request_id = request_id
    return request_id


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = _request_id(request)
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    response_headers = dict(headers or {})
    response_headers["X-Request-ID"] = request_id
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error,
            "request_id": request_id,
        },
        headers=response_headers,
    )


async def handle_http_exception(
    request: Request,
    exception: HTTPException,
) -> JSONResponse:
    message = (
        exception.detail
        if isinstance(exception.detail, str)
        else "The request could not be completed."
    )
    return _error_response(
        request,
        status_code=exception.status_code,
        code=_ERROR_CODES.get(exception.status_code, "request_failed"),
        message=message,
        headers=exception.headers,
    )


async def handle_validation_exception(
    request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(loc) for loc in error["loc"] if loc != "body"),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exception.errors()
    ]
    return _error_response(
        request,
        status_code=422,
        code="invalid_request",
        message="Validation failed for submitted data. Please verify required fields.",
        details=details,
    )


async def handle_httpx_exception(
    request: Request,
    exception: httpx.HTTPError,
) -> JSONResponse:
    request_id = _request_id(request)
    logger.error(
        f"Upstream database/network HTTP exception: {exception}",
        extra={"request_id": request_id},
    )
    if isinstance(exception, httpx.HTTPStatusError):
        status_code = exception.response.status_code
        try:
            err_data = exception.response.json()
            err_msg = err_data.get("message") or err_data.get("hint") or str(exception)
        except Exception:
            err_msg = exception.response.text or str(exception)
        return _error_response(
            request,
            status_code=status_code if 400 <= status_code < 500 else 502,
            code="upstream_status_error",
            message=err_msg,
        )
    return _error_response(
        request,
        status_code=502,
        code="upstream_error",
        message="A communication error occurred with the backend database. Please retry shortly.",
    )


async def handle_unexpected_exception(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    request_id = _request_id(request)
    logger.exception(
        f"Unhandled API exception: {exception}",
        extra={"request_id": request_id},
    )
    return _error_response(
        request,
        status_code=500,
        code="internal_error",
        message="An internal server error occurred. Please contact support or try again.",
    )
