"""Base class for all Nexus modules."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Dict, List, Optional, Type

from fastapi import APIRouter
from pydantic import BaseModel

if TYPE_CHECKING:
    from bot.core.context import NexusContext


class EventType(str, Enum):
    """Event types that modules can listen to."""
    MESSAGE = "message"
    EDITED_MESSAGE = "edited_message"
    NEW_MEMBER = "new_member"
    LEFT_MEMBER = "left_member"
    CALLBACK = "callback_query"
    INLINE = "inline_query"
    POLL = "poll"
    REACTION = "reaction"


class ModuleCategory(str, Enum):
    """Module categories."""
    MODERATION = "moderation"
    GREETINGS = "greetings"
    ANTISPAM = "antispam"
    COMMUNITY = "community"
    AI = "ai"
    GAMES = "games"
    UTILITY = "utility"
    INTEGRATION = "integration"


@dataclass
class CommandDef:
    """Command definition."""
    name: str
    description: str
    admin_only: bool = False
    aliases: List[str] = None
    args: Optional[str] = None

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []


class NexusModule(ABC):
    """Base class for all Nexus modules."""

    # Module metadata
    name: str = ""  # Unique slug
    version: str = "1.0.0"
    author: str = "Nexus Team"
    description: str = ""
    category: ModuleCategory = ModuleCategory.UTILITY

    # Configuration
    config_schema: Type[BaseModel] = BaseModel
    default_config: Dict[str, Any] = {}

    # Commands and listeners
    commands: List[CommandDef] = []
    listeners: List[EventType] = []

    # Routes and UI
    api_router: Optional[APIRouter] = None
    mini_app_component: Optional[str] = None

    # Dependencies
    dependencies: List[str] = []
    conflicts: List[str] = []

    def __init__(self):
        self._command_handlers: Dict[str, Callable] = {}
        self._enabled_groups: set = set()

    async def on_load(self, app: Any) -> None:
        """Called when module is loaded."""
        pass

    async def on_unload(self) -> None:
        """Called when module is unloaded."""
        pass

    async def on_enable(self, group_id: int) -> None:
        """Called when module is enabled for a group."""
        self._enabled_groups.add(group_id)

    async def on_disable(self, group_id: int) -> None:
        """Called when module is disabled for a group."""
        self._enabled_groups.discard(group_id)

    async def on_message(self, ctx: "NexusContext") -> bool:
        """
        Handle a new message.
        Returns True if message was handled, False otherwise.
        """
        return False

    async def on_edited_message(self, ctx: "NexusContext") -> bool:
        """Handle an edited message."""
        return False

    async def on_new_member(self, ctx: "NexusContext") -> bool:
        """Handle new member join."""
        return False

    async def on_left_member(self, ctx: "NexusContext") -> bool:
        """Handle member leave."""
        return False

    async def on_callback_query(self, ctx: "NexusContext") -> bool:
        """Handle callback query."""
        return False

    async def on_inline_query(self, ctx: "NexusContext") -> bool:
        """Handle inline query."""
        return False

    async def on_reaction(self, ctx: "NexusContext") -> bool:
        """Handle message reaction."""
        return False

    def is_enabled_for(self, group_id: int) -> bool:
        """Check if module is enabled for a group."""
        return group_id in self._enabled_groups

    def register_command(self, name: str, handler: Callable[["NexusContext"], Coroutine]):
        """Register a command handler."""
        self._command_handlers[name] = handler

    async def handle_command(self, name: str, ctx: "NexusContext") -> bool:
        """Handle a command."""
        if name in self._command_handlers:
            await self._command_handlers[name](ctx)
            return True
        return False

    def get_info(self) -> Dict[str, Any]:
        """Get module information."""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "category": self.category.value,
            "commands": [
                {
                    "name": cmd.name,
                    "description": cmd.description,
                    "admin_only": cmd.admin_only,
                    "aliases": cmd.aliases,
                }
                for cmd in self.commands
            ],
            "listeners": [e.value for e in self.listeners],
            "dependencies": self.dependencies,
            "conflicts": self.conflicts,
            "has_mini_app": self.mini_app_component is not None,
        }
