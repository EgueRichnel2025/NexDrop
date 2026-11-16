"""Initial database versioning checkpoint.

No business tables exist in this infrastructure-only phase. Domain models and
their schema will be introduced by subsequent, independently reviewable revisions.
"""

from collections.abc import Sequence

revision: str = "3e98c6e8eb34"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Establish the initial schema checkpoint without creating domain tables."""
    # Intentionally empty: this revision initializes Alembic version tracking only.


def downgrade() -> None:
    """Reverse the empty initial schema checkpoint."""
    # Intentionally empty: no business objects were created by this revision.
