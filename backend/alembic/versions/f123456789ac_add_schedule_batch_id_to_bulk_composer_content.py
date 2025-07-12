"""Add schedule_batch_id to bulk_composer_content

Revision ID: f123456789ac
Revises: e123456789ab
Create Date: 2025-06-25 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f123456789ac'
down_revision = 'e123456789ab'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('bulk_composer_content', sa.Column('schedule_batch_id', sa.String(length=64), nullable=True))
    op.create_index('ix_bulk_composer_content_schedule_batch_id', 'bulk_composer_content', ['schedule_batch_id'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_bulk_composer_content_schedule_batch_id', table_name='bulk_composer_content')
    op.drop_column('bulk_composer_content', 'schedule_batch_id') 