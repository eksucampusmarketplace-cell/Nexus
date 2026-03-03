"""Message Graveyard API endpoints."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shared.database import get_db
from shared.models import DeletedMessage, Group, User
from shared.schemas import (
    DeletedMessageListResponse,
    DeletedMessageResponse,
    DeletedMessageStats,
)

router = APIRouter()


@router.get("/groups/{group_id}/graveyard", response_model=DeletedMessageListResponse)
async def list_deleted_messages(
    group_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    deletion_reason: Optional[str] = None,
    user_id: Optional[int] = None,
    content_type: Optional[str] = None,
    restored: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List deleted messages in the graveyard.
    
    Supports filtering by:
    - deletion_reason: Filter by reason (word_filter, flood, lock_violation, etc.)
    - user_id: Filter by user whose message was deleted
    - content_type: Filter by content type (text, photo, video, etc.)
    - restored: Filter by restoration status
    """
    # Build query
    query = (
        select(DeletedMessage)
        .options(
            joinedload(DeletedMessage.user),
            joinedload(DeletedMessage.deleter),
        )
        .where(DeletedMessage.group_id == group_id)
    )
    
    # Apply filters
    if deletion_reason:
        query = query.where(DeletedMessage.deletion_reason == deletion_reason)
    
    if user_id:
        query = query.where(DeletedMessage.user_id == user_id)
    
    if content_type:
        query = query.where(DeletedMessage.content_type == content_type)
    
    if restored is not None:
        if restored:
            query = query.where(DeletedMessage.restored_at.isnot(None))
        else:
            query = query.where(DeletedMessage.restored_at.is_(None))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(DeletedMessage.deleted_at.desc()).offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    deleted_messages = result.unique().scalars().all()
    
    # Build response
    items = []
    for msg in deleted_messages:
        items.append(
            DeletedMessageResponse(
                id=msg.id,
                group_id=msg.group_id,
                message_id=msg.message_id,
                user_id=msg.user_id,
                content=msg.content,
                content_type=msg.content_type,
                deletion_reason=msg.deletion_reason,
                deleted_by=msg.deleted_by,
                deleted_at=msg.deleted_at,
                can_restore=msg.can_restore,
                restored_at=msg.restored_at,
                restored_by=msg.restored_by,
                restored_message_id=msg.restored_message_id,
                trigger_word=msg.trigger_word,
                lock_type=msg.lock_type,
                ai_confidence=msg.ai_confidence,
                user_username=msg.user.username if msg.user else None,
                user_first_name=msg.user.first_name if msg.user else None,
                user_last_name=msg.user.last_name if msg.user else None,
                deleter_username=msg.deleter.username if msg.deleter else None,
                deleter_first_name=msg.deleter.first_name if msg.deleter else None,
            )
        )
    
    return DeletedMessageListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(items)) < total,
    )


@router.get("/groups/{group_id}/graveyard/stats", response_model=DeletedMessageStats)
async def get_graveyard_stats(
    group_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics about deleted messages in the graveyard.
    """
    # Total deleted
    total_query = select(func.count()).select_from(DeletedMessage).where(
        DeletedMessage.group_id == group_id
    )
    total_result = await db.execute(total_query)
    total_deleted = total_result.scalar()
    
    # By reason
    reason_query = (
        select(
            DeletedMessage.deletion_reason,
            func.count().label("count")
        )
        .where(DeletedMessage.group_id == group_id)
        .group_by(DeletedMessage.deletion_reason)
    )
    reason_result = await db.execute(reason_query)
    by_reason = {row.deletion_reason: row.count for row in reason_result}
    
    # By content type
    content_query = (
        select(
            DeletedMessage.content_type,
            func.count().label("count")
        )
        .where(DeletedMessage.group_id == group_id)
        .group_by(DeletedMessage.content_type)
    )
    content_result = await db.execute(content_query)
    by_content_type = {row.content_type: row.count for row in content_result}
    
    # Recent deletions (24h)
    yesterday = datetime.utcnow() - timedelta(hours=24)
    recent_query = select(func.count()).select_from(DeletedMessage).where(
        DeletedMessage.group_id == group_id,
        DeletedMessage.deleted_at >= yesterday
    )
    recent_result = await db.execute(recent_query)
    recent_deletions_24h = recent_result.scalar()
    
    # Restored count
    restored_query = select(func.count()).select_from(DeletedMessage).where(
        DeletedMessage.group_id == group_id,
        DeletedMessage.restored_at.isnot(None)
    )
    restored_result = await db.execute(restored_query)
    restored_count = restored_result.scalar()
    
    # Restoration rate
    restoration_rate = (restored_count / total_deleted * 100) if total_deleted > 0 else 0.0
    
    return DeletedMessageStats(
        total_deleted=total_deleted,
        by_reason=by_reason,
        by_content_type=by_content_type,
        recent_deletions_24h=recent_deletions_24h,
        restored_count=restored_count,
        restoration_rate=restoration_rate,
    )


@router.get("/groups/{group_id}/graveyard/{message_id}", response_model=DeletedMessageResponse)
async def get_deleted_message(
    group_id: int,
    message_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get details of a specific deleted message.
    """
    query = (
        select(DeletedMessage)
        .options(
            joinedload(DeletedMessage.user),
            joinedload(DeletedMessage.deleter),
        )
        .where(
            DeletedMessage.id == message_id,
            DeletedMessage.group_id == group_id,
        )
    )
    
    result = await db.execute(query)
    msg = result.unique().scalar_one_or_none()
    
    if not msg:
        raise HTTPException(status_code=404, detail="Deleted message not found")
    
    return DeletedMessageResponse(
        id=msg.id,
        group_id=msg.group_id,
        message_id=msg.message_id,
        user_id=msg.user_id,
        content=msg.content,
        content_type=msg.content_type,
        deletion_reason=msg.deletion_reason,
        deleted_by=msg.deleted_by,
        deleted_at=msg.deleted_at,
        can_restore=msg.can_restore,
        restored_at=msg.restored_at,
        restored_by=msg.restored_by,
        restored_message_id=msg.restored_message_id,
        trigger_word=msg.trigger_word,
        lock_type=msg.lock_type,
        ai_confidence=msg.ai_confidence,
        user_username=msg.user.username if msg.user else None,
        user_first_name=msg.user.first_name if msg.user else None,
        user_last_name=msg.user.last_name if msg.user else None,
        deleter_username=msg.deleter.username if msg.deleter else None,
        deleter_first_name=msg.deleter.first_name if msg.deleter else None,
    )


@router.post("/groups/{group_id}/graveyard/{message_id}/restore")
async def restore_deleted_message(
    group_id: int,
    message_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Restore a deleted message from the graveyard.
    
    This will re-send the message to the group.
    Note: Media messages may not be fully restorable if the file has expired.
    """
    # Import here to avoid circular dependency
    from aiogram import Bot
    from bot.services.action_executor import SharedActionExecutor
    from shared.models import User as UserModel
    
    # Get the deleted message
    query = (
        select(DeletedMessage)
        .options(
            joinedload(DeletedMessage.user),
        )
        .where(
            DeletedMessage.id == message_id,
            DeletedMessage.group_id == group_id,
        )
    )
    
    result = await db.execute(query)
    deleted_msg = result.unique().scalar_one_or_none()
    
    if not deleted_msg:
        raise HTTPException(status_code=404, detail="Deleted message not found")
    
    # Get or create bot user for restoration
    bot_user_query = select(UserModel).where(UserModel.telegram_id == 0)  # Bot user marker
    bot_user_result = await db.execute(bot_user_query)
    bot_user = bot_user_result.scalar_one_or_none()
    
    if not bot_user:
        # Create a placeholder bot user
        bot_user = UserModel(
            telegram_id=0,
            username="nexus_bot",
            first_name="Nexus Bot",
        )
        db.add(bot_user)
        await db.commit()
    
    # Get bot instance
    import os
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise HTTPException(status_code=500, detail="Bot token not configured")
    
    bot = Bot(token=bot_token)
    
    try:
        # Create action executor
        executor = SharedActionExecutor(db, bot, group_id)
        
        # Restore the message
        action_result = await executor.restore_message(message_id, bot_user)
        
        if not action_result.success:
            raise HTTPException(
                status_code=400,
                detail=action_result.error or "Failed to restore message"
            )
        
        return {
            "success": True,
            "message": "Message restored successfully",
            "new_message_id": action_result.extra_data.get("new_message_id") if action_result.extra_data else None,
        }
        
    finally:
        await bot.session.close()


@router.delete("/groups/{group_id}/graveyard/{message_id}")
async def purge_deleted_message(
    group_id: int,
    message_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete a message from the graveyard.
    
    This removes all traces of the message and it cannot be restored.
    Admin only - requires elevated permissions.
    """
    # Get the deleted message
    query = select(DeletedMessage).where(
        DeletedMessage.id == message_id,
        DeletedMessage.group_id == group_id,
    )
    
    result = await db.execute(query)
    deleted_msg = result.scalar_one_or_none()
    
    if not deleted_msg:
        raise HTTPException(status_code=404, detail="Deleted message not found")
    
    # Mark as non-restorable and clear content
    deleted_msg.can_restore = False
    deleted_msg.content = None
    deleted_msg.media_file_id = None
    
    await db.commit()
    
    return {
        "success": True,
        "message": "Message purged from graveyard",
    }
