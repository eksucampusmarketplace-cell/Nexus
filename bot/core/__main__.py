"""Main entry point for the bot."""

import asyncio
import logging
import os
import signal
import sys

from aiogram import Bot

from bot.core.middleware import pipeline, setup_pipeline
from bot.core.module_registry import module_registry
from bot.core.token_manager import token_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def startup():
    """Initialize and start the bot."""
    logger.info("Starting Nexus Bot...")

    # Get bot token
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not set!")
        sys.exit(1)

    # Initialize token manager
    logger.info("Initializing token manager...")
    await token_manager.initialize()

    # Setup middleware pipeline
    logger.info("Setting up middleware pipeline...")
    setup_pipeline()

    # Load modules
    logger.info("Loading modules...")
    await module_registry.load_all()

    # Check dependencies and conflicts
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

    # Set up webhook for shared bot
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        shared_webhook = f"{webhook_url}/webhook/shared"
        bot = Bot(token=bot_token)
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

    logger.info("Nexus Bot started successfully!")

    # Keep running
    while True:
        await asyncio.sleep(3600)


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
