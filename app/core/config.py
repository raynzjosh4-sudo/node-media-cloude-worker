import os

from dotenv import load_dotenv
from fastapi import HTTPException, status

load_dotenv(override=True)


def app_environment() -> str:
    environment = os.getenv("APP_ENV", "development").strip().lower()
    if environment not in {"development", "test", "production"}:
        raise RuntimeError("APP_ENV must be development, test, or production.")
    return environment


def is_production() -> bool:
    return app_environment() == "production"


def database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./node_api.db").strip()


def jwt_secret_key() -> str:
    key = os.getenv("JWT_SECRET_KEY", "insecure-dev-secret-key-change-in-production-node-api-backend-32-chars").strip()
    if is_production() and ("insecure" in key or len(key) < 32):
        raise RuntimeError("Production requires a strong JWT_SECRET_KEY (at least 32 characters).")
    return key


def resend_api_key() -> str:
    return os.getenv("RESEND_API_KEY", "").strip()


def resend_from_email() -> str:
    return os.getenv("RESEND_FROM_EMAIL", "no-reply@mail.crimchart.com").strip()


def cors_allowed_origins() -> list[str]:
    default = "" if is_production() else "*"
    origins = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOWED_ORIGINS", default).split(",")
        if origin.strip()
    ]
    if is_production() and (not origins or "*" in origins):
        raise RuntimeError(
            "Set CORS_ALLOWED_ORIGINS to explicit web origins in production."
        )
    return origins


def allowed_hosts() -> list[str]:
    default = "" if is_production() else "*"
    hosts = [
        host.strip()
        for host in os.getenv("ALLOWED_HOSTS", default).split(",")
        if host.strip()
    ]
    if is_production() and (not hosts or "*" in hosts):
        raise RuntimeError("Set ALLOWED_HOSTS to explicit host names in production.")
    return hosts


def validate_production_config() -> None:
    if not is_production():
        return

    jwt_secret_key()
    cors_allowed_origins()
    allowed_hosts()
    if not resend_api_key():
        raise RuntimeError("Production requires a valid RESEND_API_KEY.")


def supabase_url() -> str:
    return os.getenv("SUPABASE_URL", "https://lihoygvdnnfqodjjxqnz.supabase.co").strip()


def supabase_anon_key() -> str:
    return os.getenv(
        "SUPABASE_ANON_KEY",
        "sb_publishable_xknRF_gqAzQqznqNvSONRg_j6GkQdrS",
    ).strip()


def supabase_auth_config() -> tuple[str, str]:
    return supabase_url(), supabase_anon_key()


def supabase_admin_config() -> tuple[str, str]:
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", supabase_anon_key()).strip()
    return supabase_url(), service_role_key


class SmtpConfig:
    def __init__(
        self,
        host: str = "",
        port: int = 587,
        username: str = "",
        password: str = "",
        from_address: str = "",
        from_name: str = "N.O.D.E.",
        use_ssl: bool = False,
        use_starttls: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_address = from_address
        self.from_name = from_name
        self.use_ssl = use_ssl
        self.use_starttls = use_starttls


def r2_public_url() -> str:
    """Cloudflare R2 public base CDN URL from Flutter project."""
    return os.getenv("R2_PUBLIC_URL", "https://nodemediafiles.crimchart.com").rstrip("/")


def cloudflare_media_endpoint() -> str:
    """Cloudflare media upload worker endpoint."""
    return os.getenv("CLOUDFLARE_MEDIA_ENDPOINT", f"{r2_public_url()}/_node/media").strip()


def backend_base_url() -> str:
    """Public base URL for this backend service (used to build absolute static-file URLs)."""
    return os.getenv(
        "BACKEND_BASE_URL", "https://n-o-d-e-backent.onrender.com"
    ).rstrip("/")

