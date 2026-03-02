"""Message Templates API Router."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from shared.database import get_db
from shared.models import (
    MessageTemplate,
    MessageTemplateCategory,
    MessageTemplateDefinition,
    User,
)

router = APIRouter()


# ============ Request Models ============


class SaveTemplateRequest(BaseModel):
    identifier: str
    custom_text: str
    language: str = "en"
    tone: Optional[str] = None
    destination: str = "public"
    self_destruct_seconds: Optional[int] = None
    is_enabled: bool = True


class ToggleTemplateRequest(BaseModel):
    identifier: str
    language: str = "en"


# ============ Helpers ============


async def check_admin_access(group_id: int, user: User, db: AsyncSession):
    """Check if user has admin access to the group."""
    from shared.models import Member
    
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


# ============ Categories ============


@router.get("/groups/{group_id}/message-categories")
async def get_message_categories(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all message template categories."""
    await check_admin_access(group_id, current_user, db)
    
    result = await db.execute(
        select(MessageTemplateCategory).order_by(MessageTemplateCategory.sort_order)
    )
    categories = result.scalars().all()
    
    return [
        {
            "slug": c.slug,
            "name": c.name,
            "description": c.description,
            "icon": c.icon,
        }
        for c in categories
    ]


# ============ Template Definitions ============


@router.get("/groups/{group_id}/message-definitions")
async def get_message_definitions(
    group_id: int,
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all message template definitions."""
    await check_admin_access(group_id, current_user, db)
    
    query = select(MessageTemplateDefinition).where(
        MessageTemplateDefinition.is_enabled == True
    )
    
    if category:
        query = query.where(MessageTemplateDefinition.category_slug == category)
    
    query = query.order_by(MessageTemplateDefinition.sort_order)
    
    result = await db.execute(query)
    definitions = result.scalars().all()
    
    return [
        {
            "identifier": d.identifier,
            "category_slug": d.category_slug,
            "name": d.name,
            "description": d.description,
            "default_text": d.default_text,
            "default_tone": d.default_tone,
            "allowed_destinations": d.allowed_destinations,
            "supports_self_destruct": d.supports_self_destruct,
            "supports_variables": d.supports_variables,
            "available_variables": d.available_variables,
            "module_name": d.module_name,
        }
        for d in definitions
    ]


@router.get("/groups/{group_id}/message-definitions/{identifier}")
async def get_message_definition(
    group_id: int,
    identifier: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific message template definition with its variables."""
    await check_admin_access(group_id, current_user, db)
    
    result = await db.execute(
        select(MessageTemplateDefinition).where(
            MessageTemplateDefinition.identifier == identifier,
            MessageTemplateDefinition.is_enabled == True,
        )
    )
    definition = result.scalar_one_or_none()
    
    if not definition:
        raise HTTPException(status_code=404, detail="Message definition not found")
    
    return {
        "identifier": definition.identifier,
        "category_slug": definition.category_slug,
        "name": definition.name,
        "description": definition.description,
        "default_text": definition.default_text,
        "default_tone": definition.default_tone,
        "allowed_destinations": definition.allowed_destinations,
        "supports_self_destruct": definition.supports_self_destruct,
        "supports_variables": definition.supports_variables,
        "available_variables": definition.available_variables,
        "tone_variations": definition.tone_variations,
        "module_name": definition.module_name,
    }


# ============ Group Templates ============


@router.get("/groups/{group_id}/message-templates")
async def get_group_templates(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all custom message templates for a group."""
    await check_admin_access(group_id, current_user, db)
    
    result = await db.execute(
        select(MessageTemplate).where(MessageTemplate.group_id == group_id)
    )
    templates = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "identifier": t.identifier,
            "language": t.language,
            "custom_text": t.custom_text,
            "tone": t.tone,
            "destination": t.destination,
            "self_destruct_seconds": t.self_destruct_seconds,
            "is_enabled": t.is_enabled,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
        for t in templates
    ]


@router.get("/groups/{group_id}/message-templates/{identifier}")
async def get_group_template(
    group_id: int,
    identifier: str,
    language: str = Query("en"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific custom message template."""
    await check_admin_access(group_id, current_user, db)
    
    result = await db.execute(
        select(MessageTemplate).where(
            MessageTemplate.group_id == group_id,
            MessageTemplate.identifier == identifier,
            MessageTemplate.language == language,
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        # Return definition instead
        def_result = await db.execute(
            select(MessageTemplateDefinition).where(
                MessageTemplateDefinition.identifier == identifier,
            )
        )
        definition = def_result.scalar_one_or_none()
        
        if not definition:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "identifier": identifier,
            "language": language,
            "custom_text": definition.default_text,
            "tone": None,
            "destination": "public",
            "self_destruct_seconds": None,
            "is_enabled": True,
            "is_default": True,
            "available_variables": definition.available_variables,
        }
    
    return {
        "id": template.id,
        "identifier": template.identifier,
        "language": template.language,
        "custom_text": template.custom_text,
        "tone": template.tone,
        "destination": template.destination,
        "self_destruct_seconds": template.self_destruct_seconds,
        "is_enabled": template.is_enabled,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
        "is_default": False,
    }


@router.post("/groups/{group_id}/message-templates")
async def save_message_template(
    group_id: int,
    request: SaveTemplateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save or update a message template."""
    await check_admin_access(group_id, current_user, db)
    
    # Check if template exists
    result = await db.execute(
        select(MessageTemplate).where(
            MessageTemplate.group_id == group_id,
            MessageTemplate.identifier == request.identifier,
            MessageTemplate.language == request.language,
        )
    )
    template = result.scalar_one_or_none()
    
    if template:
        template.custom_text = request.custom_text
        template.tone = request.tone
        template.destination = request.destination
        template.self_destruct_seconds = request.self_destruct_seconds
        template.is_enabled = request.is_enabled
    else:
        template = MessageTemplate(
            group_id=group_id,
            identifier=request.identifier,
            language=request.language,
            custom_text=request.custom_text,
            tone=request.tone,
            destination=request.destination,
            self_destruct_seconds=request.self_destruct_seconds,
            is_enabled=request.is_enabled,
            created_by=current_user.id,
        )
        db.add(template)
    
    await db.flush()
    
    return {
        "id": template.id,
        "identifier": template.identifier,
        "language": template.language,
        "is_enabled": template.is_enabled,
    }


@router.delete("/groups/{group_id}/message-templates/{identifier}")
async def delete_message_template(
    group_id: int,
    identifier: str,
    language: str = Query("en"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom message template."""
    await check_admin_access(group_id, current_user, db)
    
    result = await db.execute(
        select(MessageTemplate).where(
            MessageTemplate.group_id == group_id,
            MessageTemplate.identifier == identifier,
            MessageTemplate.language == language,
        )
    )
    template = result.scalar_one_or_none()
    
    if template:
        await db.delete(template)
        await db.flush()
        return {"success": True}
    
    return {"success": False, "message": "Template not found"}


@router.post("/groups/{group_id}/message-templates/{identifier}/toggle")
async def toggle_message_template(
    group_id: int,
    identifier: str,
    language: str = Query("en"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle a message template on/off."""
    await check_admin_access(group_id, current_user, db)
    
    result = await db.execute(
        select(MessageTemplate).where(
            MessageTemplate.group_id == group_id,
            MessageTemplate.identifier == identifier,
            MessageTemplate.language == language,
        )
    )
    template = result.scalar_one_or_none()
    
    if template:
        template.is_enabled = not template.is_enabled
        await db.flush()
        return {"is_enabled": template.is_enabled}
    
    return {"is_enabled": None, "message": "No custom template - using defaults"}


# ============ Preview ============


@router.post("/groups/{group_id}/message-templates/preview")
async def preview_message_template(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Preview how a message template will look."""
    # This would use the message template service to render
    # with provided variables
    pass
