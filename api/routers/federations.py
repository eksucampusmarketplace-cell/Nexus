"""Federations router."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from shared.database import get_db
from shared.models import (
    Federation,
    FederationAdmin,
    FederationBan,
    FederationMember,
    Group,
    Member,
    User,
)
from shared.schemas import (
    FederationCreate,
    FederationResponse,
    FederationUpdate,
)

router = APIRouter()


@router.get("/federations", response_model=List[FederationResponse])
async def list_federations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List federations owned by current user."""
    result = await db.execute(
        select(Federation).where(Federation.owner_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/federations", response_model=FederationResponse)
async def create_federation(
    request: FederationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new federation."""
    federation = Federation(
        name=request.name,
        description=request.description,
        owner_id=current_user.id,
        is_public=request.is_public,
    )
    db.add(federation)
    await db.flush()

    # Add owner as admin
    admin = FederationAdmin(
        federation_id=federation.id,
        user_id=current_user.id,
        added_by=current_user.id,
    )
    db.add(admin)
    await db.commit()

    return federation


@router.get("/federations/{fed_id}", response_model=FederationResponse)
async def get_federation(
    fed_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get federation details."""
    result = await db.execute(
        select(Federation).where(Federation.id == fed_id)
    )
    federation = result.scalar()

    if not federation:
        raise HTTPException(status_code=404, detail="Federation not found")

    return federation


@router.post("/federations/{fed_id}/join/{group_id}")
async def join_federation(
    fed_id: UUID,
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a group to a federation."""
    # Check group ownership
    result = await db.execute(
        select(Group).where(
            Group.id == group_id,
            Group.owner_id == current_user.id,
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=403, detail="Group ownership required")

    # Get federation
    result = await db.execute(
        select(Federation).where(Federation.id == fed_id)
    )
    if not result.scalar():
        raise HTTPException(status_code=404, detail="Federation not found")

    # Check if already a member
    result = await db.execute(
        select(FederationMember).where(
            FederationMember.federation_id == fed_id,
            FederationMember.group_id == group_id,
        )
    )
    if result.scalar():
        raise HTTPException(status_code=400, detail="Already a member")

    # Join
    member = FederationMember(
        federation_id=fed_id,
        group_id=group_id,
        joined_by=current_user.id,
    )
    db.add(member)
    await db.commit()

    return {"success": True}


@router.post("/federations/{fed_id}/ban/{user_id}")
async def fedban_user(
    fed_id: UUID,
    user_id: int,
    reason: str = "No reason provided",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ban a user from a federation."""
    # Check federation admin
    result = await db.execute(
        select(FederationAdmin).where(
            FederationAdmin.federation_id == fed_id,
            FederationAdmin.user_id == current_user.id,
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=403, detail="Federation admin required")

    # Create ban
    ban = FederationBan(
        federation_id=fed_id,
        target_user_id=user_id,
        banned_by=current_user.id,
        reason=reason,
    )
    db.add(ban)
    await db.commit()

    return {"success": True}


@router.get("/federations/{fed_id}/bans")
async def list_fedbans(
    fed_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List federation bans."""
    result = await db.execute(
        select(FederationBan, User)
        .join(User, FederationBan.target_user_id == User.id)
        .where(FederationBan.federation_id == fed_id)
        .order_by(FederationBan.created_at.desc())
    )

    bans = [
        {
            "id": ban.id,
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
            },
            "reason": ban.reason,
            "created_at": ban.created_at,
        }
        for ban, user in result.all()
    ]

    return bans
