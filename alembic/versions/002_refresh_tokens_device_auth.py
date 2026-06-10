"""Refresh tokens table + device-bound auth

Revision ID: 002
Revises: 001
Create Date: 2026-05-24 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(128), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(64)),
        sa.Column('rotation_id', sa.String(64)),
        sa.Column('issued_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime()),
        sa.Column('revoked_reason', sa.String(128)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(256)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_device_id', 'refresh_tokens', ['device_id'])

    # Add device_id to users for device-bound auth
    op.add_column('users', sa.Column('bound_device_id', sa.String(64)))
    op.add_column('users', sa.Column('offline_auth_window', sa.Integer(), default=3600))  # 1 hour

    # Add entity_version to event_log for conflict detection
    op.add_column('event_log', sa.Column('entity_version', sa.Integer(), default=1))
    op.add_column('event_log', sa.Column('base_revision', sa.String(64)))
    op.add_column('event_log', sa.Column('server_revision', sa.String(64)))
    op.add_column('event_log', sa.Column('conflict_type', sa.String(32)))
    op.add_column('event_log', sa.Column('resolution_policy', sa.String(32), default='timestamp_wins'))

    # Add schema_version to event_log
    op.add_column('event_log', sa.Column('schema_version', sa.String(16), default='1.0'))

    # Add strict idempotency constraint
    op.create_index('ix_event_log_idempotency_payload', 'event_log', ['idempotency_key', 'payload_hash'])


def downgrade() -> None:
    op.drop_table('refresh_tokens')
    op.drop_column('users', 'bound_device_id')
    op.drop_column('users', 'offline_auth_window')
    op.drop_column('event_log', 'entity_version')
    op.drop_column('event_log', 'base_revision')
    op.drop_column('event_log', 'server_revision')
    op.drop_column('event_log', 'conflict_type')
    op.drop_column('event_log', 'resolution_policy')
    op.drop_column('event_log', 'schema_version')
    op.drop_index('ix_event_log_idempotency_payload', table_name='event_log')
