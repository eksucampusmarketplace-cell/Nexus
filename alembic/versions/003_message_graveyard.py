"""Message Graveyard - deleted messages archive

Revision ID: 003_message_graveyard
Revises: 002_advanced_analytics
Create Date: 2025-01-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_message_graveyard'
down_revision = '002_advanced_analytics'
branch_labels = None
depends_on = None


def upgrade():
    # Create deleted_messages table
    op.create_table(
        'deleted_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('content_type', sa.String(length=50), nullable=True, server_default='text'),
        sa.Column('media_file_id', sa.String(length=255), nullable=True),
        sa.Column('media_group_id', sa.String(length=255), nullable=True),
        sa.Column('deletion_reason', sa.String(length=50), nullable=False),
        sa.Column('deleted_by', sa.Integer(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('can_restore', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('restored_at', sa.DateTime(), nullable=True),
        sa.Column('restored_by', sa.Integer(), nullable=True),
        sa.Column('restored_message_id', sa.BigInteger(), nullable=True),
        sa.Column('trigger_word', sa.String(length=255), nullable=True),
        sa.Column('lock_type', sa.String(length=50), nullable=True),
        sa.Column('ai_confidence', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['restored_by'], ['users.id'], ondelete='SET NULL'),
    )
    
    # Create indexes
    op.create_index(op.f('ix_deleted_messages_group_id'), 'deleted_messages', ['group_id'], unique=False)
    op.create_index(op.f('ix_deleted_messages_message_id'), 'deleted_messages', ['message_id'], unique=False)
    op.create_index(op.f('ix_deleted_messages_user_id'), 'deleted_messages', ['user_id'], unique=False)
    op.create_index(op.f('ix_deleted_messages_deletion_reason'), 'deleted_messages', ['deletion_reason'], unique=False)
    op.create_index(op.f('ix_deleted_messages_deleted_at'), 'deleted_messages', ['deleted_at'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_deleted_messages_deleted_at'), table_name='deleted_messages')
    op.drop_index(op.f('ix_deleted_messages_deletion_reason'), table_name='deleted_messages')
    op.drop_index(op.f('ix_deleted_messages_user_id'), table_name='deleted_messages')
    op.drop_index(op.f('ix_deleted_messages_message_id'), table_name='deleted_messages')
    op.drop_index(op.f('ix_deleted_messages_group_id'), table_name='deleted_messages')
    
    # Drop table
    op.drop_table('deleted_messages')
