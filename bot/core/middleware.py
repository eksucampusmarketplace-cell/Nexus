"""Middleware pipeline for processing updates."""

from dataclasses import dataclass
from typing import Any, Callable, Coroutine, List, Optional

from aiogram import Bot
from aiogram.types import Update
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.context import (
    BotIdentity,
    GroupProfile,
    MemberProfile,
    NexusContext,
)
from bot.core.module_base import EventType, NexusModule
from bot.core.prefix_parser import prefix_parser
from shared.database import AsyncSessionLocal
from shared.models import Group, Member, ModuleConfig, User
from shared.redis_client import RateLimiter, get_group_redis
from shared.schemas import Role


@dataclass
class ParsedMessage:
    """Parsed message with command info."""

    is_command: bool = False
    is_deactivate: bool = False
    command: Optional[str] = None
    args: List[str] = None
    duration: Optional[int] = None
    time_range: Optional[tuple] = None

    def __post_init__(self):
        if self.args is None:
            self.args = []


MiddlewareFunc = Callable[[NexusContext], Coroutine[Any, Any, bool]]


class MiddlewarePipeline:
    """Middleware pipeline for processing Telegram updates."""

    def __init__(self):
        self._middlewares: List[MiddlewareFunc] = []
        self._modules: List[NexusModule] = []

    def add_middleware(self, middleware: MiddlewareFunc) -> None:
        """Add a middleware to the pipeline."""
        self._middlewares.append(middleware)

    def add_module(self, module: NexusModule) -> None:
        """Add a module to handle events."""
        self._modules.append(module)

    async def process_update(
        self,
        bot: Bot,
        bot_identity: BotIdentity,
        update: Update,
    ) -> bool:
        """
        Process an update through the middleware pipeline.

        Returns True if the update was handled, False otherwise.
        """
        # Create database session
        async with AsyncSessionLocal() as session:
            # Build context
            ctx = await self._build_context(session, bot, bot_identity, update)

            if not ctx:
                return False

            # Run middleware pipeline
            for middleware in self._middlewares:
                try:
                    should_continue = await middleware(ctx)
                    if not should_continue:
                        return False
                except Exception as e:
                    print(f"Middleware error: {e}")
                    continue

            # Route to modules
            return await self._route_to_modules(ctx)

    async def _build_context(
        self,
        session: AsyncSession,
        bot: Bot,
        bot_identity: BotIdentity,
        update: Update,
    ) -> Optional[NexusContext]:
        """Build NexusContext from update."""
        # Get user info from update
        telegram_user = None
        telegram_chat = None

        if update.message:
            telegram_user = update.message.from_user
            telegram_chat = update.message.chat
        elif update.callback_query:
            telegram_user = update.callback_query.from_user
            telegram_chat = (
                update.callback_query.message.chat
                if update.callback_query.message
                else None
            )
        elif update.inline_query:
            telegram_user = update.inline_query.from_user
        elif update.edited_message:
            telegram_user = update.edited_message.from_user
            telegram_chat = update.edited_message.chat
        elif update.chat_member:
            telegram_user = update.chat_member.from_user
            telegram_chat = update.chat_member.chat

        if not telegram_user:
            return None

        # Get or create user
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_user.id)
        )
        user = result.scalar()

        if not user:
            user = User(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
                is_bot=telegram_user.is_bot,
            )
            session.add(user)
            await session.flush()

        # Get group info
        group = None
        member = None

        if telegram_chat and telegram_chat.type in ["group", "supergroup"]:
            result = await session.execute(
                select(Group).where(Group.telegram_id == telegram_chat.id)
            )
            group = result.scalar()

            if not group:
                group = Group(
                    telegram_id=telegram_chat.id,
                    title=telegram_chat.title,
                    username=telegram_chat.username,
                )
                session.add(group)
                await session.flush()

            # Get or create member
            result = await session.execute(
                select(Member).where(
                    Member.user_id == user.id,
                    Member.group_id == group.id,
                )
            )
            member = result.scalar()

            if not member:
                # Determine role
                role = Role.MEMBER
                if telegram_chat.id == telegram_user.id:
                    role = Role.OWNER
                else:
                    # Check if user is admin
                    try:
                        chat_member = await bot.get_chat_member(
                            telegram_chat.id, telegram_user.id
                        )
                        if chat_member.status == "creator":
                            role = Role.OWNER
                        elif chat_member.status == "administrator":
                            role = Role.ADMIN
                    except Exception:
                        pass

                member = Member(
                    user_id=user.id,
                    group_id=group.id,
                    role=role.value,
                )
                session.add(member)
                await session.flush()

        # Get group profile
        group_profile = None
        if group:
            enabled_modules = []
            module_configs = {}

            result = await session.execute(
                select(ModuleConfig).where(
                    ModuleConfig.group_id == group.id,
                    ModuleConfig.is_enabled.is_(True),
                )
            )
            configs = result.scalars().all()

            for config in configs:
                enabled_modules.append(config.module_name)
                module_configs[config.module_name] = config.config

            group_profile = GroupProfile(
                id=group.id,
                telegram_id=group.telegram_id,
                title=group.title,
                username=group.username,
                language=group.language,
                owner_id=group.owner_id,
                member_count=group.member_count,
                is_premium=group.is_premium,
                enabled_modules=enabled_modules,
                module_configs=module_configs,
            )

        # Get member profile
        member_profile = None
        if member and user:
            member_profile = MemberProfile(
                id=member.id,
                user_id=user.id,
                group_id=member.group_id,
                telegram_id=user.telegram_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                role=Role(member.role),
                trust_score=member.trust_score,
                xp=member.xp,
                level=member.level,
                warn_count=member.warn_count,
                is_muted=member.is_muted,
                is_banned=member.is_banned,
                is_approved=member.is_approved,
                is_whitelisted=member.is_whitelisted,
                joined_at=member.joined_at,
                message_count=member.message_count,
                custom_title=member.custom_title,
            )

        # Get cache
        cache = None
        if group:
            cache = await get_group_redis(group.id)

        # Create context
        ctx = await NexusContext.create(
            bot=bot,
            bot_identity=bot_identity,
            update=update,
            user=member_profile,
            group=group_profile,
            db=session,
            cache=cache,
        )

        return ctx

    async def _route_to_modules(self, ctx: NexusContext) -> bool:
        """Route the update to appropriate modules."""
        if not ctx.group:
            return False

        # Determine event type
        event_type = None
        if ctx.message:
            if ctx.message.new_chat_members:
                event_type = EventType.NEW_MEMBER
            elif ctx.message.left_chat_member:
                event_type = EventType.LEFT_MEMBER
            else:
                event_type = EventType.MESSAGE
        elif ctx.callback_query:
            event_type = EventType.CALLBACK
        elif ctx.inline_query:
            event_type = EventType.INLINE

        if not event_type:
            return False

        # Route to modules
        handled = False
        for module in self._modules:
            # Check if module is enabled for this group
            if not module.is_enabled_for(ctx.group.id):
                continue

            # Check dependencies
            deps_satisfied = all(
                any(
                    m.name == dep and m.is_enabled_for(ctx.group.id)
                    for m in self._modules
                )
                for dep in module.dependencies
            )
            if not deps_satisfied:
                continue

            # Check conflicts
            has_conflict = any(
                any(
                    m.name == conflict and m.is_enabled_for(ctx.group.id)
                    for m in self._modules
                )
                for conflict in module.conflicts
            )
            if has_conflict:
                continue

            # Handle event
            try:
                if event_type == EventType.MESSAGE:
                    result = await module.on_message(ctx)
                    handled = handled or result
                elif event_type == EventType.EDITED_MESSAGE:
                    result = await module.on_edited_message(ctx)
                    handled = handled or result
                elif event_type == EventType.NEW_MEMBER:
                    result = await module.on_new_member(ctx)
                    handled = handled or result
                elif event_type == EventType.LEFT_MEMBER:
                    result = await module.on_left_member(ctx)
                    handled = handled or result
                elif event_type == EventType.CALLBACK:
                    result = await module.on_callback_query(ctx)
                    handled = handled or result
                elif event_type == EventType.INLINE:
                    result = await module.on_inline_query(ctx)
                    handled = handled or result
            except Exception as e:
                print(f"Module error in {module.name}: {e}")
                continue

        return handled


# Global pipeline instance
pipeline = MiddlewarePipeline()


# Middleware functions
async def auth_middleware(ctx: NexusContext) -> bool:
    """Authenticate and authorize the user."""
    if not ctx.user:
        return False
    return True


async def trust_score_middleware(ctx: NexusContext) -> bool:
    """Enrich context with trust score."""
    if ctx.cache and ctx.user:
        # Cache trust score
        cache_key = f"trust:{ctx.user.user_id}"
        cached = await ctx.cache.get(cache_key)
        if cached:
            ctx.user.trust_score = int(cached)
    return True


async def rate_limit_middleware(ctx: NexusContext) -> bool:
    """Apply rate limiting."""
    if not ctx.cache or not ctx.user:
        return True

    limiter = RateLimiter(ctx.cache)
    key = f"user:{ctx.user.user_id}:commands"
    allowed, remaining, reset = await limiter.is_allowed(key, limit=30, window=60)

    if not allowed:
        await ctx.reply("⚠️ Rate limit exceeded. Please slow down.")
        return False

    return True


async def antiflood_middleware(ctx: NexusContext) -> bool:
    """Anti-flood protection."""
    if not ctx.cache or not ctx.user or not ctx.group:
        return True

    # Check if antiflood is enabled
    config = ctx.group.module_configs.get("antiflood", {})
    if not config.get("is_enabled", True):
        return True

    limiter = RateLimiter(ctx.cache)
    key = f"flood:{ctx.user.user_id}"
    message_limit = config.get("message_limit", 5)
    window = config.get("window_seconds", 5)

    allowed, _, _ = await limiter.is_allowed(key, limit=message_limit, window=window)

    if not allowed:
        # Flood detected
        action = config.get("action", "mute")
        duration = config.get("action_duration", 300)

        if action == "mute":
            await ctx.mute_user(ctx.user, duration, "Anti-flood triggered", silent=True)
        elif action == "ban":
            await ctx.ban_user(ctx.user, duration, "Anti-flood triggered", silent=True)
        elif action == "kick":
            await ctx.kick_user(ctx.user, "Anti-flood triggered")

        return False

    return True


async def module_config_middleware(ctx: NexusContext) -> bool:
    """Load module configurations."""
    # Config already loaded during context building
    return True


async def prefix_parser_middleware(ctx: NexusContext) -> bool:
    """
    Parse !command and !!command patterns from messages.

    This is a critical middleware that:
    - Parses the dual prefix system (! and !!)
    - Extracts duration, time ranges, and arguments
    - Sets parsed command info on the context
    """
    if not ctx.message or not ctx.message.text:
        return True

    # Get custom prefix for this group (default is !)
    custom_prefix = ctx.group.module_configs.get("settings", {}).get(
        "command_prefix", "!"
    )

    # Parse the message
    parsed = prefix_parser.parse(ctx.message.text, custom_prefix)

    if parsed and parsed.is_valid:
        # Store parsed info in context
        ctx.parsed_command = ParsedMessage(
            is_command=True,
            is_deactivate=parsed.is_deactivate,
            command=parsed.command,
            args=parsed.args,
            duration=parsed.duration,
            time_range=parsed.time_range,
        )
    else:
        ctx.parsed_command = ParsedMessage(is_command=False)

    return True


async def command_router_middleware(ctx: NexusContext) -> bool:
    """
    Route parsed commands to module handlers.

    After prefix_parser_middleware, this routes the command
    to the appropriate module's command handler.
    """
    if not ctx.parsed_command or not ctx.parsed_command.is_command:
        return True

    # The command will be handled by module event handlers
    # This middleware just marks it as a command for routing
    return True


# Setup pipeline
def setup_pipeline():
    """Set up the middleware pipeline in the correct order."""
    # Order matters! Each middleware is run in sequence.
    pipeline.add_middleware(auth_middleware)
    pipeline.add_middleware(trust_score_middleware)
    pipeline.add_middleware(module_config_middleware)
    pipeline.add_middleware(
        prefix_parser_middleware
    )  # Critical: parse ! and !! prefixes
    pipeline.add_middleware(rate_limit_middleware)
    pipeline.add_middleware(antiflood_middleware)
    pipeline.add_middleware(command_router_middleware)
