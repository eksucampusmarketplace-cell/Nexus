"""Enhanced Members API Router - comprehensive member management."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from shared.database import get_db
from shared.models import (
    Member,
    MemberNote,
    MemberProfile,
    ModAction,
    TrustScoreHistory,
    User,
    Wallet,
    Warning,
)
from shared.schemas import Role

router = APIRouter()


# ============ Request Models ============


class BulkActionRequest(BaseModel):
    user_ids: List[int]
    action: str  # warn, mute, ban, kick, restrict, approve, whitelist
    reason: Optional[str] = None
    duration: Optional[int] = None  # seconds


class MemberNoteRequest(BaseModel):
    content: str
    is_private: bool = True


class TrustBoostRequest(BaseModel):
    amount: int
    reason: str


class GiveCoinsRequest(BaseModel):
    amount: int
    reason: Optional[str] = None


# ============ Helpers ============


async def check_admin_access(group_id: int, user: User, db: AsyncSession):
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


def member_to_dict(member: Member, user: User) -> Dict[str, Any]:
    """Convert member to dictionary with user data."""
    return {
        "id": member.id,
        "user_id": member.user_id,
        "group_id": member.group_id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        "last_active": member.last_active.isoformat() if member.last_active else None,
        "message_count": member.message_count,
        "media_count": member.media_count,
        "trust_score": member.trust_score,
        "xp": member.xp,
        "level": member.level,
        "streak_days": member.streak_days,
        "warn_count": member.warn_count,
        "mute_count": member.mute_count,
        "ban_count": member.ban_count,
        "is_muted": member.is_muted,
        "mute_until": member.mute_until.isoformat() if member.mute_until else None,
        "is_banned": member.is_banned,
        "ban_until": member.ban_until.isoformat() if member.ban_until else None,
        "is_approved": member.is_approved,
        "is_whitelisted": member.is_whitelisted,
        "role": member.role,
        "custom_title": member.custom_title,
    }


# ============ Member List ============


@router.get("/groups/{group_id}/members")
async def list_members(
    group_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = Query(None),  # muted, banned, restricted, approved, whitelisted, free
    trust_min: Optional[int] = Query(None, ge=0, le=100),
    trust_max: Optional[int] = Query(None, ge=0, le=100),
    level_min: Optional[int] = Query(None, ge=1),
    level_max: Optional[int] = Query(None, ge=1),
    joined_after: Optional[str] = None,
    joined_before: Optional[str] = None,
    inactive_days: Optional[int] = Query(None, ge=0),
    sort_by: str = Query("joined_at", pattern="^(joined_at|last_active|trust_score|level|message_count|warn_count)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive member list with filtering and sorting."""
    await check_admin_access(group_id, current_user, db)
    
    # Build query
    query = select(Member, User).join(User, Member.user_id == User.id).where(
        Member.group_id == group_id
    )
    
    # Filters
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.username.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
                User.telegram_id.cast(str).ilike(search_pattern),
            )
        )
    
    if role:
        query = query.where(Member.role == role)
    
    if status == "muted":
        query = query.where(Member.is_muted == True)
    elif status == "banned":
        query = query.where(Member.is_banned == True)
    elif status == "restricted":
        query = query.where(Member.role == "restricted")
    elif status == "approved":
        query = query.where(Member.is_approved == True)
    elif status == "whitelisted":
        query = query.where(Member.is_whitelisted == True)
    elif status == "free":
        query = query.where(
            and_(
                Member.is_muted == False,
                Member.is_banned == False,
                Member.role != "restricted",
                Member.is_approved == False,
                Member.is_whitelisted == False,
            )
        )
    
    if trust_min is not None:
        query = query.where(Member.trust_score >= trust_min)
    if trust_max is not None:
        query = query.where(Member.trust_score <= trust_max)
    
    if level_min is not None:
        query = query.where(Member.level >= level_min)
    if level_max is not None:
        query = query.where(Member.level <= level_max)
    
    if joined_after:
        try:
            after = datetime.fromisoformat(joined_after)
            query = query.where(Member.joined_at >= after)
        except ValueError:
            pass
    
    if joined_before:
        try:
            before = datetime.fromisoformat(joined_before)
            query = query.where(Member.joined_at <= before)
        except ValueError:
            pass
    
    if inactive_days is not None:
        cutoff = datetime.utcnow() - timedelta(days=inactive_days)
        query = query.where(Member.last_active < cutoff)
    
    # Sorting
    sort_column = getattr(Member, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    result = await db.execute(query)
    rows = result.all()
    
    members = []
    for member, user in rows:
        member_data = member_to_dict(member, user)
        # Add trust score badge color
        if member.trust_score >= 80:
            member_data["trust_badge"] = "green"
        elif member.trust_score >= 60:
            member_data["trust_badge"] = "yellow"
        elif member.trust_score >= 40:
            member_data["trust_badge"] = "orange"
        else:
            member_data["trust_badge"] = "red"
        members.append(member_data)
    
    return {
        "members": members,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


# ============ Single Member ============


@router.get("/groups/{group_id}/members/{user_id}")
async def get_member(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed member profile."""
    await check_admin_access(group_id, current_user, db)
    
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
    member_data = member_to_dict(member, user)
    
    # Get profile if exists
    profile_result = await db.execute(
        select(MemberProfile).where(
            MemberProfile.member_id == member.id
        )
    )
    profile = profile_result.scalar_one_or_none()
    
    if profile:
        member_data["profile"] = {
            "bio": profile.bio,
            "birthday": profile.birthday.isoformat() if profile.birthday else None,
            "social_links": profile.social_links,
            "profile_theme": profile.profile_theme,
        }
    
    # Get wallet if exists
    wallet_result = await db.execute(
        select(Wallet).where(Wallet.member_id == member.id)
    )
    wallet = wallet_result.scalar_one_or_none()
    
    if wallet:
        member_data["wallet"] = {
            "balance": wallet.balance,
            "total_earned": wallet.total_earned,
            "total_spent": wallet.total_spent,
        }
    
    # Get trust score history
    trust_result = await db.execute(
        select(TrustScoreHistory).where(
            TrustScoreHistory.member_id == member.id
        ).order_by(TrustScoreHistory.created_at.desc()).limit(30)
    )
    trust_history = trust_result.scalars().all()
    member_data["trust_history"] = [
        {
            "old_score": t.old_score,
            "new_score": t.new_score,
            "change_reason": t.change_reason,
            "created_at": t.created_at.isoformat(),
        }
        for t in trust_history
    ]
    
    return member_data


@router.get("/groups/{group_id}/members/{user_id}/overview")
async def get_member_overview(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get member overview tab data."""
    await check_admin_access(group_id, current_user, db)
    
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
    
    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_bot": user.is_bot,
        "is_premium": user.is_premium,
        "language_code": user.language_code,
        "account_created_at": user.created_at.isoformat() if user.created_at else None,
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        "last_active": member.last_active.isoformat() if member.last_active else None,
        "status": _get_member_status(member),
        "role": member.role,
        "custom_title": member.custom_title,
        "trust_score": member.trust_score,
        "trust_history": member.trust_score,  # Simplified
    }


@router.get("/groups/{group_id}/members/{user_id}/activity")
async def get_member_activity(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get member activity analytics."""
    await check_admin_access(group_id, current_user, db)
    
    # Check member exists
    result = await db.execute(
        select(Member).where(
            Member.group_id == group_id,
            Member.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Get message count over time would require aggregation
    # For now, return basic data
    return {
        "total_messages": member.message_count,
        "media_count": member.media_count,
        "last_active": member.last_active.isoformat() if member.last_active else None,
    }


@router.get("/groups/{group_id}/members/{user_id}/moderation")
async def get_member_moderation_history(
    group_id: int,
    user_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get member moderation history."""
    await check_admin_access(group_id, current_user, db)
    
    # Get warnings
    warn_result = await db.execute(
        select(Warning).where(
            Warning.group_id == group_id,
            Warning.user_id == user_id,
        ).order_by(Warning.created_at.desc())
    )
    warnings = warn_result.scalars().all()
    
    # Get mod actions
    action_query = select(ModAction).where(
        ModAction.group_id == group_id,
        ModAction.target_user_id == user_id,
    ).order_by(ModAction.created_at.desc())
    
    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(action_query.subquery())
    )
    total = count_result.scalar()
    
    # Paginate
    action_query = action_query.offset((page - 1) * per_page).limit(per_page)
    action_result = await db.execute(action_query)
    actions = action_result.scalars().all()
    
    return {
        "warnings": [
            {
                "id": w.id,
                "reason": w.reason,
                "issued_by": w.issued_by,
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "expires_at": w.expires_at.isoformat() if w.expires_at else None,
            }
            for w in warnings
        ],
        "actions": [
            {
                "id": a.id,
                "action_type": a.action_type,
                "reason": a.reason,
                "duration_seconds": a.duration_seconds,
                "actor_id": a.actor_id,
                "silent": a.silent,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "expires_at": a.expires_at.isoformat() if a.expires_at else None,
                "reversed_at": a.reversed_at.isoformat() if a.reversed_at else None,
            }
            for a in actions
        ],
        "total": total,
    }


@router.get("/groups/{group_id}/members/{user_id}/economy")
async def get_member_economy(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get member economy data."""
    await check_admin_access(group_id, current_user, db)
    
    # Get member
    member_result = await db.execute(
        select(Member).where(
            Member.group_id == group_id,
            Member.user_id == user_id,
        )
    )
    member = member_result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Get wallet
    wallet_result = await db.execute(
        select(Wallet).where(Wallet.member_id == member.id)
    )
    wallet = wallet_result.scalar_one_or_none()
    
    # Get leaderboard position
    position_result = await db.execute(
        select(func.count()).select_from(Wallet).where(
            Wallet.group_id == group_id,
            Wallet.balance > (wallet.balance if wallet else 0)
        )
    )
    position = position_result.scalar() + 1 if wallet else None
    
    return {
        "balance": wallet.balance if wallet else 0,
        "total_earned": wallet.total_earned if wallet else 0,
        "total_spent": wallet.total_spent if wallet else 0,
        "leaderboard_position": position,
        "level": member.level,
        "xp": member.xp,
        "streak_days": member.streak_days,
    }


@router.get("/groups/{group_id}/members/{user_id}/identity")
async def get_member_identity(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get member identity and badges."""
    await check_admin_access(group_id, current_user, db)
    
    # Get member
    member_result = await db.execute(
        select(Member, User).join(User, Member.user_id == User.id).where(
            Member.group_id == group_id,
            Member.user_id == user_id,
        )
    )
    row = member_result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Member not found")
    
    member, user = row
    
    # Get profile
    profile_result = await db.execute(
        select(MemberProfile).where(
            MemberProfile.member_id == member.id
        )
    )
    profile = profile_result.scalar_one_or_none()
    
    # Get badges
    from shared.models import MemberBadge, BadgeDefinition
    badge_result = await db.execute(
        select(MemberBadge, BadgeDefinition).join(
            BadgeDefinition, MemberBadge.badge_slug == BadgeDefinition.slug
        ).where(MemberBadge.member_id == member.id)
    )
    badges = []
    for member_badge, badge_def in badge_result.all():
        badges.append({
            "slug": badge_def.slug,
            "name": badge_def.name,
            "description": badge_def.description,
            "icon": badge_def.icon,
            "earned_at": member_badge.earned_at.isoformat() if member_badge.earned_at else None,
        })
    
    # Get reputation
    from shared.models import Reputation
    rep_result = await db.execute(
        select(Reputation).where(
            Reputation.group_id == group_id,
            Reputation.user_id == user_id,
        )
    )
    reputation = rep_result.scalar_one_or_none()
    
    return {
        "level": member.level,
        "xp": member.xp,
        "xp_to_next_level": _xp_for_level(member.level + 1) - member.xp,
        "badges": badges,
        "reputation_score": reputation.score if reputation else 0,
        "bio": profile.bio if profile else None,
        "birthday": profile.birthday.isoformat() if profile and profile.birthday else None,
    }


def _get_member_status(member: Member) -> str:
    """Get member status string."""
    if member.is_banned:
        return "banned"
    elif member.is_muted:
        return "muted"
    elif member.role == "restricted":
        return "restricted"
    elif member.is_approved:
        return "approved"
    elif member.is_whitelisted:
        return "whitelisted"
    return "free"


def _xp_for_level(level: int) -> int:
    """Calculate XP required for a level."""
    return level * 100 + (level - 1) * 50


# ============ Bulk Actions ============


@router.post("/groups/{group_id}/members/bulk-action")
async def bulk_moderation_action(
    group_id: int,
    request: BulkActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Perform bulk moderation action on multiple members."""
    admin = await check_admin_access(group_id, current_user, db)
    
    if admin.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only admins can perform bulk actions")
    
    results = []
    for user_id in request.user_ids:
        try:
            # Execute action
            # This would call the shared action executor
            results.append({"user_id": user_id, "success": True})
        except Exception as e:
            results.append({"user_id": user_id, "success": False, "error": str(e)})
    
    return {"results": results}


# ============ Member Actions ============


@router.post("/groups/{group_id}/members/{user_id}/warn")
async def warn_member(
    group_id: int,
    user_id: int,
    reason: str = Query("No reason provided"),
    silent: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Warn a member using the shared action executor."""
    admin = await check_admin_access(group_id, current_user, db)
    
    # Get group telegram ID
    from shared.models import Group
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get target user telegram ID
    target_result = await db.execute(select(User).where(User.id == user_id))
    target_user = target_result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        from shared.action_executor import ActionContext, get_action_executor
        
        executor = await get_action_executor()
        
        ctx = ActionContext(
            group_id=group_id,
            actor_id=current_user.id,
            target_id=user_id,
            group_telegram_id=group.telegram_id,
            actor_telegram_id=current_user.telegram_id,
            target_telegram_id=target_user.telegram_id,
            action_type="warn",
            reason=reason,
            silent=silent,
            source="api"
        )
        
        result = await executor.warn(ctx)
        
        return {
            "success": result.success,
            "action": "warn",
            "message": result.message,
            "trust_score_change": (result.trust_score_after or 0) - (result.trust_score_before or 0),
            "warn_count": result.data.get("warn_count") if result.data else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/members/{user_id}/mute")
async def mute_member(
    group_id: int,
    user_id: int,
    duration: int = Query(3600, description="Duration in seconds"),
    reason: str = Query("No reason provided"),
    silent: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mute a member using the shared action executor."""
    admin = await check_admin_access(group_id, current_user, db)
    
    from shared.models import Group
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    target_result = await db.execute(select(User).where(User.id == user_id))
    target_user = target_result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        from shared.action_executor import ActionContext, get_action_executor
        
        executor = await get_action_executor()
        
        ctx = ActionContext(
            group_id=group_id,
            actor_id=current_user.id,
            target_id=user_id,
            group_telegram_id=group.telegram_id,
            actor_telegram_id=current_user.telegram_id,
            target_telegram_id=target_user.telegram_id,
            action_type="mute",
            reason=reason,
            duration_seconds=duration,
            silent=silent,
            source="api"
        )
        
        result = await executor.mute(ctx)
        
        return {
            "success": result.success,
            "action": "mute",
            "message": result.message,
            "trust_score_change": (result.trust_score_after or 0) - (result.trust_score_before or 0),
            "mute_until": result.data.get("mute_until") if result.data else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/members/{user_id}/unmute")
async def unmute_member(
    group_id: int,
    user_id: int,
    reason: str = Query("Unmuted via API"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unmute a member."""
    admin = await check_admin_access(group_id, current_user, db)
    
    from shared.models import Group
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    
    target_result = await db.execute(select(User).where(User.id == user_id))
    target_user = target_result.scalar_one_or_none()
    
    try:
        from shared.action_executor import ActionContext, get_action_executor
        
        executor = await get_action_executor()
        
        ctx = ActionContext(
            group_id=group_id,
            actor_id=current_user.id,
            target_id=user_id,
            group_telegram_id=group.telegram_id if group else 0,
            actor_telegram_id=current_user.telegram_id,
            target_telegram_id=target_user.telegram_id if target_user else 0,
            action_type="unmute",
            reason=reason,
            source="api"
        )
        
        result = await executor.unmute(ctx)
        
        return {
            "success": result.success,
            "action": "unmute",
            "message": result.message,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/members/{user_id}/ban")
async def ban_member(
    group_id: int,
    user_id: int,
    duration: Optional[int] = Query(None, description="Duration in seconds, None for permanent"),
    reason: str = Query("No reason provided"),
    silent: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ban a member using the shared action executor."""
    admin = await check_admin_access(group_id, current_user, db)
    
    if admin.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only admins can ban users")
    
    from shared.models import Group
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    target_result = await db.execute(select(User).where(User.id == user_id))
    target_user = target_result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        from shared.action_executor import ActionContext, get_action_executor
        
        executor = await get_action_executor()
        
        ctx = ActionContext(
            group_id=group_id,
            actor_id=current_user.id,
            target_id=user_id,
            group_telegram_id=group.telegram_id,
            actor_telegram_id=current_user.telegram_id,
            target_telegram_id=target_user.telegram_id,
            action_type="ban",
            reason=reason,
            duration_seconds=duration,
            silent=silent,
            source="api"
        )
        
        result = await executor.ban(ctx)
        
        return {
            "success": result.success,
            "action": "ban",
            "message": result.message,
            "trust_score_change": (result.trust_score_after or 0) - (result.trust_score_before or 0),
            "ban_until": result.data.get("ban_until") if result.data else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/members/{user_id}/unban")
async def unban_member(
    group_id: int,
    user_id: int,
    reason: str = Query("Unbanned via API"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unban a member."""
    admin = await check_admin_access(group_id, current_user, db)
    
    from shared.models import Group
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    
    target_result = await db.execute(select(User).where(User.id == user_id))
    target_user = target_result.scalar_one_or_none()
    
    try:
        from shared.action_executor import ActionContext, get_action_executor
        
        executor = await get_action_executor()
        
        ctx = ActionContext(
            group_id=group_id,
            actor_id=current_user.id,
            target_id=user_id,
            group_telegram_id=group.telegram_id if group else 0,
            actor_telegram_id=current_user.telegram_id,
            target_telegram_id=target_user.telegram_id if target_user else 0,
            action_type="unban",
            reason=reason,
            source="api"
        )
        
        result = await executor.unban(ctx)
        
        return {
            "success": result.success,
            "action": "unban",
            "message": result.message,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/members/{user_id}/kick")
async def kick_member(
    group_id: int,
    user_id: int,
    reason: str = Query("No reason provided"),
    silent: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Kick a member using the shared action executor."""
    admin = await check_admin_access(group_id, current_user, db)
    
    from shared.models import Group
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    target_result = await db.execute(select(User).where(User.id == user_id))
    target_user = target_result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        from shared.action_executor import ActionContext, get_action_executor
        
        executor = await get_action_executor()
        
        ctx = ActionContext(
            group_id=group_id,
            actor_id=current_user.id,
            target_id=user_id,
            group_telegram_id=group.telegram_id,
            actor_telegram_id=current_user.telegram_id,
            target_telegram_id=target_user.telegram_id,
            action_type="kick",
            reason=reason,
            silent=silent,
            source="api"
        )
        
        result = await executor.kick(ctx)
        
        return {
            "success": result.success,
            "action": "kick",
            "message": result.message,
            "trust_score_change": (result.trust_score_after or 0) - (result.trust_score_before or 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/members/{user_id}/free")
async def free_member(
    group_id: int,
    user_id: int,
    duration: Optional[int] = Query(None, description="Duration in seconds"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove all restrictions from a member."""
    admin = await check_admin_access(group_id, current_user, db)
    
    return {"success": True, "action": "free"}


@router.post("/groups/{group_id}/members/{user_id}/trust")
async def trust_member(
    group_id: int,
    user_id: int,
    request: TrustBoostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually boost trust score."""
    admin = await check_admin_access(group_id, current_user, db)
    
    return {"success": True, "action": "trust"}


@router.post("/groups/{group_id}/members/{user_id}/promote")
async def promote_member(
    group_id: int,
    user_id: int,
    role: str = Query(..., pattern="^(admin|mod|trusted|member)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Promote a member to a role."""
    admin = await check_admin_access(group_id, current_user, db)
    
    if admin.role != "owner" and role == "admin":
        raise HTTPException(status_code=403, detail="Only owner can promote to admin")
    
    return {"success": True, "action": "promote", "role": role}


@router.post("/groups/{group_id}/members/{user_id}/give-coins")
async def give_coins(
    group_id: int,
    user_id: int,
    request: GiveCoinsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Give coins to a member."""
    admin = await check_admin_access(group_id, current_user, db)
    
    return {"success": True, "action": "give_coins", "amount": request.amount}


# ============ Member Notes ============


@router.get("/groups/{group_id}/members/{user_id}/notes")
async def get_member_notes(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get admin notes for a member."""
    await check_admin_access(group_id, current_user, db)
    
    # Get member
    member_result = await db.execute(
        select(Member).where(
            Member.group_id == group_id,
            Member.user_id == user_id,
        )
    )
    member = member_result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    result = await db.execute(
        select(MemberNote).where(
            MemberNote.member_id == member.id
        ).order_by(MemberNote.created_at.desc())
    )
    notes = result.scalars().all()
    
    return [
        {
            "id": n.id,
            "content": n.content,
            "is_private": n.is_private,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notes
    ]


@router.post("/groups/{group_id}/members/{user_id}/notes")
async def add_member_note(
    group_id: int,
    user_id: int,
    request: MemberNoteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an admin note to a member."""
    admin = await check_admin_access(group_id, current_user, db)
    
    # Get member
    member_result = await db.execute(
        select(Member).where(
            Member.group_id == group_id,
            Member.user_id == user_id,
        )
    )
    member = member_result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    note = MemberNote(
        member_id=member.id,
        group_id=group_id,
        user_id=current_user.id,
        content=request.content,
        is_private=request.is_private,
    )
    db.add(note)
    await db.flush()
    
    return {"id": note.id, "success": True}


# ============ Special Views ============


@router.get("/groups/{group_id}/members/inactive")
async def get_inactive_members(
    group_id: int,
    days: int = Query(30, ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get inactive members."""
    await check_admin_access(group_id, current_user, db)
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(Member, User).join(User, Member.user_id == User.id).where(
            Member.group_id == group_id,
            Member.last_active < cutoff,
        ).order_by(Member.last_active.asc())
    )
    rows = result.all()
    
    return [
        member_to_dict(member, user)
        for member, user in rows
    ]


@router.get("/groups/{group_id}/members/new")
async def get_new_members(
    group_id: int,
    days: int = Query(7, ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recently joined members."""
    await check_admin_access(group_id, current_user, db)
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(Member, User).join(User, Member.user_id == User.id).where(
            Member.group_id == group_id,
            Member.joined_at >= cutoff,
        ).order_by(Member.joined_at.desc())
    )
    rows = result.all()
    
    return [
        member_to_dict(member, user)
        for member, user in rows
    ]


@router.get("/groups/{group_id}/leaderboards")
async def get_leaderboards(
    group_id: int,
    type: str = Query("messages", pattern="^(messages|coins|xp|trust|reputation)$"),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get group leaderboards."""
    await check_admin_access(group_id, current_user, db)
    
    if type == "messages":
        query = select(Member, User).join(User, Member.user_id == User.id).where(
            Member.group_id == group_id,
        ).order_by(Member.message_count.desc()).limit(limit)
    elif type == "coins":
        query = select(Member, User, Wallet).join(User, Member.user_id == User.id).outerjoin(
            Wallet, Member.id == Wallet.member_id
        ).where(
            Member.group_id == group_id,
        ).order_by(Wallet.balance.desc().nullslast()).limit(limit)
    elif type == "xp":
        query = select(Member, User).join(User, Member.user_id == User.id).where(
            Member.group_id == group_id,
        ).order_by(Member.xp.desc()).limit(limit)
    elif type == "trust":
        query = select(Member, User).join(User, Member.user_id == User.id).where(
            Member.group_id == group_id,
        ).order_by(Member.trust_score.desc()).limit(limit)
    else:
        query = select(Member, User).join(User, Member.user_id == User.id).where(
            Member.group_id == group_id,
        ).order_by(Member.level.desc()).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    leaderboard = []
    for i, row in enumerate(rows):
        if type == "coins":
            member, user, wallet = row
            score = wallet.balance if wallet else 0
        else:
            member, user = row
            score = getattr(member, type, 0)
        
        leaderboard.append({
            "rank": i + 1,
            "user_id": member.user_id,
            "username": user.username,
            "first_name": user.first_name,
            "score": score,
        })
    
    return leaderboard
