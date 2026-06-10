"""Conflict resolution tracking

Revision ID: 003
Revises: 002
Create Date: 2026-05-24 10:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'conflicts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conflict_id', sa.String(64), nullable=False),
        sa.Column('entity_type', sa.String(32), nullable=False),
        sa.Column('entity_id', sa.String(64), nullable=False),
        sa.Column('local_version', sa.JSON(), nullable=False),
        sa.Column('server_version', sa.JSON(), nullable=False),
        sa.Column('local_timestamp', sa.DateTime(), nullable=False),
        sa.Column('server_timestamp', sa.DateTime(), nullable=False),
        sa.Column('conflict_type', sa.String(32), nullable=False),
        sa.Column('resolution', sa.String(32)),
        sa.Column('resolved_by', sa.Integer()),
        sa.Column('resolved_at', sa.DateTime()),
        sa.Column('resolution_policy', sa.String(32), default='timestamp_wins'),
        sa.Column('manual_override', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conflict_id')
    )
    op.create_index('ix_conflicts_entity_type_id', 'conflicts', ['entity_type', 'entity_id'])
    op.create_index('ix_conflicts_conflict_type', 'conflicts', ['conflict_type'])


def downgrade() -> None:
    op.drop_table('conflicts')
