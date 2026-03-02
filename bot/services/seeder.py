"""Database seeder for populating default data."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.command_config_service import get_default_command_definitions
from bot.services.message_template_service import (
    get_default_categories,
    get_default_message_definitions,
)
from shared.models import CommandDefinition, MessageTemplateCategory, MessageTemplateDefinition

logger = logging.getLogger(__name__)


class DatabaseSeeder:
    """Populates database with default data."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def seed_all(self):
        """Run all seeders."""
        await self.seed_message_categories()
        await self.seed_message_definitions()
        await self.seed_command_definitions()
        await self.db.commit()
        logger.info("Database seeding completed")
    
    async def seed_message_categories(self):
        """Seed message template categories."""
        categories = get_default_categories()
        
        for cat_data in categories:
            # Check if exists
            result = await self.db.execute(
                select(MessageTemplateCategory).where(
                    MessageTemplateCategory.slug == cat_data["slug"]
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                category = MessageTemplateCategory(
                    slug=cat_data["slug"],
                    name=cat_data["name"],
                    description=cat_data.get("description"),
                    icon=cat_data.get("icon", "message"),
                    sort_order=cat_data.get("sort_order", 0),
                )
                self.db.add(category)
                logger.info(f"Added message category: {cat_data['slug']}")
    
    async def seed_message_definitions(self):
        """Seed message template definitions."""
        definitions = get_default_message_definitions()
        
        for msg_data in definitions:
            # Check if exists
            result = await self.db.execute(
                select(MessageTemplateDefinition).where(
                    MessageTemplateDefinition.identifier == msg_data["identifier"]
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                definition = MessageTemplateDefinition(
                    identifier=msg_data["identifier"],
                    category_slug=msg_data["category_slug"],
                    name=msg_data["name"],
                    description=msg_data["description"],
                    default_text=msg_data["default_text"],
                    default_tone=msg_data.get("default_tone", "formal"),
                    allowed_destinations=msg_data.get("allowed_destinations", ["public"]),
                    supports_self_destruct=msg_data.get("supports_self_destruct", True),
                    supports_variables=msg_data.get("supports_variables", True),
                    available_variables=msg_data.get("available_variables"),
                    tone_variations=msg_data.get("tone_variations"),
                    module_name=msg_data["module_name"],
                    is_enabled=True,
                    sort_order=msg_data.get("sort_order", 0),
                )
                self.db.add(definition)
                logger.info(f"Added message definition: {msg_data['identifier']}")
    
    async def seed_command_definitions(self):
        """Seed command definitions."""
        commands = get_default_command_definitions()
        
        for cmd_data in commands:
            # Check if exists
            result = await self.db.execute(
                select(CommandDefinition).where(
                    CommandDefinition.command_id == cmd_data["command_id"]
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                command = CommandDefinition(
                    command_id=cmd_data["command_id"],
                    module_name=cmd_data["module_name"],
                    name=cmd_data["name"],
                    description=cmd_data["description"],
                    category=cmd_data["category"],
                    usage=cmd_data.get("usage"),
                    examples=cmd_data.get("examples"),
                    default_prefix=cmd_data.get("default_prefix", "!"),
                    default_aliases=cmd_data.get("default_aliases", []),
                    default_min_role=cmd_data.get("default_min_role", "mod"),
                    default_cooldown_seconds=cmd_data.get("default_cooldown_seconds", 0),
                    default_admin_only=cmd_data.get("default_admin_only", False),
                    supports_cooldown=cmd_data.get("supports_cooldown", True),
                    supports_aliases=cmd_data.get("supports_aliases", True),
                    supports_prefix_change=cmd_data.get("supports_prefix_change", True),
                    supports_permission_change=cmd_data.get("supports_permission_change", True),
                    supports_topic_restriction=cmd_data.get("supports_topic_restriction", False),
                    supports_confirmation=cmd_data.get("supports_confirmation", False),
                    default_delete_trigger=cmd_data.get("default_delete_trigger", False),
                    default_reply_mode=cmd_data.get("default_reply_mode", True),
                    default_pin_mode=cmd_data.get("default_pin_mode", "none"),
                    is_enabled=True,
                    sort_order=cmd_data.get("sort_order", 0),
                )
                self.db.add(command)
                logger.info(f"Added command definition: {cmd_data['command_id']}")


async def seed_database(db: AsyncSession):
    """Convenience function to seed database."""
    seeder = DatabaseSeeder(db)
    await seeder.seed_all()
