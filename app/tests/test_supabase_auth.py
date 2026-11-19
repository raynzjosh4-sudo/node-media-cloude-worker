import asyncio

import httpx
import pytest
from fastapi import HTTPException

from app.authentication.email_auth.supabase_auth import proxy_supabase_auth


def test_supabase_rate_limit_response_is_preserved(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.authentication.email_auth.supabase_auth.supabase_auth_config",
        lambda: ("https://supabase.example", "anon-key"),
    )

    async def run_test() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                429,
                json={"msg": "rate limit exceeded"},
                headers={"content-type": "application/json"},
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            response = await proxy_supabase_auth(
                "POST",
                "resend",
                client=client,
                request_id="test-request-id",
                payload={"type": "signup", "email": "person@example.com"},
            )

        assert response.status_code == 429
        assert response.body == b'{"msg":"rate limit exceeded"}'

    asyncio.run(run_test())


def test_supabase_server_error_is_sanitized(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.authentication.email_auth.supabase_auth.supabase_auth_config",
        lambda: ("https://supabase.example", "anon-key"),
    )

    async def run_test() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="internal upstream details")

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            with pytest.raises(HTTPException) as error:
                await proxy_supabase_auth(
                    "POST",
                    "resend",
                    client=client,
                    request_id="test-request-id",
                    payload={"type": "signup", "email": "person@example.com"},
                )

        assert error.value.status_code == 502
        assert "internal upstream details" not in str(error.value.detail)

    asyncio.run(run_test())
