"""Internet transfer, invitation, consent, and audit persistence models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from nexdrop_api.db.base import Base


class Transfer(Base):
    """Control-plane metadata for one Internet transfer (never file contents)."""

    __tablename__ = "transfers"
    __table_args__ = (
        CheckConstraint(
            "status IN ('awaiting_receiver', 'accepted', 'connecting', "
            "'transferring', 'verifying', 'completed', 'declined', "
            "'cancelled', 'expired', 'failed')",
            name="status",
        ),
        CheckConstraint("total_bytes >= 0", name="total_bytes_non_negative"),
        CheckConstraint("item_count > 0", name="item_count_positive"),
        CheckConstraint(
            "max_transfer_bytes_snapshot IS NULL OR max_transfer_bytes_snapshot >= 0",
            name="snapshot_limit_non_negative",
        ),
        CheckConstraint("version > 0", name="version_positive"),
        CheckConstraint("expires_at > created_at", name="expires_after_created"),
        CheckConstraint(
            "max_transfer_bytes_snapshot IS NULL OR total_bytes <= max_transfer_bytes_snapshot",
            name="transfer_within_snapshot_limit",
        ),
        CheckConstraint(
            "status NOT IN ('accepted', 'connecting', 'transferring', 'verifying', 'completed') "
            "OR accepted_at IS NOT NULL",
            name="accepted_state_has_timestamp",
        ),
        CheckConstraint(
            "status NOT IN ('connecting', 'transferring', 'verifying', 'completed') "
            "OR started_at IS NOT NULL",
            name="started_state_has_timestamp",
        ),
        CheckConstraint(
            "status <> 'completed' OR completed_at IS NOT NULL",
            name="completed_state_has_timestamp",
        ),
        CheckConstraint(
            "completed_at IS NULL OR status = 'completed'",
            name="completion_timestamp_matches_state",
        ),
        CheckConstraint(
            "octet_length(manifest_digest) = 32 OR manifest_digest IS NULL",
            name="manifest_digest_length",
        ),
        ForeignKeyConstraint(
            ["created_by_device_id", "created_by_user_id"],
            ["devices.id", "devices.user_id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint("id", "created_by_user_id", name="uq_transfers_id_creator"),
        Index("ix_transfers_creator_created_at", "created_by_user_id", "created_at"),
        Index("ix_transfers_status_expires_at", "status", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    created_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_by_device_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    plan_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="awaiting_receiver")
    total_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False)
    manifest_digest: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    plan_code_snapshot: Mapped[str] = mapped_column(String(30), nullable=False)
    max_transfer_bytes_snapshot: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )

    __mapper_args__ = {"version_id_col": version}


class TransferParticipant(Base):
    """One user's role and explicit consent in an Internet transfer."""

    __tablename__ = "transfer_participants"
    __table_args__ = (
        CheckConstraint("role IN ('sender', 'recipient')", name="role"),
        CheckConstraint(
            "response_status IN ('pending', 'accepted', 'declined', 'revoked')",
            name="response_status",
        ),
        CheckConstraint(
            "role <> 'recipient' OR response_status = 'pending' OR responded_at IS NOT NULL",
            name="recipient_response_has_timestamp",
        ),
        ForeignKeyConstraint(
            ["device_id", "user_id"],
            ["devices.id", "devices.user_id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint("transfer_id", "user_id", name="uq_transfer_participants_transfer_user"),
        UniqueConstraint(
            "id", "transfer_id", "user_id", name="uq_transfer_participants_id_transfer_user"
        ),
        UniqueConstraint(
            "id",
            "transfer_id",
            "user_id",
            "role",
            name="uq_transfer_participants_id_transfer_user_role",
        ),
        Index(
            "uq_transfer_participants_one_sender",
            "transfer_id",
            unique=True,
            postgresql_where=text("role = 'sender'"),
        ),
        Index(
            "uq_transfer_participants_one_recipient",
            "transfer_id",
            unique=True,
            postgresql_where=text("role = 'recipient'"),
        ),
        Index("ix_transfer_participants_user_joined", "user_id", "joined_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    transfer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("transfers.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    device_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    response_status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TransferInvitation(Base):
    """A revocable, expiring code or secret link invitation."""

    __tablename__ = "transfer_invitations"
    __table_args__ = (
        CheckConstraint("kind IN ('code', 'link')", name="kind"),
        CheckConstraint("max_uses > 0", name="max_uses_positive"),
        CheckConstraint("max_uses = 1", name="single_use_v1"),
        CheckConstraint("use_count >= 0 AND use_count <= max_uses", name="use_count_in_range"),
        CheckConstraint("expires_at > created_at", name="expires_after_created"),
        CheckConstraint("octet_length(token_digest) = 32", name="token_digest_sha256_length"),
        ForeignKeyConstraint(
            ["transfer_id", "created_by_user_id"],
            ["transfers.id", "transfers.created_by_user_id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint("token_digest", name="uq_transfer_invitations_token_digest"),
        UniqueConstraint("id", "transfer_id", name="uq_transfer_invitations_id_transfer"),
        Index("ix_transfer_invitations_transfer_expires", "transfer_id", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    transfer_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    kind: Mapped[str] = mapped_column(String(12), nullable=False)
    token_digest: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_uses: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    use_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TransferInvitationRedemption(Base):
    """Idempotent record of a participant redeeming an invitation."""

    __tablename__ = "transfer_invitation_redemptions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["invitation_id", "transfer_id"],
            ["transfer_invitations.id", "transfer_invitations.transfer_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["participant_id", "transfer_id", "user_id", "participant_role"],
            [
                "transfer_participants.id",
                "transfer_participants.transfer_id",
                "transfer_participants.user_id",
                "transfer_participants.role",
            ],
            ondelete="RESTRICT",
        ),
        CheckConstraint("participant_role = 'recipient'", name="recipient_only"),
        UniqueConstraint(
            "invitation_id",
            "participant_id",
            name="uq_invitation_redemptions_invitation_participant",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    invitation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    participant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    transfer_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    participant_role: Mapped[str] = mapped_column(
        String(16), nullable=False, default="recipient", server_default=text("'recipient'")
    )
    redeemed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TransferEvent(Base):
    """Append-only transfer lifecycle and security event metadata."""

    __tablename__ = "transfer_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["actor_device_id", "actor_user_id"],
            ["devices.id", "devices.user_id"],
            ondelete="SET NULL",
        ),
        CheckConstraint("jsonb_typeof(event_data) = 'object'", name="event_data_is_object"),
        Index("ix_transfer_events_transfer_created", "transfer_id", "created_at"),
        Index("ix_transfer_events_actor_created", "actor_user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    transfer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("transfers.id", ondelete="RESTRICT"), nullable=False
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    actor_device_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(24))
    to_status: Mapped[str | None] = mapped_column(String(24))
    event_data: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TransferUsageRecord(Base):
    """One idempotent completed-transfer usage record per participant."""

    __tablename__ = "transfer_usage_records"
    __table_args__ = (
        CheckConstraint("bytes_transferred >= 0", name="bytes_transferred_non_negative"),
        ForeignKeyConstraint(
            ["participant_id", "transfer_id", "user_id"],
            [
                "transfer_participants.id",
                "transfer_participants.transfer_id",
                "transfer_participants.user_id",
            ],
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "transfer_id", "participant_id", name="uq_transfer_usage_transfer_participant"
        ),
        Index("ix_transfer_usage_user_recorded", "user_id", "recorded_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    transfer_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    participant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    bytes_transferred: Mapped[int] = mapped_column(BigInteger, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
