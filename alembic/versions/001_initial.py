"""Initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(32), nullable=True),
        sa.Column('first_name', sa.String(64), nullable=False),
        sa.Column('last_name', sa.String(64), nullable=True),
        sa.Column('language_code', sa.String(10), nullable=True),
        sa.Column('is_bot', sa.Boolean(), default=False),
        sa.Column('is_premium', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'])
    op.create_index('ix_users_username', 'users', ['username'])

    # Groups table
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('username', sa.String(32), nullable=True),
        sa.Column('member_count', sa.Integer(), default=0),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('timezone', sa.String(50), default='UTC'),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('is_premium', sa.Boolean(), default=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    op.create_index('ix_groups_telegram_id', 'groups', ['telegram_id'])
    op.create_index('ix_groups_username', 'groups', ['username'])

    # Bot instances table
    op.create_table(
        'bot_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False),
        sa.Column('bot_telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('bot_username', sa.String(32), nullable=False),
        sa.Column('bot_name', sa.String(64), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('registered_by', sa.Integer(), nullable=False),
        sa.Column('registered_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('webhook_url', sa.String(500), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['registered_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
        sa.UniqueConstraint('group_id')
    )

    # Members table
    op.create_table(
        'members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('last_active', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('message_count', sa.Integer(), default=0),
        sa.Column('media_count', sa.Integer(), default=0),
        sa.Column('trust_score', sa.Integer(), default=50),
        sa.Column('xp', sa.Integer(), default=0),
        sa.Column('level', sa.Integer(), default=1),
        sa.Column('streak_days', sa.Integer(), default=0),
        sa.Column('last_streak_date', sa.Date(), nullable=True),
        sa.Column('warn_count', sa.Integer(), default=0),
        sa.Column('mute_count', sa.Integer(), default=0),
        sa.Column('ban_count', sa.Integer(), default=0),
        sa.Column('is_muted', sa.Boolean(), default=False),
        sa.Column('mute_until', sa.DateTime(), nullable=True),
        sa.Column('is_banned', sa.Boolean(), default=False),
        sa.Column('ban_until', sa.DateTime(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), default=False),
        sa.Column('is_whitelisted', sa.Boolean(), default=False),
        sa.Column('role', sa.String(20), default='member'),
        sa.Column('custom_title', sa.String(64), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'group_id', name='uq_user_group')
    )
    op.create_index('ix_members_user_id', 'members', ['user_id'])
    op.create_index('ix_members_group_id', 'members', ['group_id'])

    # Module configs table
    op.create_table(
        'module_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('module_name', sa.String(50), nullable=False),
        sa.Column('config', postgresql.JSONB(), default={}),
        sa.Column('is_enabled', sa.Boolean(), default=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'module_name', name='uq_group_module')
    )
    op.create_index('ix_module_configs_group_id', 'module_configs', ['group_id'])
    op.create_index('ix_module_configs_module_name', 'module_configs', ['module_name'])

    # Notes table
    op.create_table(
        'notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('keyword', sa.String(64), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('media_file_id', sa.String(500), nullable=True),
        sa.Column('media_type', sa.String(20), nullable=True),
        sa.Column('has_buttons', sa.Boolean(), default=False),
        sa.Column('button_data', postgresql.JSONB(), nullable=True),
        sa.Column('is_private', sa.Boolean(), default=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notes_group_id', 'notes', ['group_id'])
    op.create_index('ix_notes_keyword', 'notes', ['keyword'])

    # Filters table
    op.create_table(
        'filters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('trigger', sa.String(200), nullable=False),
        sa.Column('match_type', sa.String(20), default='contains'),
        sa.Column('response_type', sa.String(20), default='text'),
        sa.Column('response_content', sa.Text(), nullable=False),
        sa.Column('response_file_id', sa.String(500), nullable=True),
        sa.Column('action', sa.String(20), nullable=True),
        sa.Column('delete_trigger', sa.Boolean(), default=False),
        sa.Column('admin_only', sa.Boolean(), default=False),
        sa.Column('case_sensitive', sa.Boolean(), default=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_filters_group_id', 'filters', ['group_id'])

    # Locks table
    op.create_table(
        'locks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('lock_type', sa.String(50), nullable=False),
        sa.Column('is_locked', sa.Boolean(), default=False),
        sa.Column('mode', sa.String(20), default='delete'),
        sa.Column('mode_duration', sa.Integer(), nullable=True),
        sa.Column('schedule_enabled', sa.Boolean(), default=False),
        sa.Column('schedule_windows', postgresql.JSONB(), nullable=True),
        sa.Column('allowlist', postgresql.JSONB(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'lock_type', name='uq_group_lock')
    )

    # Mod actions table
    op.create_table(
        'mod_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(30), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('silent', sa.Boolean(), default=False),
        sa.Column('ai_inferred', sa.Boolean(), default=False),
        sa.Column('message_id', sa.BigInteger(), nullable=True),
        sa.Column('message_content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('reversed_at', sa.DateTime(), nullable=True),
        sa.Column('reversed_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mod_actions_group_id', 'mod_actions', ['group_id'])
    op.create_index('ix_mod_actions_action_type', 'mod_actions', ['action_type'])


def downgrade() -> None:
    op.drop_table('mod_actions')
    op.drop_table('locks')
    op.drop_table('filters')
    op.drop_table('notes')
    op.drop_table('module_configs')
    op.drop_table('members')
    op.drop_table('bot_instances')
    op.drop_table('groups')
    op.drop_table('users')
