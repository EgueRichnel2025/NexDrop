"""Account, registered device, and revocable authentication-session models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from nexdrop_api.db.base import Base


class User(Base):
    """An account used for authenticated Internet transfers."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'active', 'suspended', 'deleted')", name="status"),
        UniqueConstraint("email_normalized", name="uq_users_email_normalized"),
        Index("ix_users_status_created_at", "status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    email_normalized: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default="fr")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Device(Base):
    """A NexDrop installation registered to one account."""

    __tablename__ = "devices"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'revoked')", name="status"),
        UniqueConstraint("user_id", "installation_id", name="uq_devices_user_installation"),
        UniqueConstraint("id", "user_id", name="uq_devices_id_user"),
        Index("ix_devices_user_status", "user_id", "status"),
        Index("ix_devices_last_seen_at", "last_seen_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    installation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    app_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Session(Base):
    """A revocable authenticated session, optionally bound to a device."""

    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="expires_after_created"),
        ForeignKeyConstraint(
            ["device_id", "user_id"],
            ["devices.id", "devices.user_id"],
            ondelete="RESTRICT",
        ),
        Index("ix_sessions_user_expires_at", "user_id", "expires_at"),
        Index("ix_sessions_device_id", "device_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    device_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str | None] = mapped_column(String(40))


class SessionRefreshToken(Base):
    """A hashed refresh token in a single-use rotation chain."""

    __tablename__ = "session_refresh_tokens"
    __table_args__ = (
        CheckConstraint("expires_at > issued_at", name="expires_after_issued"),
        CheckConstraint("octet_length(token_hash) = 32", name="token_hash_sha256_length"),
        UniqueConstraint("token_hash", name="uq_session_refresh_tokens_token_hash"),
        UniqueConstraint("id", "session_id", name="uq_session_refresh_tokens_id_session"),
        ForeignKeyConstraint(
            ["replaced_by_id", "session_id"],
            ["session_refresh_tokens.id", "session_refresh_tokens.session_id"],
            ondelete="RESTRICT",
        ),
        Index(
            "uq_session_refresh_tokens_current_per_session",
            "session_id",
            unique=True,
            postgresql_where=text("consumed_at IS NULL AND revoked_at IS NULL"),
        ),
        Index("ix_session_refresh_tokens_session_id", "session_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sessions.id", ondelete="RESTRICT"), nullable=False
    )
    token_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
