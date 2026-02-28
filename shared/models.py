"""SQLAlchemy models for Nexus."""

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
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class Role(PyEnum):
    """Member roles in a group."""

    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "mod"
    TRUSTED = "trusted"
    MEMBER = "member"
    RESTRICTED = "restricted"
    NEW = "new"


class ActionType(PyEnum):
    """Moderation action types."""

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


class ModuleCategory(PyEnum):
    """Module categories."""

    MODERATION = "moderation"
    GREETINGS = "greetings"
    ANTISPAM = "antispam"
    COMMUNITY = "community"
    AI = "ai"
    GAMES = "games"
    UTILITY = "utility"
    INTEGRATION = "integration"


# Association table for many-to-many relationships
class User(Base):
    """Global user model (cross-group)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[Optional[str]] = mapped_column(String(64))
    language_code: Mapped[Optional[str]] = mapped_column(String(10))
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_seen: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    members: Mapped[List["Member"]] = relationship("Member", back_populates="user")
    federations_owned: Mapped[List["Federation"]] = relationship(
        "Federation", back_populates="owner"
    )


class Group(Base):
    """Group/Chat model."""

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    username: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    language: Mapped[str] = mapped_column(String(10), default="en")
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")

    # Relationships
    members: Mapped[List["Member"]] = relationship("Member", back_populates="group")
    bot_instance: Mapped[Optional["BotInstance"]] = relationship(
        "BotInstance", back_populates="group", uselist=False
    )
    module_configs: Mapped[List["ModuleConfig"]] = relationship(
        "ModuleConfig", back_populates="group"
    )
    notes: Mapped[List["Note"]] = relationship("Note", back_populates="group")
    filters: Mapped[List["Filter"]] = relationship("Filter", back_populates="group")
    locks: Mapped[List["Lock"]] = relationship("Lock", back_populates="group")
    rules: Mapped[Optional["Rule"]] = relationship(
        "Rule", back_populates="group", uselist=False
    )
    greetings: Mapped[List["Greeting"]] = relationship(
        "Greeting", back_populates="group"
    )
    scheduled_messages: Mapped[List["ScheduledMessage"]] = relationship(
        "ScheduledMessage", back_populates="group"
    )


class BotInstance(Base):
    """Bot instance for shared and custom tokens."""

    __tablename__ = "bot_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    bot_telegram_id: Mapped[int] = mapped_column(BigInteger)
    bot_username: Mapped[str] = mapped_column(String(32))
    bot_name: Mapped[str] = mapped_column(String(64))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), unique=True)
    registered_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    webhook_url: Mapped[str] = mapped_column(String(500))

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="bot_instance")


class Member(Base):
    """Member model (user in a specific group)."""

    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("user_id", "group_id", name="uq_user_group"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_active: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    media_count: Mapped[int] = mapped_column(Integer, default=0)
    trust_score: Mapped[int] = mapped_column(Integer, default=50)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_streak_date: Mapped[Optional[date]] = mapped_column(Date)
    warn_count: Mapped[int] = mapped_column(Integer, default=0)
    mute_count: Mapped[int] = mapped_column(Integer, default=0)
    ban_count: Mapped[int] = mapped_column(Integer, default=0)
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False)
    mute_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_whitelisted: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String(20), default="member")
    custom_title: Mapped[Optional[str]] = mapped_column(String(64))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="members")
    group: Mapped["Group"] = relationship("Group", back_populates="members")
    badges: Mapped[List["MemberBadge"]] = relationship(
        "MemberBadge", back_populates="member"
    )
    profile: Mapped[Optional["MemberProfile"]] = relationship(
        "MemberProfile", back_populates="member", uselist=False
    )
    wallet: Mapped[Optional["Wallet"]] = relationship(
        "Wallet", back_populates="member", uselist=False
    )


class BadgeDefinition(Base):
    """Badge definitions."""

    __tablename__ = "badge_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    icon: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(30))
    auto_award_condition: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)


class MemberBadge(Base):
    """Badges earned by members."""

    __tablename__ = "member_badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), index=True)
    badge_slug: Mapped[str] = mapped_column(ForeignKey("badge_definitions.slug"))
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, name="metadata")

    # Relationships
    member: Mapped["Member"] = relationship("Member", back_populates="badges")
    badge: Mapped["BadgeDefinition"] = relationship("BadgeDefinition")


class MemberProfile(Base):
    """Extended member profiles."""

    __tablename__ = "member_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_profile_user_group"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    birthday: Mapped[Optional[date]] = mapped_column(Date)
    social_links: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    profile_theme: Mapped[str] = mapped_column(String(50), default="default")
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    member: Mapped["Member"] = relationship("Member", back_populates="profile")


class ModAction(Base):
    """Moderation actions log."""

    __tablename__ = "mod_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action_type: Mapped[str] = mapped_column(String(30), index=True)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    silent: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_inferred: Mapped[bool] = mapped_column(Boolean, default=False)
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    message_content: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reversed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reversed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class Warning(Base):
    """Warnings tracking."""

    __tablename__ = "warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    issued_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Federation(Base):
    """Federation for cross-group bans."""

    __tablename__ = "federations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="federations_owned")
    admins: Mapped[List["FederationAdmin"]] = relationship(
        "FederationAdmin", back_populates="federation"
    )
    members: Mapped[List["FederationMember"]] = relationship(
        "FederationMember", back_populates="federation"
    )
    bans: Mapped[List["FederationBan"]] = relationship(
        "FederationBan", back_populates="federation"
    )


class FederationAdmin(Base):
    """Federation administrators."""

    __tablename__ = "federation_admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    federation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("federations.id"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    added_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    added_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    federation: Mapped["Federation"] = relationship(
        "Federation", back_populates="admins"
    )


class FederationMember(Base):
    """Groups that are part of a federation."""

    __tablename__ = "federation_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    federation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("federations.id"), index=True
    )
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    joined_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    federation: Mapped["Federation"] = relationship(
        "Federation", back_populates="members"
    )


class FederationBan(Base):
    """Federation-wide bans."""

    __tablename__ = "federation_bans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    federation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("federations.id"), index=True
    )
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    banned_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    federation: Mapped["Federation"] = relationship("Federation", back_populates="bans")


class Note(Base):
    """Saved notes."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    keyword: Mapped[str] = mapped_column(String(64), index=True)
    content: Mapped[str] = mapped_column(Text)
    media_file_id: Mapped[Optional[str]] = mapped_column(String(500))
    media_type: Mapped[Optional[str]] = mapped_column(String(20))
    has_buttons: Mapped[bool] = mapped_column(Boolean, default=False)
    button_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="notes")


class Filter(Base):
    """Keyword auto-responses."""

    __tablename__ = "filters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    trigger: Mapped[str] = mapped_column(String(200))
    match_type: Mapped[str] = mapped_column(String(20), default="contains")
    response_type: Mapped[str] = mapped_column(String(20), default="text")
    response_content: Mapped[str] = mapped_column(Text)
    response_file_id: Mapped[Optional[str]] = mapped_column(String(500))
    action: Mapped[Optional[str]] = mapped_column(String(20))
    delete_trigger: Mapped[bool] = mapped_column(Boolean, default=False)
    admin_only: Mapped[bool] = mapped_column(Boolean, default=False)
    case_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="filters")


class Lock(Base):
    """Content type locks."""

    __tablename__ = "locks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    lock_type: Mapped[str] = mapped_column(String(50), index=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    mode: Mapped[str] = mapped_column(String(20), default="delete")
    mode_duration: Mapped[Optional[int]] = mapped_column(Integer)
    schedule_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule_windows: Mapped[Optional[List[Dict[str, str]]]] = mapped_column(JSON)
    allowlist: Mapped[Optional[Dict[str, List[str]]]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="locks")


class Rule(Base):
    """Group rules."""

    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), unique=True)
    content: Mapped[str] = mapped_column(Text)
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="rules")


class Greeting(Base):
    """Welcome and goodbye messages."""

    __tablename__ = "greetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    greeting_type: Mapped[str] = mapped_column(
        String(10), index=True
    )  # welcome/goodbye
    content: Mapped[str] = mapped_column(Text)
    media_file_id: Mapped[Optional[str]] = mapped_column(String(500))
    media_type: Mapped[Optional[str]] = mapped_column(String(20))
    has_buttons: Mapped[bool] = mapped_column(Boolean, default=False)
    button_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    delete_previous: Mapped[bool] = mapped_column(Boolean, default=False)
    delete_after_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    send_as_dm: Mapped[bool] = mapped_column(Boolean, default=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="greetings")


class CaptchaSetting(Base):
    """Captcha configuration."""

    __tablename__ = "captcha_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), unique=True)
    captcha_type: Mapped[str] = mapped_column(String(20), default="button")
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=90)
    action_on_fail: Mapped[str] = mapped_column(String(20), default="kick")
    mute_on_join: Mapped[bool] = mapped_column(Boolean, default=True)
    custom_text: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class ScheduledMessage(Base):
    """Scheduled and recurring messages."""

    __tablename__ = "scheduled_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    media_file_id: Mapped[Optional[str]] = mapped_column(String(500))
    media_type: Mapped[Optional[str]] = mapped_column(String(20))
    has_buttons: Mapped[bool] = mapped_column(Boolean, default=False)
    button_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    schedule_type: Mapped[str] = mapped_column(String(20), default="once")
    run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100))
    days_of_week: Mapped[Optional[List[int]]] = mapped_column(JSON)
    time_slot: Mapped[Optional[str]] = mapped_column(String(5))
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    max_runs: Mapped[Optional[int]] = mapped_column(Integer)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    self_destruct_after: Mapped[Optional[int]] = mapped_column(Integer)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_run: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="scheduled_messages")


class LogChannel(Base):
    """Log channel configuration."""

    __tablename__ = "log_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger)
    log_types: Mapped[List[str]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    added_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    added_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class AntifloodConfig(Base):
    """Anti-flood configuration."""

    __tablename__ = "antiflood_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), unique=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    message_limit: Mapped[int] = mapped_column(Integer, default=5)
    window_seconds: Mapped[int] = mapped_column(Integer, default=5)
    action: Mapped[str] = mapped_column(String(20), default="mute")
    action_duration: Mapped[int] = mapped_column(Integer, default=300)
    media_flood_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    media_limit: Mapped[int] = mapped_column(Integer, default=3)


class AntiraidConfig(Base):
    """Anti-raid configuration."""

    __tablename__ = "antiraid_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), unique=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    join_threshold: Mapped[int] = mapped_column(Integer, default=10)
    window_seconds: Mapped[int] = mapped_column(Integer, default=60)
    action: Mapped[str] = mapped_column(String(20), default="lock")
    auto_unlock_after: Mapped[int] = mapped_column(Integer, default=3600)
    notify_admins: Mapped[bool] = mapped_column(Boolean, default=True)


class BannedWord(Base):
    """Banned words (two lists per group)."""

    __tablename__ = "banned_words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    word: Mapped[str] = mapped_column(String(200))
    list_number: Mapped[int] = mapped_column(Integer, default=1)
    is_regex: Mapped[bool] = mapped_column(Boolean, default=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class BannedWordListConfig(Base):
    """Configuration for each banned word list."""

    __tablename__ = "banned_word_list_configs"
    __table_args__ = (
        UniqueConstraint("group_id", "list_number", name="uq_group_list"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    list_number: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(20), default="delete")
    action_duration: Mapped[Optional[int]] = mapped_column(Integer)
    delete_message: Mapped[bool] = mapped_column(Boolean, default=True)


class Approval(Base):
    """Approved users."""

    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class Connection(Base):
    """Multi-group connections for DM management."""

    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    connected_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ForceSubscribe(Base):
    """Force subscribe configuration."""

    __tablename__ = "force_subscribe"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), unique=True)
    channel_id: Mapped[int] = mapped_column(BigInteger)
    channel_username: Mapped[Optional[str]] = mapped_column(String(32))
    action_on_fail: Mapped[str] = mapped_column(String(20), default="restrict")
    message: Mapped[Optional[str]] = mapped_column(Text)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class GroupEvent(Base):
    """Group events."""

    __tablename__ = "group_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    location: Mapped[Optional[str]] = mapped_column(String(200))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="upcoming")


class EventRSVP(Base):
    """Event RSVPs."""

    __tablename__ = "event_rsvps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("group_events.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(10))
    rsvp_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class GroupMilestone(Base):
    """Group milestones and memory."""

    __tablename__ = "group_milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    happened_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, name="metadata")


class Wallet(Base):
    """Economy wallets."""

    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    balance: Mapped[int] = mapped_column(BigInteger, default=0)
    total_earned: Mapped[int] = mapped_column(BigInteger, default=0)
    total_spent: Mapped[int] = mapped_column(BigInteger, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    member: Mapped["Member"] = relationship("Member", back_populates="wallet")


class Transaction(Base):
    """Economy transactions."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_wallet_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wallets.id"))
    to_wallet_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wallets.id"))
    amount: Mapped[int] = mapped_column(BigInteger)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    transaction_type: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class EconomyConfig(Base):
    """Economy configuration per group."""

    __tablename__ = "economy_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), unique=True)
    currency_name: Mapped[str] = mapped_column(String(30), default="coins")
    currency_emoji: Mapped[str] = mapped_column(String(5), default="🪙")
    earn_per_message: Mapped[int] = mapped_column(Integer, default=1)
    earn_per_reaction: Mapped[int] = mapped_column(Integer, default=2)
    daily_bonus: Mapped[int] = mapped_column(Integer, default=100)
    xp_to_coin_enabled: Mapped[bool] = mapped_column(Boolean, default=False)


class Reputation(Base):
    """Reputation system."""

    __tablename__ = "reputation"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_rep_group_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    score: Mapped[int] = mapped_column(Integer, default=0)
    last_given_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class ReputationLog(Base):
    """Reputation transaction log."""

    __tablename__ = "reputation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    from_user: Mapped[int] = mapped_column(ForeignKey("users.id"))
    to_user: Mapped[int] = mapped_column(ForeignKey("users.id"))
    delta: Mapped[int] = mapped_column(Integer)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class GameSession(Base):
    """Active game sessions."""

    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    game_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="active")
    data: Mapped[Dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class GameScore(Base):
    """Game scores/leaderboard."""

    __tablename__ = "game_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    game_type: Mapped[str] = mapped_column(String(50))
    score: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class Poll(Base):
    """Extended polls."""

    __tablename__ = "polls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    question: Mapped[str] = mapped_column(String(300))
    options: Mapped[List[str]] = mapped_column(JSON)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    allows_multiple: Mapped[bool] = mapped_column(Boolean, default=False)
    closes_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class PollVote(Base):
    """Poll votes."""

    __tablename__ = "poll_votes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey("polls.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    option_indices: Mapped[List[int]] = mapped_column(JSON)
    voted_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class TopicConfig(Base):
    """Forum topic configurations."""

    __tablename__ = "topic_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    topic_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(100))
    enabled_modules: Mapped[Optional[Dict[str, bool]]] = mapped_column(JSON)
    custom_welcome: Mapped[Optional[str]] = mapped_column(Text)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)


class ModuleConfig(Base):
    """Per-group module configurations."""

    __tablename__ = "module_configs"
    __table_args__ = (
        UniqueConstraint("group_id", "module_name", name="uq_group_module"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    module_name: Mapped[str] = mapped_column(String(50), index=True)
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="module_configs")


class APIKey(Base):
    """API keys for REST API access."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    label: Mapped[Optional[str]] = mapped_column(String(100))
    scopes: Mapped[List[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CASCache(Base):
    """CAS (Combot Anti-Spam) cache."""

    __tablename__ = "cas_cache"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    is_banned: Mapped[bool] = mapped_column(Boolean)
    ban_reason: Mapped[Optional[str]] = mapped_column(Text)
    cached_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class ExportJob(Base):
    """Import/Export jobs."""

    __tablename__ = "export_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    modules: Mapped[List[str]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


# ============ NEW MODELS FOR ADVANCED FEATURES ============


class BotTemplate(Base):
    """Pre-built bot templates (like botifi.me, ManyBot)."""

    __tablename__ = "bot_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(30))
    icon: Mapped[str] = mapped_column(String(50))
    preview_image: Mapped[Optional[str]] = mapped_column(String(500))

    # Template structure (flow JSON)
    flow_data: Mapped[Dict[str, Any]] = mapped_column(JSON)

    # Features included
    features: Mapped[List[str]] = mapped_column(JSON)
    commands: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)

    # Metadata
    author: Mapped[str] = mapped_column(String(100))
    author_url: Mapped[Optional[str]] = mapped_column(String(500))
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)

    # Usage stats
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class UserBot(Base):
    """User-created bots via flow builder or AI."""

    __tablename__ = "user_bots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Bot identity
    name: Mapped[str] = mapped_column(String(100))
    username: Mapped[Optional[str]] = mapped_column(String(32), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    bot_token: Mapped[Optional[str]] = mapped_column(String(500))
    bot_token_encrypted: Mapped[Optional[str]] = mapped_column(String(200))

    # Bot type: 'custom' (own token), 'nexus_powered' (nexus infrastructure)
    bot_type: Mapped[str] = mapped_column(String(20), default="nexus_powered")

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    # Flow reference
    flow_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bot_flows.id"))

    # Settings
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Stats
    total_users: Mapped[int] = mapped_column(Integer, default=0)
    total_messages: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class BotFlow(Base):
    """Flow definitions for bot builders."""

    __tablename__ = "bot_flows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Flow info
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Flow structure - nodes and connections
    nodes: Mapped[List[Dict[str, Any]]] = mapped_column(JSON)
    connections: Mapped[List[Dict[str, Any]]] = mapped_column(JSON)

    # Variables and configurations
    variables: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Trigger configuration
    triggers: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)

    # Stats
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class FlowExecution(Base):
    """Flow execution logs."""

    __tablename__ = "flow_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flow_id: Mapped[int] = mapped_column(ForeignKey("bot_flows.id"), index=True)
    user_bot_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_bots.id"))

    # Execution data
    trigger_type: Mapped[str] = mapped_column(String(30))
    trigger_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Path taken
    node_path: Mapped[List[str]] = mapped_column(JSON)

    # Input/Output
    user_input: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    bot_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="running")
    error: Mapped[Optional[str]] = mapped_column(Text)

    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class ScrapingJob(Base):
    """Web scraping jobs."""

    __tablename__ = "scraping_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"))

    # Job info
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Target configuration
    target_url: Mapped[str] = mapped_column(String(1000))
    selector: Mapped[Optional[str]] = mapped_column(String(500))
    method: Mapped[str] = mapped_column(String(20), default="GET")
    headers: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    body: Mapped[Optional[str]] = mapped_column(Text)

    # Schedule
    schedule_type: Mapped[str] = mapped_column(String(20), default="manual")
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100))

    # Post-processing
    transform_rule: Mapped[Optional[str]] = mapped_column(Text)
    output_format: Mapped[str] = mapped_column(String(20), default="text")

    # Action on new data
    action_type: Mapped[str] = mapped_column(String(30), default="notify")
    action_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_run: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    last_error: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class ScrapingResult(Base):
    """Scraping results storage."""

    __tablename__ = "scraping_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("scraping_jobs.id"), index=True)

    # Result data
    data: Mapped[Dict[str, Any]] = mapped_column(JSON)
    raw_html: Mapped[Optional[Text]] = mapped_column(Text)
    status_code: Mapped[int] = mapped_column(Integer)

    # Metadata
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class ChannelConfig(Base):
    """Channel configuration for broadcasting."""

    __tablename__ = "channel_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"))

    # Channel info
    channel_id: Mapped[int] = mapped_column(BigInteger)
    channel_name: Mapped[str] = mapped_column(String(100))
    channel_username: Mapped[Optional[str]] = mapped_column(String(32))

    # Configuration
    channel_type: Mapped[str] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Auto-post settings
    auto_post_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    post_triggers: Mapped[Optional[List[str]]] = mapped_column(JSON)
    filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Formatting
    format_template: Mapped[Optional[str]] = mapped_column(Text)
    include_source: Mapped[bool] = mapped_column(Boolean, default=True)
    include_media: Mapped[bool] = mapped_column(Boolean, default=True)

    # Stats
    total_posts: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class AutoForward(Base):
    """Auto-forward rules between chats."""

    __tablename__ = "auto_forwards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"))

    # Source and destination
    source_chat_id: Mapped[int] = mapped_column(BigInteger)
    dest_chat_id: Mapped[int] = mapped_column(BigInteger)

    # Configuration
    forward_type: Mapped[str] = mapped_column(String(30))
    filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Processing
    transform_content: Mapped[Optional[str]] = mapped_column(Text)
    add_caption: Mapped[Optional[str]] = mapped_column(Text)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Stats
    total_forwarded: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class AdvancedExport(Base):
    """Advanced export configurations."""

    __tablename__ = "advanced_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"))

    # Export config
    name: Mapped[str] = mapped_column(String(100))
    export_type: Mapped[str] = mapped_column(String(50))

    # Data to include
    data_sources: Mapped[List[str]] = mapped_column(JSON)
    filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Format options
    format: Mapped[str] = mapped_column(String(20), default="json")
    include_media: Mapped[bool] = mapped_column(Boolean, default=False)
    compress: Mapped[bool] = mapped_column(Boolean, default=True)

    # Schedule
    schedule_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule_cron: Mapped[Optional[str]] = mapped_column(String(100))
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_run: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Delivery
    delivery_method: Mapped[str] = mapped_column(String(20), default="file")
    delivery_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Status
    last_status: Mapped[Optional[str]] = mapped_column(String(20))
    last_file_path: Mapped[Optional[str]] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class AIConversation(Base):
    """AI chatbot conversations."""

    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_bot_id: Mapped[int] = mapped_column(ForeignKey("user_bots.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Context
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)

    # Stats
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class AIMessage(Base):
    """AI chatbot messages."""

    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("ai_conversations.id"), index=True
    )

    # Message
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    tokens: Mapped[int] = mapped_column(Integer, default=0)

    # Extra data
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, name="metadata")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class CustomCommand(Base):
    """Custom commands created by users."""

    __tablename__ = "custom_commands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user_bot_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_bots.id"))

    # Command definition
    command: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[Optional[str]] = mapped_column(String(200))

    # Response
    response_type: Mapped[str] = mapped_column(String(20), default="text")
    response_content: Mapped[str] = mapped_column(Text)
    response_media: Mapped[Optional[str]] = mapped_column(String(500))
    buttons: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Behavior
    allow_variables: Mapped[bool] = mapped_column(Boolean, default=True)
    require_args: Mapped[bool] = mapped_column(Boolean, default=False)
    admin_only: Mapped[bool] = mapped_column(Boolean, default=False)

    # Stats
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class KeywordResponder(Base):
    """Keyword-based auto-responders."""

    __tablename__ = "keyword_responders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user_bot_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_bots.id"))

    # Keywords
    keywords: Mapped[List[str]] = mapped_column(JSON)
    match_type: Mapped[str] = mapped_column(String(20), default="contains")
    case_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)

    # Response
    responses: Mapped[List[str]] = mapped_column(JSON)
    random_response: Mapped[bool] = mapped_column(Boolean, default=True)

    # Media
    media_type: Mapped[Optional[str]] = mapped_column(String(20))
    media_file_id: Mapped[Optional[str]] = mapped_column(String(500))

    # Behavior
    delete_trigger: Mapped[bool] = mapped_column(Boolean, default=False)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # Stats
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class BotAnalytics(Base):
    """Analytics for user-created bots."""

    __tablename__ = "bot_analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_bot_id: Mapped[int] = mapped_column(ForeignKey("user_bots.id"), index=True)

    # Time period
    date: Mapped[date] = mapped_column(Date, index=True)

    # Metrics
    messages_received: Mapped[int] = mapped_column(Integer, default=0)
    messages_sent: Mapped[int] = mapped_column(Integer, default=0)
    commands_used: Mapped[int] = mapped_column(Integer, default=0)
    new_users: Mapped[int] = mapped_column(Integer, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)

    # Engagement
    avg_response_time_ms: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class SubscriptionPlan(Base):
    """Subscription plans for premium features."""

    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)

    # Pricing
    price_monthly: Mapped[int] = mapped_column(Integer, default=0)
    price_yearly: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Features
    features: Mapped[List[str]] = mapped_column(JSON)
    limits: Mapped[Dict[str, int]] = mapped_column(JSON)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class UserSubscription(Base):
    """User subscriptions."""

    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("subscription_plans.id"))

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active")

    # Billing
    billing_cycle: Mapped[str] = mapped_column(String(10), default="monthly")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Payment
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    last_payment_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_payment_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
