"""Groups router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from shared.database import get_db
from shared.models import Group, Member, ModuleConfig, User
from shared.schemas import (
    GroupCreate,
    GroupResponse,
    GroupStats,
    GroupUpdate,
    ModuleConfigResponse,
    ModuleConfigUpdate,
    PaginatedMembersResponse,
)

router = APIRouter()


@router.get("/groups", response_model=List[GroupResponse])
async def list_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List groups where user is a member."""
    result = await db.execute(
        select(Group)
        .join(Member, Member.group_id == Group.id)
        .where(Member.user_id == current_user.id)
        .order_by(Group.title)
    )
    groups = result.scalars().all()
    return groups


@router.get("/groups/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get group details."""
    result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = result.scalar()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check membership
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=403, detail="Not a member of this group")

    return group


@router.patch("/groups/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    update: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update group settings."""
    result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = result.scalar()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check admin permission
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    member = result.scalar()

    if not member or member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Update fields
    if update.title is not None:
        group.title = update.title
    if update.language is not None:
        group.language = update.language
    if update.timezone is not None:
        group.timezone = update.timezone
    if update.is_premium is not None:
        group.is_premium = update.is_premium

    await db.commit()
    await db.refresh(group)

    return group


@router.get("/groups/{group_id}/stats", response_model=GroupStats)
async def get_group_stats(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get group statistics."""
    result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = result.scalar()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check membership
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=403, detail="Not a member of this group")

    # Calculate stats
    total_members = await db.scalar(
        select(func.count()).where(Member.group_id == group_id)
    )

    from datetime import datetime, timedelta

    day_ago = datetime.utcnow() - timedelta(days=1)
    week_ago = datetime.utcnow() - timedelta(days=7)

    active_24h = await db.scalar(
        select(func.count()).where(
            Member.group_id == group_id,
            Member.last_active >= day_ago,
        )
    )

    active_7d = await db.scalar(
        select(func.count()).where(
            Member.group_id == group_id,
            Member.last_active >= week_ago,
        )
    )

    new_24h = await db.scalar(
        select(func.count()).where(
            Member.group_id == group_id,
            Member.joined_at >= day_ago,
        )
    )

    messages_24h = sum(m.message_count for m in await db.execute(
        select(Member).where(Member.group_id == group_id)
    ).scalars().all())

    # Top members
    top_members_result = await db.execute(
        select(Member, User)
        .join(User, Member.user_id == User.id)
        .where(Member.group_id == group_id)
        .order_by(Member.message_count.desc())
        .limit(10)
    )
    top_members = [
        {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "message_count": member.message_count,
            "xp": member.xp,
            "level": member.level,
        }
        for member, user in top_members_result.all()
    ]

    return GroupStats(
        total_members=total_members,
        active_members_24h=active_24h,
        active_members_7d=active_7d,
        new_members_24h=new_24h,
        messages_24h=messages_24h,
        top_members=top_members,
        mood_score=75.0,  # Placeholder for AI mood analysis
    )


@router.get("/groups/{group_id}/modules", response_model=List[ModuleConfigResponse])
async def list_group_modules(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List modules enabled for a group."""
    # Check admin permission
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    member = result.scalar()

    if not member or member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(
        select(ModuleConfig).where(ModuleConfig.group_id == group_id)
    )
    configs = result.scalars().all()
    return configs


@router.post("/groups/{group_id}/modules/{module_name}/enable")
async def enable_module(
    group_id: int,
    module_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enable a module for a group."""
    # Check admin permission
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    member = result.scalar()

    if not member or member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(
        select(ModuleConfig).where(
            ModuleConfig.group_id == group_id,
            ModuleConfig.module_name == module_name,
        )
    )
    config = result.scalar()

    if config:
        config.is_enabled = True
        config.updated_by = current_user.id
    else:
        config = ModuleConfig(
            group_id=group_id,
            module_name=module_name,
            is_enabled=True,
            updated_by=current_user.id,
        )
        db.add(config)

    await db.commit()
    return {"success": True}


@router.post("/groups/{group_id}/modules/{module_name}/disable")
async def disable_module(
    group_id: int,
    module_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disable a module for a group."""
    # Check admin permission
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    member = result.scalar()

    if not member or member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(
        select(ModuleConfig).where(
            ModuleConfig.group_id == group_id,
            ModuleConfig.module_name == module_name,
        )
    )
    config = result.scalar()

    if config:
        config.is_enabled = False
        config.updated_by = current_user.id
        await db.commit()

    return {"success": True}


@router.get("/groups/{group_id}/modules/{module_name}/config")
async def get_module_config(
    group_id: int,
    module_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get module configuration."""
    # Check admin permission
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    member = result.scalar()

    if not member or member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(
        select(ModuleConfig).where(
            ModuleConfig.group_id == group_id,
            ModuleConfig.module_name == module_name,
        )
    )
    config = result.scalar()

    if not config:
        return {"config": {}, "is_enabled": False}

    return {"config": config.config, "is_enabled": config.is_enabled}


@router.patch("/groups/{group_id}/modules/{module_name}/config")
async def update_module_config(
    group_id: int,
    module_name: str,
    update: ModuleConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update module configuration."""
    # Check admin permission
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    member = result.scalar()

    if not member or member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(
        select(ModuleConfig).where(
            ModuleConfig.group_id == group_id,
            ModuleConfig.module_name == module_name,
        )
    )
    config = result.scalar()

    if config:
        if update.config is not None:
            config.config = {**config.config, **update.config}
        if update.is_enabled is not None:
            config.is_enabled = update.is_enabled
        config.updated_by = current_user.id
    else:
        config = ModuleConfig(
            group_id=group_id,
            module_name=module_name,
            config=update.config or {},
            is_enabled=update.is_enabled if update.is_enabled is not None else False,
            updated_by=current_user.id,
        )
        db.add(config)

    await db.commit()
    return {"config": config.config, "is_enabled": config.is_enabled}
