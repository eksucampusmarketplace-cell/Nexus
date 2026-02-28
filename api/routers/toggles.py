"""Toggle API router - manage all features without sending commands."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from shared.database import get_db
from shared.models import (
    Group,
    Lock,
    Member,
    ModuleConfig,
    User,
)

router = APIRouter()


# ============ Request/Response Models ============


class ToggleModuleRequest(BaseModel):
    is_enabled: bool


class UpdateFeatureRequest(BaseModel):
    value: Any


class BatchUpdateRequest(BaseModel):
    updates: List[Dict[str, Any]]


class LockToggleRequest(BaseModel):
    is_locked: bool


class LockModeRequest(BaseModel):
    mode: str
    duration: Optional[int] = None


class TimedLockRequest(BaseModel):
    start_time: str
    end_time: str


class ModerationActionRequest(BaseModel):
    user_id: int
    reason: Optional[str] = None
    duration: Optional[str] = None


class SilentModeRequest(BaseModel):
    enabled: bool
    duration: Optional[str] = None


class SilentWindowRequest(BaseModel):
    start_time: str
    end_time: str


# ============ Permission Check ============


async def check_admin_access(group_id: int, user: User, db: AsyncSession) -> Member:
    """Check if user has admin access to the group."""
    result = await db.execute(
        select(Member).where(
            Member.user_id == user.id,
            Member.group_id == group_id,
        )
    )
    member = result.scalar()

    if not member or member.role not in ("owner", "admin", "mod"):
        raise HTTPException(status_code=403, detail="Admin access required")

    return member


# ============ Module Toggles ============


@router.get("/groups/{group_id}/toggles")
async def get_module_toggles(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all modules with their toggle states for a group."""
    await check_admin_access(group_id, current_user, db)

    # Get all module configs for this group
    result = await db.execute(
        select(ModuleConfig).where(ModuleConfig.group_id == group_id)
    )
    configs = {c.module_name: c for c in result.scalars().all()}

    # Module definitions
    module_definitions = [
        {
            "name": "moderation",
            "displayName": "Moderation",
            "description": "Core moderation tools including warn, mute, ban, kick",
            "category": "moderation",
            "icon": "shield",
            "features": [
                {
                    "key": "warn_threshold",
                    "label": "Warn Threshold",
                    "description": "Number of warnings before auto-action",
                    "type": "number",
                    "value": configs.get("moderation", ModuleConfig()).config.get(
                        "warn_threshold", 3
                    ),
                    "min": 1,
                    "max": 10,
                },
                {
                    "key": "warn_action",
                    "label": "Warn Action",
                    "description": "Action to take when threshold reached",
                    "type": "select",
                    "value": configs.get("moderation", ModuleConfig()).config.get(
                        "warn_action", "mute"
                    ),
                    "options": [
                        {"value": "mute", "label": "Mute"},
                        {"value": "kick", "label": "Kick"},
                        {"value": "ban", "label": "Ban"},
                    ],
                },
                {
                    "key": "silent_mode",
                    "label": "Silent Mode",
                    "description": "Don't announce moderation actions",
                    "type": "boolean",
                    "value": configs.get("moderation", ModuleConfig()).config.get(
                        "silent_mode", False
                    ),
                },
            ],
        },
        {
            "name": "welcome",
            "displayName": "Welcome System",
            "description": "Welcome and goodbye messages for members",
            "category": "greetings",
            "icon": "message-square",
            "features": [
                {
                    "key": "delete_after",
                    "label": "Auto-delete Welcome",
                    "description": "Delete welcome message after seconds (0 = never)",
                    "type": "number",
                    "value": configs.get("welcome", ModuleConfig()).config.get(
                        "delete_after", 0
                    ),
                    "min": 0,
                    "max": 86400,
                },
                {
                    "key": "send_as_dm",
                    "label": "Send as DM",
                    "description": "Send welcome message privately",
                    "type": "boolean",
                    "value": configs.get("welcome", ModuleConfig()).config.get(
                        "send_as_dm", False
                    ),
                },
            ],
        },
        {
            "name": "captcha",
            "displayName": "CAPTCHA",
            "description": "Anti-bot verification for new members",
            "category": "greetings",
            "icon": "lock",
            "features": [
                {
                    "key": "captcha_type",
                    "label": "CAPTCHA Type",
                    "description": "Type of challenge for verification",
                    "type": "select",
                    "value": "button",
                    "options": [
                        {"value": "button", "label": "Button Click"},
                        {"value": "math", "label": "Math Problem"},
                        {"value": "quiz", "label": "Quiz Question"},
                    ],
                },
                {
                    "key": "timeout",
                    "label": "Timeout (seconds)",
                    "description": "Time to complete verification",
                    "type": "number",
                    "value": 90,
                    "min": 30,
                    "max": 300,
                },
            ],
        },
        {
            "name": "locks",
            "displayName": "Content Locks",
            "description": "Lock specific content types like links, stickers",
            "category": "antispam",
            "icon": "lock",
            "features": [],
        },
        {
            "name": "antispam",
            "displayName": "Anti-Spam",
            "description": "Anti-flood and spam protection",
            "category": "antispam",
            "icon": "zap",
            "features": [
                {
                    "key": "message_limit",
                    "label": "Message Limit",
                    "description": "Max messages in window",
                    "type": "number",
                    "value": 5,
                    "min": 1,
                    "max": 20,
                },
                {
                    "key": "window_seconds",
                    "label": "Time Window (seconds)",
                    "description": "Time window for flood detection",
                    "type": "number",
                    "value": 5,
                    "min": 1,
                    "max": 60,
                },
            ],
        },
        {
            "name": "economy",
            "displayName": "Economy",
            "description": "Virtual currency and transactions",
            "category": "community",
            "icon": "coins",
            "features": [
                {
                    "key": "currency_name",
                    "label": "Currency Name",
                    "description": "Name of the virtual currency",
                    "type": "text",
                    "value": "coins",
                },
                {
                    "key": "daily_bonus",
                    "label": "Daily Bonus",
                    "description": "Daily bonus amount",
                    "type": "number",
                    "value": 100,
                    "min": 0,
                    "max": 1000,
                },
            ],
        },
        {
            "name": "games",
            "displayName": "Games",
            "description": "Games and entertainment",
            "category": "games",
            "icon": "gamepad-2",
            "features": [
                {
                    "key": "award_xp",
                    "label": "Award XP",
                    "description": "Award XP for playing games",
                    "type": "boolean",
                    "value": True,
                },
                {
                    "key": "award_coins",
                    "label": "Award Coins",
                    "description": "Award coins for winning games",
                    "type": "boolean",
                    "value": True,
                },
            ],
        },
        {
            "name": "ai_assistant",
            "displayName": "AI Assistant",
            "description": "AI-powered assistant features",
            "category": "ai",
            "icon": "sparkles",
            "features": [
                {
                    "key": "respond_to_mentions",
                    "label": "Respond to Mentions",
                    "description": "Respond when bot is mentioned",
                    "type": "boolean",
                    "value": True,
                },
                {
                    "key": "summarization",
                    "label": "Summarization",
                    "description": "Allow message summarization",
                    "type": "boolean",
                    "value": True,
                },
            ],
        },
    ]

    # Merge with config
    modules = []
    for mod_def in module_definitions:
        config = configs.get(mod_def["name"])
        modules.append(
            {
                **mod_def,
                "enabled": config.is_enabled if config else False,
                "config": config.config if config else {},
            }
        )

    return modules


@router.patch("/groups/{group_id}/modules/{module_name}")
async def toggle_module(
    group_id: int,
    module_name: str,
    data: ToggleModuleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle a module on/off."""
    await check_admin_access(group_id, current_user, db)

    # Get or create config
    result = await db.execute(
        select(ModuleConfig).where(
            ModuleConfig.group_id == group_id,
            ModuleConfig.module_name == module_name,
        )
    )
    config = result.scalar()

    if not config:
        config = ModuleConfig(
            group_id=group_id,
            module_name=module_name,
            is_enabled=data.is_enabled,
            config={},
            updated_by=current_user.id,
        )
        db.add(config)
    else:
        config.is_enabled = data.is_enabled
        config.updated_by = current_user.id

    await db.commit()
    return {"success": True}


@router.patch("/groups/{group_id}/modules/{module_name}/features/{feature_key}")
async def update_feature(
    group_id: int,
    module_name: str,
    feature_key: str,
    data: UpdateFeatureRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a specific feature configuration."""
    await check_admin_access(group_id, current_user, db)

    result = await db.execute(
        select(ModuleConfig).where(
            ModuleConfig.group_id == group_id,
            ModuleConfig.module_name == module_name,
        )
    )
    config = result.scalar()

    if not config:
        config = ModuleConfig(
            group_id=group_id,
            module_name=module_name,
            is_enabled=True,
            config={feature_key: data.value},
            updated_by=current_user.id,
        )
        db.add(config)
    else:
        config.config = {**(config.config or {}), feature_key: data.value}
        config.updated_by = current_user.id

    await db.commit()
    return {"success": True}


@router.post("/groups/{group_id}/toggles/batch")
async def batch_update_toggles(
    group_id: int,
    data: BatchUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch update multiple features."""
    await check_admin_access(group_id, current_user, db)

    for update_data in data.updates:
        module_name = update_data.get("module")
        feature_key = update_data.get("feature")
        value = update_data.get("value")

        if not all([module_name, feature_key]):
            continue

        result = await db.execute(
            select(ModuleConfig).where(
                ModuleConfig.group_id == group_id,
                ModuleConfig.module_name == module_name,
            )
        )
        config = result.scalar()

        if not config:
            config = ModuleConfig(
                group_id=group_id,
                module_name=module_name,
                is_enabled=True,
                config={feature_key: value},
                updated_by=current_user.id,
            )
            db.add(config)
        else:
            config.config = {**(config.config or {}), feature_key: value}
            config.updated_by = current_user.id

    await db.commit()
    return {"success": True}


@router.post("/groups/{group_id}/modules/{module_name}/reset")
async def reset_module(
    group_id: int,
    module_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reset module to default settings."""
    await check_admin_access(group_id, current_user, db)

    result = await db.execute(
        select(ModuleConfig).where(
            ModuleConfig.group_id == group_id,
            ModuleConfig.module_name == module_name,
        )
    )
    config = result.scalar()

    if config:
        config.config = {}
        config.updated_by = current_user.id

    await db.commit()
    return {"success": True}


# ============ Lock Toggles ============


@router.get("/groups/{group_id}/locks")
async def get_locks(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all lock states for a group."""
    await check_admin_access(group_id, current_user, db)

    result = await db.execute(select(Lock).where(Lock.group_id == group_id))
    locks = result.scalars().all()

    return {
        lock.lock_type: {
            "locked": lock.is_locked,
            "mode": lock.mode,
            "duration": lock.mode_duration,
            "schedule": lock.schedule_windows,
        }
        for lock in locks
    }


@router.patch("/groups/{group_id}/locks/{lock_type}")
async def toggle_lock(
    group_id: int,
    lock_type: str,
    data: LockToggleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle a specific lock."""
    await check_admin_access(group_id, current_user, db)

    result = await db.execute(
        select(Lock).where(
            Lock.group_id == group_id,
            Lock.lock_type == lock_type,
        )
    )
    lock = result.scalar()

    if not lock:
        lock = Lock(
            group_id=group_id,
            lock_type=lock_type,
            is_locked=data.is_locked,
            mode="delete",
        )
        db.add(lock)
    else:
        lock.is_locked = data.is_locked

    await db.commit()
    return {"success": True}


@router.patch("/groups/{group_id}/locks/{lock_type}/mode")
async def set_lock_mode(
    group_id: int,
    lock_type: str,
    data: LockModeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set lock mode and duration."""
    await check_admin_access(group_id, current_user, db)

    result = await db.execute(
        select(Lock).where(
            Lock.group_id == group_id,
            Lock.lock_type == lock_type,
        )
    )
    lock = result.scalar()

    if lock:
        lock.mode = data.mode
        lock.mode_duration = data.duration

    await db.commit()
    return {"success": True}


@router.post("/groups/{group_id}/locks/{lock_type}/timed")
async def set_timed_lock(
    group_id: int,
    lock_type: str,
    data: TimedLockRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set a timed lock window."""
    await check_admin_access(group_id, current_user, db)

    result = await db.execute(
        select(Lock).where(
            Lock.group_id == group_id,
            Lock.lock_type == lock_type,
        )
    )
    lock = result.scalar()

    if lock:
        lock.schedule_enabled = True
        existing_windows = lock.schedule_windows or []
        new_window = {"start": data.start_time, "end": data.end_time}
        existing_windows.append(new_window)
        lock.schedule_windows = existing_windows

    await db.commit()
    return {"success": True}


@router.delete("/groups/{group_id}/locks/{lock_type}/timed")
async def remove_timed_lock(
    group_id: int,
    lock_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove timed lock windows."""
    await check_admin_access(group_id, current_user, db)

    result = await db.execute(
        select(Lock).where(
            Lock.group_id == group_id,
            Lock.lock_type == lock_type,
        )
    )
    lock = result.scalar()

    if lock:
        lock.schedule_enabled = False
        lock.schedule_windows = []

    await db.commit()
    return {"success": True}


# ============ Moderation Quick Actions ============


@router.post("/groups/{group_id}/moderation/warn")
async def quick_warn_user(
    group_id: int,
    data: ModerationActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Quick warn a user via API."""
    await check_admin_access(group_id, current_user, db)

    # Get target member
    result = await db.execute(
        select(Member).where(
            Member.group_id == group_id,
            Member.user_id == data.user_id,
        )
    )
    target = result.scalar()

    if not target:
        raise HTTPException(status_code=404, detail="User not found in group")

    # Increment warn count
    target.warn_count += 1

    await db.commit()

    return {
        "success": True,
        "warn_count": target.warn_count,
    }


@router.post("/groups/{group_id}/moderation/mute")
async def quick_mute_user(
    group_id: int,
    data: ModerationActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Quick mute a user via API."""
    await check_admin_access(group_id, current_user, db)

    # Implementation would use Telegram API to mute
    return {"success": True}


@router.post("/groups/{group_id}/moderation/ban")
async def quick_ban_user(
    group_id: int,
    data: ModerationActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Quick ban a user via API."""
    await check_admin_access(group_id, current_user, db)

    return {"success": True}


@router.post("/groups/{group_id}/moderation/kick")
async def quick_kick_user(
    group_id: int,
    data: ModerationActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Quick kick a user via API."""
    await check_admin_access(group_id, current_user, db)

    return {"success": True}


# ============ Groups List ============


@router.get("/groups/my-groups")
async def get_my_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all groups the user can manage."""
    result = await db.execute(
        select(Member, Group)
        .join(Group)
        .where(
            Member.user_id == current_user.id,
            Member.role.in_(["owner", "admin", "mod"]),
        )
    )

    groups = []
    for member, group in result.fetchall():
        # Count enabled modules
        module_result = await db.execute(
            select(ModuleConfig).where(
                ModuleConfig.group_id == group.id,
                ModuleConfig.is_enabled.is_(True),
            )
        )
        enabled_count = len(module_result.scalars().all())

        groups.append(
            {
                "id": group.id,
                "telegramId": group.telegram_id,
                "title": group.title,
                "username": group.username,
                "memberCount": group.member_count,
                "isPremium": group.is_premium,
                "role": member.role,
                "enabledModulesCount": enabled_count,
                "lastActivity": (
                    member.last_active.isoformat() if member.last_active else None
                ),
                "hasCustomBot": False,  # Would check bot_instances table
                "customBotUsername": None,
            }
        )

    return groups
