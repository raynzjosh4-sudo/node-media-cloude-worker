import asyncio

import httpx
import pytest
from fastapi import HTTPException

from app.authentication.email_auth.generate_auth_email_properties import (
    generate_auth_email_properties,
)


def test_generate_link_uses_service_role_and_returns_email_properties(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.authentication.email_auth.generate_auth_email_properties.supabase_admin_config",
        lambda: ("https://supabase.example", "server-only-service-role"),
    )
    requests: list[httpx.Request] = []

    async def run_test() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={"properties": {"email_otp": "123456"}},
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            properties = await generate_auth_email_properties(
                client=client,
                request_id="test-request-id",
                email="person@example.com",
                email_type="signup",
                password="valid-password",
            )

        assert properties == {"email_otp": "123456"}

    asyncio.run(run_test())

    request = requests[0]
    assert request.url.path == "/auth/v1/admin/generate_link"
    assert request.headers["apikey"] == "server-only-service-role"
    assert request.headers["authorization"] == "Bearer server-only-service-role"
    assert request.read() == (
        b'{"type":"signup","email":"person@example.com",'
        b'"password":"valid-password"}'
    )


def test_generate_link_sanitizes_upstream_errors(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.authentication.email_auth.generate_auth_email_properties.supabase_admin_config",
        lambda: ("https://supabase.example", "server-only-service-role"),
    )

    async def run_test() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="sensitive upstream message")

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            with pytest.raises(HTTPException) as error:
                await generate_auth_email_properties(
                    client=client,
                    request_id="test-request-id",
                    email="person@example.com",
                    email_type="signup",
                    password="valid-password",
                )

        assert error.value.status_code == 502
        assert "sensitive upstream message" not in str(error.value.detail)

    asyncio.run(run_test())
