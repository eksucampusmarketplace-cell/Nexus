"""
Keyboard State Management System

Provides Redis-backed state management for inline keyboards, enabling:
- Persistent keyboard state across sessions
- Multi-step interactive flows
- State recovery after bot restarts
- Automatic cleanup and expiration
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, TypeVar, Generic
from contextlib import asynccontextmanager

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from shared.redis_client import GroupScopedRedis, get_group_redis


T = TypeVar('T')


class KeyboardStateStatus(str, Enum):
    """Status of a keyboard state session."""
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class KeyboardState:
    """
    Represents the state of an interactive keyboard session.
    
    This is stored in Redis and provides persistence across sessions.
    """
    state_id: str
    group_id: int
    user_id: int
    message_id: Optional[int] = None
    chat_id: Optional[int] = None
    
    # State data
    current_step: str = "start"
    data: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    status: KeyboardStateStatus = KeyboardStateStatus.ACTIVE
    
    # Flow configuration
    flow_type: str = "default"
    auto_advance: bool = True
    allow_back: bool = True
    timeout_seconds: int = 300
    
    def __post_init__(self):
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(seconds=self.timeout_seconds)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "state_id": self.state_id,
            "group_id": self.group_id,
            "user_id": self.user_id,
            "message_id": self.message_id,
            "chat_id": self.chat_id,
            "current_step": self.current_step,
            "data": self.data,
            "history": self.history,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status.value,
            "flow_type": self.flow_type,
            "auto_advance": self.auto_advance,
            "allow_back": self.allow_back,
            "timeout_seconds": self.timeout_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyboardState":
        """Create from dictionary."""
        return cls(
            state_id=data["state_id"],
            group_id=data["group_id"],
            user_id=data["user_id"],
            message_id=data.get("message_id"),
            chat_id=data.get("chat_id"),
            current_step=data.get("current_step", "start"),
            data=data.get("data", {}),
            history=data.get("history", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            status=KeyboardStateStatus(data.get("status", "active")),
            flow_type=data.get("flow_type", "default"),
            auto_advance=data.get("auto_advance", True),
            allow_back=data.get("allow_back", True),
            timeout_seconds=data.get("timeout_seconds", 300),
        )
    
    def is_expired(self) -> bool:
        """Check if state has expired."""
        if self.status != KeyboardStateStatus.ACTIVE:
            return True
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return False
    
    def transition_to(self, step: str, data_updates: Optional[Dict[str, Any]] = None):
        """Record transition to a new step."""
        self.history.append({
            "from_step": self.current_step,
            "to_step": step,
            "timestamp": datetime.utcnow().isoformat(),
            "data_snapshot": dict(self.data),
        })
        self.current_step = step
        if data_updates:
            self.data.update(data_updates)
        # Reset expiration on activity
        self.expires_at = datetime.utcnow() + timedelta(seconds=self.timeout_seconds)


@dataclass
class KeyboardButton:
    """Enhanced keyboard button with state management."""
    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None
    switch_inline_query: Optional[str] = None
    switch_inline_query_current_chat: Optional[str] = None
    callback_handler: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    
    def to_aiogram_button(self) -> InlineKeyboardButton:
        """Convert to aiogram InlineKeyboardButton."""
        return InlineKeyboardButton(
            text=self.text,
            callback_data=self.callback_data,
            url=self.url,
            switch_inline_query=self.switch_inline_query,
            switch_inline_query_current_chat=self.switch_inline_query_current_chat,
        )


@dataclass
class KeyboardLayout:
    """Layout definition for an interactive keyboard."""
    buttons: List[List[KeyboardButton]]
    layout_id: str = "default"
    persistent: bool = True
    edit_on_update: bool = True
    delete_on_complete: bool = False
    
    def to_markup(self) -> InlineKeyboardMarkup:
        """Convert to aiogram InlineKeyboardMarkup."""
        keyboard = [
            [btn.to_aiogram_button() for btn in row]
            for row in self.buttons
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


class KeyboardStateManager:
    """
    Manages keyboard state persistence using Redis.
    
    Provides:
    - State creation and retrieval
    - Automatic cleanup of expired states
    - Event handling for state transitions
    - Batch operations for maintenance
    """
    
    def __init__(self, redis: GroupScopedRedis):
        self.redis = redis
        self._handlers: Dict[str, Dict[str, Callable]] = {}
        self._layouts: Dict[str, KeyboardLayout] = {}
    
    # Redis key patterns
    def _state_key(self, state_id: str) -> str:
        return f"keyboard:state:{state_id}"
    
    def _user_states_key(self, user_id: int) -> str:
        return f"keyboard:user:{user_id}:states"
    
    def _group_states_key(self) -> str:
        return f"keyboard:group:states"
    
    def _index_key(self) -> str:
        return f"keyboard:index"
    
    async def create_state(
        self,
        group_id: int,
        user_id: int,
        flow_type: str = "default",
        initial_data: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 300,
        **kwargs
    ) -> KeyboardState:
        """
        Create a new keyboard state session.
        
        Args:
            group_id: The group/chat ID
            user_id: The user ID
            flow_type: Type of flow/interaction
            initial_data: Initial state data
            timeout_seconds: Session timeout
            
        Returns:
            New KeyboardState instance
        """
        state_id = f"{flow_type}:{group_id}:{user_id}:{uuid.uuid4().hex[:8]}"
        
        state = KeyboardState(
            state_id=state_id,
            group_id=group_id,
            user_id=user_id,
            flow_type=flow_type,
            data=initial_data or {},
            timeout_seconds=timeout_seconds,
            **kwargs
        )
        
        # Store in Redis with expiration
        await self._save_state(state)
        
        # Add to indexes
        await self.redis.sadd(self._user_states_key(user_id), state_id)
        await self.redis.sadd(self._group_states_key(), state_id)
        await self.redis.zadd(self._index_key(), {state_id: datetime.utcnow().timestamp()})
        
        return state
    
    async def get_state(self, state_id: str) -> Optional[KeyboardState]:
        """
        Get a keyboard state by ID.
        
        Returns None if not found or expired.
        """
        data = await self.redis.get_json(self._state_key(state_id))
        if not data:
            return None
        
        state = KeyboardState.from_dict(data)
        
        if state.is_expired():
            await self._cleanup_state(state_id)
            return None
        
        return state
    
    async def update_state(self, state: KeyboardState) -> bool:
        """Update a keyboard state."""
        if state.is_expired():
            await self._cleanup_state(state.state_id)
            return False
        
        await self._save_state(state)
        return True
    
    async def transition_state(
        self,
        state_id: str,
        new_step: str,
        data_updates: Optional[Dict[str, Any]] = None
    ) -> Optional[KeyboardState]:
        """
        Transition a state to a new step.
        
        Records history and updates expiration.
        """
        state = await self.get_state(state_id)
        if not state:
            return None
        
        state.transition_to(new_step, data_updates)
        await self._save_state(state)
        
        # Trigger handlers if registered
        await self._trigger_handlers(state, "transition", {
            "from_step": state.history[-1]["from_step"] if state.history else None,
            "to_step": new_step,
        })
        
        return state
    
    async def complete_state(
        self,
        state_id: str,
        final_data: Optional[Dict[str, Any]] = None
    ) -> Optional[KeyboardState]:
        """Mark a state as completed."""
        state = await self.get_state(state_id)
        if not state:
            return None
        
        state.status = KeyboardStateStatus.COMPLETED
        if final_data:
            state.data.update(final_data)
        
        await self._save_state(state)
        await self._trigger_handlers(state, "complete", state.data)
        
        # Schedule cleanup
        await self.redis.expire(self._state_key(state_id), 3600)  # Keep for 1 hour
        
        return state
    
    async def cancel_state(self, state_id: str, reason: str = "user_cancelled") -> bool:
        """Cancel a state session."""
        state = await self.get_state(state_id)
        if not state:
            return False
        
        state.status = KeyboardStateStatus.CANCELLED
        state.data["cancel_reason"] = reason
        state.data["cancelled_at"] = datetime.utcnow().isoformat()
        
        await self._save_state(state)
        await self._trigger_handlers(state, "cancel", {"reason": reason})
        await self._cleanup_state(state_id)
        
        return True
    
    async def get_user_active_states(self, user_id: int) -> List[KeyboardState]:
        """Get all active states for a user."""
        state_ids = await self.redis.smembers(self._user_states_key(user_id))
        states = []
        
        for state_id in state_ids:
            state = await self.get_state(state_id)
            if state and not state.is_expired():
                states.append(state)
        
        return states
    
    async def cleanup_expired_states(self, max_age_hours: int = 24) -> int:
        """
        Clean up expired and old completed states.
        
        Returns number of states cleaned up.
        """
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        cutoff_ts = cutoff.timestamp()
        
        # Get all state IDs older than cutoff
        old_state_ids = await self.redis.zrangebyscore(
            self._index_key(), 0, cutoff_ts
        )
        
        cleaned = 0
        for state_id in old_state_ids:
            await self._cleanup_state(state_id)
            cleaned += 1
        
        return cleaned
    
    async def _save_state(self, state: KeyboardState):
        """Save state to Redis with expiration."""
        key = self._state_key(state.state_id)
        ttl = int((state.expires_at - datetime.utcnow()).total_seconds()) if state.expires_at else state.timeout_seconds
        await self.redis.set_json(key, state.to_dict(), expire=max(ttl, 60))
    
    async def _cleanup_state(self, state_id: str):
        """Remove state from all indexes."""
        # Extract user_id from state_id (format: flow:group:user:uuid)
        parts = state_id.split(":")
        if len(parts) >= 3:
            try:
                user_id = int(parts[2])
                await self.redis.srem(self._user_states_key(user_id), state_id)
            except ValueError:
                pass
        
        await self.redis.srem(self._group_states_key(), state_id)
        await self.redis.zrem(self._index_key(), state_id)
        await self.redis.delete(self._state_key(state_id))
    
    # Handler registration
    def register_handler(
        self,
        flow_type: str,
        event: str,
        handler: Callable[[KeyboardState, Dict[str, Any]], Coroutine]
    ):
        """Register an event handler for a flow type."""
        if flow_type not in self._handlers:
            self._handlers[flow_type] = {}
        self._handlers[flow_type][event] = handler
    
    async def _trigger_handlers(self, state: KeyboardState, event: str, data: Dict[str, Any]):
        """Trigger registered handlers for an event."""
        handlers = self._handlers.get(state.flow_type, {})
        handler = handlers.get(event)
        if handler:
            try:
                await handler(state, data)
            except Exception as e:
                print(f"Error in keyboard handler: {e}")
    
    # Layout management
    def register_layout(self, layout_id: str, layout: KeyboardLayout):
        """Register a keyboard layout."""
        self._layouts[layout_id] = layout
    
    def get_layout(self, layout_id: str) -> Optional[KeyboardLayout]:
        """Get a registered layout."""
        return self._layouts.get(layout_id)


class InteractiveKeyboardBuilder:
    """
    Builder for creating interactive keyboards with state management.
    
    Example:
        builder = InteractiveKeyboardBuilder(state_manager, ctx)
        
        keyboard = (
            builder
            .with_state("wizard", initial_data={"step": 1})
            .add_row()
            .add_button("Option 1", callback="opt1", handler="on_option_1")
            .add_button("Option 2", callback="opt2", handler="on_option_2")
            .add_row()
            .add_back_button()
            .add_cancel_button()
            .build()
        )
    """
    
    def __init__(
        self,
        state_manager: KeyboardStateManager,
        group_id: int,
        user_id: int,
        bot=None
    ):
        self.state_manager = state_manager
        self.group_id = group_id
        self.user_id = user_id
        self.bot = bot
        
        self._rows: List[List[KeyboardButton]] = []
        self._current_row: List[KeyboardButton] = []
        self._state: Optional[KeyboardState] = None
        self._flow_type: str = "default"
        self._initial_data: Dict[str, Any] = {}
    
    def with_state(
        self,
        flow_type: str,
        initial_data: Optional[Dict[str, Any]] = None,
        existing_state_id: Optional[str] = None
    ) -> "InteractiveKeyboardBuilder":
        """Configure state management."""
        self._flow_type = flow_type
        self._initial_data = initial_data or {}
        return self
    
    def add_row(self) -> "InteractiveKeyboardBuilder":
        """Start a new row."""
        if self._current_row:
            self._rows.append(self._current_row)
            self._current_row = []
        return self
    
    def add_button(
        self,
        text: str,
        callback: Optional[str] = None,
        handler: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> "InteractiveKeyboardBuilder":
        """Add a button to the current row."""
        # Encode handler and payload into callback_data
        if handler or payload:
            callback_data = self._encode_callback(callback or "action", handler, payload)
        else:
            callback_data = callback
        
        button = KeyboardButton(
            text=text,
            callback_data=callback_data,
            callback_handler=handler,
            payload=payload,
            **kwargs
        )
        self._current_row.append(button)
        return self
    
    def add_back_button(
        self,
        text: str = "◀️ Back",
        step: Optional[str] = None
    ) -> "InteractiveKeyboardBuilder":
        """Add a back button."""
        payload = {"action": "back", "target_step": step}
        return self.add_button(text, callback="back", payload=payload)
    
    def add_cancel_button(
        self,
        text: str = "❌ Cancel"
    ) -> "InteractiveKeyboardBuilder":
        """Add a cancel button."""
        return self.add_button(text, callback="cancel", payload={"action": "cancel"})
    
    def add_confirm_button(
        self,
        text: str = "✅ Confirm",
        handler: str = "on_confirm"
    ) -> "InteractiveKeyboardBuilder":
        """Add a confirm button."""
        return self.add_button(text, callback="confirm", handler=handler)
    
    def build(self) -> KeyboardLayout:
        """Build the keyboard layout."""
        if self._current_row:
            self._rows.append(self._current_row)
        
        return KeyboardLayout(
            buttons=self._rows,
            layout_id=self._flow_type,
        )
    
    async def send(
        self,
        text: str,
        chat_id: int,
        parse_mode: str = "HTML"
    ) -> tuple[int, KeyboardState]:
        """
        Send the keyboard and create state.
        
        Returns:
            Tuple of (message_id, state)
        """
        layout = self.build()
        
        # Create state
        state = await self.state_manager.create_state(
            group_id=self.group_id,
            user_id=self.user_id,
            flow_type=self._flow_type,
            initial_data=self._initial_data,
        )
        
        # Update callback data to include state_id
        for row in layout.buttons:
            for btn in row:
                if btn.callback_data and not btn.callback_data.startswith("http"):
                    btn.callback_data = f"{state.state_id}:{btn.callback_data}"
        
        # Send message
        if self.bot:
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=layout.to_markup(),
                parse_mode=parse_mode,
            )
            
            # Update state with message info
            state.message_id = message.message_id
            state.chat_id = chat_id
            await self.state_manager.update_state(state)
            
            return message.message_id, state
        
        raise ValueError("Bot instance required to send keyboard")
    
    def _encode_callback(
        self,
        action: str,
        handler: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> str:
        """Encode callback data with handler and payload."""
        data = {"a": action}
        if handler:
            data["h"] = handler
        if payload:
            data["p"] = payload
        
        # Compress to fit in 64-byte limit
        json_str = json.dumps(data, separators=(',', ':'))
        if len(json_str) > 60:
            # Truncate payload if too long
            data["p"] = {"_truncated": True}
            json_str = json.dumps(data, separators=(',', ':'))
        
        return json_str


class KeyboardCallbackRouter:
    """
    Router for handling keyboard callbacks with state restoration.
    
    Automatically extracts state_id from callback data and restores
    the associated state for the handler.
    """
    
    def __init__(self, state_manager: KeyboardStateManager):
        self.state_manager = state_manager
        self._routes: Dict[str, Callable] = {}
    
    def route(self, pattern: str):
        """Decorator to register a callback handler."""
        def decorator(func: Callable):
            self._routes[pattern] = func
            return func
        return decorator
    
    async def handle(self, callback_query: CallbackQuery) -> bool:
        """
        Handle a callback query.
        
        Extracts state_id from callback_data, restores state,
        and routes to the appropriate handler.
        
        Returns:
            True if handled, False otherwise
        """
        if not callback_query.data:
            return False
        
        # Parse callback data (format: state_id:action or just action)
        parts = callback_query.data.split(":", 1)
        
        if len(parts) == 2:
            state_id, action = parts
            state = await self.state_manager.get_state(state_id)
        else:
            state_id = None
            action = parts[0]
            state = None
        
        # Handle special actions
        if action == "cancel":
            if state:
                await self.state_manager.cancel_state(state_id, "user_cancelled")
            await callback_query.answer("Cancelled")
            await callback_query.message.delete()
            return True
        
        if action == "back":
            if state and state.history:
                prev_step = state.history[-1]["from_step"]
                await self.state_manager.transition_state(state_id, prev_step)
                await callback_query.answer()
                # Would trigger re-render here
                return True
        
        # Route to handler
        handler = self._routes.get(action)
        if handler:
            try:
                await handler(callback_query, state)
                return True
            except Exception as e:
                print(f"Error in callback handler: {e}")
                await callback_query.answer("Error processing action")
                return True
        
        return False


# Global state manager cache
_state_managers: Dict[int, KeyboardStateManager] = {}


async def get_keyboard_state_manager(group_id: int) -> KeyboardStateManager:
    """Get or create a state manager for a group."""
    if group_id not in _state_managers:
        redis = await get_group_redis(group_id)
        _state_managers[group_id] = KeyboardStateManager(redis)
    return _state_managers[group_id]


@asynccontextmanager
async def keyboard_session(
    group_id: int,
    user_id: int,
    flow_type: str,
    initial_data: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 300
):
    """
    Context manager for keyboard sessions.
    
    Usage:
        async with keyboard_session(group_id, user_id, "wizard") as state:
            # Use state
            state.data["key"] = "value"
    """
    manager = await get_keyboard_state_manager(group_id)
    state = await manager.create_state(
        group_id=group_id,
        user_id=user_id,
        flow_type=flow_type,
        initial_data=initial_data,
        timeout_seconds=timeout_seconds,
    )
    
    try:
        yield state
    finally:
        await manager.complete_state(state.state_id)
