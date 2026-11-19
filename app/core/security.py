import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# JWT Configuration
DEFAULT_SECRET = "insecure-dev-secret-key-change-in-production-node-api-backend"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", DEFAULT_SECRET)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))  # 24 hours default


# ---------------------------------------------------------
# Password Hashing & Verification (PBKDF2-HMAC-SHA256)
# ---------------------------------------------------------
def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return f"pbkdf2_sha256$100000${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored PBKDF2 hash."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = parts[2]
        expected_hex = parts[3]

        key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(key.hex(), expected_hex)
    except Exception as exc:
        logger.warning("Error verifying password hash: %s", exc)
        return False


# ---------------------------------------------------------
# JWT Implementation (RFC 7519 Compliant HMAC-SHA256)
# ---------------------------------------------------------
def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    now = int(time.time())
    if expires_delta:
        expire = now + int(expires_delta.total_seconds())
    else:
        expire = now + (JWT_EXPIRATION_MINUTES * 60)

    to_encode.update({"iat": now, "exp": expire})

    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_json = json.dumps(to_encode, separators=(",", ":")).encode("utf-8")

    segments = [
        _b64url_encode(header_json),
        _b64url_encode(payload_json),
    ]
    signing_input = ".".join(segments).encode("ascii")
    signature = hmac.new(
        JWT_SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()

    segments.append(_b64url_encode(signature))
    return ".".join(segments)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a signed JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = hmac.new(
            JWT_SECRET_KEY.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()

        actual_sig = _b64url_decode(signature_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token signature.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload_bytes = _b64url_decode(payload_b64)
        payload: dict[str, Any] = json.loads(payload_bytes.decode("utf-8"))

        # Verify expiration
        exp = payload.get("exp")
        if exp is not None and time.time() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Token decoding failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ---------------------------------------------------------
# OTP Generator
# ---------------------------------------------------------
def generate_numeric_otp(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP string (e.g. '482915')."""
    max_num = 10**length
    code = secrets.randbelow(max_num)
    return f"{code:0{length}d}"

