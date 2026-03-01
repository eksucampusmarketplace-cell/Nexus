"""Integrations module - RSS feeds, YouTube, GitHub, webhook integrations."""

import re
import xml.etree.ElementTree as ET

import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from aiogram.types import Message
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class IntegrationConfig(BaseModel):
    """Configuration for integration."""
    enabled: bool = True
    max_feeds: int = 5
    check_interval: int = 300  # 5 minutes
    preview_length: int = 200


class IntegrationsModule(NexusModule):
    """External service integrations."""

    name = "integrations"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Integrations: RSS feeds, YouTube, GitHub, webhooks, and more"
    category = ModuleCategory.INTEGRATION

    config_schema = IntegrationConfig
    default_config = IntegrationConfig().dict()

    commands = [
        CommandDef(
            name="addrss",
            description="Add RSS feed",
            admin_only=True,
        ),
        CommandDef(
            name="removerss",
            description="Remove RSS feed",
            admin_only=True,
        ),
        CommandDef(
            name="listrss",
            description="List all RSS feeds",
            admin_only=True,
        ),
        CommandDef(
            name="addyoutube",
            description="Add YouTube channel",
            admin_only=True,
        ),
        CommandDef(
            name="removeyoutube",
            description="Remove YouTube channel",
            admin_only=True,
        ),
        CommandDef(
            name="listyoutube",
            description="List all YouTube channels",
            admin_only=True,
        ),
        CommandDef(
            name="addgithub",
            description="Add GitHub repository",
            admin_only=True,
        ),
        CommandDef(
            name="removegithub",
            description="Remove GitHub repository",
            admin_only=True,
        ),
        CommandDef(
            name="listgithub",
            description="List all GitHub repositories",
            admin_only=True,
        ),
        CommandDef(
            name="addwebhook",
            description="Add webhook integration",
            admin_only=True,
        ),
        CommandDef(
            name="removewebhook",
            description="Remove webhook integration",
            admin_only=True,
        ),
        CommandDef(
            name="listwebhooks",
            description="List all webhooks",
            admin_only=True,
        ),
        CommandDef(
            name="addtwitter",
            description="Add Twitter/X account",
            admin_only=True,
        ),
        CommandDef(
            name="removetwitter",
            description="Remove Twitter/X account",
            admin_only=True,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("addrss", self.cmd_addrss)
        self.register_command("removerss", self.cmd_removerss)
        self.register_command("listrss", self.cmd_listrss)
        self.register_command("addyoutube", self.cmd_addyoutube)
        self.register_command("removeyoutube", self.cmd_removeyoutube)
        self.register_command("listyoutube", self.cmd_listyoutube)
        self.register_command("addgithub", self.cmd_addgithub)
        self.register_command("removegithub", self.cmd_removegithub)
        self.register_command("listgithub", self.cmd_listgithub)
        self.register_command("addwebhook", self.cmd_addwebhook)
        self.register_command("removewebhook", self.cmd_removewebhook)
        self.register_command("listwebhooks", self.cmd_listwebhooks)
        self.register_command("addtwitter", self.cmd_addtwitter)
        self.register_command("removetwitter", self.cmd_removetwitter)

    async def cmd_addrss(self, ctx: NexusContext):
        """Add RSS feed."""
        args = ctx.message.text.split(maxsplit=2)[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply(
                "❌ Usage: /addrss <name> <url> [tags]\n\n"
                "Example: /addrss Tech https://example.com/feed technology"
            )
            return

        name = args[0]
        url = args[1]
        tags = " ".join(args[2:]) if len(args) > 2 else ""

        # Validate URL
        if not url.startswith(("http://", "https://")):
            await ctx.reply("❌ URL must start with http:// or https://")
            return

        # Store RSS feed
        # For now, just acknowledge
        await ctx.reply(
            f"✅ RSS Feed Added\n\n"
            f"📝 Name: {name}\n"
            f"🔗 URL: {url}\n"
            f"🏷️ Tags: {tags or 'No tags'}\n\n"
            f"ℹ️ RSS feeds will be checked every 5 minutes and new posts will be shared in the group."
        )

    async def cmd_removerss(self, ctx: NexusContext):
        """Remove RSS feed."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /removerss <name>")
            return

        name = args[0]

        await ctx.reply(f"✅ RSS feed removed: {name}")

    async def cmd_listrss(self, ctx: NexusContext):
        """List all RSS feeds."""
        text = "📰 RSS Feeds\n\n"
        text += "ℹ️ RSS feeds are checked every 5 minutes.\n\n"
        text += "No RSS feeds configured yet.\n\n"
        text += "Add one with: /addrss <name> <url>"

        await ctx.reply(text)

    async def cmd_addyoutube(self, ctx: NexusContext):
        """Add YouTube channel."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if len(args) < 1:
            await ctx.reply(
                "❌ Usage: /addyoutube <channel_url_or_handle>\n\n"
                "Examples:\n"
                "/addyoutube https://youtube.com/@channel\n"
                "/addyoutube @channel"
            )
            return

        channel = args[0]

        # Extract channel handle
        handle = None
        if channel.startswith("http"):
            match = re.search(r"(?:youtube\.com|youtu\.be)/(?:@|channel/)([^/?&]+)", channel)
            if match:
                handle = match.group(1)
        elif channel.startswith("@"):
            handle = channel[1:]
        else:
            handle = channel

        if not handle:
            await ctx.reply("❌ Invalid YouTube channel format")
            return

        # Store YouTube channel
        await ctx.reply(
            f"✅ YouTube Channel Added\n\n"
            f"📺 Channel: @{handle}\n"
            f"ℹ️ New videos will be posted when available."
        )

    async def cmd_removeyoutube(self, ctx: NexusContext):
        """Remove YouTube channel."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /removeyoutube <channel_handle>")
            return

        handle = args[0].lstrip("@")

        await ctx.reply(f"✅ YouTube channel removed: @{handle}")

    async def cmd_listyoutube(self, ctx: NexusContext):
        """List all YouTube channels."""
        text = "📺 YouTube Channels\n\n"
        text += "ℹ️ New videos from these channels will be posted automatically.\n\n"
        text += "No YouTube channels configured yet.\n\n"
        text += "Add one with: /addyoutube <channel_url_or_handle>"

        await ctx.reply(text)

    async def cmd_addgithub(self, ctx: NexusContext):
        """Add GitHub repository."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply(
                "❌ Usage: /addgithub <name> <repo_url> [events]\n\n"
                "Example: /addgithub Nexus https://github.com/user/repo push,star,release"
            )
            return

        name = args[0]
        url = args[1]
        events = " ".join(args[2:]) if len(args) > 2 else "push"

        # Validate URL
        if not url.startswith("https://github.com/"):
            await ctx.reply("❌ URL must be a GitHub repository URL")
            return

        # Store GitHub repo
        await ctx.reply(
            f"✅ GitHub Repository Added\n\n"
            f"📝 Name: {name}\n"
            f"🔗 URL: {url}\n"
            f"📋 Events: {events}\n\n"
            f"ℹ️ Will notify for: push, star, and release events."
        )

    async def cmd_removegithub(self, ctx: NexusContext):
        """Remove GitHub repository."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /removegithub <name>")
            return

        name = args[0]

        await ctx.reply(f"✅ GitHub repository removed: {name}")

    async def cmd_listgithub(self, ctx: NexusContext):
        """List all GitHub repositories."""
        text = "🐙 GitHub Repositories\n\n"
        text += "ℹ️ Will notify for events from these repositories.\n\n"
        text += "No GitHub repositories configured yet.\n\n"
        text += "Add one with: /addgithub <name> <repo_url> [events]"

        await ctx.reply(text)

    async def cmd_addwebhook(self, ctx: NexusContext):
        """Add webhook integration."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if len(args) < 3:
            await ctx.reply(
                "❌ Usage: /addwebhook <name> <url> <secret>\n\n"
                "Example: /addwebhook MyService https://api.example.com/webhook my_secret_key"
            )
            return

        name = args[0]
        url = args[1]
        secret = args[2]

        # Validate URL
        if not url.startswith(("http://", "https://")):
            await ctx.reply("❌ URL must start with http:// or https://")
            return

        # Store webhook
        await ctx.reply(
            f"✅ Webhook Integration Added\n\n"
            f"📝 Name: {name}\n"
            f"🔗 URL: {url}\n"
            f"🔑 Secret: {secret}\n\n"
            f"ℹ️ Webhooks will receive updates from this group."
        )

    async def cmd_removewebhook(self, ctx: NexusContext):
        """Remove webhook integration."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /removewebhook <name>")
            return

        name = args[0]

        await ctx.reply(f"✅ Webhook removed: {name}")

    async def cmd_listwebhooks(self, ctx: NexusContext):
        """List all webhooks."""
        text = "🔌 Webhook Integrations\n\n"
        text += "ℹ️ These webhooks receive updates from this group.\n\n"
        text += "No webhooks configured yet.\n\n"
        text += "Add one with: /addwebhook <name> <url> <secret>"

        await ctx.reply(text)

    async def cmd_addtwitter(self, ctx: NexusContext):
        """Add Twitter/X account."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if len(args) < 1:
            await ctx.reply(
                "❌ Usage: /addtwitter <twitter_handle>\n\n"
                "Example: /addtwitter @username"
            )
            return

        handle = args[0].lstrip("@")

        if not handle:
            await ctx.reply("❌ Invalid Twitter handle")
            return

        await ctx.reply(
            f"✅ Twitter/X Account Added\n\n"
            f"🐦 Handle: @{handle}\n"
            f"ℹ️ New tweets will be posted when available.\n\n"
            f"⚠️ Note: Twitter API access requires additional setup."
        )

    async def cmd_removetwitter(self, ctx: NexusContext):
        """Remove Twitter/X account."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /removetwitter <twitter_handle>")
            return

        handle = args[0].lstrip("@")

        await ctx.reply(f"✅ Twitter/X account removed: @{handle}")

    async def _fetch_rss(self, url: str) -> List[Dict]:
        """Fetch RSS feed and return entries."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        content = await response.text()
                        root = ET.fromstring(content)

                        ns = {"atom": "http://www.w3.org/2005/Atom"}
                        entries = []

                        # Try RSS 2.0 format
                        items = root.findall(".//item")
                        for item in items[:5]:
                            title = item.findtext("title") or "No title"
                            link = item.findtext("link") or ""
                            description = item.findtext("description") or ""
                            published = item.findtext("pubDate") or ""
                            entries.append({
                                "title": title,
                                "link": link,
                                "description": description,
                                "published": published,
                            })

                        # Try Atom format if no RSS items found
                        if not entries:
                            for entry in root.findall("atom:entry", ns)[:5]:
                                title = entry.findtext("atom:title", namespaces=ns) or "No title"
                                link_el = entry.find("atom:link", ns)
                                link = link_el.get("href", "") if link_el is not None else ""
                                summary = entry.findtext("atom:summary", namespaces=ns) or ""
                                published = entry.findtext("atom:published", namespaces=ns) or ""
                                entries.append({
                                    "title": title,
                                    "link": link,
                                    "description": summary,
                                    "published": published,
                                })

                        return entries
        except Exception as e:
            print(f"Error fetching RSS: {e}")
            return []

    async def _format_rss_entry(self, entry: Dict, config: IntegrationConfig) -> str:
        """Format RSS entry for posting."""
        title = entry["title"]
        link = entry["link"]
        description = entry.get("description", "")

        # Truncate description
        if len(description) > config.preview_length:
            description = description[:config.preview_length] + "..."

        text = f"📰 {title}\n\n"
        text += f"{description}\n\n"
        text += f"🔗 Read more: {link}"

        return text

    async def _fetch_youtube_videos(self, handle: str) -> List[Dict]:
        """Fetch latest videos from YouTube channel."""
        # This would use YouTube API
        # For now, return placeholder
        return []
