"""Tighten transfer, invitation, and refresh-session invariants.

Revision ID: 041602a30cb7
Revises: 8d9e28ddd1c7
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "041602a30cb7"
down_revision: str | Sequence[str] | None = "8d9e28ddd1c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enforce snapshot limits, recipient consent, and same-session token rotation."""
    # A refresh-token replacement must stay within the same session.
    op.create_unique_constraint(
        "uq_session_refresh_tokens_id_session",
        "session_refresh_tokens",
        ["id", "session_id"],
    )
    op.drop_constraint(
        op.f("fk_session_refresh_tokens_replaced_by_id_session_refresh_tokens"),
        "session_refresh_tokens",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_session_refresh_tokens_replaced_by_id_session_refresh_tokens"),
        "session_refresh_tokens",
        "session_refresh_tokens",
        ["replaced_by_id", "session_id"],
        ["id", "session_id"],
        ondelete="RESTRICT",
    )

    # V1 invitations and their redemptions are single-recipient operations.
    op.add_column(
        "transfer_invitation_redemptions",
        sa.Column(
            "participant_role",
            sa.String(length=16),
            server_default=sa.text("'recipient'"),
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "uq_transfer_participants_id_transfer_user_role",
        "transfer_participants",
        ["id", "transfer_id", "user_id", "role"],
    )
    op.drop_constraint(
        op.f("fk_transfer_invitation_redemptions_participant_id_trans_47bd"),
        "transfer_invitation_redemptions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_transfer_invitation_redemptions_participant_id_transfer_participants"),
        "transfer_invitation_redemptions",
        "transfer_participants",
        ["participant_id", "transfer_id", "user_id", "participant_role"],
        ["id", "transfer_id", "user_id", "role"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        op.f("ck_transfer_invitation_redemptions_recipient_only"),
        "transfer_invitation_redemptions",
        "participant_role = 'recipient'",
    )
    op.create_check_constraint(
        op.f("ck_transfer_invitations_single_use_v1"),
        "transfer_invitations",
        "max_uses = 1",
    )

    # Enforce the size cap copied onto each transfer at authorization time.
    op.create_check_constraint(
        op.f("ck_transfers_expires_after_created"),
        "transfers",
        "expires_at > created_at",
    )
    op.create_check_constraint(
        op.f("ck_transfers_transfer_within_snapshot_limit"),
        "transfers",
        "max_transfer_bytes_snapshot IS NULL OR total_bytes <= max_transfer_bytes_snapshot",
    )
    op.create_check_constraint(
        op.f("ck_transfers_accepted_state_has_timestamp"),
        "transfers",
        "status NOT IN ('accepted', 'connecting', 'transferring', 'verifying', 'completed') "
        "OR accepted_at IS NOT NULL",
    )
    op.create_check_constraint(
        op.f("ck_transfers_started_state_has_timestamp"),
        "transfers",
        "status NOT IN ('connecting', 'transferring', 'verifying', 'completed') "
        "OR started_at IS NOT NULL",
    )
    op.create_check_constraint(
        op.f("ck_transfers_completed_state_has_timestamp"),
        "transfers",
        "status <> 'completed' OR completed_at IS NOT NULL",
    )
    op.create_check_constraint(
        op.f("ck_transfers_completion_timestamp_matches_state"),
        "transfers",
        "completed_at IS NULL OR status = 'completed'",
    )
    op.create_check_constraint(
        op.f("ck_transfer_participants_recipient_response_has_timestamp"),
        "transfer_participants",
        "role <> 'recipient' OR response_status = 'pending' OR responded_at IS NOT NULL",
    )


def downgrade() -> None:
    """Remove the additional invariants without deleting application data."""
    op.drop_constraint(
        op.f("ck_transfer_participants_recipient_response_has_timestamp"),
        "transfer_participants",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_transfers_completion_timestamp_matches_state"),
        "transfers",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_transfers_completed_state_has_timestamp"),
        "transfers",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_transfers_started_state_has_timestamp"),
        "transfers",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_transfers_accepted_state_has_timestamp"),
        "transfers",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_transfers_transfer_within_snapshot_limit"),
        "transfers",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_transfers_expires_after_created"),
        "transfers",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_transfer_invitations_single_use_v1"),
        "transfer_invitations",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_transfer_invitation_redemptions_recipient_only"),
        "transfer_invitation_redemptions",
        type_="check",
    )
    op.drop_constraint(
        op.f("fk_transfer_invitation_redemptions_participant_id_transfer_participants"),
        "transfer_invitation_redemptions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_transfer_invitation_redemptions_participant_id_trans_47bd"),
        "transfer_invitation_redemptions",
        "transfer_participants",
        ["participant_id", "transfer_id", "user_id"],
        ["id", "transfer_id", "user_id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "uq_transfer_participants_id_transfer_user_role",
        "transfer_participants",
        type_="unique",
    )
    op.drop_column("transfer_invitation_redemptions", "participant_role")

    op.drop_constraint(
        op.f("fk_session_refresh_tokens_replaced_by_id_session_refresh_tokens"),
        "session_refresh_tokens",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_session_refresh_tokens_replaced_by_id_session_refresh_tokens"),
        "session_refresh_tokens",
        "session_refresh_tokens",
        ["replaced_by_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "uq_session_refresh_tokens_id_session",
        "session_refresh_tokens",
        type_="unique",
    )
