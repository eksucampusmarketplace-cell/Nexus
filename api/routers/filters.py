"""Filters router - Keyword auto-responses."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from shared.database import get_db
from shared.models import Filter, Member, User

router = APIRouter()


class FilterCreate(BaseModel):
    trigger: str
    match_type: str = "contains"
    response_type: str = "text"
    response_content: str
    action: Optional[str] = None
    delete_trigger: bool = False
    admin_only: bool = False
    case_sensitive: bool = False


class FilterUpdate(BaseModel):
    match_type: Optional[str] = None
    response_type: Optional[str] = None
    response_content: Optional[str] = None
    action: Optional[str] = None
    delete_trigger: Optional[bool] = None
    admin_only: Optional[bool] = None
    case_sensitive: Optional[bool] = None


class FilterResponse(BaseModel):
    id: int
    group_id: int
    trigger: str
    match_type: str
    response_type: str
    response_content: str
    response_file_id: Optional[str]
    action: Optional[str]
    delete_trigger: bool
    admin_only: bool
    case_sensitive: bool
    created_by: int
    created_at: str

    class Config:
        from_attributes = True


class PaginatedFiltersResponse(BaseModel):
    items: List[FilterResponse]
    total: int
    page: int
    page_size: int


@router.get("/groups/{group_id}/filters", response_model=PaginatedFiltersResponse)
async def list_filters(
    group_id: int,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all filters for a group."""
    # Check membership
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=403, detail="Not a member of this group")

    # Get filters with pagination
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Filter)
        .where(Filter.group_id == group_id)
        .order_by(Filter.trigger)
        .offset(offset)
        .limit(page_size)
    )
    filters = result.scalars().all()

    # Get total count
    total_result = await db.execute(
        select(func.count()).where(Filter.group_id == group_id)
    )
    total = total_result.scalar()

    return PaginatedFiltersResponse(
        items=[
            FilterResponse(
                id=f.id,
                group_id=f.group_id,
                trigger=f.trigger,
                match_type=f.match_type,
                response_type=f.response_type,
                response_content=f.response_content,
                response_file_id=f.response_file_id,
                action=f.action,
                delete_trigger=f.delete_trigger,
                admin_only=f.admin_only,
                case_sensitive=f.case_sensitive,
                created_by=f.created_by,
                created_at=f.created_at.isoformat() if f.created_at else "",
            )
            for f in filters
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/groups/{group_id}/filters", response_model=FilterResponse)
async def create_filter(
    group_id: int,
    filter_data: FilterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new filter."""
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

    # Check for duplicate trigger
    result = await db.execute(
        select(Filter).where(
            Filter.group_id == group_id,
            Filter.trigger == filter_data.trigger.lower(),
        )
    )
    existing = result.scalar()

    if existing:
        raise HTTPException(status_code=400, detail="Filter with this trigger already exists")

    # Create filter
    new_filter = Filter(
        group_id=group_id,
        trigger=filter_data.trigger.lower(),
        match_type=filter_data.match_type,
        response_type=filter_data.response_type,
        response_content=filter_data.response_content,
        action=filter_data.action,
        delete_trigger=filter_data.delete_trigger,
        admin_only=filter_data.admin_only,
        case_sensitive=filter_data.case_sensitive,
        created_by=current_user.id,
    )
    db.add(new_filter)
    await db.commit()
    await db.refresh(new_filter)

    return FilterResponse(
        id=new_filter.id,
        group_id=new_filter.group_id,
        trigger=new_filter.trigger,
        match_type=new_filter.match_type,
        response_type=new_filter.response_type,
        response_content=new_filter.response_content,
        response_file_id=new_filter.response_file_id,
        action=new_filter.action,
        delete_trigger=new_filter.delete_trigger,
        admin_only=new_filter.admin_only,
        case_sensitive=new_filter.case_sensitive,
        created_by=new_filter.created_by,
        created_at=new_filter.created_at.isoformat() if new_filter.created_at else "",
    )


@router.get("/groups/{group_id}/filters/{filter_id}", response_model=FilterResponse)
async def get_filter(
    group_id: int,
    filter_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific filter."""
    result = await db.execute(
        select(Filter).where(
            Filter.id == filter_id,
            Filter.group_id == group_id,
        )
    )
    filter_obj = result.scalar()

    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found")

    return FilterResponse(
        id=filter_obj.id,
        group_id=filter_obj.group_id,
        trigger=filter_obj.trigger,
        match_type=filter_obj.match_type,
        response_type=filter_obj.response_type,
        response_content=filter_obj.response_content,
        response_file_id=filter_obj.response_file_id,
        action=filter_obj.action,
        delete_trigger=filter_obj.delete_trigger,
        admin_only=filter_obj.admin_only,
        case_sensitive=filter_obj.case_sensitive,
        created_by=filter_obj.created_by,
        created_at=filter_obj.created_at.isoformat() if filter_obj.created_at else "",
    )


@router.patch("/groups/{group_id}/filters/{filter_id}", response_model=FilterResponse)
async def update_filter(
    group_id: int,
    filter_id: int,
    filter_data: FilterUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a filter."""
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
        select(Filter).where(
            Filter.id == filter_id,
            Filter.group_id == group_id,
        )
    )
    filter_obj = result.scalar()

    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found")

    # Update fields
    if filter_data.match_type is not None:
        filter_obj.match_type = filter_data.match_type
    if filter_data.response_type is not None:
        filter_obj.response_type = filter_data.response_type
    if filter_data.response_content is not None:
        filter_obj.response_content = filter_data.response_content
    if filter_data.action is not None:
        filter_obj.action = filter_data.action
    if filter_data.delete_trigger is not None:
        filter_obj.delete_trigger = filter_data.delete_trigger
    if filter_data.admin_only is not None:
        filter_obj.admin_only = filter_data.admin_only
    if filter_data.case_sensitive is not None:
        filter_obj.case_sensitive = filter_data.case_sensitive

    await db.commit()
    await db.refresh(filter_obj)

    return FilterResponse(
        id=filter_obj.id,
        group_id=filter_obj.group_id,
        trigger=filter_obj.trigger,
        match_type=filter_obj.match_type,
        response_type=filter_obj.response_type,
        response_content=filter_obj.response_content,
        response_file_id=filter_obj.response_file_id,
        action=filter_obj.action,
        delete_trigger=filter_obj.delete_trigger,
        admin_only=filter_obj.admin_only,
        case_sensitive=filter_obj.case_sensitive,
        created_by=filter_obj.created_by,
        created_at=filter_obj.created_at.isoformat() if filter_obj.created_at else "",
    )


@router.delete("/groups/{group_id}/filters/{filter_id}")
async def delete_filter(
    group_id: int,
    filter_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a filter."""
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
        select(Filter).where(
            Filter.id == filter_id,
            Filter.group_id == group_id,
        )
    )
    filter_obj = result.scalar()

    if not filter_obj:
        raise HTTPException(status_code=404, detail="Filter not found")

    await db.delete(filter_obj)
    await db.commit()

    return {"success": True}


@router.delete("/groups/{group_id}/filters")
async def delete_all_filters(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete all filters for a group."""
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

    await db.execute(
        select(Filter).where(Filter.group_id == group_id)
    )
    await db.execute(
        f"DELETE FROM filters WHERE group_id = {group_id}"
    )
    await db.commit()

    return {"success": True, "deleted_count": "all"}


@router.post("/groups/{group_id}/filters/test")
async def test_filter(
    group_id: int,
    trigger: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test which filters would match a trigger."""
    result = await db.execute(
        select(Filter).where(Filter.group_id == group_id)
    )
    filters = result.scalars().all()

    import re
    matches = []
    trigger_lower = trigger.lower()

    for f in filters:
        text_to_check = trigger_lower if not f.case_sensitive else trigger
        trigger_check = f.trigger if not f.case_sensitive else f.trigger.lower()

        is_match = False
        if f.match_type == "exact":
            is_match = text_to_check == trigger_check
        elif f.match_type == "contains":
            is_match = trigger_check in text_to_check
        elif f.match_type == "startswith":
            is_match = text_to_check.startswith(trigger_check)
        elif f.match_type == "endswith":
            is_match = text_to_check.endswith(trigger_check)
        elif f.match_type == "regex":
            try:
                pattern = re.compile(f.trigger)
                is_match = bool(pattern.search(trigger))
            except Exception:
                pass

        if is_match:
            matches.append({
                "id": f.id,
                "trigger": f.trigger,
                "match_type": f.match_type,
                "response_type": f.response_type,
                "action": f.action,
            })

    return {"trigger": trigger, "matches": matches, "match_count": len(matches)}
