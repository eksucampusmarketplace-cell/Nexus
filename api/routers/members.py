"""Members router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from shared.database import get_db
from shared.models import Member, ModAction, User, Warning
from shared.schemas import (
    BanRequest,
    MemberHistoryResponse,
    MemberResponse,
    MemberUpdate,
    ModerationActionResponse,
    MuteRequest,
    MuteRequest as MuteRequestSchema,
    PaginatedActionsResponse,
    WarnRequest,
    WarningResponse,
)


async def _publish_mod_event(group_id: int, action: str, target_user_id: int, actor_id: int, reason: Optional[str] = None):
    """Publish a moderation action event to the live feed."""
    try:
        import json
        from shared.redis_client import get_redis
        redis = await get_redis()
        channel = f"nexus:g{group_id}:feed"
        event = {
            "type": "mod_action",
            "action": action,
            "target_user_id": target_user_id,
            "actor_id": actor_id,
            "reason": reason,
        }
        await redis.publish(channel, json.dumps(event))
    except Exception:
        pass

router = APIRouter()


@router.get("/groups/{group_id}/members", response_model=List[MemberResponse])
async def list_members(
    group_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List members of a group."""
    # Check membership
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=403, detail="Not a member of this group")

    query = select(Member, User).join(User, Member.user_id == User.id).where(
        Member.group_id == group_id
    )

    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) |
            (User.first_name.ilike(f"%{search}%")) |
            (User.last_name.ilike(f"%{search}%"))
        )

    if role:
        query = query.where(Member.role == role)

    query = query.order_by(Member.joined_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    members = []
    for member, user in result.all():
        member.user = user
        members.append(member)

    return members


@router.get("/groups/{group_id}/members/{user_id}", response_model=MemberResponse)
async def get_member(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific member."""
    result = await db.execute(
        select(Member, User).join(User, Member.user_id == User.id).where(
            Member.group_id == group_id,
            Member.user_id == user_id,
        )
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Member not found")

    member, user = row
    member.user = user
    return member


@router.get("/groups/{group_id}/members/{user_id}/history")
async def get_member_history(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get member moderation history."""
    # Check moderator permission
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    member = result.scalar()

    if not member or member.role not in ("owner", "admin", "mod"):
        raise HTTPException(status_code=403, detail="Moderator access required")

    # Get warnings
    result = await db.execute(
        select(Warning, User).join(User, Warning.issued_by == User.id).where(
            Warning.group_id == group_id,
            Warning.user_id == user_id,
            Warning.deleted_at.is_(None),
        ).order_by(Warning.created_at.desc())
    )
    warnings = [
        {
            "id": w.id,
            "reason": w.reason,
            "issued_by": {
                "id": u.id,
                "username": u.username,
                "first_name": u.first_name,
            },
            "created_at": w.created_at,
            "expires_at": w.expires_at,
        }
        for w, u in result.all()
    ]

    # Get moderation actions
    result = await db.execute(
        select(ModAction, User).join(User, ModAction.actor_id == User.id).where(
            ModAction.group_id == group_id,
            ModAction.target_user_id == user_id,
        ).order_by(ModAction.created_at.desc())
    )
    actions = [
        {
            "id": a.id,
            "action_type": a.action_type,
            "reason": a.reason,
            "actor": {
                "id": u.id,
                "username": u.username,
                "first_name": u.first_name,
            },
            "created_at": a.created_at,
        }
        for a, u in result.all()
    ]

    return {
        "warnings": warnings,
        "actions": actions,
        "total_warnings": len(warnings),
        "total_actions": len(actions),
    }


@router.post("/groups/{group_id}/members/{user_id}/warn")
async def warn_member(
    group_id: int,
    user_id: int,
    request: WarnRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Warn a member."""
    # Check moderator permission
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    actor = result.scalar()

    if not actor or actor.role not in ("owner", "admin", "mod"):
        raise HTTPException(status_code=403, detail="Moderator access required")

    # Get target member
    result = await db.execute(
        select(Member).where(
            Member.user_id == user_id,
            Member.group_id == group_id,
        )
    )
    target = result.scalar()

    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    # Create warning
    warning = Warning(
        group_id=group_id,
        user_id=user_id,
        issued_by=current_user.id,
        reason=request.reason or "No reason provided",
    )
    db.add(warning)

    # Update warn count
    target.warn_count += 1

    # Log action
    action = ModAction(
        group_id=group_id,
        target_user_id=user_id,
        actor_id=current_user.id,
        action_type="warn",
        reason=request.reason,
        silent=request.silent,
    )
    db.add(action)

    await db.commit()

    await _publish_mod_event(group_id, "warn", user_id, current_user.id, request.reason)

    return {
        "success": True,
        "warn_count": target.warn_count,
        "message": f"User has been warned. Total warnings: {target.warn_count}",
    }


@router.post("/groups/{group_id}/members/{user_id}/mute")
async def mute_member(
    group_id: int,
    user_id: int,
    request: MuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mute a member."""
    # Check moderator permission
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    actor = result.scalar()

    if not actor or actor.role not in ("owner", "admin", "mod"):
        raise HTTPException(status_code=403, detail="Moderator access required")

    # Get target member
    result = await db.execute(
        select(Member).where(
            Member.user_id == user_id,
            Member.group_id == group_id,
        )
    )
    target = result.scalar()

    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    # Parse duration
    duration_seconds = None
    if request.duration:
        duration_seconds = parse_duration(request.duration)
        if duration_seconds is None:
            raise HTTPException(status_code=400, detail="Invalid duration format")

    # Update member
    target.is_muted = True
    if duration_seconds:
        from datetime import datetime, timedelta
        target.mute_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
    target.mute_count += 1

    # Log action
    action = ModAction(
        group_id=group_id,
        target_user_id=user_id,
        actor_id=current_user.id,
        action_type="mute",
        reason=request.reason,
        duration_seconds=duration_seconds,
        silent=request.silent,
    )
    db.add(action)

    await db.commit()

    await _publish_mod_event(group_id, "mute", user_id, current_user.id, request.reason)

    return {
        "success": True,
        "duration": request.duration,
        "message": f"User has been muted" + (f" for {request.duration}" if request.duration else " permanently"),
    }


@router.post("/groups/{group_id}/members/{user_id}/unmute")
async def unmute_member(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unmute a member."""
    # Check moderator permission
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    actor = result.scalar()

    if not actor or actor.role not in ("owner", "admin", "mod"):
        raise HTTPException(status_code=403, detail="Moderator access required")

    # Get target member
    result = await db.execute(
        select(Member).where(
            Member.user_id == user_id,
            Member.group_id == group_id,
        )
    )
    target = result.scalar()

    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    target.is_muted = False
    target.mute_until = None

    # Log action
    action = ModAction(
        group_id=group_id,
        target_user_id=user_id,
        actor_id=current_user.id,
        action_type="unmute",
    )
    db.add(action)

    await db.commit()

    await _publish_mod_event(group_id, "unmute", user_id, current_user.id)

    return {"success": True, "message": "User has been unmuted"}


@router.post("/groups/{group_id}/members/{user_id}/ban")
async def ban_member(
    group_id: int,
    user_id: int,
    request: BanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ban a member."""
    # Check moderator permission
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    actor = result.scalar()

    if not actor or actor.role not in ("owner", "admin", "mod"):
        raise HTTPException(status_code=403, detail="Moderator access required")

    # Get target member
    result = await db.execute(
        select(Member).where(
            Member.user_id == user_id,
            Member.group_id == group_id,
        )
    )
    target = result.scalar()

    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    # Parse duration
    duration_seconds = None
    if request.duration:
        duration_seconds = parse_duration(request.duration)
        if duration_seconds is None:
            raise HTTPException(status_code=400, detail="Invalid duration format")

    # Update member
    target.is_banned = True
    if duration_seconds:
        from datetime import datetime, timedelta
        target.ban_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
    target.ban_count += 1

    # Log action
    action = ModAction(
        group_id=group_id,
        target_user_id=user_id,
        actor_id=current_user.id,
        action_type="ban",
        reason=request.reason,
        duration_seconds=duration_seconds,
        silent=request.silent,
    )
    db.add(action)

    await db.commit()

    await _publish_mod_event(group_id, "ban", user_id, current_user.id, request.reason)

    return {
        "success": True,
        "duration": request.duration,
        "message": f"User has been banned" + (f" for {request.duration}" if request.duration else " permanently"),
    }


@router.post("/groups/{group_id}/members/{user_id}/unban")
async def unban_member(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unban a member."""
    # Check moderator permission
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    actor = result.scalar()

    if not actor or actor.role not in ("owner", "admin", "mod"):
        raise HTTPException(status_code=403, detail="Moderator access required")

    # Get target member
    result = await db.execute(
        select(Member).where(
            Member.user_id == user_id,
            Member.group_id == group_id,
        )
    )
    target = result.scalar()

    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    target.is_banned = False
    target.ban_until = None

    # Log action
    action = ModAction(
        group_id=group_id,
        target_user_id=user_id,
        actor_id=current_user.id,
        action_type="unban",
    )
    db.add(action)

    await db.commit()

    return {"success": True, "message": "User has been unbanned"}


@router.post("/groups/{group_id}/members/{user_id}/kick")
async def kick_member(
    group_id: int,
    user_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Kick a member."""
    # Check moderator permission
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    actor = result.scalar()

    if not actor or actor.role not in ("owner", "admin", "mod"):
        raise HTTPException(status_code=403, detail="Moderator access required")

    # Get target member
    result = await db.execute(
        select(Member).where(
            Member.user_id == user_id,
            Member.group_id == group_id,
        )
    )
    target = result.scalar()

    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    # Log action
    action = ModAction(
        group_id=group_id,
        target_user_id=user_id,
        actor_id=current_user.id,
        action_type="kick",
        reason=reason,
    )
    db.add(action)

    # Delete member
    await db.delete(target)
    await db.commit()

    return {"success": True, "message": "User has been kicked"}


def parse_duration(duration_str: str) -> Optional[int]:
    """Parse duration string to seconds."""
    if not duration_str:
        return None

    duration_str = duration_str.lower().strip()
    multipliers = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
        "w": 604800,
    }

    for suffix, multiplier in multipliers.items():
        if duration_str.endswith(suffix):
            try:
                return int(duration_str[:-1]) * multiplier
            except ValueError:
                return None

    try:
        return int(duration_str)
    except ValueError:
        return None
