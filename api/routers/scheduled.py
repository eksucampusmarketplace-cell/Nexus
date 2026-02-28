"""Scheduled messages router."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from shared.database import get_db
from shared.models import Group, Member, ScheduledMessage
from shared.schemas import ScheduledMessageCreate, ScheduledMessageResponse

router = APIRouter()


@router.get("/groups/{group_id}/scheduled")
async def list_scheduled_messages(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List scheduled messages for a group."""
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
        select(ScheduledMessage).where(
            ScheduledMessage.group_id == group_id,
        ).order_by(ScheduledMessage.next_run)
    )

    return result.scalars().all()


@router.post("/groups/{group_id}/scheduled")
async def create_scheduled_message(
    group_id: int,
    request: ScheduledMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a scheduled message."""
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

    scheduled = ScheduledMessage(
        group_id=group_id,
        content=request.content,
        media_file_id=request.media_file_id,
        media_type=request.media_type,
        has_buttons=request.has_buttons,
        button_data=request.button_data,
        schedule_type=request.schedule_type,
        run_at=request.run_at,
        cron_expression=request.cron_expression,
        days_of_week=request.days_of_week,
        time_slot=request.time_slot,
        end_date=request.end_date,
        max_runs=request.max_runs,
        self_destruct_after=request.self_destruct_after,
        created_by=current_user.id,
    )
    db.add(scheduled)
    await db.commit()

    return scheduled


@router.delete("/groups/{group_id}/scheduled/{message_id}")
async def delete_scheduled_message(
    group_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a scheduled message."""
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
        select(ScheduledMessage).where(
            ScheduledMessage.id == message_id,
            ScheduledMessage.group_id == group_id,
        )
    )
    scheduled = result.scalar()

    if not scheduled:
        raise HTTPException(status_code=404, detail="Scheduled message not found")

    await db.delete(scheduled)
    await db.commit()

    return {"success": True}


@router.post("/groups/{group_id}/scheduled/{message_id}/toggle")
async def toggle_scheduled_message(
    group_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle a scheduled message on/off."""
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
        select(ScheduledMessage).where(
            ScheduledMessage.id == message_id,
            ScheduledMessage.group_id == group_id,
        )
    )
    scheduled = result.scalar()

    if not scheduled:
        raise HTTPException(status_code=404, detail="Scheduled message not found")

    scheduled.is_enabled = not scheduled.is_enabled
    await db.commit()

    return {"success": True, "is_enabled": scheduled.is_enabled}
