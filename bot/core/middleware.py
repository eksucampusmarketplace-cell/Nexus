"""Middleware pipeline for processing updates."""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, List, Optional

from aiogram import Bot
from aiogram.types import ReplyParameters, Update
from aiogram.utils.markdown import hbold, hcode, hitalic
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

logger = logging.getLogger(__name__)


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

    async def _handle_private_command(self, bot: Bot, update: Update) -> bool:
        """Handle slash commands sent in private chat without a DB session."""
        if not update.message or update.message.chat.type != "private":
            return False

        if not update.message.text or not update.message.text.startswith("/"):
            return False

        parts = update.message.text.split()
        command = parts[0].lower().split("@")[0].lstrip("/")
        
        logger.info(f"Handling private command: /{command} from user {update.message.from_user.id}")

        if command == "start":
            text = f"👋 {hbold('Welcome to Nexus Bot!')} 🚀\n\n"
            text += f"{hbold('The Ultimate Telegram Bot Platform')} 🎉\n\n"
            text += f"📚 {hcode('/help')} - View all commands\n"
            text += f"📱 {hcode('/settings')} - Open settings panel\n"
            text += "ℹ️ Use commands or open the Mini App for full control!\n\n"
            text += f"💡 {hitalic('Type /help <command> for detailed information')}"
            try:
                await bot.send_message(
                    chat_id=update.message.chat.id,
                    text=text,
                    reply_parameters=ReplyParameters(message_id=update.message.message_id),
                    parse_mode="HTML",
                )
                logger.info(f"Sent /start response to chat {update.message.chat.id}")
            except Exception as e:
                logger.error(f"Failed to send /start response: {e}")
            return True

        if command == "help":
            from bot.modules.help.module import (
                ALIAS_MAP, CATEGORIES, CATEGORY_ICONS, COMMAND_DETAILS,
                ADMIN_COMMANDS, _resolve_command, _find_category,
            )
            args = parts[1:]
            if args:
                query = args[0].lower().lstrip("/")
                matched_cat = next((c for c in CATEGORIES if c.lower() == query), None)
                if matched_cat:
                    cmds = CATEGORIES[matched_cat]
                    icon = CATEGORY_ICONS.get(matched_cat, "📦")
                    text = f"{icon} {hbold(matched_cat + ' Commands')}\n\n"
                    for cmd in cmds:
                        lock = "🔒 " if cmd in ADMIN_COMMANDS else ""
                        text += f"{lock}{hcode('/' + cmd)}\n"
                    text += f"\n💡 Use {hcode('/help <command>')} for details."
                else:
                    canonical = _resolve_command(query)
                    if canonical:
                        details = COMMAND_DETAILS.get(canonical, {})
                        usage = details.get("usage", f"/{canonical}")
                        examples = details.get("examples", [])
                        category = _find_category(canonical)
                        is_admin = canonical in ADMIN_COMMANDS
                        aliases = sorted(a for a, t in ALIAS_MAP.items() if t == canonical)
                        text = f"📚 {hbold(f'/{canonical}')}\n"
                        text += f"📂 {hbold('Category:')} {category or 'General'}\n\n"
                        text += f"🔧 {hbold('Usage:')}\n{hcode(usage)}\n\n"
                        if examples:
                            text += f"📌 {hbold('Examples:')}\n"
                            for ex in examples:
                                text += f"• {hcode(ex)}\n"
                            text += "\n"
                        if aliases:
                            text += f"🔀 {hbold('Aliases:')}\n"
                            for alias in aliases:
                                text += f"• {hcode('/' + alias)}\n"
                            text += "\n"
                        perm = "🔒 Admin Only" if is_admin else "✅ Everyone"
                        text += f"{hbold('Permissions:')} {perm}\n"
                    else:
                        text = (
                            f"❌ Command {hcode(query)} not found.\n\n"
                            f"Use {hcode('/help')} to see all categories."
                        )
            else:
                text = f"{hbold('📚 Nexus Bot Help')}\n\n"
                text += f"Use {hcode('/help <command>')} for command details.\n"
                text += f"Use {hcode('/help <category>')} to list commands in a category.\n\n"
                text += f"{hbold('Categories:')}\n\n"
                for i, (cat, cmds) in enumerate(CATEGORIES.items(), 1):
                    icon = CATEGORY_ICONS.get(cat, "📦")
                    text += f"{i}. {icon} {hbold(cat)} — {len(cmds)} commands\n"
                text += "\n💡 Add me to a group to enable all features!"
            try:
                await bot.send_message(
                    chat_id=update.message.chat.id,
                    text=text,
                    reply_parameters=ReplyParameters(message_id=update.message.message_id),
                    parse_mode="HTML",
                )
                logger.info(f"Sent /help response to chat {update.message.chat.id}")
            except Exception as e:
                logger.error(f"Failed to send /help response: {e}")
            return True

        if command == "ping":
            try:
                await bot.send_message(
                    chat_id=update.message.chat.id,
                    text="🏓 Pong!",
                    reply_parameters=ReplyParameters(message_id=update.message.message_id),
                )
                logger.info(f"Sent /ping response to chat {update.message.chat.id}")
            except Exception as e:
                logger.error(f"Failed to send /ping response: {e}")
            return True

        if command == "about":
            text = f"🤖 {hbold('Nexus Bot')} v1.0.0\n\n"
            text += f"{hbold('The Ultimate Telegram Bot Platform')} 🚀\n\n"
            text += f"• 27 production-ready modules\n"
            text += f"• 230+ documented commands\n"
            text += f"• AI-powered assistant\n"
            text += f"• Economy, games, moderation & more\n\n"
            text += f"Add me to a group and type {hcode('/help')} to get started!"
            try:
                await bot.send_message(
                    chat_id=update.message.chat.id,
                    text=text,
                    reply_parameters=ReplyParameters(message_id=update.message.message_id),
                    parse_mode="HTML",
                )
                logger.info(f"Sent /about response to chat {update.message.chat.id}")
            except Exception as e:
                logger.error(f"Failed to send /about response: {e}")
            return True

        # Unknown private command — give a hint
        logger.info(f"Unknown command /{command}, sending hint")
        try:
            await bot.send_message(
                chat_id=update.message.chat.id,
                text=f"ℹ️ Use {hcode('/help')} to see available commands, or add me to a group for full features.",
                reply_parameters=ReplyParameters(message_id=update.message.message_id),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send unknown command hint: {e}")
        return True

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
        logger.debug(f"process_update called, modules loaded: {len(self._modules)}")
        
        # Handle private chat slash commands without requiring DB
        if update.message and update.message.chat.type == "private":
            logger.info(f"Routing to private command handler for chat {update.message.chat.id}")
            result = await self._handle_private_command(bot, update)
            logger.info(f"Private command handler result: {result}")
            return result

        # Create database session for group updates
        try:
            logger.debug("Creating database session for group update")
            async with AsyncSessionLocal() as session:
                # Build context
                ctx = await self._build_context(session, bot, bot_identity, update)

                if not ctx:
                    logger.warning("Failed to build context - ctx is None")
                    return False

                logger.debug(f"Context built: group={ctx.group.id if ctx.group else None}, user={ctx.user.telegram_id if ctx.user else None}")

                # Run middleware pipeline
                for i, middleware in enumerate(self._middlewares):
                    try:
                        logger.debug(f"Running middleware {i}: {middleware.__name__ if hasattr(middleware, '__name__') else 'unknown'}")
                        should_continue = await middleware(ctx)
                        if not should_continue:
                            logger.info(f"Middleware {i} returned False, stopping pipeline")
                            return False
                    except Exception as e:
                        logger.error(f"Middleware error: {e}")
                        continue

                # Route to modules
                logger.debug(f"Routing to modules ({len(self._modules)} modules loaded)")
                result = await self._route_to_modules(ctx)
                logger.debug(f"Module routing result: {result}")
                return result
        except Exception as e:
            logger.exception(f"Pipeline error: {e}")
            return False

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

    def _is_module_enabled(self, module: NexusModule, group_id: int, enabled_modules: list) -> bool:
        """Check if a module is enabled for a group.

        Falls back to True (all modules on by default) if no explicit config exists.
        """
        if module.is_enabled_for(group_id):
            return True
        # If there's an explicit enabled_modules list, respect it
        if enabled_modules:
            return module.name in enabled_modules
        # No config yet — treat all modules as enabled by default
        return True

    async def _route_to_modules(self, ctx: NexusContext) -> bool:
        """Route the update to appropriate modules."""
        if not ctx.group:
            return False

        enabled_modules = ctx.group.enabled_modules if ctx.group else []

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

        # For slash commands in groups, dispatch to module command handlers
        if event_type == EventType.MESSAGE and ctx.message and ctx.message.text:
            text = ctx.message.text.strip()
            if text.startswith("/"):
                parts = text.split()
                command = parts[0].lower().split("@")[0].lstrip("/")
                for module in self._modules:
                    if not self._is_module_enabled(module, ctx.group.id, enabled_modules):
                        continue
                    if command in module._command_handlers:
                        try:
                            await module._command_handlers[command](ctx)
                            return True
                        except Exception as e:
                            print(f"Command handler error in {module.name}.{command}: {e}")
                            return False

        # Route to modules for event handling
        handled = False
        for module in self._modules:
            if not self._is_module_enabled(module, ctx.group.id, enabled_modules):
                continue

            # Check dependencies
            deps_satisfied = all(
                any(
                    m.name == dep and self._is_module_enabled(m, ctx.group.id, enabled_modules)
                    for m in self._modules
                )
                for dep in module.dependencies
            )
            if not deps_satisfied:
                continue

            # Check conflicts
            has_conflict = any(
                any(
                    m.name == conflict and self._is_module_enabled(m, ctx.group.id, enabled_modules)
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
