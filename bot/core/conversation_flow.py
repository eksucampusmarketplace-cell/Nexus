"""
Conversation Flow Engine

Multi-step interactive flows for complex user interactions.
Unlike simple keyboards, flows maintain complex state across multiple
steps with validation, branching, and rollback capabilities.

Use cases:
- Onboarding flows
- Configuration wizards
- Report filing
- Survey/forms
- Multi-step moderation
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, TypeVar, Union
from abc import ABC, abstractmethod

from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from shared.redis_client import GroupScopedRedis


T = TypeVar('T')


class FlowStepType(str, Enum):
    """Types of flow steps."""
    TEXT_INPUT = "text_input"
    NUMBER_INPUT = "number_input"
    CHOICE = "choice"  # Single choice
    MULTI_CHOICE = "multi_choice"
    CONFIRM = "confirm"
    DISPLAY = "display"  # Just show info
    CONDITIONAL = "conditional"  # Branch based on condition
    EXTERNAL = "external"  # Call external service
    COMPLETE = "complete"
    CANCEL = "cancel"


class FlowStatus(str, Enum):
    """Status of a flow instance."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"
    TIMEOUT = "timeout"


class ValidationResult:
    """Result of input validation."""
    
    def __init__(
        self,
        is_valid: bool,
        value: Any = None,
        error_message: Optional[str] = None,
        transformed_value: Any = None,
    ):
        self.is_valid = is_valid
        self.value = value
        self.error_message = error_message
        self.transformed_value = transformed_value if transformed_value is not None else value
    
    @classmethod
    def success(cls, value: Any, transformed: Any = None):
        return cls(True, value, None, transformed)
    
    @classmethod
    def failure(cls, error_message: str, value: Any = None):
        return cls(False, value, error_message, None)


class Validator(ABC):
    """Base class for input validators."""
    
    @abstractmethod
    async def validate(self, value: Any, context: Dict[str, Any]) -> ValidationResult:
        """Validate a value."""
        pass


class TextLengthValidator(Validator):
    """Validate text length."""
    
    def __init__(self, min_len: int = 0, max_len: int = 1000):
        self.min_len = min_len
        self.max_len = max_len
    
    async def validate(self, value: Any, context: Dict[str, Any]) -> ValidationResult:
        text = str(value)
        if len(text) < self.min_len:
            return ValidationResult.failure(
                f"Text must be at least {self.min_len} characters"
            )
        if len(text) > self.max_len:
            return ValidationResult.failure(
                f"Text must be at most {self.max_len} characters"
            )
        return ValidationResult.success(text)


class NumberRangeValidator(Validator):
    """Validate number range."""
    
    def __init__(self, min_val: Optional[float] = None, max_val: Optional[float] = None):
        self.min_val = min_val
        self.max_val = max_val
    
    async def validate(self, value: Any, context: Dict[str, Any]) -> ValidationResult:
        try:
            num = float(value)
        except (ValueError, TypeError):
            return ValidationResult.failure("Please enter a valid number")
        
        if self.min_val is not None and num < self.min_val:
            return ValidationResult.failure(f"Number must be at least {self.min_val}")
        
        if self.max_val is not None and num > self.max_val:
            return ValidationResult.failure(f"Number must be at most {self.max_val}")
        
        return ValidationResult.success(value, num)


class RegexValidator(Validator):
    """Validate with regex pattern."""
    
    def __init__(self, pattern: str, error_message: str = "Invalid format"):
        self.pattern = re.compile(pattern)
        self.error_message = error_message
    
    async def validate(self, value: Any, context: Dict[str, Any]) -> ValidationResult:
        if not self.pattern.match(str(value)):
            return ValidationResult.failure(self.error_message)
        return ValidationResult.success(value)


@dataclass
class FlowChoice:
    """A choice option for choice steps."""
    id: str
    label: str
    value: Any = None
    description: Optional[str] = None
    emoji: Optional[str] = None
    next_step: Optional[str] = None  # Override next step
    condition: Optional[str] = None  # Show only if condition met


@dataclass
class FlowStep:
    """
    A single step in a conversation flow.
    """
    step_id: str
    step_type: FlowStepType
    
    # Content
    title: Optional[str] = None
    description: Optional[str] = None
    prompt: str = ""
    
    # Input handling
    validators: List[Validator] = field(default_factory=list)
    placeholder: Optional[str] = None
    
    # Choices (for choice steps)
    choices: List[FlowChoice] = field(default_factory=list)
    allow_custom: bool = False  # Allow free text input for choice
    
    # Navigation
    next_step: Optional[str] = None  # Default next step
    back_step: Optional[str] = None  # Where to go on 'back'
    skip_allowed: bool = False
    
    # Branching
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    branches: Dict[str, str] = field(default_factory=dict)  # value -> next_step
    
    # External
    external_handler: Optional[Callable] = None
    
    # UI
    buttons_per_row: int = 2
    show_progress: bool = True
    
    # Timeouts
    timeout_seconds: int = 300
    timeout_action: str = "cancel"  # cancel, complete, pause
    
    # Hooks
    on_enter: Optional[Callable] = None
    on_exit: Optional[Callable] = None
    on_validate: Optional[Callable] = None


@dataclass
class FlowInstance:
    """
    An active instance of a flow.
    """
    # Identity
    instance_id: str
    flow_id: str
    group_id: int
    user_id: int
    chat_id: int
    
    # State
    current_step_id: Optional[str] = None
    step_history: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    status: FlowStatus = FlowStatus.ACTIVE
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Messages
    prompt_message_id: Optional[int] = None
    current_message_id: Optional[int] = None
    
    # Error handling
    error_count: int = 0
    last_error: Optional[str] = None
    
    # Results
    results: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "flow_id": self.flow_id,
            "group_id": self.group_id,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "current_step_id": self.current_step_id,
            "step_history": self.step_history,
            "data": self.data,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "prompt_message_id": self.prompt_message_id,
            "current_message_id": self.current_message_id,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "results": self.results,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FlowInstance":
        return cls(
            instance_id=data["instance_id"],
            flow_id=data["flow_id"],
            group_id=data["group_id"],
            user_id=data["user_id"],
            chat_id=data["chat_id"],
            current_step_id=data.get("current_step_id"),
            step_history=data.get("step_history", []),
            data=data.get("data", {}),
            status=FlowStatus(data.get("status", "active")),
            started_at=datetime.fromisoformat(data["started_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            prompt_message_id=data.get("prompt_message_id"),
            current_message_id=data.get("current_message_id"),
            error_count=data.get("error_count", 0),
            last_error=data.get("last_error"),
            results=data.get("results", {}),
        )
    
    def is_expired(self, timeout_seconds: int = 300) -> bool:
        """Check if flow has expired due to inactivity."""
        elapsed = (datetime.utcnow() - self.last_activity).total_seconds()
        return elapsed > timeout_seconds
    
    def record_step(self, step_id: str):
        """Record navigation to a step."""
        self.step_history.append(step_id)
        self.current_step_id = step_id
        self.last_activity = datetime.utcnow()
    
    def go_back(self) -> Optional[str]:
        """Navigate back to previous step."""
        if len(self.step_history) < 2:
            return None
        
        # Remove current
        self.step_history.pop()
        # Get previous
        previous = self.step_history[-1]
        self.current_step_id = previous
        self.last_activity = datetime.utcnow()
        return previous
    
    def set_data(self, key: str, value: Any):
        """Set data value."""
        self.data[key] = value
        self.results[key] = value
        self.last_activity = datetime.utcnow()
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data value."""
        return self.data.get(key, default)


class ConversationFlow:
    """
    Defines a conversation flow with steps and transitions.
    """
    
    def __init__(
        self,
        flow_id: str,
        name: str,
        description: str = "",
        first_step: str = "start",
    ):
        self.flow_id = flow_id
        self.name = name
        self.description = description
        self.first_step = first_step
        
        self.steps: Dict[str, FlowStep] = {}
        self.on_complete: Optional[Callable[[FlowInstance], Coroutine]] = None
        self.on_cancel: Optional[Callable[[FlowInstance], Coroutine]] = None
        self.on_error: Optional[Callable[[FlowInstance, Exception], Coroutine]] = None
    
    def add_step(self, step: FlowStep) -> "ConversationFlow":
        """Add a step to the flow."""
        self.steps[step.step_id] = step
        return self
    
    def get_step(self, step_id: str) -> Optional[FlowStep]:
        """Get a step by ID."""
        return self.steps.get(step_id)
    
    def get_first_step(self) -> Optional[FlowStep]:
        """Get the first step."""
        return self.steps.get(self.first_step)


class FlowEngine:
    """
    Engine for managing and executing conversation flows.
    """
    
    def __init__(self, redis: GroupScopedRedis, bot):
        self.redis = redis
        self.bot = bot
        self.flows: Dict[str, ConversationFlow] = {}
        self._active_instances: Dict[str, FlowInstance] = {}
    
    def _instance_key(self, instance_id: str) -> str:
        return f"flow:instance:{instance_id}"
    
    def _user_flow_key(self, user_id: int) -> str:
        return f"flow:user:{user_id}:active"
    
    def register_flow(self, flow: ConversationFlow):
        """Register a flow definition."""
        self.flows[flow.flow_id] = flow
    
    async def start_flow(
        self,
        flow_id: str,
        group_id: int,
        user_id: int,
        chat_id: int,
        initial_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[FlowInstance]:
        """
        Start a new flow instance.
        
        Returns:
            FlowInstance or None if flow not found or user already in flow
        """
        flow = self.flows.get(flow_id)
        if not flow:
            return None
        
        # Check if user already has active flow
        existing = await self.get_user_active_flow(user_id, group_id)
        if existing:
            # Cancel existing
            await self.cancel_flow(existing.instance_id, "new_flow_started")
        
        # Create instance
        instance_id = f"flow_{flow_id}_{group_id}_{user_id}_{datetime.utcnow().timestamp()}"
        instance = FlowInstance(
            instance_id=instance_id,
            flow_id=flow_id,
            group_id=group_id,
            user_id=user_id,
            chat_id=chat_id,
            data=initial_data or {},
            results=initial_data or {},
        )
        
        # Store
        await self._save_instance(instance)
        await self.redis.set(self._user_flow_key(user_id), instance_id, expire=3600)
        
        # Start first step
        await self._enter_step(instance, flow.first_step)
        
        return instance
    
    async def handle_message(self, message: Message) -> Optional[FlowInstance]:
        """
        Handle a message as potential flow input.
        
        Returns:
            FlowInstance if handled, None otherwise
        """
        if not message.from_user:
            return None
        
        user_id = message.from_user.id
        group_id = message.chat.id
        
        instance = await self.get_user_active_flow(user_id, group_id)
        if not instance:
            return None
        
        # Check expiration
        flow = self.flows.get(instance.flow_id)
        if not flow:
            await self.cancel_flow(instance.instance_id, "flow_not_found")
            return None
        
        step = flow.get_step(instance.current_step_id) if instance.current_step_id else None
        if not step:
            await self.cancel_flow(instance.instance_id, "step_not_found")
            return None
        
        if instance.is_expired(step.timeout_seconds):
            await self.timeout_flow(instance.instance_id)
            return None
        
        # Process input based on step type
        if step.step_type in (FlowStepType.TEXT_INPUT, FlowStepType.NUMBER_INPUT):
            result = await self._process_text_input(instance, step, message.text or "")
        elif step.step_type == FlowStepType.CHOICE and step.allow_custom:
            result = await self._process_choice_input(instance, step, message.text or "")
        else:
            # Not expecting text input
            return instance
        
        if result:
            instance = result
            await self._save_instance(instance)
        
        return instance
    
    async def handle_callback(self, callback: CallbackQuery) -> Optional[FlowInstance]:
        """
        Handle a callback query as flow interaction.
        """
        if not callback.from_user or not callback.data:
            return None
        
        user_id = callback.from_user.id
        
        instance = await self.get_user_active_flow(user_id)
        if not instance:
            return None
        
        # Parse callback data
        parts = callback.data.split(":")
        if len(parts) < 2:
            return None
        
        action = parts[0]
        value = parts[1] if len(parts) > 1 else None
        
        flow = self.flows.get(instance.flow_id)
        step = flow.get_step(instance.current_step_id) if instance.current_step_id else None
        
        if action == "flow_choice" and value:
            await self._process_choice_input(instance, step, value)
        elif action == "flow_back":
            await self._go_back(instance)
        elif action == "flow_cancel":
            await self.cancel_flow(instance.instance_id, "user_cancelled")
        elif action == "flow_skip":
            await self._skip_step(instance)
        
        await self._save_instance(instance)
        await callback.answer()
        
        return instance
    
    async def get_user_active_flow(
        self,
        user_id: int,
        group_id: Optional[int] = None,
    ) -> Optional[FlowInstance]:
        """Get user's active flow instance."""
        instance_id = await self.redis.get(self._user_flow_key(user_id))
        if not instance_id:
            return None
        
        instance = await self._load_instance(instance_id)
        if not instance:
            return None
        
        if group_id and instance.group_id != group_id:
            return None
        
        return instance
    
    async def cancel_flow(self, instance_id: str, reason: str = "cancelled"):
        """Cancel a flow instance."""
        instance = await self._load_instance(instance_id)
        if not instance:
            return
        
        instance.status = FlowStatus.CANCELLED
        instance.completed_at = datetime.utcnow()
        instance.data["cancel_reason"] = reason
        
        await self._cleanup_instance(instance)
        
        # Trigger callback
        flow = self.flows.get(instance.flow_id)
        if flow and flow.on_cancel:
            try:
                await flow.on_cancel(instance)
            except Exception as e:
                print(f"Error in on_cancel: {e}")
    
    async def complete_flow(self, instance_id: str, final_data: Optional[Dict[str, Any]] = None):
        """Complete a flow instance."""
        instance = await self._load_instance(instance_id)
        if not instance:
            return
        
        instance.status = FlowStatus.COMPLETED
        instance.completed_at = datetime.utcnow()
        
        if final_data:
            instance.results.update(final_data)
        
        await self._cleanup_instance(instance)
        
        # Trigger callback
        flow = self.flows.get(instance.flow_id)
        if flow and flow.on_complete:
            try:
                await flow.on_complete(instance)
            except Exception as e:
                print(f"Error in on_complete: {e}")
    
    async def timeout_flow(self, instance_id: str):
        """Handle flow timeout."""
        instance = await self._load_instance(instance_id)
        if not instance:
            return
        
        instance.status = FlowStatus.TIMEOUT
        instance.completed_at = datetime.utcnow()
        
        await self._cleanup_instance(instance)
        
        # Notify user
        try:
            await self.bot.send_message(
                chat_id=instance.chat_id,
                text="⏱️ This session has expired due to inactivity.",
            )
        except Exception:
            pass
    
    async def _enter_step(self, instance: FlowInstance, step_id: str):
        """Enter a flow step."""
        flow = self.flows.get(instance.flow_id)
        step = flow.get_step(step_id) if flow else None
        
        if not step:
            await self.complete_flow(instance.instance_id)
            return
        
        instance.record_step(step_id)
        
        # Call on_enter hook
        if step.on_enter:
            try:
                await step.on_enter(instance, step)
            except Exception as e:
                print(f"Error in on_enter: {e}")
        
        # Send prompt
        await self._send_step_prompt(instance, step)
        await self._save_instance(instance)
    
    async def _send_step_prompt(self, instance: FlowInstance, step: FlowStep):
        """Send the prompt for a step."""
        # Build text
        lines = []
        
        if step.title:
            lines.append(f"<b>{step.title}</b>")
        
        if step.description:
            lines.append(step.description)
        
        lines.append(step.prompt)
        
        # Add progress indicator
        if step.show_progress:
            progress = len(instance.step_history)
            lines.append(f"\n<i>Step {progress}</i>")
        
        text = "\n\n".join(lines)
        
        # Build keyboard based on step type
        keyboard = []
        
        if step.step_type in (FlowStepType.CHOICE, FlowStepType.MULTI_CHOICE):
            row = []
            for choice in step.choices:
                # Check condition
                if choice.condition and not self._evaluate_condition(choice.condition, instance.data):
                    continue
                
                btn = InlineKeyboardButton(
                    text=f"{choice.emoji or ''} {choice.label}".strip(),
                    callback_data=f"flow_choice:{choice.id}",
                )
                row.append(btn)
                
                if len(row) >= step.buttons_per_row:
                    keyboard.append(row)
                    row = []
            
            if row:
                keyboard.append(row)
        
        # Navigation buttons
        nav_row = []
        
        if len(instance.step_history) > 1:
            nav_row.append(InlineKeyboardButton(
                text="◀️ Back",
                callback_data="flow_back",
            ))
        
        if step.skip_allowed:
            nav_row.append(InlineKeyboardButton(
                text="⏭️ Skip",
                callback_data="flow_skip",
            ))
        
        nav_row.append(InlineKeyboardButton(
            text="❌ Cancel",
            callback_data="flow_cancel",
        ))
        
        keyboard.append(nav_row)
        
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        # Send or edit message
        try:
            if instance.current_message_id:
                await self.bot.edit_message_text(
                    chat_id=instance.chat_id,
                    message_id=instance.current_message_id,
                    text=text,
                    reply_markup=markup,
                    parse_mode="HTML",
                )
            else:
                msg = await self.bot.send_message(
                    chat_id=instance.chat_id,
                    text=text,
                    reply_markup=markup,
                    parse_mode="HTML",
                )
                instance.current_message_id = msg.message_id
        except Exception as e:
            print(f"Error sending step prompt: {e}")
    
    async def _process_text_input(
        self,
        instance: FlowInstance,
        step: FlowStep,
        text: str,
    ) -> Optional[FlowInstance]:
        """Process text input for a step."""
        # Run validators
        for validator in step.validators:
            result = await validator.validate(text, instance.data)
            if not result.is_valid:
                # Send error
                await self.bot.send_message(
                    chat_id=instance.chat_id,
                    text=f"❌ {result.error_message}\n\nPlease try again:",
                )
                instance.error_count += 1
                instance.last_error = result.error_message
                return instance
            text = result.transformed_value
        
        # Store value
        instance.set_data(step.step_id, text)
        
        # Call on_exit hook
        if step.on_exit:
            try:
                await step.on_exit(instance, step, text)
            except Exception as e:
                print(f"Error in on_exit: {e}")
        
        # Move to next step
        next_step = self._determine_next_step(instance, step, text)
        await self._enter_step(instance, next_step)
        
        return instance
    
    async def _process_choice_input(
        self,
        instance: FlowInstance,
        step: Optional[FlowStep],
        value: str,
    ):
        """Process choice input."""
        if not step:
            return
        
        # Find choice
        choice = next((c for c in step.choices if c.id == value), None)
        
        if choice:
            instance.set_data(step.step_id, choice.value or choice.id)
            next_step = choice.next_step or step.next_step
        else:
            # Custom input
            instance.set_data(step.step_id, value)
            next_step = step.next_step
        
        # Move to next step
        if next_step:
            await self._enter_step(instance, next_step)
        else:
            await self.complete_flow(instance.instance_id)
    
    async def _go_back(self, instance: FlowInstance):
        """Navigate back."""
        previous = instance.go_back()
        if previous:
            await self._enter_step(instance, previous)
    
    async def _skip_step(self, instance: FlowInstance):
        """Skip current step."""
        flow = self.flows.get(instance.flow_id)
        step = flow.get_step(instance.current_step_id) if instance.current_step_id else None
        
        if step and step.next_step:
            await self._enter_step(instance, step.next_step)
        else:
            await self.complete_flow(instance.instance_id)
    
    def _determine_next_step(self, instance: FlowInstance, step: FlowStep, value: Any) -> str:
        """Determine the next step based on branching."""
        # Check branches
        if value in step.branches:
            return step.branches[value]
        
        # Default next step
        if step.next_step:
            return step.next_step
        
        # Complete if no next step
        return "__complete__"
    
    def _evaluate_condition(self, condition: str, data: Dict[str, Any]) -> bool:
        """Evaluate a simple condition string."""
        # Simple implementation - could use a proper expression evaluator
        try:
            return eval(condition, {"__builtins__": {}}, data)
        except:
            return False
    
    async def _save_instance(self, instance: FlowInstance):
        """Save instance to Redis."""
        key = self._instance_key(instance.instance_id)
        await self.redis.set_json(key, instance.to_dict(), expire=3600)
    
    async def _load_instance(self, instance_id: str) -> Optional[FlowInstance]:
        """Load instance from Redis."""
        data = await self.redis.get_json(self._instance_key(instance_id))
        if not data:
            return None
        return FlowInstance.from_dict(data)
    
    async def _cleanup_instance(self, instance: FlowInstance):
        """Clean up instance data."""
        await self.redis.delete(self._instance_key(instance.instance_id))
        await self.redis.delete(self._user_flow_key(instance.user_id))


# Pre-built flows

async def create_report_flow() -> ConversationFlow:
    """Create a user report flow."""
    flow = ConversationFlow(
        flow_id="user_report",
        name="Report User",
        description="Report a user for moderation review",
        first_step="select_reason",
    )
    
    flow.add_step(FlowStep(
        step_id="select_reason",
        step_type=FlowStepType.CHOICE,
        title="Report User",
        description="Please select a reason for your report:",
        prompt="What type of issue are you reporting?",
        choices=[
            FlowChoice("spam", "🚫 Spam", "spam"),
            FlowChoice("harassment", "😠 Harassment", "harassment"),
            FlowChoice("nsfw", "🔞 Inappropriate Content", "nsfw"),
            FlowChoice("other", "📋 Other", "other"),
        ],
        next_step="describe_issue",
    ))
    
    flow.add_step(FlowStep(
        step_id="describe_issue",
        step_type=FlowStepType.TEXT_INPUT,
        title="Describe the Issue",
        prompt="Please provide more details about the issue:",
        validators=[TextLengthValidator(min_len=10, max_len=500)],
        next_step="provide_evidence",
    ))
    
    flow.add_step(FlowStep(
        step_id="provide_evidence",
        step_type=FlowStepType.CHOICE,
        title="Evidence",
        prompt="Do you have screenshots or links as evidence?",
        choices=[
            FlowChoice("yes", "✅ Yes, I'll provide it", "yes"),
            FlowChoice("no", "❌ No evidence", "no"),
        ],
        next_step="confirm",
    ))
    
    flow.add_step(FlowStep(
        step_id="confirm",
        step_type=FlowStepType.CONFIRM,
        title="Confirm Report",
        prompt="Are you ready to submit this report?",
        choices=[
            FlowChoice("yes", "✅ Submit Report", "yes"),
            FlowChoice("no", "❌ Cancel", "no"),
        ],
        next_step="__complete__",
    ))
    
    return flow


async def create_onboarding_flow() -> ConversationFlow:
    """Create a new user onboarding flow."""
    flow = ConversationFlow(
        flow_id="user_onboarding",
        name="Welcome",
        description="Welcome new users to the group",
        first_step="welcome",
    )
    
    flow.add_step(FlowStep(
        step_id="welcome",
        step_type=FlowStepType.DISPLAY,
        title="Welcome! 👋",
        description="Welcome to our community! Let's get you set up.",
        prompt="Please take a moment to review our community guidelines.",
        next_step="accept_rules",
    ))
    
    flow.add_step(FlowStep(
        step_id="accept_rules",
        step_type=FlowStepType.CONFIRM,
        title="Community Rules",
        prompt="Do you agree to follow our community guidelines?",
        choices=[
            FlowChoice("yes", "✅ I Agree", True),
            FlowChoice("no", "❌ I Don't Agree", False),
        ],
        next_step="introduce",
    ))
    
    flow.add_step(FlowStep(
        step_id="introduce",
        step_type=FlowStepType.TEXT_INPUT,
        title="Introduction",
        prompt="Tell us a bit about yourself (optional):",
        validators=[TextLengthValidator(max_len=200)],
        skip_allowed=True,
        next_step="__complete__",
    ))
    
    return flow
