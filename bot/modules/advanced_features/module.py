"""
Advanced Features Module - Integration of all advanced systems.

This module provides:
- Interactive keyboard state management
- Advanced poll system with vote actions
- Thread-aware conversation context
- Smart notification system
- Conversation flows
- Content moderation pipeline
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule, EventType
from bot.core.keyboard_state import (
    get_keyboard_state_manager,
    InteractiveKeyboardBuilder,
    KeyboardCallbackRouter,
)
from bot.core.thread_context import ThreadContextManager, ThreadAwareContext
from bot.core.notification_system import (
    get_notification_manager,
    NotificationRule,
    NotificationChannel,
    NotificationPriority,
    ActionCategory,
    QuietHours,
    NotificationDelivery,
)
from bot.core.conversation_flow import FlowEngine, create_report_flow, create_onboarding_flow
from bot.core.content_pipeline import ContentPipeline


class AdvancedFeaturesConfig(BaseModel):
    """Configuration for advanced features module."""
    enabled: bool = True
    enable_threading: bool = True
    enable_smart_notifications: bool = True
    enable_flows: bool = True
    enable_content_pipeline: bool = True
    notification_default_channel: str = "log_channel"
    thread_auto_create: bool = True
    content_pipeline_mode: str = "async"  # async, sync, disabled


class AdvancedFeaturesModule(NexusModule):
    """
    Advanced Features Module - Integration layer for all advanced systems.
    """
    
    name = "advanced_features"
    version = "2.0.0"
    author = "Nexus Team"
    description = "Advanced keyboard state, threading, notifications, flows, and content moderation"
    category = ModuleCategory.UTILITY
    
    config_schema = AdvancedFeaturesConfig
    default_config = AdvancedFeaturesConfig().dict()
    
    listeners = [EventType.MESSAGE, EventType.CALLBACK, EventType.EDITED_MESSAGE]
    
    commands = [
        CommandDef(
            name="thread",
            description="Manage conversation threads",
            admin_only=False,
            args="[info|list|summarize]",
        ),
        CommandDef(
            name="threadadmin",
            description="Thread moderation commands",
            admin_only=True,
            args="<lock|unlock|archive|pin> [thread_id]",
        ),
        CommandDef(
            name="notifyconfig",
            description="Configure notification rules",
            admin_only=True,
            args="<add|remove|list>",
        ),
        CommandDef(
            name="polladv",
            description="Create advanced poll with vote actions",
            admin_only=True,
            args="<question> [options...] [--action=ban,mute] [--threshold=70%]",
        ),
        CommandDef(
            name="reportflow",
            description="Start user report flow",
            admin_only=False,
        ),
        CommandDef(
            name="onboarding",
            description="Trigger onboarding flow for a user",
            admin_only=True,
            args="@username",
        ),
        CommandDef(
            name="contentcheck",
            description="Check content against moderation pipeline",
            admin_only=True,
            args="[text to check]",
        ),
    ]
    
    def __init__(self):
        super().__init__()
        self._keyboard_routers: Dict[int, KeyboardCallbackRouter] = {}
        self._thread_managers: Dict[int, ThreadContextManager] = {}
        self._notification_managers = {}
        self._flow_engines: Dict[int, FlowEngine] = {}
        self._content_pipelines: Dict[int, ContentPipeline] = {}
    
    async def on_load(self, app):
        """Initialize all advanced systems."""
        self.register_command("thread", self.cmd_thread)
        self.register_command("threadadmin", self.cmd_thread_admin)
        self.register_command("notifyconfig", self.cmd_notify_config)
        self.register_command("polladv", self.cmd_poll_advanced)
        self.register_command("reportflow", self.cmd_report_flow)
        self.register_command("onboarding", self.cmd_onboarding)
        self.register_command("contentcheck", self.cmd_content_check)
        
        print(f"Loaded {self.name} with advanced systems")
    
    async def on_enable(self, group_id: int):
        """Set up advanced systems for a group."""
        await super().on_enable(group_id)
        
        # Initialize systems
        await self._get_keyboard_router(group_id)
        await self._get_thread_manager(group_id)
        await self._get_notification_manager(group_id)
        await self._get_flow_engine(group_id)
        await self._get_content_pipeline(group_id)
        
        # Set up default notification rules
        await self._setup_default_notifications(group_id)
    
    async def on_message(self, ctx: NexusContext) -> bool:
        """Handle messages with threading and content pipeline."""
        if not ctx.message or not ctx.group:
            return False
        
        group_id = ctx.group.id
        config = ctx.group.module_configs.get("advanced_features", {})
        
        # Content pipeline processing
        if config.get("enable_content_pipeline", True):
            pipeline = await self._get_content_pipeline(group_id)
            record = await pipeline.process_message(ctx.message, group_id)
            
            # Store in context for potential moderation action
            ctx.message._content_record = record
            
            # If decision requires action, take it
            if record.decision and record.decision.decision != "allow":
                await self._handle_content_decision(ctx, record)
        
        # Thread detection and management
        if config.get("enable_threading", True):
            manager = await self._get_thread_manager(group_id)
            
            # Detect or create thread
            thread, is_new = await manager.detect_or_create_thread(
                group_id=group_id,
                message=ctx.message,
                user_role=ctx.user.role.value if ctx.user else "member",
            )
            
            if thread and is_new:
                # New thread created - could notify or log
                pass
        
        # Flow handling
        if config.get("enable_flows", True):
            engine = await self._get_flow_engine(group_id)
            handled = await engine.handle_message(ctx.message)
            if handled:
                return True
        
        return False
    
    async def on_callback_query(self, ctx: NexusContext) -> bool:
        """Handle callback queries with keyboard routing and flows."""
        if not ctx.callback_query:
            return False
        
        group_id = ctx.group.id if ctx.group else 0
        
        # Try flow engine first
        engine = await self._get_flow_engine(group_id)
        handled = await engine.handle_callback(ctx.callback_query)
        if handled:
            return True
        
        # Try keyboard router
        router = await self._get_keyboard_router(group_id)
        handled = await router.handle(ctx.callback_query)
        if handled:
            return True
        
        return False
    
    async def cmd_thread(self, ctx: NexusContext):
        """Thread management command."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []
        action = args[0] if args else "info"
        
        manager = await self._get_thread_manager(ctx.group.id)
        
        if action == "info":
            # Get current thread info
            thread_ctx = ThreadAwareContext(ctx, manager)
            thread = await thread_ctx.get_current_thread()
            
            if not thread:
                await ctx.reply("You're not currently in a recognized conversation thread.")
                return
            
            stats = thread.get_participant_stats()
            flow = thread.get_conversation_flow()
            
            text = f"🧵 <b>Thread Info</b>\n\n"
            text += f"ID: <code>{thread.thread_id}</code>\n"
            text += f"Type: {thread.thread_type.value}\n"
            text += f"Messages: {thread.message_count}\n"
            text += f"Participants: {thread.unique_participants}\n"
            text += f"Started: {thread.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            
            if thread.summary:
                text += f"\n<b>Summary:</b>\n{thread.summary.summary_text[:200]}..."
            
            # Keyboard actions
            buttons = [
                [
                    {"text": "📊 Stats", "callback_data": f"thread_stats:{thread.thread_id}"},
                    {"text": "📝 Summarize", "callback_data": f"thread_summarize:{thread.thread_id}"},
                ]
            ]
            
            await ctx.reply(text, buttons=buttons)
        
        elif action == "list":
            threads = await manager.get_active_threads(limit=10)
            
            if not threads:
                await ctx.reply("No active threads found.")
                return
            
            text = "📋 <b>Active Threads</b>\n\n"
            for i, thread in enumerate(threads[:5], 1):
                text += f"{i}. {thread.title or f'Thread {thread.thread_id[:8]}'} "
                text += f"({thread.message_count} msgs, {thread.unique_participants} users)\n"
            
            await ctx.reply(text)
        
        elif action == "summarize":
            thread_ctx = ThreadAwareContext(ctx, manager)
            summary = await thread_ctx.summarize_current_thread()
            
            if summary:
                await ctx.reply(f"📝 <b>Thread Summary</b>\n\n{summary}")
            else:
                await ctx.reply("Unable to generate summary. Thread may be too short.")
    
    async def cmd_thread_admin(self, ctx: NexusContext):
        """Thread moderation commands."""
        if not ctx.user or not ctx.user.is_admin:
            await ctx.reply("❌ Admin access required.")
            return
        
        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("Usage: /threadadmin <lock|unlock|archive|pin>")
            return
        
        action = args[0]
        manager = await self._get_thread_manager(ctx.group.id)
        
        # Get current thread
        thread_ctx = ThreadAwareContext(ctx, manager)
        thread = await thread_ctx.get_current_thread()
        
        if not thread:
            await ctx.reply("❌ No active thread found.")
            return
        
        success = await manager.moderate_thread(
            thread_id=thread.thread_id,
            action=action,
            moderator_id=ctx.user.user_id,
            reason="Admin action",
        )
        
        if success:
            await ctx.reply(f"✅ Thread {action}ed successfully.")
        else:
            await ctx.reply(f"❌ Failed to {action} thread.")
    
    async def cmd_notify_config(self, ctx: NexusContext):
        """Configure notification rules."""
        if not ctx.user or not ctx.user.is_admin:
            await ctx.reply("❌ Admin access required.")
            return
        
        args = ctx.message.text.split()[1:] if ctx.message.text else []
        action = args[0] if args else "list"
        
        manager = await self._get_notification_manager(ctx.group.id)
        
        if action == "list":
            rules = await manager.get_all_rules()
            
            if not rules:
                await ctx.reply("No notification rules configured.")
                return
            
            text = "🔔 <b>Notification Rules</b>\n\n"
            for rule in rules:
                status = "✅" if rule.enabled else "❌"
                text += f"{status} <b>{rule.rule_id}</b>\n"
                text += f"   Categories: {', '.join(c.value for c in rule.action_categories)}\n"
                text += f"   Channels: {', '.join(c.value for c in rule.channels)}\n"
                text += f"   Priority: {rule.priority.value}\n\n"
            
            await ctx.reply(text)
        
        elif action == "add":
            # Create example rule
            rule = NotificationRule(
                rule_id=f"mod_alert_{ctx.group.id}",
                group_id=ctx.group.id,
                action_categories={ActionCategory.MODERATION, ActionCategory.SECURITY},
                priority=NotificationPriority.HIGH,
                channels=[NotificationChannel.LOG_CHANNEL, NotificationChannel.PRIVATE],
                target_roles={"owner", "admin"},
                quiet_hours=QuietHours(enabled=True, start_time="22:00", end_time="08:00"),
            )
            
            await manager.create_rule(rule)
            await ctx.reply("✅ Created default moderation alert rule.")
        
        elif action == "remove":
            if len(args) < 2:
                await ctx.reply("Usage: /notifyconfig remove <rule_id>")
                return
            
            rule_id = args[1]
            success = await manager.delete_rule(rule_id)
            
            if success:
                await ctx.reply(f"✅ Removed rule {rule_id}")
            else:
                await ctx.reply(f"❌ Rule {rule_id} not found")
    
    async def cmd_poll_advanced(self, ctx: NexusContext):
        """Create an advanced poll with vote actions."""
        if not ctx.user or not ctx.user.is_admin:
            await ctx.reply("❌ Admin access required.")
            return
        
        # This is a simplified version - full implementation would parse args properly
        await ctx.reply(
            "📊 <b>Advanced Poll Creator</b>\n\n"
            "This command creates polls with vote-based actions.\n\n"
            "Example:\n"
            "/polladv \"Should we ban @spammer?\" Yes No --action=ban --threshold=70%\n\n"
            "Actions available: ban, mute, kick, pin, announce"
        )
    
    async def cmd_report_flow(self, ctx: NexusContext):
        """Start user report flow."""
        engine = await self._get_flow_engine(ctx.group.id)
        
        instance = await engine.start_flow(
            flow_id="user_report",
            group_id=ctx.group.id,
            user_id=ctx.user.user_id,
            chat_id=ctx.chat_id,
        )
        
        if not instance:
            # Flow not found, try to create it
            flow = await create_report_flow()
            engine.register_flow(flow)
            
            instance = await engine.start_flow(
                flow_id="user_report",
                group_id=ctx.group.id,
                user_id=ctx.user.user_id,
                chat_id=ctx.chat_id,
            )
        
        if instance:
            await ctx.reply("📝 Starting report flow... Check your DMs or the buttons below.")
        else:
            await ctx.reply("❌ Unable to start report flow.")
    
    async def cmd_onboarding(self, ctx: NexusContext):
        """Trigger onboarding flow for a user."""
        if not ctx.user or not ctx.user.is_admin:
            await ctx.reply("❌ Admin access required.")
            return
        
        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("Usage: /onboarding @username")
            return
        
        # Parse target user
        target = args[0]
        # In real implementation, resolve username to user_id
        
        engine = await self._get_flow_engine(ctx.group.id)
        flow = await create_onboarding_flow()
        engine.register_flow(flow)
        
        await ctx.reply(f"🎓 Onboarding flow would start for {target}")
    
    async def cmd_content_check(self, ctx: NexusContext):
        """Check content against moderation pipeline."""
        if not ctx.user or not ctx.user.is_admin:
            await ctx.reply("❌ Admin access required.")
            return
        
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("Usage: /contentcheck <text to analyze>")
            return
        
        text = args[0]
        
        # Create mock message
        from aiogram.types import Message, User, Chat
        
        mock_message = Message(
            message_id=0,
            date=datetime.utcnow(),
            chat=Chat(id=ctx.chat_id, type="group"),
            from_user=User(id=ctx.user.telegram_id, is_bot=False, first_name="Test"),
            text=text,
        )
        
        pipeline = await self._get_content_pipeline(ctx.group.id)
        record = await pipeline.process_message(mock_message, ctx.group.id)
        
        if record.decision:
            d = record.decision
            text = f"🔍 <b>Content Analysis</b>\n\n"
            text += f"<b>Decision:</b> {d.decision.value.upper()}\n"
            text += f"<b>Risk Level:</b> {d.risk_level.value}\n"
            text += f"<b>Confidence:</b> {d.confidence:.1%}\n"
            text += f"<b>Reason:</b> {d.primary_reason}\n\n"
            
            if d.all_reasons:
                text += "<b>All factors:</b>\n"
                for reason in d.all_reasons[:5]:
                    text += f"• {reason}\n"
            
            await ctx.reply(text)
    
    # Helper methods
    
    async def _get_keyboard_router(self, group_id: int) -> KeyboardCallbackRouter:
        """Get or create keyboard router for group."""
        if group_id not in self._keyboard_routers:
            from bot.core.keyboard_state import get_keyboard_state_manager
            manager = await get_keyboard_state_manager(group_id)
            self._keyboard_routers[group_id] = KeyboardCallbackRouter(manager)
        return self._keyboard_routers[group_id]
    
    async def _get_thread_manager(self, group_id: int) -> ThreadContextManager:
        """Get or create thread manager for group."""
        if group_id not in self._thread_managers:
            from shared.redis_client import get_group_redis
            redis = await get_group_redis(group_id)
            self._thread_managers[group_id] = ThreadContextManager(redis)
        return self._thread_managers[group_id]
    
    async def _get_notification_manager(self, group_id: int):
        """Get or create notification manager for group."""
        if group_id not in self._notification_managers:
            self._notification_managers[group_id] = await get_notification_manager(group_id)
        return self._notification_managers[group_id]
    
    async def _get_flow_engine(self, group_id: int) -> FlowEngine:
        """Get or create flow engine for group."""
        if group_id not in self._flow_engines:
            from shared.redis_client import get_group_redis
            redis = await get_group_redis(group_id)
            # Need to get bot from somewhere - in real implementation inject it
            self._flow_engines[group_id] = FlowEngine(redis, None)
        return self._flow_engines[group_id]
    
    async def _get_content_pipeline(self, group_id: int) -> ContentPipeline:
        """Get or create content pipeline for group."""
        if group_id not in self._content_pipelines:
            from shared.redis_client import get_group_redis
            redis = await get_group_redis(group_id)
            self._content_pipelines[group_id] = ContentPipeline(redis)
        return self._content_pipelines[group_id]
    
    async def _setup_default_notifications(self, group_id: int):
        """Set up default notification rules for a group."""
        manager = await self._get_notification_manager(group_id)
        
        # Critical moderation alerts
        critical_rule = NotificationRule(
            rule_id=f"critical_mod_{group_id}",
            group_id=group_id,
            action_categories={ActionCategory.SECURITY},
            priority=NotificationPriority.CRITICAL,
            channels=[NotificationChannel.PRIVATE],
            target_roles={"owner", "admin"},
        )
        await manager.create_rule(critical_rule)
    
    async def _handle_content_decision(self, ctx: NexusContext, record):
        """Handle a content moderation decision."""
        decision = record.decision
        if not decision:
            return
        
        if decision.decision == "delete":
            await ctx.delete_message(record.message_id)
            await ctx.reply(f"⚠️ Message removed: {decision.primary_reason}")
        
        elif decision.decision == "mute":
            if ctx.target_user:
                await ctx.mute_user(
                    target=ctx.target_user,
                    duration=3600,
                    reason=f"Automated: {decision.primary_reason}",
                )
        
        elif decision.decision in ("kick", "ban"):
            # These would require additional confirmation in practice
            pass
        
        # Send notification
        if decision.requires_review:
            manager = await self._get_notification_manager(ctx.group.id)
            await manager.process_action(
                category=ActionCategory.SECURITY,
                action="content_flagged",
                group_id=ctx.group.id,
                severity=decision.review_priority,
                actor_id=record.user_id,
                context_data={
                    "reason": decision.primary_reason,
                    "risk_level": decision.risk_level.value,
                    "record_id": record.record_id,
                },
            )
