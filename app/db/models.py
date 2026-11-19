from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: uuid4().hex, index=True)
    email = Column(String(254), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class VerificationToken(Base):
    __tablename__ = "verification_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(254), index=True, nullable=False)
    token = Column(String(64), nullable=False, index=True)
    token_type = Column(String(20), nullable=False)  # "signup", "recovery"
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class EmailImage(Base):
    __tablename__ = "email_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    image_url = Column(String(500), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


