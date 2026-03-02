"""Commands API Router - manage all bot commands."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from shared.database import get_db
from shared.models import CommandConfig, CommandDefinition, User

router = APIRouter()


# ============ Request Models ============


class SaveCommandConfigRequest(BaseModel):
    command_id: str
    custom_name: Optional[str] = None
    custom_aliases: Optional[List[str]] = None
    custom_prefix: Optional[str] = None
    min_role: Optional[str] = None
    admin_only: Optional[bool] = None
    cooldown_seconds: Optional[int] = None
    allowed_topics: Optional[List[int]] = None
    denied_topics: Optional[List[int]] = None
    delete_trigger: Optional[bool] = None
    reply_mode: Optional[bool] = None
    pin_mode: Optional[str] = None
    is_enabled: bool = True
    require_confirmation: bool = False


class RenameCommandRequest(BaseModel):
    new_name: str


class AddAliasRequest(BaseModel):
    alias: str


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


# ============ Command Definitions ============


@router.get("/groups/{group_id}/commands")
async def list_commands(
    group_id: int,
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all available commands with their current settings."""
    await check_admin_access(group_id, current_user, db)
    
    # Get all definitions
    query = select(CommandDefinition).where(CommandDefinition.is_enabled == True)
    
    if category:
        query = query.where(CommandDefinition.category == category)
    if module:
        query = query.where(CommandDefinition.module_name == module)
    if search:
        search_lower = search.lower()
        query = query.where(
            (CommandDefinition.name.ilike(f"%{search}%")) |
            (CommandDefinition.description.ilike(f"%{search}%"))
        )
    
    query = query.order_by(CommandDefinition.sort_order)
    result = await db.execute(query)
    definitions = result.scalars().all()
    
    # Get all custom configs for this group
    config_result = await db.execute(
        select(CommandConfig).where(CommandConfig.group_id == group_id)
    )
    configs = {c.command_id: c for c in config_result.scalars().all()}
    
    commands = []
    for definition in definitions:
        config = configs.get(definition.command_id)
        
        # Resolve final values
        custom_name = config.custom_name if config and config.custom_name else definition.name
        custom_aliases = config.custom_aliases if config and config.custom_aliases else definition.default_aliases
        custom_prefix = config.custom_prefix if config and config.custom_prefix is not None else definition.default_prefix
        min_role = config.min_role if config and config.min_role else definition.default_min_role
        admin_only = config.admin_only if config and config.admin_only is not None else definition.default_admin_only
        cooldown = config.cooldown_seconds if config and config.cooldown_seconds is not None else definition.default_cooldown_seconds
        is_enabled = config.is_enabled if config else definition.is_enabled
        
        commands.append({
            "command_id": definition.command_id,
            "name": custom_name,
            "description": definition.description,
            "category": definition.category,
            "module": definition.module_name,
            "prefix": custom_prefix,
            "aliases": custom_aliases,
            "min_role": min_role,
            "admin_only": admin_only,
            "cooldown_seconds": cooldown,
            "is_enabled": is_enabled,
            "features": {
                "supports_cooldown": definition.supports_cooldown,
                "supports_aliases": definition.supports_aliases,
                "supports_prefix_change": definition.supports_prefix_change,
                "supports_permission_change": definition.supports_permission_change,
                "supports_topic_restriction": definition.supports_topic_restriction,
                "supports_confirmation": definition.supports_confirmation,
            },
            "defaults": {
                "name": definition.name,
                "prefix": definition.default_prefix,
                "aliases": definition.default_aliases,
                "min_role": definition.default_min_role,
                "cooldown": definition.default_cooldown_seconds,
            },
        })
    
    return commands


@router.get("/groups/{group_id}/commands/categories")
async def get_command_categories(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all command categories."""
    await check_admin_access(group_id, current_user, db)
    
    result = await db.execute(
        select(CommandDefinition.category).distinct()
    )
    categories = [row[0] for row in result.all()]
    
    return [{"slug": c, "name": c.title()} for c in categories]


@router.get("/groups/{group_id}/commands/modules")
async def get_command_modules(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all modules that have commands."""
    await check_admin_access(group_id, current_user, db)
    
    result = await db.execute(
        select(CommandDefinition.module_name).distinct()
    )
    modules = [row[0] for row in result.all()]
    
    return [{"slug": m, "name": m.replace("_", " ").title()} for m in modules]


# ============ Single Command ============


@router.get("/groups/{group_id}/commands/{command_id}")
async def get_command(
    group_id: int,
    command_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information about a command."""
    await check_admin_access(group_id, current_user, db)
    
    # Get definition
    def_result = await db.execute(
        select(CommandDefinition).where(CommandDefinition.command_id == command_id)
    )
    definition = def_result.scalar_one_or_none()
    
    if not definition:
        raise HTTPException(status_code=404, detail="Command not found")
    
    # Get config
    config_result = await db.execute(
        select(CommandConfig).where(
            CommandConfig.group_id == group_id,
            CommandConfig.command_id == command_id,
        )
    )
    config = config_result.scalar_one_or_none()
    
    return {
        "command_id": definition.command_id,
        "name": config.custom_name if config and config.custom_name else definition.name,
        "description": definition.description,
        "category": definition.category,
        "module": definition.module_name,
        "usage": definition.usage,
        "examples": definition.examples,
        
        # Current settings (merged)
        "prefix": config.custom_prefix if config and config.custom_prefix is not None else definition.default_prefix,
        "aliases": config.custom_aliases if config and config.custom_aliases else definition.default_aliases,
        "min_role": config.min_role if config and config.min_role else definition.default_min_role,
        "admin_only": config.admin_only if config and config.admin_only is not None else definition.default_admin_only,
        "cooldown_seconds": config.cooldown_seconds if config and config.cooldown_seconds is not None else definition.default_cooldown_seconds,
        "delete_trigger": config.delete_trigger if config and config.delete_trigger is not None else definition.default_delete_trigger,
        "reply_mode": config.reply_mode if config and config.reply_mode is not None else definition.default_reply_mode,
        "pin_mode": config.pin_mode if config and config.pin_mode else definition.default_pin_mode,
        "is_enabled": config.is_enabled if config else definition.is_enabled,
        "require_confirmation": config.require_confirmation if config else False,
        "allowed_topics": config.allowed_topics if config and config.allowed_topics else None,
        "denied_topics": config.denied_topics if config and config.denied_topics else None,
        
        # Features
        "features": {
            "supports_cooldown": definition.supports_cooldown,
            "supports_aliases": definition.supports_aliases,
            "supports_prefix_change": definition.supports_prefix_change,
            "supports_permission_change": definition.supports_permission_change,
            "supports_topic_restriction": definition.supports_topic_restriction,
            "supports_confirmation": definition.supports_confirmation,
        },
        
        # Defaults
        "defaults": {
            "name": definition.name,
            "prefix": definition.default_prefix,
            "aliases": definition.default_aliases,
            "min_role": definition.default_min_role,
            "admin_only": definition.default_admin_only,
            "cooldown": definition.default_cooldown_seconds,
            "delete_trigger": definition.default_delete_trigger,
            "reply_mode": definition.default_reply_mode,
            "pin_mode": definition.default_pin_mode,
        },
    }


# ============ Update Command Settings ============


@router.post("/groups/{group_id}/commands/{command_id}/config")
async def save_command_config(
    group_id: int,
    command_id: str,
    request: SaveCommandConfigRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save or update command configuration."""
    await check_admin_access(group_id, current_user, db)
    
    # Check command exists
    def_result = await db.execute(
        select(CommandDefinition).where(CommandDefinition.command_id == command_id)
    )
    definition = def_result.scalar_one_or_none()
    
    if not definition:
        raise HTTPException(status_code=404, detail="Command not found")
    
    # Check if config exists
    config_result = await db.execute(
        select(CommandConfig).where(
            CommandConfig.group_id == group_id,
            CommandConfig.command_id == command_id,
        )
    )
    config = config_result.scalar_one_or_none()
    
    if config:
        # Update existing
        if request.custom_name is not None:
            config.custom_name = request.custom_name
        if request.custom_aliases is not None:
            config.custom_aliases = request.custom_aliases
        if request.custom_prefix is not None:
            config.custom_prefix = request.custom_prefix
        if request.min_role is not None:
            config.min_role = request.min_role
        if request.admin_only is not None:
            config.admin_only = request.admin_only
        if request.cooldown_seconds is not None:
            config.cooldown_seconds = request.cooldown_seconds
        if request.allowed_topics is not None:
            config.allowed_topics = request.allowed_topics
        if request.denied_topics is not None:
            config.denied_topics = request.denied_topics
        if request.delete_trigger is not None:
            config.delete_trigger = request.delete_trigger
        if request.reply_mode is not None:
            config.reply_mode = request.reply_mode
        if request.pin_mode is not None:
            config.pin_mode = request.pin_mode
        config.is_enabled = request.is_enabled
        config.require_confirmation = request.require_confirmation
        config.updated_by = current_user.id
    else:
        # Create new
        config = CommandConfig(
            group_id=group_id,
            command_id=command_id,
            custom_name=request.custom_name,
            custom_aliases=request.custom_aliases,
            custom_prefix=request.custom_prefix,
            min_role=request.min_role,
            admin_only=request.admin_only,
            cooldown_seconds=request.cooldown_seconds,
            allowed_topics=request.allowed_topics,
            denied_topics=request.denied_topics,
            delete_trigger=request.delete_trigger,
            reply_mode=request.reply_mode,
            pin_mode=request.pin_mode,
            is_enabled=request.is_enabled,
            require_confirmation=request.require_confirmation,
            updated_by=current_user.id,
        )
        db.add(config)
    
    await db.flush()
    
    return {"success": True, "command_id": command_id}


@router.post("/groups/{group_id}/commands/{command_id}/rename")
async def rename_command(
    group_id: int,
    command_id: str,
    request: RenameCommandRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rename a command."""
    await check_admin_access(group_id, current_user, db)
    
    # Check command exists
    def_result = await db.execute(
        select(CommandDefinition).where(CommandDefinition.command_id == command_id)
    )
    definition = def_result.scalar_one_or_none()
    
    if not definition:
        raise HTTPException(status_code=404, detail="Command not found")
    
    if not definition.supports_prefix_change:
        raise HTTPException(status_code=400, detail="This command cannot be renamed")
    
    # Save config
    config_result = await db.execute(
        select(CommandConfig).where(
            CommandConfig.group_id == group_id,
            CommandConfig.command_id == command_id,
        )
    )
    config = config_result.scalar_one_or_none()
    
    if config:
        config.custom_name = request.new_name
    else:
        config = CommandConfig(
            group_id=group_id,
            command_id=command_id,
            custom_name=request.new_name,
            updated_by=current_user.id,
        )
        db.add(config)
    
    await db.flush()
    
    return {"success": True, "new_name": request.new_name}


@router.post("/groups/{group_id}/commands/{command_id}/aliases")
async def add_alias(
    group_id: int,
    command_id: str,
    request: AddAliasRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an alias to a command."""
    await check_admin_access(group_id, current_user, db)
    
    # Check command exists
    def_result = await db.execute(
        select(CommandDefinition).where(CommandDefinition.command_id == command_id)
    )
    definition = def_result.scalar_one_or_none()
    
    if not definition:
        raise HTTPException(status_code=404, detail="Command not found")
    
    if not definition.supports_aliases:
        raise HTTPException(status_code=400, detail="This command does not support aliases")
    
    # Get or create config
    config_result = await db.execute(
        select(CommandConfig).where(
            CommandConfig.group_id == group_id,
            CommandConfig.command_id == command_id,
        )
    )
    config = config_result.scalar_one_or_none()
    
    current_aliases = config.custom_aliases if config and config.custom_aliases else definition.default_aliases
    
    if request.alias in current_aliases:
        raise HTTPException(status_code=400, detail="Alias already exists")
    
    new_aliases = current_aliases + [request.alias]
    
    if config:
        config.custom_aliases = new_aliases
    else:
        config = CommandConfig(
            group_id=group_id,
            command_id=command_id,
            custom_aliases=new_aliases,
            updated_by=current_user.id,
        )
        db.add(config)
    
    await db.flush()
    
    return {"success": True, "aliases": new_aliases}


@router.delete("/groups/{group_id}/commands/{command_id}/aliases/{alias}")
async def remove_alias(
    group_id: int,
    command_id: str,
    alias: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove an alias from a command."""
    await check_admin_access(group_id, current_user, db)
    
    # Get config
    config_result = await db.execute(
        select(CommandConfig).where(
            CommandConfig.group_id == group_id,
            CommandConfig.command_id == command_id,
        )
    )
    config = config_result.scalar_one_or_none()
    
    # Get definition for defaults
    def_result = await db.execute(
        select(CommandDefinition).where(CommandDefinition.command_id == command_id)
    )
    definition = def_result.scalar_one_or_none()
    
    if not definition:
        raise HTTPException(status_code=404, detail="Command not found")
    
    current_aliases = config.custom_aliases if config and config.custom_aliases else definition.default_aliases
    
    if alias not in current_aliases:
        raise HTTPException(status_code=404, detail="Alias not found")
    
    new_aliases = [a for a in current_aliases if a != alias]
    
    if config:
        config.custom_aliases = new_aliases
    else:
        config = CommandConfig(
            group_id=group_id,
            command_id=command_id,
            custom_aliases=new_aliases,
            updated_by=current_user.id,
        )
        db.add(config)
    
    await db.flush()
    
    return {"success": True, "aliases": new_aliases}


@router.post("/groups/{group_id}/commands/{command_id}/toggle")
async def toggle_command(
    group_id: int,
    command_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle a command on/off."""
    await check_admin_access(group_id, current_user, db)
    
    # Get config
    config_result = await db.execute(
        select(CommandConfig).where(
            CommandConfig.group_id == group_id,
            CommandConfig.command_id == command_id,
        )
    )
    config = config_result.scalar_one_or_none()
    
    # Get definition
    def_result = await db.execute(
        select(CommandDefinition).where(CommandDefinition.command_id == command_id)
    )
    definition = def_result.scalar_one_or_none()
    
    if not definition:
        raise HTTPException(status_code=404, detail="Command not found")
    
    if config:
        config.is_enabled = not config.is_enabled
    else:
        config = CommandConfig(
            group_id=group_id,
            command_id=command_id,
            is_enabled=False,
            updated_by=current_user.id,
        )
        db.add(config)
    
    await db.flush()
    
    return {"is_enabled": config.is_enabled}


@router.post("/groups/{group_id}/commands/{command_id}/reset")
async def reset_command_config(
    group_id: int,
    command_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reset command configuration to defaults."""
    await check_admin_access(group_id, current_user, db)
    
    # Get config
    config_result = await db.execute(
        select(CommandConfig).where(
            CommandConfig.group_id == group_id,
            CommandConfig.command_id == command_id,
        )
    )
    config = config_result.scalar_one_or_none()
    
    if config:
        await db.delete(config)
        await db.flush()
    
    return {"success": True}
