"""Polls router - Advanced polling and voting system."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from shared.database import get_db
from shared.models import Member, Poll, User

router = APIRouter()


class PollOption(BaseModel):
    id: int
    text: str
    voter_count: int = 0


class PollCreate(BaseModel):
    question: str
    options: List[str]
    is_anonymous: bool = False
    allows_multiple: bool = False
    poll_type: str = "regular"  # regular, quiz, straw
    correct_option_id: Optional[int] = None
    close_date: Optional[str] = None


class PollResponse(BaseModel):
    id: int
    group_id: int
    question: str
    options: List[str]
    is_anonymous: bool
    allows_multiple: bool
    is_closed: bool
    message_id: Optional[int]
    created_by: int
    created_at: str
    total_votes: int = 0


class PollWithResults(PollResponse):
    options_with_counts: List[PollOption] = []


class PaginatedPollsResponse(BaseModel):
    items: List[PollResponse]
    total: int
    page: int
    page_size: int


@router.get("/groups/{group_id}/polls", response_model=PaginatedPollsResponse)
async def list_polls(
    group_id: int,
    page: int = 1,
    page_size: int = 20,
    include_closed: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all polls for a group."""
    # Check membership
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=403, detail="Not a member of this group")

    # Build query
    query = select(Poll).where(Poll.group_id == group_id)
    if not include_closed:
        query = query.where(Poll.is_closed == False)
    
    # Get total count
    count_result = await db.execute(
        select(func.count()).where(Poll.group_id == group_id)
    )
    total = count_result.scalar()

    # Get polls with pagination
    offset = (page - 1) * page_size
    result = await db.execute(
        query
        .order_by(Poll.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    polls = result.scalars().all()

    return PaginatedPollsResponse(
        items=[
            PollResponse(
                id=p.id,
                group_id=p.group_id,
                question=p.question,
                options=p.options if isinstance(p.options, list) else [],
                is_anonymous=p.is_anonymous,
                allows_multiple=p.allows_multiple,
                is_closed=p.is_closed,
                message_id=p.message_id,
                created_by=p.created_by,
                created_at=p.created_at.isoformat() if p.created_at else "",
                total_votes=sum(p.voter_counts) if isinstance(p.voter_counts, list) else 0,
            )
            for p in polls
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/groups/{group_id}/polls/{poll_id}", response_model=PollWithResults)
async def get_poll(
    group_id: int,
    poll_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific poll with results."""
    result = await db.execute(
        select(Poll).where(
            Poll.id == poll_id,
            Poll.group_id == group_id,
        )
    )
    poll = result.scalar()

    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    options_list = poll.options if isinstance(poll.options, list) else []
    voter_counts_list = poll.voter_counts if isinstance(poll.voter_counts, list) else []

    options_with_counts = [
        PollOption(
            id=i,
            text=opt,
            voter_count=voter_counts_list[i] if i < len(voter_counts_list) else 0,
        )
        for i, opt in enumerate(options_list)
    ]

    return PollWithResults(
        id=poll.id,
        group_id=poll.group_id,
        question=poll.question,
        options=options_list,
        is_anonymous=poll.is_anonymous,
        allows_multiple=poll.allows_multiple,
        is_closed=poll.is_closed,
        message_id=poll.message_id,
        created_by=poll.created_by,
        created_at=poll.created_at.isoformat() if poll.created_at else "",
        total_votes=sum(voter_counts_list),
        options_with_counts=options_with_counts,
    )


@router.post("/groups/{group_id}/polls", response_model=PollResponse)
async def create_poll(
    group_id: int,
    poll_data: PollCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new poll."""
    # Check admin permission for some poll types
    if poll_data.poll_type in ("scheduled",):
        result = await db.execute(
            select(Member).where(
                Member.user_id == current_user.id,
                Member.group_id == group_id,
            )
        )
        member = result.scalar()
        if not member or member.role not in ("owner", "admin"):
            raise HTTPException(status_code=403, detail="Admin access required")

    # Validate options
    if len(poll_data.options) < 2:
        raise HTTPException(status_code=400, detail="Poll must have at least 2 options")
    if len(poll_data.options) > 10:
        raise HTTPException(status_code=400, detail="Poll can have at most 10 options")

    # Create poll
    new_poll = Poll(
        group_id=group_id,
        question=poll_data.question,
        options=poll_data.options,
        is_anonymous=poll_data.is_anonymous,
        allows_multiple=poll_data.allows_multiple,
        is_closed=False,
        poll_type=poll_data.poll_type,
        correct_option_id=poll_data.correct_option_id,
        message_id=None,
        created_by=current_user.id,
    )
    db.add(new_poll)
    await db.commit()
    await db.refresh(new_poll)

    return PollResponse(
        id=new_poll.id,
        group_id=new_poll.group_id,
        question=new_poll.question,
        options=new_poll.options if isinstance(new_poll.options, list) else [],
        is_anonymous=new_poll.is_anonymous,
        allows_multiple=new_poll.allows_multiple,
        is_closed=new_poll.is_closed,
        message_id=new_poll.message_id,
        created_by=new_poll.created_by,
        created_at=new_poll.created_at.isoformat() if new_poll.created_at else "",
        total_votes=0,
    )


@router.post("/groups/{group_id}/polls/{poll_id}/close")
async def close_poll(
    group_id: int,
    poll_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Close a poll."""
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
        select(Poll).where(
            Poll.id == poll_id,
            Poll.group_id == group_id,
        )
    )
    poll = result.scalar()

    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    if poll.is_closed:
        raise HTTPException(status_code=400, detail="Poll is already closed")

    poll.is_closed = True
    await db.commit()

    return {"success": True, "poll_id": poll_id}


@router.post("/groups/{group_id}/polls/{poll_id}/vote")
async def vote_poll(
    group_id: int,
    poll_id: int,
    option_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Vote on a poll."""
    result = await db.execute(
        select(Poll).where(
            Poll.id == poll_id,
            Poll.group_id == group_id,
        )
    )
    poll = result.scalar()

    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    if poll.is_closed:
        raise HTTPException(status_code=400, detail="Poll is closed")

    # Get voter counts
    voter_counts = poll.voter_counts if isinstance(poll.voter_counts, list) else []
    while len(voter_counts) < len(poll.options):
        voter_counts.append(0)

    # Check if multiple votes allowed
    if not poll.allows_multiple:
        # Check if already voted - for simplicity, we track last vote
        # In a real app, you'd have a separate votes table
        pass

    # Add vote
    if 0 <= option_id < len(voter_counts):
        voter_counts[option_id] += 1
        poll.voter_counts = voter_counts

    await db.commit()

    return {"success": True, "option_id": option_id, "new_count": voter_counts[option_id]}


@router.delete("/groups/{group_id}/polls/{poll_id}")
async def delete_poll(
    group_id: int,
    poll_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a poll."""
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
        select(Poll).where(
            Poll.id == poll_id,
            Poll.group_id == group_id,
        )
    )
    poll = result.scalar()

    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    await db.delete(poll)
    await db.commit()

    return {"success": True}


@router.get("/groups/{group_id}/polls/stats/summary")
async def get_polls_stats(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get poll statistics summary."""
    # Check membership
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=403, detail="Not a member of this group")

    # Get counts
    total_result = await db.execute(
        select(func.count()).where(Poll.group_id == group_id)
    )
    total_polls = total_result.scalar()

    active_result = await db.execute(
        select(func.count()).where(
            Poll.group_id == group_id,
            Poll.is_closed == False
        )
    )
    active_polls = active_result.scalar()

    closed_result = await db.execute(
        select(func.count()).where(
            Poll.group_id == group_id,
            Poll.is_closed == True
        )
    )
    closed_polls = closed_result.scalar()

    # Get recent polls
    recent_result = await db.execute(
        select(Poll)
        .where(Poll.group_id == group_id)
        .order_by(Poll.created_at.desc())
        .limit(5)
    )
    recent_polls = recent_result.scalars().all()

    return {
        "total_polls": total_polls,
        "active_polls": active_polls,
        "closed_polls": closed_polls,
        "recent_polls": [
            {
                "id": p.id,
                "question": p.question,
                "is_closed": p.is_closed,
                "created_at": p.created_at.isoformat() if p.created_at else "",
                "total_votes": sum(p.voter_counts) if isinstance(p.voter_counts, list) else 0,
            }
            for p in recent_polls
        ],
    }
