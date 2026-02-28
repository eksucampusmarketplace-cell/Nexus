"""Modules registry router."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from shared.database import get_db
from shared.models import Member, ModuleConfig, User
from shared.schemas import ModuleInfoResponse

router = APIRouter()


# Module definitions (this would be populated from the actual module registry)
MODULE_DEFINITIONS = [
    {
        "name": "moderation",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Core moderation tools including warn, mute, ban, kick",
        "category": "moderation",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "welcome",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Welcome and goodbye messages for new and leaving members",
        "category": "greetings",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "captcha",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Anti-bot verification with multiple challenge types",
        "category": "greetings",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "locks",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Lock specific content types like links, stickers, forwards",
        "category": "antispam",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "antispam",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Anti-flood and spam protection",
        "category": "antispam",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "blocklist",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Banned words and phrases with multiple lists",
        "category": "antispam",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "notes",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Save and retrieve notes with #keyword",
        "category": "utility",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "filters",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Auto-responses based on keywords",
        "category": "utility",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "rules",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Group rules management",
        "category": "utility",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "economy",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Virtual currency and transactions",
        "category": "community",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "reputation",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Member reputation system",
        "category": "community",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "games",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Games and entertainment",
        "category": "games",
        "dependencies": ["economy"],
        "conflicts": [],
    },
    {
        "name": "polls",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Advanced polls and voting",
        "category": "utility",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "scheduler",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Schedule messages and automation",
        "category": "utility",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "ai_assistant",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "AI-powered assistant features",
        "category": "ai",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "analytics",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Group insights and statistics",
        "category": "utility",
        "dependencies": [],
        "conflicts": [],
    },
    {
        "name": "federations",
        "version": "1.0.0",
        "author": "Nexus Team",
        "description": "Cross-group ban synchronization",
        "category": "moderation",
        "dependencies": [],
        "conflicts": [],
    },
]


@router.get("/modules/registry")
async def list_modules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all available modules."""
    return MODULE_DEFINITIONS


@router.get("/groups/{group_id}/modules")
async def list_group_modules(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List modules with their enabled status for a group."""
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

    # Get enabled modules
    result = await db.execute(
        select(ModuleConfig).where(ModuleConfig.group_id == group_id)
    )
    configs = {c.module_name: c.is_enabled for c in result.scalars().all()}

    # Merge with definitions
    modules = []
    for module_def in MODULE_DEFINITIONS:
        modules.append({
            **module_def,
            "is_enabled": configs.get(module_def["name"], False),
        })

    return modules
