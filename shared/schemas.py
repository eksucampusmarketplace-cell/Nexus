"""Pydantic schemas for Nexus API."""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Enums
class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "mod"
    TRUSTED = "trusted"
    MEMBER = "member"
    RESTRICTED = "restricted"
    NEW = "new"


class ActionType(str, Enum):
    WARN = "warn"
    MUTE = "mute"
    BAN = "ban"
    KICK = "kick"
    UNMUTE = "unmute"
    UNBAN = "unban"
    APPROVE = "approve"
    RESTRICT = "restrict"
    TRUST = "trust"
    UNTRUST = "untrust"


class ModuleCategory(str, Enum):
    MODERATION = "moderation"
    GREETINGS = "greetings"
    ANTISPAM = "antispam"
    COMMUNITY = "community"
    AI = "ai"
    GAMES = "games"
    UTILITY = "utility"
    INTEGRATION = "integration"


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(from_attributes=True)


class TimestampMixin(BaseSchema):
    created_at: datetime
    updated_at: Optional[datetime] = None


# User schemas
class UserBase(BaseSchema):
    telegram_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    is_bot: bool = False
    is_premium: bool = False


class UserCreate(UserBase):
    pass


class UserResponse(UserBase, TimestampMixin):
    id: int


# Group schemas
class GroupBase(BaseSchema):
    telegram_id: int
    title: str
    username: Optional[str] = None
    language: str = "en"
    timezone: str = "UTC"


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseSchema):
    title: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    is_premium: Optional[bool] = None


class GroupResponse(GroupBase, TimestampMixin):
    id: int
    member_count: int
    is_premium: bool
    owner_id: Optional[int]


class GroupStats(BaseSchema):
    total_members: int
    active_members_24h: int
    active_members_7d: int
    new_members_24h: int
    messages_24h: int
    top_members: List[Dict[str, Any]]
    mood_score: float


# Member schemas
class MemberBase(BaseSchema):
    trust_score: int = 50
    role: Role = Role.MEMBER
    custom_title: Optional[str] = None


class MemberCreate(MemberBase):
    user_id: int
    group_id: int


class MemberUpdate(BaseSchema):
    trust_score: Optional[int] = None
    role: Optional[Role] = None
    custom_title: Optional[str] = None
    is_approved: Optional[bool] = None
    is_whitelisted: Optional[bool] = None


class MemberResponse(MemberBase, TimestampMixin):
    id: int
    user_id: int
    group_id: int
    joined_at: datetime
    last_active: datetime
    message_count: int
    media_count: int
    xp: int
    level: int
    streak_days: int
    warn_count: int
    is_muted: bool
    is_banned: bool
    is_approved: bool
    is_whitelisted: bool
    user: UserResponse


class MemberProfileResponse(BaseSchema):
    id: int
    bio: Optional[str] = None
    birthday: Optional[date] = None
    social_links: Optional[Dict[str, str]] = None
    profile_theme: str = "default"
    is_public: bool = True


class MemberHistoryResponse(BaseSchema):
    warnings: List[Dict[str, Any]]
    mutes: List[Dict[str, Any]]
    bans: List[Dict[str, Any]]
    reputation: int
    achievements: List[str]


# Badge schemas
class BadgeDefinitionResponse(BaseSchema):
    id: int
    slug: str
    name: str
    description: str
    icon: str
    category: str


class MemberBadgeResponse(BaseSchema):
    id: int
    badge: BadgeDefinitionResponse
    earned_at: datetime


# Moderation schemas
class ModerationActionBase(BaseSchema):
    action_type: ActionType
    reason: Optional[str] = None
    duration_seconds: Optional[int] = None
    silent: bool = False


class ModerationActionCreate(ModerationActionBase):
    target_user_id: int


class ModerationActionResponse(ModerationActionBase, TimestampMixin):
    id: int
    group_id: int
    target_user_id: int
    actor_id: int
    ai_inferred: bool


class WarningResponse(BaseSchema):
    id: int
    reason: str
    issued_by: UserResponse
    created_at: datetime
    expires_at: Optional[datetime]


class WarnRequest(BaseSchema):
    reason: Optional[str] = None
    silent: bool = False


class MuteRequest(BaseSchema):
    duration: str  # e.g., "1h", "2d", "30m"
    reason: Optional[str] = None
    silent: bool = False


class BanRequest(BaseSchema):
    duration: Optional[str] = None  # None = permanent
    reason: Optional[str] = None
    silent: bool = False


# Federation schemas
class FederationBase(BaseSchema):
    name: str
    description: Optional[str] = None
    is_public: bool = False


class FederationCreate(FederationBase):
    pass


class FederationUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class FederationResponse(FederationBase, TimestampMixin):
    id: UUID
    owner_id: int
    owner: UserResponse


class FederationBanRequest(BaseSchema):
    reason: str
    expires_at: Optional[datetime] = None


class FederationBanResponse(BaseSchema):
    id: int
    target_user: UserResponse
    banned_by: UserResponse
    reason: str
    created_at: datetime
    expires_at: Optional[datetime]


# Note schemas
class NoteBase(BaseSchema):
    keyword: str
    content: str
    is_private: bool = False


class NoteCreate(NoteBase):
    media_file_id: Optional[str] = None
    media_type: Optional[str] = None
    has_buttons: bool = False
    button_data: Optional[Dict[str, Any]] = None


class NoteUpdate(BaseSchema):
    content: Optional[str] = None
    is_private: Optional[bool] = None


class NoteResponse(NoteBase, TimestampMixin):
    id: int
    group_id: int
    created_by: UserResponse


# Filter schemas
class FilterBase(BaseSchema):
    trigger: str
    match_type: str = "contains"
    response_type: str = "text"
    response_content: str
    action: Optional[str] = None
    delete_trigger: bool = False
    admin_only: bool = False
    case_sensitive: bool = False


class FilterCreate(FilterBase):
    pass


class FilterResponse(FilterBase, TimestampMixin):
    id: int
    group_id: int
    created_by: UserResponse


# Lock schemas
class LockBase(BaseSchema):
    lock_type: str
    is_locked: bool = False
    mode: str = "delete"
    mode_duration: Optional[int] = None


class LockUpdate(BaseSchema):
    is_locked: Optional[bool] = None
    mode: Optional[str] = None
    mode_duration: Optional[int] = None
    schedule_enabled: Optional[bool] = None
    schedule_windows: Optional[List[Dict[str, str]]] = None
    allowlist: Optional[Dict[str, List[str]]] = None


class LockResponse(LockBase, TimestampMixin):
    id: int
    group_id: int
    schedule_enabled: bool
    schedule_windows: Optional[List[Dict[str, str]]]
    allowlist: Optional[Dict[str, List[str]]]


# Greeting schemas
class GreetingBase(BaseSchema):
    greeting_type: str  # welcome/goodbye
    content: str
    delete_previous: bool = False
    delete_after_seconds: Optional[int] = None
    send_as_dm: bool = False
    is_enabled: bool = True


class GreetingCreate(GreetingBase):
    media_file_id: Optional[str] = None
    media_type: Optional[str] = None
    has_buttons: bool = False
    button_data: Optional[Dict[str, Any]] = None


class GreetingResponse(GreetingBase, TimestampMixin):
    id: int
    group_id: int
    updated_by: UserResponse


# Scheduled Message schemas
class ScheduledMessageBase(BaseSchema):
    content: str
    schedule_type: str = "once"
    run_at: Optional[datetime] = None
    cron_expression: Optional[str] = None
    days_of_week: Optional[List[int]] = None
    time_slot: Optional[str] = None
    is_enabled: bool = True


class ScheduledMessageCreate(ScheduledMessageBase):
    media_file_id: Optional[str] = None
    media_type: Optional[str] = None
    has_buttons: bool = False
    button_data: Optional[Dict[str, Any]] = None
    end_date: Optional[date] = None
    max_runs: Optional[int] = None
    self_destruct_after: Optional[int] = None


class ScheduledMessageResponse(ScheduledMessageBase, TimestampMixin):
    id: int
    group_id: int
    run_count: int
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    created_by: UserResponse


# Module Config schemas
class ModuleConfigBase(BaseSchema):
    module_name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    is_enabled: bool = False


class ModuleConfigUpdate(BaseSchema):
    config: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class ModuleConfigResponse(ModuleConfigBase, TimestampMixin):
    id: int
    group_id: int
    updated_by: Optional[UserResponse]


class ModuleInfoResponse(BaseSchema):
    name: str
    version: str
    author: str
    description: str
    category: ModuleCategory
    dependencies: List[str]
    conflicts: List[str]
    is_enabled: bool


# Economy schemas
class WalletResponse(BaseSchema):
    id: int
    balance: int
    total_earned: int
    total_spent: int


class TransactionRequest(BaseSchema):
    to_user_id: int
    amount: int
    reason: Optional[str] = None


class TransactionResponse(BaseSchema):
    id: int
    amount: int
    reason: Optional[str]
    transaction_type: str
    created_at: datetime


class EconomyConfigResponse(BaseSchema):
    currency_name: str
    currency_emoji: str
    earn_per_message: int
    earn_per_reaction: int
    daily_bonus: int


# Reputation schemas
class ReputationResponse(BaseSchema):
    score: int
    last_given_at: Optional[datetime]


class ReputationRequest(BaseSchema):
    delta: int
    reason: Optional[str] = None


# Poll schemas
class PollBase(BaseSchema):
    question: str
    options: List[str]
    is_anonymous: bool = True
    allows_multiple: bool = False
    closes_at: Optional[datetime] = None


class PollCreate(PollBase):
    pass


class PollResponse(PollBase, TimestampMixin):
    id: int
    group_id: int
    is_closed: bool
    created_by: UserResponse
    votes: List[Dict[str, Any]]


# Captcha schemas
class CaptchaSettingResponse(BaseSchema):
    captcha_type: str
    timeout_seconds: int
    action_on_fail: str
    mute_on_join: bool
    custom_text: Optional[str]


class CaptchaSettingUpdate(BaseSchema):
    captcha_type: Optional[str] = None
    timeout_seconds: Optional[int] = None
    action_on_fail: Optional[str] = None
    mute_on_join: Optional[bool] = None
    custom_text: Optional[str] = None


# Anti-spam schemas
class AntifloodConfigResponse(BaseSchema):
    is_enabled: bool
    message_limit: int
    window_seconds: int
    action: str
    action_duration: int
    media_flood_enabled: bool
    media_limit: int


class AntiraidConfigResponse(BaseSchema):
    is_enabled: bool
    join_threshold: int
    window_seconds: int
    action: str
    auto_unlock_after: int
    notify_admins: bool


# Banned Word schemas
class BannedWordBase(BaseSchema):
    word: str
    list_number: int = 1
    is_regex: bool = False


class BannedWordCreate(BannedWordBase):
    pass


class BannedWordResponse(BannedWordBase, TimestampMixin):
    id: int
    is_enabled: bool
    created_by: UserResponse


class BannedWordListConfigResponse(BaseSchema):
    list_number: int
    action: str
    action_duration: Optional[int]
    delete_message: bool


# Analytics schemas
class AnalyticsOverviewResponse(BaseSchema):
    total_messages_24h: int
    total_messages_7d: int
    active_members_24h: int
    active_members_7d: int
    new_members_7d: int
    left_members_7d: int
    mod_actions_24h: int
    mod_actions_7d: int


class ActivityHeatmapResponse(BaseSchema):
    hours: List[str]
    days: List[str]
    data: List[List[int]]


class MemberGrowthResponse(BaseSchema):
    dates: List[str]
    member_count: List[int]
    new_members: List[int]
    left_members: List[int]


# API Key schemas
class APIKeyCreate(BaseSchema):
    label: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseSchema):
    id: int
    key: str  # Only shown once on creation
    label: Optional[str]
    scopes: List[str]
    created_at: datetime
    last_used: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool


class APIKeyListResponse(BaseSchema):
    id: int
    label: Optional[str]
    scopes: List[str]
    created_at: datetime
    last_used: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool


# Token schemas
class BotTokenRegisterRequest(BaseSchema):
    token: str


class BotTokenResponse(BaseSchema):
    bot_telegram_id: int
    bot_username: str
    bot_name: str
    is_active: bool
    registered_at: datetime


# Auth schemas
class AuthTokenRequest(BaseSchema):
    init_data: str  # Telegram WebApp initData


class AuthTokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserPermissionsResponse(BaseSchema):
    is_owner: bool
    is_admin: bool
    is_moderator: bool
    can_manage_modules: bool
    can_moderate: bool
    permissions: List[str]


# Event schemas
class GroupEventBase(BaseSchema):
    title: str
    description: Optional[str] = None
    starts_at: datetime
    ends_at: Optional[datetime] = None
    location: Optional[str] = None
    is_recurring: bool = False


class GroupEventCreate(GroupEventBase):
    pass


class GroupEventResponse(GroupEventBase, TimestampMixin):
    id: int
    group_id: int
    status: str
    created_by: UserResponse
    rsvp_count: int


class EventRSVPRequest(BaseSchema):
    status: str  # going/maybe/not_going


# Export/Import schemas
class ExportRequest(BaseSchema):
    modules: Optional[List[str]] = None


class ExportJobResponse(BaseSchema):
    id: int
    status: str
    file_url: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


# Error schemas
class ErrorResponse(BaseSchema):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# Pagination schemas
class PaginatedResponse(BaseSchema):
    total: int
    page: int
    per_page: int
    pages: int


class PaginatedMembersResponse(PaginatedResponse):
    items: List[MemberResponse]


class PaginatedNotesResponse(PaginatedResponse):
    items: List[NoteResponse]


class PaginatedFiltersResponse(PaginatedResponse):
    items: List[FilterResponse]


class PaginatedActionsResponse(PaginatedResponse):
    items: List[ModerationActionResponse]
