import logging
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import supabase_admin_config

logger = logging.getLogger(__name__)


async def generate_auth_email_properties(
    *,
    client: httpx.AsyncClient,
    request_id: str,
    email: str,
    email_type: str,
    password: str | None = None,
    redirect_to: str | None = None,
    allow_missing_user: bool = False,
) -> dict[str, Any]:
    supabase_url, service_role_key = supabase_admin_config()
    payload: dict[str, Any] = {"type": email_type, "email": email}
    if password is not None:
        payload["password"] = password
    if redirect_to:
        payload["redirect_to"] = redirect_to

    try:
        upstream = await client.post(
            f"{supabase_url}/auth/v1/admin/generate_link",
            headers={
                "apikey": service_role_key,
                "Authorization": f"Bearer {service_role_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    except httpx.TimeoutException as error:
        logger.warning(
            "Supabase email token generation timed out",
            extra={"request_id": request_id},
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The authentication service timed out. Please try again.",
        ) from error
    except httpx.RequestError as error:
        logger.warning(
            "Supabase email token generation failed (%s)",
            type(error).__name__,
            extra={"request_id": request_id},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The authentication service is currently unavailable.",
        ) from error

    if upstream.is_error:
        if allow_missing_user and upstream.status_code == status.HTTP_404_NOT_FOUND:
            return {}
        logger.warning(
            "Supabase email token generation returned HTTP %s",
            upstream.status_code,
            extra={"request_id": request_id},
        )
        if upstream.status_code >= 500:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The authentication service could not complete the request.",
            )
        if allow_missing_user:
            try:
                error_code = upstream.json().get("code")
            except (ValueError, AttributeError):
                error_code = None
            if error_code == "user_not_found":
                return {}
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The email request could not be completed.",
        )

    try:
        response_body = upstream.json()
    except ValueError as error:
        logger.error(
            "Supabase email token generation returned invalid JSON",
            extra={"request_id": request_id},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The authentication service returned an invalid response.",
        ) from error

    if not isinstance(response_body, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The authentication service returned an invalid response.",
        )
    properties = response_body.get("properties", response_body)
    if not isinstance(properties, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The authentication service returned an invalid response.",
        )
    return properties
