"""Bot Builder Module - Handles user-created bots and custom commands."""

import re
import random
import json
from typing import Any, Dict, List, Optional

from aiogram import Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.core.module_base import NexusModule, ModuleCategory
from bot.core.context import NexusContext
from shared.database import AsyncSessionLocal
from shared.models import CustomCommand, KeywordResponder, UserBot, BotFlow, FlowExecution
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BotBuilderModule(NexusModule):
    """Module for handling user-created bots and custom commands."""
    
    name = "bot_builder"
    version = "1.0.0"
    author = "Nexus"
    description = "Create and manage custom Telegram bots with flows and commands"
    category = ModuleCategory.UTILITY
    
    config_schema = None
    default_config = {}
    
    commands = [
        {"name": "mybot", "description": "Manage your custom bots", "admin_only": False},
        {"name": "botcommands", "description": "List custom bot commands", "admin_only": False},
        {"name": "addcommand", "description": "Add a custom command", "admin_only": True},
        {"name": "delcommand", "description": "Delete a custom command", "admin_only": True},
        {"name": "addkeyword", "description": "Add keyword auto-responder", "admin_only": True},
        {"name": "delkeyword", "description": "Delete keyword responder", "admin_only": True},
    ]
    
    listeners = ["message", "edited_message", "callback_query"]
    
    def __init__(self):
        super().__init__()
        self.command_cache: Dict[int, List[CustomCommand]] = {}
        self.keyword_cache: Dict[int, List[KeywordResponder]] = {}
    
    async def on_load(self, app):
        """Load the module."""
        self.bot = app
        await self._load_commands_cache()
        await self._load_keywords_cache()
    
    async def _load_commands_cache(self):
        """Load custom commands into cache."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(CustomCommand))
            commands = result.scalars().all()
            
            for cmd in commands:
                if cmd.user_bot_id:
                    if cmd.user_bot_id not in self.command_cache:
                        self.command_cache[cmd.user_bot_id] = []
                    self.command_cache[cmd.user_bot_id].append(cmd)
    
    async def _load_keywords_cache(self):
        """Load keyword responders into cache."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(KeywordResponder).where(KeywordResponder.is_active == True))
            responders = result.scalars().all()
            
            for responder in responders:
                if responder.user_bot_id:
                    if responder.user_bot_id not in self.keyword_cache:
                        self.keyword_cache[responder.user_bot_id] = []
                    self.keyword_cache[responder.user_bot_id].append(responder)
    
    async def on_message(self, ctx: NexusContext) -> None:
        """Handle incoming messages for custom bot processing."""
        if not ctx.message or not ctx.message.text:
            return
        
        text = ctx.message.text
        user_id = ctx.user.user.telegram_id
        
        # Check for custom commands (starts with /)
        if text.startswith('/'):
            await self._handle_command(ctx, text)
        else:
            # Check for keyword responders
            await self._handle_keywords(ctx, text)
    
    async def _handle_command(self, ctx: NexusContext, text: str) -> None:
        """Handle custom bot commands."""
        # Extract command and args
        parts = text.split(' ', 1)
        command = parts[0][1:].lower()  # Remove /
        args = parts[1] if len(parts) > 1 else None
        
        # Get user's bots
        user_id = ctx.user.user.telegram_id
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UserBot).where(
                    UserBot.owner_id == ctx.user.user.id,
                    UserBot.is_active == True
                )
            )
            bots = result.scalars().all()
            
            for bot in bots:
                commands = self.command_cache.get(bot.id, [])
                
                for cmd in commands:
                    if cmd.command.lower() == command:
                        # Execute command
                        await self._execute_command(ctx, cmd, args)
                        return
    
    async def _execute_command(self, ctx: NexusContext, cmd: CustomCommand, args: Optional[str]):
        """Execute a custom command."""
        content = cmd.response_content
        
        # Replace variables
        if cmd.allow_variables:
            content = content.replace('{user}', ctx.user.user.first_name)
            content = content.replace('{username}', f"@{ctx.user.user.username}" if ctx.user.user.username else "N/A")
            content = content.replace('{id}', str(ctx.user.user.telegram_id))
            content = content.replace('{args}', args or "")
        
        # Send response
        if cmd.response_type == "text":
            await ctx.reply(content, parse_mode="Markdown")
        elif cmd.response_type == "photo" and cmd.response_media:
            await ctx.reply_media(cmd.response_media, caption=content)
        elif cmd.response_type == "sticker" and cmd.response_media:
            await ctx.bot.send_sticker(ctx.message.chat.id, cmd.response_media)
        
        # Update usage count
        cmd.usage_count += 1
    
    async def _handle_keywords(self, ctx: NexusContext, text: str) -> None:
        """Handle keyword-based auto-responders."""
        user_id = ctx.user.user.telegram_id
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UserBot).where(
                    UserBot.owner_id == ctx.user.user.id,
                    UserBot.is_active == True
                )
            )
            bots = result.scalars().all()
            
            for bot in bots:
                responders = self.keyword_cache.get(bot.id, [])
                
                for responder in responders:
                    if await self._matches_keyword(responder, text):
                        # Random response if multiple
                        response = random.choice(responder.responses) if responder.random_response else responder.responses[0]
                        
                        # Send response
                        await ctx.reply(response)
                        
                        # Delete trigger if enabled
                        if responder.delete_trigger:
                            await ctx.delete_message()
                        
                        # Update trigger count
                        responder.trigger_count += 1
                        break  # Only first matching responder
    
    async def _matches_keyword(self, responder: KeywordResponder, text: str) -> bool:
        """Check if text matches any keyword in the responder."""
        text_to_check = text if responder.case_sensitive else text.lower()
        
        for keyword in responder.keywords:
            kw = keyword if responder.case_sensitive else keyword.lower()
            
            if responder.match_type == "exact":
                if text_to_check == kw:
                    return True
            elif responder.match_type == "contains":
                if kw in text_to_check:
                    return True
            elif responder.match_type == "startswith":
                if text_to_check.startswith(kw):
                    return True
            elif responder.match_type == "endswith":
                if text_to_check.endswith(kw):
                    return True
            elif responder.match_type == "regex":
                try:
                    if re.search(kw, text_to_check):
                        return True
                except:
                    pass
        
        return False
    
    async def on_command_mybot(self, ctx: NexusContext) -> None:
        """Handle /mybot command - show user's bots."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UserBot).where(UserBot.owner_id == ctx.user.user.id)
            )
            bots = result.scalars().all()
        
        if not bots:
            await ctx.reply("You don't have any bots yet. Create one from the Mini App!")
            return
        
        text = "Your Bots:\n\n"
        for bot in bots:
            status = "✅ Active" if bot.is_active else "⏸️ Stopped"
            text += f"• {bot.name} ({status})\n"
            text += f"  Username: @{bot.username or 'Not set'}\n"
            text += f"  Messages: {bot.total_messages}\n\n"
        
        await ctx.reply(text)
    
    async def on_command_botcommands(self, ctx: NexusContext) -> None:
        """Handle /botcommands - list available commands."""
        # This would show commands for user's bots
        await ctx.reply("Use the Mini App to manage your bot commands!")
    
    async def on_command_addcommand(self, ctx: NexusContext) -> None:
        """Handle /addcommand - add a custom command."""
        await ctx.reply("Use the Mini App to add custom commands with full formatting support!")
    
    async def on_command_delcommand(self, ctx: NexusContext) -> None:
        """Handle /delcommand - delete a custom command."""
        await ctx.reply("Use the Mini App to manage your custom commands!")
    
    async def on_command_addkeyword(self, ctx: NexusContext) -> None:
        """Handle /addkeyword - add keyword responder."""
        await ctx.reply("Use the Mini App to add keyword responders with full control!")
    
    async def on_command_delkeyword(self, ctx: NexusContext) -> None:
        """Handle /delkeyword - delete keyword responder."""
        await ctx.reply("Use the Mini App to manage your keyword responders!")


# Create module instance
module = BotBuilderModule()
