"""Advanced analytics and AI features migration.

Revision ID: 002_advanced_analytics
Revises: 001_initial
Create Date: 2024-01-15 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002_advanced_analytics"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============ ANALYTICS TABLES ============

    # Hourly message stats for heatmaps
    op.create_table(
        "hourly_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False, index=True),
        sa.Column("date", sa.Date(), nullable=False, index=True),
        sa.Column("hour", sa.Integer(), nullable=False),
        sa.Column("message_count", sa.Integer(), default=0),
        sa.Column("unique_users", sa.Integer(), default=0),
        sa.Column("media_count", sa.Integer(), default=0),
        sa.Column("reaction_count", sa.Integer(), default=0),
        sa.UniqueConstraint("group_id", "date", "hour", name="uq_hourly_stats"),
    )

    # Daily analytics rollup
    op.create_table(
        "daily_analytics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False, index=True),
        sa.Column("date", sa.Date(), nullable=False, index=True),
        sa.Column("total_messages", sa.Integer(), default=0),
        sa.Column("unique_users", sa.Integer(), default=0),
        sa.Column("new_members", sa.Integer(), default=0),
        sa.Column("left_members", sa.Integer(), default=0),
        sa.Column("mod_actions", sa.Integer(), default=0),
        sa.Column("avg_sentiment", sa.Float(), default=0.0),
        sa.Column("peak_hour", sa.Integer(), nullable=True),
        sa.UniqueConstraint("group_id", "date", name="uq_daily_analytics"),
    )

    # Member retention tracking
    op.create_table(
        "member_retention",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.Column("last_active_at", sa.DateTime(), nullable=False),
        sa.Column("days_active", sa.Integer(), default=0),
        sa.Column("retention_score", sa.Float(), default=0.0),  # 0-100
        sa.Column("churn_risk", sa.String(20), default="low"),  # low, medium, high
    )

    # ============ TRUST SCORE SYSTEM ============

    # Trust score history
    op.create_table(
        "trust_score_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("old_score", sa.Integer(), nullable=False),
        sa.Column("new_score", sa.Integer(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(100), nullable=False),
        sa.Column("influencing_factors", postgresql.JSON(), default=dict),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Trust score configuration per group
    op.create_table(
        "trust_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), unique=True, nullable=False),
        sa.Column("enabled", sa.Boolean(), default=True),
        sa.Column("message_weight", sa.Float(), default=1.0),
        sa.Column("reaction_weight", sa.Float(), default=0.5),
        sa.Column("report_penalty", sa.Integer(), default=-10),
        sa.Column("warn_penalty", sa.Integer(), default=-15),
        sa.Column("mute_penalty", sa.Integer(), default=-25),
        sa.Column("ban_penalty", sa.Integer(), default=-50),
        sa.Column("daily_active_bonus", sa.Integer(), default=2),
        sa.Column("streak_bonus", sa.Integer(), default=5),
        sa.Column("high_trust_threshold", sa.Integer(), default=80),
        sa.Column("low_trust_threshold", sa.Integer(), default=30),
        sa.Column("ai_influence_enabled", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ============ AI MODERATION QUEUE ============

    # Flagged content for admin review
    op.create_table(
        "ai_moderation_queue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("message_id", sa.BigInteger(), nullable=False),
        sa.Column("message_content", sa.Text()),
        sa.Column("media_type", sa.String(20)),
        sa.Column("media_file_id", sa.String(500)),
        sa.Column("flagged_categories", postgresql.JSON(), default=list),
        sa.Column("confidence_score", sa.Float(), nullable=False),  # 0-100
        sa.Column("severity", sa.String(20), default="medium"),  # low, medium, high, critical
        sa.Column("ai_reasoning", sa.Text()),
        sa.Column("suggested_action", sa.String(20)),  # delete, mute, ban, warn, review
        sa.Column("status", sa.String(20), default="pending"),  # pending, approved, dismissed, auto_action
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("reviewed_at", sa.DateTime()),
        sa.Column("action_taken", sa.String(20)),
        sa.Column("false_positive", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # AI moderation configuration
    op.create_table(
        "ai_moderation_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), unique=True, nullable=False),
        sa.Column("enabled", sa.Boolean(), default=False),
        sa.Column("auto_action_threshold", sa.Integer(), default=90),  # Confidence for auto-action
        sa.Column("queue_threshold", sa.Integer(), default=70),  # Confidence to queue
        sa.Column("scan_media", sa.Boolean(), default=True),
        sa.Column("scan_links", sa.Boolean(), default=True),
        sa.Column("scan_forwarded", sa.Boolean(), default=True),
        sa.Column("categories", postgresql.JSON(), default=list),  # spam, toxicity, etc.
        sa.Column("trusted_bypass", sa.Boolean(), default=True),  # High trust users bypass
        sa.Column("min_trust_bypass", sa.Integer(), default=80),
        sa.Column("notify_admins", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ============ MOOD TRACKING ============

    # Group mood/sentiment tracking
    op.create_table(
        "mood_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False, index=True),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("avg_sentiment", sa.Float(), default=0.0),  # -1 to 1
        sa.Column("positive_ratio", sa.Float(), default=0.0),
        sa.Column("negative_ratio", sa.Float(), default=0.0),
        sa.Column("neutral_ratio", sa.Float(), default=0.0),
        sa.Column("mood_label", sa.String(20), default="neutral"),  # positive, negative, neutral, mixed
        sa.Column("message_count", sa.Integer(), default=0),
        sa.Column("dominant_topics", postgresql.JSON(), default=list),
        sa.Column("alert_triggered", sa.Boolean(), default=False),
        sa.Column("alert_reason", sa.Text()),
    )

    # Mood configuration
    op.create_table(
        "mood_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), unique=True, nullable=False),
        sa.Column("enabled", sa.Boolean(), default=True),
        sa.Column("tracking_period_hours", sa.Integer(), default=24),
        sa.Column("alert_negative_streak_days", sa.Integer(), default=3),
        sa.Column("alert_threshold", sa.Float(), default=-0.3),
        sa.Column("notify_admins", sa.Boolean(), default=True),
        sa.Column("weekly_report", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ============ BEHAVIORAL BADGES ============

    # Badge inference rules (AI-detected behaviors)
    op.create_table(
        "badge_inference_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("badge_slug", sa.String(50), sa.ForeignKey("badge_definitions.slug"), nullable=False),
        sa.Column("rule_type", sa.String(50), nullable=False),  # message_pattern, activity_streak, contribution_type
        sa.Column("rule_config", postgresql.JSON(), nullable=False),
        sa.Column("ai_detection_enabled", sa.Boolean(), default=False),
        sa.Column("detection_prompt", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Behavioral patterns detected
    op.create_table(
        "member_behavior_patterns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("pattern_type", sa.String(50), nullable=False),
        sa.Column("pattern_data", postgresql.JSON(), default=dict),
        sa.Column("confidence", sa.Float(), default=0.0),
        sa.Column("detected_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_observed_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # ============ GROUP MEMORY & MILESTONES ============

    # Enhanced milestones with AI-generated narratives
    op.create_table(
        "milestone_narratives",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("milestone_id", sa.Integer(), sa.ForeignKey("group_milestones.id"), nullable=False, index=True),
        sa.Column("narrative_type", sa.String(20), default="summary"),  # summary, story, quote
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("ai_generated", sa.Boolean(), default=False),
        sa.Column("contributor_count", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Group stories (ongoing narratives)
    op.create_table(
        "group_stories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("story_type", sa.String(50), default="general"),  # debate, event, era, legend
        sa.Column("summary", sa.Text()),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime()),
        sa.Column("key_participants", postgresql.JSON(), default=list),
        sa.Column("message_count", sa.Integer(), default=0),
        sa.Column("ai_summary", sa.Text()),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ============ NATURAL LANGUAGE INTERFACE ============

    # NL command patterns
    op.create_table(
        "nl_command_patterns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False, index=True),
        sa.Column("intent", sa.String(50), nullable=False),  # warn, mute, ban, info, etc.
        sa.Column("pattern_text", sa.Text(), nullable=False),
        sa.Column("mapped_command", sa.String(50), nullable=False),
        sa.Column("extracted_params", postgresql.JSON(), default=dict),
        sa.Column("success_count", sa.Integer(), default=0),
        sa.Column("failure_count", sa.Integer(), default=0),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # NL interaction log
    op.create_table(
        "nl_interactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("detected_intent", sa.String(50)),
        sa.Column("confidence", sa.Float()),
        sa.Column("executed_command", sa.String(50)),
        sa.Column("success", sa.Boolean()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # NL configuration
    op.create_table(
        "nl_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), unique=True, nullable=False),
        sa.Column("enabled", sa.Boolean(), default=True),
        sa.Column("min_confidence", sa.Float(), default=0.7),
        sa.Column("require_confirmation", sa.Boolean(), default=True),
        sa.Column("learn_patterns", sa.Boolean(), default=True),
        sa.Column("allowed_intents", postgresql.JSON(), default=list),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ============ MEMBER SPOTLIGHT ============

    # Spotlight features
    op.create_table(
        "member_spotlights",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("spotlight_type", sa.String(50), default="weekly"),  # weekly, monthly, special
        sa.Column("selection_reason", sa.Text()),
        sa.Column("ai_writeup", sa.Text()),
        sa.Column("featured_stats", postgresql.JSON(), default=dict),
        sa.Column("community_quotes", postgresql.JSON(), default=list),
        sa.Column("published_at", sa.DateTime()),
        sa.Column("message_id", sa.BigInteger()),
        sa.Column("reactions_positive", sa.Integer(), default=0),
        sa.Column("reactions_total", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Spotlight configuration
    op.create_table(
        "spotlight_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), unique=True, nullable=False),
        sa.Column("enabled", sa.Boolean(), default=False),
        sa.Column("frequency", sa.String(20), default="weekly"),  # weekly, monthly
        sa.Column("day_of_week", sa.Integer(), default=5),  # Friday
        sa.Column("time_of_day", sa.String(5), default="12:00"),
        sa.Column("selection_criteria", postgresql.JSON(), default=dict),
        sa.Column("ai_personality", sa.String(20), default="friendly"),  # friendly, professional, playful
        sa.Column("include_stats", sa.Boolean(), default=True),
        sa.Column("include_quotes", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ============ SHARED GROUP CHALLENGES ============

    # Group challenges
    op.create_table(
        "group_challenges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("challenge_type", sa.String(50), nullable=False),  # messages, members, activity, engagement
        sa.Column("target_value", sa.Integer(), nullable=False),
        sa.Column("current_value", sa.Integer(), default=0),
        sa.Column("target_metric", sa.String(50), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column("reward_type", sa.String(50)),  # badge, xp, coins, title
        sa.Column("reward_config", postgresql.JSON(), default=dict),
        sa.Column("status", sa.String(20), default="active"),  # active, completed, cancelled
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime()),
    )

    # Challenge participants progress
    op.create_table(
        "challenge_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("challenge_id", sa.Integer(), sa.ForeignKey("group_challenges.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("contribution", sa.Integer(), default=0),
        sa.Column("percent_complete", sa.Float(), default=0.0),
        sa.Column("rank", sa.Integer()),
        sa.Column("reward_claimed", sa.Boolean(), default=False),
        sa.Column("claimed_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ============ CROSS-MODULE INTELLIGENCE ============

    # Unified member intelligence snapshot
    op.create_table(
        "member_intelligence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("calculated_at", sa.DateTime(), server_default=sa.func.now()),
        # Cross-module scores
        sa.Column("trust_tier", sa.String(20), default="neutral"),  # trusted, neutral, suspicious
        sa.Column("engagement_tier", sa.String(20), default="average"),  # high, average, low
        sa.Column("reputation_tier", sa.String(20), default="neutral"),  # positive, neutral, negative
        sa.Column("activity_tier", sa.String(20), default="regular"),  # very_active, regular, inactive
        # Composite influence scores
        sa.Column("moderation_influence", sa.Float(), default=0.0),  # -1 to 1, affects mod decisions
        sa.Column("visibility_boost", sa.Float(), default=0.0),  # For spotlight, challenges
        sa.Column("privilege_level", sa.Integer(), default=0),  # Calculated privilege tier
        # Contributing factors
        sa.Column("factor_trust", sa.Float(), default=0.0),
        sa.Column("factor_xp", sa.Float(), default=0.0),
        sa.Column("factor_warnings", sa.Float(), default=0.0),
        sa.Column("factor_streak", sa.Float(), default=0.0),
        sa.Column("factor_badges", sa.Float(), default=0.0),
        sa.Column("factor_reputation", sa.Float(), default=0.0),
        sa.Column("factor_economy", sa.Float(), default=0.0),
        # Recommendations
        sa.Column("recommended_actions", postgresql.JSON(), default=list),
        sa.UniqueConstraint("group_id", "user_id", name="uq_member_intelligence"),
    )

    # Intelligence configuration
    op.create_table(
        "intelligence_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), unique=True, nullable=False),
        sa.Column("enabled", sa.Boolean(), default=True),
        sa.Column("calculation_frequency", sa.String(20), default="daily"),  # hourly, daily, weekly
        sa.Column("trust_weight", sa.Float(), default=0.25),
        sa.Column("xp_weight", sa.Float(), default=0.15),
        sa.Column("reputation_weight", sa.Float(), default=0.20),
        sa.Column("activity_weight", sa.Float(), default=0.20),
        sa.Column("economy_weight", sa.Float(), default=0.10),
        sa.Column("badge_weight", sa.Float(), default=0.10),
        sa.Column("influence_moderation", sa.Boolean(), default=True),
        sa.Column("influence_spotlight", sa.Boolean(), default=True),
        sa.Column("influence_challenges", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ============ MESSAGE TABLE (for analytics) ============
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("message_id", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.Text()),
        sa.Column("content_type", sa.String(20), default="text"),
        sa.Column("sentiment_score", sa.Float()),  # -1 to 1
        sa.Column("is_forwarded", sa.Boolean(), default=False),
        sa.Column("has_media", sa.Boolean(), default=False),
        sa.Column("media_types", postgresql.JSON(), default=list),
        sa.Column("reply_to_message_id", sa.BigInteger()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_messages_created_at", "messages", ["created_at"])


def downgrade() -> None:
    # Drop in reverse order
    op.drop_table("messages")
    op.drop_table("intelligence_config")
    op.drop_table("member_intelligence")
    op.drop_table("challenge_progress")
    op.drop_table("group_challenges")
    op.drop_table("spotlight_config")
    op.drop_table("member_spotlights")
    op.drop_table("nl_config")
    op.drop_table("nl_interactions")
    op.drop_table("nl_command_patterns")
    op.drop_table("group_stories")
    op.drop_table("milestone_narratives")
    op.drop_table("member_behavior_patterns")
    op.drop_table("badge_inference_rules")
    op.drop_table("mood_config")
    op.drop_table("mood_snapshots")
    op.drop_table("ai_moderation_config")
    op.drop_table("ai_moderation_queue")
    op.drop_table("trust_config")
    op.drop_table("trust_score_history")
    op.drop_table("member_retention")
    op.drop_table("daily_analytics")
    op.drop_table("hourly_stats")
