"""Admin router for owner-only system functions."""

import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import (
    get_current_user,
    is_owner,
    OWNER_IDS,
    SUPPORT_IDS,
)
from shared.database import get_db
from shared.models import Group, Member, User, BotInstance

router = APIRouter()


async def require_owner(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to require owner permissions."""
    if not is_owner(current_user.telegram_id):
        raise HTTPException(status_code=403, detail="Owner access required")
    return current_user


async def require_staff(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to require owner or support permissions."""
    from api.routers.auth import is_staff
    if not is_staff(current_user.telegram_id):
        raise HTTPException(status_code=403, detail="Staff access required")
    return current_user


@router.get("/admin/stats")
async def get_system_stats(
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get system-wide statistics (owner only)."""
    # Total users
    total_users = await db.scalar(select(func.count()).select_from(User))
    
    # Total groups
    total_groups = await db.scalar(select(func.count()).select_from(Group))
    
    # Active groups (with activity in last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_groups = await db.scalar(
        select(func.count())
        .select_from(Group)
        .where(Group.updated_at >= week_ago)
    )
    
    # Total members across all groups
    total_members = await db.scalar(select(func.count()).select_from(Member))
    
    # Custom bot instances
    custom_bots = await db.scalar(
        select(func.count())
        .select_from(BotInstance)
        .where(BotInstance.is_active == True)
    )
    
    # Recent signups (last 24 hours)
    day_ago = datetime.utcnow() - timedelta(days=1)
    recent_users = await db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.created_at >= day_ago)
    )
    
    return {
        "total_users": total_users,
        "total_groups": total_groups,
        "active_groups": active_groups,
        "total_members": total_members,
        "custom_bots": custom_bots,
        "recent_users_24h": recent_users,
        "owner_count": len(OWNER_IDS),
        "support_count": len(SUPPORT_IDS),
    }


@router.get("/admin/users")
async def list_users(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """List users with pagination (staff only)."""
    result = await db.execute(
        select(User)
        .order_by(User.last_seen.desc())
        .limit(limit)
        .offset(offset)
    )
    users = result.scalars().all()
    
    return [
        {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code,
            "is_premium": user.is_premium,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_seen": user.last_seen.isoformat() if user.last_seen else None,
            "is_owner": user.telegram_id in OWNER_IDS,
            "is_support": user.telegram_id in SUPPORT_IDS,
        }
        for user in users
    ]


@router.get("/admin/groups")
async def list_all_groups(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """List all groups with pagination (staff only)."""
    result = await db.execute(
        select(Group)
        .order_by(Group.member_count.desc())
        .limit(limit)
        .offset(offset)
    )
    groups = result.scalars().all()
    
    return [
        {
            "id": group.id,
            "telegram_id": group.telegram_id,
            "title": group.title,
            "username": group.username,
            "member_count": group.member_count,
            "language": group.language,
            "is_premium": group.is_premium,
            "timezone": group.timezone,
            "created_at": group.created_at.isoformat() if group.created_at else None,
            "updated_at": group.updated_at.isoformat() if group.updated_at else None,
            "has_custom_bot": group.bot_instance is not None,
        }
        for group in groups
    ]


@router.get("/admin/config")
async def get_system_config(
    current_user: User = Depends(require_owner),
):
    """Get system configuration (owner only) - safe values only."""
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "owner_count": len(OWNER_IDS),
        "support_count": len(SUPPORT_IDS),
        "features": {
            "ai_enabled": bool(os.getenv("OPENAI_API_KEY")),
            "custom_bots_enabled": True,
            "webhooks_enabled": bool(os.getenv("WEBHOOK_URL")),
        }
    }


@router.post("/admin/users/{user_id}/toggle-support")
async def toggle_support_status(
    user_id: int,
    is_support: bool,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """Toggle support status for a user (owner only).
    
    Note: This updates the runtime SUPPORT_IDS set. For persistence,
    update the SUPPORT_IDS environment variable.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if is_support:
        SUPPORT_IDS.add(user.telegram_id)
    else:
        SUPPORT_IDS.discard(user.telegram_id)
    
    return {
        "success": True,
        "user_id": user_id,
        "telegram_id": user.telegram_id,
        "is_support": is_support,
        "note": "Update SUPPORT_IDS env var for persistence across restarts"
    }
