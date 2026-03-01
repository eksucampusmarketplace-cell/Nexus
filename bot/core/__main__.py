"""Main entry point for the bot."""

import asyncio
import logging
import os
import signal
import sys
from datetime import timedelta
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold, hcode, hitalic
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from bot.core.middleware import pipeline, setup_pipeline
from bot.core.module_registry import module_registry
from bot.core.token_manager import token_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def start_command(message: Message, bot: Bot):
    """Handle /start command in private chats."""
    text = f"👋 {hbold('Welcome to Nexus Bot!')} 🚀\n\n"
    text += f"{hbold('The Ultimate Telegram Bot Platform')} 🎉\n\n"
    text += f"📚 {hcode('/help')} - View all commands\n"
    text += f"📱 {hcode('/settings')} - Open settings panel\n"
    text += "ℹ️ Use commands or open the Mini App for full control!\n\n"
    text += f"💡 {hitalic('Type /help <command> for detailed information')}"

    await message.answer(text, parse_mode=ParseMode.HTML)


async def help_command(message: Message, bot: Bot):
    """Handle /help command."""
    text = f"{hbold('📚 Nexus Bot Help')}\n\n"
    text += f"{hbold('Core Commands')}:\n"
    text += f"  {hcode('/start')} - Start the bot\n"
    text += f"  {hcode('/help')} - Show this help\n"
    text += f"  {hcode('/ping')} - Check bot latency\n"
    text += f"  {hcode('/about')} - About Nexus bot\n\n"
    text += f"Add me to a group to enable moderation features!"

    await message.answer(text, parse_mode=ParseMode.HTML)


async def ping_command(message: Message, bot: Bot):
    """Handle /ping command."""
    await message.answer("🏓 Pong!")


async def run_long_polling(dp: Dispatcher, bot: Bot):
    """Run bot in long-polling mode."""
    logger.info("Starting long-polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def startup():
    """Initialize and start the bot."""
    logger.info("Starting Nexus Bot...")

    # Get bot token
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not set!")
        sys.exit(1)

    # Initialize token manager (try/catch for when database is unavailable)
    logger.info("Initializing token manager...")
    try:
        await token_manager.initialize()
    except Exception as e:
        logger.warning(f"Token manager initialization skipped (DB unavailable): {e}")

    # Setup middleware pipeline
    logger.info("Setting up middleware pipeline...")
    setup_pipeline()

    # Load modules (try/catch for when database is unavailable)
    logger.info("Loading modules...")
    try:
        await module_registry.load_all()
    except Exception as e:
        logger.warning(f"Module loading skipped (DB unavailable): {e}")

    # Check dependencies and conflicts
    try:
        missing_deps = module_registry.check_dependencies()
        if missing_deps:
            for name, deps in missing_deps.items():
                logger.warning(f"Module {name} missing dependencies: {deps}")

        conflicts = module_registry.check_conflicts()
        if conflicts:
            for name, confs in conflicts.items():
                logger.warning(f"Module {name} conflicts with: {confs}")

        # Register modules with pipeline
        for module in module_registry.get_all_modules():
            pipeline.add_module(module)

        logger.info(f"Loaded {len(module_registry.get_all_modules())} modules")
    except Exception as e:
        logger.warning(f"Module registration skipped: {e}")

    # Check mode: long-polling (development) or webhooks (production)
    webhook_url = os.getenv("WEBHOOK_URL")
    
    # Create bot and dispatcher
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Register command handlers
    dp.message.register(start_command, Command("start"))
    dp.message.register(help_command, Command("help"))
    dp.message.register(ping_command, Command("ping"))

    if webhook_url:
        # Production mode: Use webhooks
        shared_webhook = f"{webhook_url}/shared"
        if not shared_webhook.startswith("http"):
             shared_webhook = f"https://{shared_webhook}"
        
        print(f"DEBUG: Setting webhook to {shared_webhook}")
        await bot.set_webhook(
            url=shared_webhook,
            allowed_updates=[
                "message",
                "edited_message",
                "callback_query",
                "inline_query",
                "chat_member",
                "my_chat_member",
                "poll",
                "poll_answer",
                "chat_join_request",
                "message_reaction",
            ],
        )
        await bot.session.close()
        logger.info(f"Webhook set to {shared_webhook}")
        
        # Keep running
        while True:
            await asyncio.sleep(3600)
    else:
        # Development mode: Use long-polling
        logger.info("No WEBHOOK_URL set, using long-polling mode for development")
        await run_long_polling(dp, bot)


async def shutdown():
    """Graceful shutdown."""
    logger.info("Shutting down...")
    await module_registry.unload_all()
    await token_manager.cleanup()
    logger.info("Shutdown complete.")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    asyncio.create_task(shutdown())
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        asyncio.run(startup())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        asyncio.run(shutdown())
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        asyncio.run(shutdown())
        sys.exit(1)
