"""Add user sessions table for session management.

Revision ID: 004_user_sessions
Revises: 003_message_graveyard
Create Date: 2024-01-15 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "004_user_sessions"
down_revision = "003_message_graveyard"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # User sessions table - tracks active login sessions
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_token", sa.String(255), unique=True, nullable=False),
        sa.Column("device_info", sa.String(255)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index(
        "ix_user_sessions_session_token", "user_sessions", ["session_token"]
    )
    op.create_index("ix_user_sessions_expires_at", "user_sessions", ["expires_at"])

    # Add refresh_token column to store Telegram initData for re-authentication
    op.add_column(
        "users",
        sa.Column("last_init_data", sa.Text()),
    )


def downgrade() -> None:
    op.drop_column("users", "last_init_data")
    op.drop_index("ix_user_sessions_expires_at", table_name="user_sessions")
    op.drop_index("ix_user_sessions_session_token", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")
