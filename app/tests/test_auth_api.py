import importlib

from fastapi.testclient import TestClient

from app.main import app


def test_auth_routes_are_registered() -> None:
    paths = app.openapi()["paths"]
    expected_methods = {
        "/api/v1/auth/email/sign-in": {"post"},
        "/api/v1/auth/email/sign-up": {"post"},
        "/api/v1/auth/email/otp/verify": {"post"},
        "/api/v1/auth/email/otp/resend": {"post"},
        "/api/v1/auth/email/password-reset": {"post"},
        "/api/v1/auth/email/password": {"put"},
        "/api/v1/auth/email/pending-account": {"delete"},
        "/api/v1/auth/account": {"delete"},
    }

    for path, methods in expected_methods.items():
        assert set(paths[path]) == methods


def test_sign_up_generates_code_and_sends_email(monkeypatch) -> None:
    endpoint = importlib.import_module("app.authentication.email_auth.endpoints.sign_up")
    generated: dict[str, object] = {}
    sent: dict[str, object] = {}

    async def fake_generate_auth_email_properties(**kwargs):
        generated.update(kwargs)
        return {"email_otp": "123456"}

    async def fake_send_auth_email(**kwargs):
        sent.update(kwargs)

    monkeypatch.setattr(
        endpoint,
        "generate_auth_email_properties",
        fake_generate_auth_email_properties,
    )
    monkeypatch.setattr(endpoint, "send_auth_email", fake_send_auth_email)

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/auth/email/sign-up",
            json={"email": "person@example.com", "password": "valid-password"},
        )

    assert response.status_code == 202
    assert response.json()["message"]
    assert generated["request_id"] == response.headers["x-request-id"]
    assert generated["email"] == "person@example.com"
    assert generated["email_type"] == "signup"
    assert generated["password"] == "valid-password"
    assert sent == {
        "recipient": "person@example.com",
        "subject": "Verify your N.O.D.E. email",
        "template_name": "email_verification.html",
        "request_id": response.headers["x-request-id"],
        "template_values": {"TOKEN": "123456"},
    }


def test_password_update_requires_bearer_token() -> None:
    with TestClient(app) as test_client:
        response = test_client.put(
            "/api/v1/auth/email/password",
            json={"password": "new-valid-password"},
        )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "unauthorized"
    assert response.json()["request_id"] == response.headers["x-request-id"]


def test_invalid_request_does_not_echo_submitted_password() -> None:
    secret = "never-echo-this-password"
    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/auth/email/sign-up",
            json={"email": "not-an-email", "password": secret},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
    assert secret not in response.text
    assert response.headers["x-request-id"] == response.json()["request_id"]


def test_unexpected_error_is_generic_and_logged_with_request_id(
    monkeypatch,
    caplog,
) -> None:
    endpoint = importlib.import_module("app.authentication.email_auth.endpoints.sign_up")

    async def fail_generate_auth_email_properties(**kwargs):
        raise RuntimeError("sensitive upstream detail")

    monkeypatch.setattr(
        endpoint,
        "generate_auth_email_properties",
        fail_generate_auth_email_properties,
    )

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.post(
            "/api/v1/auth/email/sign-up",
            json={"email": "person@example.com", "password": "valid-password"},
        )

    assert response.status_code == 500
    assert "sensitive upstream detail" not in response.text
    request_id = response.headers["x-request-id"]
    assert response.json()["request_id"] == request_id
    assert any(
        getattr(record, "request_id", None) == request_id
        for record in caplog.records
    )


def test_resend_signup_otp_sends_generated_code(monkeypatch) -> None:
    endpoint = importlib.import_module(
        "app.authentication.email_auth.endpoints.resend_signup_otp"
    )
    generated: dict[str, object] = {}
    sent: dict[str, object] = {}

    async def fake_generate_auth_email_properties(**kwargs):
        generated.update(kwargs)
        return {"email_otp": "654321"}

    async def fake_send_auth_email(**kwargs):
        sent.update(kwargs)

    monkeypatch.setattr(
        endpoint,
        "generate_auth_email_properties",
        fake_generate_auth_email_properties,
    )
    monkeypatch.setattr(endpoint, "send_auth_email", fake_send_auth_email)

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/auth/email/otp/resend",
            json={"email": "person@example.com"},
        )

    assert response.status_code == 202
    assert generated["email"] == "person@example.com"
    assert generated["email_type"] == "signup"
    assert "password" not in generated
    assert sent["recipient"] == "person@example.com"
    assert sent["template_values"] == {"TOKEN": "654321"}


def test_password_reset_generates_link_and_sends_email(monkeypatch) -> None:
    endpoint = importlib.import_module(
        "app.authentication.email_auth.endpoints.request_password_reset"
    )
    generated: dict[str, object] = {}
    sent: dict[str, object] = {}

    async def fake_generate_auth_email_properties(**kwargs):
        generated.update(kwargs)
        return {"action_link": "https://auth.example/reset?token=abc"}

    async def fake_send_auth_email(**kwargs):
        sent.update(kwargs)

    monkeypatch.setattr(
        endpoint,
        "generate_auth_email_properties",
        fake_generate_auth_email_properties,
    )
    monkeypatch.setattr(endpoint, "send_auth_email", fake_send_auth_email)

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/auth/email/password-reset",
            json={
                "email": "person@example.com",
                "redirect_to": "https://app.example/reset",
            },
        )

    assert response.status_code == 202
    assert generated["email_type"] == "recovery"
    assert generated["redirect_to"] == "https://app.example/reset"
    assert generated["allow_missing_user"] is True
    assert sent["template_values"] == {
        "ACTION_LINK": "https://auth.example/reset?token=abc",
    }
