import pytest

from app.core.config import allowed_hosts, cors_allowed_origins, validate_production_config


def test_production_requires_explicit_cors_origins(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "*")

    with pytest.raises(RuntimeError, match="explicit web origins"):
        cors_allowed_origins()


def test_production_requires_explicit_allowed_hosts(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ALLOWED_HOSTS", "*")

    with pytest.raises(RuntimeError, match="explicit host names"):
        allowed_hosts()


def test_production_requires_https_supabase_url(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SUPABASE_URL", "http://supabase.example")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://app.example")
    monkeypatch.setenv("ALLOWED_HOSTS", "api.example")

    with pytest.raises(RuntimeError, match="HTTPS SUPABASE_URL"):
        validate_production_config()


def test_production_requires_smtp_email_settings(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SUPABASE_URL", "https://supabase.example")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://app.example")
    monkeypatch.setenv("ALLOWED_HOSTS", "api.example")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_FROM_ADDRESS", raising=False)

    with pytest.raises(RuntimeError, match="SMTP email settings"):
        validate_production_config()
