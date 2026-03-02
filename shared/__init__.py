"""Shared components for Nexus."""

from shared.database import AsyncSessionLocal, get_db, init_db
from shared.models import Base
from shared.redis_client import GroupScopedRedis, get_redis
from shared.event_bus import (
    EventBus, NexusEvent, EventType,
    get_event_bus, publish_event
)
from shared.action_executor import (
    ActionExecutor, ActionContext, ActionResult,
    get_action_executor
)
from shared.websocket_manager import (
    WebSocketManager, ConnectedClient, WSMessage,
    get_ws_manager, shutdown_ws_manager
)
from shared.health_check import (
    ModuleHealthChecker, SystemHealthChecker,
    HealthCheckStatus, HealthCheckResult, ModuleHealthReport,
    get_health_checker, run_startup_health_checks
)

# Import intelligence models and add to Base metadata
from shared.models_intelligence import (
    BehaviorPattern,
    MemberBehaviorLog,
    PredictiveScore,
    ConversationNode,
    ConversationEdge,
    AnomalyEvent,
    MemberJourney,
    TopicCluster,
    ChurnPrediction,
    AutomationRule,
    BehavioralTripwire,
    MemberTripwireState,
    TimeBasedRuleSet,
    SmartCooldown,
    AutomatedEvent,
    BroadcastCampaign,
    DMCampaign,
    AnnouncementReaction,
    MemberPreferences,
    AdminPreferences,
    GroupTheme,
    CustomRankName,
    CustomEconomyConfig,
    WelcomeFlow,
    CoordinatedAttack,
    HoneypotTrap,
    VerificationLevel,
    VerificationRequirement,
    ShadowWatchSession,
    ShadowWatchMessage,
    WebhookConfig,
    WebhookLog,
    EventSubscription,
    TimeCapsule,
    GroupSoundtrack,
    LegacyMember,
    GroupOath,
    OathAcceptance,
    LiveCollaborationSession,
    SeasonalMode,
)

__all__ = [
    # Database
    "Base",
    "AsyncSessionLocal",
    "get_db",
    "init_db",
    # Redis
    "GroupScopedRedis",
    "get_redis",
    # Event Bus
    "EventBus",
    "NexusEvent",
    "EventType",
    "get_event_bus",
    "publish_event",
    # Action Executor
    "ActionExecutor",
    "ActionContext",
    "ActionResult",
    "get_action_executor",
    # WebSocket
    "WebSocketManager",
    "ConnectedClient",
    "WSMessage",
    "get_ws_manager",
    "shutdown_ws_manager",
    # Health Check
    "ModuleHealthChecker",
    "SystemHealthChecker",
    "HealthCheckStatus",
    "HealthCheckResult",
    "ModuleHealthReport",
    "get_health_checker",
    "run_startup_health_checks",
    # Intelligence models
    "BehaviorPattern",
    "MemberBehaviorLog",
    "PredictiveScore",
    "ConversationNode",
    "ConversationEdge",
    "AnomalyEvent",
    "MemberJourney",
    "TopicCluster",
    "ChurnPrediction",
    "AutomationRule",
    "BehavioralTripwire",
    "MemberTripwireState",
    "TimeBasedRuleSet",
    "SmartCooldown",
    "AutomatedEvent",
    "BroadcastCampaign",
    "DMCampaign",
    "AnnouncementReaction",
    "MemberPreferences",
    "AdminPreferences",
    "GroupTheme",
    "CustomRankName",
    "CustomEconomyConfig",
    "WelcomeFlow",
    "CoordinatedAttack",
    "HoneypotTrap",
    "VerificationLevel",
    "VerificationRequirement",
    "ShadowWatchSession",
    "ShadowWatchMessage",
    "WebhookConfig",
    "WebhookLog",
    "EventSubscription",
    "TimeCapsule",
    "GroupSoundtrack",
    "LegacyMember",
    "GroupOath",
    "OathAcceptance",
    "LiveCollaborationSession",
    "SeasonalMode",
]
