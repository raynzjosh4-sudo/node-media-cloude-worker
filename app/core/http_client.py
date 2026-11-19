from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from fastapi import FastAPI, Request

_TIMEOUT = httpx.Timeout(20.0, connect=5.0)
_LIMITS = httpx.Limits(max_connections=100, max_keepalive_connections=20)


@asynccontextmanager
async def lifespan_http_client(app: FastAPI) -> AsyncIterator[None]:
    async with httpx.AsyncClient(timeout=_TIMEOUT, limits=_LIMITS) as client:
        app.state.http_client = client
        yield


def get_http_client(request: Request) -> httpx.AsyncClient:
    client = getattr(request.app.state, "http_client", None)
    if not isinstance(client, httpx.AsyncClient):
        raise RuntimeError("The application HTTP client has not been started.")
    return client
