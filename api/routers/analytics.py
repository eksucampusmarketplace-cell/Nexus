"""Analytics router."""

from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from shared.database import get_db
from shared.models import Group, Member, ModAction, User
from shared.schemas import (
    ActivityHeatmapResponse,
    AnalyticsOverviewResponse,
    MemberGrowthResponse,
)

router = APIRouter()


@router.get("/groups/{group_id}/analytics/overview")
async def get_analytics_overview(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics overview for a group."""
    # Check membership
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=403, detail="Not a member of this group")

    day_ago = datetime.utcnow() - timedelta(days=1)
    week_ago = datetime.utcnow() - timedelta(days=7)

    total_messages_24h = 0  # Would need message tracking table
    total_messages_7d = 0

    active_members_24h = await db.scalar(
        select(func.count()).where(
            Member.group_id == group_id,
            Member.last_active >= day_ago,
        )
    )

    active_members_7d = await db.scalar(
        select(func.count()).where(
            Member.group_id == group_id,
            Member.last_active >= week_ago,
        )
    )

    new_members_7d = await db.scalar(
        select(func.count()).where(
            Member.group_id == group_id,
            Member.joined_at >= week_ago,
        )
    )

    left_members_7d = 0  # Would need tracking for left members

    mod_actions_24h = await db.scalar(
        select(func.count()).where(
            ModAction.group_id == group_id,
            ModAction.created_at >= day_ago,
        )
    )

    mod_actions_7d = await db.scalar(
        select(func.count()).where(
            ModAction.group_id == group_id,
            ModAction.created_at >= week_ago,
        )
    )

    return AnalyticsOverviewResponse(
        total_messages_24h=total_messages_24h,
        total_messages_7d=total_messages_7d,
        active_members_24h=active_members_24h,
        active_members_7d=active_members_7d,
        new_members_7d=new_members_7d,
        left_members_7d=left_members_7d,
        mod_actions_24h=mod_actions_24h,
        mod_actions_7d=mod_actions_7d,
    )


@router.get("/groups/{group_id}/analytics/heatmap")
async def get_activity_heatmap(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get activity heatmap for a group."""
    # Check membership
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=403, detail="Not a member of this group")

    hours = [f"{h:02d}:00" for h in range(24)]
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    data = [[0 for _ in range(24)] for _ in range(7)]

    # Placeholder - would need detailed activity tracking

    return ActivityHeatmapResponse(hours=hours, days=days, data=data)


@router.get("/groups/{group_id}/analytics/growth")
async def get_member_growth(
    group_id: int,
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get member growth data."""
    # Check membership
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=403, detail="Not a member of this group")

    dates = []
    member_count = []
    new_members = []
    left_members = []

    # Placeholder data
    for i in range(days):
        d = datetime.utcnow() - timedelta(days=days - i - 1)
        dates.append(d.strftime("%Y-%m-%d"))
        member_count.append(0)
        new_members.append(0)
        left_members.append(0)

    return MemberGrowthResponse(
        dates=dates,
        member_count=member_count,
        new_members=new_members,
        left_members=left_members,
    )
