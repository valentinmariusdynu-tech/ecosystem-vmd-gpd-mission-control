"""Initial schema — users, devices, matches, incidents, event_log, audit_log

Revision ID: 001
Revises: 
Create Date: 2026-05-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(128), nullable=False),
        sa.Column('hashed_password', sa.String(256)),
        sa.Column('first_name', sa.String(64)),
        sa.Column('last_name', sa.String(64)),
        sa.Column('phone', sa.String(32)),
        sa.Column('role', sa.String(32), default='spectator'),
        sa.Column('permissions', sa.JSON()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('failed_login_attempts', sa.Integer(), default=0),
        sa.Column('locked_until', sa.DateTime()),
        sa.Column('last_login', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('created_by', sa.Integer()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # devices
    op.create_table(
        'devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(64), nullable=False),
        sa.Column('device_type', sa.String(32), nullable=False),
        sa.Column('status', sa.String(32), default='pending'),
        sa.Column('name', sa.String(128)),
        sa.Column('owner_id', sa.Integer()),
        sa.Column('assigned_match_id', sa.Integer()),
        sa.Column('public_key', sa.String(512)),
        sa.Column('trust_score', sa.Integer(), default=0),
        sa.Column('last_attestation', sa.DateTime()),
        sa.Column('capabilities', sa.JSON()),
        sa.Column('mesh_node_id', sa.String(64)),
        sa.Column('last_seen_mesh', sa.DateTime()),
        sa.Column('firmware_version', sa.String(32)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id')
    )

    # matches
    op.create_table(
        'matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.String(32), nullable=False),
        sa.Column('home_team', sa.String(128), nullable=False),
        sa.Column('away_team', sa.String(128), nullable=False),
        sa.Column('home_score', sa.Integer(), default=0),
        sa.Column('away_score', sa.Integer(), default=0),
        sa.Column('status', sa.String(32), default='scheduled'),
        sa.Column('phase', sa.String(32), default='regular'),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('ended_at', sa.DateTime()),
        sa.Column('venue_id', sa.Integer()),
        sa.Column('field_number', sa.Integer()),
        sa.Column('referee_id', sa.Integer()),
        sa.Column('assistant_1_id', sa.Integer()),
        sa.Column('assistant_2_id', sa.Integer()),
        sa.Column('var_id', sa.Integer()),
        sa.Column('config', sa.JSON()),
        sa.Column('competition_id', sa.Integer()),
        sa.Column('season', sa.String(16)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('match_id')
    )

    # incidents
    op.create_table(
        'incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.String(32), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('reported_by_device_id', sa.String(64)),
        sa.Column('incident_type', sa.String(32), nullable=False),
        sa.Column('severity', sa.String(32), default='low'),
        sa.Column('minute', sa.Integer()),
        sa.Column('description', sa.Text()),
        sa.Column('media_urls', sa.JSON()),
        sa.Column('validated_by', sa.Integer()),
        sa.Column('validated_at', sa.DateTime()),
        sa.Column('validation_status', sa.String(16), default='pending'),
        sa.Column('local_timestamp', sa.DateTime()),
        sa.Column('synced_at', sa.DateTime()),
        sa.Column('sync_batch_id', sa.String(32)),
        sa.Column('idempotency_key', sa.String(64)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('incident_id'),
        sa.UniqueConstraint('idempotency_key')
    )

    # event_log
    op.create_table(
        'event_log',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('event_id', sa.String(64), nullable=False),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('payload_hash', sa.String(64)),
        sa.Column('source_device_id', sa.String(64)),
        sa.Column('source_service', sa.String(64)),
        sa.Column('idempotency_key', sa.String(64)),
        sa.Column('event_signature', sa.String(512)),
        sa.Column('replay_status', sa.String(16), default='original'),
        sa.Column('replay_of', sa.String(64)),
        sa.Column('event_timestamp', sa.DateTime(), nullable=False),
        sa.Column('received_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime()),
        sa.Column('partition_key', sa.String(32)),
        sa.Column('tags', sa.JSON()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id'),
        sa.UniqueConstraint('idempotency_key')
    )

    # audit_log
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('user_id', sa.Integer()),
        sa.Column('details', sa.JSON()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(256)),
        sa.Column('resource_type', sa.String(64)),
        sa.Column('resource_id', sa.String(64)),
        sa.Column('success', sa.String(16), default='success'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes
    op.create_index('ix_event_log_event_type', 'event_log', ['event_type'])
    op.create_index('ix_event_log_source_device_id', 'event_log', ['source_device_id'])
    op.create_index('ix_event_log_event_timestamp', 'event_log', ['event_timestamp'])
    op.create_index('ix_audit_log_action', 'audit_log', ['action'])
    op.create_index('ix_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('ix_incidents_match_id', 'incidents', ['match_id'])


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('event_log')
    op.drop_table('incidents')
    op.drop_table('matches')
    op.drop_table('devices')
    op.drop_table('users')
