"""Channels Module - Channel posting and auto-forwarding."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from bot.core.module_base import NexusModule, ModuleCategory
from bot.core.context import NexusContext
from shared.models import ChannelConfig, AutoForward


class ChannelsModule(NexusModule):
    """Module for channel posting and auto-forwarding."""
    
    name = "channels"
    version = "1.0.0"
    author = "Nexus"
    description = "Post to channels and auto-forward messages"
    category = ModuleCategory.INTEGRATION
    
    config_schema = None
    default_config = {}
    
    commands = [
        {"name": "channel", "description": "Manage channels", "admin_only": True},
        {"name": "forward", "description": "Manage auto-forwarding", "admin_only": True},
        {"name": "broadcast", "description": "Broadcast to all channels", "admin_only": True},
    ]
    
    def __init__(self):
        super().__init__()
        self.channel_configs: Dict[int, List[ChannelConfig]] = {}
        self.forward_rules: Dict[int, List[AutoForward]] = {}
    
    async def on_load(self, app):
        """Load the module."""
        self.bot = app
        await self._load_channels()
        await self._load_forwards()
    
    async def _load_channels(self):
        """Load channel configurations."""
        # Would load from database
        pass
    
    async def _load_forwards(self):
        """Load forward rules."""
        # Would load from database
        pass
    
    async def on_message(self, ctx: NexusContext) -> None:
        """Handle message for channel posting."""
        if not ctx.message:
            return
        
        chat_id = ctx.message.chat.id
        
        # Check if there are auto-post rules for this chat
        if chat_id in self.channel_configs:
            for config in self.channel_configs[chat_id]:
                if config.auto_post_enabled and config.is_active:
                    await self._post_to_channel(ctx, config)
        
        # Check auto-forward rules
        if chat_id in self.forward_rules:
            for forward in self.forward_rules[chat_id]:
                if forward.is_active:
                    await self._forward_message(ctx, forward)
    
    async def _post_to_channel(self, ctx: NexusContext, config: ChannelConfig):
        """Post a message to a channel."""
        if not ctx.message:
            return
        
        # Format the message
        content = ctx.message.text or ""
        
        if config.format_template:
            content = config.format_template.format(
                user=ctx.user.user.first_name,
                username=ctx.user.user.username or "N/A",
                chat=ctx.message.chat.title or "Chat",
                text=content,
                date=datetime.now().strftime("%Y-%m-%d %H:%M")
            )
        
        # Add source info if enabled
        if config.include_source:
            content = f"📢 {ctx.message.chat.title}\n\n{content}"
        
        # Send to channel
        try:
            await ctx.bot.send_message(config.channel_id, content)
            config.total_posts += 1
        except Exception as e:
            await ctx.notify_admins(f"Channel post failed: {e}")
    
    async def _forward_message(self, ctx: NexusContext, forward: AutoForward):
        """Forward a message to another chat."""
        if not ctx.message:
            return
        
        try:
            await ctx.bot.forward_message(
                forward.dest_chat_id,
                forward.source_chat_id,
                ctx.message.message_id
            )
            
            forward.total_forwarded += 1
            
            # Add caption if specified
            if forward.add_caption:
                await ctx.bot.send_message(
                    forward.dest_chat_id,
                    forward.add_caption.format(
                        user=ctx.user.user.first_name,
                        original_chat=ctx.message.chat.title
                    )
                )
        except Exception as e:
            pass  # Silently fail for forwards
    
    async def on_command_channel(self, ctx: NexusContext) -> None:
        """Handle /channel command."""
        await ctx.reply("Use the Mini App to manage your channels with auto-post and formatting!")
    
    async def on_command_forward(self, ctx: NexusContext) -> None:
        """Handle /forward command."""
        await ctx.reply("Use the Mini App to set up auto-forwarding between chats!")
    
    async def on_command_broadcast(self, ctx: NexusContext) -> None:
        """Handle /broadcast command."""
        if not ctx.message:
            return
        
        text = ctx.message.text.replace("/broadcast", "").strip()
        
        if not text:
            await ctx.reply("Usage: /broadcast <message>")
            return
        
        # Get user's channels
        channels = self.channel_configs.get(ctx.user.user.telegram_id, [])
        
        if not channels:
            await ctx.reply("No channels configured!")
            return
        
        success = 0
        failed = 0
        
        for channel in channels:
            try:
                await ctx.bot.send_message(channel.channel_id, text)
                success += 1
            except:
                failed += 1
        
        await ctx.reply(f"Broadcast complete!\n✅ Success: {success}\n❌ Failed: {failed}")


# Create module instance
module = ChannelsModule()
