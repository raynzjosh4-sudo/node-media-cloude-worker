import logging
from typing import Any

import httpx
from fastapi import HTTPException, status
from starlette.responses import Response

from app.core.config import supabase_auth_config

logger = logging.getLogger(__name__)


async def proxy_supabase_auth(
    method: str,
    path: str,
    *,
    client: httpx.AsyncClient,
    request_id: str,
    payload: dict[str, Any] | None = None,
    access_token: str | None = None,
    rest_endpoint: bool = False,
) -> Response:
    supabase_url, anon_key = supabase_auth_config()
    endpoint = "rest/v1" if rest_endpoint else "auth/v1"
    url = f"{supabase_url}/{endpoint}/{path.lstrip('/')}"
    headers = {
        "apikey": anon_key,
        "Authorization": f"Bearer {access_token or anon_key}",
        "Content-Type": "application/json",
    }

    try:
        upstream = await client.request(
            method,
            url,
            headers=headers,
            json=payload,
        )
    except httpx.TimeoutException as error:
        logger.warning(
            "Supabase authentication request timed out",
            extra={"request_id": request_id},
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The authentication service timed out. Please try again.",
        ) from error
    except httpx.RequestError as error:
        logger.warning(
            "Supabase authentication request failed (%s)",
            type(error).__name__,
            extra={"request_id": request_id},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The authentication service is currently unavailable.",
        ) from error

    if upstream.status_code >= 500:
        logger.error(
            "Supabase authentication returned HTTP %s",
            upstream.status_code,
            extra={"request_id": request_id},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The authentication service could not complete the request.",
        )

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )
