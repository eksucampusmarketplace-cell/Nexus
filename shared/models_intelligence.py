"""Group Intelligence and Advanced Features models for Nexus."""

import uuid
from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


# ============ GROUP INTELLIGENCE MODELS ============


class BehaviorPattern(Base):
    """Behavioral patterns for predictive moderation."""

    __tablename__ = "behavior_patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pattern_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(30))  # spam, raid, abuse, scam, etc.
    
    # Pattern definition
    sequence: Mapped[List[Dict[str, Any]]] = mapped_column(JSON)  # Ordered list of behaviors
    time_window_seconds: Mapped[int] = mapped_column(Integer, default=3600)
    min_occurrences: Mapped[int] = mapped_column(Integer, default=1)
    
    # Risk scoring
    base_risk_score: Mapped[int] = mapped_column(Integer, default=50)
    false_positive_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Actions
    auto_action: Mapped[Optional[str]] = mapped_column(String(30))
    action_threshold: Mapped[int] = mapped_column(Integer, default=80)
    
    # Learning
    is_platform_pattern: Mapped[bool] = mapped_column(Boolean, default=False)
    is_learned: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class MemberBehaviorLog(Base):
    """Log of member behaviors for pattern matching."""

    __tablename__ = "member_behavior_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Behavior details
    behavior_type: Mapped[str] = mapped_column(String(50), index=True)
    behavior_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Context
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    
    # Analysis
    matched_patterns: Mapped[Optional[List[str]]] = mapped_column(JSON)
    risk_contribution: Mapped[int] = mapped_column(Integer, default=0)


class PredictiveScore(Base):
    """Predictive risk scores for members."""

    __tablename__ = "predictive_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Scores
    risk_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    spam_likelihood: Mapped[float] = mapped_column(Float, default=0.0)
    raid_likelihood: Mapped[float] = mapped_column(Float, default=0.0)
    abuse_likelihood: Mapped[float] = mapped_column(Float, default=0.0)
    churn_likelihood: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Contributing factors
    matched_patterns: Mapped[List[str]] = mapped_column(JSON, default=list)
    behavioral_flags: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Monitoring level
    monitoring_level: Mapped[int] = mapped_column(Integer, default=0)  # 0=normal, 1=enhanced, 2=intensive
    shadow_watch: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Predictions
    predicted_action: Mapped[Optional[str]] = mapped_column(String(50))
    prediction_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Timing
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    first_flagged: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_predictive_user_group"),
    )


class ConversationNode(Base):
    """Nodes in the conversation/social graph."""

    __tablename__ = "conversation_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Node metrics
    influence_score: Mapped[float] = mapped_column(Float, default=0.0)
    centrality_score: Mapped[float] = mapped_column(Float, default=0.0)
    trust_score_normalized: Mapped[float] = mapped_column(Float, default=0.5)
    
    # Interaction counts
    total_interactions: Mapped[int] = mapped_column(Integer, default=0)
    messages_sent: Mapped[int] = mapped_column(Integer, default=0)
    replies_received: Mapped[int] = mapped_column(Integer, default=0)
    reactions_received: Mapped[int] = mapped_column(Integer, default=0)
    
    # Community detection
    clique_membership: Mapped[Optional[List[str]]] = mapped_column(JSON)
    bridges_to: Mapped[Optional[List[int]]] = mapped_column(JSON)  # User IDs bridged to
    is_isolated: Mapped[bool] = mapped_column(Boolean, default=False)
    
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class ConversationEdge(Base):
    """Edges in the conversation/social graph."""

    __tablename__ = "conversation_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    source_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Edge weights
    reply_count: Mapped[int] = mapped_column(Integer, default=0)
    mention_count: Mapped[int] = mapped_column(Integer, default=0)
    reaction_count: Mapped[int] = mapped_column(Integer, default=0)
    forward_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationship strength
    strength: Mapped[float] = mapped_column(Float, default=0.0)
    reciprocity: Mapped[float] = mapped_column(Float, default=0.0)  # How bidirectional
    
    # Sentiment
    avg_sentiment: Mapped[float] = mapped_column(Float, default=0.0)
    
    last_interaction: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    __table_args__ = (
        UniqueConstraint("group_id", "source_user_id", "target_user_id", name="uq_conversation_edge"),
    )


class AnomalyEvent(Base):
    """Anomaly events for timeline."""

    __tablename__ = "anomaly_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    anomaly_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Anomaly details
    anomaly_type: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    
    # Metrics
    severity: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    deviation_score: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_value: Mapped[float] = mapped_column(Float, default=0.0)
    actual_value: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Context
    involved_users: Mapped[Optional[List[int]]] = mapped_column(JSON)
    related_messages: Mapped[Optional[List[int]]] = mapped_column(JSON)
    context_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Resolution
    action_taken: Mapped[Optional[str]] = mapped_column(String(100))
    action_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    is_false_positive: Mapped[bool] = mapped_column(Boolean, default=False)


class MemberJourney(Base):
    """Member journey tracking for onboarding analysis."""

    __tablename__ = "member_journeys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Journey timeline
    joined_at: Mapped[datetime] = mapped_column(DateTime)
    first_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    first_reply_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    first_reaction_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Onboarding milestones
    read_rules: Mapped[bool] = mapped_column(Boolean, default=False)
    read_rules_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    introduced_self: Mapped[bool] = mapped_column(Boolean, default=False)
    introduced_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    welcomed_by_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    responded_to_welcome: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # First 72 hours metrics
    first_72h_messages: Mapped[int] = mapped_column(Integer, default=0)
    first_72h_reactions_given: Mapped[int] = mapped_column(Integer, default=0)
    first_72h_reactions_received: Mapped[int] = mapped_column(Integer, default=0)
    first_72h_violations: Mapped[int] = mapped_column(Integer, default=0)
    
    # Trajectory prediction
    trajectory: Mapped[str] = mapped_column(String(20), default="unknown")  # positive, negative, neutral, unknown
    trajectory_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    engagement_trend: Mapped[float] = mapped_column(Float, default=0.0)  # Slope of engagement
    
    # Outcome
    became_active: Mapped[bool] = mapped_column(Boolean, default=False)
    churned_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    banned_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    last_analyzed: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class TopicCluster(Base):
    """Topic clusters for topic intelligence."""

    __tablename__ = "topic_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Topic details
    name: Mapped[str] = mapped_column(String(100))
    keywords: Mapped[List[str]] = mapped_column(JSON)
    representative_messages: Mapped[Optional[List[int]]] = mapped_column(JSON)
    
    # Metrics
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    unique_participants: Mapped[int] = mapped_column(Integer, default=0)
    avg_sentiment: Mapped[float] = mapped_column(Float, default=0.0)
    controversy_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Trend
    is_emerging: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dying: Mapped[bool] = mapped_column(Boolean, default=False)
    is_controversial: Mapped[bool] = mapped_column(Boolean, default=False)
    is_connector: Mapped[bool] = mapped_column(Boolean, default=False)  # Bridges different member groups
    
    # Engagement
    messages_24h: Mapped[int] = mapped_column(Integer, default=0)
    messages_7d: Mapped[int] = mapped_column(Integer, default=0)
    trend_direction: Mapped[float] = mapped_column(Float, default=0.0)  # Positive = growing
    
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class ChurnPrediction(Base):
    """Churn predictions for members."""

    __tablename__ = "churn_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Risk scores
    churn_risk: Mapped[float] = mapped_column(Float, default=0.0)
    engagement_decline_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Contributing factors
    days_inactive: Mapped[int] = mapped_column(Integer, default=0)
    message_quality_trend: Mapped[float] = mapped_column(Float, default=0.0)
    reaction_giving_trend: Mapped[float] = mapped_column(Float, default=0.0)
    social_connection_loss: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Suggested intervention
    suggested_intervention: Mapped[Optional[str]] = mapped_column(String(100))
    intervention_priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Intervention tracking
    intervention_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    intervention_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    intervention_result: Mapped[Optional[str]] = mapped_column(String(50))
    
    predicted_churn_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


# ============ AUTOMATION MODELS ============


class AutomationRule(Base):
    """Conditional automation rules."""

    __tablename__ = "automation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Rule definition
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Conditions (JSON representation of condition blocks)
    conditions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON)
    condition_logic: Mapped[str] = mapped_column(String(10), default="and")  # and/or
    
    # Actions
    actions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON)
    
    # Trigger
    trigger_type: Mapped[str] = mapped_column(String(30))  # message, join, leave, reaction, scheduled, etc.
    
    # Settings
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=0)
    max_triggers_per_day: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Stats
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    last_triggered: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class BehavioralTripwire(Base):
    """Behavioral tripwires with escalation ladders."""

    __tablename__ = "behavioral_tripwires"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tripwire_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Tripwire definition
    name: Mapped[str] = mapped_column(String(100))
    trigger_behavior: Mapped[str] = mapped_column(String(100))
    
    # Escalation ladder
    escalation_levels: Mapped[List[Dict[str, Any]]] = mapped_column(JSON)
    # Each level: {threshold, action, duration, notify_admins, require_confirmation}
    
    # Tracking window
    window_seconds: Mapped[int] = mapped_column(Integer, default=86400)
    
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class MemberTripwireState(Base):
    """Current state of members against tripwires."""

    __tablename__ = "member_tripwire_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    tripwire_id: Mapped[str] = mapped_column(String(100), index=True)
    
    # Current state
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    current_level: Mapped[int] = mapped_column(Integer, default=0)
    last_triggered: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Window tracking
    window_start: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", "tripwire_id", name="uq_member_tripwire"),
    )


class TimeBasedRuleSet(Base):
    """Time-based rule sets for different operating modes."""

    __tablename__ = "time_based_rule_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ruleset_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Rule set info
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Schedule
    schedule_type: Mapped[str] = mapped_column(String(20))  # recurring, one_time, seasonal
    days_of_week: Mapped[Optional[List[int]]] = mapped_column(JSON)
    start_time: Mapped[str] = mapped_column(String(5))  # HH:MM
    end_time: Mapped[str] = mapped_column(String(5))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    
    # Seasonal
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Configuration overrides
    config_overrides: Mapped[Dict[str, Any]] = mapped_column(JSON)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class SmartCooldown(Base):
    """Smart cooldown configurations."""

    __tablename__ = "smart_cooldowns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), unique=True)
    
    # Base cooldowns
    link_cooldown_base: Mapped[int] = mapped_column(Integer, default=600)  # seconds
    media_cooldown_base: Mapped[int] = mapped_column(Integer, default=300)
    deleted_message_cooldown_base: Mapped[int] = mapped_column(Integer, default=1800)
    warn_cooldown_base: Mapped[int] = mapped_column(Integer, default=86400)
    
    # Trust score modifiers
    high_trust_threshold: Mapped[int] = mapped_column(Integer, default=70)
    high_trust_multiplier: Mapped[float] = mapped_column(Float, default=0.5)  # 50% cooldown
    low_trust_threshold: Mapped[int] = mapped_column(Integer, default=30)
    low_trust_multiplier: Mapped[float] = mapped_column(Float, default=2.0)  # 2x cooldown
    
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class AutomatedEvent(Base):
    """Automated community events."""

    __tablename__ = "automated_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Event definition
    name: Mapped[str] = mapped_column(String(100))
    event_type: Mapped[str] = mapped_column(String(30))  # trivia, spotlight, challenge, etc.
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Schedule
    schedule_type: Mapped[str] = mapped_column(String(20))  # daily, weekly, monthly, custom
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    
    # Configuration
    config: Mapped[Dict[str, Any]] = mapped_column(JSON)
    rewards: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # State
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    next_run: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


# ============ COMMUNICATION MODELS ============


class BroadcastCampaign(Base):
    """Broadcast campaigns for announcements."""

    __tablename__ = "broadcast_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Campaign info
    name: Mapped[str] = mapped_column(String(100))
    
    # Content
    content: Mapped[str] = mapped_column(Text)
    media_file_id: Mapped[Optional[str]] = mapped_column(String(500))
    media_type: Mapped[Optional[str]] = mapped_column(String(20))
    button_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Targeting
    targeting: Mapped[Dict[str, Any]] = mapped_column(JSON)
    # {active_days: 7, min_level: 10, has_badge: "xxx", custom_list: [...]}
    
    # Delivery
    delivery_type: Mapped[str] = mapped_column(String(20))  # now, scheduled, recurring
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # A/B Testing
    is_ab_test: Mapped[bool] = mapped_column(Boolean, default=False)
    variant_a_content: Mapped[Optional[str]] = mapped_column(Text)
    variant_b_content: Mapped[Optional[str]] = mapped_column(Text)
    ab_split_ratio: Mapped[float] = mapped_column(Float, default=0.5)
    
    # Stats
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    reaction_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)
    
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class DMCampaign(Base):
    """DM campaigns for personalized messaging."""

    __tablename__ = "dm_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Campaign info
    name: Mapped[str] = mapped_column(String(100))
    
    # Template with variables
    template: Mapped[str] = mapped_column(Text)
    # Supports {name}, {level}, {coins}, {last_activity}, etc.
    
    # Targeting
    segment: Mapped[str] = mapped_column(String(50))  # new_members, inactive_14d, top_10, etc.
    segment_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Delivery
    delay_between_sends: Mapped[int] = mapped_column(Integer, default=5)  # seconds
    total_targets: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    response_count: Mapped[int] = mapped_column(Integer, default=0)
    
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class AnnouncementReaction(Base):
    """Reaction tracking for announcements."""

    __tablename__ = "announcement_reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    message_id: Mapped[int] = mapped_column(BigInteger, index=True)
    campaign_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Reaction data
    reactions: Mapped[Dict[str, int]] = mapped_column(JSON)  # emoji -> count
    total_reactions: Mapped[int] = mapped_column(Integer, default=0)
    
    # Member details
    member_reactions: Mapped[Dict[str, List[int]]] = mapped_column(JSON)  # emoji -> user_ids
    
    # Timing
    first_reaction_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_reaction_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    posted_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


# ============ PERSONALIZATION MODELS ============


class MemberPreferences(Base):
    """Member preference profiles."""

    __tablename__ = "member_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Communication preferences
    digest_delivery: Mapped[str] = mapped_column(String(20), default="group")  # dm, group, none
    dm_notifications: Mapped[str] = mapped_column(String(20), default="mentions")  # all, mentions, critical, none
    
    # Privacy
    show_on_leaderboard: Mapped[bool] = mapped_column(Boolean, default=True)
    show_on_member_map: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Profile
    bio: Mapped[Optional[str]] = mapped_column(Text)
    birthday: Mapped[Optional[date]] = mapped_column(Date)
    country: Mapped[Optional[str]] = mapped_column(String(50))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    language: Mapped[str] = mapped_column(String(10), default="en")
    
    # Custom fields
    custom_fields: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_member_prefs"),
    )


class AdminPreferences(Base):
    """Admin notification preferences."""

    __tablename__ = "admin_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Notification levels
    moderation_alerts: Mapped[str] = mapped_column(String(20), default="critical")  # all, critical, digest, none
    security_alerts: Mapped[str] = mapped_column(String(20), default="all")
    member_alerts: Mapped[str] = mapped_column(String(20), default="digest")
    
    # Delivery
    delivery_channel: Mapped[str] = mapped_column(String(20), default="group")  # dm, group, log_channel
    
    # Digest
    digest_frequency: Mapped[str] = mapped_column(String(20), default="daily")
    digest_time: Mapped[str] = mapped_column(String(5), default="09:00")
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_admin_prefs"),
    )


class GroupTheme(Base):
    """Custom group themes."""

    __tablename__ = "group_themes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), unique=True)
    
    # Color scheme
    primary_color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    secondary_color: Mapped[str] = mapped_column(String(7), default="#1E40AF")
    accent_color: Mapped[str] = mapped_column(String(7), default="#10B981")
    background_color: Mapped[str] = mapped_column(String(7), default="#0F172A")
    text_color: Mapped[str] = mapped_column(String(7), default="#F8FAFC")
    
    # Card/profile styling
    card_style: Mapped[str] = mapped_column(String(20), default="rounded")
    welcome_card_template: Mapped[Optional[str]] = mapped_column(String(50))
    profile_card_template: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Logo
    logo_file_id: Mapped[Optional[str]] = mapped_column(String(500))
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class CustomRankName(Base):
    """Custom rank names for levels."""

    __tablename__ = "custom_rank_names"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    level_min: Mapped[int] = mapped_column(Integer)
    level_max: Mapped[int] = mapped_column(Integer)
    rank_name: Mapped[str] = mapped_column(String(50))
    rank_icon: Mapped[Optional[str]] = mapped_column(String(10))
    
    __table_args__ = (
        UniqueConstraint("group_id", "level_min", name="uq_group_rank_level"),
    )


class CustomEconomyConfig(Base):
    """Extended custom economy configuration."""

    __tablename__ = "custom_economy_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), unique=True)
    
    # Naming
    currency_name: Mapped[str] = mapped_column(String(30), default="coins")
    currency_name_plural: Mapped[str] = mapped_column(String(30), default="coins")
    currency_emoji: Mapped[str] = mapped_column(String(5), default="🪙")
    
    # Custom labels
    shop_name: Mapped[str] = mapped_column(String(50), default="Shop")
    treasury_name: Mapped[str] = mapped_column(String(50), default="Treasury")
    daily_bonus_name: Mapped[str] = mapped_column(String(50), default="Daily Bonus")
    leaderboard_name: Mapped[str] = mapped_column(String(50), default="Leaderboard")
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class WelcomeFlow(Base):
    """Conditional welcome sequences."""

    __tablename__ = "welcome_flows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flow_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Flow definition
    name: Mapped[str] = mapped_column(String(100))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Conditions
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSON)
    # {invite_link: "xxx", is_premium: true, trust_score_min: 50, etc.}
    
    # Welcome content
    welcome_message: Mapped[str] = mapped_column(Text)
    media_file_id: Mapped[Optional[str]] = mapped_column(String(500))
    button_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Behavior
    require_verification: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_type: Mapped[Optional[str]] = mapped_column(String(20))
    
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


# ============ SAFETY ARCHITECTURE MODELS ============


class CoordinatedAttack(Base):
    """Detected coordinated attacks."""

    __tablename__ = "coordinated_attacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attack_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Attack details
    attack_type: Mapped[str] = mapped_column(String(30))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    involved_users: Mapped[List[int]] = mapped_column(JSON)
    
    # Detection signals
    signals: Mapped[Dict[str, Any]] = mapped_column(JSON)
    # {similar_usernames: true, join_time_cluster: true, message_similarity: 0.8}
    
    # Response
    action_taken: Mapped[Optional[str]] = mapped_column(String(50))
    action_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_false_positive: Mapped[bool] = mapped_column(Boolean, default=False)


class HoneypotTrap(Base):
    """Honeypot triggers for spam detection."""

    __tablename__ = "honeypot_traps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Trap definition
    trap_type: Mapped[str] = mapped_column(String(30))  # phrase, link, pattern
    trigger: Mapped[str] = mapped_column(Text)
    
    # Action
    action: Mapped[str] = mapped_column(String(20), default="ban")
    
    # Stats
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class VerificationLevel(Base):
    """Member verification levels."""

    __tablename__ = "verification_levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Level
    verification_level: Mapped[int] = mapped_column(Integer, default=0)
    # 0=unverified, 1=basic, 2=established, 3=trusted, 4=verified
    
    # Verification method
    verified_via: Mapped[Optional[str]] = mapped_column(String(30))
    # messages, days, admin_approval, twitter, github, custom
    
    # External verifications
    external_accounts: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    # {twitter: "handle", github: "username"}
    
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    verified_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_verification_user_group"),
    )


class VerificationRequirement(Base):
    """Verification requirements for actions."""

    __tablename__ = "verification_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Action requiring verification
    action_type: Mapped[str] = mapped_column(String(50))  # post_links, post_media, tag_admins, etc.
    min_verification_level: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class ShadowWatchSession(Base):
    """Shadow watch sessions for pre-moderation."""

    __tablename__ = "shadow_watch_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Session info
    started_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    started_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Settings
    delay_seconds: Mapped[int] = mapped_column(Integer, default=5)
    notify_channel_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    
    # Stats
    messages_watched: Mapped[int] = mapped_column(Integer, default=0)
    messages_blocked: Mapped[int] = mapped_column(Integer, default=0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class ShadowWatchMessage(Base):
    """Messages captured in shadow watch."""

    __tablename__ = "shadow_watch_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("shadow_watch_sessions.id"), index=True)
    
    # Message
    message_id: Mapped[int] = mapped_column(BigInteger)
    content: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(50))
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, blocked
    action_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    action_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


# ============ INTEGRATION MODELS ============


class WebhookConfig(Base):
    """Webhook configurations."""

    __tablename__ = "webhook_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    webhook_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Webhook info
    name: Mapped[str] = mapped_column(String(100))
    webhook_type: Mapped[str] = mapped_column(String(20))  # incoming, outgoing
    
    # Configuration
    url: Mapped[str] = mapped_column(String(500))
    method: Mapped[str] = mapped_column(String(10), default="POST")
    headers: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    secret: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Events (for outgoing)
    events: Mapped[List[str]] = mapped_column(JSON)
    
    # Response mapping (for incoming)
    response_mapping: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class WebhookLog(Base):
    """Webhook execution logs."""

    __tablename__ = "webhook_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    webhook_id: Mapped[str] = mapped_column(String(100), index=True)
    
    # Request
    request_payload: Mapped[Dict[str, Any]] = mapped_column(JSON)
    
    # Response
    response_status: Mapped[int] = mapped_column(Integer)
    response_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Result
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[Optional[str]] = mapped_column(Text)
    
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class EventSubscription(Base):
    """Event stream subscriptions."""

    __tablename__ = "event_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscription_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Subscription info
    name: Mapped[str] = mapped_column(String(100))
    webhook_url: Mapped[str] = mapped_column(String(500))
    
    # Events to subscribe
    event_types: Mapped[List[str]] = mapped_column(JSON)
    
    # Filtering
    filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


# ============ UNIQUE FEATURES MODELS ============


class TimeCapsule(Base):
    """Time capsules for future messages."""

    __tablename__ = "time_capsules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    capsule_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Capsule content
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    media_file_id: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Open settings
    open_at: Mapped[datetime] = mapped_column(DateTime)
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    
    # Creator
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Type
    capsule_type: Mapped[str] = mapped_column(String(20), default="message")  # message, prediction, milestone


class GroupSoundtrack(Base):
    """Voice message soundtracks for events."""

    __tablename__ = "group_soundtracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Event trigger
    event_type: Mapped[str] = mapped_column(String(30))  # level_up, new_member, raid_alert, etc.
    
    # Audio
    audio_file_id: Mapped[str] = mapped_column(String(500))
    audio_name: Mapped[Optional[str]] = mapped_column(String(100))
    
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class LegacyMember(Base):
    """Legacy members - honored departed members."""

    __tablename__ = "legacy_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Tribute
    tribute_text: Mapped[str] = mapped_column(Text)
    contribution_highlights: Mapped[List[str]] = mapped_column(JSON)
    
    # Dates
    active_from: Mapped[datetime] = mapped_column(DateTime)
    active_until: Mapped[datetime] = mapped_column(DateTime)
    
    # Honors
    badges_earned: Mapped[List[str]] = mapped_column(JSON)
    final_rank: Mapped[Optional[str]] = mapped_column(String(50))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class GroupOath(Base):
    """Group oath acceptance records."""

    __tablename__ = "group_oaths"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), unique=True)
    
    # Oath content
    oath_text: Mapped[str] = mapped_column(Text)
    confirmation_phrase: Mapped[str] = mapped_column(String(100))
    
    # Settings
    require_on_join: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class OathAcceptance(Base):
    """Records of oath acceptances."""

    __tablename__ = "oath_acceptances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    accepted_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_oath_user_group"),
    )


class LiveCollaborationSession(Base):
    """Live collaboration sessions for admins."""

    __tablename__ = "live_collaboration_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Session
    started_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    started_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Participants
    participants: Mapped[List[int]] = mapped_column(JSON)
    
    # Shared state
    highlighted_messages: Mapped[List[int]] = mapped_column(JSON, default=list)
    comments: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class SeasonalMode(Base):
    """Seasonal operating modes."""

    __tablename__ = "seasonal_modes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mode_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    
    # Mode info
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Schedule
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    recurring_yearly: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Configuration
    config_overrides: Mapped[Dict[str, Any]] = mapped_column(JSON)
    
    # Theme
    theme_name: Mapped[Optional[str]] = mapped_column(String(50))
    special_badges: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
