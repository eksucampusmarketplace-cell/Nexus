"""Initial migration with all Nexus tables.

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), unique=True, nullable=False),
        sa.Column("username", sa.String(32)),
        sa.Column("first_name", sa.String(64), nullable=False),
        sa.Column("last_name", sa.String(64)),
        sa.Column("language_code", sa.String(10)),
        sa.Column("is_bot", sa.Boolean(), default=False),
        sa.Column("is_premium", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "last_seen",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])
    op.create_index("ix_users_username", "users", ["username"])

    # Groups table
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), unique=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("username", sa.String(32)),
        sa.Column("member_count", sa.Integer(), default=0),
        sa.Column("language", sa.String(10), default="en"),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("is_premium", sa.Boolean(), default=False),
        sa.Column("timezone", sa.String(50), default="UTC"),
    )
    op.create_index("ix_groups_telegram_id", "groups", ["telegram_id"])
    op.create_index("ix_groups_username", "groups", ["username"])

    # Bot instances table
    op.create_table(
        "bot_instances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("token_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("bot_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("bot_username", sa.String(32), nullable=False),
        sa.Column("bot_name", sa.String(64), nullable=False),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), unique=True),
        sa.Column("registered_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("registered_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("webhook_url", sa.String(500)),
    )
    op.create_index("ix_bot_instances_token_hash", "bot_instances", ["token_hash"])

    # Members table
    op.create_table(
        "members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_active", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("message_count", sa.Integer(), default=0),
        sa.Column("media_count", sa.Integer(), default=0),
        sa.Column("trust_score", sa.Integer(), default=50),
        sa.Column("xp", sa.Integer(), default=0),
        sa.Column("level", sa.Integer(), default=1),
        sa.Column("streak_days", sa.Integer(), default=0),
        sa.Column("last_streak_date", sa.Date()),
        sa.Column("warn_count", sa.Integer(), default=0),
        sa.Column("mute_count", sa.Integer(), default=0),
        sa.Column("ban_count", sa.Integer(), default=0),
        sa.Column("is_muted", sa.Boolean(), default=False),
        sa.Column("mute_until", sa.DateTime()),
        sa.Column("is_banned", sa.Boolean(), default=False),
        sa.Column("ban_until", sa.DateTime()),
        sa.Column("is_approved", sa.Boolean(), default=False),
        sa.Column("is_whitelisted", sa.Boolean(), default=False),
        sa.Column("role", sa.String(20), default="member"),
        sa.Column("custom_title", sa.String(64)),
        sa.UniqueConstraint("user_id", "group_id", name="uq_user_group"),
    )
    op.create_index("ix_members_user_id", "members", ["user_id"])
    op.create_index("ix_members_group_id", "members", ["group_id"])

    # Badge definitions table
    op.create_table(
        "badge_definitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("icon", sa.String(50), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("auto_award_condition", postgresql.JSON()),
    )
    op.create_index("ix_badge_definitions_slug", "badge_definitions", ["slug"])

    # Member badges table
    op.create_table(
        "member_badges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "member_id", sa.Integer(), sa.ForeignKey("members.id"), nullable=False
        ),
        sa.Column(
            "badge_slug",
            sa.String(50),
            sa.ForeignKey("badge_definitions.slug"),
            nullable=False,
        ),
        sa.Column("earned_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("metadata", postgresql.JSON()),
    )
    op.create_index("ix_member_badges_member_id", "member_badges", ["member_id"])

    # Member profiles table
    op.create_table(
        "member_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id")),
        sa.Column("bio", sa.Text()),
        sa.Column("birthday", sa.Date()),
        sa.Column("social_links", postgresql.JSON()),
        sa.Column("profile_theme", sa.String(50), default="default"),
        sa.Column("is_public", sa.Boolean(), default=True),
        sa.UniqueConstraint("user_id", "group_id", name="uq_profile_user_group"),
    )

    # Mod actions table
    op.create_table(
        "mod_actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column(
            "target_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action_type", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("silent", sa.Boolean(), default=False),
        sa.Column("ai_inferred", sa.Boolean(), default=False),
        sa.Column("message_id", sa.BigInteger()),
        sa.Column("message_content", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime()),
        sa.Column("reversed_at", sa.DateTime()),
        sa.Column("reversed_by", sa.Integer(), sa.ForeignKey("users.id")),
    )
    op.create_index("ix_mod_actions_group_id", "mod_actions", ["group_id"])
    op.create_index("ix_mod_actions_target_user_id", "mod_actions", ["target_user_id"])
    op.create_index("ix_mod_actions_action_type", "mod_actions", ["action_type"])

    # Warnings table
    op.create_table(
        "warnings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("issued_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime()),
    )
    op.create_index("ix_warnings_group_id", "warnings", ["group_id"])
    op.create_index("ix_warnings_user_id", "warnings", ["user_id"])

    # Federations table
    op.create_table(
        "federations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("is_public", sa.Boolean(), default=False),
    )

    # Federation admins table
    op.create_table(
        "federation_admins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "federation_id",
            postgresql.UUID(),
            sa.ForeignKey("federations.id"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("added_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("added_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_federation_admins_federation_id", "federation_admins", ["federation_id"]
    )

    # Federation members table
    op.create_table(
        "federation_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "federation_id",
            postgresql.UUID(),
            sa.ForeignKey("federations.id"),
            nullable=False,
        ),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("joined_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_index(
        "ix_federation_members_federation_id", "federation_members", ["federation_id"]
    )

    # Federation bans table
    op.create_table(
        "federation_bans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "federation_id",
            postgresql.UUID(),
            sa.ForeignKey("federations.id"),
            nullable=False,
        ),
        sa.Column(
            "target_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("banned_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime()),
    )
    op.create_index(
        "ix_federation_bans_federation_id", "federation_bans", ["federation_id"]
    )

    # Notes table
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("keyword", sa.String(64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("media_file_id", sa.String(500)),
        sa.Column("media_type", sa.String(20)),
        sa.Column("has_buttons", sa.Boolean(), default=False),
        sa.Column("button_data", postgresql.JSON()),
        sa.Column("is_private", sa.Boolean(), default=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_notes_group_id", "notes", ["group_id"])
    op.create_index("ix_notes_keyword", "notes", ["keyword"])

    # Filters table
    op.create_table(
        "filters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("trigger", sa.String(200), nullable=False),
        sa.Column("match_type", sa.String(20), default="contains"),
        sa.Column("response_type", sa.String(20), default="text"),
        sa.Column("response_content", sa.Text(), nullable=False),
        sa.Column("response_file_id", sa.String(500)),
        sa.Column("action", sa.String(20)),
        sa.Column("delete_trigger", sa.Boolean(), default=False),
        sa.Column("admin_only", sa.Boolean(), default=False),
        sa.Column("case_sensitive", sa.Boolean(), default=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_filters_group_id", "filters", ["group_id"])

    # Locks table
    op.create_table(
        "locks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("lock_type", sa.String(50), nullable=False),
        sa.Column("is_locked", sa.Boolean(), default=False),
        sa.Column("mode", sa.String(20), default="delete"),
        sa.Column("mode_duration", sa.Integer()),
        sa.Column("schedule_enabled", sa.Boolean(), default=False),
        sa.Column("schedule_windows", postgresql.JSON()),
        sa.Column("allowlist", postgresql.JSON()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_locks_group_id", "locks", ["group_id"])
    op.create_index("ix_locks_lock_type", "locks", ["lock_type"])

    # Rules table
    op.create_table(
        "rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "group_id",
            sa.Integer(),
            sa.ForeignKey("groups.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Greetings table
    op.create_table(
        "greetings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("greeting_type", sa.String(10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("media_file_id", sa.String(500)),
        sa.Column("media_type", sa.String(20)),
        sa.Column("has_buttons", sa.Boolean(), default=False),
        sa.Column("button_data", postgresql.JSON()),
        sa.Column("delete_previous", sa.Boolean(), default=False),
        sa.Column("delete_after_seconds", sa.Integer()),
        sa.Column("send_as_dm", sa.Boolean(), default=False),
        sa.Column("is_enabled", sa.Boolean(), default=True),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_greetings_group_id", "greetings", ["group_id"])
    op.create_index("ix_greetings_greeting_type", "greetings", ["greeting_type"])

    # Captcha settings table
    op.create_table(
        "captcha_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "group_id",
            sa.Integer(),
            sa.ForeignKey("groups.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column("captcha_type", sa.String(20), default="button"),
        sa.Column("timeout_seconds", sa.Integer(), default=90),
        sa.Column("action_on_fail", sa.String(20), default="kick"),
        sa.Column("mute_on_join", sa.Boolean(), default=True),
        sa.Column("custom_text", sa.Text()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Scheduled messages table
    op.create_table(
        "scheduled_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("media_file_id", sa.String(500)),
        sa.Column("media_type", sa.String(20)),
        sa.Column("has_buttons", sa.Boolean(), default=False),
        sa.Column("button_data", postgresql.JSON()),
        sa.Column("schedule_type", sa.String(20), default="once"),
        sa.Column("run_at", sa.DateTime()),
        sa.Column("cron_expression", sa.String(100)),
        sa.Column("days_of_week", postgresql.JSON()),
        sa.Column("time_slot", sa.String(5)),
        sa.Column("end_date", sa.Date()),
        sa.Column("max_runs", sa.Integer()),
        sa.Column("run_count", sa.Integer(), default=0),
        sa.Column("self_destruct_after", sa.Integer()),
        sa.Column("is_enabled", sa.Boolean(), default=True),
        sa.Column("last_run", sa.DateTime()),
        sa.Column("next_run", sa.DateTime()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_scheduled_messages_group_id", "scheduled_messages", ["group_id"]
    )

    # Module configs table
    op.create_table(
        "module_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("module_name", sa.String(50), nullable=False),
        sa.Column("config", postgresql.JSON(), default={}),
        sa.Column("is_enabled", sa.Boolean(), default=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.UniqueConstraint("group_id", "module_name", name="uq_group_module"),
    )
    op.create_index("ix_module_configs_group_id", "module_configs", ["group_id"])
    op.create_index("ix_module_configs_module_name", "module_configs", ["module_name"])

    # Wallets table
    op.create_table(
        "wallets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id")),
        sa.Column("balance", sa.BigInteger(), default=0),
        sa.Column("total_earned", sa.BigInteger(), default=0),
        sa.Column("total_spent", sa.BigInteger(), default=0),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Transactions table
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("from_wallet_id", sa.Integer(), sa.ForeignKey("wallets.id")),
        sa.Column("to_wallet_id", sa.Integer(), sa.ForeignKey("wallets.id")),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("transaction_type", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Economy config table
    op.create_table(
        "economy_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), unique=True),
        sa.Column("currency_name", sa.String(30), default="coins"),
        sa.Column("currency_emoji", sa.String(5), default="🪙"),
        sa.Column("earn_per_message", sa.Integer(), default=1),
        sa.Column("earn_per_reaction", sa.Integer(), default=2),
        sa.Column("daily_bonus", sa.Integer(), default=100),
        sa.Column("xp_to_coin_enabled", sa.Boolean(), default=False),
    )

    # Reputation table
    op.create_table(
        "reputation",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id")),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("score", sa.Integer(), default=0),
        sa.Column("last_given_at", sa.DateTime()),
        sa.UniqueConstraint("group_id", "user_id", name="uq_rep_group_user"),
    )

    # Game sessions table
    op.create_table(
        "game_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("game_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("data", postgresql.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime()),
    )
    op.create_index("ix_game_sessions_group_id", "game_sessions", ["group_id"])

    # API keys table
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("key_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("label", sa.String(100)),
        sa.Column("scopes", postgresql.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_used", sa.DateTime()),
        sa.Column("expires_at", sa.DateTime()),
        sa.Column("is_active", sa.Boolean(), default=True),
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"])
    op.create_index("ix_api_keys_group_id", "api_keys", ["group_id"])


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table("api_keys")
    op.drop_table("game_sessions")
    op.drop_table("reputation")
    op.drop_table("economy_config")
    op.drop_table("transactions")
    op.drop_table("wallets")
    op.drop_table("module_configs")
    op.drop_table("scheduled_messages")
    op.drop_table("captcha_settings")
    op.drop_table("greetings")
    op.drop_table("rules")
    op.drop_table("locks")
    op.drop_table("filters")
    op.drop_table("notes")
    op.drop_table("federation_bans")
    op.drop_table("federation_members")
    op.drop_table("federation_admins")
    op.drop_table("federations")
    op.drop_table("warnings")
    op.drop_table("mod_actions")
    op.drop_table("member_profiles")
    op.drop_table("member_badges")
    op.drop_table("badge_definitions")
    op.drop_table("members")
    op.drop_table("bot_instances")
    op.drop_table("groups")
    op.drop_table("users")
