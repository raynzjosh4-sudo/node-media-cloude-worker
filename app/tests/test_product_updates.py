import asyncio

import pytest

from app.products.helpers import replace_primary_media_url
from app.products.supabase import products as products_client


def test_replace_primary_media_url_removes_old_primary_and_preserves_gallery() -> None:
    assert replace_primary_media_url(
        ["old-primary.jpg", "gallery.jpg", "new-primary.jpg"],
        "old-primary.jpg",
        "new-primary.jpg",
    ) == ["new-primary.jpg", "gallery.jpg"]


def test_update_product_raises_when_supabase_returns_no_rows(monkeypatch) -> None:
    captured_headers = {}

    class EmptyResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> list:
            return []

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            return None

        async def patch(self, url, *, params, json, headers):
            captured_headers.update(headers)
            return EmptyResponse()

    monkeypatch.setattr(
        products_client.httpx,
        "AsyncClient",
        lambda: FakeAsyncClient(),
    )

    with pytest.raises(RuntimeError, match="did not return an updated row"):
        asyncio.run(
            products_client.update_product(
                "product-id",
                {"image_url": "https://cdn.example/new-image.jpg"},
            )
        )

    assert captured_headers["Authorization"] == (
        f"Bearer {products_client.SUPABASE_ADMIN_KEY}"
    )
