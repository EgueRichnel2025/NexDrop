"""Import every mapped model so SQLAlchemy metadata is complete for Alembic."""

from nexdrop_api.db.models.billing import Payment, Plan, Subscription
from nexdrop_api.db.models.identity import Device, Session, SessionRefreshToken, User
from nexdrop_api.db.models.transfers import (
    Transfer,
    TransferEvent,
    TransferInvitation,
    TransferInvitationRedemption,
    TransferParticipant,
    TransferUsageRecord,
)

__all__ = [
    "Device",
    "Payment",
    "Plan",
    "Session",
    "SessionRefreshToken",
    "Subscription",
    "Transfer",
    "TransferEvent",
    "TransferInvitation",
    "TransferInvitationRedemption",
    "TransferParticipant",
    "TransferUsageRecord",
    "User",
]
