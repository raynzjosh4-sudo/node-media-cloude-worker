import asyncio

import pytest
from fastapi import HTTPException

from app.services import cloud_media_service


class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class FakeAsyncClient:
    def __init__(self, responses: list[FakeResponse], captured_headers: list[dict]) -> None:
        self.responses = responses
        self.captured_headers = captured_headers

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

    async def post(self, url, *, headers, content):
        self.captured_headers.append(headers)
        return self.responses.pop(0)


def _mock_upload_configuration(monkeypatch, responses: list[FakeResponse]):
    captured_headers: list[dict] = []
    monkeypatch.setattr(cloud_media_service, "compress_image", lambda data, **kwargs: (data, "image/jpeg"))
    monkeypatch.setattr(cloud_media_service, "is_production", lambda: True)
    monkeypatch.setattr(
        cloud_media_service,
        "cloudflare_media_endpoint",
        lambda: "https://media.example/upload",
    )
    monkeypatch.setattr(
        cloud_media_service,
        "supabase_admin_config",
        lambda: ("https://supabase.example", "service-role-key"),
    )
    monkeypatch.setattr(cloud_media_service, "supabase_anon_key", lambda: "anon-key")
    monkeypatch.setattr(
        cloud_media_service.httpx,
        "AsyncClient",
        lambda timeout: FakeAsyncClient(responses, captured_headers),
    )
    return captured_headers


def test_supabase_storage_fallback_uses_service_role_and_persistent_url(monkeypatch) -> None:
    captured_headers = _mock_upload_configuration(
        monkeypatch,
        [FakeResponse(503), FakeResponse(201)],
    )

    image_url = asyncio.run(
        cloud_media_service.upload_to_cloudflare(
            b"image-bytes",
            "photo.jpg",
            token="user-access-token",
        )
    )

    assert image_url.startswith(
        "https://supabase.example/storage/v1/object/public/products/"
    )
    assert captured_headers[0]["Authorization"] == "Bearer user-access-token"
    assert captured_headers[1]["Authorization"] == "Bearer service-role-key"


def test_production_upload_does_not_return_ephemeral_static_url(monkeypatch) -> None:
    _mock_upload_configuration(
        monkeypatch,
        [FakeResponse(503), FakeResponse(404)],
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            cloud_media_service.upload_to_cloudflare(
                b"image-bytes",
                "photo.jpg",
                token="user-access-token",
            )
        )

    assert exc_info.value.status_code == 502
    assert "no persistent image was saved" in exc_info.value.detail
