"""Bot builder API routes."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date, timedelta

from api.routers.auth import get_current_user
from shared.database import get_db
from shared.models import User, BotTemplate, BotFlow, UserBot, FlowExecution, CustomCommand, KeywordResponder, BotAnalytics
from shared.schemas import (
    BotTemplateResponse, BotTemplateCreate, BotTemplateListResponse,
    BotFlowResponse, BotFlowCreate, BotFlowUpdate, BotFlowListResponse,
    UserBotResponse, UserBotCreate, UserBotUpdate, UserBotListResponse,
    AIBotGenerationRequest, AIBotGenerationResponse,
    CustomCommandResponse, CustomCommandCreate, CustomCommandUpdate, CustomCommandListResponse,
    KeywordResponderResponse, KeywordResponderCreate, KeywordResponderUpdate, KeywordResponderListResponse,
    BotAnalyticsResponse, BotAnalyticsSummary, FlowExecutionResponse,
    PaginatedResponse
)

router = APIRouter(prefix="/bot-builder", tags=["Bot Builder"])


# ==================== BOT TEMPLATES ====================

@router.get("/templates", response_model=BotTemplateListResponse)
async def list_templates(
    category: Optional[str] = None,
    featured: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List available bot templates."""
    query = select(BotTemplate).where(BotTemplate.is_public == True)
    
    if category:
        query = query.where(BotTemplate.category == category)
    if featured:
        query = query.where(BotTemplate.is_featured == True)
    
    query = query.order_by(BotTemplate.usage_count.desc())
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return BotTemplateListResponse(
        total=total or 0,
        page=page,
        per_page=per_page,
        pages=((total or 0) + per_page - 1) // per_page,
        items=[BotTemplateResponse.model_validate(t) for t in templates]
    )


@router.get("/templates/{template_id}", response_model=BotTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific bot template."""
    template = await db.get(BotTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return BotTemplateResponse.model_validate(template)


@router.post("/templates", response_model=BotTemplateResponse)
async def create_template(
    data: BotTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new bot template (admin only)."""
    # Check admin role
    # TODO: Add admin check
    
    template = BotTemplate(**data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return BotTemplateResponse.model_validate(template)


# ==================== BOT FLOWS ====================

@router.get("/flows", response_model=BotFlowListResponse)
async def list_flows(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's flows."""
    query = select(BotFlow).where(BotFlow.owner_id == current_user.id)
    query = query.order_by(BotFlow.updated_at.desc())
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    flows = result.scalars().all()
    
    return BotFlowListResponse(
        total=total or 0,
        page=page,
        per_page=per_page,
        pages=((total or 0) + per_page - 1) // per_page,
        items=[BotFlowResponse.model_validate(f) for f in flows]
    )


@router.post("/flows", response_model=BotFlowResponse)
async def create_flow(
    data: BotFlowCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new flow."""
    flow = BotFlow(
        owner_id=current_user.id,
        name=data.name,
        description=data.description,
        nodes=data.nodes,
        connections=data.connections,
        variables=data.variables,
        settings=data.settings,
        triggers=data.triggers,
        is_template=data.is_template
    )
    db.add(flow)
    await db.commit()
    await db.refresh(flow)
    return BotFlowResponse.model_validate(flow)


@router.get("/flows/{flow_id}", response_model=BotFlowResponse)
async def get_flow(
    flow_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific flow."""
    flow = await db.get(BotFlow, flow_id)
    if not flow or flow.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Flow not found")
    return BotFlowResponse.model_validate(flow)


@router.patch("/flows/{flow_id}", response_model=BotFlowResponse)
async def update_flow(
    flow_id: int,
    data: BotFlowUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a flow."""
    flow = await db.get(BotFlow, flow_id)
    if not flow or flow.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(flow, field, value)
    
    await db.commit()
    await db.refresh(flow)
    return BotFlowResponse.model_validate(flow)


@router.delete("/flows/{flow_id}")
async def delete_flow(
    flow_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a flow."""
    flow = await db.get(BotFlow, flow_id)
    if not flow or flow.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    await db.delete(flow)
    await db.commit()
    return {"message": "Flow deleted"}


@router.post("/flows/{flow_id}/duplicate", response_model=BotFlowResponse)
async def duplicate_flow(
    flow_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Duplicate a flow."""
    flow = await db.get(BotFlow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    new_flow = BotFlow(
        owner_id=current_user.id,
        name=f"{flow.name} (Copy)",
        description=flow.description,
        nodes=flow.nodes,
        connections=flow.connections,
        variables=flow.variables,
        settings=flow.settings,
        triggers=flow.triggers,
        is_template=False
    )
    db.add(new_flow)
    await db.commit()
    await db.refresh(new_flow)
    return BotFlowResponse.model_validate(new_flow)


# ==================== USER BOTS ====================

@router.get("/bots", response_model=UserBotListResponse)
async def list_user_bots(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's bots."""
    query = select(UserBot).where(UserBot.owner_id == current_user.id)
    query = query.order_by(UserBot.updated_at.desc())
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    bots = result.scalars().all()
    
    return UserBotListResponse(
        total=total or 0,
        page=page,
        per_page=per_page,
        pages=((total or 0) + per_page - 1) // per_page,
        items=[UserBotResponse.model_validate(b) for b in bots]
    )


@router.post("/bots", response_model=UserBotResponse)
async def create_user_bot(
    data: UserBotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user bot."""
    bot = UserBot(
        owner_id=current_user.id,
        name=data.name,
        description=data.description,
        bot_type=data.bot_type,
        bot_token=data.bot_token,
        flow_id=data.flow_id,
        settings=data.settings or {}
    )
    
    # If custom token, validate it
    if data.bot_token and data.bot_type == "custom":
        # TODO: Validate token with Telegram API
        pass
    
    db.add(bot)
    await db.commit()
    await db.refresh(bot)
    
    # Return without exposing token
    response = UserBotResponse.model_validate(bot)
    response.bot_token = None
    return response


@router.get("/bots/{bot_id}", response_model=UserBotResponse)
async def get_user_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific user bot."""
    bot = await db.get(UserBot, bot_id)
    if not bot or bot.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    response = UserBotResponse.model_validate(bot)
    response.bot_token = None  # Never expose token
    return response


@router.patch("/bots/{bot_id}", response_model=UserBotResponse)
async def update_user_bot(
    bot_id: int,
    data: UserBotUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a user bot."""
    bot = await db.get(UserBot, bot_id)
    if not bot or bot.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(bot, field, value)
    
    await db.commit()
    await db.refresh(bot)
    
    response = UserBotResponse.model_validate(bot)
    response.bot_token = None
    return response


@router.delete("/bots/{bot_id}")
async def delete_user_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user bot."""
    bot = await db.get(UserBot, bot_id)
    if not bot or bot.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    await db.delete(bot)
    await db.commit()
    return {"message": "Bot deleted"}


@router.post("/bots/{bot_id}/start")
async def start_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a user bot."""
    bot = await db.get(UserBot, bot_id)
    if not bot or bot.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # TODO: Register webhook, start processing
    bot.is_active = True
    await db.commit()
    
    return {"message": "Bot started", "bot_id": bot.id}


@router.post("/bots/{bot_id}/stop")
async def stop_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stop a user bot."""
    bot = await db.get(UserBot, bot_id)
    if not bot or bot.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # TODO: Remove webhook, stop processing
    bot.is_active = False
    await db.commit()
    
    return {"message": "Bot stopped", "bot_id": bot.id}


# ==================== AI BOT BUILDER ====================

@router.post("/ai-generate", response_model=AIBotGenerationResponse)
async def generate_bot_with_ai(
    data: AIBotGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a bot using AI from a prompt."""
    # This would use OpenAI to generate a flow based on the prompt
    # For now, return a placeholder
    
    # Create flow from AI-generated structure
    flow = BotFlow(
        owner_id=current_user.id,
        name=data.bot_name,
        description=data.description,
        nodes=[
            {
                "id": "start",
                "type": "trigger",
                "position": {"x": 100, "y": 100},
                "data": {"trigger_type": "message"}
            },
            {
                "id": "respond",
                "type": "response",
                "position": {"x": 300, "y": 100},
                "data": {"content": "Hello! How can I help you?"}
            }
        ],
        connections=[
            {"id": "c1", "source": "start", "target": "respond"}
        ],
        triggers=[{"type": "message", "pattern": ".*"}]
    )
    db.add(flow)
    
    # Create bot
    bot = UserBot(
        owner_id=current_user.id,
        name=data.bot_name,
        description=data.description,
        bot_type="nexus_powered",
        flow_id=flow.id,
        settings={"ai_generated": True}
    )
    db.add(bot)
    
    await db.commit()
    await db.refresh(flow)
    await db.refresh(bot)
    
    return AIBotGenerationResponse(
        flow=BotFlowResponse.model_validate(flow),
        bot=UserBotResponse.model_validate(bot),
        suggested_commands=["/start", "/help", "/info"],
        suggested_keywords=["hello", "help", "info"]
    )


# ==================== CUSTOM COMMANDS ====================

@router.get("/bots/{bot_id}/commands", response_model=CustomCommandListResponse)
async def list_commands(
    bot_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List custom commands for a bot."""
    bot = await db.get(UserBot, bot_id)
    if not bot or bot.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    query = select(CustomCommand).where(CustomCommand.user_bot_id == bot_id)
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    commands = result.scalars().all()
    
    return CustomCommandListResponse(
        total=total or 0,
        page=page,
        per_page=per_page,
        pages=((total or 0) + per_page - 1) // per_page,
        items=[CustomCommandResponse.model_validate(c) for c in commands]
    )


@router.post("/bots/{bot_id}/commands", response_model=CustomCommandResponse)
async def create_command(
    bot_id: int,
    data: CustomCommandCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a custom command."""
    bot = await db.get(UserBot, bot_id)
    if not bot or bot.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    command = CustomCommand(
        owner_id=current_user.id,
        user_bot_id=bot_id,
        **data.model_dump()
    )
    db.add(command)
    await db.commit()
    await db.refresh(command)
    return CustomCommandResponse.model_validate(command)


@router.patch("/bots/{bot_id}/commands/{command_id}", response_model=CustomCommandResponse)
async def update_command(
    bot_id: int,
    command_id: int,
    data: CustomCommandUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a custom command."""
    command = await db.get(CustomCommand, command_id)
    if not command or command.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Command not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(command, field, value)
    
    await db.commit()
    await db.refresh(command)
    return CustomCommandResponse.model_validate(command)


@router.delete("/bots/{bot_id}/commands/{command_id}")
async def delete_command(
    bot_id: int,
    command_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a custom command."""
    command = await db.get(CustomCommand, command_id)
    if not command or command.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Command not found")
    
    await db.delete(command)
    await db.commit()
    return {"message": "Command deleted"}


# ==================== KEYWORD RESPONDERS ====================

@router.get("/bots/{bot_id}/keywords", response_model=KeywordResponderListResponse)
async def list_keyword_responders(
    bot_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List keyword responders for a bot."""
    bot = await db.get(UserBot, bot_id)
    if not bot or bot.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    query = select(KeywordResponder).where(KeywordResponder.user_bot_id == bot_id)
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    responders = result.scalars().all()
    
    return KeywordResponderListResponse(
        total=total or 0,
        page=page,
        per_page=per_page,
        pages=((total or 0) + per_page - 1) // per_page,
        items=[KeywordResponderResponse.model_validate(r) for r in responders]
    )


@router.post("/bots/{bot_id}/keywords", response_model=KeywordResponderResponse)
async def create_keyword_responder(
    bot_id: int,
    data: KeywordResponderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a keyword responder."""
    bot = await db.get(UserBot, bot_id)
    if not bot or bot.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    responder = KeywordResponder(
        owner_id=current_user.id,
        user_bot_id=bot_id,
        **data.model_dump()
    )
    db.add(responder)
    await db.commit()
    await db.refresh(responder)
    return KeywordResponderResponse.model_validate(responder)


@router.patch("/bots/{bot_id}/keywords/{keyword_id}", response_model=KeywordResponderResponse)
async def update_keyword_responder(
    bot_id: int,
    keyword_id: int,
    data: KeywordResponderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a keyword responder."""
    responder = await db.get(KeywordResponder, keyword_id)
    if not responder or responder.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Responder not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(responder, field, value)
    
    await db.commit()
    await db.refresh(responder)
    return KeywordResponderResponse.model_validate(responder)


@router.delete("/bots/{bot_id}/keywords/{keyword_id}")
async def delete_keyword_responder(
    bot_id: int,
    keyword_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a keyword responder."""
    responder = await db.get(KeywordResponder, keyword_id)
    if not responder or responder.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Responder not found")
    
    await db.delete(responder)
    await db.commit()
    return {"message": "Responder deleted"}


# ==================== BOT ANALYTICS ====================

@router.get("/bots/{bot_id}/analytics", response_model=BotAnalyticsSummary)
async def get_bot_analytics(
    bot_id: int,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get bot analytics summary."""
    bot = await db.get(UserBot, bot_id)
    if not bot or bot.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Get analytics for the past N days
    start_date = date.today() - timedelta(days=days)
    
    query = select(BotAnalytics).where(
        BotAnalytics.user_bot_id == bot_id,
        BotAnalytics.date >= start_date
    ).order_by(BotAnalytics.date)
    
    result = await db.execute(query)
    analytics = result.scalars().all()
    
    total_messages = sum(a.messages_received + a.messages_sent for a in analytics)
    total_commands = sum(a.commands_used for a in analytics)
    total_users = bot.total_users
    
    # Calculate averages
    avg_daily_messages = total_messages / days if days > 0 else 0
    avg_daily_users = total_users / days if days > 0 else 0
    
    return BotAnalyticsSummary(
        total_messages=total_messages,
        total_commands=total_commands,
        total_users=total_users,
        avg_daily_messages=round(avg_daily_messages, 2),
        avg_daily_users=round(avg_daily_users, 2),
        top_commands=[{"command": "/start", "count": 100}],
        messages_over_time=[{"date": str(a.date), "count": a.messages_received + a.messages_sent} for a in analytics]
    )


@router.get("/bots/{bot_id}/executions", response_model=List[FlowExecutionResponse])
async def get_bot_executions(
    bot_id: int,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recent flow executions."""
    bot = await db.get(UserBot, bot_id)
    if not bot or bot.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    query = select(FlowExecution).where(
        FlowExecution.user_bot_id == bot_id
    ).order_by(FlowExecution.started_at.desc()).limit(limit)
    
    result = await db.execute(query)
    executions = result.scalars().all()
    
    return [FlowExecutionResponse.model_validate(e) for e in executions]
