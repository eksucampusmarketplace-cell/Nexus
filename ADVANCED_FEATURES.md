# Nexus Advanced Features

This document describes the advanced features built for the Nexus Telegram Bot Platform.

## Table of Contents

1. [Inline Keyboard State Management](#1-inline-keyboard-state-management)
2. [Advanced Poll System](#2-advanced-poll-system)
3. [Message Threading](#3-message-threading)
4. [Smart Notification System](#4-smart-notification-system)
5. [Conversation Flow Engine](#5-conversation-flow-engine)
6. [Content Moderation Pipeline](#6-content-moderation-pipeline)

---

## 1. Inline Keyboard State Management

### Problem
Telegram's inline keyboards have no native state management. Once sent, you cannot track user interactions across sessions without building your own state layer.

### Solution
Redis-backed keyboard state management that provides:
- Persistent keyboard state across sessions
- Multi-step interactive flows
- State recovery after bot restarts
- Automatic cleanup and expiration

### Key Components

#### KeyboardState
```python
@dataclass
class KeyboardState:
    state_id: str
    group_id: int
    user_id: int
    current_step: str
    data: Dict[str, Any]
    history: List[Dict[str, Any]]
    status: KeyboardStateStatus
```

#### KeyboardStateManager
Core methods:
- `create_state()` - Create new keyboard session
- `get_state()` - Retrieve existing state
- `transition_state()` - Move to next step
- `complete_state()` - Mark as completed
- `cancel_state()` - Cancel session

#### InteractiveKeyboardBuilder
Fluent builder for creating keyboards:
```python
builder = InteractiveKeyboardBuilder(state_manager, group_id, user_id)
keyboard = (
    builder
    .with_state("wizard", initial_data={"step": 1})
    .add_row()
    .add_button("Option 1", callback="opt1", handler="on_option_1")
    .add_back_button()
    .add_cancel_button()
    .build()
)
```

### Usage Example
```python
from bot.core.keyboard_state import get_keyboard_state_manager

async def create_interactive_menu(ctx: NexusContext):
    manager = await get_keyboard_state_manager(ctx.group.id)
    
    state = await manager.create_state(
        group_id=ctx.group.id,
        user_id=ctx.user.user_id,
        flow_type="settings_wizard",
        initial_data={"category": None, "settings": {}}
    )
    
    # Send keyboard with state
    # ... handle callbacks with state restoration
```

---

## 2. Advanced Poll System

### Problem
Telegram's native polls are limited:
- No timed closing with callbacks
- No vote-based moderation actions
- No recurring polls
- No poll history or analytics

### Solution
Extended poll system that wraps and enhances native polls:
- Timed closing with configurable callbacks
- Vote-based moderation (ban/mute at threshold)
- Weighted voting by role/reputation
- Recurring polls with scheduling
- Comprehensive analytics

### Key Components

#### AdvancedPoll
```python
@dataclass
class AdvancedPoll:
    poll_id: str
    question: str
    options: List[PollOption]
    poll_type: PollType  # SINGLE, MULTIPLE, QUIZ, RANKED, WEIGHTED
    closes_at: Optional[datetime]
    vote_actions: List[PollVoteAction]
    is_recurring: bool
    analytics: PollAnalytics
```

#### PollVoteAction
```python
@dataclass
class PollVoteAction:
    action_type: VoteAction  # BAN, MUTE, KICK, PIN, ANNOUNCE
    threshold_type: str  # percentage, count, majority
    threshold_value: float
    target_user_id: Optional[int]
```

#### AdvancedPollManager
Core methods:
- `create_poll()` - Create extended poll
- `record_vote()` - Record weighted vote
- `close_poll()` - Close and calculate results
- `create_recurring_instance()` - Spawn recurring poll

### Usage Example
```python
from bot.modules.polls.advanced_poll_system import AdvancedPollManager, PollType, VoteAction

async def create_moderation_poll(ctx: NexusContext, target_user_id: int):
    manager = AdvancedPollManager(redis)
    
    poll = await manager.create_poll(
        group_id=ctx.group.id,
        created_by=ctx.user.user_id,
        question=f"Should we ban user {target_user_id}?",
        options=["Yes", "No", "Abstain"],
        poll_type=PollType.SINGLE,
        closes_at=datetime.utcnow() + timedelta(hours=24),
        vote_actions=[{
            "action_type": VoteAction.BAN,
            "threshold_type": "majority",
            "threshold_value": 0.66,
            "target_user_id": target_user_id
        }]
    )
```

---

## 3. Message Threading

### Problem
Telegram has reply threads but bots have no native concept of a conversation thread as a unit. You cannot summarize, moderate, or analyze a whole thread.

### Solution
Thread-aware context system:
- Automatic thread detection and creation
- Thread-level moderation (lock, archive, slow mode)
- Conversation summarization
- Thread forking

### Key Components

#### ConversationThread
```python
@dataclass
class ConversationThread:
    thread_id: str
    root_message_id: int
    thread_type: ThreadType  # QUESTION, DISCUSSION, DEBATE, etc.
    messages: deque[ThreadMessage]
    participants: Dict[int, ThreadParticipant]
    summary: Optional[ThreadSummary]
    status: ThreadStatus
```

#### ThreadContextManager
Core methods:
- `detect_or_create_thread()` - Auto-detect thread from message
- `create_thread()` - Manual thread creation
- `fork_thread()` - Fork thread at message
- `moderate_thread()` - Lock, archive, restrict
- `summarize_thread()` - Generate summary

#### ThreadAwareContext
Wrapper for NexusContext:
```python
thread_ctx = ThreadAwareContext(ctx, manager)
thread = await thread_ctx.get_current_thread()
summary = await thread_ctx.summarize_current_thread()
```

### Usage Example
```python
from bot.core.thread_context import ThreadContextManager, ThreadAwareContext

async def handle_message(ctx: NexusContext):
    manager = await get_thread_manager(ctx.group.id)
    
    # Auto-detect or create thread
    thread, is_new = await manager.detect_or_create_thread(
        group_id=ctx.group.id,
        message=ctx.message,
        user_role=ctx.user.role.value
    )
    
    if is_new:
        await ctx.reply(f"🧵 New {thread.thread_type.value} thread started!")
```

---

## 4. Smart Notification System

### Problem
Telegram's bot notifications are all-or-nothing. Admins cannot configure which actions trigger notifications, volume thresholds, or delivery channels.

### Solution
Smart notification layer with:
- Configurable notification rules per action type
- Volume threshold batching
- Multiple delivery channels (group, DM, log channel)
- Quiet hours with priority override
- Digest modes for non-urgent notifications

### Key Components

#### NotificationRule
```python
@dataclass
class NotificationRule:
    action_categories: Set[ActionCategory]
    priority: NotificationPriority
    channels: List[NotificationChannel]
    volume_threshold: int
    time_window_minutes: int
    quiet_hours: QuietHours
    digest_mode: bool
```

#### NotificationManager
Core methods:
- `create_rule()` - Create notification rule
- `process_action()` - Generate notifications for action
- `process_digests()` - Send batched digests

### Usage Example
```python
from bot.core.notification_system import (
    get_notification_manager,
    NotificationRule,
    ActionCategory,
    NotificationPriority,
    NotificationChannel,
    QuietHours
)

async def setup_notifications(group_id: int):
    manager = await get_notification_manager(group_id)
    
    rule = NotificationRule(
        rule_id="mod_alerts",
        group_id=group_id,
        action_categories={ActionCategory.MODERATION, ActionCategory.SECURITY},
        priority=NotificationPriority.HIGH,
        channels=[NotificationChannel.LOG_CHANNEL, NotificationChannel.PRIVATE],
        target_roles={"owner", "admin"},
        quiet_hours=QuietHours(enabled=True, start_time="22:00", end_time="08:00"),
        volume_threshold=3,  # Batch if 3+ in 5 minutes
        time_window_minutes=5
    )
    
    await manager.create_rule(rule)
```

---

## 5. Conversation Flow Engine

### Problem
Complex multi-step interactions (onboarding, reports, wizards) are difficult to implement with simple state machines.

### Solution
Multi-step flow engine with:
- Step-by-step navigation with back/forward
- Input validation with pluggable validators
- Conditional branching
- External service integration
- Timeout handling

### Key Components

#### FlowStep
```python
@dataclass
class FlowStep:
    step_id: str
    step_type: FlowStepType  # TEXT_INPUT, CHOICE, CONFIRM, etc.
    prompt: str
    validators: List[Validator]
    choices: List[FlowChoice]
    next_step: Optional[str]
    branches: Dict[str, str]  # value -> next_step
    condition: Optional[Callable]
```

#### FlowEngine
Core methods:
- `start_flow()` - Begin new flow instance
- `handle_message()` - Process flow input
- `handle_callback()` - Process button clicks

### Pre-built Flows

#### User Report Flow
```python
from bot.core.conversation_flow import create_report_flow

flow = await create_report_flow()
engine.register_flow(flow)

instance = await engine.start_flow(
    flow_id="user_report",
    group_id=group_id,
    user_id=user_id,
    chat_id=chat_id
)
```

#### Onboarding Flow
```python
from bot.core.conversation_flow import create_onboarding_flow

flow = await create_onboarding_flow()
engine.register_flow(flow)
```

### Custom Flow Example
```python
from bot.core.conversation_flow import ConversationFlow, FlowStep, FlowStepType

flow = ConversationFlow(
    flow_id="custom_survey",
    name="User Survey",
    first_step="ask_age"
)

flow.add_step(FlowStep(
    step_id="ask_age",
    step_type=FlowStepType.NUMBER_INPUT,
    title="Survey",
    prompt="How old are you?",
    validators=[NumberRangeValidator(min_val=13, max_val=120)],
    next_step="ask_interests"
))

flow.add_step(FlowStep(
    step_id="ask_interests",
    step_type=FlowStepType.MULTI_CHOICE,
    prompt="What are your interests?",
    choices=[
        FlowChoice("tech", "💻 Technology"),
        FlowChoice("gaming", "🎮 Gaming"),
        FlowChoice("music", "🎵 Music"),
    ],
    next_step="confirm"
))
```

---

## 6. Content Moderation Pipeline

### Problem
Content moderation needs to be fast, accurate, and configurable. Single-pass checks are insufficient for complex moderation needs.

### Solution
Multi-stage content pipeline:
1. Pre-filter (fast regex, allowlist/blocklist)
2. Content extraction (entities, links, features)
3. Feature analysis (spam, toxicity, duplicates)
4. Policy enforcement (actions based on scores)
5. Post-processing (logging, notifications)

### Key Components

#### ContentAnalyzer
```python
class ContentAnalyzer(ABC):
    name: str
    categories: List[str]
    
    async def analyze(self, record: ContentRecord) -> AnalysisResult:
        # Return risk level, confidence, reasons
        pass
```

Built-in analyzers:
- `SpamAnalyzer` - Detects promotional/spam content
- `ToxicityAnalyzer` - Detects harmful/toxic content
- `DuplicateAnalyzer` - Detects repetitive content

#### ContentPipeline
```python
pipeline = ContentPipeline(redis)
pipeline.add_analyzer(SpamAnalyzer())
pipeline.add_analyzer(ToxicityAnalyzer())

# Add policy rules
pipeline.add_policy_rule(PolicyRule(
    name="spam_auto_delete",
    condition="spam.score > 0.8",
    action=ActionDecision.DELETE
))
```

### Usage Example
```python
from bot.core.content_pipeline import ContentPipeline, SpamAnalyzer, ToxicityAnalyzer

async def process_message(message: Message, group_id: int):
    pipeline = await get_content_pipeline(group_id)
    
    record = await pipeline.process_message(message, group_id)
    
    if record.decision:
        if record.decision.decision == "delete":
            await bot.delete_message(message.chat.id, message.message_id)
        elif record.decision.decision == "mute":
            await bot.restrict_chat_member(...)
        
        # Log for review if needed
        if record.decision.requires_review:
            await send_to_mod_queue(record)
```

---

## Integration

All features are integrated through the `AdvancedFeaturesModule`:

```python
# Enable in your group
!advanced_features enable

# Commands
/thread info           - Show current thread info
/thread list           - List active threads
/threadadmin lock      - Lock current thread
/notifyconfig list     - Show notification rules
/reportflow            - Start report flow
/contentcheck <text>   - Test content moderation
```

## Database Models

New SQLAlchemy models added:
- `Thread` - Thread records
- `ThreadParticipant` - Thread participation
- `NotificationRuleModel` - Notification configuration
- `AdvancedPollModel` - Extended polls
- `AdvancedPollVote` - Weighted votes
- `ContentModerationRecord` - Moderation decisions
- `FlowInstanceModel` - Flow execution state
- `KeyboardStateModel` - Keyboard sessions
- `NotificationLog` - Delivery logs

## Redis Keys

Namespaced Redis keys:
- `nexus:g{group_id}:keyboard:state:{state_id}` - Keyboard state
- `nexus:g{group_id}:thread:{thread_id}` - Thread data
- `nexus:g{group_id}:poll:{poll_id}` - Poll data
- `nexus:g{group_id}:flow:instance:{instance_id}` - Flow instances
- `nexus:g{group_id}:content:record:{record_id}` - Content records

---

## Architecture Decisions

1. **Redis for Active State**: All transient state (keyboard sessions, active threads, polls) stored in Redis for fast access and automatic expiration.

2. **PostgreSQL for History**: Completed/archived data persisted to PostgreSQL for long-term storage and analytics.

3. **Modular Analyzers**: Content analyzers are pluggable and can be added/removed without changing core logic.

4. **Rule-Based Notifications**: Notification rules use declarative conditions for flexibility.

5. **Thread Detection**: Threads auto-detect based on reply chains and message patterns.

---

## Performance Considerations

- All Redis operations are async
- Content analysis runs in parallel (asyncio.gather)
- Thread summaries cached
- Keyboard states auto-expire
- Poll results calculated incrementally
- Notification digests batch-processed

## Security Considerations

- All user input validated through configurable validators
- Content analysis includes rate limiting
- Appeal system for moderation decisions
- Admin-only access to sensitive commands
- Audit logging for all moderation actions
