"""Pydantic schemas for Group Intelligence and Advanced Features."""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ============ GROUP INTELLIGENCE SCHEMAS ============


class BehaviorPatternBase(BaseModel):
    pattern_id: str
    name: str
    description: str
    category: str
    sequence: List[Dict[str, Any]]
    time_window_seconds: int = 3600
    min_occurrences: int = 1
    base_risk_score: int = 50
    auto_action: Optional[str] = None
    action_threshold: int = 80


class BehaviorPatternCreate(BehaviorPatternBase):
    pass


class BehaviorPatternResponse(BehaviorPatternBase):
    id: int
    false_positive_rate: float
    is_platform_pattern: bool
    is_learned: bool
    confidence: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PredictiveScoreBase(BaseModel):
    risk_score: int = 0
    spam_likelihood: float = 0.0
    raid_likelihood: float = 0.0
    abuse_likelihood: float = 0.0
    churn_likelihood: float = 0.0


class PredictiveScoreResponse(PredictiveScoreBase):
    id: int
    user_id: int
    group_id: int
    matched_patterns: List[str]
    behavioral_flags: List[str]
    monitoring_level: int
    shadow_watch: bool
    predicted_action: Optional[str]
    prediction_confidence: float
    last_updated: datetime
    first_flagged: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ConversationNodeResponse(BaseModel):
    id: int
    user_id: int
    group_id: int
    influence_score: float
    centrality_score: float
    trust_score_normalized: float
    total_interactions: int
    messages_sent: int
    replies_received: int
    reactions_received: int
    clique_membership: Optional[List[str]]
    bridges_to: Optional[List[int]]
    is_isolated: bool
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationEdgeResponse(BaseModel):
    id: int
    source_user_id: int
    target_user_id: int
    reply_count: int
    mention_count: int
    reaction_count: int
    forward_count: int
    strength: float
    reciprocity: float
    avg_sentiment: float
    last_interaction: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationGraphResponse(BaseModel):
    nodes: List[ConversationNodeResponse]
    edges: List[ConversationEdgeResponse]
    cliques: List[List[int]]
    isolated_members: List[int]
    top_influencers: List[int]
    bridges: List[Dict[str, Any]]


class AnomalyEventBase(BaseModel):
    anomaly_type: str
    title: str
    description: str
    severity: int = 1
    deviation_score: float = 0.0
    baseline_value: float = 0.0
    actual_value: float = 0.0


class AnomalyEventCreate(AnomalyEventBase):
    involved_users: Optional[List[int]] = None
    related_messages: Optional[List[int]] = None
    context_data: Optional[Dict[str, Any]] = None


class AnomalyEventResponse(AnomalyEventBase):
    id: int
    anomaly_id: str
    group_id: int
    involved_users: Optional[List[int]]
    related_messages: Optional[List[int]]
    context_data: Optional[Dict[str, Any]]
    action_taken: Optional[str]
    action_by: Optional[int]
    resolved_at: Optional[datetime]
    detected_at: datetime
    is_false_positive: bool

    model_config = ConfigDict(from_attributes=True)


class AnomalyTimelineResponse(BaseModel):
    anomalies: List[AnomalyEventResponse]
    total: int
    by_type: Dict[str, int]
    by_severity: Dict[int, int]


class MemberJourneyBase(BaseModel):
    trajectory: str = "unknown"
    engagement_trend: float = 0.0


class MemberJourneyResponse(MemberJourneyBase):
    id: int
    user_id: int
    group_id: int
    joined_at: datetime
    first_message_at: Optional[datetime]
    first_reply_at: Optional[datetime]
    first_reaction_at: Optional[datetime]
    read_rules: bool
    introduced_self: bool
    welcomed_by_bot: bool
    responded_to_welcome: bool
    first_72h_messages: int
    first_72h_reactions_given: int
    first_72h_reactions_received: int
    first_72h_violations: int
    trajectory_confidence: float
    became_active: bool
    churned_at: Optional[datetime]
    banned_at: Optional[datetime]
    last_analyzed: datetime

    model_config = ConfigDict(from_attributes=True)


class TopicClusterBase(BaseModel):
    name: str
    keywords: List[str]
    representative_messages: Optional[List[int]] = None


class TopicClusterResponse(TopicClusterBase):
    id: int
    cluster_id: str
    group_id: int
    total_messages: int
    unique_participants: int
    avg_sentiment: float
    controversy_score: float
    is_emerging: bool
    is_dying: bool
    is_controversial: bool
    is_connector: bool
    messages_24h: int
    messages_7d: int
    trend_direction: float
    first_seen: datetime
    last_seen: datetime

    model_config = ConfigDict(from_attributes=True)


class TopicLandscapeResponse(BaseModel):
    topics: List[TopicClusterResponse]
    emerging: List[str]
    dying: List[str]
    controversial: List[str]
    connectors: List[str]


class ChurnPredictionBase(BaseModel):
    churn_risk: float = 0.0
    engagement_decline_rate: float = 0.0


class ChurnPredictionResponse(ChurnPredictionBase):
    id: int
    user_id: int
    group_id: int
    days_inactive: int
    message_quality_trend: float
    reaction_giving_trend: float
    social_connection_loss: float
    suggested_intervention: Optional[str]
    intervention_priority: int
    intervention_sent: bool
    intervention_at: Optional[datetime]
    intervention_result: Optional[str]
    predicted_churn_date: Optional[datetime]
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)


class ChurnRiskPanelResponse(BaseModel):
    at_risk_members: List[Dict[str, Any]]
    total_at_risk: int
    by_risk_level: Dict[str, int]


# ============ AUTOMATION SCHEMAS ============


class AutomationCondition(BaseModel):
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, contains, matches, in
    value: Any
    group: Optional[str] = None  # For grouping conditions


class AutomationAction(BaseModel):
    type: str  # mute, delete, dm, notify_admins, award_xp, deduct_coins, etc.
    params: Dict[str, Any]
    order: int = 0


class AutomationRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    conditions: List[Dict[str, Any]]
    condition_logic: str = "and"  # and/or
    actions: List[Dict[str, Any]]
    trigger_type: str
    is_enabled: bool = True
    priority: int = 0
    cooldown_seconds: int = 0
    max_triggers_per_day: Optional[int] = None


class AutomationRuleCreate(AutomationRuleBase):
    pass


class AutomationRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    condition_logic: Optional[str] = None
    actions: Optional[List[Dict[str, Any]]] = None
    trigger_type: Optional[str] = None
    is_enabled: Optional[bool] = None
    priority: Optional[int] = None
    cooldown_seconds: Optional[int] = None
    max_triggers_per_day: Optional[int] = None


class AutomationRuleResponse(AutomationRuleBase):
    id: int
    rule_id: str
    group_id: int
    trigger_count: int
    last_triggered: Optional[datetime]
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EscalationLevel(BaseModel):
    threshold: int
    action: str
    duration: Optional[int] = None
    notify_admins: bool = False
    require_confirmation: bool = False


class BehavioralTripwireBase(BaseModel):
    name: str
    trigger_behavior: str
    escalation_levels: List[Dict[str, Any]]
    window_seconds: int = 86400
    is_enabled: bool = True


class BehavioralTripwireCreate(BehavioralTripwireBase):
    pass


class BehavioralTripwireResponse(BehavioralTripwireBase):
    id: int
    tripwire_id: str
    group_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TimeBasedRuleSetBase(BaseModel):
    name: str
    description: Optional[str] = None
    schedule_type: str
    days_of_week: Optional[List[int]] = None
    start_time: str
    end_time: str
    timezone: str = "UTC"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    config_overrides: Dict[str, Any]
    is_active: bool = True


class TimeBasedRuleSetCreate(TimeBasedRuleSetBase):
    pass


class TimeBasedRuleSetResponse(TimeBasedRuleSetBase):
    id: int
    ruleset_id: str
    group_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SmartCooldownBase(BaseModel):
    link_cooldown_base: int = 600
    media_cooldown_base: int = 300
    deleted_message_cooldown_base: int = 1800
    warn_cooldown_base: int = 86400
    high_trust_threshold: int = 70
    high_trust_multiplier: float = 0.5
    low_trust_threshold: int = 30
    low_trust_multiplier: float = 2.0
    is_enabled: bool = True


class SmartCooldownResponse(SmartCooldownBase):
    id: int
    group_id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AutomatedEventBase(BaseModel):
    name: str
    event_type: str
    description: Optional[str] = None
    schedule_type: str
    cron_expression: Optional[str] = None
    duration_minutes: int = 30
    config: Dict[str, Any]
    rewards: Optional[Dict[str, Any]] = None
    is_active: bool = True


class AutomatedEventCreate(AutomatedEventBase):
    pass


class AutomatedEventResponse(AutomatedEventBase):
    id: int
    event_id: str
    group_id: int
    next_run: Optional[datetime]
    last_run: Optional[datetime]
    run_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ COMMUNICATION SCHEMAS ============


class BroadcastCampaignBase(BaseModel):
    name: str
    content: str
    media_file_id: Optional[str] = None
    media_type: Optional[str] = None
    button_data: Optional[Dict[str, Any]] = None
    targeting: Dict[str, Any]
    delivery_type: str
    scheduled_for: Optional[datetime] = None
    is_ab_test: bool = False
    variant_a_content: Optional[str] = None
    variant_b_content: Optional[str] = None
    ab_split_ratio: float = 0.5


class BroadcastCampaignCreate(BroadcastCampaignBase):
    pass


class BroadcastCampaignResponse(BroadcastCampaignBase):
    id: int
    campaign_id: str
    group_id: int
    sent_count: int
    reaction_count: int
    reply_count: int
    status: str
    created_by: int
    created_at: datetime
    sent_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class DMCampaignBase(BaseModel):
    name: str
    template: str
    segment: str
    segment_config: Optional[Dict[str, Any]] = None
    delay_between_sends: int = 5
    is_active: bool = True


class DMCampaignCreate(DMCampaignBase):
    pass


class DMCampaignResponse(DMCampaignBase):
    id: int
    campaign_id: str
    group_id: int
    total_targets: int
    sent_count: int
    response_count: int
    status: str
    created_by: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class AnnouncementReactionResponse(BaseModel):
    id: int
    group_id: int
    message_id: int
    campaign_id: Optional[str]
    reactions: Dict[str, int]
    total_reactions: int
    member_reactions: Dict[str, List[int]]
    first_reaction_at: Optional[datetime]
    last_reaction_at: datetime
    posted_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ PERSONALIZATION SCHEMAS ============


class MemberPreferencesBase(BaseModel):
    digest_delivery: str = "group"
    dm_notifications: str = "mentions"
    show_on_leaderboard: bool = True
    show_on_member_map: bool = False
    bio: Optional[str] = None
    birthday: Optional[date] = None
    country: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    custom_fields: Optional[Dict[str, Any]] = None


class MemberPreferencesUpdate(BaseModel):
    digest_delivery: Optional[str] = None
    dm_notifications: Optional[str] = None
    show_on_leaderboard: Optional[bool] = None
    show_on_member_map: Optional[bool] = None
    bio: Optional[str] = None
    birthday: Optional[date] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None


class MemberPreferencesResponse(MemberPreferencesBase):
    id: int
    user_id: int
    group_id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminPreferencesBase(BaseModel):
    moderation_alerts: str = "critical"
    security_alerts: str = "all"
    member_alerts: str = "digest"
    delivery_channel: str = "group"
    digest_frequency: str = "daily"
    digest_time: str = "09:00"


class AdminPreferencesUpdate(BaseModel):
    moderation_alerts: Optional[str] = None
    security_alerts: Optional[str] = None
    member_alerts: Optional[str] = None
    delivery_channel: Optional[str] = None
    digest_frequency: Optional[str] = None
    digest_time: Optional[str] = None


class AdminPreferencesResponse(AdminPreferencesBase):
    id: int
    user_id: int
    group_id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroupThemeBase(BaseModel):
    primary_color: str = "#3B82F6"
    secondary_color: str = "#1E40AF"
    accent_color: str = "#10B981"
    background_color: str = "#0F172A"
    text_color: str = "#F8FAFC"
    card_style: str = "rounded"
    welcome_card_template: Optional[str] = None
    profile_card_template: Optional[str] = None
    logo_file_id: Optional[str] = None


class GroupThemeUpdate(BaseModel):
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    card_style: Optional[str] = None
    welcome_card_template: Optional[str] = None
    profile_card_template: Optional[str] = None
    logo_file_id: Optional[str] = None


class GroupThemeResponse(GroupThemeBase):
    id: int
    group_id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomRankNameBase(BaseModel):
    level_min: int
    level_max: int
    rank_name: str
    rank_icon: Optional[str] = None


class CustomRankNameCreate(CustomRankNameBase):
    pass


class CustomRankNameResponse(CustomRankNameBase):
    id: int
    group_id: int

    model_config = ConfigDict(from_attributes=True)


class CustomEconomyConfigBase(BaseModel):
    currency_name: str = "coins"
    currency_name_plural: str = "coins"
    currency_emoji: str = "🪙"
    shop_name: str = "Shop"
    treasury_name: str = "Treasury"
    daily_bonus_name: str = "Daily Bonus"
    leaderboard_name: str = "Leaderboard"


class CustomEconomyConfigResponse(CustomEconomyConfigBase):
    id: int
    group_id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WelcomeFlowBase(BaseModel):
    name: str
    priority: int = 0
    conditions: Dict[str, Any]
    welcome_message: str
    media_file_id: Optional[str] = None
    button_data: Optional[Dict[str, Any]] = None
    require_verification: bool = False
    verification_type: Optional[str] = None
    is_enabled: bool = True


class WelcomeFlowCreate(WelcomeFlowBase):
    pass


class WelcomeFlowResponse(WelcomeFlowBase):
    id: int
    flow_id: str
    group_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ SAFETY ARCHITECTURE SCHEMAS ============


class CoordinatedAttackBase(BaseModel):
    attack_type: str
    confidence: float
    involved_users: List[int]
    signals: Dict[str, Any]


class CoordinatedAttackResponse(CoordinatedAttackBase):
    id: int
    attack_id: str
    group_id: int
    action_taken: Optional[str]
    action_details: Optional[Dict[str, Any]]
    detected_at: datetime
    resolved_at: Optional[datetime]
    is_false_positive: bool

    model_config = ConfigDict(from_attributes=True)


class HoneypotTrapBase(BaseModel):
    trap_type: str
    trigger: str
    action: str = "ban"
    is_active: bool = True


class HoneypotTrapCreate(HoneypotTrapBase):
    pass


class HoneypotTrapResponse(HoneypotTrapBase):
    id: int
    group_id: int
    trigger_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationLevelBase(BaseModel):
    verification_level: int = 0
    verified_via: Optional[str] = None
    external_accounts: Optional[Dict[str, str]] = None


class VerificationLevelResponse(VerificationLevelBase):
    id: int
    user_id: int
    group_id: int
    verified_at: Optional[datetime]
    verified_by: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class VerificationRequirementBase(BaseModel):
    action_type: str
    min_verification_level: int = 0


class VerificationRequirementCreate(VerificationRequirementBase):
    pass


class VerificationRequirementResponse(VerificationRequirementBase):
    id: int
    group_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShadowWatchSessionBase(BaseModel):
    delay_seconds: int = 5
    notify_channel_id: Optional[int] = None
    reason: Optional[str] = None


class ShadowWatchSessionCreate(ShadowWatchSessionBase):
    user_id: int  # Target user


class ShadowWatchSessionResponse(ShadowWatchSessionBase):
    id: int
    user_id: int
    group_id: int
    started_at: datetime
    started_by: int
    messages_watched: int
    messages_blocked: int
    is_active: bool
    ended_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ShadowWatchMessageResponse(BaseModel):
    id: int
    session_id: int
    message_id: int
    content: str
    content_type: str
    status: str
    action_by: Optional[int]
    action_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ INTEGRATION SCHEMAS ============


class WebhookConfigBase(BaseModel):
    name: str
    webhook_type: str
    url: str
    method: str = "POST"
    headers: Optional[Dict[str, str]] = None
    secret: Optional[str] = None
    events: List[str] = []
    response_mapping: Optional[Dict[str, Any]] = None
    is_active: bool = True


class WebhookConfigCreate(WebhookConfigBase):
    pass


class WebhookConfigUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    secret: Optional[str] = None
    events: Optional[List[str]] = None
    response_mapping: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class WebhookConfigResponse(WebhookConfigBase):
    id: int
    webhook_id: str
    group_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookLogResponse(BaseModel):
    id: int
    webhook_id: str
    request_payload: Dict[str, Any]
    response_status: int
    response_body: Optional[Dict[str, Any]]
    success: bool
    error: Optional[str]
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventSubscriptionBase(BaseModel):
    name: str
    webhook_url: str
    event_types: List[str]
    filters: Optional[Dict[str, Any]] = None
    is_active: bool = True


class EventSubscriptionCreate(EventSubscriptionBase):
    pass


class EventSubscriptionResponse(EventSubscriptionBase):
    id: int
    subscription_id: str
    group_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ UNIQUE FEATURES SCHEMAS ============


class TimeCapsuleBase(BaseModel):
    title: str
    message: str
    media_file_id: Optional[str] = None
    open_at: datetime
    capsule_type: str = "message"


class TimeCapsuleCreate(TimeCapsuleBase):
    pass


class TimeCapsuleResponse(TimeCapsuleBase):
    id: int
    capsule_id: str
    group_id: int
    opened_at: Optional[datetime]
    message_id: Optional[int]
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroupSoundtrackBase(BaseModel):
    event_type: str
    audio_file_id: str
    audio_name: Optional[str] = None
    is_enabled: bool = True


class GroupSoundtrackCreate(GroupSoundtrackBase):
    pass


class GroupSoundtrackResponse(GroupSoundtrackBase):
    id: int
    group_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LegacyMemberBase(BaseModel):
    tribute_text: str
    contribution_highlights: List[str]
    active_from: datetime
    active_until: datetime
    badges_earned: List[str]
    final_rank: Optional[str] = None


class LegacyMemberCreate(LegacyMemberBase):
    user_id: int


class LegacyMemberResponse(LegacyMemberBase):
    id: int
    group_id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroupOathBase(BaseModel):
    oath_text: str
    confirmation_phrase: str
    require_on_join: bool = False


class GroupOathUpdate(BaseModel):
    oath_text: Optional[str] = None
    confirmation_phrase: Optional[str] = None
    require_on_join: Optional[bool] = None


class GroupOathResponse(GroupOathBase):
    id: int
    group_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OathAcceptanceResponse(BaseModel):
    id: int
    user_id: int
    group_id: int
    accepted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LiveCollaborationSessionBase(BaseModel):
    participants: List[int] = []


class LiveCollaborationSessionCreate(LiveCollaborationSessionBase):
    pass


class LiveCollaborationSessionResponse(LiveCollaborationSessionBase):
    id: int
    session_id: str
    group_id: int
    started_at: datetime
    started_by: int
    highlighted_messages: List[int]
    comments: List[Dict[str, Any]]
    is_active: bool
    ended_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class SeasonalModeBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    recurring_yearly: bool = True
    config_overrides: Dict[str, Any]
    theme_name: Optional[str] = None
    special_badges: Optional[List[str]] = None
    is_active: bool = True


class SeasonalModeCreate(SeasonalModeBase):
    pass


class SeasonalModeResponse(SeasonalModeBase):
    id: int
    mode_id: str
    group_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ INTELLIGENCE DASHBOARD SCHEMAS ============


class IntelligenceOverviewResponse(BaseModel):
    predictive_moderation: Dict[str, Any]
    conversation_graph: Dict[str, Any]
    anomaly_timeline: AnomalyTimelineResponse
    member_journeys: Dict[str, Any]
    topic_intelligence: TopicLandscapeResponse
    churn_predictions: ChurnRiskPanelResponse


class MemberIntelligenceResponse(BaseModel):
    predictive_score: Optional[PredictiveScoreResponse]
    journey: Optional[MemberJourneyResponse]
    churn_prediction: Optional[ChurnPredictionResponse]
    conversation_node: Optional[ConversationNodeResponse]
    verification_level: Optional[VerificationLevelResponse]
    preferences: Optional[MemberPreferencesResponse]


class GroupIntelligenceConfig(BaseModel):
    predictive_moderation_enabled: bool = True
    conversation_graph_enabled: bool = True
    anomaly_detection_enabled: bool = True
    member_journey_tracking: bool = True
    topic_intelligence_enabled: bool = True
    churn_prediction_enabled: bool = True
    analysis_frequency_hours: int = 1
