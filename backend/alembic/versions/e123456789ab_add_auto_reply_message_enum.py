"""Add AUTO_REPLY_MESSAGE to ruletype enum

Revision ID: e123456789ab
Revises: d123456789ef
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'e123456789ab'
down_revision = 'd123456789ef'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add AUTO_REPLY_MESSAGE to the ruletype enum."""
    # Add the new enum value to the existing enum
    op.execute("ALTER TYPE ruletype ADD VALUE 'AUTO_REPLY_MESSAGE'")


def downgrade() -> None:
    """Remove AUTO_REPLY_MESSAGE from the ruletype enum."""
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex
    # For now, we'll leave this as a no-op
    pass 