"""Scraping Module - Web scraping for user bots."""

from typing import Any, Dict, List, Optional
import httpx
from bs4 import BeautifulSoup
import re

from bot.core.module_base import NexusModule, ModuleCategory
from bot.core.context import NexusContext


class ScrapingModule(NexusModule):
    """Module for web scraping functionality."""
    
    name = "scraping"
    version = "1.0.0"
    author = "Nexus"
    description = "Scrape web content and send to channels"
    category = ModuleCategory.INTEGRATION
    
    config_schema = None
    default_config = {}
    
    commands = [
        {"name": "scrape", "description": "Scrape a URL", "admin_only": True},
        {"name": "rss", "description": "Add RSS feed", "admin_only": True},
    ]
    
    def __init__(self):
        super().__init__()
        self.rss_feeds: Dict[int, List[Dict]] = {}
    
    async def on_load(self, app):
        """Load the module."""
        self.bot = app
        await self._load_rss_feeds()
    
    async def _load_rss_feeds(self):
        """Load RSS feeds from database."""
        # Would load from DB
        pass
    
    async def on_message(self, ctx: NexusContext) -> None:
        """Check for RSS updates."""
        # This would run periodically to check RSS feeds
        pass
    
    async def _scrape_url(self, url: str, selector: Optional[str] = None) -> Dict[str, Any]:
        """Scrape a URL and return content."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            
            result = {
                "status": response.status_code,
                "url": url,
                "content_length": len(response.text)
            }
            
            if selector:
                soup = BeautifulSoup(response.text, 'html.parser')
                elements = soup.select(selector)
                result["data"] = [
                    {"text": el.get_text(strip=True), "html": str(el)}
                    for el in elements[:10]
                ]
                result["count"] = len(elements)
            else:
                result["data"] = response.text[:5000]
            
            return result
    
    async def on_command_scrape(self, ctx: NexusContext) -> None:
        """Handle /scrape command."""
        if not ctx.message:
            return
        
        # Get URL from message
        text = ctx.message.text.replace("/scrape", "").strip()
        
        if not text:
            await ctx.reply("Usage: /scrape <url> [selector]")
            return
        
        parts = text.split(" ", 1)
        url = parts[0]
        selector = parts[1] if len(parts) > 1 else None
        
        if not url.startswith("http"):
            url = "https://" + url
        
        await ctx.reply(f"Scraping {url}...")
        
        try:
            result = await self._scrape_url(url, selector)
            
            if result["status"] == 200:
                await ctx.reply(
                    f"✅ Success!\n\n"
                    f"URL: {result['url']}\n"
                    f"Content length: {result['content_length']} bytes\n"
                    f"Data items: {result.get('count', 'N/A')}"
                )
            else:
                await ctx.reply(f"❌ Error: HTTP {result['status']}")
        except Exception as e:
            await ctx.reply(f"❌ Error: {str(e)}")
    
    async def on_command_rss(self, ctx: NexusContext) -> None:
        """Handle /rss command."""
        if not ctx.message:
            return
        
        await ctx.reply("Use the Mini App to manage RSS feeds with scheduling and filters!")


# Create module instance
module = ScrapingModule()
