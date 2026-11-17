"""Plans, subscriptions, and payment reference models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from nexdrop_api.db.base import Base


class Plan(Base):
    """An authoritative set of server-enforced Internet transfer entitlements."""

    __tablename__ = "plans"
    __table_args__ = (
        CheckConstraint(
            "max_transfer_bytes IS NULL OR max_transfer_bytes >= 0",
            name="max_transfer_bytes_non_negative",
        ),
        UniqueConstraint("code", name="uq_plans_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    max_transfer_bytes: Mapped[int | None] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Subscription(Base):
    """The paid subscription history for one account."""

    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'active', 'past_due', 'cancelled', 'expired')",
            name="status",
        ),
        CheckConstraint(
            "current_period_end IS NULL OR current_period_start IS NULL "
            "OR current_period_end > current_period_start",
            name="period_is_valid",
        ),
        UniqueConstraint("id", "user_id", name="uq_subscriptions_id_user"),
        Index("ix_subscriptions_user_status", "user_id", "status"),
        Index(
            "uq_subscriptions_one_effective_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("status IN ('active', 'past_due')"),
        ),
        Index(
            "uq_subscriptions_provider_reference",
            "provider",
            "provider_subscription_id",
            unique=True,
            postgresql_where=text("provider_subscription_id IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    plan_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    provider: Mapped[str | None] = mapped_column(String(30))
    provider_subscription_id: Mapped[str | None] = mapped_column(String(160))
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Payment(Base):
    """A payment reference without card data or payment credentials."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount_minor >= 0", name="amount_minor_non_negative"),
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="currency_iso_code"),
        CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed', 'refunded', 'partially_refunded')",
            name="status",
        ),
        ForeignKeyConstraint(
            ["subscription_id", "user_id"],
            ["subscriptions.id", "subscriptions.user_id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "provider", "provider_payment_id", name="uq_payments_provider_payment_reference"
        ),
        Index("ix_payments_user_created_at", "user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    subscription_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    provider_payment_id: Mapped[str | None] = mapped_column(String(160))
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
